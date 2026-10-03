"""First-innings final-score candidate training and inference."""

from __future__ import annotations

import copy
from dataclasses import dataclass
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

import numpy as np

from ..features.datasets import feature_names, numeric_matrix
from .baselines import CurrentRunRateBaseline, ResourceTableRegressor, _rows


def _sklearn_components() -> Mapping[str, Any]:
    try:
        from sklearn.ensemble import HistGradientBoostingRegressor
        from sklearn.linear_model import Ridge, TweedieRegressor
        from sklearn.pipeline import Pipeline
        from sklearn.preprocessing import StandardScaler
    except ImportError as exc:  # pragma: no cover - exercised in minimal installs
        raise RuntimeError(
            "scikit-learn is required to train ML WASP-style candidates"
        ) from exc
    return {
        "hgb": HistGradientBoostingRegressor,
        "ridge": Ridge,
        "tweedie": TweedieRegressor,
        "pipeline": Pipeline,
        "scaler": StandardScaler,
    }


class SklearnRemainingRegressor:
    """Map state records to a scikit-learn remaining-runs estimator."""

    def __init__(self, estimator: Any, features: Sequence[str], name: str) -> None:
        self.estimator = estimator
        self.features = tuple(features)
        self.name = name

    def fit(self, records: Any, y: Optional[Sequence[float]] = None) -> "SklearnRemainingRegressor":
        rows = _rows(records)
        matrix, _ = numeric_matrix(rows, self.features)
        target = np.asarray(
            y if y is not None else [float(row["remaining_runs"]) for row in rows],
            dtype=np.float64,
        )
        weights = np.asarray(
            [float(row.get("sample_weight") or 1.0) for row in rows], dtype=np.float64
        )
        try:
            if hasattr(self.estimator, "named_steps"):
                self.estimator.fit(matrix, target, model__sample_weight=weights)
            else:
                self.estimator.fit(matrix, target, sample_weight=weights)
        except TypeError:
            self.estimator.fit(matrix, target)
        return self

    def predict_remaining(self, records: Any) -> List[float]:
        rows = _rows(records)
        if not rows:
            return []
        matrix, _ = numeric_matrix(rows, self.features)
        values = np.asarray(self.estimator.predict(matrix), dtype=np.float64)
        return [max(0.0, float(value)) for value in values]

    def predict_remaining_one(self, row: Mapping[str, Any]) -> float:
        return self.predict_remaining([row])[0]

    def predict(self, records: Any) -> List[float]:
        rows = _rows(records)
        remaining = self.predict_remaining(rows)
        return [
            max(float(row.get("runs_so_far") or 0), float(row.get("runs_so_far") or 0) + value)
            if int(row.get("wickets_lost") or 0) < 10 and int(row.get("balls_remaining") or 0) > 0
            else float(row.get("runs_so_far") or 0)
            for row, value in zip(rows, remaining)
        ]


@dataclass(frozen=True)
class CandidateScore:
    name: str
    match_macro_mae: float
    match_macro_rmse: float
    phase_mae: Mapping[str, float]


@dataclass
class FirstInningsSelection:
    selected_name: str
    model: Any
    candidates: Sequence[CandidateScore]
    feature_set: str
    validation_predictions: Sequence[float]


def _make_ml_candidates(*, context: bool, random_state: int) -> List[Tuple[str, Any]]:
    try:
        parts = _sklearn_components()
    except RuntimeError:
        return []
    names = feature_names("first_innings", context=context)
    Pipeline = parts["pipeline"]
    StandardScaler = parts["scaler"]
    Ridge = parts["ridge"]
    Tweedie = parts["tweedie"]
    HGB = parts["hgb"]
    candidates: List[Tuple[str, Any]] = []
    ridge = Pipeline([("scale", StandardScaler()), ("model", Ridge(alpha=10.0))])
    candidates.append(("ridge", SklearnRemainingRegressor(ridge, names, "ridge")))
    for power in (1.1, 1.5):
        tweedie = Pipeline(
            [
                ("scale", StandardScaler()),
                (
                    "model",
                    Tweedie(alpha=1.0, power=power, link="log", max_iter=1000),
                ),
            ]
        )
        candidates.append(
            (
                "tweedie_{:.1f}".format(power),
                SklearnRemainingRegressor(tweedie, names, "tweedie"),
            )
        )
    monotonic = [0] * len(names)
    for feature in ("balls_remaining", "wickets_remaining"):
        if feature in names:
            monotonic[names.index(feature)] = 1
    kwargs = {
        "loss": "poisson",
        "learning_rate": 0.06,
        "max_iter": 250,
        "l2_regularization": 2.0,
        "random_state": random_state,
    }
    try:
        hgb = HGB(monotonic_cst=monotonic, **kwargs)
    except TypeError:  # older supported sklearn
        hgb = HGB(**kwargs)
    candidates.append(("hgb", SklearnRemainingRegressor(hgb, names, "hgb")))
    return candidates


