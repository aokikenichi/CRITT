"""Match-macro score, probability, calibration and interval metrics."""

from __future__ import annotations

import math
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

import numpy as np


def _group_values(
    match_ids: Sequence[Any], values: Sequence[float]
) -> Mapping[str, List[float]]:
    result: Dict[str, List[float]] = {}
    for match_id, value in zip(match_ids, values):
        result.setdefault(str(match_id), []).append(float(value))
    return result


def match_macro_mean(match_ids: Sequence[Any], values: Sequence[float]) -> float:
    grouped = _group_values(match_ids, values)
    if not grouped:
        return float("nan")
    return float(np.mean([np.mean(items) for items in grouped.values()]))


def first_innings_metrics(
    truth: Sequence[float],
    predictions: Sequence[float],
    match_ids: Sequence[Any],
) -> Mapping[str, float]:
    actual = np.asarray(truth, dtype=np.float64)
    predicted = np.asarray(predictions, dtype=np.float64)
    if len(actual) != len(predicted) or len(actual) != len(match_ids):
        raise ValueError("metric inputs must have equal length")
    errors = predicted - actual
    squared_by_match = _group_values(match_ids, errors ** 2)
    match_macro_rmse = (
        float(np.mean([np.sqrt(np.mean(values)) for values in squared_by_match.values()]))
        if squared_by_match
        else float("nan")
    )
    return {
        "states": int(len(actual)),
        "matches": int(len(set(str(value) for value in match_ids))),
        "mae": float(np.mean(np.abs(errors))) if len(errors) else float("nan"),
        "rmse": float(np.sqrt(np.mean(errors ** 2))) if len(errors) else float("nan"),
        "match_macro_mae": match_macro_mean(match_ids, np.abs(errors)),
        "match_macro_rmse": match_macro_rmse,
    }


def equal_mass_ece(
    labels: Sequence[float], probabilities: Sequence[float], bins: int = 10
) -> float:
    y = np.asarray(labels, dtype=np.float64)
    p = np.asarray(probabilities, dtype=np.float64)
    if len(y) == 0:
        return float("nan")
    chunks = np.array_split(np.argsort(p, kind="stable"), min(bins, len(p)))
    return float(
        sum(
            len(indices) / len(p) * abs(float(np.mean(p[indices])) - float(np.mean(y[indices])))
            for indices in chunks
            if len(indices)
        )
    )


def calibration_curve_equal_mass(
    labels: Sequence[float], probabilities: Sequence[float], bins: int = 10
) -> List[Mapping[str, float]]:
    y = np.asarray(labels, dtype=np.float64)
    p = np.asarray(probabilities, dtype=np.float64)
    if len(y) == 0:
        return []
    result = []
    for number, indices in enumerate(np.array_split(np.argsort(p, kind="stable"), min(bins, len(p))), start=1):
        if len(indices):
            result.append(
                {
                    "bin": number,
                    "count": int(len(indices)),
                    "mean_probability": float(np.mean(p[indices])),
                    "observed_rate": float(np.mean(y[indices])),
                }
            )
    return result


def calibration_slope_intercept(
    labels: Sequence[float], probabilities: Sequence[float]
) -> Tuple[Optional[float], Optional[float]]:
    from ..models.chase import PlattCalibrator

    if len(set(float(value) for value in labels)) < 2:
        return None, None
    calibrator = PlattCalibrator().fit(probabilities, labels)
    return calibrator.slope, calibrator.intercept


