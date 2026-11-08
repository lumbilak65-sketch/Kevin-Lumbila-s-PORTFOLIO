export const SURFACES=['front','back','left','right'];
export const GARMENT_IDS=['tee','hoodie','jersey','jacket','crop','tank','jeans','cargo','shorts','skirt','dress','boots','sweater'];
export function defaultState(){return {schema:'k3tel-studio',version:1,name:'Untitled exploration',garment:'tee',fit:110,length:100,sleeve:100,base:'#263d34',secondary:'#263d34',trim:'#d7dfc8',material:'cotton',pattern:'solid',patternScale:6,seams:true,layers:[{id:'first-mark',type:'text',surface:'front',text:'K3TEL',font:'Impact',color:'#e4ead4',x:50,y:31,scale:64,rotation:0,opacity:100,visible:true},{id:'first-legacy',type:'text',surface:'front',text:'DIVISION / EST. 1975',font:'Courier New',color:'#e4ead4',x:50,y:43,scale:49,rotation:0,opacity:100,visible:true}]};}
const number=(v,min,max,fallback)=>Number.isFinite(Number(v))?Math.min(max,Math.max(min,Number(v))):fallback;
const color=(v,fallback)=>typeof v==='string'&&/^#[0-9a-f]{6}$/i.test(v)?v:fallback;
const choice=(v,allowed,fallback)=>allowed.includes(v)?v:fallback;
export function normalizeProject(raw){
 if(!raw||typeof raw!=='object'||raw.schema!=='k3tel-studio'||raw.version!==1)throw Error('Choose a K3TEL Studio project file (version 1).');
 const d=defaultState();
 const s={schema:d.schema,version:1,name:typeof raw.name==='string'?raw.name.slice(0,60):d.name,garment:choice(raw.garment,GARMENT_IDS,'tee'),fit:number(raw.fit,75,140,100),length:number(raw.length,65,135,100),sleeve:number(raw.sleeve,55,150,100),base:color(raw.base,d.base),secondary:color(raw.secondary,d.secondary),trim:color(raw.trim,d.trim),material:choice(raw.material,['cotton','jersey','denim','nylon','leather','metallic'],'cotton'),pattern:choice(raw.pattern,['solid','stripes','pinstripe','checker','camo','dots'],'solid'),patternScale:number(raw.patternScale,2,16,6),seams:raw.seams!==false,layers:[]};
 if(Array.isArray(raw.layers))for(const [index,l] of raw.layers.slice(0,30).entries()){
  if(!l||!['text','image'].includes(l.type)||!SURFACES.includes(l.surface))continue;
  if(l.type==='image'&&(typeof l.src!=='string'||l.src.length>3500000||!/^data:image\/(png|jpeg|webp);base64,[a-zA-Z0-9+/=]+$/.test(l.src)))continue;
  const base={id:'layer-'+index+'-'+Math.random().toString(36).slice(2,7),type:l.type,surface:l.surface,x:number(l.x,0,100,50),y:number(l.y,0,100,35),scale:number(l.scale,5,120,50),rotation:number(l.rotation,-180,180,0),opacity:number(l.opacity,10,100,100),visible:l.visible!==false};
  if(l.type==='text')Object.assign(base,{text:typeof l.text==='string'?l.text.slice(0,120):'YOUR VISION',font:choice(l.font,['Impact','Arial','Georgia','Courier New','cursive'],'Impact'),color:color(l.color,'#ffffff')});
  else Object.assign(base,{src:l.src,name:typeof l.name==='string'?l.name.slice(0,80):'Artwork',removeWhite:!!l.removeWhite});
  s.layers.push(base);
 }
 return s;
}
export function layerBounds(layer,images,size=1024){const width=size*layer.scale/100;let height;
 if(layer.type==='image'){const im=images.get(layer.src+'|'+!!layer.removeWhite);height=im?width*im.height/im.width:width;}
 else{const lines=layer.text.split('\n'),n=Math.max(...lines.map(x=>x.length),1);const fontSize=Math.min(230,width/Math.max(1,n*.58));height=fontSize*1.16*lines.length;}
 return {width,height};
}
