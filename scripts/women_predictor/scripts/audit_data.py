"""Audit a Cricsheet CSV2 archive for WASP-style modelling."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Optional, Sequence

from cricket_japan_bi.wasp.data.audit import audit_csv2_archive
from cricket_japan_bi.wasp.config import DEFAULT_CONFIG_PATH, load_wasp_config


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = PROJECT_ROOT / "data" / "raw" / "t20s_female_csv2.zip"
DEFAULT_REPORT_DIR = PROJECT_ROOT / "reports" / "wasp"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Audit the CSV2 source used by the T20 WASP-style system."
    )
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG_PATH)
    parser.add_argument("--source", type=Path)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--expected-sha256")
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    config = load_wasp_config(args.config)
    source = args.source or config.resolve_path("source_zip")
    output_dir = (args.output_dir or config.resolve_path("reports_dir")).expanduser().resolve()
    report = audit_csv2_archive(
        source,
        output_json=output_dir / "data_audit.json",
        output_markdown=output_dir / "data_audit.md",
        expected_sha256=args.expected_sha256 or config.expected_source_sha256,
    )
    print(
        json.dumps(
            {
                "source_sha256": report.source_sha256,
                "matches": report.counts["matches"],
                "deliveries": report.counts["deliveries"],
                "strict_full_chase_cohort": report.counts[
                    "strict_full_chase_cohort"
                ],
                "output_dir": str(output_dir),
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":  # pragma: no cover - exercised as a CLI
    raise SystemExit(main())
