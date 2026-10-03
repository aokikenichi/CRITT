"""Serialize the executable portion of an :class:`ArtifactBundle` to JSON.

Only stable numeric prediction state is exported.  Training data, estimator
objects and Python class names are intentionally excluded.  HistGradientBoosting
uses private scikit-learn tree arrays because sklearn does not provide a public
portable format; the resulting JSON is versioned and its predictions are
verified by the standalone export command before publication.
"""

from __future__ import annotations

import hashlib
import json
import math
from datetime import date, datetime
from typing import Any, Dict, Mapping, Sequence

from ..models.baselines import (
    CurrentRunRateBaseline,
    HierarchicalWinProbability,
    ResourceTableRegressor,
)
from ..models.chase import PlattCalibrator, SklearnChaseClassifier
from ..models.contracts import ArtifactBundle
from ..models.first_innings import SklearnRemainingRegressor
from ..models.intervals import (
    ConformalIntervalModel,
    QuantileConformalIntervalModel,
)


STANDALONE_MODEL_SCHEMA_VERSION = "wasp-standalone-models/1.0"


class UnsupportedEstimatorError(TypeError):
    """Raised when an artifact cannot be represented by the browser runtime."""


def _json_safe(value: Any) -> Any:
    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("standalone model JSON cannot contain NaN or infinity")
        return value
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Mapping):
        return {
            str(key): _json_safe(item)
            for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))
        }
    if isinstance(value, (list, tuple, set)):
        items = list(value)
        if isinstance(value, set):
            items.sort(key=str)
        return [_json_safe(item) for item in items]
    module = value.__class__.__module__
    if module.startswith("numpy") and hasattr(value, "tolist"):
        return _json_safe(value.tolist())
    if module.startswith("numpy") and hasattr(value, "item"):
        return _json_safe(value.item())
    raise TypeError("value is not JSON-safe: {}".format(type(value).__name__))


