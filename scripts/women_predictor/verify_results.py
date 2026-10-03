"""Independently verify the women's predictor after training and HTML export.

This command never changes models, input data or HTML. Its only output is
reports/wasp/verification.json. Frozen test predictions are executed again
for every eligible test state and checked against the saved prediction file.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import warnings
from html.parser import HTMLParser
from typing import Any, Mapping


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))


class VerificationError(RuntimeError):
    pass


def digest(path: Path) -> str:
    result = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            result.update(block)
    return result.hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise VerificationError(message)


def close_tree(actual: Any, expected: Any, label: str) -> None:
    """Compare JSON-compatible structures, with tight float tolerance."""
    if isinstance(expected, Mapping):
        require(isinstance(actual, Mapping), f"{label}: mapping missing")
        require(set(actual) == set(expected), f"{label}: mapping keys differ")
        for key, value in expected.items():
            close_tree(actual[key], value, f"{label}.{key}")
    elif isinstance(expected, (list, tuple)):
        require(isinstance(actual, (list, tuple)), f"{label}: sequence missing")
        require(len(actual) == len(expected), f"{label}: sequence lengths differ")
        for index, (left, right) in enumerate(zip(actual, expected)):
            close_tree(left, right, f"{label}[{index}]")
    elif isinstance(expected, (int, float)) and not isinstance(expected, bool):
        require(actual is not None and math.isclose(float(actual), float(expected),
                rel_tol=1e-9, abs_tol=1e-9), f"{label}: {actual!r} != {expected!r}")
    else:
        require(actual == expected, f"{label}: {actual!r} != {expected!r}")


class Document(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.scripts: list[tuple[dict[str, str | None], str]] = []
        self.assets: list[str] = []
        self._attrs: dict[str, str | None] | None = None
        self._text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        if tag == "script":
            self._attrs, self._text = values, []
        if tag in {"script", "link", "img", "iframe", "source", "video", "audio"}:
            source = values.get("src") or (values.get("href") if tag == "link" else None)
            if source and not source.startswith(("data:", "blob:", "#")):
                self.assets.append(source)

    def handle_data(self, data: str) -> None:
        if self._attrs is not None:
            self._text.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "script" and self._attrs is not None:
            self.scripts.append((self._attrs, "".join(self._text)))
            self._attrs, self._text = None, []


def independent_metrics(frame: Any, task: str, prediction: Any) -> dict[str, Any]:
    """Do not call the pipeline's metric functions for this cross-check."""
    import numpy as np
    import pandas as pd

    truth = frame["truth"].to_numpy(dtype=float)
    values = np.asarray(prediction, dtype=float)
    match_ids = frame["match_id"].astype(str).to_numpy()
    result: dict[str, Any] = {"states": len(frame), "matches": len(set(match_ids))}
    if task == "first_innings":
        error = values - truth
        absolute = pd.Series(np.abs(error)).groupby(match_ids).mean()
        squared = pd.Series(error ** 2).groupby(match_ids).mean()
        result.update(mae=float(np.mean(np.abs(error))),
                      rmse=float(np.sqrt(np.mean(error ** 2))),
                      match_macro_mae=float(absolute.mean()),
                      match_macro_rmse=float(np.sqrt(squared).mean()))
    else:
        probability = np.clip(values, 1e-6, 1 - 1e-6)
        brier = (probability - truth) ** 2
        log_loss = -(truth * np.log(probability) + (1 - truth) * np.log(1 - probability))
        order = np.argsort(probability, kind="stable")
        chunks = np.array_split(order, min(10, len(order)))
        ece = sum(len(indices) / len(order) * abs(float(probability[indices].mean())
                  - float(truth[indices].mean())) for indices in chunks if len(indices))
        result.update(brier=float(brier.mean()), log_loss=float(log_loss.mean()),
                      match_macro_brier=float(pd.Series(brier).groupby(match_ids).mean().mean()),
                      match_macro_log_loss=float(pd.Series(log_loss).groupby(match_ids).mean().mean()),
                      ece=float(ece))
    return result


