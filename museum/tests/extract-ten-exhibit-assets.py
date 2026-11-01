"""Deterministically extract committed HTML assets/code; never write the source HTML.
Run from repository root. Derived native.mjs files retain the artists' existing
geometry/image placements and equations; renderer, UI and enclosing walls are
owned by the shared exhibition. Handwritten adapters live beside these outputs.
"""
import base64, hashlib, json, pathlib, re
ROOT = pathlib.Path(__file__).resolve().parents[1]
manifest = {'schemaVersion': 1, 'approval': '正式原画としての承認は未確認', 'items': []}
sources = {}
for item in json.loads((ROOT/'TEN_EXHIBIT_SOURCE_MAP.json').read_text())['items']:
    ident = item['id']; original = (ROOT/item['path']).read_text(); assets=[]
    folder=ROOT/'exhibition-assets'/ident; folder.mkdir(parents=True, exist_ok=True)
    def extract(m):
        mime=m[1]; raw=base64.b64decode(m[2]); n=len(assets)+1
        ext={'jpeg':'jpg','png':'png','webp':'webp'}.get(mime,mime)
        name=f'{n:02d}.{ext}'; (folder/name).write_bytes(raw)
        path=f'exhibition-assets/{ident}/{name}'
        assets.append({'index':n,'path':path,'mime':'image/'+mime,'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'source':item['path'],'sourceBlob':item['git_blob_sha'],'sourceLine':original.count('\n',0,m.start())+1,'category':'制作参考画像（正式原画としては未確認）'})
        return path
    sanitized=re.sub(r'data:image/([^;\s"\']+);base64,([A-Za-z0-9+/=]+)',extract,original)
    scripts=re.findall(r'<script\b([^>]*)>([\s\S]*?)</script>',sanitized)
    data={}
    for attrs,body in scripts:
        if 'application/json' in attrs:
            key=re.search(r'id=["\']([^"\']+)',attrs)
            if key:data[key[1]]=json.loads(body)
    if ident=='009': data['images']=json.loads(re.search(r'const IMAGES=(\{.*?\});',sanitized)[1])
    (folder/'data.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
    sources[ident]={'html':sanitized,'js':max((b for a,b in scripts),key=len),'data':data}
    manifest['items'].append({'id':ident,'source':item['path'],'sourceBlob':item['git_blob_sha'],'sourceSHA256':hashlib.sha256((ROOT/item['path']).read_bytes()).hexdigest(),'images':assets})
(ROOT/'exhibition-assets/manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')

def lines(ident,a,b): return '\n'.join(sources[ident]['js'].splitlines()[a-1:b])+'\n'
def emit(ident,body):
    dest=ROOT/'exhibits'/ident;dest.mkdir(exist_ok=True)
    (dest/'native.mjs').write_text('// Derived by tests/extract-ten-exhibit-assets.py. Source HTML is preserved.\n// See exhibition-assets/manifest.json for source blob and embedded image hashes.\nexport function createNative({THREE, scene, camera, renderer, assets, works, images, ui}) {\nconst $=ui;\n'+body+'\n}\n')

# 001: only the original ball material/intersection, excluding composite Work 02.
s=sources['001']['html']; shader=re.search(r'<script id="fragment"[^>]*>([\s\S]*?)</script>',s)[1]
shader=shader[shader.index('#define PI'):shader.index('vec3 slabColor')]
(ROOT/'exhibits/001').mkdir(exist_ok=True)
(ROOT/'exhibits/001/ball-source.glsl').write_text('// Extracted from 001 v1.1; original sphere relief and photographic material.\n'+shader)
# 003: all original rope geometry, transported frames and fibre shader.
emit('003',lines('003',6,48)+lines('003',63,161)+'''
function geometry(builder) {
 const g=new THREE.BufferGeometry(),v=new THREE.InterleavedBuffer(new Float32Array(builder.v),13);
 for(const [name,size,offset] of [['aPos',3,0],['aNorm',3,3],['aCol',4,6],['aUV',2,10],['aKind',1,12]])g.setAttribute(name,new THREE.InterleavedBufferAttribute(v,size,offset));
 g.setAttribute('position',g.getAttribute('aPos'));g.setIndex(builder.i);g.computeBoundingSphere();return g;
}
const uniforms={uProj:{value:new THREE.Matrix4()},uView:{value:new THREE.Matrix4()},uCamera:{value:new THREE.Vector3()},uLight:{value:1}};
const mat=new THREE.RawShaderMaterial({glslVersion:THREE.GLSL3,vertexShader:VS.replace('#version 300 es',''),fragmentShader:FS.replace('#version 300 es',''),uniforms,side:THREE.DoubleSide});
let level=3,mesh=new THREE.Mesh(geometry(ropeGeometry(3)),mat);scene.add(mesh);
return {update(){uniforms.uProj.value.copy(camera.projectionMatrix);uniforms.uView.value.copy(camera.matrixWorldInverse);uniforms.uCamera.value.copy(camera.position)},set(name,value){if(name==='material'){level=Number(value);const g=geometry(ropeGeometry(level));mesh.geometry.dispose();mesh.geometry=g}},stats(){return {material:['滑らかな管','三つ撚り','繊維の質感','3束×9本の撚り糸'][level],materialMode:level,triangles:mesh.geometry.index.count/3}}};
''')
# 004: original eleven cutouts/scrim/echoes and three sightline stations.
emit('004','let artworks=[],sightMarkers=[];\n'+lines('004',6,17)+lines('004',21,84)+'''
spawn();return {update(){for(const e of sightMarkers){const d=Math.hypot(camera.position.x-e.spot.x,camera.position.z-e.spot.z);e.ring.material.opacity=THREE.MathUtils.lerp(.35,.81,THREE.MathUtils.clamp(1-d/3,0,1))}},stats(){return {layers:artworks.length,stations:sightStops.length}}};
''')
# 005: original eleven bodies, echo planes and source light relations.
emit('005','let subjects=[],orb,lightThreads=[],relations=false;\n'+sources['005']['js'][sources['005']['js'].index('const tloader'):sources['005']['js'].index('function makeRoom')]+sources['005']['js'][sources['005']['js'].index('function makeSubject'):sources['005']['js'].index('function setup')]+'''
works.forEach(makeSubject);makeConstellation();return {update(dt){const d=Math.hypot(camera.position.x,camera.position.z),tgt=relations?(.13+.23*Math.max(0,1-d/12)):0;for(const l of lightThreads)l.material.opacity+=(tgt-l.material.opacity)*Math.min(1,dt*3.5)},set(name,value){if(name==='relations')relations=value},stats(){return {bodies:subjects.length,relations}}};
''')
# 006: original 12 image scrims, 4200 particles, 86 filaments and 13 waves.
emit('006','const loader=new THREE.TextureLoader();let reflect=true;\n'+lines('006',8,12)+lines('006',15,51)+lines('006',96,123)+'''
return {update(dt,now){updateArt(now,dt)},set(name,value){if(name==='reflect')reflect=value},stats(){return {particles:COUNT,scrims:photopanels.length,filaments:filaments.length,reflect}}};
''')
# 007: preserve hanging archives, blank sheets and distance-sensitive silence.
s=sources['007']['js']; core=s[s.index(' const gold='):s.index(' let yaw=')]
core='\n'.join(l for l in core.splitlines() if not l.strip().startswith(('box([0,5,-16]', 'box([0,10,0]')))
emit('007','const slices=assets.panels;let group,emptyGroup,ambient,lamps=[];\n'+core+"function nearest(){let min=Infinity;for(const p of archive)min=Math.min(min,Math.hypot(p.x-camera.position.x,p.z-camera.position.z));return {dist:min}}\n"+s[s.index(' let phase=0;'):s.index(' let prevFrame=')]+'''
return {update(dt){art(dt)},stats(){return {documents:archive.length,blankSheets:voidSheets.length}}};
''')
# 008: retain source mapping, fixture, signatures and all three animation modes.
s=sources['008']['js']; start=s.index('const COLORS=');end=s.index('function selectNearest')
pure=s[s.index('function mulberry32'):s.index('function prepareBalls')]
(ROOT/'exhibits/008').mkdir(exist_ok=True)
(ROOT/'exhibits/008/data-source.mjs').write_text('// Pure data functions extracted verbatim from Work08 v2.9.\n'+pure+'\nexport {mulberry32,fakeData,classify,parseCricsheet};\n')
body=s[start:end].replace(pure,'')
body=s[s.index('const curatedMatches='):s.index('const curatedData=')]+s[s.index('function sumInnings'):s.index('function currentCurated')]+body
body+='\n'+s[s.index('function loadPhotoPanels'):s.index('function reset()')].replace("JSON.parse(document.querySelector('#image-assets').textContent)",'assets')
# Native update without source camera/input/UI loop.
update=s[s.index(' const focusCycle=now-pulseBirth'):s.index('function setOverOptions')]
update=update[:update.rfind('}')]
emit('008','''
let starRoot=new THREE.Group(),lineRoot=new THREE.Group(),photoRoot,starMeshes=[],glows=[],pulseFocus=null,featuredEvent=null,pulseFocusIndex=-1,pulseEvents=[],pulseBirth=performance.now();
scene.add(starRoot,lineRoot);let allBalls=[],displayBalls=[],visibleBalls=[],mode='trace',typeFilter='all',focusOver='all',dismissalFilter='all',wicketKindsOn=true,scoreColorsOn=true,intensity='high',selectedIndex=-1,demo=true,dataName='創作120球';
const toastEl=ui('#toast'),PULSE_STEP=1950,intensityValues={low:1.25,medium:2,high:3.05};let actionToastTime=0,userJSON=null,inning=0,selectedMatch='',dataAuto=false,dataClock=0,dwellSeconds=30,curatedData=new Map();
'''+body+'''
allBalls=fakeData();loadPhotoPanels();redraw();
function animateArt(dt,now){
'''+update+'''
}
function loadJSON(obj,index=0){const parsed=parseCricsheet(obj,index);userJSON=obj;inning=index;selectedMatch='';dataAuto=false;dataClock=0;allBalls=parsed.balls;demo=false;dataName='読み込みJSON / '+parsed.team;focusOver='all';typeFilter='all';dismissalFilter='all';redraw()}
async function loadZIP(file,onProgress){if(typeof JSZip==='undefined')throw new Error('ローカルZIPライブラリを取得できません');const zip=await JSZip.loadAsync(file),entries=Object.values(zip.files).filter(f=>!f.dir&&/\.json$/i.test(f.name));if(!entries.length)throw new Error('ZIPにJSONがありません');for(let n=0;n<entries.length;n++){if(n%70===0){onProgress?.(n,entries.length);await new Promise(r=>setTimeout(r,0))}let raw,obj;try{raw=await entries[n].async('string');if(!curatedMatches.some(c=>raw.includes(c.date)))continue;obj=JSON.parse(raw)}catch{continue}for(const c of curatedMatches)if(!curatedData.has(c.id)&&matchesCurated(obj,c))curatedData.set(c.id,{obj,fileName:entries[n].name});if(curatedData.size===curatedMatches.length)break}onProgress?.(entries.length,entries.length);return {found:curatedData.size,total:curatedMatches.length}}
function playMatch(id){if(!curatedData.has(id))return;loadJSON(curatedData.get(id).obj);selectedMatch=id}
function advanceData(){const match=curatedData.get(selectedMatch);if(match&&inning+1<match.obj.innings.length){const id=selectedMatch;loadJSON(match.obj,inning+1);selectedMatch=id}else{const loaded=curatedMatches.filter(c=>curatedData.has(c.id)),index=loaded.findIndex(c=>c.id===selectedMatch);if(loaded.length)playMatch(loaded[(index+1+loaded.length)%loaded.length].id)}dataAuto=true;dataClock=0}
return {update(dt,now){animateArt(dt,now);if(dataAuto){dataClock+=dt;if(dataClock>=dwellSeconds)advanceData()}},set(name,value){if(name==='sourceDwell')dwellSeconds=Number(value);if(name==='autoMatches'){dataAuto=Boolean(value)&&curatedData.size>0;dataClock=0;if(dataAuto&&!curatedData.has(selectedMatch)){playMatch(curatedMatches.find(c=>curatedData.has(c.id)).id);dataAuto=true}}
if(name==='mode')mode=value;if(name==='filter')typeFilter=value;if(name==='over')focusOver=value;if(name==='dismissal')dismissalFilter=value;if(name==='intensity')intensity=value;if(name==='wicketKinds')wicketKindsOn=value;if(name==='scoreColors')scoreColorsOn=value;if(name==='inning'&&userJSON){const id=selectedMatch;loadJSON(userJSON,Number(value));selectedMatch=id;return}if(name==='match'&&curatedData.has(value)){loadJSON(curatedData.get(value).obj);selectedMatch=value;return}if(name==='demo'){allBalls=fakeData();demo=true;userJSON=null;inning=0;selectedMatch='';dataAuto=false;dataClock=0;dataName='創作120球';focusOver='all';typeFilter='all';dismissalFilter='all'}redraw()},loadJSON,loadZIP,stats(){return {balls:allBalls.length,shown:starMeshes.length,demo,mode,events:pulseEvents.length,inning,innings:userJSON?.innings.map((i,n)=>[String(n),'第'+(n+1)+'イニング '+(i.team||'')])||[],overs:[...new Set(allBalls.map(b=>b.over))].map(o=>[String(o),String(o+1)+'オーバー目']),matches:curatedMatches.filter(c=>curatedData.has(c.id)).map(c=>[c.id,c.title]),curatedFound:curatedData.size,dataAuto,dwellSeconds,currentMatch:selectedMatch,values:{autoMatches:dataAuto,sourceDwell:String(dwellSeconds),mode,filter:typeFilter,over:focusOver,dismissal:dismissalFilter,intensity,wicketKinds:wicketKindsOn,scoreColors:scoreColorsOn,inning:String(inning),match:selectedMatch}}}};
''')
native=ROOT/'exhibits/008/native.mjs'
native.write_text("import {mulberry32,fakeData,classify,parseCricsheet} from './data-source.mjs';\n"+native.read_text())
# Equations/data from Canvas sources; their world primitives are mapped by adapters.
(ROOT/'exhibits/009').mkdir(exist_ok=True)
(ROOT/'exhibits/009/source-data.mjs').write_text('// Original Work09 deterministic positions and gravity equation.\nconst clamp=(x,a,b)=>Math.min(b,Math.max(a,x));\nexport function sourceData(){\n'+lines('009',12,16)+'return {islands,balls,bats,rocks};}\nexport '+lines('009',48,48).replace('function floatingHeight(base,phase,amplitude=1)','function floatingHeight(base,phase,amplitude=1,gravity=1,time=0,motionReduced=false)') )
(ROOT/'exhibits/010').mkdir(exist_ok=True)
(ROOT/'exhibits/010/source-equations.mjs').write_text('// Original Work10 boundary equations; renderer-independent.\nexport function equations(state){\nconst {artTime,crossCount}=state;\n'+lines('010',33,35)+'return {boundaryRadius,boundaryPos,boundaryLevel};}\n')
print('Extracted',sum(len(i['images']) for i in manifest['items']),'embedded images; native source modules 003–008 and ball shader.')
