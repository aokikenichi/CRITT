#!/usr/bin/env python3
"""Verify all 10 preserved Museum sources from the current checkout, with Git object identity."""
import hashlib, json, pathlib, sys
ROOT = pathlib.Path(__file__).resolve().parents[1]
manifest = json.loads((ROOT / "TEN_EXHIBIT_SOURCE_MAP.json").read_text(encoding="utf-8"))
items = manifest["items"]
errors = []
seen = set()
for row in items:
    ident = row["id"]
    path = ROOT / row["path"]
    if ident in seen or ident not in {f"{i:03}" for i in range(1, 11)}:
        errors.append(f"INVALID ID {ident}")
    seen.add(ident)
    if not path.is_file():
        errors.append(f"MISSING {ident}: {row['path']}")
        print(f"FAIL {ident}: missing {row['path']}")
        continue
    raw = path.read_bytes()
    sha = hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()
    ok = len(raw) == row["size"] and sha == row["git_blob_sha"]
    print(f"{'PASS' if ok else 'FAIL'} {ident}: {row['path']} {len(raw)} bytes")
    if not ok: errors.append(f"MISMATCH {ident}: byte count or Git blob sha")
if seen != {f"{i:03}" for i in range(1, 11)}: errors.append("not exactly 001..010")
print(f"RESULT: {10-len(errors)}/10" if errors else "RESULT: 10/10 PASS")
if errors:
    print("\n".join(errors), file=sys.stderr)
    sys.exit(1)
