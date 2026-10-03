"""Explainable WASP-style resource and empirical win-probability baselines."""

from __future__ import annotations

import math
from collections import defaultdict
from typing import Any, DefaultDict, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple


def _rows(value: Any) -> List[Mapping[str, Any]]:
    if hasattr(value, "to_dict"):
        try:
            return value.to_dict(orient="records")
        except TypeError:
            pass
    if isinstance(value, Mapping):
        return [value]
    return list(value)


def _phase(row: Mapping[str, Any]) -> str:
    value = row.get("phase_absolute") or row.get("phase")
    if value:
        return str(value).casefold()
    legal = int(row.get("legal_balls_bowled") or 0)
    return "powerplay" if legal < 36 else ("middle" if legal < 96 else "death")


def _wicket_band(wickets_remaining: int) -> str:
    if wickets_remaining >= 8:
        return "8-10"
    if wickets_remaining >= 5:
        return "5-7"
    if wickets_remaining >= 3:
        return "3-4"
    return "0-2"


def _rrr_band(value: Any) -> str:
    try:
        rate = float(value)
    except (TypeError, ValueError):
        return "start"
    if not math.isfinite(rate):
        return "15+"
    if rate < 5:
        return "<5"
    if rate < 7:
        return "5-7"
    if rate < 9:
        return "7-9"
    if rate < 11:
        return "9-11"
    if rate < 15:
        return "11-15"
    return "15+"


class CurrentRunRateBaseline:
    """Project the current run rate, with a historical start-state fallback."""

    def __init__(self, start_score: float = 150.0) -> None:
        self.start_score = float(start_score)

    def fit(self, records: Any, y: Optional[Sequence[float]] = None, **_: Any) -> "CurrentRunRateBaseline":
        values: List[float] = []
        for index, row in enumerate(_rows(records)):
            if int(row.get("legal_balls_bowled") or 0) != 0:
                continue
            final = row.get("final_score")
            if final is not None:
                values.append(float(final))
            elif y is not None:
                values.append(float(row.get("runs_so_far") or 0) + float(y[index]))
        if values:
            self.start_score = sum(values) / len(values)
        return self

    def predict_one(self, row: Mapping[str, Any]) -> float:
        runs = float(row.get("runs_so_far") or 0)
        wickets = int(row.get("wickets_lost") or 0)
        remaining = max(0, int(row.get("balls_remaining") or 0))
        legal = int(row.get("legal_balls_bowled") or 0)
        if wickets >= 10 or remaining == 0:
            return runs
        if legal == 0:
            return max(runs, self.start_score)
        crr = float(row.get("current_run_rate") or runs * 6.0 / legal)
        return max(runs, runs + crr * remaining / 6.0)

    def predict(self, records: Any) -> List[float]:
        return [self.predict_one(row) for row in _rows(records)]


