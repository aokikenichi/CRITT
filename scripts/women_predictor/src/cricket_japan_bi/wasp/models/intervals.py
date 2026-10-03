"""First-innings predictive intervals with split-conformal correction."""

from __future__ import annotations

from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

import numpy as np

from .baselines import _rows


def _higher_quantile(values: Sequence[float], quantile: float) -> float:
    if not values:
        return 0.0
    try:
        return float(np.quantile(np.asarray(values), quantile, method="higher"))
    except TypeError:  # NumPy < 1.22
        return float(np.quantile(np.asarray(values), quantile, interpolation="higher"))


class ConformalIntervalModel:
    """Symmetric match-agnostic conformal intervals around a point estimate."""

    def __init__(self) -> None:
        self.radius_50 = 0.0
        self.radius_80 = 0.0
        self.fitted = False

    def fit(
        self, truth: Sequence[float], predictions: Sequence[float]
    ) -> "ConformalIntervalModel":
        if len(truth) != len(predictions):
            raise ValueError("truth and predictions must have equal length")
        residuals = [abs(float(actual) - float(predicted)) for actual, predicted in zip(truth, predictions)]
        self.radius_50 = _higher_quantile(residuals, 0.50)
        self.radius_80 = _higher_quantile(residuals, 0.80)
        self.fitted = True
        return self

    def predict_one(self, state: Mapping[str, Any], point: float) -> Mapping[str, Mapping[str, float]]:
        runs = float(state.get("runs_so_far") or 0)
        point = max(runs, float(point))
        terminal = int(state.get("wickets_lost") or 0) >= 10 or int(state.get("balls_remaining") or 0) <= 0
        if terminal:
            return {
                "p50": {"lower": runs, "upper": runs},
                "p80": {"lower": runs, "upper": runs},
            }
        lower50 = max(runs, point - self.radius_50)
        upper50 = max(point, point + self.radius_50)
        lower80 = max(runs, min(lower50, point - self.radius_80))
        upper80 = max(upper50, point + self.radius_80)
        return {
            "p50": {"lower": lower50, "upper": upper50},
            "p80": {"lower": lower80, "upper": upper80},
        }

    def predict(self, states: Any, points: Sequence[float]) -> List[Mapping[str, Any]]:
        rows = _rows(states)
        return [self.predict_one(row, point) for row, point in zip(rows, points)]


