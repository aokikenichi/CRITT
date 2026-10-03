"""Role-specific, gated Japan corrections fitted only from OOF residuals."""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

import numpy as np

from .chase import PlattCalibrator
from .contracts import CorrectionStatus


JAPAN = "Japan"


def first_innings_role(row: Mapping[str, Any]) -> Optional[str]:
    if str(row.get("batting_team") or "") == JAPAN:
        return "japan_batting"
    if str(row.get("bowling_team") or "") == JAPAN:
        return "japan_bowling"
    return None


def chase_role(row: Mapping[str, Any]) -> Optional[str]:
    if str(row.get("batting_team") or row.get("chasing_team") or "") == JAPAN:
        return "japan_chasing"
    if str(row.get("bowling_team") or row.get("defending_team") or "") == JAPAN:
        return "japan_defending"
    return None


def _bootstrap_ci(
    values_by_match: Mapping[str, Sequence[float]],
    *,
    iterations: int = 500,
    random_state: int = 20260731,
) -> Tuple[Tuple[float, float], Tuple[float, float]]:
    if not values_by_match:
        return (0.0, 0.0), (0.0, 0.0)
    match_means = {
        str(match_id): float(np.mean(values))
        for match_id, values in values_by_match.items()
        if values
    }
    identifiers = sorted(match_means)
    rng = np.random.default_rng(random_state)
    estimates = []
    for _ in range(iterations):
        sampled = rng.choice(identifiers, size=len(identifiers), replace=True)
        estimates.append(float(np.mean([match_means[str(key)] for key in sampled])))
    return (
        (float(np.quantile(estimates, 0.10)), float(np.quantile(estimates, 0.90))),
        (float(np.quantile(estimates, 0.025)), float(np.quantile(estimates, 0.975))),
    )


@dataclass
class JapanRoleCorrection:
    role: str
    kind: str
    enabled: bool
    match_count: int
    offset: float = 0.0
    calibrator: Optional[PlattCalibrator] = None
    fallback_reason: Optional[str] = None
    ci80: Tuple[float, float] = (0.0, 0.0)
    ci95: Tuple[float, float] = (0.0, 0.0)
    gate_details: Mapping[str, Any] = field(default_factory=dict)

    def apply(self, value: float) -> float:
        if not self.enabled:
            return float(value)
        if self.kind == "score":
            return max(0.0, float(value) + self.offset)
        if self.calibrator is not None:
            return min(1.0, max(0.0, self.calibrator.predict([float(value)])[0]))
        return min(1.0, max(0.0, float(value)))

    def status(self, requested: bool, applicable: bool = True) -> CorrectionStatus:
        return CorrectionStatus(
            requested=requested,
            applicable=applicable,
            applied=bool(requested and applicable and self.enabled),
            fallback_reason=(
                None if requested and applicable and self.enabled else self.fallback_reason or "gate_not_passed"
            ),
            match_count=self.match_count,
            ci80=self.ci80,
            ci95=self.ci95,
        )


