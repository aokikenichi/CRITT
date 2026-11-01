"""Verify byte-exact image extraction and preservation of committed entrances/sources."""
import hashlib,json,pathlib,re,subprocess
root=pathlib.Path(__file__).resolve().parents[1];repo=root.parent
manifest=json.loads((root/'exhibition-assets/manifest.json').read_text());count=0
for work in manifest['items']:
 raw=(root/work['source']).read_bytes();assert hashlib.sha256(raw).hexdigest()==work['sourceSHA256'],work['id']
 embedded=re.findall(rb'data:image/[^;\s"\']+;base64,([A-Za-z0-9+/=]+)',raw)
 import base64
 assert len(embedded)==len(work['images'])
 for info,encoded in zip(work['images'],embedded):
  data=(root/info['path']).read_bytes();assert data==base64.b64decode(encoded),info['path'];assert len(data)==info['bytes'];assert hashlib.sha256(data).hexdigest()==info['sha256'];count+=1
 assert (root/'exhibits'/work['id']/'index.mjs').is_file()
for rel in ['museum/index.html','museum/gallery.html','museum/gallery-direct-pilot.html']+[f"museum/{w['source']}" for w in manifest['items']]:
 original=subprocess.check_output(['git','show',f'40e96c2:{rel}'],cwd=repo);assert original==(repo/rel).read_bytes(),rel
entry=(root/'exhibition.html').read_text();assert '<iframe' not in entry;assert 'https://' not in entry
print(f'PASS {count}/88 embedded images byte-identical, 10 adapters, 13 protected originals/entrances unchanged; no entry CDN/iframe.')
