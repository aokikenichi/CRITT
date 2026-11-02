import {mulberry32,fakeData,classify,parseCricsheet} from './data-source.mjs';
// Derived by tests/extract-ten-exhibit-assets.py. Source HTML is preserved.
// See exhibition-assets/manifest.json for source blob and embedded image hashes.
export function createNative({THREE, scene, camera, renderer, assets, works, images, ui}) {
const $=ui;

let starRoot=new THREE.Group(),lineRoot=new THREE.Group(),photoRoot,starMeshes=[],glows=[],pulseFocus=null,featuredEvent=null,pulseFocusIndex=-1,pulseEvents=[],pulseBirth=performance.now();
scene.add(starRoot,lineRoot);let allBalls=[],displayBalls=[],visibleBalls=[],mode='trace',typeFilter='all',focusOver='all',dismissalFilter='all',wicketKindsOn=true,scoreColorsOn=true,intensity='high',selectedIndex=-1,demo=true,dataName='創作120球';
const toastEl=ui('#toast'),PULSE_STEP=1950,intensityValues={low:1.25,medium:2,high:3.05};let actionToastTime=0,userJSON=null,inning=0,selectedMatch='',dataAuto=false,dataClock=0,dwellSeconds=30,curatedData=new Map();
const curatedMatches=[
 {id:'wi2016',date:'2016-04-03',teams:['England','West Indies'],gender:'male',title:'2016 世界T20決勝｜西インド諸島 vs イングランド',reason:'最終オーバーの4連続シックス。最後の一球に向かって星が集中する。'},
 {id:'indpak2022',date:'2022-10-23',teams:['India','Pakistan'],gender:'male',title:'2022 MCG｜インド vs パキスタン',reason:'大観衆の中での劇的な追い上げ。得点の時間的な偏りを見る。'},
 {id:'jpnmng2024',date:'2024-05-08',teams:['Japan','Mongolia'],gender:'male',title:'2024 佐野｜日本 vs モンゴル（第2戦）',reason:'日本217/7、モンゴル12。対照的な二つのイニングを比べる。',check:obj=>{const a=obj.innings||[];return a.length>=2&&a[0].team==='Japan'&&sumInnings(a[0])>=215&&sumInnings(a[0])<=219&&sumInnings(a[1])===12;}},
 {id:'usapak2024',date:'2024-06-06',teams:['United States of America','Pakistan'],gender:'male',title:'2024 ワールドカップ｜米国 vs パキスタン',reason:'同点からスーパーオーバーへ。小さなイニングが試合を決めた。'},
 {id:'indsa2024',date:'2024-06-29',teams:['India','South Africa'],gender:'male',title:'2024 男子T20W杯決勝｜インド vs 南アフリカ',reason:'7点差の決着。得点とウィケットの密度を見比べる。'},
 {id:'nzwsa2024',date:'2024-10-20',teams:['New Zealand','South Africa'],gender:'female',title:'2024 女子T20W杯決勝｜NZ vs 南アフリカ',reason:'ニュージーランド初優勝。女子クリケットの記録を星座に。'}
];
function sumInnings(inn){return (inn.overs||[]).reduce((t,ov)=>t+(ov.deliveries||[]).reduce((q,d)=>q+Number(d.runs?.total??0),0),0);}
function normTeam(s){let t=String(s||'').toLowerCase().replace(/women|women's|womens|team|the /g,'').replace(/[^a-z]/g,'');if(t==='usa'||t==='unitedstates')return 'unitedstatesofamerica';if(t==='windies')return 'westindies';return t;}
function matchesCurated(obj,c){const info=obj?.info||{};if(String(info.dates?.[0]||'').slice(0,10)!==c.date)return false;
 if(info.gender!==c.gender)return false;
 const teams=(info.teams||[]).map(normTeam).sort().join('|');
 if(teams!==c.teams.map(normTeam).sort().join('|'))return false;
 return !c.check||c.check(obj);
}
const COLORS={dot:0x74bafc,small:0xc5d6ee,four:0x70f2c3,six:0xffcc75,wicket:0xff7184,extra:0xbaa8ff};
const WICKET_COLORS={caught:0xff72c0,bowled:0xff5b5b,lbw:0xffdc65,'run out':0x64dcff,stumped:0xbb8eff,other:0xf4a8a8};
const WICKET_JA={caught:'Caught / キャッチ',bowled:'Bowled / ボウルド',lbw:'LBW','run out':'Run out / ランアウト',stumped:'Stumped / スタンプト',other:'その他の記録・退場'};
function wicketKey(kind){const s=String(kind||'').trim().toLowerCase();
 if(s==='caught'||s==='caught and bowled')return 'caught';
 if(['bowled','lbw','run out','stumped'].includes(s))return s;
 return 'other';
}
function kindOfBall(b){return wicketKey(b.wicketKinds?.[0]||b.wicketKind?.split(',')[0]||'');}
function ballColor(type,b){return (!scoreColorsOn ? 0xdde8f4 : type==='wicket' && wicketKindsOn ? WICKET_COLORS[kindOfBall(b)] : COLORS[type]);}

const COLORS_CSS={dot:'#8bbffc',small:'#d0dff0',four:'#78efd5',six:'#ffd18b',wicket:'#ff899a',extra:'#c4aaff'};
function notify(s){toastEl.textContent=s;toastEl.classList.add('on');actionToastTime=performance.now()+3200;}
function prepareBalls(){
 displayBalls=allBalls.filter(b=>focusOver==='all'||b.over===Number(focusOver));
 visibleBalls=displayBalls.filter(b=>(typeFilter==='all'||classify(b)===typeFilter) && (dismissalFilter==='all'||(b.wicket && kindOfBall(b)===dismissalFilter)));
}
function ringMat(c,opacity){return new THREE.MeshBasicMaterial({color:c,transparent:true,opacity,depthWrite:false,side:THREE.DoubleSide,blending:THREE.AdditiveBlending})}
function makeCircleTex(){const canvas=document.createElement('canvas');canvas.width=96;canvas.height=96;const ctx=canvas.getContext('2d');const grd=ctx.createRadialGradient(48,48,0,48,48,46);grd.addColorStop(0,'rgba(255,255,255,1)');grd.addColorStop(.11,'rgba(255,255,255,.98)');grd.addColorStop(.32,'rgba(255,255,255,.41)');grd.addColorStop(1,'rgba(255,255,255,0)');ctx.fillStyle=grd;ctx.fillRect(0,0,96,96);return new THREE.CanvasTexture(canvas);}
const circleTexture=makeCircleTex();
const disposeGroup=g=>{while(g.children.length){let o=g.children.pop();if(o.parent)o.parent.remove(o);o.traverse?.(x=>{x.geometry?.dispose?.();if(x.material && !x.material.userData?.shared)x.material.dispose?.()})}};
function spatial(b,idx,total){
  // Explicit conceptual mapping, NOT a reconstructed ball trajectory.
  const order=idx, phase=(order/Math.max(1,total-1))*Math.PI*2*3.4+.45;
  const lane=(b.over%4)*.11;
  const radius=3.9+lane+(Math.max(0,b.total)*.13)+(b.wicket?.34:0);
  const y=2.65+(b.over/Math.max(1,Math.max(...allBalls.map(x=>x.over))))*4.7+Math.sin(phase*1.83)*.32+(b.wicket?.38:0);
  return new THREE.Vector3(Math.sin(phase)*radius,y,Math.cos(phase)*radius);
}
// Out types have distinct shapes as well as colors; the shapes remain visible in trace mode.
function addWicketSignature(parent,p,kind,color,scale=.5){
 const group=new THREE.Group();group.position.copy(p);parent.add(group);
 const mat=new THREE.MeshBasicMaterial({color,transparent:true,opacity:.68,depthWrite:false,blending:THREE.AdditiveBlending,side:THREE.DoubleSide});
 const rod=(a,b,r=.011)=>{const v=new THREE.Vector3().subVectors(b,a),mesh=new THREE.Mesh(new THREE.CylinderGeometry(r,r,v.length(),6),mat);mesh.position.copy(a).addScaledVector(v,.5);mesh.quaternion.setFromUnitVectors(new THREE.Vector3(0,1,0),v.normalize());group.add(mesh);return mesh;};
 const torus=(r,arc=Math.PI*2)=>{const o=new THREE.Mesh(new THREE.TorusGeometry(r,.013,5,44,arc),mat);group.add(o);return o;};
 if(kind==='caught'){const t1=torus(scale*.42,Math.PI*.9),t2=torus(scale*.42,Math.PI*.9);t1.position.x=-scale*.10;t2.position.x=scale*.10;t2.rotation.z=Math.PI;}
 else if(kind==='bowled'){for(let x of [-.17,0,.17])rod(new THREE.Vector3(x*scale, -.22*scale,0),new THREE.Vector3(x*scale,.25*scale,0),.018);rod(new THREE.Vector3(-.25*scale,.20*scale,0),new THREE.Vector3(.25*scale,.20*scale,0),.015);}
 else if(kind==='lbw'){const w=scale*.27;for(const [a,b] of [[[-w,-w,0],[w,-w,0]],[[w,-w,0],[w,w,0]],[[w,w,0],[-w,w,0]],[[-w,w,0],[-w,-w,0]]])rod(new THREE.Vector3(...a),new THREE.Vector3(...b),.015);}
 else if(kind==='run out'){rod(new THREE.Vector3(-scale*.35,-scale*.15,0),new THREE.Vector3(scale*.35,scale*.15,0),.022);rod(new THREE.Vector3(scale*.35,-scale*.15,0),new THREE.Vector3(-scale*.35,scale*.15,0),.022);}
 else if(kind==='stumped'){torus(scale*.32);torus(scale*.12);}
 else torus(scale*.28);
 return group;
}

// One large, changing pulse at a time: keeps the spatial rhythm legible even with 120 balls.
function makeFocusEffects(event){
 if(pulseFocus){lineRoot.remove(pulseFocus);disposeGroup(pulseFocus);pulseFocus=null;}
 if(!event)return;
 const type=event.type,kind=event.kind,color=ballColor(type,event.ball);
 pulseFocus=new THREE.Group();pulseFocus.position.copy(event.pos);lineRoot.add(pulseFocus);
 const makeRing=(radius,opacity,arc=2*Math.PI)=>{const m=new THREE.MeshBasicMaterial({color,transparent:true,opacity,depthWrite:false,side:THREE.DoubleSide,blending:THREE.AdditiveBlending});const x=new THREE.Mesh(new THREE.TorusGeometry(radius,.025,7,80,arc),m);pulseFocus.add(x);return x;};
 const r1=makeRing(.40,.82),r2=makeRing(.73,.48);pulseFocus.userData.rings=[r1,r2];
 const petals=[];const rodMat=new THREE.MeshBasicMaterial({color,transparent:true,opacity:.9,depthWrite:false,blending:THREE.AdditiveBlending});
 const rod=(a,b,r=.025)=>{const v=new THREE.Vector3().subVectors(b,a);const g=new THREE.CylinderGeometry(r,r,v.length(),7);const m=new THREE.Mesh(g,rodMat);m.position.copy(a).addScaledVector(v,.5);m.quaternion.setFromUnitVectors(new THREE.Vector3(0,1,0),v.normalize());pulseFocus.add(m);petals.push(m);return m;};
 if(type==='wicket' && wicketKindsOn){
  if(kind==='caught'){const a=makeRing(.58,.92,Math.PI*.78),b=makeRing(.58,.92,Math.PI*.78);a.position.x=-.23;b.position.x=.23;b.rotation.z=Math.PI;pulseFocus.userData.special=[a,b];}
  else if(kind==='bowled'){for(let i=0;i<9;i++){const a=(i/9)*Math.PI*2;rod(new THREE.Vector3(Math.cos(a)*.20,Math.sin(a)*.20,0),new THREE.Vector3(Math.cos(a)*1.6,Math.sin(a)*1.6,0),.021);} }
  else if(kind==='lbw'){for(let i=-1;i<=1;i++)rod(new THREE.Vector3(i*.18,-.60,0),new THREE.Vector3(i*.18,.60,0),.035);}
  else if(kind==='run out'){rod(new THREE.Vector3(-1.1,-.45,0),new THREE.Vector3(1.1,.45,0),.038);rod(new THREE.Vector3(1.1,-.45,0),new THREE.Vector3(-1.1,.45,0),.038);}
  else if(kind==='stumped'){pulseFocus.userData.special=[makeRing(.46,.95),makeRing(.24,.7)];}
 }
 pulseFocus.userData.petals=petals;
}
function animateFocus(t){if(!pulseFocus||!featuredEvent)return;
 const power=intensityValues[intensity], type=featuredEvent.type, kind=featuredEvent.kind;
 pulseFocus.quaternion.copy(camera.quaternion);const tt=Math.min(1,t);const envelope=Math.sin(tt*Math.PI);
 const r=pulseFocus.userData.rings||[];
 r.forEach((x,i)=>{const size=(.35+i*.4+tt*power*.85);x.scale.setScalar(size);x.material.opacity=(1-tt)*(.72-i*.23)*Math.min(1.35,power/2);});
 const p=pulseFocus.userData.petals||[];
 p.forEach((x,i)=>{x.visible=tt<.65;x.scale.setScalar(.35+tt*power*.70);x.material.opacity=Math.max(0,1-tt*1.7);});
 const extra=pulseFocus.userData.special||[];
 if(type==='wicket' && wicketKindsOn){
  if(kind==='caught'&&extra.length===2){const close=.24*(1-tt);extra[0].position.x=-close;extra[1].position.x=close;extra.forEach(x=>{x.scale.setScalar(.6+.6*envelope);x.material.opacity=.8*(1-tt*.7);});}
  if(kind==='stumped')extra.forEach((x,i)=>{x.scale.setScalar(Math.max(.12,(1-tt)*1.7-i*.15));x.material.opacity=1-tt;});
 }
 pulseFocus.visible=true;
}
function redraw(){
 prepareBalls();disposeGroup(starRoot);disposeGroup(lineRoot);pulseFocus=null;featuredEvent=null;pulseFocusIndex=-1;pulseEvents=[];pulseBirth=performance.now();starMeshes=[];glows=[];selectedIndex=-1;
 const positions=displayBalls.map((b,i)=>spatial(b,i,displayBalls.length));
 const selected=displayBalls.map((b,i)=>({b,i})).filter(({b})=>(typeFilter==='all'||classify(b)===typeFilter) && (dismissalFilter==='all'||(b.wicket&&kindOfBall(b)===dismissalFilter)));
 if(mode==='memory'){
   const ghostGeo=new THREE.BufferGeometry().setFromPoints(positions);
   const ghost=new THREE.Line(ghostGeo,new THREE.LineBasicMaterial({color:0x526d82,transparent:true,opacity:.22}));lineRoot.add(ghost);
 } else if(positions.length>1){
   const lineGeo=new THREE.BufferGeometry().setFromPoints(positions);
   const col=mode==='pulse'?0x315474:0x8ab4ed;
   const line=new THREE.Line(lineGeo,new THREE.LineBasicMaterial({color:col,transparent:true,opacity:mode==='trace'?.27:.12,depthWrite:false}));lineRoot.add(line);
 }
 for(const {b,i} of selected){
   const type=classify(b), p=positions[i],kind=type==='wicket'?kindOfBall(b):'';
   if(mode==='memory' && type!=='wicket'&&type!=='six'&&type!=='four'&&i%5!==0)continue;
   const isMajor=type==='six'||type==='wicket', scale=(mode==='pulse'?(type==='wicket'?.47:type==='six'?.36:type==='four'?.28:(.11+Math.min(3,b.total)*.026)):(isMajor?.31:type==='four'?.22:.12));
   const mat=new THREE.SpriteMaterial({map:circleTexture,color:ballColor(type,b),transparent:true,opacity:mode==='memory'?.9:.92,depthWrite:false,blending:THREE.AdditiveBlending});
   const sprite=new THREE.Sprite(mat);sprite.position.copy(p);sprite.scale.set(scale*2.1,scale*2.1,1);sprite.userData={ball:b,index:i,color:ballColor(type,b),size:scale,type,kind};starRoot.add(sprite);starMeshes.push(sprite);
   if(isMajor || type==='four'){
     const sphere=new THREE.Mesh(new THREE.SphereGeometry(scale*.19,12,8),new THREE.MeshBasicMaterial({color:ballColor(type,b),transparent:true,opacity:.9}));sphere.position.copy(p);starRoot.add(sphere);
     glows.push({sprite,phase:i*1.31});
    pulseEvents.push({sprite,pos:p.clone(),ball:b,type,kind,index:i});
   }
   if(type==='wicket'&&wicketKindsOn){addWicketSignature(starRoot,p,kind,ballColor(type,b),.60);}
   if(mode==='trace'&&i>0&&type!=='dot'){
     // Halo, no misleading literal ball travel path.
     const ring=new THREE.Mesh(new THREE.TorusGeometry(scale*.57,.007,4,48),ringMat(ballColor(type,b),.32));ring.position.copy(p);ring.rotation.x=Math.PI/2.9;starRoot.add(ring);
   }
 }
 $('#count').textContent=`${selected.length}球表示 / 記録${allBalls.length}球`;
 const shownScore=allBalls.length?allBalls.at(-1).score:0;
 const suffix=demo?'架空の試作データ':'読み込みデータ';
 $('#dataset').textContent=`${suffix}｜${dataName}`;$('#dataset2').textContent=demo?'試作データ':'Cricsheet JSON';
 $('#mapping').textContent=`表示：${mode==='trace'?'連なり':mode==='pulse'?'脈動':'余白'} ／ ${focusOver==='all'?'全オーバー':Number(focusOver)+1+'オーバー目'} ／ ${shownScore}ラン（選択イニング合計・記録分）`;
 const wks=allBalls.filter(b=>b.wicket).length;
 $('#wicketLegend').style.display=wicketKindsOn?'block':'none';
 $('#pulseStatus').textContent=mode==='pulse'?`重要イベント ${pulseEvents.length}件を順に強調中｜表示イニングのアウト ${wks}球`:'「脈動」に切り替えると重要イベントを順に強調します。';

 $('#modeBtns').querySelectorAll('button').forEach(b=>b.classList.toggle('active',b.dataset.mode===mode));
 $('#filterBtns').querySelectorAll('button').forEach(b=>b.classList.toggle('active',b.dataset.filter===typeFilter));
}

function loadPhotoPanels(){const data=assets;photoRoot=new THREE.Group();scene.add(photoRoot);
 const positions=[{x:0,y:5.55,z:-11.15,w:14.4,h:8.1,rot:0,idx:0,o:.45},{x:-10.4,y:5.3,z:1.4,w:6.2,h:8.6,rot:Math.PI/2.4,idx:1,o:.40},{x:9.4,y:5.2,z:-3.5,w:9,h:6.25,rot:-.99,idx:2,o:.36}];
 positions.forEach((q,i)=>{const tex=new THREE.TextureLoader().load(data[`veil${q.idx}`]);tex.colorSpace=THREE.SRGBColorSpace;const mat=new THREE.MeshBasicMaterial({map:tex,transparent:true,opacity:q.o,depthWrite:false,side:THREE.DoubleSide,blending:THREE.AdditiveBlending});const m=new THREE.Mesh(new THREE.PlaneGeometry(q.w,q.h),mat);m.position.set(q.x,q.y,q.z);m.rotation.y=q.rot;photoRoot.add(m)});
}

allBalls=fakeData();loadPhotoPanels();redraw();
function animateArt(dt,now){
 const focusCycle=now-pulseBirth;let active=-1,phase=0;
 if(mode==='pulse'&&pulseEvents.length){active=Math.floor(focusCycle/PULSE_STEP)%pulseEvents.length;phase=(focusCycle%PULSE_STEP)/PULSE_STEP;
  if(pulseFocusIndex!==active){pulseFocusIndex=active;featuredEvent=pulseEvents[active];makeFocusEffects(featuredEvent);}
  if(featuredEvent){const b=featuredEvent.ball;
   const tag=featuredEvent.type==='wicket'?(wicketKindsOn?WICKET_JA[featuredEvent.kind]:'アウト'):featuredEvent.type==='six'?'SIX / シックス':'FOUR / フォー';
   $('#pulseStatus').textContent=`脈動：${tag}｜${b.display}球　重要イベント ${active+1}/${pulseEvents.length}`;animateFocus(phase);
  }
 }
 const amp=intensityValues[intensity];
 for(const o of glows){
  const s=o.sprite, base=s.userData.size*2.1;
  let m=1+.17*Math.sin(now*.004+o.phase);
  if(mode==='pulse'){
   const isF=featuredEvent?.sprite===s;
   m=1+(.17+.20*amp)*Math.pow(.5+.5*Math.sin(now*.007+o.phase),2);
   if(isF){const e=Math.pow(Math.sin(Math.min(1,phase)*Math.PI),.7);m+=amp*1.12*e;}
  }
  s.scale.set(base*m,base*m,1);
 }
 if(now>actionToastTime)toastEl.classList.remove('on');

}
function loadJSON(obj,index=0){const parsed=parseCricsheet(obj,index);userJSON=obj;inning=index;selectedMatch='';dataAuto=false;dataClock=0;allBalls=parsed.balls;demo=false;dataName='読み込みJSON / '+parsed.team;focusOver='all';typeFilter='all';dismissalFilter='all';redraw()}
async function loadZIP(file,onProgress){if(typeof JSZip==='undefined')throw new Error('ローカルZIPライブラリを取得できません');const zip=await JSZip.loadAsync(file),entries=Object.values(zip.files).filter(f=>!f.dir&&/\.json$/i.test(f.name));if(!entries.length)throw new Error('ZIPにJSONがありません');for(let n=0;n<entries.length;n++){if(n%70===0){onProgress?.(n,entries.length);await new Promise(r=>setTimeout(r,0))}let raw,obj;try{raw=await entries[n].async('string');if(!curatedMatches.some(c=>raw.includes(c.date)))continue;obj=JSON.parse(raw)}catch{continue}for(const c of curatedMatches)if(!curatedData.has(c.id)&&matchesCurated(obj,c))curatedData.set(c.id,{obj,fileName:entries[n].name});if(curatedData.size===curatedMatches.length)break}onProgress?.(entries.length,entries.length);return {found:curatedData.size,total:curatedMatches.length}}
function playMatch(id){if(!curatedData.has(id))return;loadJSON(curatedData.get(id).obj);selectedMatch=id}
function advanceData(){const match=curatedData.get(selectedMatch);if(match&&inning+1<match.obj.innings.length){const id=selectedMatch;loadJSON(match.obj,inning+1);selectedMatch=id}else{const loaded=curatedMatches.filter(c=>curatedData.has(c.id)),index=loaded.findIndex(c=>c.id===selectedMatch);if(loaded.length)playMatch(loaded[(index+1+loaded.length)%loaded.length].id)}dataAuto=true;dataClock=0}
return {update(dt,now){animateArt(dt,now);if(dataAuto){dataClock+=dt;if(dataClock>=dwellSeconds)advanceData()}},set(name,value){if(name==='sourceDwell')dwellSeconds=Number(value);if(name==='autoMatches'){dataAuto=Boolean(value)&&curatedData.size>0;dataClock=0;if(dataAuto&&!curatedData.has(selectedMatch)){playMatch(curatedMatches.find(c=>curatedData.has(c.id)).id);dataAuto=true}}
if(name==='mode')mode=value;if(name==='filter')typeFilter=value;if(name==='over')focusOver=value;if(name==='dismissal')dismissalFilter=value;if(name==='intensity')intensity=value;if(name==='wicketKinds')wicketKindsOn=value;if(name==='scoreColors')scoreColorsOn=value;if(name==='inning'&&userJSON){const id=selectedMatch;loadJSON(userJSON,Number(value));selectedMatch=id;return}if(name==='match'&&curatedData.has(value)){loadJSON(curatedData.get(value).obj);selectedMatch=value;return}if(name==='demo'){allBalls=fakeData();demo=true;userJSON=null;inning=0;selectedMatch='';dataAuto=false;dataClock=0;dataName='創作120球';focusOver='all';typeFilter='all';dismissalFilter='all'}redraw()},loadJSON,loadZIP,stats(){return {balls:allBalls.length,shown:starMeshes.length,demo,mode,events:pulseEvents.length,inning,innings:userJSON?.innings.map((i,n)=>[String(n),'第'+(n+1)+'イニング '+(i.team||'')])||[],overs:[...new Set(allBalls.map(b=>b.over))].map(o=>[String(o),String(o+1)+'オーバー目']),matches:curatedMatches.filter(c=>curatedData.has(c.id)).map(c=>[c.id,c.title]),curatedFound:curatedData.size,dataAuto,dwellSeconds,currentMatch:selectedMatch,values:{autoMatches:dataAuto,sourceDwell:String(dwellSeconds),mode,filter:typeFilter,over:focusOver,dismissal:dismissalFilter,intensity,wicketKinds:wicketKindsOn,scoreColors:scoreColorsOn,inning:String(inning),match:selectedMatch}}}};

}
