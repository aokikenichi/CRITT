import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync,existsSync} from 'node:fs';
import {execFileSync} from 'node:child_process';
import {ENTRANCE,ROOMS,WORKS,TOUR,move,canStand,roomAt,safePose,nearestWork} from '../js/gallery-model.mjs';
test('specified 10 URLs, allowed defaults, local previews and originals=0',()=>{
 const c=JSON.parse(readFileSync(new URL('../review-artworks.json',import.meta.url)));
 assert.equal(WORKS.length,10);
 for(const w of WORKS){const item=c.items.find(i=>i.id===w.id);assert.equal(item.originals.length,0);assert.ok(existsSync(new URL('../'+w.preview,import.meta.url)));if(w.variant){assert.equal(w.variant,item.default_variant);assert.ok(item.variants.find(v=>v.key===w.variant).connection_allowed);}else assert.equal(w.url,`work.html?id=${w.id}`);assert.equal(roomAt(w.spot),w.room);assert.equal(nearestWork(w.spot).id,w.id);}
});
test('all 5 rooms connected by continuous collision-safe paths, 10 tour stops',()=>{
 const p={...ENTRANCE};let visited=[];
 for(const t of TOUR){let frames=0;while(Math.hypot(t.x-p.x,t.z-p.z)>.01){const d=Math.hypot(t.x-p.x,t.z-p.z),step=Math.min(.1,d);move(p,(t.x-p.x)/d*step,(t.z-p.z)/d*step);assert.ok(canStand(p.x,p.z));assert.ok(++frames<3000,`Blocked en route to ${JSON.stringify(t)}`);}if(t.work)visited.push(t.work);}
 assert.deepEqual(visited,WORKS.map(w=>w.id));
 // Reverse the same path to establish room-to-corridor return paths.
 for(const t of [...TOUR].reverse().concat([ENTRANCE])){let n=0;while(Math.hypot(t.x-p.x,t.z-p.z)>.01){const d=Math.hypot(t.x-p.x,t.z-p.z);move(p,(t.x-p.x)/d*Math.min(.1,d),(t.z-p.z)/d*Math.min(.1,d));assert.ok(++n<3000);}}
});
test('walls block long steps, doorways pass, invalid persisted poses reset',()=>{
 const p={x:0,z:-5};move(p,100,0);assert.ok(p.x<2.61);const door={x:0,z:-10};move(door,-10,0);assert.equal(roomAt(door),1);assert.deepEqual(safePose({x:999,z:0,yaw:0,pitch:0}),ENTRANCE);assert.deepEqual(safePose({x:0,z:0,yaw:NaN,pitch:0}),ENTRANCE);
});
test('protected source, historical QA, comparison UI and CRITT unchanged',()=>{
 const root=new URL('../../',import.meta.url);
 const tracked=execFileSync('git',['diff','--name-only','5f47308a76201cd550c81302666ec6500b5bb296','--','.'],{cwd:root,encoding:'utf8'}).trim().split('\n').filter(Boolean);
 assert.ok(tracked.every(p=>/^(museum\/(gallery\.html|gallery-direct-pilot\.html|js\/gallery[^/]*|js\/direct-pilot[^/]*|css\/(gallery|direct-pilot)\.css|direct-pilot-assets\/|vendor\/|tests\/(gallery|direct-pilot)[^/]*|qa-results\/(gallery04|direct-pilot)\/|GALLERY04_|DIRECT_PILOT_))/.test(p)),tracked.join('\n'));
});
