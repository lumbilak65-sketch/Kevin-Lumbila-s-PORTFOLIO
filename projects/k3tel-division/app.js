const imagePath = name => "../../images/k3tel/" + ({"campaign.jpg":"IMG_2301.jpg","campaign-warm.jpg":"IMG_2300.jpg","lookbook.jpg":"IMG_2382.jpg","stripe-look.jpg":"IMG_0841.jpg","stripe-back.jpg":"IMG_0819%202.jpg","detail.jpg":"IMG_1274.JPG","emblem.jpg":"IMG_0825.JPG","legacy.jpg":"k3tel-collection-board.jpg","wave-jersey.jpg":"k3tel-campaign.jpg","panther-jersey.jpg":"k3tel-jersey-concept.jpg"})[name];
'use strict';
// Working titles: confirm final product names and specifications before launch.
const products = [
 {id:'blue-tracksuit',title:'DIVISION TRACKSUIT',color:'BLUE / BLACK',category:'tracksuits',image:'campaign.jpg',gallery:['campaign.jpg','lookbook.jpg','campaign-warm.jpg'],position:'70% center',description:'The blue and black K3TEL tracksuit features signature graphics and contrasting panel lines. Explore the campaign photography for a closer look.',badge:'PREVIEW'},
 {id:'black-tracksuit',title:'DIVISION TRACKSUIT',color:'BLACK / WHITE',category:'tracksuits',image:'lookbook.jpg',gallery:['lookbook.jpg','campaign-warm.jpg','campaign.jpg'],position:'75% center',description:'The black K3TEL tracksuit pairs contrasting stripes with signature Division artwork. Final product specifications will be shared before launch.',badge:'PREVIEW'},
 {id:'striped-shirt',title:'CHROME STRIPE SHIRT',color:'RED / WHITE',category:'tops',image:'stripe-look.jpg',gallery:['stripe-look.jpg','stripe-back.jpg','detail.jpg'],description:'A red and white striped shirt with the chrome K3TEL emblem and Division lettering across the back. The detail photograph also explores a green and black design.',badge:'PREVIEW'},
 {id:'wave-jersey',title:'1975 WAVE JERSEY',color:'BLUE / WHITE',category:'concepts',image:'wave-jersey.jpg',gallery:['wave-jersey.jpg'],contain:true,description:'A design concept connecting the EST. 1975 story with blue wave panels and signature web artwork. Concept imagery is shown; production details and availability are not yet confirmed.',badge:'DESIGN CONCEPT'},
 {id:'panther-jersey',title:'75 PANTHER JERSEY',color:'PINK / BLACK',category:'concepts',image:'panther-jersey.jpg',gallery:['panther-jersey.jpg'],contain:true,description:'A pink and black jersey concept with a panther graphic, chrome Division lettering and the number 75. Concept imagery is shown; production details and availability are not yet confirmed.',badge:'DESIGN CONCEPT'}
];
const $=(s,r=document)=>r.querySelector(s);
const dialogs=[...document.querySelectorAll('dialog')];
let bag=[];
try{const saved=JSON.parse(localStorage.getItem('k3tel-preview-bag-v1')||'[]');if(Array.isArray(saved))bag=[...new Set(saved)].filter(id=>products.some(p=>p.id===id));}catch{}
let toastTimer;
function notify(message){$('#toast').textContent=message;$('#toast').classList.add('visible');clearTimeout(toastTimer);toastTimer=setTimeout(()=>$('#toast').classList.remove('visible'),2600);}
function openDialog(dialog){dialogs.forEach(d=>{if(d.open)d.close();});dialog.showModal();document.body.classList.add('modal-open');}
dialogs.forEach(dialog=>{$('.close',dialog).addEventListener('click',()=>dialog.close());dialog.addEventListener('close',()=>{if(!dialogs.some(d=>d.open))document.body.classList.remove('modal-open');});dialog.addEventListener('click',e=>{if(e.target===dialog){const r=dialog.getBoundingClientRect();if(e.clientX<r.left||e.clientX>r.right||e.clientY<r.top||e.clientY>r.bottom)dialog.close();}});});
function renderProducts(filter='all'){
 const shown=products.filter(p=>filter==='all'||p.category===filter);
 $('#product-count').textContent=`${shown.length} PIECE${shown.length===1?'':'S'}`;
 $('#products').innerHTML=shown.map(p=>`<button class="product-card" data-product="${p.id}" aria-label="View ${p.title}, ${p.color}"><div class="product-image"><img src="${imagePath(p.image)}" alt="${p.title}, ${p.color}" loading="lazy" width="600" height="800" ${p.contain?'class="contain"':''} style="object-position:${p.position||'center'}"><span class="product-badge">${p.badge}</span><span class="product-plus" aria-hidden="true">+</span></div><div class="product-info"><div><h3>${p.title}</h3><p>[${p.color}]</p></div><span>COMING SOON</span></div></button>`).join('');
}
function openProduct(id){
 const p=products.find(p=>p.id===id);if(!p)return;
 $('#product-detail').innerHTML=`<div class="product-detail-grid"><div class="product-detail-image"><img id="detail-image" src="${imagePath(p.image)}" alt="${p.title}, ${p.color}"></div><div class="product-detail-copy"><p class="eyebrow">K3TEL DIVISION / ${p.badge}</p><h2 id="product-title">${p.title}</h2><p class="color-label">[${p.color}]</p><p class="description">${p.description}</p>${p.gallery.length>1?`<div class="thumbnails" role="group" aria-label="Product photographs">${p.gallery.map((image,i)=>`<button data-image="${image}" aria-label="View photograph ${i+1}" aria-pressed="${i===0}"><img src="${imagePath(image)}" alt="" width="48" height="62"></button>`).join('')}</div>`:''}<p class="availability">RELEASE: TO BE ANNOUNCED<br>PRICING & SIZES: COMING SOON</p><button class="button" id="save-piece" data-id="${p.id}">${bag.includes(p.id)?'SAVED TO YOUR BAG':'SAVE TO PREVIEW BAG'} <span>+</span></button><p class="save-note">Preview only. Saving a piece does not reserve stock or place an order.</p></div></div>`;
 openDialog($('#product-dialog'));
}
function persistBag(){try{localStorage.setItem('k3tel-preview-bag-v1',JSON.stringify(bag));}catch{}renderBag();}
function renderBag(){
 $('#bag-count').textContent=`[${bag.length}]`;
 $('#bag-items').innerHTML=bag.length?bag.map(id=>{const p=products.find(p=>p.id===id);return `<div class="bag-item"><img src="${imagePath(p.image)}" alt="${p.title}, ${p.color}"><div><h3>${p.title}</h3><p>[${p.color}]<br>COMING SOON</p><button class="remove-item" data-remove="${p.id}" aria-label="Remove ${p.title}, ${p.color}">REMOVE</button></div></div>`;}).join(''):'<p class="empty-bag">Your next chapter starts here.<br>Explore the collection and save your favorite pieces.</p>';
}
function closeMenu(){$('#navigation').hidden=true;$('.menu-toggle').setAttribute('aria-expanded','false');$('.menu-toggle span').textContent='+';}
$('.menu-toggle').addEventListener('click',()=>{const open=$('.menu-toggle').getAttribute('aria-expanded')==='true';$('.menu-toggle').setAttribute('aria-expanded',String(!open));$('#navigation').hidden=open;$('.menu-toggle span').textContent=open?'+':'−';});
$('#navigation').addEventListener('click',e=>{if(e.target.closest('a'))closeMenu();});
document.addEventListener('keydown',e=>{if(e.key==='Escape')closeMenu();});
document.querySelectorAll('[data-filter]').forEach(button=>button.addEventListener('click',()=>{document.querySelectorAll('[data-filter]').forEach(b=>b.setAttribute('aria-pressed',String(b===button)));renderProducts(button.dataset.filter);}));
$('#products').addEventListener('click',e=>{const button=e.target.closest('[data-product]');if(button)openProduct(button.dataset.product);});
$('#product-detail').addEventListener('click',e=>{
 const thumb=e.target.closest('[data-image]');if(thumb){$('#detail-image').src=`${imagePath(thumb.dataset.image)}`;document.querySelectorAll('[data-image]').forEach(b=>b.setAttribute('aria-pressed',String(b===thumb)));}
 const save=e.target.closest('#save-piece');if(save){if(!bag.includes(save.dataset.id)){bag.push(save.dataset.id);persistBag();notify('PIECE SAVED TO YOUR PREVIEW BAG');}else notify('THIS PIECE IS ALREADY IN YOUR BAG');save.innerHTML='SAVED TO YOUR BAG <span>✓</span>';}
});
$('.bag-toggle').addEventListener('click',()=>{renderBag();openDialog($('#bag-dialog'));});
$('#bag-items').addEventListener('click',e=>{const remove=e.target.closest('[data-remove]');if(remove){bag=bag.filter(id=>id!==remove.dataset.remove);persistBag();notify('PIECE REMOVED');}});
$('.continue').addEventListener('click',()=>{$('#bag-dialog').close();$('#collection').scrollIntoView({behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'instant':'smooth'});});
$('#open-lookbook').addEventListener('click',()=>openDialog($('#lookbook-dialog')));
$('#year').textContent=new Date().getFullYear();renderProducts();renderBag();
