import {makeAdapter,THREE,plane} from '../shared/adapter.mjs';
export default meta=>makeAdapter(meta,({scene,camera})=>{
 const widths=[3.35,2.8,2.9,3.15,3.75],heights=[6.55,6.4,6.15,5.7,4.35],zs=[-.9,-1,-.6,-.8,-1];
 const layers=widths.map((w,i)=>{const h=heights[i],m=plane(`exhibition-assets/002/0${i+3}.png`,w,h,.85);m.position.set(-10.3+i*5.15,h/2,zs[i]);m.rotation.y=-Math.PI/2;m.material.depthWrite=false;m.material.blending=THREE.AdditiveBlending;scene.add(m);return m});
 return {update(){const cx=camera.position.x+28.7,progress=THREE.MathUtils.clamp((cx-14)/27,0,1);layers.forEach((m,i)=>{const focus=1-THREE.MathUtils.smoothstep(Math.abs(cx-(18.4+i*5.15)),1,10),sequence=Math.exp(-Math.pow((progress-i*.25)*5,2));m.material.opacity=.32+focus*.58+sequence*.50})},stats(){return {figureMode:'A',layers:5,worldFixed:true}}};
});
