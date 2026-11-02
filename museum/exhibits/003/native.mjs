// Derived by tests/extract-ten-exhibit-assets.py. Source HTML is preserved.
// See exhibition-assets/manifest.json for source blob and embedded image hashes.
export function createNative({THREE, scene, camera, renderer, assets, works, images, ui}) {
const $=ui;
const clamp=(a,lo,hi)=>Math.max(lo,Math.min(hi,a));
const add=(a,b)=>[a[0]+b[0],a[1]+b[1],a[2]+b[2]], sub=(a,b)=>[a[0]-b[0],a[1]-b[1],a[2]-b[2]], mul=(a,v)=>[a[0]*v,a[1]*v,a[2]*v], dot=(a,b)=>a[0]*b[0]+a[1]*b[1]+a[2]*b[2],cross=(a,b)=>[a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]],len=a=>Math.hypot(...a),unit=a=>mul(a,1/(len(a)||1));
class Builder{
 constructor(){this.v=[];this.i=[];this.count=0}
 vertex(p,n,c,uv=[0,0],type=0){this.v.push(...p,...n,...c,...uv,type);return this.count++}
 quad(a,b,c,d,color,type=1,uvs=[[0,0],[1,0],[1,1],[0,1]]){const n=unit(cross(sub(b,a),sub(d,a)));let inds=[a,b,c,d].map((p,i)=>this.vertex(p,n,color,uvs[i],type));this.i.push(inds[0],inds[1],inds[2],inds[0],inds[2],inds[3]);}
 box(x,y,z,sx,sy,sz,c,type=1){let x0=x-sx/2,x1=x+sx/2,y0=y-sy/2,y1=y+sy/2,z0=z-sz/2,z1=z+sz/2;
 this.quad([x0,y0,z1],[x1,y0,z1],[x1,y1,z1],[x0,y1,z1],c,type);this.quad([x1,y0,z0],[x0,y0,z0],[x0,y1,z0],[x1,y1,z0],c,type);this.quad([x0,y0,z0],[x0,y0,z1],[x0,y1,z1],[x0,y1,z0],c,type);this.quad([x1,y0,z1],[x1,y0,z0],[x1,y1,z0],[x1,y1,z1],c,type);this.quad([x0,y1,z1],[x1,y1,z1],[x1,y1,z0],[x0,y1,z0],c,type);this.quad([x0,y0,z0],[x1,y0,z0],[x1,y0,z1],[x0,y0,z1],c,type);}
 tube(centers,radius,sides,color,type=0,distances=null,twist=0){
  let frames=[],lastN=null; const count=centers.length;
  for(let i=0;i<count;i++){
   const tangent=unit(sub(centers[Math.min(i+1,count-1)],centers[Math.max(0,i-1)]));
   let n=lastN?sub(lastN,mul(tangent,dot(lastN,tangent))):cross(tangent,[0,1,0]);
   if(len(n)<1e-3)n=cross(tangent,[0,0,1]); n=unit(n); let b=unit(cross(tangent,n)); frames.push([n,b,tangent]); lastN=n;
  }
  return this.tubeFrame(centers,frames,radius,sides,color,type,distances,twist);
 }
 tubeFrame(centers,frames,radius,sides,color,type=0,distances=null,twist=0){
  const start=this.count;
  for(let i=0;i<centers.length;i++){
   const [n,b]=frames[i],s=distances?distances[i]:i*.1;
   for(let j=0;j<=sides;j++){
    const phase=j*2*Math.PI/sides + (twist? s*twist:0);const radial=add(mul(n,Math.cos(phase)),mul(b,Math.sin(phase)));
    const vcolor=[color[0],color[1],color[2],1];
    this.vertex(add(centers[i],mul(radial,radius)),radial,vcolor,[s,j/sides],type);
   }
  }
  for(let i=0;i<centers.length-1;i++)for(let j=0;j<sides;j++){
   const a=start+i*(sides+1)+j,b=a+sides+1; this.i.push(a,b,a+1,b,b+1,a+1);
  }
 }
}
// Control points approximate the original installation: a thick rope traces the floor,
// climbs the left wall, forms an immense elevated loop, then returns to the right.
const control=[
 [-12,.44,12],[-8,.48,10],[-5,.5,7],[-3,.48,3],[-5,.45,0],[-9,.44,-1.2],[-11.9,.5,-3.5],[-12.1,3,-4.4],[-12.1,8,-4.2],[-12,12.4,-4],[-9.5,13.1,-4.6],[-4,12.6,-5.8],[0,11.7,-6.5],
 [5.8,11.7,-6.4],[9.8,10.1,-6.8],[10.5,8.1,-8],[8.2,7.7,-9.8],[3,8.4,-10],[-1,10,-9.1],[-1.1,11.8,-7],[2.5,12.9,-6.1],[7.6,12.1,-6.9],[11.1,9.9,-8.2],[12.1,5.4,-8.7],[12,.5,-9.5],[10,.48,-9.8],[7,.45,-9.1]
];
function catmull(p0,p1,p2,p3,t){const t2=t*t,t3=t2*t;return [0,1,2].map(i=>0.5*((2*p1[i])+(-p0[i]+p2[i])*t+(2*p0[i]-5*p1[i]+4*p2[i]-p3[i])*t2+(-p0[i]+3*p1[i]-3*p2[i]+p3[i])*t3));}
function sampleCurve(n){const p=[],d=[0]; for(let i=0;i<n;i++){const f=(i/(n-1))*(control.length-1),a=Math.min(control.length-2,Math.floor(f)),t=f-a;p.push(catmull(control[Math.max(a-1,0)],control[a],control[a+1],control[Math.min(a+2,control.length-1)],t)); if(i>0)d.push(d[i-1]+len(sub(p[i],p[i-1])));}return {p,d};}
const centerline=sampleCurve(1480);
function framesFor(points){const frames=[],N=points.length;let prev=null;for(let i=0;i<N;i++){const t=unit(sub(points[Math.min(i+1,N-1)],points[Math.max(0,i-1)]));let n=prev?sub(prev,mul(t,dot(prev,t))):cross(t,[0,1,0]);if(len(n)<.0001)n=cross(t,[0,0,1]);n=unit(n);frames.push([n,unit(cross(t,n)),t]);prev=n;}return frames;}
const frame=framesFor(centerline.p); const palette={wall:[.86,.858,.831,1],floor:[.66,.67,.64,1],roof:[.92,.926,.92,1],beam:[.78,.78,.76,1],glass:[.78,.9,.92,1],plaque:[.18,.2,.19,1]};
function floorShadowGeometry(){const g=new Builder(),p=centerline.p; // Wide, very faint contact shadow under the ground rope.
 for(let i=0;i<p.length-12;i+=6){ if(p[i][1]>.9||p[i+6][1]>.9)continue;let a=p[i],b=p[i+6],t=unit([b[0]-a[0],0,b[2]-a[2]]),n=[-t[2],0,t[0]],w=.63;
  const A=[a[0]+n[0]*w,.013,a[2]+n[2]*w],B=[b[0]+n[0]*w,.013,b[2]+n[2]*w],C=[b[0]-n[0]*w,.013,b[2]-n[2]*w],D=[a[0]-n[0]*w,.013,a[2]-n[2]*w];g.quad(A,B,C,D,[.05,.06,.05,.33],5);
 }return g;}