def canonical_json(value: Any) -> str:
    """Return the byte-for-byte deterministic JSON representation."""

    return json.dumps(
        _json_safe(value),
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def _link_name(estimator: Any) -> str:
    link = getattr(getattr(estimator, "_loss", None), "link", None)
    name = type(link).__name__.casefold()
    if "identity" in name:
        return "identity"
    if "logit" in name:
        return "logit"
    if "log" in name:
        return "log"
    raise UnsupportedEstimatorError(
        "unsupported HistGradientBoosting inverse link: {}".format(type(link).__name__)
    )


def _serialize_tree(predictor: Any) -> Mapping[str, Any]:
    nodes = getattr(predictor, "nodes", None)
    if nodes is None:
        raise UnsupportedEstimatorError("HistGradientBoosting tree has no node array")
    categorical = [int(node["is_categorical"]) for node in nodes]
    if any(categorical):
        # None of the WASP feature schemas contains categorical columns.  Fail
        # explicitly if that invariant changes instead of exporting a subtly
        # different membership test.
        raise UnsupportedEstimatorError(
            "categorical HistGradientBoosting nodes are not supported"
        )
    return {
        "value": [float(node["value"]) for node in nodes],
        "feature": [int(node["feature_idx"]) for node in nodes],
        "threshold": [float(node["num_threshold"]) for node in nodes],
        "missing_left": [int(node["missing_go_to_left"]) for node in nodes],
        "left": [int(node["left"]) for node in nodes],
        "right": [int(node["right"]) for node in nodes],
        "leaf": [int(node["is_leaf"]) for node in nodes],
    }


def _serialize_hgb(estimator: Any) -> Mapping[str, Any]:
    predictors = getattr(estimator, "_predictors", None)
    baseline = getattr(estimator, "_baseline_prediction", None)
    if predictors is None or baseline is None:
        raise UnsupportedEstimatorError("estimator is not a fitted HistGradientBoosting model")
    if any(len(iteration) != 1 for iteration in predictors):
        raise UnsupportedEstimatorError(
            "only scalar and binary HistGradientBoosting models are supported"
        )
    flattened_baseline = baseline.ravel().tolist()
    if len(flattened_baseline) != 1:
        raise UnsupportedEstimatorError("multi-output HistGradientBoosting is unsupported")
    return {
        "kind": "hist_gradient_boosting",
        "baseline": float(flattened_baseline[0]),
        "inverse_link": _link_name(estimator),
        "n_features": int(getattr(estimator, "n_features_in_", 0)),
        "trees": [_serialize_tree(iteration[0]) for iteration in predictors],
    }


def _standardized_parameters(
    scaler: Any, model: Any
) -> tuple[Sequence[float], Sequence[float], Sequence[float], float]:
    """Extract a fitted one-output linear model after StandardScaler.

    Keeping scaling explicit makes the JSON independent from scikit-learn and
    avoids folding coefficients in a way that can amplify rounding error.
    """

    if not hasattr(model, "coef_") or not hasattr(model, "intercept_"):
        raise UnsupportedEstimatorError("pipeline model is not fitted")
    raw_coefficients = model.coef_.tolist()
    if raw_coefficients and isinstance(raw_coefficients[0], list):
        raise UnsupportedEstimatorError("multi-output linear models are unsupported")
    coefficients = [float(value) for value in raw_coefficients]
    feature_count = len(coefficients)
    if feature_count < 1:
        raise UnsupportedEstimatorError("linear model contains no coefficients")
    if int(getattr(scaler, "n_features_in_", 0)) != feature_count:
        raise UnsupportedEstimatorError("StandardScaler/model feature-count mismatch")
    if bool(getattr(scaler, "with_mean", True)):
        if getattr(scaler, "mean_", None) is None:
            raise UnsupportedEstimatorError("fitted StandardScaler mean is missing")
        means = [float(value) for value in scaler.mean_.tolist()]
    else:
        means = [0.0] * feature_count
    if bool(getattr(scaler, "with_std", True)):
        if getattr(scaler, "scale_", None) is None:
            raise UnsupportedEstimatorError("fitted StandardScaler scale is missing")
        scales = [float(value) for value in scaler.scale_.tolist()]
    else:
        scales = [1.0] * feature_count
    if len(means) != feature_count or len(scales) != feature_count:
        raise UnsupportedEstimatorError("StandardScaler/model feature-count mismatch")
    if any(not math.isfinite(value) or value <= 0.0 for value in scales):
        raise UnsupportedEstimatorError("StandardScaler scale must be finite and positive")
    raw_intercept = model.intercept_
    if hasattr(raw_intercept, "tolist"):
        raw_intercept = raw_intercept.tolist()
    if isinstance(raw_intercept, list):
        if len(raw_intercept) != 1:
            raise UnsupportedEstimatorError("multi-output linear models are unsupported")
        raw_intercept = raw_intercept[0]
    intercept = float(raw_intercept)
    if not all(math.isfinite(value) for value in (*means, *coefficients, intercept)):
        raise UnsupportedEstimatorError("linear pipeline parameters must be finite")
    return means, scales, coefficients, intercept


def _serialize_standardized_pipeline(estimator: Any) -> Mapping[str, Any]:
    steps = getattr(estimator, "named_steps", None)
    if not steps or "scale" not in steps or "model" not in steps:
        raise UnsupportedEstimatorError("expected a scale/model sklearn pipeline")
    scaler = steps["scale"]
    model = steps["model"]
    if type(scaler).__name__ != "StandardScaler":
        raise UnsupportedEstimatorError(
            "only StandardScaler pipelines are portable, got {}".format(
                type(scaler).__name__
            )
        )
    model_name = type(model).__name__
    if model_name == "LogisticRegression":
        coefficients = model.coef_.tolist()
        intercepts = model.intercept_.tolist()
        if len(coefficients) != 1 or len(intercepts) != 1:
            raise UnsupportedEstimatorError(
                "only binary LogisticRegression is supported"
            )
        classes = [_json_safe(item) for item in model.classes_.tolist()]
        if classes != [0, 1]:
            raise UnsupportedEstimatorError(
                "standalone chase logistic requires classes [0, 1]"
            )
        # LogisticRegression publishes its coefficients as a two-dimensional
        # binary-class array, unlike the regressors below.
        coefficient = [float(value) for value in coefficients[0]]
        feature_count = len(coefficient)
        if int(getattr(scaler, "n_features_in_", 0)) != feature_count:
            raise UnsupportedEstimatorError(
                "StandardScaler/model feature-count mismatch"
            )
        mean = (
            [float(value) for value in scaler.mean_.tolist()]
            if bool(getattr(scaler, "with_mean", True))
            else [0.0] * feature_count
        )
        scale = (
            [float(value) for value in scaler.scale_.tolist()]
            if bool(getattr(scaler, "with_std", True))
            else [1.0] * feature_count
        )
        if len(mean) != feature_count or len(scale) != feature_count:
            raise UnsupportedEstimatorError(
                "StandardScaler/model feature-count mismatch"
            )
        if any(not math.isfinite(value) or value <= 0.0 for value in scale):
            raise UnsupportedEstimatorError(
                "StandardScaler scale must be finite and positive"
            )
        intercept = float(intercepts[0])
        if not all(
            math.isfinite(value) for value in (*mean, *coefficient, intercept)
        ):
            raise UnsupportedEstimatorError(
                "logistic pipeline parameters must be finite"
            )
        return {
            "kind": "standardized_logistic",
            "mean": mean,
            "scale": scale,
            "coefficient": coefficient,
            "intercept": intercept,
        }

    if model_name not in {"Ridge", "TweedieRegressor"}:
        raise UnsupportedEstimatorError(
            "unsupported StandardScaler pipeline model: {}".format(model_name)
        )
    mean, scale, coefficient, intercept = _standardized_parameters(scaler, model)
    inverse_link = "identity"
    if model_name == "TweedieRegressor":
        link = str(getattr(model, "link", "auto")).casefold()
        if link == "auto":
            link = "log" if float(getattr(model, "power", 0.0)) > 0.0 else "identity"
        if link not in {"identity", "log"}:
            raise UnsupportedEstimatorError(
                "unsupported TweedieRegressor inverse link: {}".format(link)
            )
        inverse_link = link
    return {
        "kind": "standardized_linear",
        "inverse_link": inverse_link,
        "mean": list(mean),
        "scale": list(scale),
        "coefficient": list(coefficient),
        "intercept": intercept,
    }


def _serialize_estimator(estimator: Any) -> Mapping[str, Any]:
    name = type(estimator).__name__
    if name.startswith("HistGradientBoosting"):
        return _serialize_hgb(estimator)
    if hasattr(estimator, "named_steps"):
        return _serialize_standardized_pipeline(estimator)
    raise UnsupportedEstimatorError("unsupported sklearn estimator: {}".format(name))


def _table_levels(levels: Sequence[Mapping[Any, Any]]) -> Sequence[Any]:
    result = []
    for level in levels:
        entries = []
        for key, value in level.items():
            key_items = list(key)
            entries.append([key_items, float(value[0]), float(value[1])])
        entries.sort(key=lambda item: canonical_json(item[0]))
        result.append(entries)
    return result


def _serialize_first_model(model: Any) -> Mapping[str, Any]:
    if isinstance(model, SklearnRemainingRegressor):
        return {
            "kind": "remaining_regressor",
            "features": list(model.features),
            "estimator": _serialize_estimator(model.estimator),
        }
    if isinstance(model, CurrentRunRateBaseline):
        return {"kind": "current_run_rate", "start_score": float(model.start_score)}
    if isinstance(model, ResourceTableRegressor):
        return {
            "kind": "resource_table",
            "pseudo_count": float(model.pseudo_count),
            "global_mean": float(model.global_mean),
            "levels": _table_levels(model.stats),
        }
    raise UnsupportedEstimatorError(
        "unsupported first-innings model: {}".format(type(model).__name__)
    )


def _serialize_calibrator(calibrator: Any) -> Any:
    if calibrator is None:
        return None
    if not isinstance(calibrator, PlattCalibrator):
        raise UnsupportedEstimatorError(
            "unsupported probability calibrator: {}".format(type(calibrator).__name__)
        )
    return {
        "kind": "platt",
        "slope": float(calibrator.slope),
        "intercept": float(calibrator.intercept),
    }


def _serialize_chase_model(model: Any) -> Mapping[str, Any]:
    if isinstance(model, SklearnChaseClassifier):
        return {
            "kind": "chase_classifier",
            "features": list(model.features),
            "estimator": _serialize_estimator(model.estimator),
            "calibrator": _serialize_calibrator(model.calibrator),
        }
    if isinstance(model, HierarchicalWinProbability):
        return {
            "kind": "hierarchical_probability",
            "pseudo_count": float(model.pseudo_count),
            "global_probability": float(model.global_probability),
            "levels": _table_levels(model.stats),
        }
    raise UnsupportedEstimatorError(
        "unsupported chase model: {}".format(type(model).__name__)
    )


def _serialize_interval(model: Any) -> Mapping[str, Any]:
    if isinstance(model, QuantileConformalIntervalModel):
        quantile_models = {
            format(float(quantile), ".2f"): _serialize_hgb(estimator)
            for quantile, estimator in sorted(model.models.items())
        }
        expected = {"0.10", "0.25", "0.75", "0.90"}
        if set(quantile_models) != expected:
            raise UnsupportedEstimatorError(
                "quantile interval model must contain q=.10/.25/.75/.90"
            )
        return {
            "kind": "quantile_conformal",
            "features": list(model.features),
            "models": quantile_models,
            "correction_50": float(model.correction_50),
            "correction_80": float(model.correction_80),
        }
    if isinstance(model, ConformalIntervalModel):
        return {
            "kind": "symmetric_conformal",
            "radius_50": float(model.radius_50),
            "radius_80": float(model.radius_80),
        }
    raise UnsupportedEstimatorError(
        "unsupported interval model: {}".format(type(model).__name__)
    )


def _serialize_corrections(corrections: Mapping[str, Any]) -> Mapping[str, Any]:
    result: Dict[str, Any] = {}
    for role, correction in sorted(corrections.items()):
        result[str(role)] = {
            "role": str(correction.role),
            "kind": str(correction.kind),
            "enabled": bool(correction.enabled),
            "match_count": int(correction.match_count),
            "offset": float(correction.offset),
            "calibrator": _serialize_calibrator(correction.calibrator),
            "fallback_reason": correction.fallback_reason,
            "ci80": [float(value) for value in correction.ci80],
            "ci95": [float(value) for value in correction.ci95],
        }
    return result


def serialize_bundle_inference(bundle: ArtifactBundle) -> Mapping[str, Any]:
    """Return a deterministic, JSON-safe browser inference payload.

    ``content_sha256`` covers the canonical payload with that field omitted,
    allowing the HTML exporter or browser runtime to identify the exact model
    payload independently of the larger joblib artifact.
    """

    bundle.validate_serving()
    payload: Dict[str, Any] = {
        "schema_version": STANDALONE_MODEL_SCHEMA_VERSION,
        "source_sha256": bundle.manifest.source_sha256,
        "config_sha256": bundle.manifest.config_sha256,
        "source_cutoff": bundle.manifest.source_cutoff,
        "selected_models": dict(bundle.manifest.selected_models),
        "reduced_match_enabled": bool(bundle.manifest.reduced_match_enabled),
        "known_teams": sorted(str(value) for value in bundle.known_teams),
        "known_venues": sorted(str(value) for value in bundle.known_venues),
        "context": {
            "global": _json_safe(bundle.global_context),
            "teams": _json_safe(bundle.latest_team_context),
            "venues": _json_safe(bundle.latest_venue_context),
        },
        "models": {
            "first_global": _serialize_first_model(bundle.first_innings_global),
            "first_team": _serialize_first_model(bundle.first_innings_team),
            "chase_global": _serialize_chase_model(bundle.chase_global),
            "chase_team": _serialize_chase_model(bundle.chase_team),
        },
        "interval": _serialize_interval(bundle.interval_model),
        "japan_corrections": _serialize_corrections(bundle.japan_corrections),
    }
    payload = _json_safe(payload)
    payload["content_sha256"] = hashlib.sha256(
        canonical_json(payload).encode("utf-8")
    ).hexdigest()
    return payload
