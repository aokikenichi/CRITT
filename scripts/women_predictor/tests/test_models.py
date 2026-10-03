from __future__ import annotations

from pathlib import Path

import pytest

from cricket_japan_bi.wasp.evaluation.metrics import (
    first_innings_metrics,
    interval_metrics,
    probability_metrics,
)
from cricket_japan_bi.wasp.evaluation.splits import assign_split, rolling_origin_folds
from cricket_japan_bi.wasp.features.datasets import build_chase_dataset
from cricket_japan_bi.wasp.models.baselines import (
    HierarchicalWinProbability,
    ResourceTableRegressor,
)
from cricket_japan_bi.wasp.models.chase import next_ball_scenarios
from cricket_japan_bi.wasp.models.contracts import (
    ArtifactBundle,
    ArtifactManifest,
    ArtifactSchemaError,
)
from cricket_japan_bi.wasp.models.intervals import ConformalIntervalModel
from cricket_japan_bi.wasp.models.japan import JapanRoleCorrection, fit_score_correction
from cricket_japan_bi.wasp.models.chase import PlattCalibrator
from cricket_japan_bi.wasp.models.service import (
    PredictionService,
    UnsupportedReducedMatchError,
)


def _first_rows():
    return [
        {
            "match_id": match_id,
            "runs_so_far": 0,
            "wickets_lost": 0,
            "wickets_remaining": 10,
            "legal_balls_bowled": 0,
            "balls_remaining": balls,
            "phase_absolute": "powerplay",
            "final_score": score,
            "remaining_runs": score,
            "sample_weight": 1.0,
        }
        for match_id, balls, score in (("a", 120, 100), ("b", 120, 120), ("c", 60, 55))
    ]


def _chase_rows():
    return [
        {
            "match_id": match_id,
            "phase_absolute": "middle",
            "balls_remaining": balls,
            "wickets_remaining": wickets,
            "required_run_rate": rrr,
            "chase_won": won,
            "sample_weight": 1.0,
        }
        for match_id, balls, wickets, rrr, won in (
            ("a", 60, 8, 6.0, 1),
            ("b", 60, 8, 12.0, 0),
            ("c", 30, 5, 8.0, 1),
            ("d", 30, 5, 14.0, 0),
        )
    ]


def _manifest(source: str = "a", *, serving: bool = False) -> ArtifactManifest:
    return ArtifactManifest(
        source_sha256=source * 64,
        config_sha256="c" * 64,
        bundle_sha256="d" * 64 if serving else "",
        selected_models={
            "first_innings_global": "resource",
            "first_innings_team": "resource",
            "chase_global": "empirical",
            "chase_team": "empirical",
        },
        feature_schema={
            "first_innings_model_0": ["runs_so_far"],
            "first_innings_model_1": ["runs_so_far", "elo_diff"],
            "chase_model_0": ["runs_required"],
            "chase_model_1": ["runs_required", "elo_diff"],
        },
    )


class ContextFinalModel:
    def __init__(self, base: float, use_context: bool = False) -> None:
        self.base = base
        self.use_context = use_context
        self.last_state = None

    def predict(self, rows):
        self.last_state = rows[0]
        adjustment = rows[0].get("elo_diff", 0.0) / 10.0 if self.use_context else 0.0
        return [float(rows[0].get("runs_so_far") or 0) + self.base + adjustment]


class FeatureModel:
    def __init__(self, features):
        self.features = tuple(features)

    def predict(self, rows):
        return [0.5 for _ in rows]


def test_resource_and_empirical_models_are_finite_and_serializable(tmp_path: Path):
    resource = ResourceTableRegressor(24).fit(_first_rows())
    chase = HierarchicalWinProbability(24).fit(_chase_rows())
    assert resource.predict(_first_rows())[0] >= 0
    assert 0 < chase.predict(_chase_rows())[0] < 1
    bundle = ArtifactBundle(
        _manifest(),
        resource,
        resource,
        chase,
        chase,
        interval_model=ConformalIntervalModel().fit([100.0], [100.0]),
    )
    bundle.save(tmp_path)
    loaded = ArtifactBundle.load(tmp_path)
    assert loaded.manifest.source_sha256 == "a" * 64
    assert loaded.first_innings_global.predict(_first_rows()) == pytest.approx(
        resource.predict(_first_rows())
    )
    payload = tmp_path / "bundle.joblib"
    payload.write_bytes(payload.read_bytes() + b"tampered")
    with pytest.raises(ValueError, match="SHA-256 mismatch"):
        ArtifactBundle.load(tmp_path)


