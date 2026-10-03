"""Model-ready record construction from normalized WASP states."""

from __future__ import annotations

import math
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple


STATE_FEATURES_FIRST = (
    "runs_so_far",
    "wickets_lost",
    "wickets_remaining",
    "legal_balls_bowled",
    "balls_remaining",
    "innings_ball_limit",
    "current_run_rate",
    "progress",
)
STATE_FEATURES_CHASE = STATE_FEATURES_FIRST + (
    "target",
    "runs_required",
    "required_run_rate",
    "rrr_minus_crr",
)
CONTEXT_FEATURES = (
    "elo_diff",
    "batting_form_delta",
    "bowling_suppression_delta",
    "venue_prior",
    "venue_sample_count",
    "team_cold_start",
    "opponent_cold_start",
    "era_trend",
    "batting_team_won_toss",
)


def _records(value: Any) -> List[Dict[str, Any]]:
    if value is None:
        return []
    if hasattr(value, "to_dict"):
        try:
            return [dict(row) for row in value.to_dict(orient="records")]
        except TypeError:
            pass
    return [dict(row) for row in value]


def _truthy(value: Any, default: bool = True) -> bool:
    if value is None:
        return default
    if isinstance(value, str):
        return value.casefold() not in {"", "0", "false", "no", "none"}
    return bool(value)


def attach_prematch_features(
    states: Any, prematch_features: Any
) -> List[Mapping[str, Any]]:
    """Attach the batting team's pre-date snapshot to each state."""

    snapshots = {
        (str(row.get("match_id") or ""), str(row.get("team") or "")): row
        for row in _records(prematch_features)
    }
    result: List[Mapping[str, Any]] = []
    for row in _records(states):
        snapshot = snapshots.get(
            (str(row.get("match_id") or ""), str(row.get("batting_team") or "")),
            {},
        )
        merged = dict(row)
        for key in CONTEXT_FEATURES:
            merged.setdefault(key, snapshot.get(key))
        result.append(merged)
    return result


def _apply_match_weights(rows: List[Dict[str, Any]]) -> None:
    counts: Dict[str, int] = {}
    for row in rows:
        match_id = str(row.get("match_id") or "")
        counts[match_id] = counts.get(match_id, 0) + 1
    for row in rows:
        row["sample_weight"] = 1.0 / counts[str(row.get("match_id") or "")]


def build_first_innings_dataset(
    states: Any,
    *,
    include_reduced: bool = False,
    eligible_only: bool = True,
) -> List[Mapping[str, Any]]:
    """Return first-innings states labelled with remaining runs."""

    result: List[Dict[str, Any]] = []
    for row in _records(states):
        if int(row.get("innings") or 0) != 1:
            continue
        if eligible_only and not _truthy(row.get("first_innings_eligible"), True):
            continue
        if not include_reduced and _truthy(row.get("is_reduced_match"), False):
            continue
        final_score = row.get("final_score")
        if final_score is None:
            final_score = row.get("final_runs")
        if final_score is None:
            continue
        record = dict(row)
        record["remaining_runs"] = max(
            0.0, float(final_score) - float(row.get("runs_so_far") or 0)
        )
        result.append(record)
    _apply_match_weights(result)
    return result


def build_chase_dataset(
    states: Any,
    *,
    include_reduced: bool = False,
    eligible_only: bool = True,
    include_terminal: bool = False,
) -> List[Mapping[str, Any]]:
    """Return binary-labelled chase states, excluding regulation ties."""

    result: List[Dict[str, Any]] = []
    for row in _records(states):
        if int(row.get("innings") or 0) != 2:
            continue
        if eligible_only and not _truthy(row.get("chase_eligible"), True):
            continue
        if not include_reduced and _truthy(row.get("is_reduced_match"), False):
            continue
        terminal_status = str(row.get("terminal_status") or "").strip().casefold()
        if terminal_status == "tied_regulation":
            continue
        terminal_probability = row.get("terminal_probability")
        has_terminal_probability = terminal_probability is not None and not (
            isinstance(terminal_probability, float)
            and not math.isfinite(terminal_probability)
        )
        is_terminal = (
            has_terminal_probability
            or terminal_status
            in {
                "won",
                "lost",
                "chase_won",
                "chase_lost",
                "target_reached",
                "all_out",
                "quota_reached",
            }
        )
        if not include_terminal and is_terminal:
            continue
        label = row.get("chase_won")
        if label is None:
            continue
        record = dict(row)
        record["chase_won"] = int(bool(label))
        result.append(record)
    _apply_match_weights(result)
    return result


def feature_names(model: str, *, context: bool = False) -> Tuple[str, ...]:
    base = STATE_FEATURES_FIRST if model == "first_innings" else STATE_FEATURES_CHASE
    return base + CONTEXT_FEATURES if context else base


def numeric_matrix(
    records: Any, names: Sequence[str]
) -> Tuple[List[List[float]], List[str]]:
    """Convert mappings to a finite numeric matrix and return cold-start notes."""

    matrix: List[List[float]] = []
    warnings: List[str] = []
    missing_seen = set()
    for row in _records(records):
        values: List[float] = []
        for name in names:
            value = row.get(name)
            if value is None or (isinstance(value, float) and not math.isfinite(value)):
                value = 0.0
                missing_seen.add(name)
            values.append(float(value))
        matrix.append(values)
    if missing_seen:
        warnings.append("missing features filled with zero: {}".format(", ".join(sorted(missing_seen))))
    return matrix, warnings