class ResourceTableRegressor:
    """Hierarchically shrunk remaining-runs table.

    Lookup order is global -> phase/wicket band -> six-ball bucket -> exact
    balls/wickets.  Each child is empirical-Bayes shrunk toward its parent.
    """

    def __init__(self, pseudo_count: float = 24.0) -> None:
        if pseudo_count < 0:
            raise ValueError("pseudo_count cannot be negative")
        self.pseudo_count = float(pseudo_count)
        self.stats: List[Dict[Tuple[Any, ...], Tuple[float, float]]] = []
        self.global_mean = 0.0

    @staticmethod
    def _keys(row: Mapping[str, Any]) -> Tuple[Tuple[Any, ...], ...]:
        balls = max(0, int(row.get("balls_remaining") or 0))
        wickets = max(0, int(row.get("wickets_remaining") or 0))
        return (
            (),
            (_phase(row), _wicket_band(wickets)),
            ((balls + 5) // 6, _wicket_band(wickets)),
            (balls, wickets),
        )

    def fit(
        self,
        records: Any,
        y: Optional[Sequence[float]] = None,
        sample_weight: Optional[Sequence[float]] = None,
    ) -> "ResourceTableRegressor":
        rows = _rows(records)
        totals: List[DefaultDict[Tuple[Any, ...], List[float]]] = [
            defaultdict(lambda: [0.0, 0.0]) for _ in range(4)
        ]
        for index, row in enumerate(rows):
            target = (
                float(y[index])
                if y is not None
                else float(
                    row.get("remaining_runs")
                    if row.get("remaining_runs") is not None
                    else float(row.get("final_score") or 0) - float(row.get("runs_so_far") or 0)
                )
            )
            weight = (
                float(sample_weight[index])
                if sample_weight is not None
                else float(row.get("sample_weight") or 1.0)
            )
            for level, key in enumerate(self._keys(row)):
                totals[level][key][0] += weight * max(0.0, target)
                totals[level][key][1] += weight
        self.stats = [
            {key: (value[0], value[1]) for key, value in level.items()}
            for level in totals
        ]
        total_sum, total_count = self.stats[0].get((), (0.0, 0.0))
        self.global_mean = total_sum / total_count if total_count else 0.0
        return self

    def predict_remaining_one(self, row: Mapping[str, Any]) -> float:
        if int(row.get("wickets_lost") or 0) >= 10 or int(row.get("balls_remaining") or 0) <= 0:
            return 0.0
        prediction = self.global_mean
        if not self.stats:
            return max(0.0, prediction)
        for level, key in enumerate(self._keys(row)):
            value = self.stats[level].get(key)
            if value is None or value[1] <= 0:
                continue
            observed = value[0] / value[1]
            if level == 0:
                prediction = observed
            else:
                prediction = (
                    value[1] * observed + self.pseudo_count * prediction
                ) / (value[1] + self.pseudo_count)
        return max(0.0, prediction)

    def predict_remaining(self, records: Any) -> List[float]:
        return [self.predict_remaining_one(row) for row in _rows(records)]

    def predict(self, records: Any) -> List[float]:
        rows = _rows(records)
        return [
            float(row.get("runs_so_far") or 0) + self.predict_remaining_one(row)
            for row in rows
        ]


class HierarchicalWinProbability:
    """Beta-smoothed empirical chase win probability."""

    def __init__(self, pseudo_count: float = 48.0) -> None:
        if pseudo_count < 0:
            raise ValueError("pseudo_count cannot be negative")
        self.pseudo_count = float(pseudo_count)
        self.stats: List[Dict[Tuple[Any, ...], Tuple[float, float]]] = []
        self.global_probability = 0.5

    @staticmethod
    def _keys(row: Mapping[str, Any]) -> Tuple[Tuple[Any, ...], ...]:
        balls = max(0, int(row.get("balls_remaining") or 0))
        wickets = max(0, int(row.get("wickets_remaining") or 0))
        return (
            (),
            (_phase(row),),
            (_phase(row), (balls + 5) // 6),
            (_phase(row), (balls + 5) // 6, wickets),
            (_phase(row), (balls + 5) // 6, wickets, _rrr_band(row.get("required_run_rate"))),
        )

    def fit(
        self,
        records: Any,
        y: Optional[Sequence[float]] = None,
        sample_weight: Optional[Sequence[float]] = None,
    ) -> "HierarchicalWinProbability":
        rows = _rows(records)
        totals: List[DefaultDict[Tuple[Any, ...], List[float]]] = [
            defaultdict(lambda: [0.0, 0.0]) for _ in range(5)
        ]
        for index, row in enumerate(rows):
            label = float(y[index]) if y is not None else float(row["chase_won"])
            weight = (
                float(sample_weight[index])
                if sample_weight is not None
                else float(row.get("sample_weight") or 1.0)
            )
            for level, key in enumerate(self._keys(row)):
                totals[level][key][0] += weight * label
                totals[level][key][1] += weight
        self.stats = [
            {key: (value[0], value[1]) for key, value in level.items()}
            for level in totals
        ]
        wins, count = self.stats[0].get((), (0.0, 0.0))
        self.global_probability = wins / count if count else 0.5
        return self

    def predict_one(self, row: Mapping[str, Any]) -> float:
        terminal = row.get("terminal_probability")
        if terminal is not None:
            value = float(terminal)
            if math.isfinite(value):
                return value
        prediction = self.global_probability
        if self.stats:
            for level, key in enumerate(self._keys(row)):
                value = self.stats[level].get(key)
                if value is None or value[1] <= 0:
                    continue
                observed = value[0] / value[1]
                if level == 0:
                    prediction = observed
                else:
                    prediction = (
                        value[1] * observed + self.pseudo_count * prediction
                    ) / (value[1] + self.pseudo_count)
        return min(1.0 - 1e-6, max(1e-6, prediction))

    def predict_proba(self, records: Any) -> List[List[float]]:
        probabilities = [self.predict_one(row) for row in _rows(records)]
        return [[1.0 - value, value] for value in probabilities]

    def predict(self, records: Any) -> List[float]:
        return [self.predict_one(row) for row in _rows(records)]
