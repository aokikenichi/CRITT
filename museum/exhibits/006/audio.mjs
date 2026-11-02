// Local audio for work 006. Playback is created only after an explicit gesture.
const smooth=(x,a,b)=>{const t=Math.max(0,Math.min(1,(x-a)/(b-a)));return t*t*(3-2*t)};
export function crowdMix(radius,time=0){
 const outer=smooth(radius,4.0,10.5),center=1-smooth(radius,1.8,7.2),reach=1-smooth(radius,18,23);
 const swell=.58+.42*(.5+.5*Math.sin(time*.17));
 const cheerWave=.86+.14*(.5+.5*Math.sin(time*.095+1.3));
 return {zone:radius<2.1?'中央':radius<5.4?'内側':radius<8.8?'中間':'外周',reach,base:reach*(.11+.09*outer),swell:reach*(.12*outer+.025*center)*swell,cheer:reach*(.25*center+.025*outer)*cheerWave,cheerCutoff:1800+center*7200};
}
// Fold the last second over the first second; a periodic buffer has no abrupt seam.
function crossfadeLoop(ctx,source){
 const fade=Math.min(Math.floor(source.sampleRate),Math.floor(source.length/4)),length=source.length-fade;
 const result=ctx.createBuffer(source.numberOfChannels,length,source.sampleRate);
 for(let c=0;c<source.numberOfChannels;c++){const src=source.getChannelData(c),dst=result.getChannelData(c);for(let i=0;i<length;i++){if(i<fade){const t=i/fade;dst[i]=src[length+i]*(1-t)+src[i]*t}else dst[i]=src[i]}}
 return result;
}
export function createCrowdAudio(onChange=()=>{}){
 let ctx,master,analyser,compressor,layers=[],enabled=false,loading=false,error='',volume=.6,present=false,inWork=false,radius=99,stopTimer=0,disposed=false,starting=null,level=0;
 const state=()=>({enabled,loading,error,volume,present,radius,context:ctx?.state||'uninitialized',level,targets:crowdMix(radius,ctx?.currentTime||0)});
 const report=()=>onChange(state());
 async function prepare(){
  if(layers.length)return;
  const ids=['02','04','03'];const buffers=await Promise.all(ids.map(async id=>{const r=await fetch(`exhibition-assets/006/audio/crowd-${id}.mp3`);if(!r.ok)throw Error(`音声 ${id} を取得できませんでした`);return ctx.decodeAudioData(await r.arrayBuffer())}));
  if(disposed)return;
  master=ctx.createGain();master.gain.value=0;compressor=ctx.createDynamicsCompressor();compressor.threshold.value=-18;compressor.knee.value=8;compressor.ratio.value=12;compressor.attack.value=.01;compressor.release.value=.25;analyser=ctx.createAnalyser();analyser.fftSize=512;master.connect(compressor);compressor.connect(analyser);analyser.connect(ctx.destination);
  layers=buffers.map((buffer,i)=>{const src=ctx.createBufferSource(),gain=ctx.createGain();gain.gain.value=0;src.buffer=crossfadeLoop(ctx,buffer);src.loop=true;let filter=null;if(i===2){filter=ctx.createBiquadFilter();filter.type='lowpass';filter.frequency.value=1800;src.connect(filter);filter.connect(gain)}else src.connect(gain);gain.connect(master);src.start();return {src,gain,filter}});
 }
 function setTarget(param,value,tau=.35){param.setTargetAtTime(value,ctx.currentTime,tau)}
 async function enable(){
  if(disposed)return;enabled=true;error='';loading=true;report();
  try{if(!ctx){const Audio=window.AudioContext||window.webkitAudioContext;if(!Audio)throw Error('このブラウザでは音声を再生できません');ctx=new Audio()}const resumed=ctx.resume();starting=prepare();await Promise.all([resumed,starting]);if(disposed)return;if(!enabled||!present||document.hidden)await ctx.suspend();}
  catch(e){enabled=false;error=e.message||'音声を読み込めませんでした';if(ctx?.state==='running')await ctx.suspend().catch(()=>{})}
  finally{loading=false;report()}
 }
 function disable(){enabled=false;clearTimeout(stopTimer);if(ctx&&master){setTarget(master.gain,0,.12);stopTimer=setTimeout(()=>{if(!enabled&&ctx?.state==='running')ctx.suspend().catch(()=>{})},700)}report()}
 function update(isWork,localRadius){
  radius=localRadius;inWork=isWork;const inRange=isWork&&localRadius<23&&!document.hidden;
  if(inRange!==present){present=inRange;clearTimeout(stopTimer);if(ctx&&enabled&&layers.length){if(present&&ctx.state==='suspended')ctx.resume().catch(()=>{});if(!present){setTarget(master.gain,0,.3);stopTimer=setTimeout(()=>{if(!present&&ctx?.state==='running')ctx.suspend().catch(()=>{})},1600)}}report()}
  if(!ctx||!layers.length||ctx.state!=='running')return;
  const mix=crowdMix(radius,ctx.currentTime),values=[mix.base,mix.swell,mix.cheer];layers.forEach((l,i)=>setTarget(l.gain.gain,values[i]));setTarget(layers[2].filter.frequency,mix.cheerCutoff,.6);setTarget(master.gain,enabled&&present?volume*.65:0,.3);
  if(enabled&&present){const samples=new Uint8Array(analyser.fftSize);analyser.getByteTimeDomainData(samples);let sum=0;for(const x of samples)sum+=((x-128)/128)**2;level=level*.97+Math.min(1,Math.sqrt(sum/samples.length)*12)*.03}else level*=.95;
 }
 function visibility(){if(!ctx||!enabled)return;if(document.hidden){clearTimeout(stopTimer);present=false;ctx.suspend().catch(()=>{});report()}else if(inWork&&radius<23){present=true;ctx.resume().catch(()=>{});report()}}
 document.addEventListener('visibilitychange',visibility);
 function dispose(){disposed=true;enabled=false;clearTimeout(stopTimer);document.removeEventListener('visibilitychange',visibility);layers.forEach(l=>{try{l.src.stop()}catch{}});ctx?.close().catch(()=>{});layers=[]}
 return {enable,disable,update,dispose,state,setVolume(v){volume=Math.max(0,Math.min(1,Number(v)));report()}};
}
