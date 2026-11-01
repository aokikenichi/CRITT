"""Check the browser proof set collected with cua_repl and summarize acceptance."""
import json,pathlib
root=pathlib.Path(__file__).resolve().parents[1];proof=root/'qa/ten-exhibits'
rows=[]
for n in range(1,11):
 ident=f'{n:03}'; row={'id':ident}
 for viewport in ['pc','mobile']:
  samples=[]
  for h in range(1,4):
   stem=f'{viewport}-{ident}-{h}';assert (proof/(stem+'.jpg')).stat().st_size>5000
   s=json.loads((proof/(stem+'.json')).read_text());assert s['ready'] and not s['failures'];assert s['active']==ident
   art=next(a for a in s['exhibits'] if a['id']==ident);assert art['loaded'] and art['objects']>0
   if ident=='002':assert art['figureMode']=='A' and art['layers']==5
   samples.append(s)
  assert len({tuple(s['position']) for s in samples})==3
  ui=json.loads((proof/f'{viewport}-{ident}-ui.json').read_text());assert ui['positionPreserved'] and ui['focus']=='details'
  if ident=='010':assert ui['image']['image'] is None and '未収録' in ui['image']['text']
  else:assert ui['image']['image']['complete'] and ui['image']['image']['width']>0
  row[viewport]={'highlights':3,'fps_min':min(s['fps'] for s in samples),'fps_max':max(s['fps'] for s in samples),'images':f'{viewport}-{ident}-images.jpg','ui':'PASS'}
 manual=json.loads((proof/f'pc-{ident}-manual.json').read_text());assert manual['before']['mode']=='auto' and manual['after']['mode']=='manual';a,b=manual['before']['position'],manual['lateral']['position'];distance=((a[0]-b[0])**2+(a[2]-b[2])**2)**.5;assert distance>.8;assert abs(manual['after']['yaw']-manual['lateral']['yaw'])>.1
 row['manual_lateral_m']=round(distance,3);rows.append(row)
expected=[(f'{n:03}',h) for n in range(1,11) for h in range(3)]+[('exit',0)]
for v in ['pc','mobile']:
 t=json.loads((proof/f'{v}-full-tour.json').read_text());s=t['state'];assert [(p['id'],p['highlight']) for p in s['visits']]==expected;assert s['position']==[22.5,1.7,-317];assert s['mode']=='manual' and not s['failures'];assert not t['console']
assert not json.loads((proof/'pc-final-console.json').read_text())
q=json.loads((proof/'mobile-008-inning-recheck.json').read_text());assert q['first']['balls']==2 and q['second']['balls']==1 and q['second']['inning']==1
q=json.loads((proof/'mobile-viewer.json').read_text());assert q['zoom']['value']=='4' and q['zoom']['stage']['scrollWidth']>q['zoom']['stage']['clientWidth'];assert q['second']['complete']
report={'viewports':{'pc':[1440,900],'mobile':[390,844]},'works':rows,'highlightScreenshots':60,'fullTours':{'pc':31,'mobile':31},'scope':'IAB desktop browser with viewport override; not physical iOS/Android','unverified':['Real Cricsheet ZIP positive matches and match Auto with actual records','Physical mobile devices / low-memory WebGL GPUs']}
(proof/'summary.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print('PASS 10/10 works × PC/mobile × 3 viewpoints = 60 screenshots; 20 UI proofs; 10 Manual interventions; two 30-viewpoint tours + exit; viewer zoom; second inning.')
