// Filming coordinates are local to each adopted work, never changes to its catalog.
const shotPoints=[
 [[0,8,0,4.05,0],[4,6,0,4.05,0]],
 [[-15,7,-4,3,0],[-9,5,6,3,0]],
 [[3,11,-5,.5,7],[1,9,-2,12,-6]],
 [[6.7,11.8,4.5,3,1.6],[4.8,10,0,3,-1]],
 [[-2.8,10.4,-7.2,3,7.7],[-.5,9,0,3,-4.4]],
 [[-8.8,6.3,0,4.3,0],[-4.8,3.8,0,3.7,0],[1,1.2,0,2.5,0],[.6,1.2,0,2.5,0]],
 [[-7,7,-5,4.3,2],[.1,1,0,4.2,0]],
 [[8,6,0,4.5,0],[4,2,0,4.5,0],[0,0,0,6.5,-4]],
 [[0,6,0,-.2,-10],[1.5,-24,-2,3,-39],[-1.7,-53,.3,3,-62]],
 [[0,-13.4,0,5,1.8],[0,-5.8,0,5,1.8],[-1,-5.3,0,5,1.8]]
];
const ease=t=>t*t*t*(t*(t*6-15)+10);
const lerp=(a,b,t)=>a.map((x,i)=>x+(b[i]-x)*t);
export const DURATION=120;
export function createTimeline(catalog,nav){
 let at=5;const shots=catalog.map((m,i)=>{const scale=m.scale||1,origin=m.origin;const points=shotPoints[i].map(([x,z,lx,ly,lz])=>({position:[origin[0]+x*scale,1.7,origin[2]+z*scale],look:[origin[0]+lx*scale,origin[1]+ly*scale,origin[2]+lz*scale]}));
 for(let j=1;j<points.length;j++){const a=points[j-1].position,b=points[j].position;if(!nav.clear({x:a[0],z:a[2]},{x:b[0],z:b[2]}))throw Error(`${m.id} の撮影経路が展示物に近すぎます`)}
 const duration=i===5?18:9,transition=i===5?1.6:.925,shot={id:m.id,title:m.title,start:at,end:at+duration,points,knots:i===5?[0,.38,.78,1]:points.map((_,j)=>j/(points.length-1))};at=shot.end+(i<9?transition:0);shot.nextAt=at;return shot;
 });
 return {shots,creditsAt:at,duration:DURATION};
}
export function sampleShot(shot,t){const u=Math.max(0,Math.min(1,t));let i=0;while(i<shot.knots.length-2&&u>shot.knots[i+1])i++;const f=ease((u-shot.knots[i])/(shot.knots[i+1]-shot.knots[i]));return {position:lerp(shot.points[i].position,shot.points[i+1].position,f),look:lerp(shot.points[i].look,shot.points[i+1].look,f)};}
export function sampleTimeline(timeline,time){
 const t=Math.max(0,Math.min(DURATION,time)),shots=timeline.shots;
 if(t<5)return {phase:'title',id:'001',opacity:1-Math.max(0,(t-4)/1),pose:sampleShot(shots[0],0),audio:false};
 for(let i=0;i<shots.length;i++){const s=shots[i];if(t<s.end)return {phase:'shot',id:s.id,opacity:0,pose:sampleShot(s,(t-s.start)/(s.end-s.start)),audio:s.id==='006'};
 if(i<9&&t<s.nextAt){const u=(t-s.end)/(s.nextAt-s.end),cut=u>=.25,next=shots[i+1];return {phase:'transition',id:cut?next.id:s.id,opacity:u<.25?ease(u/.25):u<.75?1:1-ease((u-.75)/.25),pose:cut?sampleShot(next,0):sampleShot(s,1),audio:false}}}
 return {phase:'credits',id:'010',opacity:Math.min(1,(t-timeline.creditsAt)/.6),pose:sampleShot(shots[9],1),audio:false};
}
export function createFilmClock(){let elapsed=0,last=null,paused=false;return {reset(now){elapsed=0;last=now;paused=false},tick(now){if(last!==null&&!paused)elapsed+=Math.max(0,(now-last)/1000);last=now;return elapsed},pause(now){this.tick(now);paused=true},resume(now){last=now;paused=false},get paused(){return paused},get elapsed(){return elapsed}}}
