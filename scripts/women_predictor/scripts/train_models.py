"""Train, select, evaluate and serialize WASP-style models offline."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import platform
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path)
    parser.add_argument("--processed-dir", type=Path)
    parser.add_argument("--artifact-dir", type=Path)
    parser.add_argument("--report-dir", type=Path)
    parser.add_argument("--random-state", type=int)
    return parser


def _load_json(path: Path) -> Mapping[str, Any]:
    if not path.is_file():
        return {}
    value = json.loads(path.read_text(encoding="utf-8"))
    return value if isinstance(value, Mapping) else {}


def _source_sha(manifest: Mapping[str, Any]) -> str:
    direct = manifest.get("source_sha256") or manifest.get("archive_sha256")
    if direct:
        return str(direct)
    source = manifest.get("source")
    if isinstance(source, Mapping) and source.get("sha256"):
        return str(source["sha256"])
    # A missing upstream digest remains visibly unknown; do not invent a hash
    # that could be confused with the archive's SHA-256.
    return ""


def _records(frame: Any) -> List[Mapping[str, Any]]:
    return frame.to_dict(orient="records")


def _selection_score(selection: Any, metric: str) -> float:
    for score in selection.candidates:
        if score.name == selection.selected_name:
            return float(getattr(score, metric))
    return float("inf")


def _first_context_gate(global_selection: Any, context_selection: Any) -> bool:
    global_score = next(
        item for item in global_selection.candidates if item.name == global_selection.selected_name
    )
    context_score = next(
        item for item in context_selection.candidates if item.name == context_selection.selected_name
    )
    if context_score.match_macro_mae >= global_score.match_macro_mae:
        return False
    for phase, base_value in global_score.phase_mae.items():
        compared = context_score.phase_mae.get(phase)
        if compared is not None and base_value > 0 and compared > base_value * 1.05:
            return False
    return True


def _fit_again(model: Any, records: Sequence[Mapping[str, Any]]) -> Any:
    fitted = copy.deepcopy(model)
    if hasattr(fitted, "fit"):
        fitted.fit(records)
    return fitted


def _rolling_predictions(
    template: Any,
    train: Sequence[Mapping[str, Any]],
    validation: Sequence[Mapping[str, Any]],
    *,
    prior_validation: Optional[Sequence[Mapping[str, Any]]] = None,
) -> List[float]:
    predictions: List[Optional[float]] = [None] * len(validation)
    years = sorted(
        {
            int(str(row.get("match_date") or row.get("date") or "0")[:4])
            for row in validation
        }
    )
    for year in years:
        history = validation if prior_validation is None else prior_validation
        fold_train = list(train) + [
            row
            for row in history
            if int(str(row.get("match_date") or row.get("date") or "0")[:4]) < year
        ]
        indices = [
            index
            for index, row in enumerate(validation)
            if int(str(row.get("match_date") or row.get("date") or "0")[:4]) == year
        ]
        model = copy.deepcopy(template)
        if hasattr(model, "calibrator"):
            model.calibrator = None
        model.fit(fold_train)
        for index, value in zip(
            indices, model.predict([validation[item] for item in indices])
        ):
            predictions[index] = float(value)
    if any(value is None for value in predictions):
        raise ValueError("rolling prediction did not cover every validation row")
    return [float(value) for value in predictions if value is not None]


def _correction_metadata(correction: Any) -> Mapping[str, Any]:
    calibrator = getattr(correction, "calibrator", None)
    return {
        "role": correction.role,
        "kind": correction.kind,
        "enabled": bool(correction.enabled),
        "match_count": int(correction.match_count),
        "offset": float(correction.offset),
        "fallback_reason": correction.fallback_reason,
        "ci80": list(correction.ci80),
        "ci95": list(correction.ci95),
        "calibration_slope": (float(calibrator.slope) if calibrator is not None else None),
        "calibration_intercept": (
            float(calibrator.intercept) if calibrator is not None else None
        ),
        "gate_details": dict(correction.gate_details),
    }


def _apply_score_interval_gate(
    corrections: Mapping[str, Any],
    rows: Sequence[Mapping[str, Any]],
    predictions: Sequence[float],
    interval_model: Any,
) -> None:
    from cricket_japan_bi.wasp.models.japan import first_innings_role

    for role in ("japan_batting", "japan_bowling"):
        correction = corrections[role]
        gate_rows: List[Mapping[str, Any]] = []
        base_points: List[float] = []
        for row, prediction in zip(rows, predictions):
            if (
                first_innings_role(row) == role
                and str(row.get("match_date") or row.get("date") or "")[:4]
                == "2025"
            ):
                gate_rows.append(row)
                base_points.append(float(prediction))
        if not gate_rows:
            correction.enabled = False
            correction.fallback_reason = "interval_gate_unavailable"
            correction.gate_details = {"interval_gate": "no_2025_rows"}
            continue
        corrected_points = [
            max(float(row.get("runs_so_far") or 0), float(point) + correction.offset)
            for row, point in zip(gate_rows, base_points)
        ]
        base_intervals = interval_model.predict(gate_rows, base_points)
        corrected_intervals = interval_model.predict(gate_rows, corrected_points)
        weights = [float(row.get("sample_weight") or 1.0) for row in gate_rows]
        total_weight = sum(weights)

        def coverage(intervals: Sequence[Mapping[str, Any]]) -> float:
            covered = 0.0
            for row, item, weight in zip(gate_rows, intervals, weights):
                truth = float(row["final_score"])
                covered += weight * float(
                    item["p80"]["lower"] <= truth <= item["p80"]["upper"]
                )
            return covered / total_weight if total_weight else 0.0

        base_coverage = coverage(base_intervals)
        corrected_coverage = coverage(corrected_intervals)
        coverage_ok = abs(corrected_coverage - 0.80) <= abs(base_coverage - 0.80) + 0.05
        correction.gate_details = {
            **dict(correction.gate_details),
            "base_80_coverage": base_coverage,
            "corrected_80_coverage": corrected_coverage,
            "coverage_error_guard_passed": coverage_ok,
        }
        if correction.enabled and not coverage_ok:
            correction.enabled = False
            correction.fallback_reason = "interval_coverage_gate_failed"


def _decorate_slices(rows: Sequence[Mapping[str, Any]]) -> List[Mapping[str, Any]]:
    decorated: List[Mapping[str, Any]] = []
    for source in rows:
        row = dict(source)
        row["legal_over"] = str(int(row.get("legal_balls_bowled") or 0) // 6)
        row["match_format"] = "reduced" if bool(row.get("is_reduced_match")) else "full"
        innings = int(row.get("innings") or 0)
        if innings == 1:
            if str(row.get("batting_team") or "") == "Japan":
                row["japan_role"] = "japan_batting"
            elif str(row.get("bowling_team") or "") == "Japan":
                row["japan_role"] = "japan_bowling"
            else:
                row["japan_role"] = "other"
        elif innings == 2:
            if str(row.get("batting_team") or "") == "Japan":
                row["japan_role"] = "japan_chasing"
            elif str(row.get("bowling_team") or "") == "Japan":
                row["japan_role"] = "japan_defending"
            else:
                row["japan_role"] = "other"
        decorated.append(row)
    return decorated


def _selection_report(selection: Any, gate_passed: bool, gate_reason: str) -> Mapping[str, Any]:
    return {
        "selected": selection.selected_name,
        "feature_set": selection.feature_set,
        "selection_rule": gate_reason,
        "model_1_gate_passed": gate_passed,
        "candidates": [item.__dict__ for item in selection.candidates],
    }


def _terminal_probability(status: Any) -> Optional[float]:
    normalized = str(status or "").strip().casefold()
    if normalized in {"won", "chase_won", "target_reached"}:
        return 1.0
    if normalized in {"lost", "chase_lost", "all_out", "quota_reached"}:
        return 0.0
    return None


def _predict_chase_with_terminals(model: Any, rows: Sequence[Mapping[str, Any]]) -> List[Optional[float]]:
    values = list(model.predict(rows))
    result: List[Optional[float]] = []
    for row, value in zip(rows, values):
        if str(row.get("terminal_status") or "").casefold() == "tied_regulation":
            result.append(None)
            continue
        terminal = _terminal_probability(row.get("terminal_status"))
        result.append(terminal if terminal is not None else float(value))
    return result


def _build_compact_replays(
    states: Sequence[Mapping[str, Any]],
    *,
    first_model: Any,
    chase_model: Any,
    interval_model: Any,
    corrections: Mapping[str, Any],
    batch_size: int = 20_000,
) -> Mapping[str, Any]:
    from cricket_japan_bi.wasp.models.japan import chase_role, first_innings_role

    replays: Dict[str, Dict[str, Any]] = {}
    first_rows = [row for row in states if int(row.get("innings") or 0) == 1]
    for start in range(0, len(first_rows), batch_size):
        batch = first_rows[start : start + batch_size]
        points = list(first_model.predict(batch))
        selected: List[float] = []
        for row, point in zip(batch, points):
            correction = corrections.get(first_innings_role(row))
            selected.append(
                float(correction.apply(point))
                if correction is not None and correction.enabled
                else float(point)
            )
        intervals = interval_model.predict(batch, selected)
        for row, point, bounds in zip(batch, selected, intervals):
            match_id = str(row.get("match_id") or "")
            replay = replays.setdefault(
                match_id,
                {"match_id": match_id, "first_innings": [], "chase": []},
            )
            replay["first_innings"].append(
                {
                    "state_sequence": int(row.get("state_sequence") or 0),
                    "legal_balls_bowled": int(row.get("legal_balls_bowled") or 0),
                    "runs_so_far": int(row.get("runs_so_far") or 0),
                    "wickets_lost": int(row.get("wickets_lost") or 0),
                    "event": row.get("previous_event") or row.get("previous_event_type"),
                    "selected": point,
                    "p50": bounds["p50"],
                    "p80": bounds["p80"],
                }
            )
    chase_rows = [row for row in states if int(row.get("innings") or 0) == 2]
    for start in range(0, len(chase_rows), batch_size):
        batch = chase_rows[start : start + batch_size]
        eligible_indices = [
            index
            for index, row in enumerate(batch)
            if (bool(row.get("chase_eligible")) or bool(row.get("reduced_match_eligible")))
            and str(row.get("terminal_status") or "").casefold() != "tied_regulation"
        ]
        probabilities: List[Optional[float]] = [None] * len(batch)
        if eligible_indices:
            eligible_rows = [batch[index] for index in eligible_indices]
            values = _predict_chase_with_terminals(chase_model, eligible_rows)
            for index, row, value in zip(eligible_indices, eligible_rows, values):
                correction = corrections.get(chase_role(row))
                probabilities[index] = (
                    correction.apply(value)
                    if value is not None and correction is not None and correction.enabled
                    else value
                )
        for row, probability in zip(batch, probabilities):
            match_id = str(row.get("match_id") or "")
            replay = replays.setdefault(
                match_id,
                {"match_id": match_id, "first_innings": [], "chase": []},
            )
            replay["chase"].append(
                {
                    "state_sequence": int(row.get("state_sequence") or 0),
                    "legal_balls_bowled": int(row.get("legal_balls_bowled") or 0),
                    "runs_so_far": int(row.get("runs_so_far") or 0),
                    "wickets_lost": int(row.get("wickets_lost") or 0),
                    "event": row.get("previous_event") or row.get("previous_event_type"),
                    "selected": probability,
                    "terminal_status": row.get("terminal_status"),
                    "experimental_reduced": bool(row.get("is_reduced_match")),
                }
            )
    return replays


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _parser().parse_args(argv)
    from cricket_japan_bi.wasp.config import load_wasp_config
    from cricket_japan_bi.wasp.data.storage import validate_processed_dataset

    config = load_wasp_config(args.config)
    args.processed_dir = (args.processed_dir or config.resolve_path("processed_dir")).resolve()
    args.artifact_dir = (args.artifact_dir or config.resolve_path("artifacts_dir")).resolve()
    args.report_dir = (args.report_dir or config.resolve_path("reports_dir")).resolve()
    args.random_state = args.random_state if args.random_state is not None else config.random_seed
    manifest_input = validate_processed_dataset(
        args.processed_dir, expected_config_hash=config.sha256
    )
    try:
        import numpy as np
        import pandas as pd
    except ImportError as exc:
        raise SystemExit("pandas, NumPy and PyArrow are required to train models: {}".format(exc))

    from cricket_japan_bi.wasp.evaluation.metrics import (
        first_innings_metrics,
        interval_metrics,
        interval_slice_metrics,
        probability_metrics,
        slice_metrics,
    )
    from cricket_japan_bi.wasp.evaluation.reports import write_report
    from cricket_japan_bi.wasp.features.chronology import (
        EloConfig,
        build_latest_context,
        select_elo_k,
    )
    from cricket_japan_bi.wasp.features.datasets import (
        build_chase_dataset,
        build_first_innings_dataset,
        feature_names,
    )
    from cricket_japan_bi.wasp.models.chase import train_chase_candidates
    from cricket_japan_bi.wasp.models.contracts import ArtifactBundle, ArtifactManifest
    from cricket_japan_bi.wasp.models.first_innings import train_first_innings_candidates
    from cricket_japan_bi.wasp.models.intervals import (
        QuantileConformalIntervalModel,
        train_rolling_quantile_intervals,
    )
    from cricket_japan_bi.wasp.models.japan import (
        fit_chase_correction,
        fit_score_correction,
    )

    states_path = args.processed_dir / "model_ready_states.parquet"
    matches_path = args.processed_dir / "matches.parquet"
    if not states_path.is_file() or not matches_path.is_file():
        raise SystemExit(
            "run python -m scripts.prepare_data first; model-ready states or matches are missing"
        )
    states_frame = pd.read_parquet(states_path)
    matches_frame = pd.read_parquet(matches_path)
    states = _records(states_frame)
    matches = _records(matches_frame)

    # Preserve scope-specific exclusion reasons for retrospective Replay.
    # This annotation does not enter model features or candidate selection.
    exclusions_path = args.processed_dir / "exclusions.parquet"
    if exclusions_path.is_file():
        exclusions_by_match: Dict[str, List[Mapping[str, Any]]] = {}
        for item in _records(pd.read_parquet(exclusions_path)):
            exclusions_by_match.setdefault(str(item["match_id"]), []).append(
                {key: item.get(key) for key in ("model_scope", "reason", "detail")}
            )
        for match in matches:
            match["model_exclusions"] = exclusions_by_match.get(str(match["match_id"]), [])

    innings_path = args.processed_dir / "innings.parquet"
    innings = _records(pd.read_parquet(innings_path)) if innings_path.is_file() else []
    elo_selection = select_elo_k(matches)
    prepared_elo_k = float(
        (manifest_input.get("chronology") or {}).get("selected_elo_k", float("nan"))
    )
    if prepared_elo_k != elo_selection.selected_k:
        raise SystemExit(
            "processed chronology Elo K mismatch: manifest={} selected={}".format(
                prepared_elo_k, elo_selection.selected_k
            )
        )
    chronology_config = EloConfig(k_factor=elo_selection.selected_k)
    match_metadata = {str(row.get("match_id") or ""): row for row in matches}
    enriched_states: List[Mapping[str, Any]] = []
    for source in states:
        row = dict(source)
        metadata = match_metadata.get(str(row.get("match_id") or ""), {})
        row["method"] = metadata.get("method")
        row["reduced_match_eligible"] = metadata.get("reduced_match_eligible", False)
        enriched_states.append(row)
    states = enriched_states
    states = _decorate_slices(states)
    latest_context = build_latest_context(
        matches, innings, config=chronology_config
    )

    first = build_first_innings_dataset(states)
    chase = build_chase_dataset(states)
    chase_inclusive = build_chase_dataset(states, include_terminal=True)
    first_train = [row for row in first if str(row.get("split")) == "train"]
    first_validation = [row for row in first if str(row.get("split")) == "validation"]
    first_test = [row for row in first if str(row.get("split")) == "test"]
    chase_train = [row for row in chase if str(row.get("split")) == "train"]
    chase_validation = [row for row in chase if str(row.get("split")) == "validation"]
    chase_test = [row for row in chase if str(row.get("split")) == "test"]
    first_reduced = [
        row
        for row in build_first_innings_dataset(
            states, include_reduced=True, eligible_only=False
        )
        if bool(row.get("is_reduced_match"))
        and bool(row.get("reduced_match_eligible"))
    ]
    chase_reduced = [
        row
        for row in build_chase_dataset(
            states,
            include_reduced=True,
            eligible_only=False,
            include_terminal=False,
        )
        if bool(row.get("is_reduced_match"))
        and bool(row.get("reduced_match_eligible"))
    ]
    if not all((first_train, first_validation, chase_train, chase_validation)):
        raise SystemExit("fixed train/validation cohorts are empty; inspect processed split flags")

    print("[train] first innings: state-only candidates", flush=True)
    first_global = train_first_innings_candidates(
        first_train, first_validation, context=False, random_state=args.random_state
    )
    print("[train] first innings: female context candidates", flush=True)
    first_context = train_first_innings_candidates(
        first_train, first_validation, context=True, random_state=args.random_state
    )
    use_first_context = _first_context_gate(first_global, first_context)
    first_team_model = first_context.model if use_first_context else first_global.model
    first_team_name = first_context.selected_name if use_first_context else first_global.selected_name
    first_validation_oof = list(
        first_context.validation_predictions
        if use_first_context
        else first_global.validation_predictions
    )

    print("[train] chase: state-only candidates", flush=True)
    chase_global = train_chase_candidates(
        chase_train, chase_validation, context=False, random_state=args.random_state
    )
    print("[train] chase: female context candidates", flush=True)
    chase_context = train_chase_candidates(
        chase_train, chase_validation, context=True, random_state=args.random_state
    )
    use_chase_context = (
        _selection_score(chase_context, "match_macro_brier")
        < _selection_score(chase_global, "match_macro_brier")
        and _selection_score(chase_context, "match_macro_log_loss")
        <= _selection_score(chase_global, "match_macro_log_loss") * 1.01
        and _selection_score(chase_context, "ece")
        <= _selection_score(chase_global, "ece") + 0.02
    )
    chase_team_model = chase_context.model if use_chase_context else chase_global.model
    chase_team_name = chase_context.selected_name if use_chase_context else chase_global.selected_name
    chase_validation_oof = list(
        chase_context.validation_predictions
        if use_chase_context
        else chase_global.validation_predictions
    )

    reduced_development_matches = {
        str(row.get("match_id") or "")
        for row in first_reduced + chase_reduced
        if str(row.get("split")) in {"train", "validation"}
    }
    first_reduced_train = [row for row in first_reduced if str(row.get("split")) == "train"]
    first_reduced_validation = [
        row for row in first_reduced if str(row.get("split")) == "validation"
    ]
    chase_reduced_train = [row for row in chase_reduced if str(row.get("split")) == "train"]
    chase_reduced_validation = [
        row for row in chase_reduced if str(row.get("split")) == "validation"
    ]
    reduced_gate: Dict[str, Any] = {
        "development_matches": len(reduced_development_matches),
        "minimum_matches": 50,
        "enabled": False,
        "reason": "insufficient_development_matches",
    }
    reduced_first_selection = None
    reduced_chase_selection = None
    if (
        len(reduced_development_matches) >= 50
        and first_reduced_train
        and first_reduced_validation
        and chase_reduced_train
        and chase_reduced_validation
    ):
        reduced_first_selection = train_first_innings_candidates(
            first_train + first_reduced_train,
            first_validation + first_reduced_validation,
            context=use_first_context,
            random_state=args.random_state,
        )
        reduced_chase_selection = train_chase_candidates(
            chase_train + chase_reduced_train,
            chase_validation + chase_reduced_validation,
            context=use_chase_context,
            random_state=args.random_state,
        )
        combined_first_oof = list(reduced_first_selection.validation_predictions)
        combined_chase_oof = list(reduced_chase_selection.validation_predictions)
        combined_first_full = combined_first_oof[: len(first_validation)]
        combined_first_reduced = combined_first_oof[len(first_validation) :]
        combined_chase_full = combined_chase_oof[: len(chase_validation)]
        combined_chase_reduced = combined_chase_oof[len(chase_validation) :]
        baseline_first_reduced = _rolling_predictions(
            first_team_model,
            first_train,
            first_reduced_validation,
            prior_validation=first_validation,
        )
        baseline_chase_reduced = _rolling_predictions(
            chase_team_model,
            chase_train,
            chase_reduced_validation,
            prior_validation=chase_validation,
        )
        first_full_base = first_innings_metrics(
            [float(row["final_score"]) for row in first_validation],
            first_validation_oof,
            [row["match_id"] for row in first_validation],
        )["match_macro_mae"]
        first_full_combined = first_innings_metrics(
            [float(row["final_score"]) for row in first_validation],
            combined_first_full,
            [row["match_id"] for row in first_validation],
        )["match_macro_mae"]
        first_reduced_base = first_innings_metrics(
            [float(row["final_score"]) for row in first_reduced_validation],
            baseline_first_reduced,
            [row["match_id"] for row in first_reduced_validation],
        )["match_macro_mae"]
        first_reduced_combined = first_innings_metrics(
            [float(row["final_score"]) for row in first_reduced_validation],
            combined_first_reduced,
            [row["match_id"] for row in first_reduced_validation],
        )["match_macro_mae"]
        chase_full_base = probability_metrics(
            [float(row["chase_won"]) for row in chase_validation],
            chase_validation_oof,
            [row["match_id"] for row in chase_validation],
        )["match_macro_brier"]
        chase_full_combined = probability_metrics(
            [float(row["chase_won"]) for row in chase_validation],
            combined_chase_full,
            [row["match_id"] for row in chase_validation],
        )["match_macro_brier"]
        chase_reduced_base = probability_metrics(
            [float(row["chase_won"]) for row in chase_reduced_validation],
            baseline_chase_reduced,
            [row["match_id"] for row in chase_reduced_validation],
        )["match_macro_brier"]
        chase_reduced_combined = probability_metrics(
            [float(row["chase_won"]) for row in chase_reduced_validation],
            combined_chase_reduced,
            [row["match_id"] for row in chase_reduced_validation],
        )["match_macro_brier"]
        first_pass = (
            first_full_combined <= first_full_base * 1.01
            and first_reduced_combined < first_reduced_base
        )
        chase_pass = (
            chase_full_combined <= chase_full_base * 1.01
            and chase_reduced_combined < chase_reduced_base
        )
        reduced_gate.update(
            {
                "enabled": bool(first_pass and chase_pass),
                "reason": (
                    "passed" if first_pass and chase_pass else "validation_gate_failed"
                ),
                "first_innings": {
                    "full_base_mae": first_full_base,
                    "full_combined_mae": first_full_combined,
                    "reduced_base_mae": first_reduced_base,
                    "reduced_combined_mae": first_reduced_combined,
                    "passed": first_pass,
                },
                "chase": {
                    "full_base_brier": chase_full_base,
                    "full_combined_brier": chase_full_combined,
                    "reduced_base_brier": chase_reduced_base,
                    "reduced_combined_brier": chase_reduced_combined,
                    "passed": chase_pass,
                },
            }
        )
    elif len(reduced_development_matches) >= 50:
        missing_cohorts = []
        if not first_reduced_train or not first_reduced_validation:
            missing_cohorts.append("first_innings_reduced_cohort")
        if not chase_reduced_train or not chase_reduced_validation:
            missing_cohorts.append("chase_reduced_cohort")
        reduced_gate["reason"] = "insufficient_{}".format(
            "_and_".join(missing_cohorts) or "reduced_cohort"
        )

    interval_features = feature_names(
        "first_innings", context=use_first_context
    )
    reduced_enabled = bool(reduced_gate["enabled"])
    if reduced_enabled:
        first_team_model = reduced_first_selection.model
        chase_team_model = reduced_chase_selection.model
        first_team_name = reduced_first_selection.selected_name
        chase_team_name = reduced_chase_selection.selected_name
        first_validation_oof = combined_first_full
        chase_validation_oof = combined_chase_full
    interval_train = first_train + first_reduced_train if reduced_enabled else first_train
    interval_validation = (
        first_validation + first_reduced_validation
        if reduced_enabled
        else first_validation
    )
    print("[train] rolling quantile intervals", flush=True)
    interval_model = train_rolling_quantile_intervals(
        interval_train,
        interval_validation,
        features=interval_features,
        random_state=args.random_state,
    )

    # Japan corrections see only out-of-time states: validation (2023-24) is
    # predicted by train-only models, and the 2025 gate remains pre-refit.
    correction_first_rows = first_validation + [
        row for row in first_test if str(row.get("match_date") or "")[:4] == "2025"
    ]
    correction_first_predictions = first_validation_oof + list(
        first_team_model.predict(correction_first_rows[len(first_validation) :])
    )
    correction_chase_rows = chase_validation + [
        row for row in chase_test if str(row.get("match_date") or "")[:4] == "2025"
    ]
    correction_chase_predictions = chase_validation_oof + list(
        chase_team_model.predict(correction_chase_rows[len(chase_validation) :])
    )
    print("[train] Japan women correction gates", flush=True)
    corrections = {
        role: fit_score_correction(
            correction_first_rows,
            correction_first_predictions,
            role=role,
            random_state=args.random_state,
        )
        for role in ("japan_batting", "japan_bowling")
    }
    corrections.update(
        {
            role: fit_chase_correction(
                correction_chase_rows,
                correction_chase_predictions,
                role=role,
                random_state=args.random_state,
            )
            for role in ("japan_chasing", "japan_defending")
        }
    )
    _apply_score_interval_gate(
        corrections,
        correction_first_rows,
        correction_first_predictions,
        interval_model,
    )

    japan_audit_2026: Dict[str, Any] = {}
    first_2026 = [
        row
        for row in first_test
        if str(row.get("match_date") or "")[:4] == "2026"
    ]
    if first_2026:
        from cricket_japan_bi.wasp.models.japan import first_innings_role

        base_values = list(first_team_model.predict(first_2026))
        for role in ("japan_batting", "japan_bowling"):
            selected = [
                (row, value)
                for row, value in zip(first_2026, base_values)
                if first_innings_role(row) == role
            ]
            if not selected:
                continue
            role_rows = [item[0] for item in selected]
            role_base = [float(item[1]) for item in selected]
            role_corrected = [
                max(0.0, value + corrections[role].offset) for value in role_base
            ]
            japan_audit_2026[role] = {
                "base": first_innings_metrics(
                    [float(row["final_score"]) for row in role_rows],
                    role_base,
                    [row["match_id"] for row in role_rows],
                ),
                "corrected": first_innings_metrics(
                    [float(row["final_score"]) for row in role_rows],
                    role_corrected,
                    [row["match_id"] for row in role_rows],
                ),
                "correction_enabled": corrections[role].enabled,
            }
    chase_2026 = [
        row
        for row in chase_test
        if str(row.get("match_date") or "")[:4] == "2026"
    ]
    if chase_2026:
        from cricket_japan_bi.wasp.models.japan import chase_role

        base_values = list(chase_team_model.predict(chase_2026))
        for role in ("japan_chasing", "japan_defending"):
            selected = [
                (row, value)
                for row, value in zip(chase_2026, base_values)
                if chase_role(row) == role
            ]
            if not selected:
                continue
            role_rows = [item[0] for item in selected]
            role_base = [float(item[1]) for item in selected]
            role_corrected = (
                corrections[role].calibrator.predict(role_base)
                if corrections[role].calibrator is not None
                else role_base
            )
            japan_audit_2026[role] = {
                "base": probability_metrics(
                    [float(row["chase_won"]) for row in role_rows],
                    role_base,
                    [row["match_id"] for row in role_rows],
                ),
                "corrected": probability_metrics(
                    [float(row["chase_won"]) for row in role_rows],
                    role_corrected,
                    [row["match_id"] for row in role_rows],
                ),
                "correction_enabled": corrections[role].enabled,
            }

    evaluation: Dict[str, Any] = {
        "chronology": {
            "selected_elo_k": elo_selection.selected_k,
            "validation_brier_by_k": dict(elo_selection.validation_brier),
            "evaluated_matches": elo_selection.evaluated_matches,
            "selection_rule": "minimum 2023-24 pre-match Brier; locked test unused",
        },
        "reduced_match_gate": reduced_gate,
        "japan_audit_2026": japan_audit_2026,
    }
    slice_fields = ("legal_over", "phase_absolute", "phase_relative", "japan_role", "match_format")
    print("[train] frozen locked-test evaluation", flush=True)
    first_test_predictions: List[float] = []
    first_test_intervals: List[Mapping[str, Any]] = []
    chase_test_predictions: List[float] = []
    if first_test:
        first_test_predictions = list(first_team_model.predict(first_test))
        first_test_intervals = interval_model.predict(first_test, first_test_predictions)
        interval_overall: Dict[str, Any] = {}
        for interval_name, coverage in (("p50", 0.50), ("p80", 0.80)):
            interval_overall[interval_name] = interval_metrics(
                [float(row["final_score"]) for row in first_test],
                [item[interval_name]["lower"] for item in first_test_intervals],
                [item[interval_name]["upper"] for item in first_test_intervals],
                nominal_coverage=coverage,
            )
        evaluation["first_innings"] = {
            "locked_test": first_innings_metrics(
                [float(row["final_score"]) for row in first_test],
                first_test_predictions,
                [row["match_id"] for row in first_test],
            ),
            "intervals": {
                "overall": interval_overall,
                "by_slice": {
                    field: interval_slice_metrics(
                        first_test, first_test_intervals, field=field
                    )
                    for field in slice_fields
                },
            },
            "by_slice": {
                field: slice_metrics(
                    first_test,
                    first_test_predictions,
                    task="first_innings",
                    field=field,
                )
                for field in slice_fields
            },
            "selection_model_0": _selection_report(
                first_global, True, "rolling-origin match-macro MAE with 1% simplicity rule"
            ),
            "selection_model_1": _selection_report(
                first_context,
                use_first_context,
                "Model 1 must improve MAE and avoid >5% phase degradation",
            ),
            "selected": first_team_name,
        }
    if chase_test:
        chase_test_predictions = list(chase_team_model.predict(chase_test))
        chase_inclusive_test = [
            row for row in chase_inclusive if str(row.get("split")) == "test"
        ]
        inclusive_probabilities = _predict_chase_with_terminals(
            chase_team_model, chase_inclusive_test
        )
        inclusive_rows_and_values = [
            (row, value)
            for row, value in zip(chase_inclusive_test, inclusive_probabilities)
            if value is not None
        ]
        evaluation["chase"] = {
            "locked_test": probability_metrics(
                [float(row["chase_won"]) for row in chase_test],
                chase_test_predictions,
                [row["match_id"] for row in chase_test],
            ),
            "terminal_inclusive": probability_metrics(
                [float(row["chase_won"]) for row, _ in inclusive_rows_and_values],
                [float(value) for _, value in inclusive_rows_and_values],
                [row["match_id"] for row, _ in inclusive_rows_and_values],
            ),
            "by_slice": {
                field: slice_metrics(
                    chase_test, chase_test_predictions, task="chase", field=field
                )
                for field in slice_fields
            },
            "selection_model_0": _selection_report(
                chase_global,
                True,
                "rolling-origin match-macro Brier with log-loss/ECE guards",
            ),
            "selection_model_1": _selection_report(
                chase_context,
                use_chase_context,
                "Model 1 must improve rolling-origin match-macro Brier",
            ),
            "selected": chase_team_name,
        }

    first_reduced_test = [
        row
        for row in build_first_innings_dataset(
            states, include_reduced=True, eligible_only=False
        )
        if str(row.get("split")) == "test"
        and bool(row.get("is_reduced_match"))
        and str(row.get("method") or "").casefold() not in {"d/l", "dls"}
    ]
    if first_reduced_test:
        reduced_prediction_model = (
            reduced_first_selection.model
            if reduced_enabled and reduced_first_selection is not None
            else first_team_model
        )
        reduced_predictions = reduced_prediction_model.predict(first_reduced_test)
        evaluation["first_innings"]["experimental_reduced"] = first_innings_metrics(
            [float(row["final_score"]) for row in first_reduced_test],
            reduced_predictions,
            [row["match_id"] for row in first_reduced_test],
        )
    chase_reduced_test = [
        row
        for row in build_chase_dataset(
            states,
            include_reduced=True,
            eligible_only=False,
            include_terminal=False,
        )
        if str(row.get("split")) == "test"
        and bool(row.get("is_reduced_match"))
        and bool(row.get("reduced_match_eligible"))
    ]
    if chase_reduced_test:
        reduced_probability_model = (
            reduced_chase_selection.model
            if reduced_enabled and reduced_chase_selection is not None
            else chase_team_model
        )
        reduced_probabilities = reduced_probability_model.predict(chase_reduced_test)
        evaluation["chase"]["experimental_reduced"] = probability_metrics(
            [float(row["chase_won"]) for row in chase_reduced_test],
            reduced_probabilities,
            [row["match_id"] for row in chase_reduced_test],
        )

    # Freeze evaluation above, then refit the selected production structures to
    # all data available at the source cutoff.
    production_first_records = first + first_reduced if reduced_enabled else first
    production_chase_records = chase + chase_reduced if reduced_enabled else chase
    first_production_template = (
        reduced_first_selection.model
        if reduced_enabled and reduced_first_selection is not None
        else first_team_model
    )
    chase_production_template = (
        reduced_chase_selection.model
        if reduced_enabled and reduced_chase_selection is not None
        else chase_team_model
    )
    print("[train] production refit across full female history", flush=True)
    production_first_global = _fit_again(first_global.model, production_first_records)
    production_first_team = _fit_again(first_production_template, production_first_records)
    production_chase_global = _fit_again(chase_global.model, production_chase_records)
    production_chase_team = _fit_again(chase_production_template, production_chase_records)
    production_interval_model = QuantileConformalIntervalModel(
        interval_features, random_state=args.random_state
    ).fit(production_first_records)
    production_interval_model.correction_50 = interval_model.correction_50
    production_interval_model.correction_80 = interval_model.correction_80
    source_cutoff = max((str(row.get("match_date") or row.get("date") or "") for row in matches), default=None)
    config_sha = config.sha256
    try:
        import sklearn

        sklearn_version = sklearn.__version__
    except ImportError:
        sklearn_version = "not-installed"
    selected_models = {
        "first_innings_global": first_global.selected_name,
        "first_innings_team": (
            reduced_first_selection.selected_name
            if reduced_enabled and reduced_first_selection is not None
            else first_team_name
        ),
        "chase_global": chase_global.selected_name,
        "chase_team": (
            reduced_chase_selection.selected_name
            if reduced_enabled and reduced_chase_selection is not None
            else chase_team_name
        ),
        "elo_k": "{:g}".format(elo_selection.selected_k),
    }
    artifact_manifest = ArtifactManifest(
        source_sha256=_source_sha(manifest_input),
        config_sha256=config_sha,
        source_cutoff=source_cutoff,
        split={
            "train": "<=2022-12-31",
            "validation": "2023-01-01..2024-12-31",
            "test": ">=2025-01-01",
        },
        feature_schema={
            "first_innings_model_0": feature_names("first_innings", context=False),
            "first_innings_model_1": feature_names("first_innings", context=True),
            "chase_model_0": feature_names("chase", context=False),
            "chase_model_1": feature_names("chase", context=True),
        },
        selected_models=selected_models,
        reduced_match_enabled=reduced_enabled,
        library_versions={
            "python": platform.python_version(),
            "numpy": np.__version__,
            "pandas": pd.__version__,
            "scikit_learn": sklearn_version,
        },
        run_parameters={
            "random_state": args.random_state,
            "config_path": str(config.path),
            "effective_config_sha256": config.canonical_values_sha256(),
        },
        japan_gates={key: _correction_metadata(value) for key, value in corrections.items()},
        metrics={
            "evaluation": evaluation,
            "data": {
                "row_counts": dict(manifest_input.get("row_counts") or {}),
                "exclusion_counts": dict(
                    manifest_input.get("exclusion_counts") or {}
                ),
                "audit_counts": dict(
                    (manifest_input.get("audit") or {}).get("counts") or {}
                ),
            },
        },
        limitations=(
            "WASP-style estimate; not an official WASP reproduction",
            "D/L and DLS matches are unsupported in v1",
            "Japan correction falls back role-by-role when its activation gate fails",
        ),
    )
    known_teams = sorted(
        {
            str(value)
            for row in matches
            for value in (
                [row.get("team_1"), row.get("team_2")]
                + list(row.get("teams") or [])
            )
            if value
        }
    )
    known_venues = sorted({str(row.get("venue")) for row in matches if row.get("venue")})
    print("[train] retrospective replays and artifact serialization", flush=True)
    replays = _build_compact_replays(
        states,
        first_model=production_first_team,
        chase_model=production_chase_team,
        interval_model=production_interval_model,
        corrections=corrections,
    )
    frozen_manifest = copy.deepcopy(artifact_manifest)
    frozen_manifest.bundle_role = "frozen_test"
    frozen_manifest.bundle_sha256 = ""
    frozen_bundle = ArtifactBundle(
        manifest=frozen_manifest,
        first_innings_global=first_global.model,
        first_innings_team=first_production_template,
        chase_global=chase_global.model,
        chase_team=chase_production_template,
        interval_model=interval_model,
        japan_corrections=corrections,
        known_teams=known_teams,
        known_venues=known_venues,
        latest_team_context=latest_context.get("teams", {}),
        latest_venue_context=latest_context.get("venues", {}),
        global_context=latest_context.get("global", {}),
        matches=matches,
        evaluation=evaluation,
    )
    frozen_bundle.save(args.artifact_dir / "frozen_test")
    bundle = ArtifactBundle(
        manifest=artifact_manifest,
        first_innings_global=production_first_global,
        first_innings_team=production_first_team,
        chase_global=production_chase_global,
        chase_team=production_chase_team,
        interval_model=production_interval_model,
        japan_corrections=corrections,
        known_teams=known_teams,
        known_venues=known_venues,
        latest_team_context=latest_context.get("teams", {}),
        latest_venue_context=latest_context.get("venues", {}),
        global_context=latest_context.get("global", {}),
        matches=matches,
        replays=replays,
        evaluation=evaluation,
    )
    bundle.save(args.artifact_dir)
    prediction_rows: List[Mapping[str, Any]] = []
    for row, value in zip(first_validation, first_validation_oof):
        prediction_rows.append(
            {
                "task": "first_innings",
                "split": "validation_oof",
                "match_id": row["match_id"],
                "innings": 1,
                "state_sequence": row.get("state_sequence"),
                "truth": row["final_score"],
                "prediction": value,
                "terminal": bool(row.get("terminal_status")),
            }
        )
    for row, value, bounds in zip(
        first_test, first_test_predictions, first_test_intervals
    ):
        prediction_rows.append(
            {
                "task": "first_innings",
                "split": "locked_test",
                "match_id": row["match_id"],
                "innings": 1,
                "state_sequence": row.get("state_sequence"),
                "truth": row["final_score"],
                "prediction": value,
                "terminal": bool(row.get("terminal_status")),
                "p50_lower": bounds["p50"]["lower"],
                "p50_upper": bounds["p50"]["upper"],
                "p80_lower": bounds["p80"]["lower"],
                "p80_upper": bounds["p80"]["upper"],
            }
        )
    for row, value in zip(chase_validation, chase_validation_oof):
        prediction_rows.append(
            {
                "task": "chase",
                "split": "validation_oof",
                "match_id": row["match_id"],
                "innings": 2,
                "state_sequence": row.get("state_sequence"),
                "truth": row["chase_won"],
                "prediction": value,
                "terminal": False,
            }
        )
    for row, value in zip(chase_test, chase_test_predictions):
        prediction_rows.append(
            {
                "task": "chase",
                "split": "locked_test",
                "match_id": row["match_id"],
                "innings": 2,
                "state_sequence": row.get("state_sequence"),
                "truth": row["chase_won"],
                "prediction": value,
                "terminal": False,
            }
        )
    pd.DataFrame(prediction_rows).to_parquet(
        args.processed_dir / "model_predictions_oof.parquet", index=False
    )
    paths = write_report(evaluation, args.report_dir, stem="evaluation")
    print(
        json.dumps(
            {
                "artifact_dir": str(args.artifact_dir),
                "reports": paths,
                "selected_models": selected_models,
                "first_states": len(first),
                "chase_states": len(chase),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
