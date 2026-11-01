// Extracted from 001 v1.1; original sphere relief and photographic material.
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
