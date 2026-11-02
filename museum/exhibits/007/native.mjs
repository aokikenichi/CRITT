// Derived by tests/extract-ten-exhibit-assets.py. Source HTML is preserved.
// See exhibition-assets/manifest.json for source blob and embedded image hashes.
export function createNative({THREE, scene, camera, renderer, assets, works, images, ui}) {
const $=ui;
const slices=assets.panels;let group,emptyGroup,ambient,lamps=[];
 const gold=0xc9a677,amber=0xd09c66;
 const warm1=new THREE.PointLight(0xffca8b,120,22,1.6);warm1.position.set(-7,7,3);scene.add(warm1);
 const warm2=new THREE.PointLight(0xffca8b,120,22,1.6);warm2.position.set(7,7,-3);scene.add(warm2);
 const quietLight=new THREE.PointLight(0xfff0d4,17,8,2);quietLight.position.set(0,5.1,0);scene.add(quietLight);
 const dark=new THREE.MeshStandardMaterial({color:0x161d1f,roughness:.94,metalness:.03});
 function box(pos,size,material,parent=scene){const m=new THREE.Mesh(new THREE.BoxGeometry(...size),material);m.position.set(...pos);parent.add(m);return m}
 const floor=new THREE.Mesh(new THREE.PlaneGeometry(54,54),new THREE.MeshStandardMaterial({color:0x152024,roughness:.34,metalness:.18}));floor.rotation.x=-Math.PI/2;scene.add(floor);
 // dark architectural shell and a restrained circular archive desk
 const circleM=new THREE.MeshStandardMaterial({color:0x272421,roughness:.53,metalness:.22});
 const rimM=new THREE.MeshStandardMaterial({color:0x8c6b42,roughness:.45,metalness:.45});
 const outerDesk=new THREE.Mesh(new THREE.TorusGeometry(6.9,.48,12,116),circleM);outerDesk.rotation.x=Math.PI/2;outerDesk.position.y=.88;scene.add(outerDesk);
 const deskRim=new THREE.Mesh(new THREE.TorusGeometry(6.9,.50,8,116),rimM);deskRim.rotation.x=Math.PI/2;deskRim.position.y=.92;deskRim.scale.set(1.005,1.005,1.005);deskRim.material.transparent=true;deskRim.material.opacity=.12;scene.add(deskRim);
 const centerCircle=new THREE.Mesh(new THREE.RingGeometry(2.15,2.17,100),new THREE.MeshBasicMaterial({color:0xbca078,transparent:true,opacity:.23,side:THREE.DoubleSide}));centerCircle.rotation.x=-Math.PI/2;centerCircle.position.y=.012;scene.add(centerCircle);
 // Subtle overhead brass runners; suspended works read as documents, not information panels.
 for(let i=-4;i<=4;i++){box([i*3.2,9.73,0],[.07,.06,31],new THREE.MeshBasicMaterial({color:0x5f5647}));}
 const texLoader=new THREE.TextureLoader();group=new THREE.Group();scene.add(group);
 const archive=[];const angles=[.22,.71,1.16,1.49,1.91,2.35,2.78,3.08,3.53,3.88,4.25,4.57,4.92,5.22,5.56,5.96, .05,1.32,3.31,5.06];
 const texturePool=slices.map(x=>{const t=texLoader.load(x.src);t.colorSpace=THREE.SRGBColorSpace;t.anisotropy=renderer.capabilities.getMaxAnisotropy();return t});
 const lineMat=new THREE.LineBasicMaterial({color:0x7a7164,transparent:true,opacity:.36});
 const brass=new THREE.LineBasicMaterial({color:0x958267,transparent:true,opacity:.58});
 function line(a,b,mat=lineMat,parent=group){const g=new THREE.BufferGeometry().setFromPoints([new THREE.Vector3(...a),new THREE.Vector3(...b)]);const l=new THREE.Line(g,mat);parent.add(l);return l}
 for(let i=0;i<slices.length;i++){
  const a=angles[i],ring=i%5===0?5.25:(i%3===0?7.9:9.4); const x=Math.sin(a)*ring,z=Math.cos(a)*ring;
  const w=(slices[i].w/slices[i].h)*(i%3===0?2.45:2.05),h=i%3===0?2.45:2.05;
  const y=[3.25,4.55,5.95,3.9,6.7][i%5];
  const mat=new THREE.MeshBasicMaterial({map:texturePool[i],color:0xfaf4ec,transparent:true,opacity:.89,depthWrite:true,side:THREE.DoubleSide});
  const frame=new THREE.Group();frame.position.set(x,y,z);frame.rotation.y=a+Math.PI;
  const glass=new THREE.Mesh(new THREE.PlaneGeometry(w,h),mat);frame.add(glass);
  const back=new THREE.Mesh(new THREE.PlaneGeometry(w+.07,h+.07),new THREE.MeshBasicMaterial({color:0x201e1b,side:THREE.DoubleSide}));back.position.z=-.014;frame.add(back);
  const edge=new THREE.LineSegments(new THREE.EdgesGeometry(new THREE.PlaneGeometry(w+.06,h+.06)),brass);edge.position.z=.02;frame.add(edge);
  group.add(frame);
  // Draw the suspension cables in world-space so the fragile image reads as a hanging object.
  line([x-w*.37,y+h*.5,z],[x-w*.37,9.65,z]);line([x+w*.37,y+h*.5,z],[x+w*.37,9.65,z]);
  archive.push({frame,mat,x,z,y,w,h,i});
 }
 // Deliberately empty suspended sheets are art, not fabricated personal records.
 emptyGroup=new THREE.Group();scene.add(emptyGroup);
 const voidSheets=[];
 for(let i=0;i<13;i++){
  const a=i*2.399963,ring=.65+Math.sqrt(i/13)*1.6;
  const x=Math.sin(a)*ring,z=Math.cos(a)*ring;
  const y=2.4+(i%4)*.78,w=.72+(i%3)*.12,h=1.14+(i%4)*.14;
  const frame=new THREE.Group();frame.position.set(x,y,z);frame.rotation.y=a*.55;
  const sheetMat=new THREE.MeshPhysicalMaterial({color:0xe3d8be,transparent:true,opacity:.11,side:THREE.DoubleSide,depthWrite:false,roughness:.7,metalness:0});
  const s=new THREE.Mesh(new THREE.PlaneGeometry(w,h),sheetMat);frame.add(s);
  const edges=new THREE.LineSegments(new THREE.EdgesGeometry(new THREE.PlaneGeometry(w,h)),new THREE.LineBasicMaterial({color:0xbc9e78,transparent:true,opacity:.16}));frame.add(edges);
  emptyGroup.add(frame);line([x,y+h*.5,z],[x,9.65,z],lineMat,emptyGroup);
  voidSheets.push({mat:sheetMat,edge:edges.material,i});
 }
 // Golden lamps at variable heights to emphasize serial archival space.
 for(let i=0;i<10;i++){
  const a=i*Math.PI*2/10,r=7.5;const x=Math.sin(a)*r,z=Math.cos(a)*r;
  let lamp=new THREE.PointLight(0xffc893,15,6,2);lamp.position.set(x,7.9,z);scene.add(lamp);lamps.push(lamp);
  const bulb=new THREE.Mesh(new THREE.SphereGeometry(.057,10,8),new THREE.MeshBasicMaterial({color:0xd7ab70}));bulb.position.copy(lamp.position);scene.add(bulb);
 }function nearest(){let min=Infinity;for(const p of archive)min=Math.min(min,Math.hypot(p.x-camera.position.x,p.z-camera.position.z));return {dist:min}}
 let phase=0;
 function art(dt){phase+=dt;
  const r=Math.hypot(camera.position.x,camera.position.z),silence=1-THREE.MathUtils.smoothstep(r,2.3,8.8);
  for(const p of archive){p.mat.opacity=THREE.MathUtils.lerp(.90,.26,silence*.82)}
  voidSheets.forEach(({mat,edge,i})=>{mat.opacity=.06+.27*silence+.018*Math.sin(phase*.45+i*.5);edge.opacity=.09+.32*silence});
  quietLight.intensity=12+48*silence;lamps.forEach((lamp,i)=>lamp.intensity=12+6*Math.sin(phase*.35+i*.7));
  if(r<2.6){$('#zone').textContent='中心｜名前のない空白';$('#near').textContent='何も書かれていない展示面'}
  else if(r<6.5){$('#zone').textContent='内側｜記録から離れる';$('#near').textContent='写真の光が少しずつ遠のく'}
  else{$('#zone').textContent='回廊｜吊り下げられた記録';const {dist}=nearest();$('#near').textContent=dist<3.6?'近くの画像をEnterで確認できます':'史料風の画像へ近づけます'}
 }

return {update(dt){art(dt)},stats(){return {documents:archive.length,blankSheets:voidSheets.length}}};

}