def test_serving_manifest_rejects_missing_feature_contract():
    manifest = _manifest(serving=True)
    manifest.feature_schema = {}
    with pytest.raises(ValueError, match="feature_schema missing"):
        manifest.validate_serving()


def test_serving_bundle_rejects_missing_models_intervals_and_feature_mismatch():
    interval = ConformalIntervalModel().fit([100.0], [100.0])
    bundle = ArtifactBundle(
        manifest=_manifest(serving=True),
        first_innings_global=FeatureModel(("runs_so_far",)),
        first_innings_team=FeatureModel(("runs_so_far", "elo_diff")),
        chase_global=FeatureModel(("runs_required",)),
        chase_team=FeatureModel(("runs_required", "elo_diff")),
        interval_model=interval,
    )
    bundle.validate_serving()

    bundle.chase_team = None
    with pytest.raises(ArtifactSchemaError, match="chase_team must expose predict"):
        bundle.validate_serving()

    bundle.chase_team = FeatureModel(("runs_so_far",))
    with pytest.raises(ArtifactSchemaError, match="chase_team feature schema mismatch"):
        bundle.validate_serving()

    bundle.chase_team = FeatureModel(("runs_required", "elo_diff"))
    bundle.interval_model = object()
    with pytest.raises(ArtifactSchemaError, match="interval_model missing"):
        bundle.validate_serving()


def test_conformal_intervals_are_nested_and_contain_point():
    model = ConformalIntervalModel().fit([100, 120, 80], [90, 118, 90])
    state = {"runs_so_far": 40, "wickets_lost": 2, "balls_remaining": 80}
    intervals = model.predict_one(state, 100)
    assert intervals["p80"]["lower"] <= intervals["p50"]["lower"] <= 100
    assert 100 <= intervals["p50"]["upper"] <= intervals["p80"]["upper"]
    score = interval_metrics([100], [intervals["p80"]["lower"]], [intervals["p80"]["upper"]], nominal_coverage=0.8)
    assert 0 <= score["coverage"] <= 1


def test_japan_correction_falls_back_with_too_few_matches():
    rows = [
        {
            "match_id": "j{}".format(index),
            "match_date": "2024-01-01",
            "batting_team": "Japan",
            "bowling_team": "X",
            "final_score": 100,
        }
        for index in range(3)
    ]
    correction = fit_score_correction(rows, [90, 90, 90], role="japan_batting")
    assert correction.enabled is False
    assert correction.fallback_reason == "insufficient_history"


def test_chase_dataset_excludes_terminal_status_without_probability_column():
    base = {
        "match_id": "m",
        "innings": 2,
        "chase_eligible": True,
        "is_reduced_match": False,
        "chase_won": True,
    }
    rows = [dict(base, state_sequence=0, terminal_status=None), dict(base, state_sequence=1, terminal_status="won")]
    assert len(build_chase_dataset(rows)) == 1
    assert len(build_chase_dataset(rows, include_terminal=True)) == 2


def test_metrics_are_match_macro_and_time_splits_are_match_safe():
    assert assign_split("2022-12-31") == "train"
    assert assign_split("2023-01-01") == "validation"
    assert assign_split("2025-01-01") == "test"
    records = [
        {"match_id": "a", "match_date": "2022-01-01"},
        {"match_id": "a", "match_date": "2022-01-01"},
        {"match_id": "b", "match_date": "2023-01-01"},
    ]
    folds = rolling_origin_folds(records, validation_years=(2023,))
    assert folds[0].train_indices == (0, 1)
    assert folds[0].validation_indices == (2,)
    score = first_innings_metrics([100, 100, 80], [90, 100, 80], ["a", "a", "b"])
    assert score["match_macro_mae"] == pytest.approx(2.5)
    probability = probability_metrics([0, 1], [0.2, 0.8], ["a", "b"])
    assert probability["brier"] == pytest.approx(0.04)


def test_match_macro_rmse_is_root_mean_square_within_match():
    score = first_innings_metrics([0, 0], [1, 3], ["same", "same"])
    assert score["match_macro_rmse"] == pytest.approx(5 ** 0.5)


