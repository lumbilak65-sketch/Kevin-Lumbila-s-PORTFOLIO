import * as THREE from 'three';
export const GARMENTS=[
 {id:'tee',name:'Oversized tee',short:'TEE',icon:'M3 10 10 6 14 8 18 6 25 10 22 17 18 15 18 29 10 29 10 15 6 17Z',hint:'Width changes the silhouette. Length changes the body. The third slider changes sleeve length.'},
 {id:'hoodie',name:'Pullover hoodie',short:'HOODIE',icon:'M10 7Q9 1 14 1T18 7L25 11 28 28 22 29 19 18 19 31 9 31 9 18 6 29 1 28 3 11Z',hint:'Adjust the body and sleeves. Hood, cuffs, pocket and drawstrings follow the garment.'},
 {id:'jersey',name:'Sport jersey',short:'JERSEY',icon:'M3 10 10 6 14 11 18 6 25 10 22 18 18 16 18 29 10 29 10 16 6 18ZM12 8 14 13 16 8',hint:'Create a jersey silhouette with adjustable width, body length, and short sleeves.'},
 {id:'jacket',name:'Bomber jacket',short:'JACKET',icon:'M11 4 14 6 17 4 24 9 28 27 22 28 19 18 19 30 9 30 9 18 6 28 1 27 4 9ZM14 6 14 30',hint:'A zip-front jacket with ribbed trims. Adjust the body width, length and sleeves.'},
 {id:'crop',name:'Cropped tee',short:'CROP TOP',icon:'M3 10 10 6 14 9 18 6 25 10 22 18 18 15 18 23 10 23 10 15 6 18Z',hint:'Explore cropped proportions. The third slider controls the sleeve length.'},
 {id:'tank',name:'Tank top',short:'TANK',icon:'M9 4 12 4Q14 11 16 4L19 4Q18 13 22 16L21 30 7 30 6 16Q10 13 9 4Z',hint:'A sleeveless silhouette. Width changes fit, length changes the hem, and depth changes the volume.'},
 {id:'jeans',name:'Wide-leg jeans',short:'JEANS',icon:'M8 3 21 3 24 30 16 30 14 13 12 30 4 30ZM8 7 21 7M14 3 14 12',hint:'Width changes leg volume. Length changes the inseam visually. Flare changes the hem opening.'},
 {id:'cargo',name:'Cargo pants',short:'CARGOS',icon:'M8 3 21 3 24 30 16 30 14 13 12 30 4 30ZM5 15 11 15 11 20 5 20M18 15 23 15 23 20 18 20',hint:'Adjust width, leg length and hem flare. Secondary color controls the utility pockets.'},
 {id:'shorts',name:'Utility shorts',short:'SHORTS',icon:'M7 5 22 5 25 25 16 25 14 14 12 25 3 25ZM7 9 22 9M14 5 14 14',hint:'Width changes fit. Length changes the leg length. Flare changes the hem opening.'},
 {id:'skirt',name:'A-line skirt',short:'SKIRT',icon:'M10 4 19 4 26 29 3 29ZM9 8 20 8',hint:'Width changes the waist silhouette. Length changes the hem. Flare changes the A-line shape.'},
 {id:'dress',name:'Streetwear dress',short:'DRESS',icon:'M10 2 13 2 14 6 16 2 19 2 19 10 17 14 26 30 3 30 11 14 9 10Z',hint:'An editable bodice and skirt. Front/back artwork covers the bodice; left/right covers skirt panels.'},
 {id:'boots',name:'Platform boots',short:'BOOTS',icon:'M7 3 18 3 17 19Q27 20 27 27L3 27 3 22 7 19ZM3 28 27 28 27 31 3 31',hint:'Width changes the foot and shaft. Height changes the shaft. Depth changes the toe length.'},
 {id:'sweater',name:'Long-sleeve knit',short:'KNIT',icon:'M3 10 10 6Q14 12 18 6L25 10 28 28 22 29 18 17 18 30 10 30 10 17 6 29 1 28Z',hint:'Explore knit shapes with body width, body length and sleeve adjustments.'}
];
export const MATERIALS={cotton:{roughness:.95,metalness:0},jersey:{roughness:.72,metalness:0},denim:{roughness:1,metalness:0},nylon:{roughness:.32,metalness:.08},leather:{roughness:.4,metalness:.04},metallic:{roughness:.26,metalness:.78}};
function surface(rows,columns,fn){const positions=[],uvs=[],indices=[];for(let j=0;j<=rows;j++){for(let i=0;i<=columns;i++){const u=i/columns,v=j/rows,p=fn(u,v);positions.push(...p.slice(0,3));uvs.push(...(p.length>3?p.slice(3,5):[u,v]));}}for(let j=0;j<rows;j++)for(let i=0;i<columns;i++){const a=j*(columns+1)+i,b=a+1,c=a+columns+1,d=c+1;indices.push(a,b,d,a,d,c);}const g=new THREE.BufferGeometry();g.setAttribute('position',new THREE.Float32BufferAttribute(positions,3));g.setAttribute('uv',new THREE.Float32BufferAttribute(uvs,2));g.setIndex(indices);g.computeVertexNormals();return g;}
function line(points,color,radius=.007){return new THREE.Mesh(new THREE.TubeGeometry(new THREE.CatmullRomCurve3(points.map(p=>new THREE.Vector3(...p))),Math.max(16,points.length*4),radius,5,false),new THREE.MeshStandardMaterial({color,roughness:.9}));}
export function makeGarment(state,textures){
 const group=new THREE.Group();group.name=state.name||'K3TEL Design';
 const F=state.fit/100,L=state.length/100,S=state.sleeve/100;
 const params=MATERIALS[state.material]||MATERIALS.cotton;
 const mats={};for(const side of ['front','back','left','right']){mats[side]=new THREE.MeshStandardMaterial({...params,map:textures[side],side:THREE.DoubleSide});mats[side].name=side+' surface';}
 const trim=new THREE.MeshStandardMaterial({...params,color:state.trim});
 const secondary=new THREE.MeshStandardMaterial({...params,color:state.secondary,side:THREE.DoubleSide});
 const dark=new THREE.MeshStandardMaterial({color:'#151c18',roughness:.9});
 const mesh=(geometry,material,name,parent=group)=>{const m=new THREE.Mesh(geometry,material);m.name=name;m.castShadow=true;m.receiveShadow=true;parent.add(m);return m;};
 const ring=(rx,rz,y,color=state.trim,parent=group)=>{const pts=[];for(let i=0;i<=64;i++){const a=i/64*Math.PI*2;pts.push([Math.cos(a)*rx,y,Math.sin(a)*rz]);}const m=line(pts,color,.012);parent.add(m);return m;};
 const seam=(points,parent=group,color=state.trim,r=.004)=>{const m=line(points,color,r);parent.add(m);return m;};
 const tube=(cx,top,bottom,rt,rb,depth,frontMat=mats.front,backMat=mats.back,name='panel',uvBounds={minX:-.85,maxX:.85,minY:-1.25,maxY:1})=>{
  for(const back of [false,true])mesh(surface(36,32,(u,v)=>{const angle=(back?Math.PI:0)+u*Math.PI;const y=bottom+(top-bottom)*v;const radius=rb+(rt-rb)*v;const x=cx+Math.cos(angle)*radius;const z=Math.sin(angle)*depth*(.95+.05*Math.cos(v*Math.PI));const uvx=(x-uvBounds.minX)/(uvBounds.maxX-uvBounds.minX);return[x,y,z,back?1-uvx:uvx,(y-uvBounds.minY)/(uvBounds.maxY-uvBounds.minY)];}),back?backMat:frontMat,name+(back?' back':' front'));
 };
 function upper(kind,parent=group){
  const cropped=kind==='crop',sleeveless=kind==='tank'||kind==='dress';
  const W=(sleeveless?.53:.69)*F, bottom=(cropped?-.52:-1.02)*L, neck=(sleeveless?.235:.245)*Math.min(F,1.2),D=(sleeveless?.20:.25)*(kind==='tank'?S:1);
  const topAt=(x,back)=>{const k=Math.abs(x);return k<neck?.93-(back?.065:.23)*Math.sqrt(Math.max(0,1-(x/neck)**2)):.93-.12*(k-neck)/Math.max(.01,W-neck);};
  const point=(u,v,back)=>{const x=(u*2-1)*W*(.94+.06*v+.025*Math.sin(v*Math.PI));const y=bottom+(topAt(x,back)-bottom)*v;const d=D*Math.sqrt(Math.max(.08,1-(x/W)**2*.72));const wrinkles=.006*Math.sin(x*35+y*14)*Math.sin(v*Math.PI);return[x,y,(back?-1:1)*(d+wrinkles),back?1-u:u,v];};
  for(const back of [false,true])mesh(surface(48,48,(u,v)=>point(u,v,back)),back?mats.back:mats.front,'body '+(back?'back':'front'),parent);
  for(const side of [0,1])mesh(surface(24,8,(u,v)=>{const a=point(side,v,false),b=point(side,v,true);return[a[0],a[1],a[2]+(b[2]-a[2])*u,u,v];}),secondary,'side seam',parent);
  for(const side of [-1,1])mesh(surface(8,24,(u,v)=>{const x=side*(neck+(W-neck)*u),nx=(x/W+1)/2,a=point(nx,1,false),b=point(nx,1,true);return[x,a[1]+(b[1]-a[1])*v,a[2]+(b[2]-a[2])*v,u,v];}),secondary,'shoulder bridge',parent);
  const collar=[];for(let i=0;i<=72;i++){const a=i/72*Math.PI*2;collar.push([neck*Math.cos(a),.93-(Math.sin(a)>0?.23:.065)*Math.abs(Math.sin(a)),D*Math.sqrt(Math.max(.08,1-(neck*Math.cos(a)/W)**2*.72))*Math.sin(a)]);}seam(collar,parent,state.trim,kind==='jersey'?.022:.018);
  const hem=[];for(let i=0;i<=64;i++){const a=i/64*Math.PI*2;hem.push([W*.94*Math.cos(a),bottom+.015,D*Math.sin(a)*.54]);}if(state.seams)seam(hem,parent,state.trim,kind==='jacket'?.035:.008);
  if(!sleeveless){for(const sign of [-1,1]){
   const long=['hoodie','jacket','sweater'].includes(kind), len=(long?1.02:.48)*S;
   const start=new THREE.Vector3(sign*(W-.14),.65,0),end=new THREE.Vector3(sign*(W+len*.65),.65-len*.9,0),axis=end.clone().sub(start).normalize();
   const tangent=new THREE.Vector3(-axis.y,axis.x,0).normalize();
   const radStart=.30,radEnd=long?.135:.22;
   const sleeveMat=sign<0?mats.left:mats.right;
   mesh(surface(30,40,(u,v)=>{const a=u*Math.PI*2,center=start.clone().lerp(end,v),r=radStart+(radEnd-radStart)*v;const p=center.addScaledVector(tangent,Math.cos(a)*r).add(new THREE.Vector3(0,0,Math.sin(a)*r*.87));return[p.x,p.y,p.z,u,1-v];}),sleeveMat,sign<0?'left sleeve':'right sleeve',parent);
   if(state.seams){const cuff=[];for(let i=0;i<=48;i++){const a=i/48*Math.PI*2,p=end.clone().addScaledVector(tangent,Math.cos(a)*radEnd).add(new THREE.Vector3(0,0,Math.sin(a)*radEnd*.87));cuff.push([p.x,p.y,p.z]);}seam(cuff,parent,state.trim,long?.024:.008);}
  }}
  if(kind==='hoodie'){
   mesh(surface(32,44,(u,v)=>{const a=u*Math.PI,theta=.06+v*1.72;return[.38*F*Math.cos(a)*Math.sin(theta),.93+.58*Math.cos(theta),-.04-.38*Math.sin(a)*Math.sin(theta),u,1-v];}),secondary,'hood',parent);
   const edge=[];for(let i=0;i<=48;i++){const a=i/48*Math.PI;edge.push([.38*F*Math.cos(a),.93+.58*Math.sin(a),-.035]);}if(state.seams)seam(edge,parent,state.trim,.011);
   const pocket=mesh(new THREE.BoxGeometry(.75*F,.29,.025),secondary,'kangaroo pocket',parent);pocket.position.set(0,bottom+.39,D+.01);
   if(state.seams){seam([[-.37*F,bottom+.52,D+.03],[-.26*F,bottom+.25,D+.03],[.26*F,bottom+.25,D+.03],[.37*F,bottom+.52,D+.03]],parent);for(const sign of [-1,1])seam([[sign*.12,.76,D+.015],[sign*.13,.43,D+.04]],parent,state.trim,.009);}
  }
  if(kind==='jacket'&&state.seams){seam([[0,.72,D+.015],[0,bottom+.05,D+.018]],parent,state.trim,.012);const zip=mesh(new THREE.BoxGeometry(.04,.075,.02),trim,'zipper pull',parent);zip.position.set(.025,.52,D+.035);for(const sign of [-1,1])seam([[sign*.32,-.2,D*.95],[sign*.4,-.55,D*.95]],parent,state.trim,.009);}
 }
 function lower(kind){
  const shorts=kind==='shorts',width=.69*F,top=1.0,bottom=shorts?-.05*L:-1.15*L;
  tube(0,top,.48,width,width*.91,.26,mats.front,mats.back,'waist');
  for(const sign of [-1,1]){
   const cx=sign*width*.5,rt=width*.51,rb=rt*(kind==='cargo'?.95:1.0)*(S*.6+.4);
   tube(cx,.58,bottom,rt,rb,.23,mats.front,mats.back,sign<0?'left leg':'right leg');
   if(state.seams){seam([[cx+sign*rt,.56,0],[cx+sign*rb,bottom,0]],group,state.trim);ring(rb,.23,bottom+.02,state.trim).position.x=cx;}
   if(kind==='cargo'){const pocket=mesh(new THREE.BoxGeometry(rt*.9,.35,.045),secondary,'cargo pocket');pocket.position.set(cx+sign*.1,.13,.23);const flap=mesh(new THREE.BoxGeometry(rt*.94,.075,.055),trim,'cargo flap');flap.position.set(cx+sign*.1,.29,.24);}
   if(state.seams){seam([[cx-.12,.85,-.27],[cx-.1,.63,-.27],[cx+.1,.6,-.27],[cx+.12,.85,-.27]],group,state.trim,.006);}
  }
  ring(width,.265,.96,state.trim);if(state.seams){for(let i=0;i<7;i++){const a=i/7*Math.PI*2;const loop=mesh(new THREE.BoxGeometry(.055,.12,.027),trim,'belt loop');loop.position.set(Math.cos(a)*width,.94,Math.sin(a)*.267);loop.rotation.y=Math.PI/2-a;}seam([[0,.96,.273],[0,.64,.273]],group,state.trim,.007);}
 }
 function skirt(dress=false){const top=dress?.35:.85,bottom=dress?-1.15*L:-.8*L,wt=(dress?.52:.55)*F,wb=wt*(1+S*.6),fm=dress?mats.left:mats.front,bm=dress?mats.right:mats.back;for(const back of [false,true])mesh(surface(40,48,(u,v)=>{const a=(back?Math.PI:0)+u*Math.PI,wr=wb+(wt-wb)*v,pleat=.015*Math.cos(a*16)*(1-v);return[Math.cos(a)*(wr+pleat),bottom+(top-bottom)*v,Math.sin(a)*(.28+(1-v)*.08+pleat),back?1-u:u,v];}),back?bm:fm,'skirt '+(back?'back':'front'));ring(wt,.28,top,state.trim);if(state.seams)ring(wb,.36,bottom+.02,state.trim);}
 function boots(){for(const sign of [-1,1]){
  const parent=new THREE.Group();parent.position.x=sign*.4*F;group.add(parent);parent.name=sign<0?'left boot':'right boot';
  const shaft=mesh(new THREE.CylinderGeometry(.23*F,.2*F,.95*L,36,20,true),sign<0?mats.left:mats.right,'boot shaft',parent);shaft.position.y=.1+.475*L;
  const foot=mesh(new THREE.SphereGeometry(1,40,24),sign<0?mats.front:mats.back,'boot toe',parent);foot.scale.set(.27*F,.28,.57*S);foot.position.set(0,-.03,.22*S);
  const soleShape=new THREE.Shape();soleShape.moveTo(-.28*F,-.3*S);soleShape.lineTo(-.3*F,.49*S);soleShape.quadraticCurveTo(0,.83*S,.3*F,.49*S);soleShape.lineTo(.28*F,-.3*S);soleShape.quadraticCurveTo(0,-.42*S,-.28*F,-.3*S);
  const sole=mesh(new THREE.ExtrudeGeometry(soleShape,{depth:.14,bevelEnabled:true,bevelSegments:3,steps:1,bevelSize:.025,bevelThickness:.025}),trim,'platform sole',parent);sole.rotation.x=Math.PI/2;sole.position.y=-.23;
  ring(.234*F,.234*F,.1+.95*L,state.trim,parent);
  if(state.seams){for(let i=0;i<7;i++){const y=.12+i*.105*L,z=.22;seam([[-.1*F,y,z],[.1*F,y+.07*L,z+.012]],parent,state.trim,.008);seam([[.1*F,y,z],[-.1*F,y+.07*L,z+.012]],parent,state.trim,.008);}}
 }group.position.y=-.25;}
 if(['jeans','cargo','shorts'].includes(state.garment))lower(state.garment);
 else if(state.garment==='skirt')skirt();
 else if(state.garment==='dress'){const bodice=new THREE.Group();group.add(bodice);upper('dress',bodice);bodice.scale.y=.53;bodice.position.y=.87;skirt(true);}
 else if(state.garment==='boots')boots();
 else upper(state.garment);
 group.userData={application:'K3TEL Studio',garment:state.garment,conceptOnly:true};return group;
}
export function disposeGarment(group){if(!group)return;const geometries=new Set(),materials=new Set();group.traverse(o=>{if(o.geometry)geometries.add(o.geometry);if(o.material)(Array.isArray(o.material)?o.material:[o.material]).forEach(m=>materials.add(m));});geometries.forEach(g=>g.dispose());materials.forEach(m=>m.dispose());}