function ropeGeometry(detail){
 const builder=new Builder(),p=centerline.p,d=centerline.d;
 if(detail===0){builder.tubeFrame(p,frame,.43,15,[.8,.79,.745],0,d);return builder;}
 const strandCenters=[[],[],[]];
 // FIRST SCALE: three large strands twisted along the monumental rope's centreline.
 // The three lobes should be visible from a distance in every direction.
 for(let i=0;i<p.length;i++){
  const s=d[i],angle=2*Math.PI*s/2.1; const [n,b]=frame[i];
  for(let j=0;j<3;j++){
   const a=angle+j*Math.PI*2/3;
   strandCenters[j].push(add(p[i],add(mul(n,.164*Math.cos(a)),mul(b,.164*Math.sin(a)))));
  }
 }
 const colors=[[.86,.839,.79],[.80,.786,.744],[.90,.875,.826]];
 for(let j=0;j<3;j++){
  const centers=strandCenters[j],f=framesFor(centers);
  if(detail<3){
   builder.tubeFrame(centers,f,.247,detail===1?11:10,colors[j],detail===2?7:0,d);
   continue;
  }
  // SECOND SCALE: each of the three large strands is made of a compact core
  // surrounded by NINE actual, helically plied smaller cords. In C these were
  // simulated as drawn grooves; here the nine cords have their own silhouettes.
  // Their pitch is independent of the larger rope's pitch (2.1 m).
  const yarnN=9;
  const yarnRadius=.068, yarnOrbit=.188, yarnPitch=1.10;
  const coreColor=colors[j].map(c=>c*.94);
  builder.tubeFrame(centers,f,.197,9,coreColor,9,d);
  // Avoid a full extra framesFor() pass for each of 27 yarns: each spun yarn
  // reuses the main strand's local frame. Its normals remain consistent in
  // curved sections and don't flicker from one sample to the next.
  for(let k=0;k<yarnN;k++){
   const yarnPoints=[];
   for(let i=0;i<centers.length;i++){
    // Reverse the secondary lay direction relative to the main rope.
    // This makes the characteristic crossing diagonal of multi-ply cordage.
    const phase=-2*Math.PI*d[i]/yarnPitch+2*Math.PI*k/yarnN+j*.13;
    const [n,b]=f[i];
    yarnPoints.push(add(centers[i],add(mul(n,yarnOrbit*Math.cos(phase)),mul(b,yarnOrbit*Math.sin(phase)))));
   }
   const yarnFrames=framesFor(yarnPoints);
   const tint=1+(.016*Math.sin(k*7.17+j*4.1));
   const yarnColor=colors[j].map(c=>Math.min(.95,c*tint));
   builder.tubeFrame(yarnPoints,yarnFrames,yarnRadius,6,yarnColor,8,d);
  }
 }
 return builder;
}
const VS=`#version 300 es
precision highp float;
layout(location=0) in vec3 aPos;layout(location=1) in vec3 aNorm;layout(location=2) in vec4 aCol;layout(location=3) in vec2 aUV;layout(location=4) in float aKind;
uniform mat4 uProj,uView;out vec3 vPos,vNorm;out vec4 vCol;out vec2 vUV;flat out int vKind;
void main(){vPos=aPos;vNorm=aNorm;vCol=aCol;vUV=aUV;vKind=int(aKind+.5);gl_Position=uProj*uView*vec4(aPos,1.);}`;
const FS=`#version 300 es
precision highp float;
in vec3 vPos,vNorm;in vec4 vCol;in vec2 vUV;flat in int vKind;out vec4 fragColor;
uniform vec3 uCamera;uniform float uLight;
float hash21(vec2 p){return fract(sin(dot(p,vec2(127.1,311.7)))*43758.5453);}
void main(){vec3 n=normalize(vNorm), l=normalize(vec3(-.39,.88,.37));vec3 v=normalize(uCamera-vPos);
 float diff=max(0.,dot(n,l));float rim=pow(1.-max(0.,dot(n,v)),2.4);
 vec3 col=vCol.rgb;float rough=.7;
 if(vKind==0){float thread=.026*sin(vUV.x*57.+vUV.y*12.)+.021*sin(vUV.x*93.+vUV.y*24.);float tiny=.018*hash21(floor(vUV*vec2(95.,46.)));col*=1.+thread+tiny;rough=.92;}
 if(vKind==7){
  // Smooth, directional fibres hugging each rope strand; never add independent bumps.
  // Screen-space derivatives suppress moire/granularity at viewing distance.
  float ph1=vUV.x*17.0-vUV.y*157.07963;
  float ph2=vUV.x*31.0-vUV.y*251.32741;
  float aa1=1.-smoothstep(.75,2.1,fwidth(ph1));
  float aa2=1.-smoothstep(.75,2.1,fwidth(ph2));
  float yarn=.075*sin(ph1)*aa1+.022*sin(ph2)*aa2;
  col*=1.+yarn;
  rough=.94;
 }
 if(vKind==8){
  // Fibres in each physical sub-cord: very restrained multi-frequency tonal
  // variation, with fwidth-based filtering to avoid speckling when distant.
  float p1=vUV.x*38.0-vUV.y*18.8495559;
  float p2=vUV.x*79.0+vUV.y*37.6991118;
  float fade1=1.-smoothstep(.6,2.7,fwidth(p1));
  float fade2=1.-smoothstep(.6,2.7,fwidth(p2));
  float linen=.035*sin(p1)*fade1+.014*sin(p2)*fade2;
  col*=1.+linen;
  rough=.98;
 }
 if(vKind==9){rough=.97;col*=.91;}
 if(vKind==2){float grout=max(step(.985,fract(abs(vPos.x)*.78)),step(.985,fract(abs(vPos.z)*.78)));col*=1.-.04*grout;rough=.58;}
 if(vKind==3){fragColor=vec4(col,.35);return;}
 if(vKind==5){fragColor=vec4(col,.18);return;}
 float fill=.60+uLight*.48*diff;
 vec3 halfv=normalize(v+l);float spec=pow(max(0.,dot(n,halfv)),rough>.8?13.:25.)*(rough>.8?.085:.16);
 col=col*fill + vec3(spec)+rim*(vKind==0?.065:.023);
 if(vKind==6) col=vec3(.24,.26,.25);
 float fog=clamp((length(uCamera-vPos)-28.)/23.,0.,.55);col=mix(col,vec3(.78,.79,.77),fog);
 fragColor=vec4(pow(clamp(col,0.,2.),vec3(.97)),vCol.a);
}`;

