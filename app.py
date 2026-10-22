from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, abort
import sqlite3, os, csv, io, math
from datetime import datetime, timezone

app = Flask(__name__)
app.secret_key = os.environ.get('NEARCART_SECRET', 'dev-only-change-this')
# Vercel Functions have an ephemeral, writable /tmp directory. Use it only for a
# demo deployment; use a hosted database (e.g. Postgres) for durable production data.
if os.environ.get('NEARCART_DB_PATH'):
    DB = os.environ['NEARCART_DB_PATH']
elif os.environ.get('VERCEL'):
    DB = '/tmp/nearcart.db'
else:
    DB = os.path.join(os.path.dirname(__file__), 'nearcart.db')

PUNE_AREAS = {
    'Pune centre': (18.5204, 73.8567),
    'FC Road / Deccan': (18.5202, 73.8416),
    'Kothrud': (18.5074, 73.8077),
    'Baner': (18.5590, 73.7868),
    'Aundh': (18.5587, 73.8072),
    'Viman Nagar': (18.5679, 73.9143),
    'Koregaon Park': (18.5362, 73.8939),
}

SEED_STORES = [
    ('Kirana Corner', 'Grocery & daily needs', 'FC Road, Deccan, Pune', 18.5202, 73.8416, '08:00', '22:00', 'directory'),
    ('Metro Mobile Hub', 'Electronics', 'JM Road, Shivajinagar, Pune', 18.5238, 73.8478, '10:00', '21:30', 'directory'),
    ('Daily Needs Market', 'Supermarket', 'Baner Road, Baner, Pune', 18.5590, 73.7868, '08:30', '22:00', 'directory'),
    ('Paper & Pen Studio', 'Stationery', 'Fergusson College Road, Deccan, Pune', 18.5232, 73.8411, '09:30', '20:30', 'directory'),
    ('CarePlus Pharmacy', 'Pharmacy', 'Paud Road, Kothrud, Pune', 18.5074, 73.8077, '09:00', '23:00', 'directory'),
    ('TechStop Accessories', 'Electronics', 'Viman Nagar, Pune', 18.5679, 73.9143, '10:00', '21:00', 'directory'),
    ('Green Basket', 'Fresh produce', 'DP Road, Aundh, Pune', 18.5587, 73.8072, '07:30', '21:30', 'directory'),
    ('Home & Handy', 'Household', 'North Main Road, Koregaon Park, Pune', 18.5362, 73.8939, '09:00', '21:00', 'directory'),
]
PRODUCTS = [
    ('USB-C 20W Charger', 'Electronics', 'charger usb-c adapter fast charge', 499, 8, 'Metro Mobile Hub'),
    ('USB-C 20W Charger', 'Electronics', 'charger usb-c adapter fast charge', 449, 3, 'TechStop Accessories'),
    ('USB-C 20W Charger', 'Electronics', 'charger usb-c adapter fast charge', 529, 5, 'Daily Needs Market'),
    ('USB-C Cable 1m', 'Electronics', 'cable usb-c charging wire', 199, 12, 'Metro Mobile Hub'),
    ('USB-C Cable 1m', 'Electronics', 'cable usb-c charging wire', 149, 2, 'TechStop Accessories'),
    ('AA Batteries (4 pack)', 'Electronics', 'battery batteries aa', 160, 6, 'Metro Mobile Hub'),
    ('Bluetooth Earphones', 'Electronics', 'earphones audio wireless earbuds', 899, 4, 'TechStop Accessories'),
    ('A5 Notebook', 'Stationery', 'notebook paper school college', 65, 22, 'Paper & Pen Studio'),
    ('A5 Notebook', 'Stationery', 'notebook paper school college', 59, 2, 'Kirana Corner'),
    ('Blue Ball Pen', 'Stationery', 'pen writing stationery', 10, 50, 'Paper & Pen Studio'),
    ('Whiteboard Markers (4 pack)', 'Stationery', 'marker pens office', 120, 7, 'Paper & Pen Studio'),
    ('First Aid Bandages', 'Pharmacy', 'first aid bandage medical dressing', 85, 9, 'CarePlus Pharmacy'),
    ('Digital Thermometer', 'Pharmacy', 'thermometer health temperature', 199, 4, 'CarePlus Pharmacy'),
    ('Hand Sanitizer 100ml', 'Pharmacy', 'sanitizer hygiene handwash', 55, 11, 'CarePlus Pharmacy'),
    ('Milk 500ml', 'Groceries', 'milk dairy', 32, 14, 'Kirana Corner'),
    ('Bread Loaf', 'Groceries', 'bread bakery', 40, 7, 'Kirana Corner'),
    ('Packaged Drinking Water 1L', 'Groceries', 'water bottle drinking', 20, 18, 'Daily Needs Market'),
    ('Rice 1kg', 'Groceries', 'rice grain grocery', 74, 16, 'Green Basket'),
    ('Tomatoes 500g', 'Groceries', 'tomato vegetables produce', 28, 9, 'Green Basket'),
    ('Bananas (6 pcs)', 'Groceries', 'banana fruit fresh produce', 42, 13, 'Green Basket'),
    ('LED Bulb 9W', 'Household', 'led bulb light electricity', 99, 10, 'Home & Handy'),
    ('AA Batteries (4 pack)', 'Electronics', 'battery batteries aa', 149, 5, 'Home & Handy'),
    ('Dishwashing Liquid 500ml', 'Household', 'dish soap cleaning kitchen', 89, 6, 'Home & Handy'),
    ('A5 Notebook', 'Stationery', 'notebook paper school college', 62, 8, 'Daily Needs Market'),
]