def fit_score_correction(
    records: Sequence[Mapping[str, Any]],
    predictions: Sequence[float],
    *,
    role: str,
    minimum_history_matches: int = 12,
    minimum_gate_matches: int = 8,
    random_state: int = 20260731,
) -> JapanRoleCorrection:
    """Fit an OOF residual offset and activate only after the 2025 gate improves."""

    history_by_match: Dict[str, List[float]] = {}
    gate: List[Tuple[str, float, float, float]] = []
    for row, prediction in zip(records, predictions):
        if first_innings_role(row) != role:
            continue
        year = int(str(row.get("match_date") or row.get("date") or "0000")[:4])
        truth = float(row.get("final_score") or row.get("final_runs") or 0)
        match_id = str(row.get("match_id") or "")
        if year <= 2024:
            history_by_match.setdefault(match_id, []).append(truth - float(prediction))
    history_matches = set(history_by_match)
    if len(history_matches) < minimum_history_matches:
        return JapanRoleCorrection(
            role, "score", False, len(history_matches), fallback_reason="insufficient_history"
        )
    # Ridge-to-zero partial pooling: eight pseudo-observations at no offset.
    match_residuals = [float(np.mean(values)) for values in history_by_match.values()]
    offset = float(sum(match_residuals) / (len(match_residuals) + 8.0))
    for row, prediction in zip(records, predictions):
        if first_innings_role(row) != role:
            continue
        year = int(str(row.get("match_date") or row.get("date") or "0000")[:4])
        if year != 2025:
            continue
        truth = float(row.get("final_score") or row.get("final_runs") or 0)
        gate.append((str(row.get("match_id") or ""), truth, float(prediction), float(prediction) + offset))
    gate_matches = {item[0] for item in gate}
    if len(gate_matches) < minimum_gate_matches:
        return JapanRoleCorrection(
            role, "score", False, len(history_matches), offset=offset, fallback_reason="insufficient_gate_matches"
        )
    by_match: Dict[str, List[float]] = {}
    for match_id, truth, base, corrected in gate:
        by_match.setdefault(match_id, []).append(abs(corrected - truth) - abs(base - truth))
    ci80, ci95 = _bootstrap_ci(by_match, random_state=random_state)
    base_squared: Dict[str, List[float]] = {}
    corrected_squared: Dict[str, List[float]] = {}
    for match_id, truth, base, corrected in gate:
        base_squared.setdefault(match_id, []).append((base - truth) ** 2)
        corrected_squared.setdefault(match_id, []).append((corrected - truth) ** 2)
    base_rmse = float(
        np.mean([math.sqrt(float(np.mean(values))) for values in base_squared.values()])
    )
    corrected_rmse = float(
        np.mean(
            [math.sqrt(float(np.mean(values))) for values in corrected_squared.values()]
        )
    )
    enabled = ci80[1] < 0.0 and corrected_rmse <= base_rmse
    return JapanRoleCorrection(
        role=role,
        kind="score",
        enabled=enabled,
        match_count=len(history_matches),
        offset=offset,
        fallback_reason=None if enabled else "activation_gate_failed",
        ci80=ci80,
        ci95=ci95,
        gate_details={
            "gate_matches": len(gate_matches),
            "base_match_macro_rmse": base_rmse,
            "corrected_match_macro_rmse": corrected_rmse,
        },
    )


def _binary_metrics(
    labels: Sequence[float],
    probabilities: Sequence[float],
    match_ids: Optional[Sequence[str]] = None,
    sample_weight: Optional[Sequence[float]] = None,
) -> Tuple[float, float, float]:
    y = np.asarray(labels, dtype=np.float64)
    p = np.clip(np.asarray(probabilities, dtype=np.float64), 1e-6, 1 - 1e-6)
    brier_values = (p - y) ** 2
    log_values = -(y * np.log(p) + (1 - y) * np.log(1 - p))
    if match_ids is not None:
        grouped_brier: Dict[str, List[float]] = {}
        grouped_log: Dict[str, List[float]] = {}
        for match_id, brier_value, log_value in zip(match_ids, brier_values, log_values):
            grouped_brier.setdefault(str(match_id), []).append(float(brier_value))
            grouped_log.setdefault(str(match_id), []).append(float(log_value))
        brier = float(np.mean([np.mean(values) for values in grouped_brier.values()]))
        log = float(np.mean([np.mean(values) for values in grouped_log.values()]))
    else:
        brier = float(np.mean(brier_values))
        log = float(np.mean(log_values))
    bins = np.array_split(np.argsort(p), min(10, len(p)))
    weights = np.asarray(
        sample_weight if sample_weight is not None else np.ones(len(p)),
        dtype=np.float64,
    )
    total_weight = float(np.sum(weights))
    ece = sum(
        float(np.sum(weights[idx])) / total_weight
        * abs(
            float(np.average(p[idx], weights=weights[idx]))
            - float(np.average(y[idx], weights=weights[idx]))
        )
        for idx in bins
        if len(idx) and float(np.sum(weights[idx])) > 0
    )
    return brier, log, ece


