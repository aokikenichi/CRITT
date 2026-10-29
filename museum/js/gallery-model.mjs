// Metres in a single continuous floor plan. Camera yaw 0 looks down -Z.
export const ENTRANCE = Object.freeze({x:0,z:8,yaw:0,pitch:0});
export const ROOMS = [
 {id:1,name:'静止と時間',x1:-18,x2:-3,z1:-16,z2:-4,cx:-10.5,cz:-10,height:5.6,color:'#b8aa8a'},
 {id:2,name:'線と所有',x1:3,x2:19,z1:-29,z2:-15,cx:11,cz:-22,height:5,color:'#bb8e71'},
 {id:3,name:'身体と群衆',x1:-21,x2:-3,z1:-42,z2:-26,cx:-12,cz:-34,height:6.4,color:'#698c8c'},
 {id:4,name:'記憶と軌跡',x1:3,x2:19,z1:-53,z2:-39,cx:11,cz:-46,height:5.2,color:'#a292b7'},
 {id:5,name:'重力と境界',x1:-11,x2:11,z1:-77,z2:-58,cx:0,cz:-67,height:7,color:'#718baf'}
];
const titles=['空中で止まった一球','22ヤードの永遠','境界線を引く者','奪い返されたゲーム','11の身体','十万人の声','スコアカードにない名前','球の星座','重力のないクリケット','最後のバウンダリー'];
const variants=['quality_lab_v1.1','3d_lab_v1.2','boundary_rope_lab_v1.9','hybrid_walk_v2.3','hybrid_walk_v2.4','hybrid_walk_v2.5','hybrid_walk_v2.6','pulse_wicket_v2.9'];
export const WORKS=titles.map((title,i)=>{
 const id=String(i+1).padStart(3,'0'), room=ROOMS[Math.floor(i/2)], side=i%2;
 const x=room.id===5?(side?5:-5):(room.cx<0?room.x1+0.4:room.x2-0.4);
 const z=room.id===5?-76.5:room.cz+(side?3.1:-3.1);
 const yaw=room.id===5?0:(room.cx<0?Math.PI/2:-Math.PI/2);
 const spot={x:room.id===5?x:x+(room.cx<0?4:-4),z:room.id===5?z+4:z,yaw,pitch:0};
 const preview=i===1?'qa-results/step04/002-operated-pc.png':i<8?`qa-results/step04/${id}-${variants[i]}-pc.png`:`qa-results/desktop-${id}.png`;
 return {id,title,room:room.id,variant:variants[i]||null,url:i<8?`review-work.html?id=${id}&variant=${variants[i]}`:`work.html?id=${id}`,x,z,yaw,spot,preview,
 note:i<2?'第1室試作／技術検証版（001・002複合ラボ）':i===7?'初期表示は架空の120球データ':i===8?'現行再構築版 v0.5':i===9?'現行再構築版 v1.0':'α版採用作品'};
});
export const FLOORS=[{x1:-8,x2:8,z1:-2,z2:12},{x1:-3,x2:3,z1:-60,z2:0},...ROOMS];
export const WALLS=[];
const wall=(x1,x2,z1,z2,h=5)=>WALLS.push({x1,x2,z1,z2,h});
// Lobby boundary leaves the corridor opening on its north side.
wall(-8.2,-7.9,-2,12,6);wall(7.9,8.2,-2,12,6);wall(-8,8,11.9,12.2,6);
wall(-8,-3,-2.15,-1.9,6);wall(3,8,-2.15,-1.9,6);
for(const side of [-1,1]){
 const doors=ROOMS.filter(r=>r.id<5&&Math.sign(r.cx)===side).map(r=>[r.cz-2,r.cz+2]).sort((a,b)=>a[0]-b[0]);
 let last=-58;
 for(const [a,b] of doors){wall(side*3-.12,side*3+.12,last,a);last=b;}
 wall(side*3-.12,side*3+.12,last,-2);
}
for(const r of ROOMS){
 wall(r.x1,r.x2,r.z1-.12,r.z1+.12,r.height);
 if(r.id===5){wall(r.x1,-2,r.z2-.12,r.z2+.12,r.height);wall(2,r.x2,r.z2-.12,r.z2+.12,r.height);}
 else wall(r.x1,r.x2,r.z2-.12,r.z2+.12,r.height);
 if(r.id===5||r.cx<0)wall(r.x1-.12,r.x1+.12,r.z1,r.z2,r.height);
 if(r.id===5||r.cx>0)wall(r.x2-.12,r.x2+.12,r.z1,r.z2,r.height);
}
export function canStand(x,z,radius=.28){
 if(!FLOORS.some(f=>x>=f.x1&&x<=f.x2&&z>=f.z1&&z<=f.z2))return false;
 return !WALLS.some(w=>x>w.x1-radius&&x<w.x2+radius&&z>w.z1-radius&&z<w.z2+radius);
}
export function move(p,dx,dz){
 // Substeps prevent tunnelling, including after a slow frame.
 const n=Math.max(1,Math.ceil(Math.hypot(dx,dz)/.12));
 for(let i=0;i<n;i++){if(canStand(p.x+dx/n,p.z))p.x+=dx/n;if(canStand(p.x,p.z+dz/n))p.z+=dz/n;}
 return p;
}
export function roomAt(p){return ROOMS.find(r=>p.x>r.x1+.15&&p.x<r.x2-.15&&p.z>r.z1&&p.z<r.z2)?.id||0;}
export function safePose(p){return p&&['x','z','yaw','pitch'].every(k=>Number.isFinite(p[k]))&&canStand(p.x,p.z)?{x:p.x,z:p.z,yaw:p.yaw,pitch:Math.max(-.65,Math.min(.65,p.pitch))}:{...ENTRANCE};}
export function nearestWork(p){return WORKS.filter(w=>roomAt(p)===w.room&&Math.hypot(p.x-w.x,p.z-w.z)<6&&Math.abs(w.room===5?p.x-w.x:p.z-w.z)<2.7).sort((a,b)=>Math.hypot(p.x-a.x,p.z-a.z)-Math.hypot(p.x-b.x,p.z-b.z))[0]||null;}
export const TOUR=[];
for(const r of ROOMS){
 TOUR.push({x:0,z:r.id===5?-60:r.cz});
 if(r.id<5)TOUR.push({x:r.cx,z:r.cz});
 for(const w of WORKS.filter(w=>w.room===r.id))TOUR.push({...w.spot,work:w.id});
 if(r.id<5){TOUR.push({x:r.cx,z:r.cz});TOUR.push({x:0,z:r.cz});}
}
