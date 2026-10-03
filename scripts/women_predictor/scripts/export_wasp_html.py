"""Export the trained Japan T20 WASP-style system as one offline HTML file."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Optional, Sequence

from cricket_japan_bi.wasp.standalone import (
    DEFAULT_ARTIFACT_DIR,
    DEFAULT_OUTPUT_PATH,
    DEFAULT_TITLE,
    export_standalone_html,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--artifact-dir",
        type=Path,
        default=DEFAULT_ARTIFACT_DIR,
        help="学習済みbundle.joblibとmanifest.jsonのあるフォルダ",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT_PATH,
        help="出力する単一HTMLファイル",
    )
    parser.add_argument("--title", default=DEFAULT_TITLE, help="HTMLの文書タイトル")
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    destination = export_standalone_html(
        artifact_dir=args.artifact_dir,
        output_path=args.output,
        title=args.title,
    )
    print(
        json.dumps(
            {
                "bytes": destination.stat().st_size,
                "offline": True,
                "output": str(destination),
            },
            ensure_ascii=False,
            sort_keys=True,
        ),
        flush=True,
    )
    return 0


if __name__ == "__main__":  # pragma: no cover - exercised as a CLI
    raise SystemExit(main())
