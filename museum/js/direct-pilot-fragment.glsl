#version 300 es
precision highp float;
out vec4 fragColor;
uniform vec2 uRes;uniform float uTime;uniform vec3 uCam;uniform mat3 uRot;uniform float uQuality;uniform sampler2D uBallPhoto; uniform float uPhotoReady; uniform float uGhostReady; uniform float uWalkProgress;uniform int uFigureMode;
uniform int uMaterialMode;
uniform float uFocal;
uniform sampler2D uBallMicro; uniform float uMicroReady;
uniform sampler2D uGhost0;uniform sampler2D uGhost1;uniform sampler2D uGhost2;uniform sampler2D uGhost3;uniform sampler2D uGhost4;
#define PI 3.14159265359
float hash1(float n){return fract(sin(n*127.1)*43758.5453);}
float hash2(vec2 p){return fract(sin(dot(p,vec2(127.1,311.7)))*43758.5453123);}
float noise(vec3 p){vec3 i=floor(p),f=fract(p);f=f*f*(3.-2.*f);float n=dot(i,vec3(1.,57.,113.));return mix(mix(mix(hash1(n),hash1(n+1.),f.x),mix(hash1(n+57.),hash1(n+58.),f.x),f.y),mix(mix(hash1(n+113.),hash1(n+114.),f.x),mix(hash1(n+170.),hash1(n+171.),f.x),f.y),f.z);}
float fbm(vec3 p){float a=.5,v=0.;for(int i=0;i<4;i++){v+=a*noise(p);p*=2.12;a*=.5;}return v;}
float sdCapsule(vec3 p, vec3 a, vec3 b, float r){vec3 pa=p-a,ba=b-a;float h=clamp(dot(pa,ba)/dot(ba,ba),0.,1.);return length(pa-ba*h)-r;}
const vec3 ballCenter=vec3(0.,4.05,0.);const float R=2.18;
float hitSphere(vec3 ro,vec3 rd,vec3 ce,float ra){vec3 o=ro-ce;float b=dot(o,rd);float c=dot(o,o)-ra*ra;float h=b*b-c;if(h<0.)return 1e10;h=sqrt(h);float t=-b-h;return t>.0001?t:(-b+h>.0001?-b+h:1e10);}
const vec3 seamNormal=vec3(.927,.062,-.370);
// A continuous great-circle seam in actual 3D spherical coordinates.
// Raised rows and individual stitch bumps are displaced in the ray/sphere intersection.
float seamHeight(vec3 d){
 // Lightweight analytic relief. Evaluate once at intersection; no nested ray marching.
 float s=dot(d,seamNormal)*R;
 if(abs(s)>.16)return 0.;
 vec3 su=normalize(cross(seamNormal,vec3(0.,1.,0.)));
 vec3 sv=normalize(cross(seamNormal,su));
 float ang=atan(dot(d,sv),dot(d,su));
 float rib=.5+.5*cos(ang*96.);
 float stitch=pow(rib,8.);
 return exp(-pow(s/.063,2.))*(.008+.011*stitch);
}
// v1.1: stitch rows run around the whole sphere, not merely across the projected image.
// Each row has a narrow raised welt and a separate rhythm of transverse thread loops.
float seamHeightV11(vec3 d){
 float s=dot(d,seamNormal)*R;
 if(abs(s)>.38)return 0.;
 vec3 su=normalize(cross(seamNormal,vec3(0.,1.,0.)));
 vec3 sv=normalize(cross(seamNormal,su));
 float ang=atan(dot(d,sv),dot(d,su));
 float h=0.;
 for(int i=0;i<5;i++){
   float row=(float(i)-2.)*.106;
   float off=s-row;
   float rib=exp(-pow(off/.032,2.));
   float phase=fract(ang*12.4+float(i)*.31);
   float stitch=exp(-pow((phase-.5)/.27,2.));
   // Offset center subtly as a thread crosses the stitched channel.
   float lace=exp(-pow((off+(phase-.5)*.046)/.024,2.))*stitch;
   h+=.011*rib+.024*lace;
 }
 return h;
}
vec3 surfaceNormalV11(vec3 d){
 float s=dot(d,seamNormal)*R;
 if(abs(s)>.39)return d;
 // Finite-difference relief normal along both local sphere tangent directions.
 vec3 u=normalize(seamNormal-dot(seamNormal,d)*d);
 vec3 v=normalize(cross(d,u));
 float eps=.007;
 float du=(seamHeightV11(normalize(d+u*eps))-seamHeightV11(normalize(d-u*eps)))/(2.*R*eps);
 float dv=(seamHeightV11(normalize(d+v*eps))-seamHeightV11(normalize(d-v*eps)))/(2.*R*eps);
 return normalize(d-du*u-dv*v);
}
vec3 surfaceNormal(vec3 d){
 float s=dot(d,seamNormal)*R;
 if(abs(s)>.18)return d;
 // Small analytic tilt of the normal toward the raised stitch ridges.
 vec3 tangent=seamNormal-dot(seamNormal,d)*d;
 float tilt=exp(-pow(s/.083,2.))*s*1.8;
 return normalize(d-tangent*tilt);
}
float ballHit(vec3 ro,vec3 rd){
 float t=hitSphere(ro,rd,ballCenter,R);
 if(uMaterialMode==0||t>1e9)return t;
 vec3 d=normalize(ro+rd*t-ballCenter);
 float dh=uMaterialMode==3?seamHeightV11(d):seamHeight(d);
 return max(.01,t-dh/max(.32,abs(dot(d,rd))));
}
float softShadow(vec3 p){float d=length(p.xz-ballCenter.xz);return (1.-smoothstep(.9,5.8,d))*exp(-abs(p.y)*2.0);}
vec3 ballSurface(vec3 pos,vec3 normal,vec3 rd){
 vec3 d=normalize(pos-ballCenter);float sd=dot(d,seamNormal);
 if(uMaterialMode==3)normal=surfaceNormalV11(d);
 else if(uMaterialMode!=0)normal=surfaceNormal(d);
 // Local seam tangent coordinates, to map stitch placement consistently around the ball.
 vec3 u=normalize(cross(seamNormal,vec3(0.,1.,0.)));vec3 v=normalize(cross(seamNormal,u));
 float theta=atan(dot(d,v),dot(d,u));float stitchPattern=abs(fract(theta*29.0/PI)*2.-1.);
 float ringDist=abs(sd)*R;
 float leather=fbm(d*84.)*.14+noise(d*250.)*.075+noise(d*20.)*.13;
 float wear=fbm(d*6.7);
 // Irregular scarred cream-leather with small dark patina flecks.
 vec3 leatherColor=mix(vec3(.68,.655,.595),vec3(.85,.84,.787),clamp(.37+wear*.55+leather*.56,0.,1.));
 float patina=smoothstep(.65,.81,fbm(d*15.7)+.13*noise(d*135.));
 leatherColor=mix(leatherColor,vec3(.41,.38,.32),patina*.54);
 float scratch=smoothstep(.925,.985,noise(d*420.))*smoothstep(.2,.8,wear);
 leatherColor=mix(leatherColor,vec3(.93,.89,.82),scratch*.32);
 if(uMaterialMode==3){
   float pore=noise(d*415.);
   float dry=fbm(d*22.1)-.5;
   leatherColor*=.94+.09*pore+.12*dry;
 }
 // Parallel seam channels, braided stitches and the center raised seam.
 float centerLine=1.-smoothstep(.022,.049,ringDist);
 float seamOuter=1.-smoothstep(.09,.125,ringDist);
 float seamStitchZone=(1.-smoothstep(.19,.205,ringDist))*smoothstep(.02,.048,ringDist);
 float channels=0.;float threads=0.;
 for(int i=0;i<5;i++){
   float off=(float(i)-2.)*.044;
   float dd=abs(sd*R-off);
   float channel=1.-smoothstep(.009,.016,dd);
   channels+=channel;
   // Each tiny transverse stitch appears as a slanted stitch loop.
   float curve=abs(fract(theta*48.0/PI+float(i)*.35)-.5);
   float thread=(1.-smoothstep(.12,.20,curve))*(1.-smoothstep(.012,.019,dd));
   threads+=thread;
 }
 leatherColor=mix(leatherColor,vec3(.30,.27,.23),clamp(channels*.59+seamOuter*.27,0.,.9));
 leatherColor=mix(leatherColor,vec3(.90,.86,.76),clamp(threads*.85,0.,.95));
 leatherColor=mix(leatherColor,vec3(.55,.5,.41),centerLine*.72);
 if(uMaterialMode==3){
   // Fine five-row stitch construction, consistent when walking around the back.
   float rows=0.,lace=0., grooves=0.;
   for(int i=0;i<5;i++){
     float row=(float(i)-2.)*.106;
     float off=sd*R-row;
     float c=exp(-pow(off/.031,2.));
     float phase=fract(theta*12.4+float(i)*.31);
     float thread=exp(-pow((phase-.5)/.27,2.))*exp(-pow((off+(phase-.5)*.046)/.021,2.));
     rows+=c;lace+=thread;
     grooves+=exp(-pow(abs(off)/.014,2.));
   }
   leatherColor=mix(leatherColor,vec3(.34,.30,.255),min(.68,grooves*.27));
   leatherColor=mix(leatherColor,vec3(.83,.76,.65),min(.9,rows*.24+lace*.69));
 }
 // Bumpy lighting from grain and stitched ridges.
 float micro=noise(d*225.);vec3 bump=normalize(normal+vec3(noise(d*225.+vec3(7.,2.,1.))-.5,noise(d*225.+vec3(1.,4.,5.))-.5,micro-.5)*.10+seamNormal*sd*seamOuter*.05);
 vec3 key=normalize(vec3(-.46,.92,.57));vec3 fill=normalize(vec3(.78,.25,-.15));
 float diff=max(dot(bump,key),0.);float back=max(dot(bump,fill),0.);
 float spec=pow(max(dot(reflect(-key,bump),-rd),0.),38.)*.23;
 float rim=pow(1.-max(dot(normal,-rd),0.),2.5);
 vec3 shaded=leatherColor*(vec3(.18,.2,.23)+vec3(1.11,1.06,.98)*diff*.90+vec3(.29,.32,.37)*back*.38);
 shaded+=vec3(.95,.9,.8)*spec+vec3(.21,.22,.23)*rim*.5;
 // Faithful front-facing texture from the original high-resolution concept artwork.
 // The reference is one perspective only: uncovered back/side surfaces remain procedural estimates.
 vec2 photoUV = vec2(.5 + d.x*.5, .5 + d.y*.5);
 vec2 puv=clamp(photoUV,vec2(.003),vec2(.997));
 vec3 photo = texture(uBallPhoto,puv).rgb;
 float photoBlend = uPhotoReady * smoothstep(-.1,.62,d.z)*.98;
 if(uMaterialMode==1)photoBlend=0.;
 if(uMaterialMode==3)photoBlend=uPhotoReady*smoothstep(-.18,.50,d.z)*.985;
 if(uMaterialMode==2){
   // The concept image contains baked illumination. Preserve it, adding only gentle
   // geometric shading to stitches and not double-lighting the whole photo.
   float seamMask=1.-smoothstep(.11,.23,abs(sd)*R);
   float lightRelief=clamp(.73+.50*max(dot(normal,key),0.)+.12*max(dot(normal,fill),0.),.64,1.26);
   photo*=mix(1.,lightRelief,seamMask*.55);
 }
 if(uMaterialMode==3){
   // The artwork carries its own baked light. Use the source only for albedo/details
   // and modulate gently with the photo-derived high-frequency relief normals.
   vec3 micron=texture(uBallMicro,puv).rgb*2.-1.;
   float nlight=clamp(micron.x*.24+micron.y*.18,-.21,.21);
   float seamFactor=1.-smoothstep(.17,.40,abs(sd)*R);
   float shallow=max(dot(normal,key),0.)-max(dot(d,key),0.);
   float daylight=clamp(1.+nlight*uMicroReady*.56+shallow*seamFactor*.25,.82,1.19);
   photo*=daylight;
   // Suppress the overly bright, showroom-like highlights on the procedural back.
   shaded*=.95;
 }
 return mix(shaded, photo, photoBlend);
}
vec3 slabColor(vec3 p, int kind){
 float large=fbm(p*1.2),fine=noise(p*19.);vec3 base;
 if(kind==0){ // floor
  base=vec3(.145,.148,.146)+(large-.45)*.057+(fine-.5)*.022;
  // large polished concrete slab joints
  float gx=abs(fract((p.x+20.)/4.)-.5),gz=abs(fract((p.z+30.)/5.)-.5);
  base*=1.-(1.-smoothstep(.002,.005,min(gx,gz)))*.14;
  if(p.x>12.5){
    base=vec3(.080,.090,.100)+(large-.46)*.027+(fine-.5)*.009;
    float edge=1.-smoothstep(.025,.05,abs(abs(p.z+.1)-3.8));
    base+=vec3(.045,.040,.033)*edge*(1.-smoothstep(18.,42.,p.x))*.4;
    float axis=exp(-pow(p.z/1.0,2.))*.015;
    base+=vec3(axis);
  }
  // Extremely faint trace of a pitch rectangle under the floating object.
  float lineX=1.-smoothstep(.015,.05,abs(abs(p.x)-2.95));
  float lineZ=1.-smoothstep(.015,.05,abs(abs(p.z)-3.2));
  float marks=max(lineX*(1.-smoothstep(3.25,3.33,abs(p.z))),lineZ*(1.-smoothstep(2.95,3.05,abs(p.x))));
  if(p.x<12.5)base=mix(base,vec3(.33,.33,.32),marks*.33);
 } else if(kind==1){base= p.x>12.5 ?vec3(.033,.045,.052)+(large-.5)*.011 : vec3(.087,.095,.102)+(large-.5)*.019+(fine-.5)*.012;
  float joint=1.-smoothstep(.004,.013,abs(fract(p.y/4.)-.5));base*=1.-joint*.15;
 } else {base=p.x>12.5 ?vec3(.042,.052,.057)+(large-.5)*.018:vec3(.065,.071,.077)+(large-.5)*.021;}
 return base;
}
// Two physically connected gallery rooms. The side opening is a real passage, not a scene switch.
bool inA(vec3 p){return abs(p.x)<12.5&&p.z>-14.&&p.z<17.;}
bool inB(vec3 p){return p.x>12.5&&p.x<46.&&p.z>-8.&&p.z<14.;}
bool inLobby(vec3 p){return abs(p.x)<12.5&&p.z>=17.&&p.z<28.;}
bool isDoor(vec3 p){return p.y<7.&&p.y>=0.&&p.z>1.&&p.z<13.;}
bool isLobbyDoor(vec3 p){return p.y<7.&&p.y>=0.&&abs(p.x)<8.;}
vec3 environment(vec3 ro,vec3 rd){
 float tmin=1e10;int mat=0;vec3 nn=vec3(0.);
 float ts=ballHit(ro,rd);if(ts<tmin){tmin=ts;mat=1;}
 // contiguous floor planes
 if(rd.y<-.0001){float t=-ro.y/rd.y;vec3 p=ro+rd*t;if(t>0.&&t<tmin&&(inA(p)||inB(p)||inLobby(p))){tmin=t;mat=2;nn=vec3(0.,1.,0.);}}
 if(rd.y>.0001){float t=(10.5-ro.y)/rd.y;vec3 p=ro+rd*t;if(t>0.&&t<tmin&&(inA(p)||inB(p)||inLobby(p))){tmin=t;mat=3;nn=vec3(0.,-1.,0.);}}
 // West edge of A
 if(rd.x<-.0001){float t=(-12.5-ro.x)/rd.x;vec3 p=ro+rd*t;if(t>0.&&t<tmin&&p.y>=0.&&p.y<10.5&&p.z>-14.&&p.z<28.){tmin=t;mat=4;nn=vec3(1.,0.,0.);}}
 // Shared wall at x=12.5 with a genuine opening (height 4.8m)
 if(abs(rd.x)>.0001){float t=(12.5-ro.x)/rd.x;vec3 p=ro+rd*t;if(t>0.&&t<tmin&&p.y>=0.&&p.y<10.5&&p.z>-14.&&p.z<17.&&!isDoor(p)){tmin=t;mat=4;nn=vec3(-sign(rd.x),0.,0.);}}
 // Lobby east wall; the shared gallery wall below has its own opening.
 if(rd.x>.0001){float t=(12.5-ro.x)/rd.x;vec3 p=ro+rd*t;if(t>0.&&t<tmin&&p.y>=0.&&p.y<10.5&&p.z>=17.&&p.z<28.){tmin=t;mat=4;nn=vec3(-1.,0.,0.);}}
 // Far end of B
 if(rd.x>.0001){float t=(46.-ro.x)/rd.x;vec3 p=ro+rd*t;if(t>0.&&t<tmin&&p.y>=0.&&p.y<10.5&&p.z>-8.&&p.z<14.){tmin=t;mat=4;nn=vec3(-1.,0.,0.);}}
 // The entrance hall and gallery share a real opening at z=17.
 if(abs(rd.z)>.0001){float t=(17.-ro.z)/rd.z;vec3 p=ro+rd*t;if(t>0.&&t<tmin&&p.y>=0.&&p.y<10.5&&abs(p.x)<12.5&&!isLobbyDoor(p)){tmin=t;mat=4;nn=vec3(0.,0.,-sign(rd.z));}}
 // Back walls of the gallery and entrance hall.
 if(abs(rd.z)>.0001){float plane=rd.z>0.?28.:-14.;float t=(plane-ro.z)/rd.z;vec3 p=ro+rd*t;if(t>0.&&t<tmin&&p.y>=0.&&p.y<10.5&&abs(p.x)<12.5){tmin=t;mat=4;nn=vec3(0.,0.,-sign(rd.z));}}
 // B front/rear
 if(abs(rd.z)>.0001){float plane=rd.z>0.?14.:-8.;float t=(plane-ro.z)/rd.z;vec3 p=ro+rd*t;if(t>0.&&t<tmin&&p.y>=0.&&p.y<10.5&&p.x>12.5&&p.x<46.){tmin=t;mat=4;nn=vec3(0.,0.,-sign(rd.z));}}
 if(mat==0) return vec3(.035,.04,.047);
 vec3 p=ro+rd*tmin;
 if(mat==1){vec3 n=normalize(p-ballCenter);vec3 col=ballSurface(p,n,rd);
   float darkDistance=1.-smoothstep(20.,50.,tmin)*.7;return col*darkDistance;}
 vec3 col=slabColor(p,mat==2?0:(mat==3?2:1));
 float envLight=.32;
 if(p.x<12.5){
  vec3 keyPos=vec3(-1.5,10.2,2.0);
  vec3 l=keyPos-p;float len=length(l);vec3 ln=l/len;
  float dif=max(dot(nn,ln),0.);
  envLight+=dif*3.6/(1.+len*.22+len*len*.035);
  for(int i=0;i<6;i++){
   float x=(mod(float(i),2.)<.5?-6.2:6.2);float z=-8.6+floor(float(i)/2.)*7.5;
   vec3 lv=vec3(x,9.9,z)-p;float dst=length(lv);vec3 ll=lv/dst;
   envLight+=max(dot(nn,ll),0.)*2.1/(1.+dst*.25+dst*dst*.05);
  }
  if(mat==2){
   float pool=exp(-dot(p.xz,p.xz)/25.);
   envLight+=pool*.23;envLight*=1.-softShadow(p)*.28;
   vec3 reflectDir=reflect(rd,nn);float refl=hitSphere(p+nn*.02,reflectDir,ballCenter,R);
   if(refl<1e9){vec3 q=p+nn*.02+reflectDir*refl;vec3 reflected=ballSurface(q,normalize(q-ballCenter),reflectDir);
    col=mix(col,reflected*.32,.18*pow(max(0.,dot(nn,-rd)),1.5));}
  }
 }else{
  // The second hall is deliberately darker and has a rhythmic row of spotlights.
  envLight=.26;
  for(int i=0;i<5;i++){
    float x=18.4+float(i)*5.15;
    vec3 lv=vec3(x,10.2,-1.1)-p;
    float d=length(lv);
    envLight+=max(dot(nn,lv/d),0.)*6.5/(1.+d*.32+d*d*.082);
  }
  if(mat==2){
    for(int i=0;i<5;i++){
     float dist=length(p.xz-vec2(18.4+float(i)*5.15,-.7));
     envLight+=exp(-dist*dist/5.)*.15;
    }
  }
 }
 if(p.z>17.) envLight+=.35;
 col*=envLight;
 if(mat==3){
  if(p.x<12.5){if(abs(p.x)<1.7&&abs(p.z)<2.6)col+=vec3(.20,.22,.25);
    float d=length(p.xz-vec2(-1.5,2.0));col+=vec3(.83,.84,.83)*(1.-smoothstep(.22,.48,d))*.52;}
  else {float slot=1.-smoothstep(.13,.21,abs(fract((p.x-18.4)/5.15)-.5));col+=vec3(.06,.08,.095)*slot;}
 }
 if(mat==4){
  float relief=1.-smoothstep(.01,.035,abs(fract(p.z/6.)-.5));col*=1.-relief*.11;
  if(abs(p.z+14.)<.03&&abs(p.x-7.5)<1.2&&p.y<3.2)col=mix(col,vec3(.018,.019,.02),.9);
  // A warm thin edge at the passage gives the visitor an architectural cue.
  if(abs(p.x-12.5)<.02&&p.z>.8&&p.z<13.2&&p.y<7.3){
    float ed=min(min(abs(p.z-1.),abs(p.z-13.)),abs(p.y-7.));
    col+=vec3(.19,.15,.095)*(1.-smoothstep(.12,.46,ed));
  }
 }
 col=mix(col,vec3(.048,.056,.068),clamp(tmin/49.,0.,.24));
 return col;
}
vec4 oneGhost(int idx,vec2 uv){
 if(idx==0)return texture(uGhost0,uv);
 if(idx==1)return texture(uGhost1,uv);
 if(idx==2)return texture(uGhost2,uv);
 if(idx==3)return texture(uGhost3,uv);
 return texture(uGhost4,uv);
}
// Image-derived translucent installation planes. These are intentionally *not* claimed as full 3D humans.
vec3 ghostInstallation(vec3 ro,vec3 rd){
 if(uGhostReady<.5||abs(rd.x)<.0001)return vec3(0.);
 vec3 accum=vec3(0.);
 for(int i=0;i<5;i++){
  float px=18.4+float(i)*5.15;
  float t=(px-ro.x)/rd.x;
  if(t<=.08||t>85.)continue;
  vec3 p=ro+rd*t;
  // An opaque wall between the camera and any figure must not be transparent.
  if(ro.x<12.5){float wt=(12.5-ro.x)/rd.x;
    if(wt>0.&&wt<t&&!isDoor(ro+rd*wt))continue;
  }
  // figure screens are real, spaced gallery installations parallel to the wall opening
  float wd=i==0?3.35:(i==1?2.8:(i==2?2.9:(i==3?3.15:3.75)));
  float ht=i==0?6.55:(i==1?6.4:(i==2?6.15:(i==3?5.7:4.35)));
  float zc=i==0?-.9:(i==1?-1.0:(i==2?-.6:(i==3?-.8:-1.0)));
  vec2 uv=vec2((p.z-zc)/wd+.5,p.y/ht);
  if(uv.x<=.002||uv.x>=.998||uv.y<=.003||uv.y>=.997)continue;
  vec4 tex=oneGhost(i,uv);
  float gl=clamp((tex.r+tex.g+tex.b)*.333,0.,1.);
  float focus=1.-smoothstep(1.,10.,abs(ro.x-px));
  float phase=float(i)*.25;float sequence=exp(-pow((uWalkProgress-phase)*5.,2.));
  float exposure=.32+focus*.58+sequence*.50;
  float a=tex.a*exposure;
  vec3 luminous=pow(tex.rgb,vec3(1.3))*a*(1.1+focus*.2);
  accum+=luminous;
  // halo on the edge of the motion layer
  accum+=vec3(.12,.105,.08)*pow(gl,4.)*tex.a*.3;
 }
 return accum;
}

void main(){
 vec2 uv=(gl_FragCoord.xy-.5*uRes)/min(uRes.x,uRes.y);
 vec3 rd=normalize(uRot*vec3(uv.x,uv.y,-uFocal));
 vec3 col=environment(uCam,rd);
 if(uFigureMode==0)col+=ghostInstallation(uCam,rd);
 // Subtle floating dust illuminated by the gallery light.
 float dust=0.;vec3 rayp=uCam+rd*7.;for(int i=0;i<5;i++){vec3 pp=rayp+rd*float(i)*1.8;
   float dotDust=pow(noise(pp*66.+vec3(uTime*.008)),20.);
   dust+=dotDust*exp(-length(pp.xz)*.11)*.032;}
 col+=vec3(.9,.77,.6)*dust;
 col=col/(vec3(1.)+col*.46); // gentle filmic compression
 col=pow(max(col,0.),vec3(1./2.2));
 float vign=1.-.23*pow(length(uv)*.66,2.);col*=vign;
 float grain=(hash2(gl_FragCoord.xy+floor(uTime*10.))-.5)*.007;
 fragColor=vec4(col+grain,1.);
}
