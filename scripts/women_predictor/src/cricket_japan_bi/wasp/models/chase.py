"""Second-innings chase probability models, calibration and scenarios."""

from __future__ import annotations

import copy
import math
from dataclasses import dataclass
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

import numpy as np

from ..features.datasets import feature_names, numeric_matrix
from ..features.states import chase_terminal, phase_absolute, phase_relative
from .baselines import HierarchicalWinProbability, _rows


def _logit(value: float) -> float:
    probability = float(value)
    if not math.isfinite(probability):
        raise ValueError("calibration probability must be finite")
    probability = min(1.0 - 1e-6, max(1e-6, probability))
    return math.log(probability / (1.0 - probability))


def _sigmoid(value: float) -> float:
    if value >= 0:
        exp = math.exp(-value)
        return 1.0 / (1.0 + exp)
    exp = math.exp(value)
    return exp / (1.0 + exp)


class PlattCalibrator:
    """Small dependency-free logistic calibration on raw probability logits."""

    def __init__(self, slope: float = 1.0, intercept: float = 0.0) -> None:
        self.slope = float(slope)
        self.intercept = float(intercept)

    def fit(
        self,
        probabilities: Sequence[float],
        labels: Sequence[float],
        *,
        offset_only: bool = False,
        sample_weight: Optional[Sequence[float]] = None,
    ) -> "PlattCalibrator":
        x = np.asarray([_logit(value) for value in probabilities], dtype=np.float64)
        y = np.asarray(labels, dtype=np.float64)
        if len(x) == 0 or len(np.unique(y)) < 2:
            return self
        observation_weight = np.asarray(
            sample_weight if sample_weight is not None else np.ones(len(x)),
            dtype=np.float64,
        )
        if len(observation_weight) != len(x):
            raise ValueError("sample_weight must match probabilities")
        if offset_only:
            self.slope = 1.0
            # Fit only an intercept while retaining the incoming probability's
            # logit as a fixed offset.  Bound each Newton step and the final
            # intercept: highly repeated states from a small number of matches
            # can otherwise create near-separation and overflow.
            intercept = 0.0
            for _ in range(100):
                z = np.clip(x + intercept, -35.0, 35.0)
                p = 1.0 / (1.0 + np.exp(-z))
                gradient = float(np.sum((p - y) * observation_weight)) + 1e-2 * intercept
                hessian = float(
                    np.sum(p * (1.0 - p) * observation_weight)
                ) + 1e-2
                step = max(-5.0, min(5.0, gradient / hessian))
                intercept = max(-20.0, min(20.0, intercept - step))
                if abs(step) < 1e-7:
                    break
            self.intercept = float(intercept)
        else:
            # A regularized solver is substantially more stable than a raw
            # two-parameter Newton solve when validation probabilities are
            # close to complete separation.
            try:
                from sklearn.linear_model import LogisticRegression

                estimator = LogisticRegression(
                    C=1.0,
                    fit_intercept=True,
                    max_iter=1000,
                    solver="lbfgs",
                )
                estimator.fit(
                    x.reshape(-1, 1), y.astype(np.int8), sample_weight=observation_weight
                )
                slope = float(estimator.coef_[0, 0])
                intercept = float(estimator.intercept_[0])
                if math.isfinite(slope) and math.isfinite(intercept):
                    self.slope = slope
                    self.intercept = intercept
            except ImportError:  # pragma: no cover - sklearn is a train dependency
                pass
        return self

    def predict(self, probabilities: Sequence[float]) -> List[float]:
        return [
            _sigmoid(self.slope * _logit(value) + self.intercept)
            for value in probabilities
        ]


class SklearnChaseClassifier:
    def __init__(self, estimator: Any, features: Sequence[str], name: str) -> None:
        self.estimator = estimator
        self.features = tuple(features)
        self.name = name
        self.calibrator: Optional[PlattCalibrator] = None

    def fit(self, records: Any, y: Optional[Sequence[float]] = None) -> "SklearnChaseClassifier":
        rows = _rows(records)
        matrix, _ = numeric_matrix(rows, self.features)
        labels = np.asarray(y if y is not None else [row["chase_won"] for row in rows], dtype=np.int8)
        weights = np.asarray([float(row.get("sample_weight") or 1.0) for row in rows])
        try:
            if hasattr(self.estimator, "named_steps"):
                self.estimator.fit(matrix, labels, model__sample_weight=weights)
            else:
                self.estimator.fit(matrix, labels, sample_weight=weights)
        except TypeError:
            self.estimator.fit(matrix, labels)
        return self

    def raw_probability(self, records: Any) -> List[float]:
        rows = _rows(records)
        if not rows:
            return []
        matrix, _ = numeric_matrix(rows, self.features)
        raw = np.asarray(self.estimator.predict_proba(matrix), dtype=np.float64)[:, 1]
        return [float(value) for value in raw]

    def calibrate(self, records: Any, labels: Optional[Sequence[float]] = None) -> "SklearnChaseClassifier":
        rows = _rows(records)
        y = labels if labels is not None else [row["chase_won"] for row in rows]
        self.calibrator = PlattCalibrator().fit(
            self.raw_probability(rows),
            y,
            sample_weight=[float(row.get("sample_weight") or 1.0) for row in rows],
        )
        return self

    def predict(self, records: Any) -> List[float]:
        rows = _rows(records)
        raw = self.raw_probability(rows)
        probabilities = self.calibrator.predict(raw) if self.calibrator else raw
        result: List[float] = []
        for row, value in zip(rows, probabilities):
            terminal = row.get("terminal_probability")
            has_terminal = terminal is not None
            if isinstance(terminal, (float, np.floating)):
                has_terminal = math.isfinite(float(terminal))
            result.append(
                float(terminal)
                if has_terminal
                else min(1.0, max(0.0, float(value)))
            )
        return result

    def predict_proba(self, records: Any) -> List[List[float]]:
        values = self.predict(records)
        return [[1.0 - value, value] for value in values]


