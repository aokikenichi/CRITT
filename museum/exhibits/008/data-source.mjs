// Pure data functions extracted verbatim from Work08 v2.9.
function mulberry32(a){return function(){let t=a+=0x6D2B79F5;t=Math.imul(t^t>>>15,t|1);t^=t+Math.imul(t^t>>>7,t|61);return((t^t>>>14)>>>0)/4294967296}}
function fakeData(){const rnd=mulberry32(24082026), balls=[];let score=0;for(let o=0;o<20;o++){for(let n=0;n<6;n++){
 const x=rnd();let batter=x<.31?0:x<.68?1:x<.81?2:x<.88?3:x<.963?4:6;
 const forced={8:'caught',28:'bowled',45:'lbw',67:'run out',85:'stumped',109:'caught and bowled'};
  const kind=forced[o*6+n] || (rnd()<.015?'bowled':'');
  const wicket=Boolean(kind);if(wicket)batter=0;
  score+=batter;balls.push({over:o,delivery:n+1,batter,total:batter,wicket,wicketKind:kind,wicketKinds:kind?[kind]:[],extra:false, nonBoundary:false,score, batterName:'',bowlerName:'',legal:true,display:`${o}.${n+1}`});
 }}return balls;}
function classify(b){if(b.wicket)return 'wicket';if(b.batter===6&&!b.nonBoundary)return 'six';if(b.batter===4&&!b.nonBoundary)return 'four';if(b.extra)return 'extra';if(b.total===0)return 'dot';return 'small';}
function parseCricsheet(obj,innIdx=0){
 if(!obj||!Array.isArray(obj.innings))throw new Error('Cricsheet JSON の innings 配列がありません。');
 if(!obj.innings[innIdx])throw new Error('指定したイニングがありません。');
 const inn=obj.innings[innIdx], balls=[];let score=0;
 for(const ov of inn.overs||[]){let k=0;for(const d of ov.deliveries||[]){k++;
   const total=Number(d.runs?.total??0), batter=Number(d.runs?.batter??d.runs?.batsman??0), extras=d.extras||{};
   const legal=!('wides'in extras)&&!('noballs'in extras);
   const wicket=Array.isArray(d.wickets)&&d.wickets.length>0;
   score+=total;
   balls.push({over:Number(ov.over)||0,delivery:k,batter,total,wicket,wicketKind:wicket?d.wickets.map(w=>w.kind||'wicket').join(', '):'',wicketKinds:wicket?d.wickets.map(w=>w.kind||'other'):[],wickets:wicket?d.wickets:[],extra:Number(d.runs?.extras||0)>0,nonBoundary:!!d.runs?.non_boundary,score,batterName:d.batter||'',bowlerName:d.bowler||'',legal,display:d.actual_delivery||`${Number(ov.over)||0}.${k}`});
 }}
 if(!balls.length)throw new Error('選択したイニングに記録された投球がありません。');
 return{balls,team:inn.team||'不明',inningsCount:obj.innings.length,matchType:obj.info?.event?.name||obj.info?.match_type||''};
}

export {mulberry32,fakeData,classify,parseCricsheet};
