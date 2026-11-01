// Original Work09 deterministic positions and gravity equation.
const clamp=(x,a,b)=>Math.min(b,Math.max(a,x));
export function sourceData(){
function hash(i){let x=Math.sin(i*127.1+78.233)*43758.545;return x-Math.floor(x)}
const islands=Array.from({length:17},(_,i)=>({x:((i%5)-2)*4.35+(hash(i+4)-.5)*1.5,z:-7-(i*3.9)+hash(i+10)*4.4,y:-1.9+(hash(i+51)*1.1),w:2.1+hash(i+13)*2.55,d:3.2+hash(i+92)*3.6,phase:hash(i+25)*6.28}));
const balls=Array.from({length:12},(_,i)=>({x:(hash(i+41)-.5)*17,z:-6-hash(i+161)*62,y:-.85+hash(i+71)*2.8,r:.22+hash(i+81)*.27,phase:hash(i+91)*6.28}));
const bats=Array.from({length:9},(_,i)=>({x:(hash(i+143)-.5)*16,z:-9-hash(i+116)*62,y:-.9+hash(i+218)*4.5,phase:hash(i+131)*6.28,scale:.8+hash(i+99)*.9}));
const rocks=Array.from({length:28},(_,i)=>({x:(hash(i+211)-.5)*22,z:-5-hash(i+355)*67,y:-1+hash(i+418)*3.8,r:.18+hash(i+421)*.55,phase:hash(i+198)*6.28}));
return {islands,balls,bats,rocks};}
export function floatingHeight(base,phase,amplitude=1,gravity=1,time=0,motionReduced=false){const u=clamp(1-gravity,0,2.15);const rest=-2.02;const k=Math.min(1,u);const rise=u*(amplitude>2.8?0.72:amplitude>2?0.68:1.3)*amplitude;const osc=motionReduced?0:Math.sin(time*.39+phase)*(.04+.26*u);return rest*(1-k)+base*k+rise+osc}
