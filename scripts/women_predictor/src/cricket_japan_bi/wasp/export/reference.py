"""Dependency-free reference evaluator for standalone model JSON.

This module intentionally does not import NumPy or scikit-learn.  It provides
an executable specification for the JavaScript runtime and a cheap parity
check for every generated single-file HTML artifact.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple


def _value(payload: Mapping[str, Any], *names: str, default: Any = None) -> Any:
    for name in names:
        if name in payload and payload[name] is not None:
            return payload[name]
    return default


def _quota_balls(value: Any, default: int = 120) -> int:
    if value is None:
        return default
    if isinstance(value, (int, float)):
        return int(value)
    if value.get("total_balls") is not None:
        return int(value["total_balls"])
    return int(value.get("overs") or 0) * 6 + int(value.get("balls") or 0)


def _completed_balls(payload: Mapping[str, Any]) -> int:
    structured = _value(payload, "completed", "current", "completed_quota")
    if structured is not None:
        return _quota_balls(structured, 0)
    if payload.get("legal_balls_bowled") is not None:
        return int(payload["legal_balls_bowled"])
    return int(_value(payload, "completed_overs", "overs", default=0)) * 6 + int(
        _value(payload, "completed_balls", "balls", default=0)
    )


def _phase_absolute(legal_balls: int) -> str:
    return "powerplay" if legal_balls < 36 else "middle" if legal_balls < 96 else "death"


def _phase_relative(legal_balls: int, limit: int) -> str:
    progress = min(1.0, legal_balls / float(limit))
    return "powerplay" if progress < 0.30 else "middle" if progress < 0.80 else "death"


def _finite_number(value: Any) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return 0.0
    return result if math.isfinite(result) else 0.0


def _vector(state: Mapping[str, Any], features: Sequence[str]) -> List[float]:
    return [_finite_number(state.get(name)) for name in features]


def _sigmoid(value: float) -> float:
    if value >= 0:
        exponential = math.exp(-value)
        return 1.0 / (1.0 + exponential)
    exponential = math.exp(value)
    return exponential / (1.0 + exponential)


def _tree_value(tree: Mapping[str, Any], vector: Sequence[float]) -> float:
    index = 0
    while not int(tree["leaf"][index]):
        feature = int(tree["feature"][index])
        value = vector[feature]
        if not math.isfinite(value):
            go_left = bool(tree["missing_left"][index])
        else:
            go_left = value <= float(tree["threshold"][index])
        index = int(tree["left"][index] if go_left else tree["right"][index])
    return float(tree["value"][index])


def _hgb_value(spec: Mapping[str, Any], vector: Sequence[float]) -> float:
    if len(vector) != int(spec["n_features"]):
        raise ValueError("standalone model feature-count mismatch")
    raw = float(spec["baseline"]) + sum(
        _tree_value(tree, vector) for tree in spec["trees"]
    )
    link = spec["inverse_link"]
    if link == "identity":
        return raw
    if link == "log":
        return math.exp(raw)
    if link == "logit":
        return _sigmoid(raw)
    raise ValueError("unknown inverse link: {}".format(link))


def _estimator_value(spec: Mapping[str, Any], vector: Sequence[float]) -> float:
    kind = spec["kind"]
    if kind == "hist_gradient_boosting":
        return _hgb_value(spec, vector)
    if kind == "standardized_logistic":
        if not (
            len(vector)
            == len(spec["mean"])
            == len(spec["scale"])
            == len(spec["coefficient"])
        ):
            raise ValueError("standalone logistic feature-count mismatch")
        raw = float(spec["intercept"])
        for value, mean, scale, coefficient in zip(
            vector, spec["mean"], spec["scale"], spec["coefficient"]
        ):
            raw += ((value - float(mean)) / float(scale)) * float(coefficient)
        return _sigmoid(raw)
    if kind == "standardized_linear":
        if not (
            len(vector)
            == len(spec["mean"])
            == len(spec["scale"])
            == len(spec["coefficient"])
        ):
            raise ValueError("standalone linear feature-count mismatch")
        raw = float(spec["intercept"])
        for value, mean, scale, coefficient in zip(
            vector, spec["mean"], spec["scale"], spec["coefficient"]
        ):
            raw += ((value - float(mean)) / float(scale)) * float(coefficient)
        link = spec["inverse_link"]
        if link == "identity":
            return raw
        if link == "log":
            return math.exp(raw)
        raise ValueError("unknown linear inverse link: {}".format(link))
    raise ValueError("unsupported standalone estimator: {}".format(kind))


def _phase(state: Mapping[str, Any]) -> str:
    return str(
        state.get("phase_absolute")
        or state.get("phase")
        or _phase_absolute(int(state.get("legal_balls_bowled") or 0))
    ).casefold()


def _wicket_band(wickets: int) -> str:
    return "8-10" if wickets >= 8 else "5-7" if wickets >= 5 else "3-4" if wickets >= 3 else "0-2"


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


def _table_lookup(level: Sequence[Any], key: Sequence[Any]) -> Optional[Tuple[float, float]]:
    for stored_key, total, count in level:
        if list(stored_key) == list(key):
            return float(total), float(count)
    return None


def _resource_remaining(spec: Mapping[str, Any], state: Mapping[str, Any]) -> float:
    if int(state.get("wickets_lost") or 0) >= 10 or int(state.get("balls_remaining") or 0) <= 0:
        return 0.0
    balls = max(0, int(state.get("balls_remaining") or 0))
    wickets = max(0, int(state.get("wickets_remaining") or 0))
    keys = (
        (),
        (_phase(state), _wicket_band(wickets)),
        ((balls + 5) // 6, _wicket_band(wickets)),
        (balls, wickets),
    )
    prediction = float(spec["global_mean"])
    for index, key in enumerate(keys):
        value = _table_lookup(spec["levels"][index], key)
        if value is None or value[1] <= 0:
            continue
        observed = value[0] / value[1]
        prediction = observed if index == 0 else (
            value[1] * observed + float(spec["pseudo_count"]) * prediction
        ) / (value[1] + float(spec["pseudo_count"]))
    return max(0.0, prediction)


def _hierarchical_probability(spec: Mapping[str, Any], state: Mapping[str, Any]) -> float:
    balls = max(0, int(state.get("balls_remaining") or 0))
    wickets = max(0, int(state.get("wickets_remaining") or 0))
    phase = _phase(state)
    keys = (
        (),
        (phase,),
        (phase, (balls + 5) // 6),
        (phase, (balls + 5) // 6, wickets),
        (phase, (balls + 5) // 6, wickets, _rrr_band(state.get("required_run_rate"))),
    )
    prediction = float(spec["global_probability"])
    for index, key in enumerate(keys):
        value = _table_lookup(spec["levels"][index], key)
        if value is None or value[1] <= 0:
            continue
        observed = value[0] / value[1]
        prediction = observed if index == 0 else (
            value[1] * observed + float(spec["pseudo_count"]) * prediction
        ) / (value[1] + float(spec["pseudo_count"]))
    return min(1.0 - 1e-6, max(1e-6, prediction))


def _apply_calibrator(value: float, calibrator: Any) -> float:
    if calibrator is None:
        return value
    clipped = min(1.0 - 1e-6, max(1e-6, float(value)))
    logit = math.log(clipped / (1.0 - clipped))
    return _sigmoid(float(calibrator["slope"]) * logit + float(calibrator["intercept"]))


def _first_model_value(spec: Mapping[str, Any], state: Mapping[str, Any]) -> float:
    runs = float(state.get("runs_so_far") or 0)
    if int(state.get("wickets_lost") or 0) >= 10 or int(state.get("balls_remaining") or 0) <= 0:
        return runs
    kind = spec["kind"]
    if kind == "remaining_regressor":
        remaining = max(
            0.0,
            _estimator_value(spec["estimator"], _vector(state, spec["features"])),
        )
        return max(runs, runs + remaining)
    if kind == "current_run_rate":
        legal = int(state.get("legal_balls_bowled") or 0)
        if legal == 0:
            return max(runs, float(spec["start_score"]))
        rate = float(state.get("current_run_rate") or runs * 6.0 / legal)
        return max(runs, runs + rate * int(state.get("balls_remaining") or 0) / 6.0)
    if kind == "resource_table":
        return runs + _resource_remaining(spec, state)
    raise ValueError("unknown first-innings model: {}".format(kind))


def _chase_model_value(spec: Mapping[str, Any], state: Mapping[str, Any]) -> float:
    if spec["kind"] == "chase_classifier":
        value = _estimator_value(
            spec["estimator"], _vector(state, spec["features"])
        )
        return min(1.0, max(0.0, _apply_calibrator(value, spec.get("calibrator"))))
    if spec["kind"] == "hierarchical_probability":
        return _hierarchical_probability(spec, state)
    raise ValueError("unknown chase model: {}".format(spec["kind"]))


def _chase_terminal(score: int, target: int, wickets: int, balls: int) -> Tuple[Optional[str], Optional[float]]:
    if target < 1:
        raise ValueError("target must be at least 1")
    if score >= target:
        return "chase_won", 1.0
    if wickets >= 10 or balls <= 0:
        if score == target - 1:
            return "tied_regulation", None
        return "chase_lost", 0.0
    return None, None


def build_state(
    exported: Mapping[str, Any],
    payload: Mapping[str, Any],
    *,
    innings: int,
) -> Mapping[str, Any]:
    """Build the same manual-prediction state as ``PredictionService``."""

    if innings not in (1, 2):
        raise ValueError("innings must be 1 or 2")
    batting = str(
        _value(
            payload,
            "batting_team" if innings == 1 else "chasing_team",
            "team" if innings == 1 else "batting_team",
            default="",
        )
    )
    bowling = str(
        _value(
            payload,
            "bowling_team" if innings == 1 else "defending_team",
            "opponent" if innings == 1 else "bowling_team",
            default="",
        )
    )
    run_names = (
        ("runs", "runs_so_far")
        if innings == 1
        else ("current_score", "runs", "runs_so_far")
    )
    runs = int(_value(payload, *run_names, default=0))
    wickets = int(_value(payload, "wickets", "wickets_lost", default=0))
    quota_value = _value(
        payload,
        "quota" if innings == 1 else "target_ball_limit",
        "innings_quota" if innings == 1 else "quota",
        "ball_limit",
    )
    ball_limit = _quota_balls(quota_value, 120)
    if innings == 2 and payload.get("balls_remaining") is not None:
        balls_remaining = _quota_balls(payload["balls_remaining"], ball_limit)
        legal_balls = max(0, ball_limit - balls_remaining)
    else:
        legal_balls = _completed_balls(payload)
        balls_remaining = max(0, ball_limit - legal_balls)
    target = (
        int(_value(payload, "target", "target_runs", default=0))
        if innings == 2
        else None
    )
    crr = runs * 6.0 / legal_balls if legal_balls else 0.0
    required = max(0, target - runs) if target is not None else None
    if required is None:
        rrr = None
    elif required == 0:
        rrr = 0.0
    elif balls_remaining:
        rrr = required * 6.0 / balls_remaining
    else:
        rrr = math.inf

    contexts = exported.get("context", {})
    global_context = dict(contexts.get("global", {}))
    team_contexts = contexts.get("teams", {})
    batting_context = dict(team_contexts.get(batting, global_context))
    bowling_context = dict(team_contexts.get(bowling, global_context))
    venue = str(payload.get("venue") or "Unknown")
    venue_context = dict(contexts.get("venues", {}).get(venue, global_context))
    batting_elo = float(batting_context.get("elo", global_context.get("elo", 1500.0)))
    bowling_elo = float(bowling_context.get("elo", global_context.get("elo", 1500.0)))
    batting_form = float(batting_context.get("batting_form", global_context.get("batting_form", 0.0)))
    opponent_form = float(bowling_context.get("batting_form", global_context.get("batting_form", 0.0)))
    batting_suppression = float(batting_context.get("bowling_suppression", global_context.get("bowling_suppression", 0.0)))
    opponent_suppression = float(bowling_context.get("bowling_suppression", global_context.get("bowling_suppression", 0.0)))
    date_text = str(_value(payload, "prediction_date", "match_date", default=exported.get("source_cutoff") or ""))
    default_year = float(str(_value(payload, "prediction_date", default="2026"))[:4] or 2026)
    return {
        "match_id": "manual",
        "match_date": date_text,
        "innings": innings,
        "batting_team": batting,
        "bowling_team": bowling,
        "venue": venue,
        "runs_so_far": runs,
        "wickets_lost": wickets,
        "wickets_remaining": max(0, 10 - wickets),
        "legal_balls_bowled": legal_balls,
        "balls_remaining": balls_remaining,
        "innings_ball_limit": ball_limit,
        "current_run_rate": crr,
        "progress": min(1.0, legal_balls / float(ball_limit)),
        "phase_absolute": _phase_absolute(legal_balls),
        "phase_relative": _phase_relative(legal_balls, ball_limit),
        "is_reduced_match": ball_limit < 120,
        "target": target,
        "runs_required": required,
        "required_run_rate": rrr,
        "rrr_minus_crr": rrr - crr if rrr is not None else None,
        "batting_team_won_toss": (
            str(payload.get("toss_winner")) == batting
            if payload.get("toss_winner")
            else None
        ),
        "elo_diff": float(payload.get("elo_diff", batting_elo - bowling_elo)),
        "batting_form_delta": float(payload.get("batting_form_delta", batting_form - opponent_form)),
        "bowling_suppression_delta": float(payload.get("bowling_suppression_delta", batting_suppression - opponent_suppression)),
        "venue_prior": float(payload.get("venue_prior", venue_context.get("venue_prior", global_context.get("venue_prior", 0.0)))),
        "venue_sample_count": float(payload.get("venue_sample_count", venue_context.get("venue_sample_count", 0.0))),
        "team_cold_start": float(batting not in team_contexts or batting_context.get("cold_start", False)),
        "opponent_cold_start": float(bowling not in team_contexts or bowling_context.get("cold_start", False)),
        "era_trend": float(payload.get("era_trend", global_context.get("era_trend", default_year))),
    }


def predict_interval(
    interval: Mapping[str, Any], state: Mapping[str, Any], point: float
) -> Mapping[str, Mapping[str, float]]:
    runs = float(state.get("runs_so_far") or 0)
    if int(state.get("wickets_lost") or 0) >= 10 or int(state.get("balls_remaining") or 0) <= 0:
        return {"p50": {"lower": runs, "upper": runs}, "p80": {"lower": runs, "upper": runs}}
    point = max(runs, float(point))
    if interval["kind"] == "symmetric_conformal":
        lower50 = max(runs, point - float(interval["radius_50"]))
        upper50 = max(point, point + float(interval["radius_50"]))
        lower80 = max(runs, min(lower50, point - float(interval["radius_80"])))
        upper80 = max(upper50, point + float(interval["radius_80"]))
    elif interval["kind"] == "quantile_conformal":
        vector = _vector(state, interval["features"])
        remaining = sorted(
            max(0.0, _estimator_value(interval["models"][key], vector))
            for key in ("0.10", "0.25", "0.75", "0.90")
        )
        raw50lower, raw50upper = runs + remaining[1], runs + remaining[2]
        raw80lower, raw80upper = runs + remaining[0], runs + remaining[3]
        lower50 = max(runs, min(point, raw50lower - float(interval["correction_50"])))
        upper50 = max(point, raw50upper + float(interval["correction_50"]))
        lower80 = max(runs, min(lower50, raw80lower - float(interval["correction_80"])))
        upper80 = max(upper50, raw80upper + float(interval["correction_80"]))
    else:
        raise ValueError("unknown interval model: {}".format(interval["kind"]))
    return {"p50": {"lower": lower50, "upper": upper50}, "p80": {"lower": lower80, "upper": upper80}}


def _warnings(exported: Mapping[str, Any], batting: str, bowling: str, venue: str) -> List[str]:
    warnings: List[str] = []
    teams = set(exported.get("known_teams", ()))
    venues = set(exported.get("known_venues", ()))
    if teams and batting not in teams:
        warnings.append("{} は学習時に未収録のためglobal priorへfallbackしました".format(batting))
    if teams and bowling not in teams:
        warnings.append("{} は学習時に未収録のためglobal priorへfallbackしました".format(bowling))
    if venues and venue not in venues:
        warnings.append("venue未収録のためglobal venue priorへfallbackしました")
    return warnings


def _role(state: Mapping[str, Any], innings: int) -> Optional[str]:
    if state["batting_team"] == "Japan":
        return "japan_batting" if innings == 1 else "japan_chasing"
    if state["bowling_team"] == "Japan":
        return "japan_bowling" if innings == 1 else "japan_defending"
    return None


def _apply_correction(value: float, correction: Mapping[str, Any]) -> float:
    if not correction.get("enabled"):
        return float(value)
    if correction["kind"] == "score":
        return max(0.0, float(value) + float(correction.get("offset", 0.0)))
    return min(1.0, max(0.0, _apply_calibrator(value, correction.get("calibrator"))))


def _correction_status(correction: Any, role: Any, requested: bool, terminal: bool = False) -> Mapping[str, Any]:
    applicable = correction is not None
    applied = bool(requested and applicable and correction.get("enabled") and not terminal)
    if terminal:
        fallback = "terminal_rule"
    elif applied:
        fallback = None
    elif correction is not None:
        fallback = correction.get("fallback_reason") or "gate_not_passed"
    else:
        fallback = "not_a_japan_role" if role is None else "correction_unavailable"
    return {
        "requested": requested,
        "applicable": applicable,
        "applied": applied,
        "fallback_reason": fallback,
        "match_count": int(correction.get("match_count", 0)) if correction else 0,
        # PredictionService intentionally omits correction uncertainty for a
        # deterministic terminal result.
        "ci80": correction.get("ci80") if correction and not terminal else None,
        "ci95": correction.get("ci95") if correction and not terminal else None,
    }


def predict_first(exported: Mapping[str, Any], payload: Mapping[str, Any]) -> Mapping[str, Any]:
    state = build_state(exported, payload, innings=1)
    if state["is_reduced_match"] and not exported.get("reduced_match_enabled"):
        raise ValueError("unsupported_reduced_match")
    global_value = _first_model_value(exported["models"]["first_global"], state)
    teams = set(exported.get("known_teams", ()))
    unknown = bool(teams) and (state["batting_team"] not in teams or state["bowling_team"] not in teams)
    team_value = global_value if unknown else _first_model_value(exported["models"]["first_team"], state)
    requested = bool(_value(payload, "use_japan_correction", "japan_correction", default=False))
    role = _role(state, 1)
    correction = exported.get("japan_corrections", {}).get(role) if role else None
    japan_value = max(float(state["runs_so_far"]), _apply_correction(team_value, correction)) if correction else team_value
    status = _correction_status(correction, role, requested)
    selected = japan_value if status["applied"] else team_value
    return {
        "comparison": {"global": global_value, "team_adjusted": team_value, "japan_adjusted": japan_value, "selected": selected},
        "intervals": predict_interval(exported["interval"], state, selected),
        "correction": status,
        "warnings": _warnings(exported, state["batting_team"], state["bowling_team"], state["venue"]),
    }


def _scenario_state(state: Mapping[str, Any], runs: int, wicket: bool) -> Mapping[str, Any]:
    child = dict(state)
    child["runs_so_far"] = int(state["runs_so_far"]) + runs
    child["wickets_lost"] = int(state["wickets_lost"]) + int(wicket)
    child["wickets_remaining"] = max(0, 10 - child["wickets_lost"])
    child["balls_remaining"] = max(0, int(state["balls_remaining"]) - 1)
    child["legal_balls_bowled"] = int(state["legal_balls_bowled"]) + 1
    limit = max(1, int(state.get("innings_ball_limit") or child["legal_balls_bowled"] + child["balls_remaining"]))
    child["current_run_rate"] = child["runs_so_far"] * 6.0 / child["legal_balls_bowled"] if child["legal_balls_bowled"] else 0.0
    child["progress"] = min(1.0, child["legal_balls_bowled"] / float(limit))
    child["phase_absolute"] = _phase_absolute(child["legal_balls_bowled"])
    child["phase_relative"] = _phase_relative(child["legal_balls_bowled"], limit)
    child["runs_required"] = max(0, int(state["target"]) - child["runs_so_far"])
    child["required_run_rate"] = child["runs_required"] * 6.0 / child["balls_remaining"] if child["runs_required"] and child["balls_remaining"] else 0.0 if child["runs_required"] == 0 else math.inf
    child["rrr_minus_crr"] = child["required_run_rate"] - child["current_run_rate"]
    return child


def predict_chase(exported: Mapping[str, Any], payload: Mapping[str, Any]) -> Mapping[str, Any]:
    state = build_state(exported, payload, innings=2)
    if state["is_reduced_match"] and not exported.get("reduced_match_enabled"):
        raise ValueError("unsupported_reduced_match")
    status_name, terminal_probability = _chase_terminal(int(state["runs_so_far"]), int(state["target"]), int(state["wickets_lost"]), int(state["balls_remaining"]))
    requested = bool(_value(payload, "use_japan_correction", "japan_correction", default=False))
    role = _role(state, 2)
    correction = exported.get("japan_corrections", {}).get(role) if role else None
    warnings = _warnings(exported, state["batting_team"], state["bowling_team"], state["venue"])
    if status_name is not None:
        return {
            "comparison": {"global": terminal_probability, "team_adjusted": terminal_probability, "japan_adjusted": terminal_probability, "selected": terminal_probability},
            "scenarios": [],
            "terminal": {"is_terminal": True, "status": status_name, "probability": terminal_probability},
            "correction": _correction_status(correction, role, requested, terminal=True),
            "warnings": warnings,
        }
    global_value = _chase_model_value(exported["models"]["chase_global"], state)
    unknown_toss = payload.get("toss_winner") not in {state["batting_team"], state["bowling_team"]}
    if unknown_toss:
        state["batting_team_won_toss"] = None
        warnings.append("トス結果が不明のため、チーム補正モデルではなくglobalモデルを使用しました")
    teams = set(exported.get("known_teams", ()))
    unknown = bool(teams) and (state["batting_team"] not in teams or state["bowling_team"] not in teams)
    model = exported["models"]["chase_global" if unknown or unknown_toss else "chase_team"]
    team_value = global_value if unknown or unknown_toss else _chase_model_value(model, state)
    japan_value = _apply_correction(team_value, correction) if correction and not unknown_toss else team_value
    correction_status = _correction_status(correction, role, requested)
    if unknown_toss and correction_status["applied"]:
        correction_status = dict(correction_status, applied=False, fallback_reason="unknown_toss", ci80=None, ci95=None)
    selected = japan_value if correction_status["applied"] else team_value
    scenarios = []
    for label, runs, wicket in (("0 runs", 0, False), ("1 run", 1, False), ("2 runs", 2, False), ("3 runs", 3, False), ("4 runs", 4, False), ("6 runs", 6, False), ("wicket", 0, True)):
        child = _scenario_state(state, runs, wicket)
        child_status, child_terminal = _chase_terminal(int(child["runs_so_far"]), int(child["target"]), int(child["wickets_lost"]), int(child["balls_remaining"]))
        probability = child_terminal if child_status is not None else _chase_model_value(model, child)
        if correction_status["applied"] and correction is not None and probability is not None:
            probability = _apply_correction(probability, correction)
        scenarios.append({"label": label, "runs": runs, "wicket": wicket, "win_probability": probability})
    return {
        "comparison": {"global": global_value, "team_adjusted": team_value, "japan_adjusted": japan_value, "selected": selected},
        "scenarios": scenarios,
        "terminal": {"is_terminal": False, "status": None, "probability": None},
        "correction": correction_status,
        "warnings": warnings,
    }