def test_next_ball_scenarios_recompute_all_derived_state_features():
    class CaptureModel:
        def predict(self, rows):
            row = rows[0]
            assert row["legal_balls_bowled"] == 37
            assert row["phase_absolute"] == "middle"
            assert row["progress"] == pytest.approx(37 / 120)
            assert row["rrr_minus_crr"] == pytest.approx(
                row["required_run_rate"] - row["current_run_rate"]
            )
            return [0.5]

    state = {
        "runs_so_far": 40,
        "wickets_lost": 2,
        "wickets_remaining": 8,
        "legal_balls_bowled": 36,
        "balls_remaining": 84,
        "innings_ball_limit": 120,
        "target": 120,
    }
    scenarios = next_ball_scenarios(CaptureModel(), state)
    assert [item["runs"] for item in scenarios] == [0, 1, 2, 3, 4, 6, 0]


def test_prediction_service_contract_and_terminal_rules(tmp_path: Path):
    first = ResourceTableRegressor().fit(_first_rows())
    chase = HierarchicalWinProbability().fit(_chase_rows())
    intervals = ConformalIntervalModel().fit([100, 120], [110, 110])
    bundle = ArtifactBundle(
        manifest=ArtifactManifest(
            source_sha256="b" * 64,
            config_sha256="c" * 64,
            bundle_sha256="d" * 64,
            source_cutoff="2026-01-01",
            selected_models=_manifest().selected_models,
            feature_schema=_manifest().feature_schema,
        ),
        first_innings_global=first,
        first_innings_team=first,
        chase_global=chase,
        chase_team=chase,
        interval_model=intervals,
        known_teams=("Japan", "World XI"),
        known_venues=("Ground",),
    )
    service = PredictionService(bundle)
    first_response = service.predict_first_innings(
        {
            "batting_team": "Japan",
            "bowling_team": "World XI",
            "runs": 40,
            "wickets": 2,
            "completed": {"overs": 6, "balls": 0},
            "quota": {"overs": 20, "balls": 0},
            "venue": "Ground",
            "use_japan_correction": True,
        }
    )
    assert first_response["comparison"]["selected"] >= 40
    assert first_response["correction"]["applied"] is False
    chase_response = service.predict_chase(
        {
            "chasing_team": "Japan",
            "defending_team": "World XI",
            "target": 80,
            "current_score": 79,
            "wickets": 10,
            "target_ball_limit": {"overs": 20, "balls": 0},
            "balls_remaining": 0,
            "venue": "Ground",
        }
    )
    assert chase_response["terminal"] == {
        "is_terminal": True,
        "status": "tied_regulation",
        "probability": None,
    }
    assert chase_response["comparison"]["selected"] is None
    with pytest.raises(UnsupportedReducedMatchError):
        service.predict_first_innings(
            {
                "batting_team": "Japan",
                "bowling_team": "World XI",
                "runs": 0,
                "wickets": 0,
                "completed": {"overs": 0, "balls": 0},
                "quota": {"overs": 17, "balls": 0},
            }
        )

    bundle.matches = (
        {"match_id": "old", "match_date": "2024-01-01", "team_1": "Japan", "team_2": "World XI"},
        {"match_id": "new", "match_date": "2025-01-01", "team_1": "Japan", "team_2": "World XI"},
    )
    service = PredictionService(bundle)
    from datetime import date

    page = service.list_matches(from_date=date(2025, 1, 1), to_date=date(2025, 12, 31))
    assert [row["match_id"] for row in page["items"]] == ["new"]


