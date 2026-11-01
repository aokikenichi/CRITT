import {makeAdapter,THREE,plane,line,texture} from '../shared/adapter.mjs';
import {sourceData,floatingHeight} from './source-data.mjs';
export default meta=>makeAdapter(meta,({scene,camera,data})=>{
 const {islands,balls,bats,rocks}=sourceData(),assets=data.images;let time=0,gravity=1,target=1,spatial=true,dense=true;
 const reduced=matchMedia('(prefers-reduced-motion: reduce)').matches;
 const islandMeshes=islands.map((it,i)=>{const g=new THREE.Group();g.position.set(it.x,0,it.z);const top=plane(assets.pitch,it.w,it.d,.93);top.rotation.x=-Math.PI/2;g.add(top);
 const w=it.w,d=it.d,facets=[[-w/2,0,-d/2],[-w/2,-.55,-d/2],[w/2,-.74,-d/2],[w/2,0,-d/2],[w/2,-.46,d/2],[w/2,0,d/2]],geo=new THREE.BufferGeometry();geo.setAttribute('position',new THREE.Float32BufferAttribute(facets.flat(),3));geo.setIndex([0,1,2,0,2,3,3,2,4,3,4,5]);geo.computeVertexNormals();g.add(new THREE.Mesh(geo,new THREE.MeshBasicMaterial({color:0x393c39,side:THREE.DoubleSide})));
 for(let k=-1;k<=1;k++)g.add(line([[it.w*.2+k*.1,.05,-it.d*.16],[it.w*.2+k*.1,.8,-it.d*.16]],0xe3cc9f));g.add(line([[it.w*.2-.17,.84,-it.d*.16],[it.w*.2+.17,.84,-it.d*.16]],0xeed0a2));scene.add(g);return g});
 const sprites=(items,key,size)=>items.map(a=>{const mat=new THREE.SpriteMaterial({map:texture(assets[key]),transparent:true,alphaTest:.02,depthWrite:false});const o=new THREE.Sprite(mat);o.position.set(a.x,a.y,a.z);const sc=size(a);o.userData.height=sc;o.scale.set(sc*(key==='bat'?.23:1),sc,1);scene.add(o);return o});
 const ballMeshes=sprites(balls,'ball',a=>a.r*2.7),batMeshes=sprites(bats,'bat',a=>2.35*a.scale);
 const rockMeshes=rocks.map((r,i)=>{const o=new THREE.Group(),sz=r.r,a=[[0,sz,0],[-sz*.8,0,sz*.13],[0,-sz*.7,sz*.48],[sz*.8,0,0]],cols=[0x4f4a43,0x746454,0x333e45,0x8a785c],positions=[...a[0],...a[1],...a[2],...a[0],...a[2],...a[3]],colors=[];for(const color of [cols[i%4],cols[(i+1)%4]]){const c=new THREE.Color(color);for(let k=0;k<3;k++)colors.push(c.r,c.g,c.b)}const g=new THREE.BufferGeometry();g.setAttribute('position',new THREE.Float32BufferAttribute(positions,3));g.setAttribute('color',new THREE.Float32BufferAttribute(colors,3));o.add(new THREE.Mesh(g,new THREE.MeshBasicMaterial({vertexColors:true,side:THREE.DoubleSide})));o.add(line([a[0],a[3]],0xb9a68b,.27));o.position.set(r.x,r.y,r.z);scene.add(o);return o});
 const orbits=[];for(let n=0;n<5;n++){const pts=[];for(let i=0;i<=45;i++){const a=i/45*Math.PI*2+.3*n,r=4.7+n*.36;pts.push([(n-2)*2.55+Math.cos(a)*r,2.2+3.5*Math.sin(a),-35-n*5.3+Math.sin(a)*r*1.2])}const o=line(pts,n%2?0xb1dfff:0xfae4b8,.22);scene.add(o);orbits.push(o)}
 const climax=new THREE.Sprite(new THREE.SpriteMaterial({map:texture(assets.ball),transparent:true,depthWrite:false}));climax.scale.set(4.3,4.3,1);scene.add(climax);
 // Original environmental images become distinct world layers, never a source-page screenshot.
 for(const [i,key] of ['room_A','room_B','room_C'].entries()){const p=plane(assets[key],34,21,.33);p.position.set(0,6,-12-i*26);p.material.depthWrite=false;p.position.x=i%2?18:-18;p.rotation.y=i%2?-Math.PI/2:Math.PI/2;scene.add(p)}
 for(let z=-71;z<=12;z+=11){const pts=[];for(let i=0;i<=50;i++){const a=i/50*Math.PI;pts.push([17.5*Math.cos(a),10+9*Math.sin(a),z])}scene.add(line(pts,0xd5c9a0,.34));for(const x of [-17.5,17.5])scene.add(line([[x,-2.46,z],[x,10,z]],0xb5d8dc,.3))}
 for(const z of [-12,-39,-68]){for(let k=-1;k<=1;k++)scene.add(line([[k*.33,-2.25,z],[k*.33,-.27,z]],0xc6b391));scene.add(line([[-.5,-.27,z],[.5,-.27,z]],0xdbc8a5))}
 return {update(dt){if(!reduced)time+=dt;if(spatial)target=camera.position.z>-16?1:camera.position.z>-43?.25:0;gravity+=(target-gravity)*Math.min(1,dt*1.7);
 for(const m of [...ballMeshes,...batMeshes,climax]){const im=m.material.map.image;if(im?.width){const h=m.userData.height||4.3;m.scale.set(h*im.width/im.height,h,1)}}
 const fh=(b,p,a)=>floatingHeight(b,p,a,gravity,time,reduced);
 islandMeshes.forEach((m,i)=>m.position.y=fh(-2.18,islands[i].phase,(i%4===0?3.2:1.5)+i*.07));
 ballMeshes.forEach((m,i)=>{const a=balls[i];m.position.y=fh(a.y,a.phase,2.9);m.material.rotation=(reduced?0:time*.08)+a.phase*.16});
 batMeshes.forEach((m,i)=>{const a=bats[i];m.visible=dense||i%2===0;m.position.y=fh(a.y,a.phase,2.7);m.material.rotation=(reduced?0:Math.sin(time*.16+a.phase)*.25)+a.phase});
 rockMeshes.forEach((m,i)=>{m.visible=dense||i%3===0;m.position.y=fh(rocks[i].y,rocks[i].phase,1.7)});
 orbits.forEach(o=>{o.visible=gravity<.8;o.position.y=Math.max(0,1-gravity)*1.2});const u=gravity>.7?0:gravity>.08?.38:1;climax.position.set(.3,.9+2.1*u+(reduced?0:Math.sin(time*.36)*.12*u),-62)},
 set(name,value){if(name==='gravity'){spatial=value==='spatial';if(!spatial)target=Number(value)}if(name==='dense')dense=value},stats(){return {islands:islands.length,balls:balls.length,bats:bats.length,rocks:rocks.length,gravity,target,spatial,dense}}};
});
