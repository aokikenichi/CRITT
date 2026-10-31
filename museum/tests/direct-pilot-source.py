"""Verify that the pilot's reference-derived images are byte-for-byte extracts."""
import base64
from pathlib import Path
import re

museum = Path(__file__).resolve().parents[1]
source = (museum / 'recovered/sources/002/CRITT_Museum_Work02_3D_Lab_v1.2.html').read_text()
assets = {
    'ballPhotoTextureData': 'ball-front.jpg',
    'leatherMicroNormalData': 'leather-normal.jpg',
    'referenceImageData': 'ball-reference.jpg',
    'secondReferenceImageData': 'bowling-reference.jpg',
}
for variable, name in assets.items():
    match = re.search(r'const ' + variable + r'''\s*=\s*['"]data:image/[^;]+;base64,([^'"]+)['"]''', source)
    assert match, f'missing source image: {variable}'
    assert base64.b64decode(match.group(1)) == (museum / 'direct-pilot-assets' / name).read_bytes(), name
print(f'PASS: {len(assets)} pilot images match the embedded Work 02 v1.2 source bytes')
