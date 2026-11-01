import * as THREE from '../../vendor/three-0.180.0/three.module.min.js';
export {THREE};
export async function json(path){const r=await fetch(path);if(!r.ok)throw new Error(`${path}: HTTP ${r.status}`);return r.json()}
export function texture(path){const t=new THREE.TextureLoader().load(path);t.colorSpace=THREE.SRGBColorSpace;t.anisotropy=4;return t}
export function line(points,color=0xe7c58b,opacity=1){return new THREE.Line(new THREE.BufferGeometry().setFromPoints(points.map(p=>new THREE.Vector3(...p))),new THREE.LineBasicMaterial({color,transparent:opacity<1,opacity,depthWrite:opacity===1}))}
export function plane(path,w,h,opacity=1){return new THREE.Mesh(new THREE.PlaneGeometry(w,h),new THREE.MeshBasicMaterial({map:texture(path),transparent:true,opacity,alphaTest:.015,side:THREE.DoubleSide,depthWrite:opacity>.8,toneMapped:false}))}
export function label(text,w=5,h=.65){const c=document.createElement('canvas');c.width=1024;c.height=128;const x=c.getContext('2d');x.clearRect(0,0,1024,128);x.fillStyle='#e7d7b7';x.font='38px sans-serif';x.textAlign='center';x.fillText(text,512,80);const m=new THREE.Mesh(new THREE.PlaneGeometry(w,h),new THREE.MeshBasicMaterial({map:new THREE.CanvasTexture(c),transparent:true,side:THREE.DoubleSide,depthWrite:false}));return m}
export function makeAdapter(meta,build){
 const root=new THREE.Group();root.name=`exhibit-${meta.id}`;
 let context,native,source,loaded=false,entered=false;
 const localCamera={position:new THREE.Vector3(),quaternion:new THREE.Quaternion(),projectionMatrix:new THREE.Matrix4(),matrixWorldInverse:new THREE.Matrix4()};
 const scratch=new THREE.Matrix4(),scale=new THREE.Vector3();const nodes=new Map();
 const ui=s=>{if(!nodes.has(s))nodes.set(s,document.createElement('div'));return nodes.get(s)};
 const api={...meta,root,images:[],
 async mount(ctx){context=ctx;source=await json(`exhibition-assets/${meta.id}/data.json`);api.images=ctx.manifest.items.find(e=>e.id===meta.id).images.filter(i=>!(meta.id==='001'&&![1,2,9].includes(i.index))&&!(meta.id==='002'&&![3,4,5,6,7,8].includes(i.index)));
 native=await build({THREE,scene:root,camera:localCamera,renderer:ctx.renderer,assets:source.assets||source['image-assets'],works:source.workdata||source.works,images:source['image-assets'],data:source,ui,texture,plane,line,label});
 // Source artworks keep their geometry and images. Shared hall owns enclosing
 // walls, ambient illumination and input. Limit source point lights across rooms.
 let points=0;const remove=[];root.traverse(o=>{if(o.isLight){if(!['006','007'].includes(meta.id)||(!o.isPointLight)||(points++>=(meta.id==='006'?2:3)))remove.push(o)}});remove.forEach(o=>o.removeFromParent());
 root.position.fromArray(meta.origin);root.scale.setScalar(meta.scale||1);ctx.scene.add(root);root.updateMatrixWorld(true);loaded=true;return api},
 enter(){entered=true;native?.enter?.()},leave(){entered=false;native?.leave?.()},
 update(dt,now){if(!loaded)return;root.updateMatrixWorld(true);scratch.copy(root.matrixWorld).invert().multiply(context.camera.matrixWorld);scratch.decompose(localCamera.position,localCamera.quaternion,scale);localCamera.matrixWorldInverse.copy(scratch).invert();localCamera.projectionMatrix.copy(context.camera.projectionMatrix);if(root.visible)native?.update?.(dt,now)},
 set(name,value){native?.set?.(name,value)},loadJSON(...args){return native?.loadJSON?.(...args)},loadZIP(...args){return native?.loadZIP?.(...args)},
 stats(){let meshes=0,vertices=0;root.traverse(o=>{if(o.isMesh||o.isPoints||o.isLine){meshes++;vertices+=o.geometry?.attributes.position?.count||o.geometry?.attributes.aPos?.count||0}});return {id:meta.id,loaded,entered,visible:root.visible,objects:meshes,vertices,...native?.stats?.()}},
 dispose(){native?.dispose?.();const textures=new Set();root.traverse(o=>{o.geometry?.dispose();for(const m of [o.material].flat().filter(Boolean)){for(const v of Object.values(m)){if(v?.isTexture)textures.add(v)}m.dispose()}});textures.forEach(t=>t.dispose());root.removeFromParent();nodes.clear();loaded=false}
 };return api;
}
