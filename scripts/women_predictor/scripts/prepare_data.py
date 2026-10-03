"""Prepare normalized Parquet and DuckDB data for WASP-style modelling."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Optional, Sequence

from cricket_japan_bi.wasp.data.normalize import prepare_dataset
from cricket_japan_bi.wasp.config import DEFAULT_CONFIG_PATH, load_wasp_config


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = PROJECT_ROOT / "data" / "raw" / "t20s_female_csv2.zip"
DEFAULT_OUTPUT = PROJECT_ROOT / "data" / "processed" / "wasp"
DEFAULT_CONFIG = PROJECT_ROOT / "config" / "wasp.toml"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Normalize audited CSV2 data for the T20 WASP-style system."
    )
    parser.add_argument("--source", type=Path)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG_PATH)
    parser.add_argument("--buffer-size", type=int)
    parser.add_argument("--expected-sha256")
    parser.add_argument(
        "--no-duckdb", action="store_true", help="Write Parquet but skip DuckDB."
    )
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    config = load_wasp_config(args.config)
    manifest = prepare_dataset(
        args.source or config.resolve_path("source_zip"),
        args.output_dir or config.resolve_path("processed_dir"),
        buffer_size=args.buffer_size or config.buffer_rows,
        create_duckdb=not args.no_duckdb,
        config_path=config.path,
        expected_sha256=args.expected_sha256 or config.expected_source_sha256,
    )
    print(
        json.dumps(
            {
                "manifest": manifest["paths"]["manifest"],
                "source_sha256": manifest["source_sha256"],
                "row_counts": manifest["row_counts"],
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":  # pragma: no cover - exercised as a CLI
    raise SystemExit(main())
