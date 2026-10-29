import * as T from '../vendor/three-0.180.0/three.module.min.js';
import {FLOORS,WALLS,ROOMS,WORKS} from './gallery-model.mjs';
export function createScene(host,onFailure){
 const renderer=new T.WebGLRenderer({antialias:true,alpha:false});
 renderer.setPixelRatio(Math.min(devicePixelRatio,1.5));renderer.outputColorSpace=T.SRGBColorSpace;
 renderer.setClearColor(0xe8e8df);host.append(renderer.domElement);
 const scene=new T.Scene();scene.background=new T.Color('#e8e8df');scene.fog=new T.Fog('#e8e8df',35,100);
 const camera=new T.PerspectiveCamera(65,1,.08,130);camera.rotation.order='YXZ';
 const ivory=new T.MeshStandardMaterial({color:0xe9e6db,roughness:.88});
 const stone=new T.MeshStandardMaterial({color:0xc4c3b5,roughness:.7});
 const brass=new T.MeshStandardMaterial({color:0x917243,metalness:.55,roughness:.5});
 function box(x,y,z,w,h,d,mat){const o=new T.Mesh(new T.BoxGeometry(w,h,d),mat);o.position.set(x,y,z);scene.add(o);return o;}
 const mat=c=>new T.MeshStandardMaterial({color:c,roughness:.78});
 scene.add(new T.HemisphereLight(0xfff9e9,0x747e70,2.6));
 const sun=new T.DirectionalLight(0xfff4d8,2.8);sun.position.set(-8,18,8);scene.add(sun);
 for(const f of FLOORS){box((f.x1+f.x2)/2,-.12,(f.z1+f.z2)/2,f.x2-f.x1,.24,f.z2-f.z1,f.id?mat(new T.Color(f.color).lerp(new T.Color('#e5e4d9'),.72)):stone);}
 for(const w of WALLS)box((w.x1+w.x2)/2,w.h/2,(w.z1+w.z2)/2,w.x2-w.x1,w.h,w.z2-w.z1,ivory);
 // Recessed ceiling strips, thresholds and floor joints unify the building.
 const glow=new T.MeshBasicMaterial({color:0xfff5d5});
 for(let z=4;z>-58;z-=6){box(0,5.03,z,5.6,.12,1.3,ivory);box(0,4.94,z,3.8,.035,.16,glow);box(0,.012,z,5.6,.018,.025,mat(0xadae9f));}
 for(const r of ROOMS){
  const floorColor=new T.Color(r.color);
  box(r.cx,r.height+.08,r.cz,r.x2-r.x1,.16,r.z2-r.z1,mat(0xe3e2d7));
  // Broad skylight coffer with softly coloured reveal.
  box(r.cx,r.height-.05,r.cz,(r.x2-r.x1)*.64,.12,(r.z2-r.z1)*.6,mat(floorColor));
  box(r.cx,r.height-.13,r.cz,(r.x2-r.x1)*.57,.03,(r.z2-r.z1)*.53,new T.MeshBasicMaterial({color:0xfff9e7}));
  const lamp=new T.PointLight(0xfff4df,35,23,2);lamp.position.set(r.cx,r.height-1,r.cz);scene.add(lamp);
  for(let z=r.z1+2;z<r.z2;z+=2)box(r.cx,.01,z,r.x2-r.x1,.01,.018,mat(floorColor.clone().lerp(new T.Color('#e5e4d9'),.5)));
  const doorX=r.id===5?0:(r.cx<0?-3:3), doorZ=r.id===5?-58:r.cz;
  if(r.id<5){box(doorX,3.45,doorZ,.35,.16,4.2,brass);box(doorX,.014,doorZ,.6,.025,3.9,brass);}
  else{box(0,4,-58,4.2,.16,.35,brass);box(0,.014,-58,3.9,.025,.6,brass);}
  // Architectural seating stays against a wall, away from the walking route.
  const bx=r.id===5?0:r.cx,bz=r.id===5?-74:r.z1+1;
  box(bx,.28,bz,2.4,.55,.65,mat(0x91877a));
  sign(`${String(r.id).padStart(2,'0')}  /  ${r.name}`,r.id===5?0:doorX,r.id===5?4.6:3.95,r.id===5?-58.2:doorZ,r.id===5?0:(r.cx<0?Math.PI/2:-Math.PI/2),3.5,.55,'#f2f0e6','#2e3c34');
 }
 function textureText(lines,bg,fg){const c=document.createElement('canvas');c.width=1024;c.height=256;const ctx=c.getContext('2d');ctx.fillStyle=bg;ctx.fillRect(0,0,c.width,c.height);ctx.fillStyle=fg;ctx.textAlign='center';ctx.textBaseline='middle';lines.forEach((line,i)=>{ctx.font=`${i===0?46:25}px sans-serif`;ctx.fillText(line,512,lines.length===1?128:80+i*75,980)});const t=new T.CanvasTexture(c);t.colorSpace=T.SRGBColorSpace;return t;}
 function sign(text,x,y,z,rot,w,h,bg='#eceadd',fg='#26372f'){
  const mesh=new T.Mesh(new T.PlaneGeometry(w,h),new T.MeshBasicMaterial({map:textureText(Array.isArray(text)?text:[text],bg,fg),side:T.DoubleSide}));mesh.position.set(x,y,z);mesh.rotation.y=rot;scene.add(mesh);return mesh;
 }
 sign(['BEYOND THE BOUNDARY','CRITT MUSEUM  /  5 ROOMS · 10 WORKS'],0,3.3,-1.82,0,5.4,1.35);
 sign(['01—05  →','展示室へ / GALLERIES'],0,.025,2,-Math.PI/2,2,1).rotation.set(-Math.PI/2,0,0);
 for(const x of [-6,6]){box(x,3.2,3,.45,6.4,.55,ivory);box(x,3.2,9,.45,6.4,.55,ivory);box(x,6.25,6,.65,.35,7,brass);}
 const textures=new T.TextureLoader();
 for(const w of WORKS){
  const g=new T.Group();g.position.set(w.x,0,w.z);g.rotation.y=w.yaw;scene.add(g);
  const add=(mesh,x,y,z)=>{mesh.position.set(x,y,z);g.add(mesh);return mesh;};
  add(new T.Mesh(new T.BoxGeometry(4.6,3.5,.15),mat(ROOMS[w.room-1].color)),0,2.5,0);
  add(new T.Mesh(new T.BoxGeometry(4.3,3.12,.12),mat(0x3b4038)),0,2.57,.12);
  // Existing QA images are display previews only, never registered as originals.
  const preview=new T.MeshBasicMaterial({color:0xe1dfd3});
  add(new T.Mesh(new T.PlaneGeometry(4.12,2.86),preview),0,2.57,.19);
  textures.load(w.preview,t=>{t.colorSpace=T.SRGBColorSpace;preview.map=t;preview.color.set(0xffffff);preview.needsUpdate=true;},undefined,()=>{preview.color.set(0x879582);});
  add(new T.Mesh(new T.PlaneGeometry(4.5,.72),new T.MeshBasicMaterial({map:textureText([`${w.id}  ${w.title}`,'作品プレビュー / 制作中'], '#eeece1','#24392e')})),0,.65,.2);
  add(new T.Mesh(new T.BoxGeometry(4.7,.12,.3),brass),0,4.3,.15);
  add(new T.Mesh(new T.BoxGeometry(4.8,.18,.6),mat(0xc4c1b1)),0,.09,.25);
  const ring=new T.Mesh(new T.RingGeometry(.28,.33,48),new T.MeshBasicMaterial({color:0x977344,side:T.DoubleSide}));ring.rotation.x=-Math.PI/2;ring.position.set(w.spot.x,.025,w.spot.z);scene.add(ring);
 }
 function resize(){const {width,height}=host.getBoundingClientRect();renderer.setSize(width,height,false);camera.aspect=width/Math.max(1,height);camera.updateProjectionMatrix();}
 const observer=new ResizeObserver(resize);observer.observe(host);resize();
 renderer.domElement.addEventListener('webglcontextlost',e=>{e.preventDefault();onFailure('3D描画が中断しました。館内図から作品を選択できます。');});
 return {render(p){camera.position.set(p.x,1.65,p.z);camera.rotation.set(p.pitch,p.yaw,0);renderer.render(scene,camera);},dispose(){observer.disconnect();scene.traverse(o=>{o.geometry?.dispose();if(o.material){for(const m of [].concat(o.material)){m.map?.dispose();m.dispose();}}});renderer.dispose();}};
}
