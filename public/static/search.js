(function(){
 const mapEl=document.getElementById('store-map');
 function esc(s){return String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))}
 if(mapEl&&window.L){
   const map=L.map('store-map',{scrollWheelZoom:false}).setView([18.5204,73.8567],13);
   L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',{maxZoom:19,attribution:'&copy; OpenStreetMap contributors'}).addTo(map);
   const rows=window.NEAR_RESULTS||[], points=[], stores=new Set();
   rows.forEach(r=>{if(!r.lat||!r.lon||stores.has(r.store_id))return;stores.add(r.store_id);const storeRows=rows.filter(x=>x.store_id===r.store_id);const marker=L.circleMarker([r.lat,r.lon],{radius:8,color:'#fff',weight:2,fillColor:'#4657d5',fillOpacity:1}).addTo(map);marker.bindPopup(`<div class="map-popup"><b>${esc(r.store_name)}</b><br><small>${esc(r.address)}</small><hr>${storeRows.slice(0,4).map(p=>`${esc(p.product_name)} · ₹${Number(p.price).toLocaleString('en-IN')} · ${esc(p.stock_label)}`).join('<br>')}<br><a href="/store/${r.store_id}">View store ↗</a></div>`);points.push([r.lat,r.lon]);});
   const loc=window.NEAR_LOCATION||{};if(loc.isUser&&loc.lat!=null&&loc.lon!=null){L.circleMarker([loc.lat,loc.lon],{radius:7,color:'#fff',weight:2,fillColor:'#508ad3',fillOpacity:1}).addTo(map).bindPopup('Your shared location');points.push([loc.lat,loc.lon]);}
   if(points.length>1)map.fitBounds(points,{padding:[25,25],maxZoom:14});else if(points.length===1)map.setView(points[0],14);
 }
 const locBtn=document.getElementById('use-location'),status=document.getElementById('location-status');
 if(locBtn)locBtn.addEventListener('click',()=>{if(!navigator.geolocation){status.textContent='Location is not supported by this browser. You can continue without it.';return}status.textContent='Waiting for browser permission…';navigator.geolocation.getCurrentPosition(pos=>{const u=new URL(window.location.href);u.searchParams.set('lat',pos.coords.latitude);u.searchParams.set('lon',pos.coords.longitude);status.textContent='Location set. Refreshing search…';window.location.href=u.toString()},err=>{status.textContent=err.code===1?'Location permission was declined. Search still works without it.':'Could not get your location. Try again or continue without it.'},{enableHighAccuracy:false,timeout:9000,maximumAge:60000})});
})();