def _macro_errors(rows: Sequence[Mapping[str, Any]], predicted: Sequence[float]) -> CandidateScore:
    by_match: Dict[str, List[float]] = {}
    squared: Dict[str, List[float]] = {}
    by_phase: Dict[str, List[float]] = {}
    for row, value in zip(rows, predicted):
        truth = float(row.get("final_score") or row.get("final_runs") or 0)
        error = abs(float(value) - truth)
        match_id = str(row.get("match_id") or "")
        by_match.setdefault(match_id, []).append(error)
        squared.setdefault(match_id, []).append((float(value) - truth) ** 2)
        by_phase.setdefault(str(row.get("phase_absolute") or "unknown"), []).append(error)
    mae = float(np.mean([np.mean(values) for values in by_match.values()])) if by_match else float("nan")
    rmse = (
        float(np.mean([np.sqrt(np.mean(values)) for values in squared.values()]))
        if squared
        else float("nan")
    )
    return CandidateScore(
        name="",
        match_macro_mae=mae,
        match_macro_rmse=rmse,
        phase_mae={key: float(np.mean(value)) for key, value in sorted(by_phase.items())},
    )


def train_first_innings_candidates(
    train_records: Any,
    validation_records: Any,
    *,
    context: bool = False,
    random_state: int = 20260731,
) -> FirstInningsSelection:
    """Fit candidates and select by match-macro MAE with simplicity tie-break."""

    train = _rows(train_records)
    validation = _rows(validation_records)
    if not train:
        raise ValueError("first-innings training data is empty")
    if not validation:
        raise ValueError("first-innings validation data is empty")
    candidates: List[Tuple[str, Any]] = []
    candidates.append(("current_run_rate", CurrentRunRateBaseline()))
    for pseudo_count in (12.0, 24.0, 48.0, 96.0):
        resource = ResourceTableRegressor(pseudo_count=pseudo_count)
        candidates.append(("resource_{:g}".format(pseudo_count), resource))
    candidates.extend(_make_ml_candidates(context=context, random_state=random_state))
    scored: List[Tuple[CandidateScore, Any, List[float]]] = []

    years = sorted(
        {
            int(str(row.get("match_date") or row.get("date") or "0")[:4])
            for row in validation
            if str(row.get("match_date") or row.get("date") or "")[:4].isdigit()
        }
    )
    for name, template in candidates:
        oof: List[Optional[float]] = [None] * len(validation)
        fold_years: Sequence[Optional[int]] = years if years else (None,)
        failed = False
        for year in fold_years:
            if year is None:
                fold_train = train
                indices = list(range(len(validation)))
            else:
                fold_train = train + [
                    row
                    for row in validation
                    if int(str(row.get("match_date") or row.get("date") or "0")[:4]) < year
                ]
                indices = [
                    index
                    for index, row in enumerate(validation)
                    if int(str(row.get("match_date") or row.get("date") or "0")[:4]) == year
                ]
            if not indices:
                continue
            model = copy.deepcopy(template)
            try:
                model.fit(fold_train)
            except (ValueError, FloatingPointError):
                failed = True
                break
            values = model.predict([validation[index] for index in indices])
            for index, value in zip(indices, values):
                oof[index] = float(value)
        if failed or any(value is None for value in oof):
            continue
        predicted = [float(value) for value in oof if value is not None]
        score = _macro_errors(validation, predicted)
        score = CandidateScore(
            name=name,
            match_macro_mae=score.match_macro_mae,
            match_macro_rmse=score.match_macro_rmse,
            phase_mae=score.phase_mae,
        )
        final_model = copy.deepcopy(template)
        try:
            final_model.fit(train + validation)
        except (ValueError, FloatingPointError):
            continue
        scored.append((score, final_model, predicted))
    best = min(score.match_macro_mae for score, _, _ in scored)
    # Candidates inside one percent of the best use the plan's simplicity order.
    def priority(name: str) -> Tuple[int, str]:
        if name.startswith("resource"):
            return (0, name)
        if name == "ridge":
            return (1, name)
        if name.startswith("tweedie"):
            return (2, name)
        if name == "hgb":
            return (3, name)
        return (4, name)

    eligible = [item for item in scored if item[0].match_macro_mae <= best * 1.01]
    selected_score, selected_model, selected_oof = min(
        eligible, key=lambda item: priority(item[0].name)
    )
    return FirstInningsSelection(
        selected_name=selected_score.name,
        model=selected_model,
        candidates=tuple(score for score, _, _ in scored),
        feature_set="model_1" if context else "model_0",
        validation_predictions=tuple(selected_oof),
    )


def predict_final_score(model: Any, state: Mapping[str, Any]) -> float:
    """Predict final score while applying deterministic terminal handling."""

    runs = float(state.get("runs_so_far") or 0)
    if int(state.get("wickets_lost") or 0) >= 10 or int(state.get("balls_remaining") or 0) <= 0:
        return runs
    value = model.predict([state])
    if isinstance(value, np.ndarray):
        value = value.tolist()
    return max(runs, float(value[0]))
