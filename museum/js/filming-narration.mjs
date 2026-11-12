// A separate audio context keeps the original 006 sound engine untouched.
export function createNarration(){
 let context=null,buffers=[],source=null,current='',loading=false;
 function stop(){if(source){try{source.stop()}catch{} source.disconnect();source=null}current=''}
 return {
  async prepare(){
   if(loading)return;loading=true;
   try{
    context ||= new AudioContext();
    await context.resume();
    if(!buffers.length){
     const files=await Promise.all(Array.from({length:10},async(_,i)=>{
      const id=String(i+1).padStart(3,'0');
      const response=await fetch(`Narration/CRITT_Museum_${id}.mp3`);
      if(!response.ok)throw new Error(`${id} の音声を取得できません`);
      return context.decodeAudioData(await response.arrayBuffer());
     }));
     buffers=files;
    }
    return buffers.map(buffer=>buffer.duration);
   } finally {loading=false}
  },
  sync(shot,elapsed,paused){
   if(!shot||paused||elapsed<shot.start+.5){stop();return}
   if(current===shot.id)return;
   stop();const buffer=buffers[Number(shot.id)-1],offset=Math.max(0,elapsed-shot.start-.5);
   if(!buffer||offset>=buffer.duration)return;
   source=context.createBufferSource();source.buffer=buffer;source.connect(context.destination);
   source.start(context.currentTime,offset);current=shot.id;
  },
  stop,
  dispose(){stop();context?.close();context=null;buffers=[]}
 };
}
