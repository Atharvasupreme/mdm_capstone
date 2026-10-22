# NearCart

NearCart is a multi-page local-shopping application. It lets shoppers discover product listings, compare prices and stock freshness, save a shopping list, plan store stops, and view a map of nearby options.

## Run locally (Windows / VS Code)

1. Extract the project ZIP and open the **NearCart** folder in VS Code.
2. In the terminal run:

   ```powershell
   python -m venv .venv
   .venv\Scripts\activate
   python -m pip install -r requirements.txt
   python app.py
   ```

3. Open **http://127.0.0.1:5000**.

Python 3.10 or newer is recommended. On macOS/Linux, activate with `source .venv/bin/activate`. On first run the app creates `nearcart.db`. Existing local databases are refreshed to the Pune neighbourhood coordinates while retaining the saved stock and price values.

## Pages and features

- **Home** — editorial-style landing page, quick product searches and a Pune neighbourhood selector.
- **Discover** — product search, stock status, update freshness, availability-confidence estimate, filters, price sorting, in-stock-only, opening-hours filter and map markers.
- **Location** — select Pune centre, FC Road/Deccan, Kothrud, Baner, Aundh, Viman Nagar, Koregaon Park or share browser location permission.
- **Product details** — price, listing details, confidence indicator, alternatives, directions, watch and compare controls.
- **Store directory/profile** — map, store categories, opening hours and listed inventory.
- **Best prices** — compare lowest listed prices without inventing discounts.
- **Shopping list** — browser-local items, checkboxes, estimated basket total and cross-page state.
- **Compare** — compare up to four selected listings side by side.
- **Stock watch** — optional browser notifications and 60-second checks while the page is open.
- **Smart trip planner** — group a list across fewer stores and request an OSRM road-route preview when multiple stops are selected.
- **Retailer studio** — edit prices/stock, add inventory rows and import CSV files.
- **How it works** — ranking/freshness method, tools used and data notes.
- **Data & API** — local API status and endpoint references.

## Free/open technologies

- Flask + SQLite for the local backend and persistent inventory.
- Leaflet + OpenStreetMap for interactive maps.
- OSRM public routing endpoint for best-effort route previews.
- Browser Geolocation, localStorage and Notifications for optional location, saved lists and page-active stock watch.
- Google Maps directions URLs for external navigation without embedding a paid Maps API.

Public map tiles and route services have usage limits and are not guaranteed production infrastructure. Review the OpenStreetMap tile usage policy before deployment. For public use, choose an approved service, cache politely and protect the backend.

## Inventory data note

The Pune directory is preloaded with illustrative local listings so the app can be explored without first onboarding stores. This is not yet connected to real retailer POS systems. For verified near-real-time stock, connect store inventory APIs, webhooks or trusted scheduled feeds and show each source's last successful sync. Please don't present seeded stock as confirmed live inventory.

## CSV import format

Download `static/inventory-template.csv`. Header fields:

`store_name,product_name,category,keywords,price,stock`

`store_name` must match a store in the directory. Matching listings are updated; new listings are added. Numeric values are checked before saving.

## Before public deployment

Retailer Studio currently has no authentication and should remain private until login, role permissions, CSRF protection, audit logging, input hardening, rate limits and HTTPS are configured. Browser lists are local to the current device, and Stock Watch only runs while its page remains open. Availability is not a reservation.

For a WSGI host, install dependencies and run `gunicorn app:app` (a Procfile is included). Set a unique `NEARCART_SECRET` before deploying.

## Design refresh
The latest design pass improves type scale, contrast, line-height, navigation legibility, button sizing, card spacing, and responsive behaviour across the main and secondary pages. Pune remains the default demonstration area.


## Deploy to Vercel (demo mode)

This folder is the Vercel project root: `app.py`, `requirements.txt`, `vercel.json`, `templates/`, and `public/` should be at the repository root. Static assets are mirrored under `public/static/` so Vercel can serve `/static/...` from its CDN.

### GitHub import
1. Create a GitHub repository. Upload the **contents of this NearCart folder** to the repository root (not an extra parent folder). Do not commit `.venv/`, `.env`, or `nearcart.db`.
2. On Vercel choose **Add New → Project**, import the repository, keep the Root Directory at `./`, and deploy. Vercel detects the Flask `app` exported from `app.py` and installs `requirements.txt`.
3. In Project Settings → Environment Variables, add `NEARCART_SECRET` with a long random value. Redeploy after adding it.
4. Check `/`, `/search?q=charger`, `/stores`, and `/retailers` after deployment.

### Important persistence limitation
For Vercel, the demo database is placed at `/tmp/nearcart.db` so the app can initialise without writing into the read-only deployment bundle. `/tmp` is ephemeral and different serverless instances do not share it. Retailer edits/imports may disappear after an instance recycles or may not be visible to other instances. This is **demo-only**, not production inventory storage. For persistent multi-user deployment, move the store/inventory tables to a hosted Postgres database (for example Supabase or Neon) and configure its connection string as a Vercel environment variable. Do not treat the Vercel demo database as durable.

### CLI option
From this project root: `npm install -g vercel`, then `vercel login`, `vercel`, and follow the prompts. When the preview works, run `vercel --prod`. The GitHub import option is usually easier for first-time deployment.
