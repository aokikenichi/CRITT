"""Rebuild the female-only standalone predictor without touching the men's pipeline.

Example:
    python scripts/build_japan_women_predictor.py --source /path/t20s_female_csv2.zip
"""
from __future__ import annotations

import argparse
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parent / "women_predictor"
OUTPUT = ROOT.parents[1] / "japan-women-t20-predictor.html"
SOURCE_SHA256 = "acb457e9d1337907e901b4aa08a3a8a1962a7b98b216476ca3236d595bb0f4d9"
STAGES = ("audit", "prepare", "train", "evaluate", "export", "verify", "report")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, help="Audited Cricsheet Women's T20I CSV2 ZIP")
    parser.add_argument("--from-stage", choices=STAGES, default="audit")
    parser.add_argument("--through-stage", choices=STAGES, default="report")
    parser.add_argument("--output", type=Path, default=OUTPUT)
    parser.add_argument("--threads", type=int, default=4)
    parser.add_argument("--node", default=os.environ.get("NODE_BINARY") or shutil.which("node"),
                        help="Node.js binary for executable export parity checks")
    args = parser.parse_args()
    if args.threads < 1:
        parser.error("--threads must be positive")
    start, end = STAGES.index(args.from_stage), STAGES.index(args.through_stage)
    if start > end:
        parser.error("--from-stage must precede --through-stage")
    source = ROOT / "data/raw/t20s_female_csv2.zip"
    candidate = (args.source or source).expanduser().resolve()
    if not candidate.is_file():
        parser.error(f"Source ZIP missing: {candidate}; supply --source")
    actual_sha = hashlib.sha256(candidate.read_bytes()).hexdigest()
    if actual_sha != SOURCE_SHA256:
        parser.error(f"Unexpected source SHA-256: {actual_sha}; update the audited config for a new release")
    if candidate != source.resolve():
        source.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(candidate, source)
    environment = dict(os.environ)
    environment["PYTHONPATH"] = str(ROOT / "src")
    environment["PYTHONUNBUFFERED"] = "1"
    for key in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
        environment[key] = str(args.threads)
    commands = {
        "audit": ["-m", "scripts.audit_data", "--config", "config/wasp.toml"],
        "prepare": ["-m", "scripts.prepare_data", "--config", "config/wasp.toml"],
        "train": ["-m", "scripts.train_models", "--config", "config/wasp.toml"],
        "evaluate": ["-m", "scripts.evaluate_models", "--config", "config/wasp.toml"],
        "export": ["-m", "scripts.export_wasp_html", "--artifact-dir", "artifacts/wasp",
                   "--output", str(args.output.resolve()), "--title", "日本女子代表 T20 Predictor | CRITT"],
        "verify": ["verify_results.py", "--html", str(args.output.resolve())],
        "report": ["write_results.py"],
    }
    node = args.node
    bundled_node = Path("/Users/aoki/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node")
    if not node and bundled_node.is_file():
        node = str(bundled_node)
    if node:
        commands["verify"].extend(["--node", node])
    for stage in STAGES[start:end + 1]:
        print(f"[women-predictor] {stage}", flush=True)
        subprocess.run([sys.executable, *commands[stage]], cwd=ROOT, env=environment, check=True)
    print(f"[women-predictor] stages complete through {args.through_stage}: {args.output.resolve()}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