class QuantileConformalIntervalModel:
    """Optional quantile HGB bounds plus validation-residual correction."""

    QUANTILES = (0.10, 0.25, 0.75, 0.90)

    def __init__(self, features: Sequence[str], random_state: int = 20260731) -> None:
        self.features = tuple(features)
        self.random_state = random_state
        self.models: Dict[float, Any] = {}
        self.correction_50 = 0.0
        self.correction_80 = 0.0

    def fit(self, train_records: Any) -> "QuantileConformalIntervalModel":
        try:
            from sklearn.ensemble import HistGradientBoostingRegressor
        except ImportError as exc:
            raise RuntimeError("scikit-learn is required for quantile intervals") from exc
        from ..features.datasets import numeric_matrix

        rows = _rows(train_records)
        matrix, _ = numeric_matrix(rows, self.features)
        target = [float(row["remaining_runs"]) for row in rows]
        for quantile in self.QUANTILES:
            model = HistGradientBoostingRegressor(
                loss="quantile",
                quantile=quantile,
                learning_rate=0.06,
                max_iter=200,
                l2_regularization=2.0,
                random_state=self.random_state,
            )
            model.fit(matrix, target)
            self.models[quantile] = model
        return self

    def calibrate(self, validation_records: Any) -> "QuantileConformalIntervalModel":
        rows = _rows(validation_records)
        bounds = self._raw(rows)
        scores50, scores80 = self.conformity_scores(rows, bounds)
        self.set_conformal_scores(scores50, scores80)
        return self

    @staticmethod
    def conformity_scores(
        rows: Sequence[Mapping[str, Any]], bounds: Sequence[Mapping[str, Any]]
    ) -> Tuple[List[float], List[float]]:
        scores50: List[float] = []
        scores80: List[float] = []
        for row, item in zip(rows, bounds):
            truth = float(row.get("final_score") or 0)
            scores50.append(max(item["p50"]["lower"] - truth, truth - item["p50"]["upper"], 0.0))
            scores80.append(max(item["p80"]["lower"] - truth, truth - item["p80"]["upper"], 0.0))
        return scores50, scores80

    def set_conformal_scores(
        self, scores50: Sequence[float], scores80: Sequence[float]
    ) -> "QuantileConformalIntervalModel":
        self.correction_50 = _higher_quantile(scores50, 0.50)
        self.correction_80 = _higher_quantile(scores80, 0.80)
        return self

    def _raw(self, rows: Any) -> List[Mapping[str, Any]]:
        from ..features.datasets import numeric_matrix

        records = _rows(rows)
        matrix, _ = numeric_matrix(records, self.features)
        predictions = {
            q: np.asarray(model.predict(matrix), dtype=np.float64)
            for q, model in self.models.items()
        }
        result: List[Mapping[str, Any]] = []
        for index, row in enumerate(records):
            runs = float(row.get("runs_so_far") or 0)
            values = sorted(max(0.0, float(predictions[q][index])) for q in self.QUANTILES)
            result.append(
                {
                    "p50": {"lower": runs + values[1], "upper": runs + values[2]},
                    "p80": {"lower": runs + values[0], "upper": runs + values[3]},
                }
            )
        return result

    def predict_one(self, state: Mapping[str, Any], point: float) -> Mapping[str, Any]:
        return self.predict([state], [point])[0]

    def predict(
        self, states: Any, points: Sequence[float]
    ) -> List[Mapping[str, Any]]:
        records = _rows(states)
        if len(records) != len(points):
            raise ValueError("states and points must have equal length")
        raw_bounds = self._raw(records)
        result: List[Mapping[str, Any]] = []
        for state, point_value, raw in zip(records, points, raw_bounds):
            runs = float(state.get("runs_so_far") or 0)
            if int(state.get("wickets_lost") or 0) >= 10 or int(state.get("balls_remaining") or 0) <= 0:
                result.append(
                    {
                        "p50": {"lower": runs, "upper": runs},
                        "p80": {"lower": runs, "upper": runs},
                    }
                )
                continue
            point = max(runs, float(point_value))
            lower50 = max(runs, min(point, raw["p50"]["lower"] - self.correction_50))
            upper50 = max(point, raw["p50"]["upper"] + self.correction_50)
            lower80 = max(runs, min(lower50, raw["p80"]["lower"] - self.correction_80))
            upper80 = max(upper50, raw["p80"]["upper"] + self.correction_80)
            result.append(
                {
                    "p50": {"lower": lower50, "upper": upper50},
                    "p80": {"lower": lower80, "upper": upper80},
                }
            )
        return result


def train_rolling_quantile_intervals(
    train_records: Any,
    validation_records: Any,
    *,
    features: Sequence[str],
    random_state: int = 20260731,
) -> QuantileConformalIntervalModel:
    """Fit quantiles on development data and calibrate with yearly OOF bounds."""

    train = _rows(train_records)
    validation = _rows(validation_records)
    years = sorted(
        {
            int(str(row.get("match_date") or row.get("date") or "0")[:4])
            for row in validation
            if str(row.get("match_date") or row.get("date") or "")[:4].isdigit()
        }
    )
    scores50: List[float] = []
    scores80: List[float] = []
    fold_years: Sequence[Optional[int]] = years if years else (None,)
    for year in fold_years:
        if year is None:
            fold_train = train
            fold_validation = validation
        else:
            fold_train = train + [
                row
                for row in validation
                if int(str(row.get("match_date") or row.get("date") or "0")[:4]) < year
            ]
            fold_validation = [
                row
                for row in validation
                if int(str(row.get("match_date") or row.get("date") or "0")[:4]) == year
            ]
        if not fold_validation:
            continue
        fold_model = QuantileConformalIntervalModel(
            features, random_state=random_state
        ).fit(fold_train)
        bounds = fold_model._raw(fold_validation)
        fold50, fold80 = fold_model.conformity_scores(fold_validation, bounds)
        scores50.extend(fold50)
        scores80.extend(fold80)
    model = QuantileConformalIntervalModel(features, random_state=random_state).fit(
        train + validation
    )
    model.set_conformal_scores(scores50, scores80)
    return model