def probability_metrics(
    labels: Sequence[float],
    probabilities: Sequence[float],
    match_ids: Sequence[Any],
) -> Mapping[str, Any]:
    y = np.asarray(labels, dtype=np.float64)
    p = np.clip(np.asarray(probabilities, dtype=np.float64), 1e-6, 1.0 - 1e-6)
    if len(y) != len(p) or len(y) != len(match_ids):
        raise ValueError("metric inputs must have equal length")
    brier_values = (p - y) ** 2
    log_values = -(y * np.log(p) + (1.0 - y) * np.log(1.0 - p))
    slope, intercept = calibration_slope_intercept(y, p)
    result: Dict[str, Any] = {
        "states": int(len(y)),
        "matches": int(len(set(str(value) for value in match_ids))),
        "brier": float(np.mean(brier_values)) if len(y) else float("nan"),
        "log_loss": float(np.mean(log_values)) if len(y) else float("nan"),
        "match_macro_brier": match_macro_mean(match_ids, brier_values),
        "match_macro_log_loss": match_macro_mean(match_ids, log_values),
        "ece": equal_mass_ece(y, p),
        "calibration_slope": slope,
        "calibration_intercept": intercept,
        "calibration_curve": calibration_curve_equal_mass(y, p),
    }
    try:
        from sklearn.metrics import roc_auc_score

        result["roc_auc"] = float(roc_auc_score(y, p)) if len(np.unique(y)) == 2 else None
    except ImportError:
        result["roc_auc"] = None
    return result


def interval_metrics(
    truth: Sequence[float],
    lower: Sequence[float],
    upper: Sequence[float],
    *,
    nominal_coverage: float,
) -> Mapping[str, float]:
    y = np.asarray(truth, dtype=np.float64)
    lo = np.asarray(lower, dtype=np.float64)
    hi = np.asarray(upper, dtype=np.float64)
    if not (len(y) == len(lo) == len(hi)):
        raise ValueError("interval metric inputs must have equal length")
    if np.any(lo > hi):
        raise ValueError("interval lower bound exceeds upper bound")
    alpha = 1.0 - nominal_coverage
    width = hi - lo
    score = width + 2.0 / alpha * (lo - y) * (y < lo) + 2.0 / alpha * (y - hi) * (y > hi)
    return {
        "nominal_coverage": nominal_coverage,
        "coverage": float(np.mean((y >= lo) & (y <= hi))) if len(y) else float("nan"),
        "mean_width": float(np.mean(width)) if len(y) else float("nan"),
        "interval_score": float(np.mean(score)) if len(y) else float("nan"),
    }


def slice_metrics(
    records: Sequence[Mapping[str, Any]],
    predictions: Sequence[float],
    *,
    task: str,
    field: str,
) -> Mapping[str, Any]:
    groups: Dict[str, List[int]] = {}
    for index, row in enumerate(records):
        groups.setdefault(str(row.get(field) or "unknown"), []).append(index)
    result: Dict[str, Any] = {}
    for key, indices in sorted(groups.items()):
        match_ids = [records[index].get("match_id") for index in indices]
        if task == "first_innings":
            truth = [float(records[index].get("final_score") or 0) for index in indices]
            result[key] = first_innings_metrics(truth, [predictions[index] for index in indices], match_ids)
        else:
            labels = [float(records[index]["chase_won"]) for index in indices]
            result[key] = probability_metrics(labels, [predictions[index] for index in indices], match_ids)
    return result


def interval_slice_metrics(
    records: Sequence[Mapping[str, Any]],
    intervals: Sequence[Mapping[str, Mapping[str, float]]],
    *,
    field: str,
) -> Mapping[str, Any]:
    groups: Dict[str, List[int]] = {}
    for index, row in enumerate(records):
        groups.setdefault(str(row.get(field) or "unknown"), []).append(index)
    result: Dict[str, Any] = {}
    for key, indices in sorted(groups.items()):
        truth = [float(records[index].get("final_score") or 0) for index in indices]
        result[key] = {}
        for name, nominal in (("p50", 0.50), ("p80", 0.80)):
            result[key][name] = interval_metrics(
                truth,
                [float(intervals[index][name]["lower"]) for index in indices],
                [float(intervals[index][name]["upper"]) for index in indices],
                nominal_coverage=nominal,
            )
        result[key]["states"] = len(indices)
        result[key]["matches"] = len(
            {str(records[index].get("match_id") or "") for index in indices}
        )
    return result