def db():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    con.execute('PRAGMA foreign_keys = ON')
    return con


def init_db():
    con = db()
    con.execute('''CREATE TABLE IF NOT EXISTS stores(
        id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, category TEXT,
        address TEXT, lat REAL, lon REAL, opens TEXT, closes TEXT, source TEXT DEFAULT 'demo',
        description TEXT DEFAULT '')''')
    con.execute('''CREATE TABLE IF NOT EXISTS inventory(
        id INTEGER PRIMARY KEY AUTOINCREMENT, store_id INTEGER NOT NULL,
        product_name TEXT NOT NULL, category TEXT, keywords TEXT, price REAL NOT NULL,
        stock INTEGER NOT NULL DEFAULT 0, updated_at TEXT NOT NULL,
        FOREIGN KEY(store_id) REFERENCES stores(id))''')
    # Backward-compatible schema migration for an earlier NearCart database.
    cols = {r['name'] for r in con.execute('PRAGMA table_info(stores)').fetchall()}
    if 'description' not in cols:
        con.execute("ALTER TABLE stores ADD COLUMN description TEXT DEFAULT ''")
    if con.execute('SELECT COUNT(*) FROM stores').fetchone()[0] == 0:
        descriptions = {
            'Kirana Corner':'Everyday essentials, quick grocery top-ups and familiar neighbourhood service.',
            'Metro Mobile Hub':'Phone accessories, charging gear and practical electronics basics.',
            'Daily Needs Market':'A general-purpose stop for household staples and convenience items.',
            'Paper & Pen Studio':'Stationery for students, makers, office desks and deadline emergencies.',
            'CarePlus Pharmacy':'Everyday health, hygiene and basic first-aid products.',
            'TechStop Accessories':'Cables, chargers and little electronics items that go missing at the worst time.',
            'Green Basket':'Fresh produce and everyday grocery picks.',
            'Home & Handy':'Small household fixes, bulbs, cleaning supplies and practical essentials.'}
        for s in SEED_STORES:
            con.execute('INSERT INTO stores(name,category,address,lat,lon,opens,closes,source,description) VALUES(?,?,?,?,?,?,?,?,?)', (*s, descriptions.get(s[0],'')))
        now = datetime.now(timezone.utc).isoformat()
        for pname, cat, kw, price, stock, store_name in PRODUCTS:
            sid = con.execute('SELECT id FROM stores WHERE name=?', (store_name,)).fetchone()['id']
            con.execute('INSERT INTO inventory(store_id,product_name,category,keywords,price,stock,updated_at) VALUES(?,?,?,?,?,?,?)',
                        (sid,pname,cat,kw,price,stock,now))
    # If the project folder is upgraded over an earlier database, append any newer demo
    # stores/listings without duplicating existing rows. This keeps upgrades painless.
    descriptions = {
        'Kirana Corner':'Everyday essentials, quick grocery top-ups and familiar neighbourhood service.',
        'Metro Mobile Hub':'Phone accessories, charging gear and practical electronics basics.',
        'Daily Needs Market':'A general-purpose stop for household staples and convenience items.',
        'Paper & Pen Studio':'Stationery for students, makers, office desks and deadline emergencies.',
        'CarePlus Pharmacy':'Everyday health, hygiene and basic first-aid products.',
        'TechStop Accessories':'Cables, chargers and little electronics items that go missing at the worst time.',
        'Green Basket':'Fresh produce and everyday grocery picks.',
        'Home & Handy':'Small household fixes, bulbs, cleaning supplies and practical essentials.'}
    for st in SEED_STORES:
        existing = con.execute('SELECT id FROM stores WHERE name=?', (st[0],)).fetchone()
        if not existing:
            con.execute('INSERT INTO stores(name,category,address,lat,lon,opens,closes,source,description) VALUES(?,?,?,?,?,?,?,?,?)', (*st, descriptions.get(st[0],'')))
        else:
            # Keep upgrades pointed at the Pune neighbourhood view, even if the local
            # database was created by an earlier Nashik version. Stock edits are retained.
            con.execute('UPDATE stores SET category=?, address=?, lat=?, lon=?, opens=?, closes=?, source=?, description=? WHERE id=?',
                        (st[1], st[2], st[3], st[4], st[5], st[6], st[7], descriptions.get(st[0], ''), existing['id']))
    now = datetime.now(timezone.utc).isoformat()
    for pname, cat, kw, price, stock, store_name in PRODUCTS:
        sidrow = con.execute('SELECT id FROM stores WHERE name=?', (store_name,)).fetchone()
        if not sidrow: continue
        exists = con.execute('SELECT id FROM inventory WHERE store_id=? AND lower(product_name)=lower(?)', (sidrow['id'], pname)).fetchone()
        if not exists:
            con.execute('INSERT INTO inventory(store_id,product_name,category,keywords,price,stock,updated_at) VALUES(?,?,?,?,?,?,?)', (sidrow['id'],pname,cat,kw,price,stock,now))
    con.commit(); con.close()


