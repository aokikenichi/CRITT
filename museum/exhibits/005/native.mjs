// Derived by tests/extract-ten-exhibit-assets.py. Source HTML is preserved.
// See exhibition-assets/manifest.json for source blob and embedded image hashes.
export function createNative({THREE, scene, camera, renderer, assets, works, images, ui}) {
const $=ui;
let subjects=[],orb,lightThreads=[],relations=false;
const tloader=new THREE.TextureLoader(), tmap=new Map();
function tex(id){if(!tmap.has(id)){const t=tloader.load(assets[id]);t.colorSpace=THREE.SRGBColorSpace;t.anisotropy=8;tmap.set(id,t)}return tmap.get(id)}
function cylinder(x,z,r=0.12,h=1,material){const p=new THREE.Mesh(new THREE.CylinderGeometry(r,r,h,16),material);p.position.set(x,h/2,z);scene.add(p);return p}
function makeSubject(w){
 const root=new THREE.Group();root.position.set(w.x,0,w.z);root.rotation.y=w.ang;
 const h=w.h, width=h*w.aspect;
 const material=new THREE.MeshBasicMaterial({map:tex(w.id),transparent:true,side:THREE.DoubleSide,depthWrite:false,alphaTest:.025,toneMapped:false});
 const p=new THREE.Mesh(new THREE.PlaneGeometry(width,h),material);p.position.y=h/2+.22;root.add(p);
 // Echo is a very faint offset plane, not a pretend volumetric statue.
 const echo=new THREE.Mesh(new THREE.PlaneGeometry(width*1.015,h*1.015),new THREE.MeshBasicMaterial({map:tex(w.id),color:'#a8bfaf',opacity:.13,transparent:true,side:THREE.DoubleSide,depthWrite:false,alphaTest:.018,toneMapped:false}));echo.position.set(.16,h/2+.22,-.26);root.add(echo);
 // minimal wires at edges, as a museum installation support, mostly invisible
 const fibre=new THREE.MeshBasicMaterial({color:'#7d9184',transparent:true,opacity:.22,depthWrite:false});
 for(const ox of [-width*.38,width*.38]){let wire=new THREE.Mesh(new THREE.CylinderGeometry(.004,.004,Math.max(1,h*.8),6),fibre);wire.position.set(ox,h*.55,-.17);root.add(wire)}
 const light=new THREE.PointLight('#d5aa70',w.id==='01'||w.id==='10'?10:4,4.8,2);light.position.set(0,h*.6,-.1);root.add(light);
 scene.add(root);subjects.push({root,work:w});
}
function makeConstellation(){
 const ballMat=new THREE.MeshStandardMaterial({color:'#f8f5e9',roughness:.68,metalness:0,emissive:'#fff3cf',emissiveIntensity:.18});
 orb=new THREE.Mesh(new THREE.SphereGeometry(.15,38,24),ballMat);orb.position.set(0,3.5,0);scene.add(orb);
 const lamp=new THREE.PointLight('#e9bd77',11,10);orb.add(lamp);
 const mat=new THREE.LineBasicMaterial({color:'#d5a878',transparent:true,opacity:0,depthWrite:false});
 for(const w of works){
  const start=new THREE.Vector3(0,3.5,0), end=new THREE.Vector3(w.x,w.h*.58+.2,w.z);
  const midpoint=start.clone().lerp(end,.5).add(new THREE.Vector3(0,1.05,0));
  const curve=new THREE.QuadraticBezierCurve3(start,midpoint,end);
  const path=new THREE.Line(new THREE.BufferGeometry().setFromPoints(curve.getPoints(28)),mat.clone());scene.add(path);lightThreads.push(path);
 }
}

works.forEach(makeSubject);makeConstellation();return {update(dt){const d=Math.hypot(camera.position.x,camera.position.z),tgt=relations?(.13+.23*Math.max(0,1-d/12)):0;for(const l of lightThreads)l.material.opacity+=(tgt-l.material.opacity)*Math.min(1,dt*3.5)},set(name,value){if(name==='relations')relations=value},stats(){return {bodies:subjects.length,relations}}};

}
