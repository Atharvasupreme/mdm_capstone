(function(){
 const LIST='nearcart-list-v2', COMPARE='nearcart-compare-v2', WATCH='nearcart-watch-v2';
 function parse(k){try{return JSON.parse(localStorage.getItem(k)||'[]')}catch(e){return []}}
 function put(k,v){localStorage.setItem(k,JSON.stringify(v));updateCount()}
 function updateCount(){const el=document.getElementById('nav-count');if(el)el.textContent=parse(LIST).length;const cc=document.getElementById('compare-count');if(cc)cc.textContent=parse(COMPARE).length}
 function esc(s){return String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))}
 function toast(message){let el=document.getElementById('near-toast');if(!el){el=document.createElement('div');el.id='near-toast';el.className='near-toast';el.setAttribute('role','status');el.setAttribute('aria-live','polite');document.body.appendChild(el)}el.textContent=message;el.classList.add('visible');clearTimeout(window.__nearToastTimer);window.__nearToastTimer=setTimeout(()=>el.classList.remove('visible'),2600)}
 window.NearCart={read:()=>parse(LIST),write:v=>put(LIST,v),readCompare:()=>parse(COMPARE),writeCompare:v=>put(COMPARE,v),readWatch:()=>parse(WATCH),writeWatch:v=>put(WATCH,v),updateCount};
 updateCount();

 // Home page: a neighbourhood choice opens the catalogue centred on that part of Pune.
 const homeArea=document.getElementById('home-area');
 homeArea?.addEventListener('change',()=>{const url=new URL('/search',window.location.origin);url.searchParams.set('area',homeArea.value);window.location.href=url.toString()});
 // Changing from browser geolocation to a named Pune area should remove the GPS override.
 const searchArea=document.getElementById('search-area');
 searchArea?.addEventListener('change',()=>{if(searchArea.value!=='Your location'){document.getElementById('active-lat')?.remove();document.getElementById('active-lon')?.remove();searchArea.removeAttribute('data-explicit-location')}});
 document.addEventListener('click',e=>{
  const add=e.target.closest('.add-list-btn'); if(add){const id=String(add.dataset.id),items=parse(LIST);const idx=items.findIndex(x=>String(x.id)===id);if(idx>=0){items.splice(idx,1);add.classList.remove('is-added');add.textContent='＋ Add'+(add.classList.contains('compact')?'':' to list')}else{items.push({id,name:add.dataset.product,store:add.dataset.store,price:Number(add.dataset.price),checked:false});add.classList.add('is-added');add.textContent='✓ Added'}put(LIST,items);toast(idx>=0?'Removed from your shopping list':'Added to your shopping list');return}
  const cmp=e.target.closest('.compare-btn');if(cmp){const id=String(cmp.dataset.compareId),items=parse(COMPARE),idx=items.findIndex(x=>String(x.id)===id);if(idx>=0){items.splice(idx,1);cmp.classList.remove('is-selected');cmp.textContent='⇄ Compare'}else if(items.length>=4){toast('Compare up to four listings at a time');return}else{items.push({id,name:cmp.dataset.name,store:cmp.dataset.store,price:Number(cmp.dataset.price),stock:Number(cmp.dataset.stock)});cmp.classList.add('is-selected');cmp.textContent='✓ Compared'}put(COMPARE,items);toast(idx>=0?'Removed from comparison':'Added to comparison');return}
  const watch=e.target.closest('.watch-btn');if(watch){const name=watch.dataset.watchName,items=parse(WATCH),idx=items.findIndex(x=>x.name.toLowerCase()===name.toLowerCase());if(idx>=0){items.splice(idx,1);watch.classList.remove('is-watching');watch.textContent='◉ Watch'}else{items.push({name,threshold:1,seenStock:null});watch.classList.add('is-watching');watch.textContent='✓ Watching'}put(WATCH,items);toast(idx>=0?'Removed from stock watch':'Added to stock watch');return}
 });
 // Restore button state when returning to a page or reloading.
 document.querySelectorAll('.add-list-btn').forEach(b=>{if(parse(LIST).some(x=>String(x.id)===String(b.dataset.id))){b.classList.add('is-added');b.textContent='✓ Added'}});
 document.querySelectorAll('.compare-btn').forEach(b=>{if(parse(COMPARE).some(x=>String(x.id)===String(b.dataset.compareId))){b.classList.add('is-selected');b.textContent='✓ Compared'}});
 document.querySelectorAll('.watch-btn').forEach(b=>{if(parse(WATCH).some(x=>x.name.toLowerCase()===b.dataset.watchName.toLowerCase())){b.classList.add('is-watching');b.textContent='✓ Watching'}});
 document.querySelectorAll('.nav-more-menu a').forEach(a=>a.addEventListener('click',()=>document.getElementById('more-menu')?.classList.remove('show')));
 document.addEventListener('click',e=>{if(!e.target.closest('.nav-more'))document.getElementById('more-menu')?.classList.remove('show')});
})();
