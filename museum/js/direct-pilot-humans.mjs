// Geometry and material extracted from Work 02 3D Lab v1.2; source preserved in recovered/.
export const humanVS=`#version 300 es
precision highp float;
in vec3 aHumanPos;in vec3 aHumanNormal;in vec2 aHumanUV;
uniform vec3 uEye;uniform vec3 uRight;uniform vec3 uUp;uniform vec3 uForward;uniform vec2 uProj;
out vec3 vNormal;out vec3 vWorld;out vec2 vUV;
void main(){vec3 d=aHumanPos-uEye;float dep=dot(d,uForward);
 gl_Position=vec4(dot(d,uRight)*uProj.x,dot(d,uUp)*uProj.y,dep*.996,dep);
 vNormal=aHumanNormal;vWorld=aHumanPos;vUV=aHumanUV;}`;
export const humanFS=`#version 300 es
precision highp float;
in vec3 vNormal;in vec3 vWorld;in vec2 vUV;
uniform vec3 uEye;uniform float uFigureLook;uniform float uProgress;uniform float uSeconds;
out vec4 fragColor;
// The raycast room has no depth buffer. Clip each mesh fragment against the
// same walls/openings and sphere, so figures cannot shine through architecture.
bool occluded(){
 vec3 d=vWorld-uEye;
 if(abs(d.x)>.0001){
  float t=(12.5-uEye.x)/d.x;
  if(t>0.&&t<1.){vec3 p=uEye+d*t;
   if(p.y>=0.&&p.y<10.5&&p.z>-14.&&p.z<17.&&!(p.y<7.&&p.z>1.&&p.z<13.))return true;
   if(p.y>=0.&&p.y<10.5&&p.z>=17.&&p.z<28.)return true;
  }
 }
 if(abs(d.z)>.0001){
  float t=(17.-uEye.z)/d.z;
  if(t>0.&&t<1.){vec3 p=uEye+d*t;
   if(p.y>=0.&&p.y<10.5&&abs(p.x)<12.5&&!(p.y<7.&&abs(p.x)<8.))return true;
  }
  for(int i=0;i<2;i++){
   float plane=i==0?-8.:14.;t=(plane-uEye.z)/d.z;
   if(t>0.&&t<1.){vec3 p=uEye+d*t;
    if(p.y>=0.&&p.y<10.5&&p.x>12.5&&p.x<46.)return true;
   }
  }
 }
 vec3 o=uEye-vec3(0.,4.05,0.);float a=dot(d,d),b=dot(o,d),c=dot(o,o)-2.18*2.18;
 float h=b*b-a*c;
 if(h>=0.){float t=(-b-sqrt(h))/a;if(t>0.&&t<1.)return true;}
 return false;
}
void main(){if(occluded())discard;vec3 n=normalize(vNormal);vec3 view=normalize(uEye-vWorld);
 float edge=pow(1.-abs(dot(n,view)),1.85);
 float lineA=1.-smoothstep(.015,.052,abs(fract(vUV.x*19.+sin(vUV.y*16.+uSeconds*.08)*.016)-.5));
 float lineB=1.-smoothstep(.012,.05,abs(fract(vUV.y*23.)-.5));
 float filigree=max(lineA*.9,lineB*.56);
 float slow=sin(vWorld.x*.19+uSeconds*.17)*.5+.5;
 vec3 pearl=mix(vec3(.57,.63,.68),vec3(.93,.80,.67),clamp(vWorld.x/45.,0.,1.));
 vec3 turquoise=vec3(.37,.73,.78);
 vec3 col=mix(pearl,turquoise,uFigureLook<1.5?.22:.16);
 col+=vec3(.66,.54,.38)*pow(max(dot(n,normalize(vec3(-.42,.83,.35))),0.),3.)*.28;
 float al = uFigureLook<1.5 ? .047+filigree*.58+edge*.30 : .16+filigree*.34+edge*.44;
 col*=.73+edge*.72+slow*.15;
 col+=vec3(.40,.53,.65)*pow(edge,3.)*.28;
 fragColor=vec4(col,clamp(al,0.,.89));}`;
