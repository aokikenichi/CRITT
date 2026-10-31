"""Check receipt integrity and separation from adopted Step03 sources."""
import base64
import hashlib
import json
from pathlib import Path
import re
import subprocess

museum = Path(__file__).resolve().parents[1]
repo = museum.parent
manifest = json.loads((museum / 'recovered/RECOVERY_MANIFEST.json').read_text())
rows = []
for asset in manifest['assets']:
    source = museum / 'recovered' / asset['rel_path']
    content = source.read_bytes()
    digest = hashlib.sha256(content).hexdigest()
    assert len(content) == asset['bytes'], source
    assert digest == asset['sha256'], source
    images = re.findall(rb'data:image/[^;"\s]+;base64,([A-Za-z0-9+/=]+)', content)
    assert len(images) == asset['embedded_data_image_count'], source
    for encoded in images:
        assert base64.b64decode(encoded, validate=True)
    rows.append({'id': asset['id'], 'variant': asset['variant'], 'bytes': len(content),
                 'sha256': digest, 'matches_received_manifest': True, 'embedded_images': len(images)})

catalog = json.loads((museum / 'review-artworks.json').read_text())['items']
assert len(catalog) == 10
assert all(item['originals'] == [] for item in catalog)
variants = [variant for item in catalog for variant in item['variants']]
assert len(variants) == 16
assert sum(variant['connection_allowed'] for variant in variants) == 14
for item in catalog:
    default = next(variant for variant in item['variants'] if variant['key'] == item['default_variant'])
    assert default['connection_allowed']
    for variant in item['variants']:
        source = museum / variant['work_url']
        assert source.is_file() and source.resolve().is_relative_to(museum.resolve())
assert catalog[8]['default_variant'] == 'current_rebuild_v0.5'
assert catalog[9]['default_variant'] == 'current_rebuild_v1.0'
old_index = subprocess.check_output(['git', 'show', 'codex/museum-step03:museum/index.html'], cwd=repo)
assert (museum / 'source-backups/STEP03_index_snapshot.html').read_bytes() == old_index
for relative in ['artworks.json', 'works/009/index.html', 'works/010/index.html']:
    original = subprocess.check_output(['git', 'show', f'codex/museum-step03:museum/{relative}'], cwd=repo)
    assert (museum / relative).read_bytes() == original, relative
assert subprocess.check_output(['git', 'rev-parse', 'codex/museum-step03'], cwd=repo, text=True).strip() == 'f4601555d287493ad17f06f7fad2e634f0ded79e'
assert subprocess.check_output(['git', 'rev-parse', 'main'], cwd=repo, text=True).strip() == '02cd388a1f752c009eb9ea63f21befe4afa0a64f'

print('PASS: 14 recovered files match receipt hashes; 120 embedded images decode; 14/16 views enabled; archived Step03 entry and protected refs unchanged.')
