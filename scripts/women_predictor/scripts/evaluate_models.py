"""Reproduce frozen WASP-style evaluation from saved OOF/test predictions."""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
from typing import Any, Mapping, Optional, Sequence


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path)
    parser.add_argument("--processed-dir", type=Path)
    parser.add_argument("--artifact-dir", type=Path)
    parser.add_argument("--report-dir", type=Path)
    return parser


def _load_json(path: Path) -> Mapping[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    return value if isinstance(value, Mapping) else {}


def _source_sha(manifest: Mapping[str, Any]) -> str:
    return str(
        manifest.get("source_sha256")
        or (manifest.get("source") or {}).get("sha256")
        or ""
    )


def _decorate(frame: Any) -> Any:
    frame = frame.copy()
    frame["legal_over"] = (frame["legal_balls_bowled"].fillna(0).astype(int) // 6).astype(str)
    frame["match_format"] = frame["is_reduced_match"].map(
        lambda value: "reduced" if bool(value) else "full"
    )

    def role(row: Any) -> str:
        if int(row["innings"]) == 1:
            if row["batting_team"] == "Japan":
                return "japan_batting"
            if row["bowling_team"] == "Japan":
                return "japan_bowling"
        if int(row["innings"]) == 2:
            if row["batting_team"] == "Japan":
                return "japan_chasing"
            if row["bowling_team"] == "Japan":
                return "japan_defending"
        return "other"

    frame["japan_role"] = frame.apply(role, axis=1)
    return frame


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _parser().parse_args(argv)
    from cricket_japan_bi.wasp.config import load_wasp_config
    from cricket_japan_bi.wasp.data.storage import validate_processed_dataset

    config = load_wasp_config(args.config)
    args.processed_dir = (args.processed_dir or config.resolve_path("processed_dir")).resolve()
    args.artifact_dir = (args.artifact_dir or config.resolve_path("artifacts_dir")).resolve()
    args.report_dir = (args.report_dir or config.resolve_path("reports_dir")).resolve()
    prepared_manifest = validate_processed_dataset(
        args.processed_dir, expected_config_hash=config.sha256
    )
    try:
        import pandas as pd
    except ImportError as exc:
        raise SystemExit("pandas and PyArrow are required: {}".format(exc))
    from cricket_japan_bi.wasp.evaluation.metrics import (
        first_innings_metrics,
        interval_metrics,
        interval_slice_metrics,
        probability_metrics,
        slice_metrics,
    )
    from cricket_japan_bi.wasp.evaluation.reports import write_report
    from cricket_japan_bi.wasp.features.chronology import EloConfig, build_prematch_features
    from cricket_japan_bi.wasp.features.datasets import attach_prematch_features
    from cricket_japan_bi.wasp.models.contracts import ArtifactBundle

    frozen_dir = args.artifact_dir / "frozen_test"
    bundle = ArtifactBundle.load(frozen_dir if frozen_dir.is_dir() else args.artifact_dir)
    if bundle.manifest.config_sha256 != config.sha256:
        raise SystemExit("artifact config SHA mismatch")
    prepared_sha = _source_sha(prepared_manifest)
    if prepared_sha != bundle.manifest.source_sha256:
        raise SystemExit(
            "source SHA mismatch: processed={} artifact={}".format(
                prepared_sha, bundle.manifest.source_sha256
            )
        )

    ready_path = args.processed_dir / "model_ready_states.parquet"
    if not ready_path.is_file():
        ready_path = args.processed_dir / "model_ready.parquet"
    if ready_path.is_file():
        states_frame = pd.read_parquet(ready_path)
    else:
        states_path = args.processed_dir / "states.parquet"
        matches_path = args.processed_dir / "matches.parquet"
        innings_path = args.processed_dir / "innings.parquet"
        if not all(path.is_file() for path in (states_path, matches_path, innings_path)):
            raise SystemExit("model-ready states and chronology fallback inputs are missing")
        matches = pd.read_parquet(matches_path).to_dict(orient="records")
        innings = pd.read_parquet(innings_path).to_dict(orient="records")
        selected_k = float(bundle.manifest.selected_models.get("elo_k", 24.0))
        chronology = build_prematch_features(
            matches, innings, config=EloConfig(k_factor=selected_k)
        )
        states = attach_prematch_features(
            pd.read_parquet(states_path).to_dict(orient="records"), chronology
        )
        states_frame = pd.DataFrame(states)
    required_features = {
        feature
        for features in bundle.manifest.feature_schema.values()
        for feature in features
    }
    missing = sorted(required_features - set(states_frame.columns))
    if missing:
        raise SystemExit(
            "model-ready feature schema mismatch; missing {}".format(
                ", ".join(missing)
            )
        )
    states_frame = _decorate(states_frame)

    predictions_path = args.processed_dir / "model_predictions_oof.parquet"
    if not predictions_path.is_file():
        report = copy.deepcopy(dict(bundle.evaluation))
        report["verification"] = {
            "status": "stored_frozen_evaluation_only",
            "reason": "model_predictions_oof.parquet is missing",
            "source_sha256": prepared_sha,
        }
    else:
        predictions = pd.read_parquet(predictions_path)
        locked = predictions[predictions["split"] == "locked_test"]
        joined = locked.merge(
            states_frame,
            on=["match_id", "innings", "state_sequence"],
            how="left",
            validate="one_to_one",
        )
        if joined["match_date"].isna().any():
            raise SystemExit("OOF predictions do not match model-ready state keys")
        report = copy.deepcopy(dict(bundle.evaluation))
        verification: dict[str, Any] = {
            "status": "recomputed_from_frozen_predictions",
            "source_sha256": prepared_sha,
        }
        slice_fields = (
            "legal_over",
            "phase_absolute",
            "phase_relative",
            "japan_role",
            "match_format",
        )
        first_frame = joined[joined["task"] == "first_innings"]
        if len(first_frame):
            rows = first_frame.to_dict(orient="records")
            values = [float(value) for value in first_frame["prediction"]]
            first_result: dict[str, Any] = {
                "locked_test": first_innings_metrics(
                    [float(value) for value in first_frame["truth"]],
                    values,
                    list(first_frame["match_id"]),
                ),
                "by_slice": {
                    field: slice_metrics(
                        rows, values, task="first_innings", field=field
                    )
                    for field in slice_fields
                },
            }
            if first_frame["p80_lower"].notna().all():
                intervals = [
                    {
                        "p50": {
                            "lower": float(row["p50_lower"]),
                            "upper": float(row["p50_upper"]),
                        },
                        "p80": {
                            "lower": float(row["p80_lower"]),
                            "upper": float(row["p80_upper"]),
                        },
                    }
                    for row in rows
                ]
                first_result["intervals"] = {
                    "overall": {
                        name: interval_metrics(
                            [float(row["truth"]) for row in rows],
                            [item[name]["lower"] for item in intervals],
                            [item[name]["upper"] for item in intervals],
                            nominal_coverage=coverage,
                        )
                        for name, coverage in (("p50", 0.50), ("p80", 0.80))
                    },
                    "by_slice": {
                        field: interval_slice_metrics(rows, intervals, field=field)
                        for field in slice_fields
                    },
                }
            verification["first_innings"] = first_result
        chase_frame = joined[joined["task"] == "chase"]
        if len(chase_frame):
            rows = chase_frame.to_dict(orient="records")
            values = [float(value) for value in chase_frame["prediction"]]
            verification["chase"] = {
                "locked_test_nonterminal": probability_metrics(
                    [float(value) for value in chase_frame["truth"]],
                    values,
                    list(chase_frame["match_id"]),
                ),
                "by_slice": {
                    field: slice_metrics(rows, values, task="chase", field=field)
                    for field in slice_fields
                },
                "terminal_inclusive": (
                    bundle.evaluation.get("chase", {}).get("terminal_inclusive", {})
                ),
            }
        report["verification"] = verification

    paths = write_report(report, args.report_dir, stem="evaluation")
    print(json.dumps({
        "reports": paths,
        "verification_status": report.get("verification", {}).get("status"),
        "first_locked_test": report.get("first_innings", {}).get("locked_test"),
        "chase_locked_test": report.get("chase", {}).get("locked_test"),
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