def javascript_parity(bundle: Any, payload: Mapping[str, Any], runtime: str,
                      node_binary: str) -> dict[str, Any]:
    """Run the exported HTML's JavaScript, including edge/fallback cases."""
    from cricket_japan_bi.wasp.models.service import PredictionService
    from cricket_japan_bi.wasp.standalone import verify_prediction_parity

    verify_prediction_parity(bundle, payload["inference"])
    service = PredictionService(bundle)
    opponent = next(team for team in bundle.known_teams if team != "Japan")
    venue = bundle.known_venues[0] if bundle.known_venues else None
    first = {"batting_team": "Japan", "bowling_team": opponent, "runs": 62,
             "wickets": 3, "completed": {"overs": 10, "balls": 0},
             "quota": {"overs": 20, "balls": 0}, "venue": venue,
             "use_japan_correction": True}
    chase = {"chasing_team": "Japan", "defending_team": opponent,
             "toss_winner": "Japan", "target": 130, "current_score": 76,
             "wickets": 4, "balls_remaining": 48,
             "target_ball_limit": {"overs": 20, "balls": 0}, "venue": venue,
             "use_japan_correction": True}
    first_cases = [first, dict(first, runs=0, wickets=0, completed={"overs": 0, "balls": 0}),
                   dict(first, runs=95, completed={"overs": 19, "balls": 5}),
                   dict(first, completed={"overs": 20, "balls": 0}),
                   dict(first, wickets=10), dict(first, batting_team="__UNKNOWN_TEAM__")]
    chase_cases = [chase, dict(chase, toss_winner=opponent), dict(chase, toss_winner=None),
                   dict(chase, current_score=130),
                   dict(chase, current_score=120, balls_remaining=0),
                   dict(chase, current_score=129, balls_remaining=0),
                   dict(chase, wickets=10), dict(chase, chasing_team="__UNKNOWN_TEAM__")]
    cases = [{"task": "first", "input": row} for row in first_cases]
    cases += [{"task": "chase", "input": row} for row in chase_cases]
    program = runtime + "\n" + r'''
const fs = require("node:fs");
const value = JSON.parse(fs.readFileSync(0, "utf8"));
const results = value.cases.map(item => item.task === "first"
  ? globalThis.WASPStandalonePredictor.predictFirst(item.input, value.payload)
  : globalThis.WASPStandalonePredictor.predictChase(item.input, value.payload));
process.stdout.write(JSON.stringify(results));
'''
    output = subprocess.run([node_binary, "-e", program],
                            input=json.dumps({"payload": {"inference": payload["inference"]},
                                              "cases": cases}, allow_nan=False),
                            text=True, capture_output=True, check=True, timeout=30)
    actual = json.loads(output.stdout)
    for index, (case, result) in enumerate(zip(cases, actual)):
        expected = (service.predict_first_innings(case["input"]) if case["task"] == "first"
                    else service.predict_chase(case["input"]))
        # These are the public inference fields; other service metadata is optional.
        fields = ("comparison", "intervals", "correction", "warnings") if case["task"] == "first" \
            else ("comparison", "scenarios", "terminal", "correction", "warnings")
        for field in fields:
            close_tree(result[field], expected[field], f"javascript.case[{index}].{field}")
    return {"status": "passed", "cases": len(cases), "node_binary": node_binary,
            "includes": ["start", "last_ball", "terminal_win", "terminal_loss",
                         "regulation_tie", "unknown_team", "unknown_toss", "known_toss_both_teams"]}


