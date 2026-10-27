"""Verify delivery inventory and byte-for-byte preservation; stdlib only."""
import csv
import hashlib
import json
from pathlib import Path

museum = Path(__file__).resolve().parents[1]
backup = museum / 'source-backups' / 'INPUT'
manifest = list(csv.DictReader((backup / 'ASSET_MANIFEST.csv').open(encoding='utf-8-sig')))
checked = []
for path in backup.rglob('*'):
    if not path.is_file():
        continue
    recorded = next((row for row in manifest if row['file_name'] == path.name), None)
    if recorded:
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        assert digest == recorded['sha256'], f'SHA mismatch: {path.name}'
        assert path.stat().st_size == int(recorded['bytes']), f'Size mismatch: {path.name}'
        checked.append(path.name)
for aid, filename in [('009', 'CRITT_Museum_Work09_Gravity_Panorama_Rebuild_v0.5.html'),
                      ('010', 'CRITT_Museum_Work10_Final_Boundary_v1.0.html')]:
    assert (museum / 'works' / aid / 'index.html').read_bytes() == (backup / filename).read_bytes()
items = json.loads((museum / 'artworks.json').read_text())['items']
assert [item['id'] for item in items] == [f'{i:03}' for i in range(1, 11)]
assert all(item['originals'] == [] for item in items), 'No approved originals supplied for this delivery'
assert all(item['work_url'] is None and item['status'] == 'missing' for item in items[:8])
assert all(item['work_url'] == f'works/{item["id"]}/index.html' for item in items[8:])
assert not any((museum / 'works' / f'{i:03}').exists() for i in range(1, 9))
print(f'PASS: {len(checked)} supplied assets match input manifest; 009/010 bytes preserved; 10 honest catalog entries.')
