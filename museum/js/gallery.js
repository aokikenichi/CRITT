import {ENTRANCE,ROOMS,WORKS,FLOORS,TOUR,move,roomAt,safePose,nearestWork} from './gallery-model.mjs';
const $=id=>document.getElementById(id), host=$('viewport');
let pose=safePose(history.state?.galleryPose), scene, raf=0, last=0, mode='manual',paused=false,tourIndex=0,dwell=0,near=null,ready=false;
let keys=new Set(),held=new Set(),drag=null,activeWork=null,cleanupFrame=null,returnPose=null,lastLabel='',lastPoseTime=0;
const reduced=matchMedia('(prefers-reduced-motion: reduce)');
const cleanURL=()=>location.pathname+location.search;
function announce(text){$('notice').textContent=text;}
function clearInput(){keys.clear();held.clear();drag=null;}
function poseText(){const r=roomAt(pose);$('pose').textContent=`x ${pose.x.toFixed(3)} / z ${pose.z.toFixed(3)} / yaw ${pose.yaw.toFixed(4)} / pitch ${pose.pitch.toFixed(4)}`;$('pose').dataset.room=String(r);$('location').textContent=r?`第${r}展示室 — ${ROOMS[r-1].name}`:pose.z>0?'入口ホール':'中央通路';$('location-detail').textContent=r?`作品 ${WORKS.filter(w=>w.room===r).map(w=>w.id).join(' / ')}`:'5展示室 / 10作品';const dot=$('map-dot');if(dot){dot.setAttribute('cx',pose.x);dot.setAttribute('cy',pose.z);}}
function modeUI(){ $('manual').setAttribute('aria-pressed',String(mode==='manual'));$('auto').setAttribute('aria-pressed',String(mode==='auto'));$('pause').disabled=mode!=='auto';$('pause').textContent=paused?'再開':'一時停止';}
function manual(){mode='manual';paused=false;clearInput();$('tour-progress').textContent='';modeUI();startLoop();}
function dismissWelcome(){$('welcome').hidden=true;}
function startTour(){dismissWelcome();clearInput();pose={...ENTRANCE};mode='auto';paused=false;tourIndex=0;dwell=0;modeUI();announce('館内Auto：5室・10作品の前を巡ります。作品は自動で開きません。');host.focus();startLoop();}
function tourStep(dt){
 if(paused)return;
 const point=TOUR[tourIndex];
 if(!point){manual();announce('館内Autoが完了しました。10作品の前を巡りました。');return;}
 if(dwell>0){dwell-=dt;if(dwell<=0)tourIndex++;return;}
 const dx=point.x-pose.x,dz=point.z-pose.z,d=Math.hypot(dx,dz);
 if(d<.06){
  pose.x=point.x;pose.z=point.z;
  if(point.work){pose.yaw=point.yaw;pose.pitch=0;dwell=3.5;const w=WORKS.find(w=>w.id===point.work);$('tour-progress').textContent=`${Number(w.id)} / 10 · 第${w.room}室 · ${w.id} ${w.title}`;}
  else tourIndex++;
 }else{const step=Math.min(d,Number($('speed').value)*dt);move(pose,dx/d*step,dz/d*step);const aim=Math.atan2(-dx,-dz);const diff=Math.atan2(Math.sin(aim-pose.yaw),Math.cos(aim-pose.yaw));pose.yaw+=diff*Math.min(1,dt*3);pose.pitch=0;}
}
function blocked(){return activeWork||$('map').open||$('help').open||document.hidden;}
function tick(time){raf=0;const dt=Math.min((time-last)/1000||0,.05);last=time;if(blocked()||!scene||!ready)return;
 if(mode==='auto')tourStep(dt);
 else if($('welcome').hidden){
  let f=Number(keys.has('w')||keys.has('arrowup')||held.has('forward'))-Number(keys.has('s')||keys.has('arrowdown')||held.has('back'));
  let s=Number(keys.has('d')||keys.has('arrowright')||held.has('right'))-Number(keys.has('a')||keys.has('arrowleft')||held.has('left'));
  const len=Math.max(1,Math.hypot(f,s));const speed=Number($('speed').value)*dt/len;
  if(held.has('turn-left'))pose.yaw+=dt*1.2;if(held.has('turn-right'))pose.yaw-=dt*1.2;
  move(pose,(-Math.sin(pose.yaw)*f+Math.cos(pose.yaw)*s)*speed,(-Math.cos(pose.yaw)*f-Math.sin(pose.yaw)*s)*speed);
 }
 near=nearestWork(pose);$('nearby').hidden=!near||!$('welcome').hidden;
 if(near&&lastLabel!==near.id){$('nearby-label').textContent=`${near.id} ${near.title}`;lastLabel=near.id;}
 scene.render(pose);if(time-lastPoseTime>120){poseText();lastPoseTime=time;}raf=requestAnimationFrame(tick);
}
function startLoop(){if(!raf&&!blocked()&&scene&&ready){last=performance.now();raf=requestAnimationFrame(tick);}}
function stopLoop(){cancelAnimationFrame(raf);raf=0;clearInput();poseText();}
function showMap(){clearInput();poseText();$('map').showModal();stopLoop();}
function jump(r){manual();dismissWelcome();pose=r?{x:r.cx,z:r.cz,yaw:r.id===5?0:(r.cx<0?Math.PI/2:-Math.PI/2),pitch:0}:{...ENTRANCE};$('map').close();poseText();host.focus();startLoop();}
$('begin').onclick=()=>{dismissWelcome();announce('WASD／矢印で歩く · ドラッグで見回す · 作品に近づいて鑑賞');host.focus();};
$('manual').onclick=()=>{dismissWelcome();manual();announce('自由回遊に切り替えました。');host.focus();};
$('auto').onclick=startTour;$('welcome-tour').onclick=startTour;
$('pause').onclick=()=>{paused=!paused;clearInput();modeUI();};
$('map-open').onclick=showMap;
$('help-open').onclick=()=>{$('help').showModal();stopLoop();};
for(const b of document.querySelectorAll('[data-close]'))b.onclick=()=>$(b.dataset.close).close();
for(const d of [$('map'),$('help')])d.addEventListener('close',()=>{host.focus();startLoop();});
document.querySelector('.skip').onclick=e=>{e.preventDefault();showMap();$('directory').scrollIntoView();};
host.addEventListener('keydown',e=>{
 if(blocked())return;const k=e.key.toLowerCase();
 if(['w','a','s','d','arrowup','arrowdown','arrowleft','arrowright'].includes(k)){e.preventDefault();dismissWelcome();if(mode==='auto')manual();keys.add(k);}
 if((k==='e'||k==='enter')&&!e.repeat&&near){e.preventDefault();openWork(near);}
});
window.addEventListener('keyup',e=>keys.delete(e.key.toLowerCase()));
window.addEventListener('blur',clearInput);
host.addEventListener('pointerdown',e=>{if(blocked())return;dismissWelcome();host.focus();if(mode==='auto')manual();drag={id:e.pointerId,x:e.clientX,y:e.clientY,startX:e.clientX,startY:e.clientY};host.setPointerCapture(e.pointerId);});
host.addEventListener('pointermove',e=>{if(!drag||drag.id!==e.pointerId)return;pose.yaw-=(e.clientX-drag.x)*.004;pose.pitch=Math.max(-.65,Math.min(.65,pose.pitch-(e.clientY-drag.y)*.003));drag.x=e.clientX;drag.y=e.clientY;});
host.addEventListener('pointerup',()=>{drag=null;});host.addEventListener('pointercancel',clearInput);
for(const b of document.querySelectorAll('[data-move],[data-look]')){
 const name=b.dataset.move||`turn-${b.dataset.look}`;
 b.addEventListener('pointerdown',e=>{e.preventDefault();dismissWelcome();if(mode==='auto')manual();held.add(name);b.setPointerCapture(e.pointerId);});
 for(const type of ['pointerup','pointercancel','lostpointercapture'])b.addEventListener(type,()=>held.delete(name));
 // Keyboard activation is a short, discrete step; a pointer is held continuously.
 b.addEventListener('click',e=>{if(e.detail!==0)return;dismissWelcome();manual();if(name==='turn-left')pose.yaw+=.25;else if(name==='turn-right')pose.yaw-=.25;else{const f=name==='forward'?1:name==='back'?-1:0,s=name==='right'?1:name==='left'?-1:0;move(pose,(-Math.sin(pose.yaw)*f+Math.cos(pose.yaw)*s)*.65,(-Math.cos(pose.yaw)*f-Math.sin(pose.yaw)*s)*.65);}poseText();});
}
$('enter-work').onclick=()=>{if(near)openWork(near);};
function adaptShell(frame,w){
 const doc=frame.contentDocument;if(!doc||frame.contentWindow.location.origin!==location.origin)return;
 const style=doc.createElement('style');
 style.textContent='.shell-heading,.review-context,.work-navigation,#mode-hint,#reduced-motion-note{display:none!important}.shell-header{padding:6px 10px!important;min-height:0!important}.shell-toolbar{justify-content:center;flex-wrap:wrap;gap:5px!important}.shell-toolbar button{min-height:36px;padding:6px 9px;font-size:12px}.shell-footer{padding:4px 8px!important;min-height:0!important}.originals-status{font-size:10px}';
 doc.head.append(style);
 doc.getElementById('about-button')?.addEventListener('click',()=>{const p=doc.createElement('p');p.textContent='統合館内ではこの版をα版採用済みです。以下は回収・比較時点の記録です。正式原画は未登録です。';doc.getElementById('info-content')?.prepend(p);});
 // Changes apply only to this iframe instance. Historical review files stay intact.
 const status=doc.getElementById('work-status');if(status)status.textContent='α版採用作品';
 const note=doc.getElementById('review-note');if(note)note.textContent=w.note;
}
function openWork(w,push=true){
 if(!WORKS.includes(w)||activeWork)return;
 dismissWelcome();returnPose={...pose};stopLoop();
 if($('map').open)$('map').close();if($('help').open)$('help').close();
 activeWork=w;stopLoop();$('view-title').textContent=`${w.id} ${w.title}`;$('view-note').textContent='α版採用済み · '+w.note;
 $('view-loading').hidden=false;$('view-loading').textContent='作品を読み込んでいます。';
 if(push){history.replaceState({galleryPose:returnPose},'',cleanURL());history.pushState({galleryWork:w.id,galleryPose:returnPose},'',`${cleanURL()}#work=${w.id}`);}
 const frame=document.createElement('iframe');frame.id='work-view';frame.title=`${w.id} ${w.title}の共通鑑賞ビュー`;
 const url=new URL(w.url,document.baseURI);if(url.origin!==location.origin)throw new Error('Only catalogued same-origin works are allowed');frame.src=url.href;
 let attempts=0,timer;
 const observe=()=>{
  if(activeWork!==w)return;
  try{const doc=frame.contentDocument;const inner=doc?.getElementById('artwork-frame');const status=doc?.getElementById('load-status');
   if(inner&&!inner.hidden&&status?.hidden){inner.title=`${w.id} ${w.title}：α版採用作品`;const badge=doc.getElementById('work-status');if(badge)badge.textContent='α版採用済み';$('view-loading').hidden=true;$('viewer').dataset.ready=w.id;return;}
  }catch{}
  if(++attempts>=80){$('view-loading').textContent='描画の確認に時間がかかっています。作品の外部CDNやWebGL環境を確認するか、「展示室に戻る」を選んでください。';return;}
  timer=setTimeout(observe,250);
 };
 frame.addEventListener('load',()=>{adaptShell(frame,w);observe();});
 cleanupFrame=()=>{clearTimeout(timer);frame.src='about:blank';frame.remove();delete $('viewer').dataset.ready;};
 $('view-frame').replaceChildren(frame);$('viewer').showModal();$('return').focus();
}
function closeWork(){if(!activeWork)return;cleanupFrame?.();cleanupFrame=null;activeWork=null;pose=safePose(returnPose);$('viewer').close();poseText();host.focus();startLoop();}
$('return').onclick=()=>{if(history.state?.galleryWork)history.back();else closeWork();};
// Esc belongs to the artwork, and must never discard a visitor's viewing session.
$('viewer').addEventListener('cancel',e=>e.preventDefault());
window.addEventListener('popstate',()=>{closeWork();pose=safePose(history.state?.galleryPose||pose);const w=WORKS.find(w=>w.id===history.state?.galleryWork);if(w)openWork(w,false);poseText();});
window.addEventListener('pagehide',()=>{stopLoop();cleanupFrame?.();scene?.dispose();});
document.addEventListener('visibilitychange',()=>{if(document.hidden)stopLoop();else startLoop();});
function makeDirectory(){
 const svg=$('floor-map'),ns='http://www.w3.org/2000/svg';
 for(const f of FLOORS){const r=document.createElementNS(ns,'rect');r.setAttribute('x',f.x1);r.setAttribute('y',f.z1);r.setAttribute('width',f.x2-f.x1);r.setAttribute('height',f.z2-f.z1);svg.append(r);}
 for(const r of ROOMS){const t=document.createElementNS(ns,'text');t.setAttribute('x',r.cx);t.setAttribute('y',r.cz);t.textContent=`第${r.id}室`;svg.append(t);}
 const dot=document.createElementNS(ns,'circle');dot.id='map-dot';dot.setAttribute('r','1');svg.append(dot);
 for(const r of [null,...ROOMS]){const b=document.createElement('button');b.dataset.room=r?.id||0;b.textContent=r?`第${r.id}室　${r.name}`:'入口ホール';b.onclick=()=>jump(r);$('shortcuts').append(b);}
 for(const w of WORKS){const a=document.createElement('article');const img=document.createElement('img');img.src=w.preview;img.alt=`${w.id} 作品プレビュー／制作中`;img.loading='lazy';const body=document.createElement('div');const title=document.createElement('h4');title.textContent=`${w.id} ${w.title}`;const p=document.createElement('p');p.textContent=w.note;const b=document.createElement('button');b.dataset.work=w.id;b.textContent='鑑賞する';b.setAttribute('aria-label',`${w.id} ${w.title}を鑑賞する`);b.onclick=()=>openWork(w);body.append(title,p,b);a.append(img,body);$('work-list').append(a);}
}
function failed(text){ready=false;stopLoop();document.body.classList.add('failed');$('welcome').hidden=true;announce(text);$('auto').disabled=true;$('welcome-tour').disabled=true;$('pause').disabled=true;if(!$('map').open&&!activeWork)showMap();}
makeDirectory();poseText();
const requested=WORKS.find(w=>`#work=${w.id}`===location.hash);
if(!history.state?.galleryWork)history.replaceState({galleryPose:{...pose}},'',cleanURL());
if(requested)openWork(requested,!history.state?.galleryWork);
else if(location.hash)history.replaceState({galleryPose:{...pose}},'',cleanURL());
try{const {createScene}=await import('./gallery-scene.js');scene=createScene(host,failed);ready=true;document.body.dataset.ready='true';announce(reduced.matches?'動きを減らす設定が有効です。館内図から作品を選べます。':'自由回遊、または館内Autoで入館できます。');scene.render(pose);if(reduced.matches&&!activeWork)showMap();startLoop();}catch(error){console.error('Gallery initialization failed:',error);failed('3Dを開始できませんでした。館内図・作品一覧から全10作品へ進めます。');}