@dataclass(frozen=True)
class ChaseCandidateScore:
    name: str
    match_macro_brier: float
    match_macro_log_loss: float
    ece: float


@dataclass
class ChaseSelection:
    selected_name: str
    model: Any
    candidates: Sequence[ChaseCandidateScore]
    feature_set: str
    validation_predictions: Sequence[float]


def _make_ml_candidates(*, context: bool, random_state: int) -> List[Tuple[str, Any]]:
    try:
        from sklearn.ensemble import HistGradientBoostingClassifier
        from sklearn.linear_model import LogisticRegression
        from sklearn.pipeline import Pipeline
        from sklearn.preprocessing import StandardScaler
    except ImportError:
        return []
    names = feature_names("chase", context=context)
    logistic = Pipeline(
        [
            ("scale", StandardScaler()),
            ("model", LogisticRegression(C=0.2, max_iter=1000, solver="lbfgs")),
        ]
    )
    result: List[Tuple[str, Any]] = [
        ("logistic", SklearnChaseClassifier(logistic, names, "logistic"))
    ]
    monotonic = [0] * len(names)
    for feature, direction in (
        ("runs_required", -1),
        ("balls_remaining", 1),
        ("wickets_remaining", 1),
    ):
        if feature in names:
            monotonic[names.index(feature)] = direction
    kwargs = {
        "loss": "log_loss",
        "learning_rate": 0.06,
        "max_iter": 250,
        "l2_regularization": 2.0,
        "random_state": random_state,
    }
    try:
        hgb = HistGradientBoostingClassifier(monotonic_cst=monotonic, **kwargs)
    except TypeError:
        hgb = HistGradientBoostingClassifier(**kwargs)
    result.append(("hgb", SklearnChaseClassifier(hgb, names, "hgb")))
    return result


def _metrics(rows: Sequence[Mapping[str, Any]], values: Sequence[float], name: str) -> ChaseCandidateScore:
    by_match_brier: Dict[str, List[float]] = {}
    by_match_log: Dict[str, List[float]] = {}
    labels: List[float] = []
    clipped_values: List[float] = []
    for row, value in zip(rows, values):
        label = float(row["chase_won"])
        probability = min(1.0 - 1e-6, max(1e-6, float(value)))
        match_id = str(row.get("match_id") or "")
        by_match_brier.setdefault(match_id, []).append((probability - label) ** 2)
        by_match_log.setdefault(match_id, []).append(
            -(label * math.log(probability) + (1.0 - label) * math.log(1.0 - probability))
        )
        labels.append(label)
        clipped_values.append(probability)
    brier = float(np.mean([np.mean(items) for items in by_match_brier.values()]))
    log_loss = float(np.mean([np.mean(items) for items in by_match_log.values()]))
    order = np.argsort(np.asarray(clipped_values))
    ece = 0.0
    for indices in np.array_split(order, min(10, len(order))):
        if len(indices):
            ece += len(indices) / len(order) * abs(
                float(np.mean(np.asarray(clipped_values)[indices]))
                - float(np.mean(np.asarray(labels)[indices]))
            )
    return ChaseCandidateScore(name, brier, log_loss, ece)


