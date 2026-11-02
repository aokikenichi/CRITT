// Derived by tests/extract-ten-exhibit-assets.py. Source HTML is preserved.
// See exhibition-assets/manifest.json for source blob and embedded image hashes.
export function createNative({THREE, scene, camera, renderer, assets, works, images, ui}) {
const $=ui;
const loader=new THREE.TextureLoader();let reflect=true,audioLevel=0;
scene.add(new THREE.HemisphereLight(0x6d9dbb,0x050914,1.65));
const ambient=new THREE.PointLight(0xe6b88d,18,24,2);ambient.position.set(0,5,0);scene.add(ambient);
const blue=new THREE.PointLight(0x5ca7ef,20,22,2);blue.position.set(-5,3,-3);scene.add(blue);
const floorMat=new THREE.MeshPhysicalMaterial({color:0x111b27,roughness:.29,metalness:.51,clearcoat:.72,clearcoatRoughness:.18});
const floor=new THREE.Mesh(new THREE.CircleGeometry(15.8,120),floorMat);floor.rotation.x=-Math.PI/2;floor.position.y=-.03;scene.add(floor);
const ringMat=new THREE.MeshBasicMaterial({color:0x6aa1bd,transparent:true,opacity:.14});const goldMat=new THREE.MeshBasicMaterial({color:0xe5c9a4,transparent:true,opacity:.22});
function makeFloorRing(radius,material,y=.006){const line=new THREE.Mesh(new THREE.TorusGeometry(radius,.018,5,140),material);line.rotation.x=-Math.PI/2;line.position.y=y;scene.add(line);return line}
makeFloorRing(2.1,ringMat);makeFloorRing(5.6,ringMat);makeFloorRing(9.8,goldMat);makeFloorRing(14.7,ringMat);
const basin=new THREE.Mesh(new THREE.CylinderGeometry(1.52,1.55,.12,100),new THREE.MeshPhysicalMaterial({color:0x080e17,roughness:.18,metalness:.70,clearcoat:.8}));basin.position.y=.03;scene.add(basin);
const focus=new THREE.Mesh(new THREE.SphereGeometry(.07,16,12),new THREE.MeshBasicMaterial({color:0xf9d3ab}));focus.position.set(0,1.9,0);scene.add(focus);
const photopanels=[];
const panelGeo=new THREE.PlaneGeometry(2.32,6.2);
for(let i=0;i<12;i++){
 const theta=2*Math.PI*(i+.38)/12;const r= i<8?10.65:7.5;
 const texture=loader.load(images.panels[i]);texture.colorSpace=THREE.SRGBColorSpace;texture.anisotropy=Math.min(8,renderer.capabilities.getMaxAnisotropy());
 const mat=new THREE.MeshBasicMaterial({map:texture,transparent:true,opacity:i<8?.86:.63,side:THREE.DoubleSide,depthWrite:false,blending:THREE.AdditiveBlending});
 const mesh=new THREE.Mesh(panelGeo,mat);mesh.position.set(Math.sin(theta)*r,4.35+(i%3-.8)*.25,Math.cos(theta)*r);mesh.rotation.y=theta;scene.add(mesh);photopanels.push({mesh,mat,theta});
 const edge=new THREE.Line(new THREE.BufferGeometry().setFromPoints([new THREE.Vector3(-1.16,-3.10,0),new THREE.Vector3(-1.16,3.10,0)]),new THREE.LineBasicMaterial({color:0x8cb9d7,transparent:true,opacity:.11}));edge.position.copy(mesh.position);edge.rotation.copy(mesh.rotation);scene.add(edge);
}
// Individual suspended filaments create physical depth between photo scrims.
const filaments=[];
for(let i=0;i<86;i++){
 const phi=i*2.399963229728653;const r=2.6+Math.sqrt((i%59)/58)*7.7; const x=r*Math.cos(phi),z=r*Math.sin(phi);
 const height=2.1+(i*0.57%5.1), material=new THREE.LineBasicMaterial({color:i%3?0x92bcdd:0xe7bf91,transparent:true,opacity:.08});
 const geo=new THREE.BufferGeometry().setFromPoints([new THREE.Vector3(x,height,z),new THREE.Vector3(x,height-(.5+i%5*.34),z)]);
 const l=new THREE.Line(geo,material);scene.add(l);filaments.push({l,material,phase:i*.45});
}
// A physically navigable lattice of voice-particles, not a sound recording.
const COUNT=4200;const pts=new Float32Array(COUNT*3);const colors=new Float32Array(COUNT*3);const base=new Float32Array(COUNT*3);const phases=new Float32Array(COUNT);
let seed=13579;function rand(){seed=(Math.imul(seed,1664525)+1013904223)>>>0;return seed/4294967296;}
for(let i=0;i<COUNT;i++){
 const theta=rand()*Math.PI*2;const r=1.6+Math.sqrt(rand())*7.5;
 base[i*3]=r*Math.cos(theta);base[i*3+1]=1.55+rand()*5.9;base[i*3+2]=r*Math.sin(theta);
 const c=rand();colors[i*3]=c>.55?1.0:.45;colors[i*3+1]=c>.55?.72:.65;colors[i*3+2]=c>.55?.42:1.0;phases[i]=rand()*6.283;
}
const gpts=new THREE.BufferGeometry();gpts.setAttribute('position',new THREE.BufferAttribute(pts,3));gpts.setAttribute('color',new THREE.BufferAttribute(colors,3));
const dots=new THREE.Points(gpts,new THREE.PointsMaterial({vertexColors:true,size:.042,sizeAttenuation:true,transparent:true,opacity:.8,depthWrite:false,blending:THREE.AdditiveBlending}));scene.add(dots);
const waves=[];
for(let k=0;k<13;k++){
 const N=150,arr=new Float32Array(N*3);const geo=new THREE.BufferGeometry();geo.setAttribute('position',new THREE.BufferAttribute(arr,3));
 const mat=new THREE.LineBasicMaterial({color:k%3===0?0xefb675:0x86b5e4,transparent:true,opacity:.2,depthWrite:false});const l=new THREE.Line(geo,mat);scene.add(l);waves.push({geo,arr,mat,k});
}
function updateArt(now,dt){
 const radius=Math.hypot(camera.position.x,camera.position.z);
 const v=THREE.MathUtils.smoothstep(radius,1.7,6.6),intensity=(reflect?v:1)*(1+audioLevel*.08);
 const quiet=radius<2.1;if(quiet){$('#zone').textContent='中央｜静寂';$('#level').textContent='声の層が遠のく位置'}
 else if(radius<5.4){$('#zone').textContent='内側｜ひとつの声';$('#level').textContent='輪郭を探す場所'}
 else if(radius<8.8){$('#zone').textContent='中間｜声の重なり';$('#level').textContent='幾重もの光が交わる場所'}
 else{$('#zone').textContent='外周｜群衆のうねり';$('#level').textContent='光の密度が高まる場所'}
 dots.material.opacity=.055+.89*intensity;
 for(let i=0;i<COUNT;i++){
  const x=base[i*3],y=base[i*3+1],z=base[i*3+2],phase=phases[i];
  pts[i*3]=x+Math.sin(now*.00056+phase+y*.43)*(.07+.075*intensity);
  pts[i*3+1]=y+Math.sin(now*.0009+phase+x*.26)*(.11+.09*intensity);
  pts[i*3+2]=z+Math.cos(now*.00067+phase+z*.19)*(.07+.075*intensity);
 }
 gpts.attributes.position.needsUpdate=true;
 for(const w of waves){
  const {k,arr,geo,mat}=w;mat.opacity=.015+.28*intensity;
  for(let j=0;j<150;j++){const u=j/149;const x=-7+14*u;
   arr[j*3]=x;arr[j*3+1]=3.0+k*.15+Math.sin(u*10.5+now*.00078+k*.83)*(.16+.18*intensity);
   arr[j*3+2]=Math.sin(u*6.8+k*.48+now*.0003)*(1.5+k*.28)+Math.cos(u*15+k)*.2;
  }
  geo.attributes.position.needsUpdate=true;geo.computeBoundingSphere();
 }
 filaments.forEach(({material,phase})=>material.opacity=.025+.14*intensity*(.7+.3*Math.sin(now*.00075+phase)));
 focus.material.color.setRGB(.5+.5*(1-intensity),.55+.28*(1-intensity),.65+.15*(1-intensity));
 photopanels.forEach(({mat},i)=>mat.opacity=(i<8?.63:.37)+.23*intensity);
 ambient.intensity=6+15*intensity;blue.intensity=8+20*intensity;
}

return {update(dt,now){updateArt(now,dt)},set(name,value){if(name==='reflect')reflect=value;if(name==='audioLevel')audioLevel=Math.max(0,Math.min(1,value))},stats(){return {particles:COUNT,scrims:photopanels.length,filaments:filaments.length,reflect}}};

}