def test_evaluation_filters_preserve_base_metrics_and_add_filtered_slice():
    first = ResourceTableRegressor().fit(_first_rows())
    chase = HierarchicalWinProbability().fit(_chase_rows())
    bundle = ArtifactBundle(
        manifest=_manifest(serving=True),
        first_innings_global=first,
        first_innings_team=first,
        chase_global=chase,
        chase_team=chase,
        interval_model=ConformalIntervalModel().fit([100.0], [100.0]),
        evaluation={
            "first_innings": {
                "locked_test": {"match_macro_mae": 10.0, "matches": 4},
                "by_slice": {
                    "phase_absolute": {
                        "powerplay": {"match_macro_mae": 11.0, "matches": 4}
                    },
                    "japan_role": {
                        "japan_batting": {"match_macro_mae": 12.0, "matches": 3}
                    },
                },
            },
            "chase": {
                "locked_test": {"match_macro_brier": 0.18, "matches": 4},
                "by_slice": {
                    "phase_absolute": {
                        "powerplay": {"match_macro_brier": 0.19, "matches": 4}
                    }
                },
            },
        },
    )
    service = PredictionService(bundle)
    selected = service.evaluation(
        model="first_innings", scope="japan", phase="powerplay"
    )
    assert selected["locked_test"]["match_macro_mae"] == 10.0
    assert selected["filtered"]["phase"]["match_macro_mae"] == 11.0
    assert selected["filtered"]["scope"]["japan_batting"]["matches"] == 3
    assert selected["filters"] == {
        "model": "first_innings",
        "scope": "japan",
        "phase": "powerplay",
    }

    combined = service.evaluation(scope="japan")
    assert "first_innings" in combined and "chase" in combined
    assert combined["filtered"]["first_innings"]["scope"]["japan_batting"][
        "match_macro_mae"
    ] == 12.0


def test_manual_prediction_uses_latest_context_and_unknown_team_falls_back_global():
    global_model = ContextFinalModel(10.0)
    team_model = ContextFinalModel(20.0, use_context=True)
    chase = HierarchicalWinProbability().fit(_chase_rows())
    bundle = ArtifactBundle(
        manifest=_manifest(serving=True),
        first_innings_global=global_model,
        first_innings_team=team_model,
        chase_global=chase,
        chase_team=chase,
        interval_model=ConformalIntervalModel().fit([100.0], [100.0]),
        known_teams=("Japan", "World XI"),
        known_venues=("Ground",),
        latest_team_context={
            "Japan": {"elo": 1550.0, "batting_form": 145.0, "bowling_suppression": 2.0},
            "World XI": {"elo": 1450.0, "batting_form": 135.0, "bowling_suppression": -1.0},
        },
        latest_venue_context={
            "Ground": {"venue_prior": 142.0, "venue_sample_count": 10.0}
        },
        global_context={
            "elo": 1500.0,
            "batting_form": 140.0,
            "bowling_suppression": 0.0,
            "venue_prior": 140.0,
            "era_trend": 2026.0,
        },
    )
    service = PredictionService(bundle)
    payload = {
        "batting_team": "Japan",
        "bowling_team": "World XI",
        "runs": 40,
        "wickets": 2,
        "completed": {"overs": 6, "balls": 0},
        "quota": {"overs": 20, "balls": 0},
        "venue": "Ground",
    }
    known = service.predict_first_innings(payload)
    assert team_model.last_state["elo_diff"] == 100.0
    assert team_model.last_state["venue_prior"] == 142.0
    assert known["comparison"]["selected"] > known["comparison"]["global"]
    unknown = service.predict_first_innings(dict(payload, bowling_team="New XI"))
    assert unknown["comparison"]["team_adjusted"] == unknown["comparison"]["global"]
    assert unknown["comparison"]["selected"] == unknown["comparison"]["global"]


def test_terminal_chase_bypasses_japan_probability_correction():
    first = ResourceTableRegressor().fit(_first_rows())
    chase = HierarchicalWinProbability().fit(_chase_rows())
    correction = JapanRoleCorrection(
        role="japan_chasing",
        kind="probability",
        enabled=True,
        match_count=20,
        calibrator=PlattCalibrator(intercept=2.0),
    )
    bundle = ArtifactBundle(
        manifest=_manifest(serving=True),
        first_innings_global=first,
        first_innings_team=first,
        chase_global=chase,
        chase_team=chase,
        interval_model=ConformalIntervalModel().fit([100.0], [100.0]),
        japan_corrections={"japan_chasing": correction},
        known_teams=("Japan", "World XI"),
    )
    response = PredictionService(bundle).predict_chase(
        {
            "chasing_team": "Japan",
            "defending_team": "World XI",
            "target": 80,
            "current_score": 80,
            "wickets": 4,
            "target_ball_limit": {"overs": 20, "balls": 0},
            "balls_remaining": 30,
            "use_japan_correction": True,
        }
    )
    assert set(response["comparison"].values()) == {1.0}
    assert response["correction"]["applied"] is False