export function buildHumans(){
 const floats=[];const slices=12,rings=10,S=2.54;
 // Every pose is a human bowler at a successive phase, not a separate player.
 const poses=[
 {hip:[-.08,1.00,0],chest:[.22,1.53,0],head:[.34,1.79,0],
  elL:[-.12,1.26,.25],wrL:[-.34,1.02,.28],elR:[.57,1.45,-.27],wrR:[.80,1.27,-.27],
  knL:[-.45,.62,.17],ftL:[-.63,.07,.23],knR:[.23,.67,-.17],ftR:[.50,.10,-.16]},
 {hip:[.01,1.23,0],chest:[.27,1.78,0],head:[.36,2.01,0],
  elL:[.05,1.90,.24],wrL:[-.13,2.13,.28],elR:[.62,1.62,-.25],wrR:[.76,1.21,-.27],
  knL:[.32,1.02,.18],ftL:[.43,.68,.16],knR:[-.30,.92,-.18],ftR:[-.69,.66,-.23]},
 {hip:[0,1.03,0],chest:[.17,1.56,0],head:[.23,1.83,0],
  elL:[-.10,1.70,.26],wrL:[-.48,1.71,.32],elR:[.36,1.23,-.28],wrR:[.11,1.01,-.30],
  knL:[-.20,.58,.16],ftL:[-.43,.10,.18],knR:[.29,.56,-.16],ftR:[.52,.06,-.18]},
 {hip:[-.02,1.00,0],chest:[-.16,1.55,0],head:[-.18,1.82,0],
  elL:[-.37,1.79,.22],wrL:[-.16,2.23,.28],elR:[.15,1.43,-.23],wrR:[.53,1.18,-.25],
  knL:[-.36,.60,.17],ftL:[-.63,.05,.18],knR:[.23,.59,-.17],ftR:[.54,.08,-.17]},
 {hip:[-.03,.94,0],chest:[.45,1.41,0],head:[.63,1.64,0],
  elL:[.76,1.32,.24],wrL:[1.02,1.05,.25],elR:[.43,1.05,-.24],wrR:[.15,.92,-.28],
  knL:[-.29,.51,.18],ftL:[-.48,.08,.19],knR:[.31,.54,-.18],ftR:[.72,.10,-.18]}
 ];
 function addEllipsoid(center,axis,r1,r2){
  // Basis along segment axis. A sphere mesh is elongated along local y.
  const up=axis, arbitrary=Math.abs(up[1])<.9?[0,1,0]:[1,0,0];
  let ux=[up[1]*arbitrary[2]-up[2]*arbitrary[1],up[2]*arbitrary[0]-up[0]*arbitrary[2],up[0]*arbitrary[1]-up[1]*arbitrary[0]];
  const ul=Math.hypot(...ux)||1;ux=ux.map(v=>v/ul);
  const uz=[ux[1]*up[2]-ux[2]*up[1],ux[2]*up[0]-ux[0]*up[2],ux[0]*up[1]-ux[1]*up[0]];
  function at(u,v){let phi=u*Math.PI*2.,th=v*Math.PI;let qx=Math.sin(th)*Math.cos(phi), qy=Math.cos(th), qz=Math.sin(th)*Math.sin(phi);
    const p=[0,1,2].map(k=>center[k]+ux[k]*qx*r1+up[k]*qy*r2+uz[k]*qz*r1);
    let nor=[0,1,2].map(k=>ux[k]*qx/r1+up[k]*qy/r2+uz[k]*qz/r1);const nlen=Math.hypot(...nor)||1;nor=nor.map(t=>t/nlen);
    return [...p,...nor,u,v];}
  for(let j=0;j<rings;j++)for(let i=0;i<slices;i++){
    let a=at(i/slices,j/rings),b=at((i+1)/slices,j/rings),c=at(i/slices,(j+1)/rings),d=at((i+1)/slices,(j+1)/rings);
    floats.push(...a,...c,...b,...b,...c,...d);
  }
 }
 for(let k=0;k<5;k++){
  const pose=poses[k],x=18.4+k*5.15;
  const placement=[x,0,-.7+(k%2)*.22];
  function P(v){return [v[0]*S+placement[0],v[1]*S,v[2]*S+placement[2]];}
  function ell(a,b,r){a=P(a);b=P(b);const axis=b.map((v,j)=>v-a[j]);const len=Math.hypot(...axis);const unit=axis.map(v=>v/len);
   addEllipsoid(a.map((v,j)=>(v+b[j])/2),unit,r*S,len/2+r*S*.28);}
  const sh=pose.chest,hip=pose.hip;
  ell(hip,sh,.23);const head=pose.head;ell([head[0],head[1]-.11,head[2]], [head[0],head[1]+.09,head[2]],.145);
  for(const side of [-1,1]){
   const shoulder=[sh[0],sh[1]-.065,side*.19],h=[hip[0],hip[1],side*.13];
   const el=pose[side===1?'elL':'elR'],wr=pose[side===1?'wrL':'wrR'];
   const kn=pose[side===1?'knL':'knR'],ft=pose[side===1?'ftL':'ftR'];
   ell(shoulder,el,.090);ell(el,wr,.071);
   ell(h,kn,.130);ell(kn,ft,.095);
   ell(ft,[ft[0]+.12,ft[1]-.013,ft[2]],.068);
  }
 }
 return new Float32Array(floats);
}
