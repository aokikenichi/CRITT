from __future__ import annotations

import pytest

from cricket_japan_bi.wasp.export import predict_first, serialize_bundle_inference
from cricket_japan_bi.wasp.models.baselines import HierarchicalWinProbability
from cricket_japan_bi.wasp.models.contracts import ArtifactBundle, ArtifactManifest
from cricket_japan_bi.wasp.models.first_innings import SklearnRemainingRegressor
from cricket_japan_bi.wasp.models.intervals import ConformalIntervalModel
from cricket_japan_bi.wasp.models.service import PredictionService


FEATURES = ("runs_so_far", "balls_remaining")


def _remaining_rows():
    return [
        {
            "match_id": str(index),
            "runs_so_far": runs,
            "balls_remaining": balls,
            "wickets_lost": 2,
            "remaining_runs": remaining,
            "sample_weight": 1.0,
        }
        for index, (runs, balls, remaining) in enumerate(
            ((10, 110, 120), (35, 90, 100), (70, 60, 70), (105, 30, 35), (140, 6, 8))
        )
    ]


def _chase_model():
    rows = [
        {
            "match_id": str(index),
            "phase_absolute": "middle",
            "balls_remaining": balls,
            "wickets_remaining": wickets,
            "required_run_rate": rate,
            "chase_won": won,
            "sample_weight": 1.0,
        }
        for index, (balls, wickets, rate, won) in enumerate(
            ((60, 8, 6.0, 1), (60, 8, 12.0, 0), (30, 5, 8.0, 1), (30, 5, 14.0, 0))
        )
    ]
    return HierarchicalWinProbability(24).fit(rows)


def _bundle(first_global, first_team) -> ArtifactBundle:
    chase = _chase_model()
    return ArtifactBundle(
        manifest=ArtifactManifest(
            source_sha256="a" * 64,
            config_sha256="b" * 64,
            bundle_sha256="c" * 64,
            source_cutoff="2026-07-13",
            selected_models={
                "first_innings_global": "ridge",
                "first_innings_team": "tweedie_1.5",
                "chase_global": "empirical",
                "chase_team": "empirical",
            },
            feature_schema={
                "first_innings_model_0": FEATURES,
                "first_innings_model_1": FEATURES,
                "chase_model_0": ("runs_required",),
                "chase_model_1": ("runs_required", "elo_diff"),
            },
        ),
        first_innings_global=first_global,
        first_innings_team=first_team,
        chase_global=chase,
        chase_team=chase,
        interval_model=ConformalIntervalModel().fit([100.0], [100.0]),
        known_teams=("Japan", "Indonesia"),
        global_context={"elo": 1500.0, "era_trend": 2026.0},
    )


def test_ridge_and_log_tweedie_pipeline_match_portable_reference():
    sklearn = pytest.importorskip("sklearn")
    del sklearn
    from sklearn.linear_model import Ridge, TweedieRegressor
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import StandardScaler

    rows = _remaining_rows()
    ridge = SklearnRemainingRegressor(
        Pipeline([("scale", StandardScaler()), ("model", Ridge(alpha=1.0))]),
        FEATURES,
        "ridge",
    ).fit(rows)
    tweedie = SklearnRemainingRegressor(
        Pipeline(
            [
                ("scale", StandardScaler()),
                (
                    "model",
                    TweedieRegressor(
                        alpha=0.1, power=1.5, link="log", max_iter=1000
                    ),
                ),
            ]
        ),
        FEATURES,
        "tweedie",
    ).fit(rows)
    bundle = _bundle(ridge, tweedie)
    exported = serialize_bundle_inference(bundle)
    request = {
        "batting_team": "Japan",
        "bowling_team": "Indonesia",
        "runs": 62,
        "wickets": 2,
        "completed": {"overs": 10, "balls": 0},
        "quota": {"overs": 20, "balls": 0},
    }

    expected = PredictionService(bundle).predict_first_innings(request)
    portable = predict_first(exported, request)

    assert exported["models"]["first_global"]["estimator"]["kind"] == "standardized_linear"
    assert exported["models"]["first_global"]["estimator"]["inverse_link"] == "identity"
    assert exported["models"]["first_team"]["estimator"]["kind"] == "standardized_linear"
    assert exported["models"]["first_team"]["estimator"]["inverse_link"] == "log"
    assert portable["comparison"] == pytest.approx(expected["comparison"], abs=1e-12)


def test_unknown_standardized_pipeline_fails_closed():
    sklearn = pytest.importorskip("sklearn")
    del sklearn
    from sklearn.dummy import DummyRegressor
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import StandardScaler

    unsupported = SklearnRemainingRegressor(
        Pipeline([("scale", StandardScaler()), ("model", DummyRegressor())]),
        FEATURES,
        "dummy",
    ).fit(_remaining_rows())

    with pytest.raises(TypeError, match="unsupported StandardScaler pipeline model"):
        serialize_bundle_inference(_bundle(unsupported, unsupported))