def train_chase_candidates(
    train_records: Any,
    validation_records: Any,
    *,
    context: bool = False,
    random_state: int = 20260731,
) -> ChaseSelection:
    train = _rows(train_records)
    validation = _rows(validation_records)
    if not train or not validation:
        raise ValueError("chase training and validation data must not be empty")
    candidates: List[Tuple[str, Any]] = []
    for pseudo in (12.0, 24.0, 48.0, 96.0):
        model = HierarchicalWinProbability(pseudo_count=pseudo)
        candidates.append(("empirical_{:g}".format(pseudo), model))
    candidates.extend(_make_ml_candidates(context=context, random_state=random_state))
    scored: List[Tuple[ChaseCandidateScore, Any, List[float]]] = []
    years = sorted(
        {
            int(str(row.get("match_date") or row.get("date") or "0")[:4])
            for row in validation
            if str(row.get("match_date") or row.get("date") or "")[:4].isdigit()
        }
    )
    labels = [float(row["chase_won"]) for row in validation]
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
            except ValueError:
                failed = True
                break
            values = model.predict([validation[index] for index in indices])
            for index, value in zip(indices, values):
                oof[index] = float(value)
        if failed or any(value is None for value in oof):
            continue
        raw_oof = [float(value) for value in oof if value is not None]
        calibrator = (
            PlattCalibrator().fit(
                raw_oof,
                labels,
                sample_weight=[
                    float(row.get("sample_weight") or 1.0) for row in validation
                ],
            )
            if name == "hgb"
            else None
        )
        values = calibrator.predict(raw_oof) if calibrator is not None else raw_oof
        final_model = copy.deepcopy(template)
        try:
            final_model.fit(train + validation)
        except ValueError:
            continue
        if isinstance(final_model, SklearnChaseClassifier):
            final_model.calibrator = calibrator
        scored.append((_metrics(validation, values, name), final_model, values))
    best_brier = min(item[0].match_macro_brier for item in scored)
    best_log = min(item[0].match_macro_log_loss for item in scored)
    best_ece = min(item[0].ece for item in scored)
    admissible = [
        item
        for item in scored
        if item[0].match_macro_log_loss <= best_log * 1.01
        and item[0].ece <= best_ece + 0.02
    ] or scored
    within = [item for item in admissible if item[0].match_macro_brier <= best_brier + 0.002] or admissible

    def priority(name: str) -> Tuple[int, str]:
        return (
            0 if name.startswith("empirical") else 1 if name == "logistic" else 2,
            name,
        )

    selected_score, selected_model, selected_oof = min(
        within, key=lambda item: priority(item[0].name)
    )
    return ChaseSelection(
        selected_name=selected_score.name,
        model=selected_model,
        candidates=tuple(item[0] for item in scored),
        feature_set="model_1" if context else "model_0",
        validation_predictions=tuple(selected_oof),
    )


def predict_win_probability(model: Any, state: Mapping[str, Any]) -> Optional[float]:
    target = int(state.get("target") or state.get("target_runs") or 0)
    score = int(state.get("runs_so_far") or state.get("current_score") or 0)
    wickets = int(state.get("wickets_lost") or state.get("wickets") or 0)
    balls = int(state.get("balls_remaining") or 0)
    status, terminal = chase_terminal(
        score=score, target=target, wickets_lost=wickets, balls_remaining=balls
    )
    if status == "tied_regulation":
        return None
    if terminal is not None:
        return terminal
    if hasattr(model, "predict"):
        return min(1.0, max(0.0, float(model.predict([state])[0])))
    return min(1.0, max(0.0, float(model.predict_proba([state])[0][1])))


def next_ball_scenarios(model: Any, state: Mapping[str, Any]) -> List[Mapping[str, Any]]:
    """Enumerate standard outcomes for the next *legal* ball."""

    scenarios: List[Mapping[str, Any]] = []
    for label, runs, wicket in (
        ("0 runs", 0, False),
        ("1 run", 1, False),
        ("2 runs", 2, False),
        ("3 runs", 3, False),
        ("4 runs", 4, False),
        ("6 runs", 6, False),
        ("wicket", 0, True),
    ):
        child = dict(state)
        child["runs_so_far"] = int(state.get("runs_so_far") or 0) + runs
        child["wickets_lost"] = int(state.get("wickets_lost") or 0) + int(wicket)
        child["wickets_remaining"] = max(0, 10 - child["wickets_lost"])
        child["balls_remaining"] = max(0, int(state.get("balls_remaining") or 0) - 1)
        child["legal_balls_bowled"] = int(state.get("legal_balls_bowled") or 0) + 1
        ball_limit = max(
            1,
            int(
                state.get("innings_ball_limit")
                or child["legal_balls_bowled"] + child["balls_remaining"]
            ),
        )
        child["innings_ball_limit"] = ball_limit
        child["current_run_rate"] = (
            child["runs_so_far"] * 6.0 / child["legal_balls_bowled"]
            if child["legal_balls_bowled"]
            else 0.0
        )
        child["progress"] = min(
            1.0, child["legal_balls_bowled"] / float(ball_limit)
        )
        child["phase_absolute"] = phase_absolute(child["legal_balls_bowled"])
        child["phase_relative"] = phase_relative(
            child["legal_balls_bowled"], ball_limit
        )
        target = int(state.get("target") or state.get("target_runs") or 0)
        child["runs_required"] = max(0, target - child["runs_so_far"])
        child["required_run_rate"] = (
            child["runs_required"] * 6.0 / child["balls_remaining"]
            if child["runs_required"] and child["balls_remaining"]
            else (0.0 if child["runs_required"] == 0 else math.inf)
        )
        child["rrr_minus_crr"] = (
            child["required_run_rate"] - child["current_run_rate"]
        )
        probability = predict_win_probability(model, child)
        scenarios.append(
            {
                "label": label,
                "runs": runs,
                "wicket": wicket,
                "win_probability": probability,
            }
        )
    return scenarios
