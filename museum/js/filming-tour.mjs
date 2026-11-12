import {createTimeline,sampleTimeline,createFilmClock} from './filming-model.mjs?v=20261108b';
import {createNarration} from './filming-narration.mjs?v=20261108a';
export function createFilmingTour({catalog,nav,crowd,snapshot,restore,applyPose,clearInput}){
 const narrated=new URLSearchParams(location.search).get('narration')==='1',narration=narrated?createNarration():null,clock=createFilmClock();let timeline=createTimeline(catalog,nav),narrationReady=!narrated,narrationError='',preparing=false,phase='setup',saved=null,countUntil=0,hud=false,lastSample=null,visits=[],lastId='',disposed=false;
 const style=document.createElement('link');style.rel='stylesheet';style.href='css/filming-tour.css?v=20261106b';document.head.append(style);
 const root=document.createElement('section');root.id='film-root';root.setAttribute('aria-label','動画閲覧ツアー');root.innerHTML=`
 <div id="film-setup"><p class="film-kicker">CRITT MUSEUM / TOUR</p><h1>動画閲覧ツアー</h1><p>約120秒で10作品を巡ります。006の音響は18秒間、鑑賞位置に応じて変化します。</p>
 <ol><li>「音声を準備」で006の音声を有効化してください。</li><li>開始ボタンを押すと、5秒のカウントダウン後に始まります。</li></ol>
 <div class="film-actions"><button id="film-audio">音声を準備</button><label>音量 <input id="film-volume" type="range" min="0" max="100" value="60"></label></div>
 <p id="film-audio-state" role="status">音声は未準備です。</p><label class="film-silent"><input id="film-silent" type="checkbox">音声なしで閲覧する</label>
 <div class="film-actions"><button id="film-start" disabled>ツアー開始（5秒後）</button><button id="film-fullscreen">全画面表示</button></div>
 <p>閲覧中：H＝操作表示切替 ／ Space＝カメラ一時停止・再開 ／ Esc＝中断。タブを非表示にすると一時停止します。</p><p id="film-result" role="status"></p><a href="exhibition.html">通常の鑑賞に戻る</a></div>
 <div id="film-curtain" hidden><div id="film-card"></div></div>
 <div id="film-controls" hidden><span id="film-time"></span><button id="film-pause">一時停止</button><button id="film-stop">ツアーを終了</button></div>`;
 document.body.append(root);
 const $=s=>root.querySelector(s),setup=$('#film-setup'),curtain=$('#film-curtain'),card=$('#film-card'),controls=$('#film-controls');
 if(narrated){setup.querySelector('h1').textContent='展示解説付き動画閲覧ツアー';setup.querySelector('h1 + p').textContent='10作品の展示解説を全編読み上げます。音声を準備すると所要時間を表示します。';setup.querySelector('.film-silent').hidden=true;setup.querySelector('ol li').textContent='「音声を準備」で展示解説と006の音声を読み込みます。';}
 setup.querySelector('label:has(#film-volume)').firstChild.textContent='作品006の音量 ';
 const switchMode=document.createElement('p'),switchLink=document.createElement('a');switchLink.href=narrated?'exhibition.html?capture=1':'exhibition.html?capture=1&narration=1';switchLink.textContent=narrated?'約120秒の動画閲覧ツアーへ':'展示解説付きの動画閲覧ツアーへ';switchMode.append(switchLink);setup.append(switchMode);
 const originalAudio=crowd.state();$('#film-volume').value=String(Math.round(originalAudio.volume*100));
 function updateReadiness(){const a=crowd.state(),silent=$('#film-silent').checked,loading=a.loading||preparing;$('#film-audio').disabled=loading;$('#film-audio').textContent=loading?'音声を準備中…':a.enabled&&!a.error&&narrationReady?'音声準備済み':'音声を準備';$('#film-audio-state').textContent=narrationError?`展示解説の読み込みに失敗しました：${narrationError}。再試行してください。`:a.error?`音声の準備に失敗しました：${a.error}。再試行してください。`:loading?'音声を読み込んでいます…':a.enabled&&narrationReady?'音声準備済み。':'音声は未準備です。';$('#film-start').disabled=loading||!narrationReady||(!silent&&(!a.enabled||Boolean(a.error)));}
 $('#film-audio').onclick=async()=>{if(preparing||crowd.state().loading)return;preparing=true;narrationError='';const pending=crowd.enable();const narrationPending=narrated?narration.prepare():null;updateReadiness();try{if(narrationPending){const durations=await narrationPending;timeline=createTimeline(catalog,nav,durations);narrationReady=true;setup.querySelector('h1 + p').textContent=`10作品の展示解説を全編読み上げます。所要時間：約${Math.ceil(timeline.duration/60)}分（${Math.ceil(timeline.duration)}秒）。`; }await pending}catch(error){narrationReady=false;narrationError=error.message||String(error);await pending.catch(()=>{})}finally{preparing=false;updateReadiness()}};$('#film-volume').oninput=e=>crowd.setVolume(Number(e.target.value)/100);$('#film-silent').onchange=updateReadiness;
 $('#film-fullscreen').onclick=()=>{document.documentElement.requestFullscreen?.().catch(()=>{$('#film-result').textContent='全画面表示を利用できません。'})};
 function showHud(){controls.hidden=!(hud||clock.paused);document.body.classList.toggle('film-hud',hud||clock.paused)}
 function finish(completed){if(!saved)return;narration?.stop();phase='setup';const previous=saved;saved=null;document.body.classList.remove('film-active','film-hud');setup.hidden=false;curtain.hidden=true;controls.hidden=true;clearInput();restore(previous);if(!originalAudio.enabled)crowd.disable();crowd.setVolume(originalAudio.volume);$('#film-volume').value=String(Math.round(originalAudio.volume*100));$('#film-result').textContent=completed?'ツアーが完了しました。':'ツアーを中断し、元の鑑賞位置に戻りました。';root.dataset.phase='setup';root.dataset.paused='false';root.dataset.result=completed?'completed':'cancelled';updateReadiness();}
 function start(){if($('#film-start').disabled)return;saved=snapshot();clearInput();if($('#film-silent').checked)crowd.disable();$('#film-pause').textContent='一時停止';phase='countdown';countUntil=performance.now()+5000;visits=[];lastId='';hud=false;setup.hidden=true;curtain.hidden=false;controls.hidden=true;document.body.classList.add('film-active');delete root.dataset.result;clock.reset(performance.now());}
 function pause(){if(phase!=='running'&&phase!=='countdown')return;if(phase==='countdown'){finish(false);return}if(clock.paused)clock.resume(performance.now());else {clock.pause(performance.now());narration?.stop()}$('#film-pause').textContent=clock.paused?'再開':'一時停止';showHud();}
 $('#film-start').onclick=start;$('#film-pause').onclick=pause;$('#film-stop').onclick=()=>finish(false);
 function key(e){if(phase==='setup'||e.metaKey||e.ctrlKey||e.altKey)return;if(e.target.closest?.('input,select,textarea'))return;e.preventDefault();e.stopImmediatePropagation();if(e.repeat)return;if(e.key==='Escape')finish(false);else if(e.code==='Space')pause();else if(e.key.toLowerCase()==='h'){hud=!hud;showHud()}}
 function visibility(){if(document.hidden&&phase==='countdown')finish(false);else if(document.hidden&&phase==='running'&&!clock.paused){clock.pause(performance.now());narration?.stop();$('#film-pause').textContent='再開';showHud()}}
 window.addEventListener('keydown',key,true);document.addEventListener('visibilitychange',visibility);
 function step(now){
 if(phase==='setup')return false;
 if(phase==='countdown'){lastSample=sampleTimeline(timeline,0);applyPose(lastSample);curtain.style.opacity='1';card.hidden=false;card.textContent=String(Math.max(1,Math.ceil((countUntil-now)/1000)));if(now>=countUntil){phase='running';clock.reset(now)}root.dataset.phase=phase;return true}
 const elapsed=clock.tick(now);lastSample=sampleTimeline(timeline,elapsed);applyPose(lastSample);if(lastSample.phase==='shot'&&lastSample.id!==lastId){lastId=lastSample.id;visits.push({id:lastId,time:elapsed})}
 if(narrated)narration.sync(lastSample.phase==='shot'?timeline.shots.find(s=>s.id===lastSample.id):null,elapsed,clock.paused);
 curtain.style.opacity=String(lastSample.opacity);card.hidden=!['title','credits'].includes(lastSample.phase);
 if(lastSample.phase==='title')card.innerHTML='<p class="film-kicker">BEYOND THE BOUNDARY</p><h1>CRITT MUSEUM</h1><p>仮想クリケット現代美術展</p>';
 else if(lastSample.phase==='credits')card.innerHTML='<h1>CRITT MUSEUM</h1><p>この仮想クリケット現代美術展は生成AIを用いております。</p><p>企画・構成：@aokikenichi<br>案作成・展示構築：ChatGPT<br>作品006音声：Eleven Creative<br>展示解説音声：Eleven Text to Speech</p><p>chatgpt.com ／ elevenlabs.io<br>aokikenichi.github.io/CRITT/museum/</p>';
 $('#film-time').textContent=`${clock.paused?'一時停止 · ':''}${Math.min(Math.ceil(timeline.duration),Math.floor(elapsed))} / ${Math.ceil(timeline.duration)}秒 · ${lastSample.id}`;
 root.dataset.phase=lastSample.phase;root.dataset.elapsed=elapsed.toFixed(3);root.dataset.paused=String(clock.paused);root.dataset.work=lastSample.id;root.dataset.visits=JSON.stringify(visits);
 if(elapsed>=timeline.duration)finish(true);return true;
 }
 updateReadiness();
 return {step,get controlling(){return phase!=='setup'},get blocksInput(){return true},get audioActive(){return phase==='running'&&Boolean(lastSample?.audio)},state(){return {phase,elapsed:clock.elapsed,paused:clock.paused,work:lastSample?.id,visits}},dispose(){if(disposed)return;disposed=true;narration?.dispose();window.removeEventListener('keydown',key,true);document.removeEventListener('visibilitychange',visibility);root.remove();style.remove();document.body.classList.remove('film-active','film-hud')}};
}
