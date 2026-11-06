import {createTimeline,sampleTimeline,createFilmClock} from './filming-model.mjs?v=20261106b';
export function createFilmingTour({catalog,nav,crowd,snapshot,restore,applyPose,clearInput}){
 const timeline=createTimeline(catalog,nav),clock=createFilmClock();let phase='setup',saved=null,countUntil=0,hud=false,lastSample=null,visits=[],lastId='',disposed=false;
 const style=document.createElement('link');style.rel='stylesheet';style.href='css/filming-tour.css?v=20261106b';document.head.append(style);
 const root=document.createElement('section');root.id='film-root';root.setAttribute('aria-label','撮影用ツアー');root.innerHTML=`
 <div id="film-setup"><p class="film-kicker">CRITT MUSEUM / CAPTURE</p><h1>撮影用ツアー</h1><p>約120秒で10作品を巡ります。006の音響は18秒間、鑑賞位置に応じて変化します。</p>
 <ol><li>「音声を準備」で006の音声を有効化してください。</li><li>OBSでブラウザの映像と音声を収録します。</li><li>録画開始後に下の開始ボタンを押すと、5秒のカウントダウン後に始まります。</li></ol>
 <div class="film-actions"><button id="film-audio">音声を準備</button><label>音量 <input id="film-volume" type="range" min="0" max="100" value="60"></label></div>
 <p id="film-audio-state" role="status">音声は未準備です。</p><label class="film-silent"><input id="film-silent" type="checkbox">音声なしで撮影する</label>
 <div class="film-actions"><button id="film-start" disabled>撮影ツアー開始（5秒後）</button><button id="film-fullscreen">全画面表示</button></div>
 <p>撮影中：H＝操作表示切替 ／ Space＝カメラ一時停止・再開 ／ Esc＝中断。タブを非表示にすると一時停止します。ブラウザの映像・音声はOBS側で収録してください。</p><p id="film-result" role="status"></p><a href="exhibition.html">通常の鑑賞に戻る</a></div>
 <div id="film-curtain" hidden><div id="film-card"></div></div>
 <div id="film-controls" hidden><span id="film-time"></span><button id="film-pause">一時停止</button><button id="film-stop">撮影を終了</button></div>`;
 document.body.append(root);
 const $=s=>root.querySelector(s),setup=$('#film-setup'),curtain=$('#film-curtain'),card=$('#film-card'),controls=$('#film-controls');
 const originalAudio=crowd.state();$('#film-volume').value=String(Math.round(originalAudio.volume*100));
 function updateReadiness(){const a=crowd.state(),silent=$('#film-silent').checked;$('#film-audio').disabled=a.loading;$('#film-audio').textContent=a.loading?'音声を準備中…':a.enabled&&!a.error?'音声準備済み':'音声を準備';$('#film-audio-state').textContent=a.error?`音声の準備に失敗しました：${a.error}。再試行または音声なしを選べます。`:a.loading?'音声を読み込んでいます…':a.enabled?'音声準備済み。006に入ると再生します。':'音声は未準備です。';$('#film-start').disabled=!silent&&(!a.enabled||a.loading||Boolean(a.error));}
 $('#film-audio').onclick=async()=>{if(crowd.state().loading)return;const pending=crowd.enable();updateReadiness();await pending;updateReadiness()};$('#film-volume').oninput=e=>crowd.setVolume(Number(e.target.value)/100);$('#film-silent').onchange=updateReadiness;
 $('#film-fullscreen').onclick=()=>{document.documentElement.requestFullscreen?.().catch(()=>{$('#film-result').textContent='全画面表示を利用できません。OBSでウィンドウを収録してください。'})};
 function showHud(){controls.hidden=!(hud||clock.paused);document.body.classList.toggle('film-hud',hud||clock.paused)}
 function finish(completed){if(!saved)return;phase='setup';const previous=saved;saved=null;document.body.classList.remove('film-active','film-hud');setup.hidden=false;curtain.hidden=true;controls.hidden=true;clearInput();restore(previous);if(!originalAudio.enabled)crowd.disable();crowd.setVolume(originalAudio.volume);$('#film-volume').value=String(Math.round(originalAudio.volume*100));$('#film-result').textContent=completed?'120秒のツアーが完了しました。OBSの録画を停止してください。':'撮影ツアーを中断し、元の鑑賞位置に戻りました。';root.dataset.phase='setup';root.dataset.paused='false';root.dataset.result=completed?'completed':'cancelled';updateReadiness();}
 function start(){if($('#film-start').disabled)return;saved=snapshot();clearInput();if($('#film-silent').checked)crowd.disable();$('#film-pause').textContent='一時停止';phase='countdown';countUntil=performance.now()+5000;visits=[];lastId='';hud=false;setup.hidden=true;curtain.hidden=false;controls.hidden=true;document.body.classList.add('film-active');delete root.dataset.result;clock.reset(performance.now());}
 function pause(){if(phase!=='running'&&phase!=='countdown')return;if(phase==='countdown'){finish(false);return}if(clock.paused)clock.resume(performance.now());else clock.pause(performance.now());$('#film-pause').textContent=clock.paused?'再開':'一時停止';showHud();}
 $('#film-start').onclick=start;$('#film-pause').onclick=pause;$('#film-stop').onclick=()=>finish(false);
 function key(e){if(phase==='setup'||e.metaKey||e.ctrlKey||e.altKey)return;if(e.target.closest?.('input,select,textarea'))return;e.preventDefault();e.stopImmediatePropagation();if(e.repeat)return;if(e.key==='Escape')finish(false);else if(e.code==='Space')pause();else if(e.key.toLowerCase()==='h'){hud=!hud;showHud()}}
 function visibility(){if(document.hidden&&phase==='countdown')finish(false);else if(document.hidden&&phase==='running'&&!clock.paused){clock.pause(performance.now());$('#film-pause').textContent='再開';showHud()}}
 window.addEventListener('keydown',key,true);document.addEventListener('visibilitychange',visibility);
 function step(now){
 if(phase==='setup')return false;
 if(phase==='countdown'){lastSample=sampleTimeline(timeline,0);applyPose(lastSample);curtain.style.opacity='1';card.hidden=false;card.textContent=String(Math.max(1,Math.ceil((countUntil-now)/1000)));if(now>=countUntil){phase='running';clock.reset(now)}root.dataset.phase=phase;return true}
 const elapsed=clock.tick(now);lastSample=sampleTimeline(timeline,elapsed);applyPose(lastSample);if(lastSample.phase==='shot'&&lastSample.id!==lastId){lastId=lastSample.id;visits.push({id:lastId,time:elapsed})}
 curtain.style.opacity=String(lastSample.opacity);card.hidden=!['title','credits'].includes(lastSample.phase);
 if(lastSample.phase==='title')card.innerHTML='<p class="film-kicker">BEYOND THE BOUNDARY</p><h1>CRITT MUSEUM</h1><p>仮想クリケット現代美術展</p>';
 else if(lastSample.phase==='credits')card.innerHTML='<h1>CRITT MUSEUM</h1><p>この仮想クリケット現代美術展は生成AIを用いております。</p><p>企画・構成：@aokikenichi<br>案作成・展示構築：ChatGPT<br>作品006音声：Eleven Creative / Sound Effect</p><p>chatgpt.com ／ elevenlabs.io<br>aokikenichi.github.io/CRITT/museum/</p>';
 $('#film-time').textContent=`${clock.paused?'一時停止 · ':''}${Math.min(120,Math.floor(elapsed))} / 120秒 · ${lastSample.id}`;
 root.dataset.phase=lastSample.phase;root.dataset.elapsed=elapsed.toFixed(3);root.dataset.paused=String(clock.paused);root.dataset.work=lastSample.id;root.dataset.visits=JSON.stringify(visits);
 if(elapsed>=120)finish(true);return true;
 }
 updateReadiness();
 return {step,get controlling(){return phase!=='setup'},get blocksInput(){return true},get audioActive(){return phase==='running'&&Boolean(lastSample?.audio)},state(){return {phase,elapsed:clock.elapsed,paused:clock.paused,work:lastSample?.id,visits}},dispose(){if(disposed)return;disposed=true;window.removeEventListener('keydown',key,true);document.removeEventListener('visibilitychange',visibility);root.remove();style.remove();document.body.classList.remove('film-active','film-hud')}};
}