@app.template_filter('money')
def money(v):
    return '₹{:,.0f}'.format(v or 0)


@app.template_filter('timeago')
def timeago(value):
    try:
        dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
        sec = max(0, (datetime.now(timezone.utc) - dt.astimezone(timezone.utc)).total_seconds())
        if sec < 60: return 'just now'
        if sec < 3600: return f'{int(sec//60)} min ago'
        if sec < 86400: return f'{int(sec//3600)} hr ago'
        return f'{int(sec//86400)} days ago'
    except Exception: return 'time unknown'


def distance_km(lat, lon, store_lat, store_lon):
    if lat is None or lon is None: return None
    p1, p2 = math.radians(lat), math.radians(store_lat)
    dp, dl = math.radians(store_lat-lat), math.radians(store_lon-lon)
    a = math.sin(dp/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return round(6371*2*math.atan2(math.sqrt(a), math.sqrt(1-a)), 1)


def enrich(row, lat=None, lon=None):
    r = dict(row)
    r['distance_km'] = distance_km(lat, lon, r['lat'], r['lon'])
    try:
        updated = datetime.fromisoformat(r['updated_at'].replace('Z', '+00:00'))
        age = max(0, (datetime.now(timezone.utc)-updated.astimezone(timezone.utc)).total_seconds())
    except Exception: age = 999999
    r['age_seconds'] = age
    r['freshness'] = 'Fresh' if age < 3600 else ('Aging' if age < 86400 else 'Stale')
    r['available'] = r['stock'] > 0
    r['stock_label'] = 'Out of stock' if r['stock'] <= 0 else ('Low stock' if r['stock'] <= 3 else 'In stock')
    r['confidence'] = round(max(15, min(98, 94 - (min(age,172800)/172800)*48 - (20 if r['stock']<=2 else 0))))
    r['is_open'] = is_open(r.get('opens'), r.get('closes'))
    dist_penalty = (r['distance_km'] if r['distance_km'] is not None else 3.0) * 3
    r['score'] = (45 if r['stock']>0 else -60) + (20 if r['freshness']=='Fresh' else 7 if r['freshness']=='Aging' else -10) + r['confidence']*.15 - dist_penalty - min(r['price']/100,20)
    return r


def is_open(opens, closes):
    try:
        from zoneinfo import ZoneInfo
        now = datetime.now(ZoneInfo('Asia/Kolkata')).strftime('%H:%M')
        return opens <= now <= closes if opens <= closes else (now >= opens or now <= closes)
    except Exception: return None


def query_products(q='', lat=None, lon=None, category='All', available_only=False, max_price=None, sort='recommended', open_now=False):
    con = db()
    sql = '''SELECT i.*, s.name AS store_name, s.category AS store_type, s.address,
             s.lat, s.lon, s.opens, s.closes, s.source, s.id AS store_id
             FROM inventory i JOIN stores s ON s.id=i.store_id WHERE 1=1'''
    params = []
    if q.strip():
        like = f'%{q.strip()}%'
        sql += ' AND (i.product_name LIKE ? OR i.category LIKE ? OR i.keywords LIKE ? OR s.name LIKE ?)'
        params += [like, like, like, like]
    if category and category != 'All': sql += ' AND i.category=?'; params.append(category)
    if available_only: sql += ' AND i.stock>0'
    if max_price is not None:
        sql += ' AND i.price<=?'; params.append(max_price)
    rows = [enrich(r, lat, lon) for r in con.execute(sql, params).fetchall()]
    con.close()
    if open_now: rows = [r for r in rows if r['is_open'] is True]
    if sort == 'price': rows.sort(key=lambda x: (x['price'], not x['available'], x['score']), reverse=False)
    elif sort == 'distance' and lat is not None: rows.sort(key=lambda x: (x['distance_km'] is None, x['distance_km'] or 999, not x['available']))
    elif sort == 'fresh': rows.sort(key=lambda x: (x['freshness'] != 'Fresh', x['age_seconds'], not x['available']))
    else: rows.sort(key=lambda x: x['score'], reverse=True)
    return rows


def get_store(store_id):
    con = db(); store = con.execute('SELECT * FROM stores WHERE id=?', (store_id,)).fetchone()
    if not store: con.close(); return None, []
    products = con.execute('SELECT i.*, s.name AS store_name, s.category AS store_type, s.address, s.lat, s.lon, s.opens, s.closes, s.source, s.id AS store_id FROM inventory i JOIN stores s ON s.id=i.store_id WHERE s.id=? ORDER BY i.stock DESC, i.product_name', (store_id,)).fetchall()
    con.close()
    return dict(store), [enrich(p) for p in products]


@app.route('/')
def home():
    con=db()
    stores=[dict(x) for x in con.execute('SELECT s.*, COUNT(i.id) AS listings, SUM(CASE WHEN i.stock>0 THEN 1 ELSE 0 END) AS available FROM stores s LEFT JOIN inventory i ON s.id=i.store_id GROUP BY s.id ORDER BY s.name LIMIT 4').fetchall()]
    con.close()
    featured=query_products('', sort='recommended')
    # one good in-stock listing per product name
    best=[]; seen=set()
    for p in featured:
        if p['product_name'] not in seen and p['stock']>0:
            best.append(p); seen.add(p['product_name'])
        if len(best)==4: break
    return render_template('home.html', stores=stores, featured=best)


@app.route('/search')
def search():
    q=request.args.get('q',''); category=request.args.get('category','All'); sort=request.args.get('sort','recommended')
    available_only=request.args.get('available')=='1'; open_now=request.args.get('open_now')=='1'
    area=request.args.get('area','Pune centre')
    has_explicit_location=bool(request.args.get('lat') and request.args.get('lon'))
    try:
        lat=float(request.args['lat']); lon=float(request.args['lon'])
        area='Your location'
    except (ValueError, KeyError):
        lat,lon=PUNE_AREAS.get(area, PUNE_AREAS['Pune centre'])
        has_explicit_location=False
        if area not in PUNE_AREAS: area='Pune centre'
    try: max_price=float(request.args['max_price']) if request.args.get('max_price') else None
    except ValueError: max_price=None
    # Search opens with the full local catalogue, not a blank results pane.
    results=query_products(q,lat,lon,category,available_only,max_price,sort,open_now)
    categories=['Electronics','Stationery','Groceries','Pharmacy','Household']
    return render_template('search.html', q=q, category=category, sort=sort, available_only=available_only, open_now=open_now, max_price=max_price, results=results, lat=lat, lon=lon, categories=categories, area=area, areas=list(PUNE_AREAS.keys()), has_explicit_location=has_explicit_location)


@app.route('/api/health')
def api_health():
    con=db()
    metrics=con.execute('''SELECT COUNT(*) listings, SUM(CASE WHEN stock>0 THEN 1 ELSE 0 END) in_stock,
        SUM(CASE WHEN stock BETWEEN 1 AND 3 THEN 1 ELSE 0 END) low_stock,
        MAX(updated_at) last_updated FROM inventory''').fetchone()
    stores_count=con.execute('SELECT COUNT(*) FROM stores').fetchone()[0]
    con.close()
    return jsonify({'status':'ok','mode':'local-catalogue','stores':stores_count,'listings':metrics['listings'] or 0,
        'in_stock':metrics['in_stock'] or 0,'low_stock':metrics['low_stock'] or 0,
        'last_updated':metrics['last_updated'],'message':'Pune starter listings are stored locally; verified live availability requires retailer inventory feeds.'})


@app.route('/api/stores')
def api_stores():
    con=db(); rows=[dict(r) for r in con.execute('SELECT id,name,category,address,lat,lon,opens,closes,source FROM stores ORDER BY name').fetchall()]; con.close()
    return jsonify(rows)


@app.route('/api-docs')
def api_docs(): return render_template('api_docs.html')


@app.route('/api/search')
def api_search():
    q=request.args.get('q',''); category=request.args.get('category','All')
    try: lat=float(request.args['lat']); lon=float(request.args['lon'])
    except (ValueError, KeyError): lat=lon=None
    try: max_price=float(request.args['max_price']) if request.args.get('max_price') else None
    except ValueError: max_price=None
    rows=query_products(q,lat,lon,category,request.args.get('available')=='1',max_price,request.args.get('sort','recommended'),request.args.get('open_now')=='1')
    return jsonify(rows)


@app.route('/stores')
def stores_page():
    con=db(); stores=[dict(r) for r in con.execute('''SELECT s.*, COUNT(i.id) listings,
       SUM(CASE WHEN i.stock>0 THEN 1 ELSE 0 END) available FROM stores s LEFT JOIN inventory i ON s.id=i.store_id
       GROUP BY s.id ORDER BY s.name''').fetchall()]; con.close()
    for s in stores: s['is_open']=is_open(s['opens'],s['closes'])
    return render_template('stores.html', stores=stores)


@app.route('/store/<int:store_id>')
def store_detail(store_id):
    store, products=get_store(store_id)
    if not store: abort(404)
    store['is_open']=is_open(store['opens'],store['closes'])
    return render_template('store.html', store=store, products=products)


@app.route('/product/<int:item_id>')
def product_detail(item_id):
    con=db(); row=con.execute('''SELECT i.*, s.name store_name, s.category store_type, s.address, s.lat, s.lon,
       s.opens, s.closes, s.source, s.id store_id FROM inventory i JOIN stores s ON i.store_id=s.id WHERE i.id=?''',(item_id,)).fetchone()
    if not row: con.close(); abort(404)
    product=enrich(row)
    alternatives=[enrich(r) for r in con.execute('''SELECT i.*,s.name store_name,s.category store_type,s.address,s.lat,s.lon,s.opens,s.closes,s.source,s.id store_id
       FROM inventory i JOIN stores s ON i.store_id=s.id WHERE lower(i.product_name)=lower(?) AND i.id<>? ORDER BY i.stock DESC,i.price ASC''',(product['product_name'],item_id)).fetchall()]
    con.close()
    return render_template('product.html', product=product, alternatives=alternatives)


@app.route('/deals')
def deals():
    rows=query_products('',sort='price')
    grouped={}
    for r in rows:
        name=r['product_name']
        grouped.setdefault(name,[]).append(r)
    offers=[]
    for name, options in grouped.items():
        available=[x for x in options if x['stock']>0]
        if not available: continue
        available.sort(key=lambda x:x['price'])
        cheapest=available[0]
        prices=[x['price'] for x in available]
        cheapest['comparison_price']=max(prices)
        cheapest['savings_vs_highest']=max(0,max(prices)-cheapest['price'])
        cheapest['other_options']=len(available)-1
        offers.append(cheapest)
    offers.sort(key=lambda x:(-x['savings_vs_highest'],x['price']))
    return render_template('deals.html', offers=offers)



@app.route('/compare')
def compare_page(): return render_template('compare.html')


@app.route('/api/item/<int:item_id>')
def item_api(item_id):
    con=db(); row=con.execute('''SELECT i.*,s.name store_name,s.category store_type,s.address,s.lat,s.lon,s.opens,s.closes,s.source,s.id store_id FROM inventory i JOIN stores s ON s.id=i.store_id WHERE i.id=?''',(item_id,)).fetchone(); con.close()
    if not row: return jsonify({'error':'not found'}),404
    return jsonify(enrich(row))

@app.route('/list')
def shopping_list(): return render_template('list.html')


@app.route('/plan')
def trip_plan(): return render_template('plan.html')


@app.post('/api/plan')
def plan_api():
    payload=request.get_json(silent=True) or {}
    names=[str(x).strip() for x in payload.get('products',[]) if str(x).strip()][:40]
    if not names: return jsonify({'stores':[],'unmatched':[],'message':'Add items to your list first.'})
    con=db(); options={}
    for name in names:
        rows=con.execute('''SELECT i.*,s.name store_name,s.address,s.lat,s.lon,s.opens,s.closes,s.id store_id,s.category store_type,s.source
          FROM inventory i JOIN stores s ON s.id=i.store_id WHERE lower(i.product_name)=lower(?) AND i.stock>0''',(name,)).fetchall()
        options[name]=[enrich(r) for r in rows]
    con.close()
    unmatched=[name for name,rows in options.items() if not rows]
    remaining={name:rows for name,rows in options.items() if rows}
    chosen=[]
    # Greedy set-cover-ish planner: select the store satisfying the most remaining items,
    # using aggregate price and stock confidence as tie-breakers.
    while remaining:
        candidates={}
        for name, rows in remaining.items():
            for row in rows:
                sid=row['store_id']; candidates.setdefault(sid,{'store':row,'items':[],'sum':0,'score':0})
                candidates[sid]['items'].append((name,row)); candidates[sid]['sum']+=row['price']; candidates[sid]['score']+=row['confidence']
        if not candidates: break
        best=max(candidates.values(), key=lambda c:(len(c['items']), c['score']-c['sum']*.05))
        store=best['store']; output={'store_id':store['store_id'],'store_name':store['store_name'],'address':store['address'],'lat':store['lat'],'lon':store['lon'],'items':[],'subtotal':0}
        covered=[]
        for name, row in best['items']:
            output['items'].append({'name':name,'price':row['price'],'stock':row['stock'],'item_id':row['id']})
            output['subtotal']+=row['price']; covered.append(name)
        output['subtotal']=round(output['subtotal'],2); chosen.append(output)
        for name in covered: remaining.pop(name,None)
    return jsonify({'stores':chosen,'unmatched':unmatched,'message':f'Plan covers {sum(len(x["items"]) for x in chosen)} item(s) across {len(chosen)} store(s). Prices and availability are demo data.'})


@app.route('/alerts')
def alerts(): return render_template('alerts.html')


@app.route('/retailers')
def retailers():
    con=db()
    rows=con.execute('''SELECT i.id,i.product_name,i.category,i.price,i.stock,i.updated_at,s.name store_name,s.id store_id
        FROM inventory i JOIN stores s ON s.id=i.store_id ORDER BY s.name,i.product_name''').fetchall()
    stores=con.execute('SELECT id,name FROM stores ORDER BY name').fetchall()
    con.close()
    return render_template('retailers.html', rows=rows, stores=stores)


@app.post('/retailers/update')
def update_stock():
    try:
        item_id=int(request.form['item_id']); stock=max(0,int(request.form['stock'])); price=max(0,float(request.form['price']))
        con=db(); con.execute('UPDATE inventory SET stock=?,price=?,updated_at=? WHERE id=?', (stock,price,datetime.now(timezone.utc).isoformat(),item_id))
        con.commit(); con.close(); flash('Inventory updated. Search results now show the new timestamp.', 'success')
    except Exception:
        flash('Could not update item. Check stock and price values.', 'error')
    return redirect(url_for('retailers'))


@app.post('/retailers/add')
def add_product():
    try:
        store_id=int(request.form['store_id']); name=request.form['product_name'].strip(); category=request.form['category'].strip()
        keywords=request.form.get('keywords','').strip(); price=float(request.form['price']); stock=max(0,int(request.form['stock']))
        if not name or not category or price < 0: raise ValueError()
        con=db(); exists=con.execute('SELECT id FROM stores WHERE id=?',(store_id,)).fetchone()
        if not exists: raise ValueError()
        con.execute('INSERT INTO inventory(store_id,product_name,category,keywords,price,stock,updated_at) VALUES(?,?,?,?,?,?,?)',
          (store_id,name,category,keywords,price,stock,datetime.now(timezone.utc).isoformat()))
        con.commit(); con.close(); flash(f'Added {name} to the catalogue.', 'success')
    except Exception:
        flash('Could not add product. Check all fields and try again.', 'error')
    return redirect(url_for('retailers'))


@app.post('/retailers/import')
def import_csv():
    f=request.files.get('file')
    if not f or not f.filename.lower().endswith('.csv'):
        flash('Choose a CSV file.', 'error'); return redirect(url_for('retailers'))
    con=None
    try:
        reader=csv.DictReader(io.StringIO(f.stream.read().decode('utf-8-sig')))
        con=db(); changed=0
        for row in reader:
            name=(row.get('store_name') or '').strip(); pname=(row.get('product_name') or '').strip()
            if not name or not pname: continue
            store=con.execute('SELECT id FROM stores WHERE name=?',(name,)).fetchone()
            if not store: continue
            price=max(0,float(row.get('price') or 0)); stock=max(0,int(row.get('stock') or 0)); category=(row.get('category') or 'Other').strip(); kw=(row.get('keywords') or '').strip()
            existing=con.execute('SELECT id FROM inventory WHERE store_id=? AND lower(product_name)=lower(?)',(store['id'],pname)).fetchone()
            vals=(category,kw,price,stock,datetime.now(timezone.utc).isoformat())
            if existing: con.execute('UPDATE inventory SET category=?,keywords=?,price=?,stock=?,updated_at=? WHERE id=?',(*vals,existing['id']))
            else: con.execute('INSERT INTO inventory(store_id,product_name,category,keywords,price,stock,updated_at) VALUES(?,?,?,?,?,?,?)',(store['id'],pname,*vals))
            changed+=1
        con.commit(); flash(f'Imported or updated {changed} inventory rows.', 'success')
    except Exception:
        if con: con.rollback()
        flash('CSV import failed. Check the template, store names and numeric columns.', 'error')
    finally:
        if con: con.close()
    return redirect(url_for('retailers'))


@app.route('/about')
def about(): return render_template('about.html')


@app.errorhandler(404)
def not_found(_): return render_template('404.html'), 404

# Make the starter database available to development servers and WSGI importers.
init_db()

if __name__ == '__main__':
    app.run(debug=os.environ.get('FLASK_DEBUG') == '1', host='127.0.0.1', port=int(os.environ.get('PORT', 5000)))
