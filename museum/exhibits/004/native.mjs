// Derived by tests/extract-ten-exhibit-assets.py. Source HTML is preserved.
// See exhibition-assets/manifest.json for source blob and embedded image hashes.
export function createNative({THREE, scene, camera, renderer, assets, works, images, ui}) {
const $=ui;
let artworks=[],sightMarkers=[];
const sightStops=[
 {x:6.7,z:11.8,lookX:4.5,lookZ:1.6,name:'受け渡された形と、溶けゆく形',works:'02《接ぎ木》＋05《溶解》'},
 {x:-6.8,z:5.4,lookX:-4.9,lookZ:-4.8,name:'硬い道具と、柔らかな抵抗',works:'04《柔らかな反撃》＋07《寄せ集めの発明》'},
 {x:-3.5,z:0.7,lookX:-1.3,lookZ:-8.1,name:'不在と、その後に残る響き',works:'06《不在の打者》＋09《打撃の残響》'}
];
const sightTrail=[{x:0,z:16.3}, {x:6.7,z:11.8}, {x:4,z:8.7}, {x:0,z:8.4}, {x:-6.8,z:5.4}, {x:-5.8,z:2.7}, {x:-3.5,z:0.7}, {x:-2.6,z:-4.8}, {x:0,z:-11.8}, {x:0,z:-17.1}];
const sightLabels=['出発','視点1','通路','通路','視点2','通路','視点3','通路','通路','終点'];
const sightLegHold=[0,7,0,0,7,0,8,0,0,8];
const sightLegDuration=[0,8,5,5,8,6,5,8,12,10];

const textureLoader=new THREE.TextureLoader(),memo=new Map();
function texture(key){if(!memo.has(key)){let t=textureLoader.load(assets[key]);t.colorSpace=THREE.SRGBColorSpace;t.anisotropy=8;memo.set(key,t)}return memo.get(key)}
function boardTexture(num,title){const c=document.createElement('canvas');c.width=960;c.height=270;const x=c.getContext('2d');x.fillStyle='#e7e3d9';x.fillRect(0,0,960,270);x.fillStyle='#293d38';x.font='30px Georgia, serif';x.fillText(num,35,60);x.fillRect(38,78,145,2);x.font='bold 50px sans-serif';x.fillText(title,35,157);x.font='21px Georgia, serif';x.fillText('CRITT / WORK 04 — photographic layer',35,220);const t=new THREE.CanvasTexture(c);t.colorSpace=THREE.SRGBColorSpace;return t}
function beam(x,y,z,w,h,d,mat){let mesh=new THREE.Mesh(new THREE.BoxGeometry(w,h,d),mat);mesh.position.set(x,y,z);scene.add(mesh);return mesh}
function buildArchitecture(){
 const plaster=new THREE.MeshStandardMaterial({color:'#deded7',roughness:.96}), stone=new THREE.MeshStandardMaterial({color:'#c6c5bb',roughness:.82,metalness:.06}),rail=new THREE.MeshStandardMaterial({color:'#c9c4b8',roughness:.4,metalness:.4});
 const floor=new THREE.Mesh(new THREE.PlaneGeometry(27,46),stone);floor.rotation.x=-Math.PI/2;floor.position.set(0,-.03,-3.8);scene.add(floor);
 beam(-13.5,5,-3.8,.4,10.1,46,plaster);beam(13.5,5,-3.8,.4,10.1,46,plaster);beam(0,5,-26.8,27,10.1,.4,plaster);
 // entrance returns, leave a generous central opening
 beam(-9.8,5,19.1,7.4,10.1,.35,plaster);beam(9.8,5,19.1,7.4,10.1,.35,plaster);
 // colonnade, above head height so artworks remain primary
 for(let z=12;z>=-21;z-=7.5){for(let x of [-11.4,11.4]){let col=beam(x,4.9,z,.42,9.8,.48,plaster);col.castShadow=false;}}
 for(let z=17;z>=-24;z-=5.3){beam(0,9.75,z,26.2,.22,.24,rail);}
 for(let x of [-8.7,-4.4,0,4.4,8.7])beam(x,9.76,-3.7,.16,.22,45.5,rail);
 const glass=new THREE.MeshPhysicalMaterial({color:'#f8ffff',transparent:true,opacity:.22,roughness:.16,metalness:0,depthWrite:false,side:THREE.DoubleSide});
 for(let x of [-6.5,0,6.5]){const p=new THREE.Mesh(new THREE.PlaneGeometry(5.85,43),glass);p.rotation.x=-Math.PI/2;p.position.set(x,9.8,-3.8);scene.add(p)}
 // in-world entrance wall graphic (not screen overlay)
 const logo=boardTexture('CRITT','ROOM 02 / 11 WORKS');const panel=new THREE.Mesh(new THREE.PlaneGeometry(4.6,1.3),new THREE.MeshBasicMaterial({map:logo}));panel.position.set(-9.7,3.1,18.87);scene.add(panel);
 const slats=new THREE.MeshStandardMaterial({color:'#d0cfc5',roughness:.92});
 for(let z=-23;z<18;z+=5){for(let x of [-12.8,12.8]){beam(x,.03,z,1.2,.05,.07,slats)}}
}
function halo(x,z,scale=1,tint='#d6cbbb'){
 const c=document.createElement('canvas');c.width=c.height=128;const ctx=c.getContext('2d');const grad=ctx.createRadialGradient(64,64,0,64,64,64);grad.addColorStop(0,'rgba(66,62,52,.28)');grad.addColorStop(.45,'rgba(72,67,60,.09)');grad.addColorStop(1,'rgba(72,67,60,0)');ctx.fillStyle=grad;ctx.fillRect(0,0,128,128);
 const t=new THREE.CanvasTexture(c),m=new THREE.Mesh(new THREE.PlaneGeometry(2.8*scale,1.4*scale),new THREE.MeshBasicMaterial({map:t,transparent:true,depthWrite:false,opacity:.85}));m.rotation.x=-Math.PI/2;m.position.set(x,.012,z);scene.add(m);
}
function addScrim(w){const g=new THREE.Group();g.position.set(w.x,0,w.z);g.rotation.y=w.ang;
 const tex=texture(w.key), ratio=1000/633;
 const mesh=new THREE.Mesh(new THREE.PlaneGeometry(5.0,3.1),new THREE.MeshBasicMaterial({map:tex,transparent:true,opacity:.91,side:THREE.DoubleSide,depthWrite:false})); mesh.position.set(0,5.6,0);mesh.rotation.x=-.18;mesh.rotation.z=-.12;g.add(mesh);
 const echo=new THREE.Mesh(new THREE.PlaneGeometry(5.25,3.15),new THREE.MeshBasicMaterial({map:tex,transparent:true,opacity:.2,side:THREE.DoubleSide,depthWrite:false,color:'#e8d9c7'}));echo.position.set(-.22,5.7,-.43);echo.rotation.copy(mesh.rotation);g.add(echo);
 const threadMat=new THREE.MeshBasicMaterial({color:'#b0a38d'});
 for(let x of [-2.25,2.25]){let wire=new THREE.Mesh(new THREE.CylinderGeometry(.006,.006,5.5,6),threadMat);wire.position.set(x,7.05,.0);g.add(wire);}
 scene.add(g);halo(w.x,w.z,1.9);return g;
}
function addCutout(w){const root=new THREE.Group();root.position.set(w.x,0,w.z);root.rotation.y=w.ang;scene.add(root);
 const image=texture(w.key);const img=image.image || {};
 // read dimensions from pre-known image data after load; for immediate geometry use fixed aspect from metadata
 const ratio=w.aspect||.27;const h=w.h,width=h*ratio;
 const mesh=new THREE.Mesh(new THREE.PlaneGeometry(width,h),new THREE.MeshBasicMaterial({map:image,transparent:true,alphaTest:.06,side:THREE.DoubleSide,depthWrite:true}));mesh.position.set(0,h/2+.14,.08);root.add(mesh);
 const ghost=new THREE.Mesh(new THREE.PlaneGeometry(width*1.025,h*1.025),new THREE.MeshBasicMaterial({map:image,color:w.num==='11'?'#aac4c7':'#c9cfce',transparent:true,opacity:w.num==='06'?.24:.14,side:THREE.DoubleSide,depthWrite:false,alphaTest:.01}));ghost.position.set(.12,h/2+.15,-.23);root.add(ghost);
 // barely-visible supporting light rods: printed / cutout 2.5D artwork, never pretend solid sculpture
 const support=new THREE.MeshStandardMaterial({color:'#abb0aa',metalness:.48,roughness:.42});
 for(const sx of [-width*.37,width*.37]){const p=new THREE.Mesh(new THREE.CylinderGeometry(.012,.012,h*.73,7),support);p.position.set(sx,h*.37,-.14);root.add(p)}
 const foot=new THREE.Mesh(new THREE.BoxGeometry(Math.max(.7,width+.13),.055,.65),new THREE.MeshStandardMaterial({color:'#d2d2cb',roughness:.8}));foot.position.y=.029;root.add(foot);
 halo(w.x,w.z,1.45);
 if(w.num==='11'){const glow=new THREE.PointLight('#92c4b5',24,5);glow.position.set(0,h*.7,-.5);root.add(glow)}
 return root;
}
function addPlaque(w){const t=boardTexture(w.num,w.name),p=new THREE.Mesh(new THREE.PlaneGeometry(1.58,.46),new THREE.MeshBasicMaterial({map:t}));p.position.set(w.x+1.05,.58,w.z+1.2);p.rotation.y=-.12;scene.add(p);
 const m=new THREE.Mesh(new THREE.CylinderGeometry(.016,.016,.56,6),new THREE.MeshStandardMaterial({color:'#9da49e',metalness:.4,roughness:.4}));m.position.set(w.x+1.05,.3,w.z+1.2);scene.add(m);
}
function addSightStations(){
 // Inlaid floor rings (not floating interface labels): optional viewing hints.
 const muted=new THREE.MeshBasicMaterial({color:'#93856d',transparent:true,opacity:.48,depthWrite:false});
 for(const spot of sightStops){
  const group=new THREE.Group();
  group.position.set(spot.x,.016,spot.z);
  const ring=new THREE.Mesh(new THREE.RingGeometry(.31,.325,52),muted.clone());
  ring.rotation.x=-Math.PI/2;group.add(ring);
  const center=new THREE.Mesh(new THREE.CircleGeometry(.018,18),muted.clone());center.rotation.x=-Math.PI/2;center.position.y=.002;group.add(center);
  // A tiny inlaid direction segment indicates the intended sightline.
  const a=Math.atan2(spot.lookX-spot.x,-(spot.lookZ-spot.z));
  const tick=new THREE.Mesh(new THREE.BoxGeometry(.035,.003,.21),muted.clone());tick.position.set(Math.sin(a)*.41,.002,-Math.cos(a)*.41);tick.rotation.y=a;group.add(tick);
  scene.add(group);sightMarkers.push({group,spot,ring});
 }
}
function spawn(){works.forEach(w=>{w.root=w.kind==='scrim'?addScrim(w):addCutout(w);addPlaque(w);artworks.push(w)});addSightStations();}

spawn();return {update(){for(const e of sightMarkers){const d=Math.hypot(camera.position.x-e.spot.x,camera.position.z-e.spot.z);e.ring.material.opacity=THREE.MathUtils.lerp(.35,.81,THREE.MathUtils.clamp(1-d/3,0,1))}},stats(){return {layers:artworks.length,stations:sightStops.length}}};

}