def verify(args: argparse.Namespace, report: dict[str, Any]) -> None:
    import numpy as np
    import pandas as pd
    from cricket_japan_bi.csv2_parser import CSV2RegistryWarning, iter_csv2_match_info
    from cricket_japan_bi.wasp.config import load_wasp_config
    from cricket_japan_bi.wasp.data.storage import validate_processed_dataset
    from cricket_japan_bi.wasp.features.chronology import EloConfig, build_latest_context, build_prematch_features
    from cricket_japan_bi.wasp.models.contracts import ArtifactBundle
    from cricket_japan_bi.wasp.standalone import build_standalone_payload

    config = load_wasp_config(args.config)
    processed = config.resolve_path("processed_dir")
    artifact = config.resolve_path("artifacts_dir")
    source = config.resolve_path("source_zip")
    source_sha = digest(source)
    require(source_sha == config.expected_source_sha256, "female archive SHA does not match config")
    prepared = validate_processed_dataset(processed, expected_config_hash=config.sha256)
    require(prepared["source_sha256"] == source_sha, "processed source SHA mismatch")
    production, frozen = ArtifactBundle.load(artifact), ArtifactBundle.load(artifact / "frozen_test")
    for bundle, role in ((production, "production_refit"), (frozen, "frozen_test")):
        require(bundle.manifest.bundle_role == role, f"incorrect {role} bundle role")
        require(bundle.manifest.source_sha256 == source_sha, f"{role} source SHA mismatch")
        require(bundle.manifest.config_sha256 == config.sha256, f"{role} config SHA mismatch")
        require(bundle.manifest.split == {"train": "<=2022-12-31",
                "validation": "2023-01-01..2024-12-31", "test": ">=2025-01-01"},
                f"{role} split contract changed")
    report["integrity"] = {"source_sha256": source_sha, "config_sha256": config.sha256,
                           "production_bundle_sha256": production.manifest.bundle_sha256,
                           "frozen_bundle_sha256": frozen.manifest.bundle_sha256,
                           "processed_file_hashes_verified": True}

    matches = pd.read_parquet(processed / "matches.parquet")
    matches["match_id"] = matches["match_id"].astype(str)
    require(matches["match_id"].is_unique, "duplicate normalized match IDs")
    for column, value in (("gender", "female"), ("team_type", "international"), ("match_type", "t20")):
        require(matches[column].str.casefold().eq(value).all(), f"normalized cohort contains other {column}")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", CSV2RegistryWarning)
        raw_cohort = {row.match_id for row in iter_csv2_match_info(source)
                      if (row.gender or "").casefold() == "female"
                      and (row.team_type or "").casefold() == "international"
                      and (row.match_type or "").casefold() == "t20"}
    require(set(matches["match_id"]) == raw_cohort, "normalized matches do not cover the complete female T20I archive cohort")
    dates = pd.to_datetime(matches["match_date"])
    expected = np.where(dates <= "2022-12-31", "train", np.where(dates <= "2024-12-31", "validation", "test"))
    require(np.array_equal(matches["split"].to_numpy(), expected), "incorrect chronological match splits")
    require(set(expected) == {"train", "validation", "test"}, "empty temporal cohort")
    match_rows = matches.to_dict(orient="records")
    require({str(row["match_id"]) for row in production.matches} == raw_cohort, "production bundle match cohort mismatch")
    require({str(row["match_id"]) for row in frozen.matches} == raw_cohort, "frozen bundle match cohort mismatch")
    cutoff = dates.max().date().isoformat()
    require(production.manifest.source_cutoff == cutoff, "production source cutoff mismatch")
    japan = matches[matches["team_1"].eq("Japan") | matches["team_2"].eq("Japan")]
    japan_ids = set(japan["match_id"])
    require(len(japan_ids) == args.expected_japan_matches, "unexpected Japan women match count")
    teams = sorted(set(matches["team_1"]) | set(matches["team_2"]))
    require(list(production.known_teams) == teams, "production team options do not match female cohort")
    report["cohort"] = {"gender": "female", "team_type": "international", "match_type": "T20",
                        "matches": len(matches), "japan_matches": len(japan), "date_from": dates.min().date().isoformat(),
                        "date_to": cutoff, "split_matches": matches.groupby("split").size().to_dict()}

    innings = pd.read_parquet(processed / "innings.parquet").to_dict(orient="records")
    chronology_config = EloConfig(k_factor=float(production.manifest.selected_models["elo_k"]))
    latest = build_latest_context(match_rows, innings, config=chronology_config)
    close_tree(production.latest_team_context, latest["teams"], "latest_team_context")
    close_tree(production.latest_venue_context, latest["venues"], "latest_venue_context")
    close_tree(production.global_context, latest["global"], "latest_global_context")
    computed = pd.DataFrame(build_prematch_features(match_rows, innings, config=chronology_config))
    prematch = pd.read_parquet(processed / "prematch_team_features.parquet")
    columns = [column for column in computed if column not in {"match_id", "match_date", "team", "opponent"}]
    joined_context = prematch.merge(computed, on=["match_id", "team"], suffixes=("_saved", "_computed"), validate="one_to_one")
    require(len(joined_context) == len(computed) == len(prematch), "prematch context cohort mismatch")
    for column in columns:
        np.testing.assert_allclose(joined_context[column + "_saved"].to_numpy(dtype=float),
                                   joined_context[column + "_computed"].to_numpy(dtype=float),
                                   rtol=1e-9, atol=1e-9, err_msg=f"prematch female-only {column}")
    report["chronology"] = {"status": "recomputed_from_female_cohort", "prematch_rows": len(prematch),
                            "teams": len(latest["teams"]), "venues": len(latest["venues"]),
                            "selected_elo_k": chronology_config.k_factor}

    predictions = pd.read_parquet(processed / "model_predictions_oof.parquet")
    states = pd.read_parquet(processed / "model_ready_states.parquet")
    for frame in (states, predictions):
        frame["match_id"] = frame["match_id"].astype(str)
    require(set(states["match_id"]) <= raw_cohort, "model-ready states outside female cohort")
    split_lookup = matches.set_index("match_id")["split"]
    require(states["split"].eq(states["match_id"].map(split_lookup)).all(), "state/match split mismatch")
    require(set(predictions["split"]) == {"validation_oof", "locked_test"}, "incorrect saved prediction cohorts")
    keys = ["match_id", "innings", "state_sequence"]
    require(not states.duplicated(keys).any(), "duplicate model-ready states")
    require(not predictions.duplicated(keys).any(), "duplicate saved prediction states")
    joined = predictions.merge(states, on=keys, suffixes=("_prediction", ""), validate="one_to_one")
    require(len(joined) == len(predictions), "saved predictions missing state keys")
    require(joined[joined["split_prediction"].eq("locked_test")]["split"].eq("test").all(), "locked predictions contain development states")
    require(joined[joined["split_prediction"].eq("validation_oof")]["split"].eq("validation").all(), "OOF predictions contain nonvalidation states")
    test_states = states[states["split"].eq("test")]
    first_eligible = test_states["innings"].eq(1) & test_states["first_innings_eligible"].fillna(False) \
        & ~test_states["is_reduced_match"].fillna(False) & test_states["final_score"].notna()
    terminal = test_states["terminal_probability"].map(lambda value: pd.notna(value) and math.isfinite(float(value))) \
        | test_states["terminal_status"].fillna("").str.casefold().isin(
            ["won", "lost", "chase_won", "chase_lost", "target_reached", "all_out", "quota_reached", "tied_regulation"])
    chase_eligible = test_states["innings"].eq(2) & test_states["chase_eligible"].fillna(False) \
        & ~test_states["is_reduced_match"].fillna(False) & ~terminal & test_states["chase_won"].notna()
    report["locked_test_inference"] = {}
    for task, model, mask, truth_column in (("first_innings", frozen.first_innings_team, first_eligible, "final_score"),
                                          ("chase", frozen.chase_team, chase_eligible, "chase_won")):
        frame = joined[joined["task"].eq(task) & joined["split_prediction"].eq("locked_test")].copy()
        require(set(map(tuple, frame[keys].to_numpy())) == set(map(tuple, test_states[mask][keys].to_numpy())),
                f"{task}: saved test predictions do not cover every eligible state exactly")
        np.testing.assert_allclose(frame["truth"].to_numpy(dtype=float), frame[truth_column].to_numpy(dtype=float), rtol=0, atol=0)
        rows = frame.to_dict(orient="records")
        actual = np.concatenate([np.asarray(model.predict(rows[start:start + 20000]), dtype=float)
                                 for start in range(0, len(rows), 20000)])
        np.testing.assert_allclose(actual, frame["prediction"].to_numpy(dtype=float), rtol=1e-10, atol=1e-10,
                                   err_msg=f"{task}: frozen executable vs saved test predictions")
        metrics = independent_metrics(frame, task, actual)
        for name, value in metrics.items():
            close_tree(value, production.evaluation[task]["locked_test"][name], f"{task}.metric.{name}")
            close_tree(value, frozen.evaluation[task]["locked_test"][name], f"frozen.{task}.metric.{name}")
        if task == "first_innings":
            intervals = [item for start in range(0, len(rows), 20000)
                         for item in frozen.interval_model.predict(rows[start:start + 20000], actual[start:start + 20000])]
            for name in ("p50", "p80"):
                for bound in ("lower", "upper"):
                    np.testing.assert_allclose([item[name][bound] for item in intervals], frame[name + "_" + bound],
                                               rtol=1e-10, atol=1e-10, err_msg=f"frozen {name} {bound}")
        report["locked_test_inference"][task] = {"status": "all_states_reexecuted", "metrics": metrics,
                                                 "maximum_absolute_prediction_difference": float(np.max(np.abs(actual - frame["prediction"].to_numpy())))}

    report["japan_corrections"] = {}
    for role in ("japan_batting", "japan_bowling", "japan_chasing", "japan_defending"):
        task = "first_innings" if role in {"japan_batting", "japan_bowling"} else "chase"
        team_column = "batting_team" if role in {"japan_batting", "japan_chasing"} else "bowling_team"
        history = joined[joined["task"].eq(task) & joined["split_prediction"].eq("validation_oof") & joined[team_column].eq("Japan")]
        count = history["match_id"].nunique()
        require(count < 12, f"{role}: expected insufficient women's correction history changed")
        for bundle in (production, frozen):
            correction = bundle.japan_corrections[role]
            require(not correction.enabled, f"{role}: correction activated")
            require(correction.fallback_reason == "insufficient_history", f"{role}: unexpected fallback reason")
            require(correction.match_count == count, f"{role}: correction history count mismatch")
            gate = bundle.manifest.japan_gates[role]
            require(not gate["enabled"] and gate["fallback_reason"] == "insufficient_history", f"{role}: manifest gate mismatch")
        report["japan_corrections"][role] = {"enabled": False, "reason": "insufficient_history", "history_matches": int(count)}
    require(not production.manifest.reduced_match_enabled and not frozen.manifest.reduced_match_enabled, "reduced-match feature unexpectedly enabled")
    require(not production.evaluation["reduced_match_gate"]["enabled"], "reduced gate evaluation mismatch")
    report["reduced_match_gate"] = dict(production.evaluation["reduced_match_gate"])

    html = args.html.read_text(encoding="utf-8")
    document = Document()
    document.feed(html)
    require(not document.assets, f"standalone HTML has external dependencies: {document.assets}")
    require("connect-src 'none'" in html, "standalone CSP allows network connections")
    data_blocks = [value for attrs, value in document.scripts if attrs.get("id") == "wasp-standalone-data"]
    require(len(data_blocks) == 1, "standalone HTML data payload missing or duplicated")
    payload = json.loads(data_blocks[0])
    expected_payload = build_standalone_payload(production)
    close_tree(payload, expected_payload, "html_payload_vs_production_bundle")
    require(payload["metadata"]["source_sha256"] == source_sha, "HTML source SHA mismatch")
    require({str(row["match_id"]) for row in payload["japan_matches"]} == japan_ids, "HTML Japan women matches mismatch")
    require(set(payload["replays"]) == japan_ids, "HTML missing Japan women replays")
    require(all(value.get("first_innings") or value.get("chase") for value in payload["replays"].values()), "empty Japan women replay")
    html_matches = {str(row["match_id"]): row for row in payload["japan_matches"]}
    excluded_ids = {"1336982", "1393877", "1485406"}
    require(excluded_ids <= set(html_matches), "excluded Japan women matches missing from Replay")
    for match_id in excluded_ids:
        require(bool(html_matches[match_id].get("model_exclusions")), f"{match_id}: exclusion metadata missing")
    japan_states = states[states["match_id"].isin(japan_ids)]
    for match_id, replay in payload["replays"].items():
        metadata = html_matches[match_id]
        for number, field, eligibility in ((1, "first_innings", "first_innings_eligible"),
                                           (2, "chase", "chase_eligible")):
            points = replay[field]
            original = japan_states[japan_states["match_id"].eq(match_id) & japan_states["innings"].eq(number)].sort_values("state_sequence")
            require(len(points) == len(original), f"{match_id}: physical Replay states lost in innings {number}")
            for column in ("legal_balls_bowled", "runs_so_far", "wickets_lost"):
                np.testing.assert_array_equal([point[column] for point in points], original[column].to_numpy(),
                                              err_msg=f"{match_id}: Replay {column}")
            if not metadata[eligibility]:
                require(all(point["selected"] is None for point in points),
                        f"{match_id}: unsupported innings {number} displays model predictions")
    runtimes = [value for attrs, value in document.scripts if attrs.get("type") != "application/json" and "root.WASPStandalonePredictor =" in value]
    require(len(runtimes) == 1, "standalone executable runtime missing or duplicated")
    require(bool(args.node), "Node.js is required for executable JavaScript parity verification; pass --node")
    report["export_parity"] = javascript_parity(production, payload, runtimes[0], args.node)
    report["standalone"] = {"path": str(args.html.resolve()), "sha256": digest(args.html),
                             "bytes": args.html.stat().st_size, "japan_matches": len(japan_ids),
                             "replays": len(payload["replays"]), "external_dependencies": document.assets,
                             "excluded_matches_retained": sorted(excluded_ids),
                             "all_japan_replay_score_states_match_normalized_data": True,
                             "payload_matches_production_bundle": True}

    provenance = json.loads((ROOT / "provenance.json").read_text(encoding="utf-8"))
    protected = provenance["protected_male_sha256"]
    require(bool(protected), "male preservation provenance is empty")
    for path, expected_sha in protected.items():
        require(digest(Path(path)) == expected_sha, f"protected male file changed: {path}")
    male_bundle_hashes = {value for path, value in protected.items() if path.endswith("bundle.joblib")}
    require(production.manifest.bundle_sha256 not in male_bundle_hashes, "production artifact copied from male bundle")
    require(frozen.manifest.bundle_sha256 not in male_bundle_hashes, "frozen artifact copied from male bundle")
    report["male_preservation"] = {"status": "all_protected_hashes_unchanged", "files": len(protected),
                                    "protected_sha256": protected}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=ROOT / "config" / "wasp.toml")
    parser.add_argument("--html", type=Path, default=ROOT.parents[1] / "japan-women-t20-predictor.html")
    parser.add_argument("--node", default=os.environ.get("NODE_BINARY") or shutil.which("node"))
    parser.add_argument("--expected-japan-matches", type=int, default=45)
    args = parser.parse_args()
    from cricket_japan_bi.wasp.config import load_wasp_config

    report_path = load_wasp_config(args.config).resolve_path("reports_dir") / "verification.json"
    report: dict[str, Any] = {"status": "running", "verification_version": "1.0"}
    started = time.perf_counter()
    try:
        verify(args, report)
        report["status"] = "passed"
    except Exception as exc:
        report["status"] = "failed"
        report["error"] = f"{type(exc).__name__}: {exc}"
    report["elapsed_seconds"] = round(time.perf_counter() - started, 3)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "report": str(report_path),
                      "elapsed_seconds": report["elapsed_seconds"], "error": report.get("error")}, ensure_ascii=False))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