function geometry(builder) {
 const g=new THREE.BufferGeometry(),v=new THREE.InterleavedBuffer(new Float32Array(builder.v),13);
 for(const [name,size,offset] of [['aPos',3,0],['aNorm',3,3],['aCol',4,6],['aUV',2,10],['aKind',1,12]])g.setAttribute(name,new THREE.InterleavedBufferAttribute(v,size,offset));
 g.setAttribute('position',g.getAttribute('aPos'));g.setIndex(builder.i);g.computeBoundingSphere();return g;
}
const uniforms={uProj:{value:new THREE.Matrix4()},uView:{value:new THREE.Matrix4()},uCamera:{value:new THREE.Vector3()},uLight:{value:1}};
const mat=new THREE.RawShaderMaterial({glslVersion:THREE.GLSL3,vertexShader:VS.replace('#version 300 es',''),fragmentShader:FS.replace('#version 300 es',''),uniforms,side:THREE.DoubleSide});
let level=3,mesh=new THREE.Mesh(geometry(ropeGeometry(3)),mat);scene.add(mesh);
return {update(){uniforms.uProj.value.copy(camera.projectionMatrix);uniforms.uView.value.copy(camera.matrixWorldInverse);uniforms.uCamera.value.copy(camera.position)},set(name,value){if(name==='material'){level=Number(value);const g=geometry(ropeGeometry(level));mesh.geometry.dispose();mesh.geometry=g}},stats(){return {material:['滑らかな管','三つ撚り','繊維の質感','3束×9本の撚り糸'][level],materialMode:level,triangles:mesh.geometry.index.count/3}}};

}
