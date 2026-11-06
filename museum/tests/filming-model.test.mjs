import {test} from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {catalog} from '../exhibits/shared/catalog.mjs';
import {makeNavigation} from '../js/ten-exhibit-model.mjs';
import {DURATION,createTimeline,sampleShot,sampleTimeline,createFilmClock} from '../js/filming-model.mjs';
import {equations} from '../exhibits/010/source-equations.mjs';

const obstacles=[{x:0,z:0,r:2.35}];
for(const id of ['004','005']){
 const data=JSON.parse(await readFile(new URL(`../exhibition-assets/${id}/data.json`,import.meta.url),'utf8'));
 const meta=catalog.find(work=>work.id===id),scale=meta.scale||1;
 for(const work of data.workdata||data.works){
  if(work.kind==='scrim')continue;
  obstacles.push({x:meta.origin[0]+work.x*scale,z:meta.origin[2]+work.z*scale,r:.48});
 }
}
const nav=makeNavigation(obstacles),timeline=createTimeline(catalog,nav);
const close=(actual,expected,epsilon=1e-8)=>assert.ok(Math.abs(actual-expected)<epsilon,`${actual} differs from ${expected}`);

test('120-second programme includes ordered ten works, 18-second sound work, opening and ending',()=>{
 assert.equal(DURATION,120);
 assert.deepEqual(timeline.shots.map(shot=>shot.id),Array.from({length:10},(_,i)=>String(i+1).padStart(3,'0')));
 assert.equal(sampleTimeline(timeline,0).phase,'title');
 close(timeline.shots[0].start,5);
 for(const shot of timeline.shots){close(shot.end-shot.start,shot.id==='006'?18:9)}
 close(timeline.creditsAt,113);assert.equal(sampleTimeline(timeline,119.999).phase,'credits');assert.equal(sampleTimeline(timeline,120).phase,'credits');
 const observed=[];for(let t=0;t<=120;t+=.05){const sample=sampleTimeline(timeline,t);if(sample.phase==='shot'&&observed.at(-1)!==sample.id)observed.push(sample.id)}
 assert.deepEqual(observed,timeline.shots.map(shot=>shot.id));
});

test('every sampled camera position and movement stays in the actual walkable space',()=>{
 assert.ok(obstacles.length>2,'real 004 and 005 asset obstacles must be loaded');
 for(const shot of timeline.shots){
  let previous=null;
  for(let n=0;n<=900;n++){
   const pose=sampleShot(shot,n/900),[x,y,z]=pose.position;
   assert.ok([...pose.position,...pose.look].every(Number.isFinite),`${shot.id}: non-finite pose`);
   assert.equal(y,1.7,`${shot.id}: common eye height`);
   assert.ok(nav.walkable(x,z),`${shot.id}: blocked at ${x},${z}`);
   if(previous)assert.ok(nav.clear(previous,{x,z}),`${shot.id}: blocked camera movement`);
   previous={x,z};
  }
 }
});

test('009 moves through original spatial gravity thresholds after applying its scale and origin',()=>{
 const shot=timeline.shots.find(s=>s.id==='009'),meta=catalog.find(s=>s.id==='009'),regions=new Set();
 for(let n=0;n<=500;n++){
  const [x,,z]=sampleShot(shot,n/500).position,localZ=(z-meta.origin[2])/meta.scale;
  regions.add(localZ> -16?'1G':localZ> -43?'quarterG':'0G');
  assert.ok(Math.abs((x-meta.origin[0])/meta.scale)<2,'stay on original narrow approach');
 }
 assert.deepEqual([...regions],['1G','quarterG','0G']);
});

test('010 actually crosses the boundary and holds inside for the visible response',()=>{
 const shot=timeline.shots.find(s=>s.id==='010'),meta=catalog.find(s=>s.id==='010');
 const level=(u,time)=>{const [x,,z]=sampleShot(shot,u).position;return equations({artTime:time,crossCount:0}).boundaryLevel(x-meta.origin[0],z-meta.origin[2])};
 for(const time of [0,30,120]){
  assert.ok(level(0,time)>0,'shot starts outside');assert.ok(level(.75,time)<0,'shot reaches inside');assert.ok(level(1,time)<0,'shot finishes inside');
 }
});

test('all inter-work repositioning happens under an opaque fade, with the 006 tail preserved',()=>{
 for(let i=0;i<timeline.shots.length-1;i++){
  const shot=timeline.shots[i],duration=shot.nextAt-shot.end,cutAt=shot.end+duration*.25;
  if(shot.id==='006')close(duration,1.6);
  const before=sampleTimeline(timeline,cutAt-.000001),after=sampleTimeline(timeline,cutAt+.000001);
  assert.equal(before.id,shot.id);assert.equal(after.id,timeline.shots[i+1].id);
  assert.ok(before.opacity>.999999,'previous work is fully covered before cut');assert.equal(after.opacity,1,'new work is fully covered after cut');
  assert.equal(before.audio,false);assert.equal(after.audio,false);
 }
 const sound=timeline.shots.find(s=>s.id==='006');assert.equal(sampleTimeline(timeline,(sound.start+sound.end)/2).audio,true);
});

test('film clock excludes pauses and resumes without timeline jumps or drift',()=>{
 const clock=createFilmClock();clock.reset(1000);close(clock.tick(2000),1);clock.pause(2500);close(clock.elapsed,1.5);
 close(clock.tick(8000),1.5);clock.pause(9000);close(clock.elapsed,1.5);
 clock.resume(10000);close(clock.tick(11000),2.5);clock.pause(11500);close(clock.elapsed,3);
 clock.resume(100000);close(clock.tick(101000),4);assert.equal(clock.paused,false);
 clock.reset(200000);close(clock.elapsed,0);close(clock.tick(320000),120);
});
