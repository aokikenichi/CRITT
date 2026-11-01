import {makeAdapter,THREE,texture} from '../shared/adapter.mjs';
export default meta=>makeAdapter(meta,async({scene,camera})=>{
 const r=await fetch('exhibits/001/ball-source.glsl');if(!r.ok)throw new Error('001 球面シェーダー未取得');const source=await r.text();
 const uniforms={uCam:{value:new THREE.Vector3()},uProj:{value:new THREE.Matrix4()},uView:{value:new THREE.Matrix4()},uBallPhoto:{value:texture('exhibition-assets/001/02.jpg')},uBallMicro:{value:texture('exhibition-assets/001/09.jpg')},uMaterialMode:{value:3},uPhotoReady:{value:1},uMicroReady:{value:1}};
 const mat=new THREE.RawShaderMaterial({glslVersion:THREE.GLSL3,side:THREE.DoubleSide,uniforms,vertexShader:'precision highp float;in vec3 position;out vec3 vPos;uniform mat4 uProj,uView;void main(){vPos=position;gl_Position=uProj*uView*vec4(position,1.);}',fragmentShader:`precision highp float;in vec3 vPos;out vec4 fragColor;uniform vec3 uCam;uniform mat4 uProj,uView;uniform sampler2D uBallPhoto,uBallMicro;uniform int uMaterialMode;uniform float uPhotoReady,uMicroReady;\n${source}\nvoid main(){vec3 rd=normalize(vPos-uCam);float t=ballHit(uCam,rd);if(t>1e9)discard;vec3 p=uCam+rd*t;vec4 clip=uProj*uView*vec4(p,1.);gl_FragDepth=clip.z/clip.w*.5+.5;fragColor=vec4(ballSurface(p,normalize(p-ballCenter),rd),1.);}`});
 uniforms.uBallPhoto.value.colorSpace=THREE.NoColorSpace;uniforms.uBallMicro.value.colorSpace=THREE.NoColorSpace;
 const geo=new THREE.SphereGeometry(2.25,40,28);geo.translate(0,4.05,0);scene.add(new THREE.Mesh(geo,mat));
 const halo=new THREE.Mesh(new THREE.CircleGeometry(3.3,64),new THREE.MeshBasicMaterial({color:0x07090a,transparent:true,opacity:.38,depthWrite:false}));halo.rotation.x=-Math.PI/2;halo.position.y=.013;scene.add(halo);
 return {update(){uniforms.uCam.value.copy(camera.position);uniforms.uProj.value.copy(camera.projectionMatrix);uniforms.uView.value.copy(camera.matrixWorldInverse)},stats(){return {materialMode:3,photo:true}}};
});