def fit_chase_correction(
    records: Sequence[Mapping[str, Any]],
    probabilities: Sequence[float],
    *,
    role: str,
    minimum_history_matches: int = 12,
    minimum_gate_matches: int = 8,
    random_state: int = 20260731,
) -> JapanRoleCorrection:
    history_p: List[float] = []
    history_y: List[float] = []
    history_weight: List[float] = []
    history_matches = set()
    history_outcomes: Dict[str, float] = {}
    for row, probability in zip(records, probabilities):
        if chase_role(row) != role:
            continue
        year = int(str(row.get("match_date") or row.get("date") or "0000")[:4])
        if year <= 2024:
            history_p.append(float(probability))
            history_y.append(float(row["chase_won"]))
            history_weight.append(float(row.get("sample_weight") or 1.0))
            match_id = str(row.get("match_id") or "")
            history_matches.add(match_id)
            history_outcomes[match_id] = float(row["chase_won"])
    if len(history_matches) < minimum_history_matches:
        return JapanRoleCorrection(role, "probability", False, len(history_matches), fallback_reason="insufficient_history")
    history_wins = sum(history_outcomes.values())
    if history_wins < 3 or len(history_outcomes) - history_wins < 3:
        return JapanRoleCorrection(role, "probability", False, len(history_matches), fallback_reason="insufficient_class_balance")
    calibrator = PlattCalibrator().fit(
        history_p,
        history_y,
        offset_only=True,
        sample_weight=history_weight,
    )
    gate_rows: List[Tuple[str, float, float, float]] = []
    for row, probability in zip(records, probabilities):
        if chase_role(row) != role:
            continue
        year = int(str(row.get("match_date") or row.get("date") or "0000")[:4])
        if year == 2025:
            gate_rows.append(
                (
                    str(row.get("match_id") or ""),
                    float(row["chase_won"]),
                    float(probability),
                    calibrator.predict([float(probability)])[0],
                )
            )
    gate_matches = {item[0] for item in gate_rows}
    if len(gate_matches) < minimum_gate_matches:
        return JapanRoleCorrection(role, "probability", False, len(history_matches), calibrator=calibrator, fallback_reason="insufficient_gate_matches")
    labels = [item[1] for item in gate_rows]
    base = [item[2] for item in gate_rows]
    corrected = [item[3] for item in gate_rows]
    gate_outcomes = {match_id: label for match_id, label, _, _ in gate_rows}
    gate_wins = sum(gate_outcomes.values())
    if gate_wins < 3 or len(gate_outcomes) - gate_wins < 3:
        return JapanRoleCorrection(role, "probability", False, len(history_matches), calibrator=calibrator, fallback_reason="insufficient_gate_class_balance")
    gate_ids = [item[0] for item in gate_rows]
    gate_weights = [
        float(row.get("sample_weight") or 1.0)
        for row, probability in zip(records, probabilities)
        if chase_role(row) == role
        and int(str(row.get("match_date") or row.get("date") or "0000")[:4]) == 2025
    ]
    base_metrics = _binary_metrics(labels, base, gate_ids, gate_weights)
    corrected_metrics = _binary_metrics(
        labels, corrected, gate_ids, gate_weights
    )
    differences: Dict[str, List[float]] = {}
    for match_id, label, p_base, p_corrected in gate_rows:
        differences.setdefault(match_id, []).append((p_corrected - label) ** 2 - (p_base - label) ** 2)
    ci80, ci95 = _bootstrap_ci(differences, random_state=random_state)
    enabled = (
        ci80[1] < 0.0
        and corrected_metrics[1] < base_metrics[1]
        and corrected_metrics[2] <= base_metrics[2] + 0.02
    )
    return JapanRoleCorrection(
        role=role,
        kind="probability",
        enabled=enabled,
        match_count=len(history_matches),
        calibrator=calibrator,
        fallback_reason=None if enabled else "activation_gate_failed",
        ci80=ci80,
        ci95=ci95,
        gate_details={
            "gate_matches": len(gate_matches),
            "gate_wins": int(gate_wins),
            "gate_losses": int(len(gate_outcomes) - gate_wins),
            "base_match_macro_brier": base_metrics[0],
            "corrected_match_macro_brier": corrected_metrics[0],
            "base_match_macro_log_loss": base_metrics[1],
            "corrected_match_macro_log_loss": corrected_metrics[1],
            "base_ece": base_metrics[2],
            "corrected_ece": corrected_metrics[2],
        },
    )


def correction_for_role(
    corrections: Mapping[str, JapanRoleCorrection], role: Optional[str]
) -> Optional[JapanRoleCorrection]:
    return corrections.get(role) if role else None
