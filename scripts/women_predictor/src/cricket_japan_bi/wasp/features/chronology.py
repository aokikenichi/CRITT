"""Pre-date team, form and venue features with same-day batch updates."""

from __future__ import annotations

import math
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Any, DefaultDict, Dict, Iterable, List, Mapping, MutableMapping, Optional, Sequence, Tuple


def _date_key(value: Any) -> date:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value)[:10])


def _value(row: Mapping[str, Any], *names: str, default: Any = None) -> Any:
    for name in names:
        value = row.get(name)
        if value is not None:
            return value
    return default


@dataclass(frozen=True)
class EloConfig:
    initial_rating: float = 1500.0
    k_factor: float = 24.0
    form_half_life_days: float = 365.0
    form_prior_innings: float = 8.0
    venue_prior_innings: float = 20.0


def expected_score(rating: float, opponent_rating: float) -> float:
    return 1.0 / (1.0 + 10.0 ** ((opponent_rating - rating) / 400.0))


def _match_teams(row: Mapping[str, Any]) -> Tuple[str, str]:
    teams = row.get("teams")
    if teams and len(teams) == 2:
        return str(teams[0]), str(teams[1])
    return str(_value(row, "team_1", "team1", default="Unknown")), str(
        _value(row, "team_2", "team2", default="Unknown")
    )


def _elo_score(row: Mapping[str, Any], team: str, opponent: str) -> Optional[float]:
    result = str(row.get("result") or "").casefold()
    method = str(row.get("method") or "").casefold()
    if result in {"no result", "awarded"} or method == "awarded":
        return None
    if (
        result == "tie"
        or row.get("bowl_out")
        or row.get("has_bowl_out")
        or row.get("eliminator")
        or row.get("has_super_over")
        or row.get("super_over")
    ):
        return 0.5
    winner = row.get("winner")
    if not winner:
        return None
    return 1.0 if str(winner) == team else 0.0


@dataclass
class _DecayedMean:
    weighted_sum: float = 0.0
    weight: float = 0.0
    last_date: Optional[date] = None

    def snapshot(self, on_date: date, half_life: float) -> Tuple[float, float]:
        if self.last_date is None:
            return self.weighted_sum, self.weight
        decay = 0.5 ** (max(0, (on_date - self.last_date).days) / half_life)
        return self.weighted_sum * decay, self.weight * decay

    def add(self, value: float, on_date: date, half_life: float) -> None:
        self.weighted_sum, self.weight = self.snapshot(on_date, half_life)
        self.weighted_sum += value
        self.weight += 1.0
        self.last_date = on_date


def _shrunk_mean(
    stat: _DecayedMean,
    on_date: date,
    half_life: float,
    prior: float,
    prior_weight: float,
) -> Tuple[float, float]:
    total, weight = stat.snapshot(on_date, half_life)
    return (total + prior * prior_weight) / (weight + prior_weight), weight


def _innings_by_match(
    innings: Optional[Iterable[Mapping[str, Any]]]
) -> Mapping[str, List[Mapping[str, Any]]]:
    result: DefaultDict[str, List[Mapping[str, Any]]] = defaultdict(list)
    for row in innings or ():
        result[str(row.get("match_id") or "")].append(row)
    return result


def build_prematch_features(
    matches: Iterable[Mapping[str, Any]],
    innings: Optional[Iterable[Mapping[str, Any]]] = None,
    *,
    config: EloConfig = EloConfig(),
) -> List[Mapping[str, Any]]:
    """Return two team snapshots per match, never using another same-day result.

    Ratings and EWMA values for every match on a date are read from the end of
    the previous date.  Only after all snapshots are emitted are that day's
    outcomes applied.
    """

    if config.k_factor <= 0:
        raise ValueError("k_factor must be positive")
    rows = sorted(
        [dict(row) for row in matches],
        key=lambda row: (_date_key(_value(row, "match_date", "date")), str(row.get("match_id"))),
    )
    innings_map = _innings_by_match(innings)
    ratings: DefaultDict[str, float] = defaultdict(lambda: config.initial_rating)
    batting_form: DefaultDict[str, _DecayedMean] = defaultdict(_DecayedMean)
    bowling_form: DefaultDict[str, _DecayedMean] = defaultdict(_DecayedMean)
    venue_scores: DefaultDict[str, _DecayedMean] = defaultdict(_DecayedMean)
    global_scores = _DecayedMean()
    result: List[Mapping[str, Any]] = []
    index = 0
    while index < len(rows):
        current_date = _date_key(_value(rows[index], "match_date", "date"))
        end = index
        while end < len(rows) and _date_key(_value(rows[end], "match_date", "date")) == current_date:
            end += 1
        day_rows = rows[index:end]

        global_prior, global_count = _shrunk_mean(
            global_scores,
            current_date,
            config.form_half_life_days,
            150.0,
            1.0,
        )
        for match in day_rows:
            team_1, team_2 = _match_teams(match)
            venue = str(match.get("venue") or "Unknown")
            venue_prior, venue_count = _shrunk_mean(
                venue_scores[venue],
                current_date,
                config.form_half_life_days,
                global_prior,
                config.venue_prior_innings,
            )
            for team, opponent in ((team_1, team_2), (team_2, team_1)):
                batting_mean, batting_count = _shrunk_mean(
                    batting_form[team],
                    current_date,
                    config.form_half_life_days,
                    global_prior,
                    config.form_prior_innings,
                )
                opponent_batting, opponent_batting_count = _shrunk_mean(
                    batting_form[opponent],
                    current_date,
                    config.form_half_life_days,
                    global_prior,
                    config.form_prior_innings,
                )
                bowling_mean, bowling_count = _shrunk_mean(
                    bowling_form[team],
                    current_date,
                    config.form_half_life_days,
                    0.0,
                    config.form_prior_innings,
                )
                opponent_bowling, opponent_bowling_count = _shrunk_mean(
                    bowling_form[opponent],
                    current_date,
                    config.form_half_life_days,
                    0.0,
                    config.form_prior_innings,
                )
                result.append(
                    {
                        "match_id": str(match.get("match_id") or ""),
                        "match_date": current_date.isoformat(),
                        "team": team,
                        "opponent": opponent,
                        "pre_match_elo": ratings[team],
                        "opponent_pre_match_elo": ratings[opponent],
                        "elo_diff": ratings[team] - ratings[opponent],
                        "batting_form": batting_mean,
                        "batting_form_delta": batting_mean - opponent_batting,
                        "bowling_suppression": bowling_mean,
                        "bowling_suppression_delta": bowling_mean - opponent_bowling,
                        "venue_prior": venue_prior,
                        "venue_sample_count": venue_count,
                        "team_cold_start": batting_count == 0 and bowling_count == 0,
                        "opponent_cold_start": opponent_batting_count == 0 and opponent_bowling_count == 0,
                        "global_prior": global_prior,
                        "global_sample_count": global_count,
                        "era_trend": current_date.year + (current_date.timetuple().tm_yday - 1) / 365.25,
                    }
                )

        # Batched Elo updates use the rating snapshot from before this date.
        rating_delta: DefaultDict[str, float] = defaultdict(float)
        for match in day_rows:
            team_1, team_2 = _match_teams(match)
            score_1 = _elo_score(match, team_1, team_2)
            if score_1 is not None:
                expected_1 = expected_score(ratings[team_1], ratings[team_2])
                delta = config.k_factor * (score_1 - expected_1)
                rating_delta[team_1] += delta
                rating_delta[team_2] -= delta
        for team, delta in rating_delta.items():
            ratings[team] += delta

        # Form and venue updates happen only after every snapshot for the date.
        for match in day_rows:
            match_id = str(match.get("match_id") or "")
            for innings_row in innings_map.get(match_id, []):
                if not bool(innings_row.get("is_main_innings", True)):
                    continue
                score_raw = _value(innings_row, "final_runs", "final_score")
                if score_raw is None:
                    continue
                score = float(score_raw)
                batting = str(_value(innings_row, "batting_team", "team", default="Unknown"))
                bowling = str(innings_row.get("bowling_team") or "Unknown")
                batting_form[batting].add(score, current_date, config.form_half_life_days)
                bowling_form[bowling].add(global_prior - score, current_date, config.form_half_life_days)
                if int(_value(innings_row, "innings", "number", default=1)) == 1:
                    venue = str(match.get("venue") or "Unknown")
                    venue_scores[venue].add(score, current_date, config.form_half_life_days)
                    global_scores.add(score, current_date, config.form_half_life_days)
        index = end
    return result


# More explicit name retained for callers that use the plan terminology.
build_chronology_features = build_prematch_features


@dataclass(frozen=True)
class EloKSelection:
    selected_k: float
    validation_brier: Mapping[str, float]
    evaluated_matches: int


def select_elo_k(
    matches: Iterable[Mapping[str, Any]],
    *,
    candidates: Sequence[float] = (16.0, 24.0, 32.0),
    validation_years: Sequence[int] = (2023, 2024),
) -> EloKSelection:
    """Select K on pre-match validation Brier without touching locked test."""

    rows = [dict(row) for row in matches]
    scores: Dict[str, float] = {}
    evaluated = 0
    for k_factor in candidates:
        snapshots = build_prematch_features(rows, config=EloConfig(k_factor=k_factor))
        by_key = {
            (str(row["match_id"]), str(row["team"])): row for row in snapshots
        }
        losses: List[float] = []
        for match in rows:
            match_date = _date_key(_value(match, "match_date", "date"))
            if match_date.year not in validation_years:
                continue
            team, opponent = _match_teams(match)
            actual = _elo_score(match, team, opponent)
            if actual is None:
                continue
            snapshot = by_key.get((str(match.get("match_id") or ""), team))
            if snapshot is None:
                continue
            probability = expected_score(
                float(snapshot["pre_match_elo"]),
                float(snapshot["opponent_pre_match_elo"]),
            )
            losses.append((probability - actual) ** 2)
        scores["{:g}".format(k_factor)] = (
            sum(losses) / len(losses) if losses else float("inf")
        )
        evaluated = max(evaluated, len(losses))
    selected = min(candidates, key=lambda value: (scores["{:g}".format(value)], value))
    return EloKSelection(float(selected), scores, evaluated)


def build_latest_context(
    matches: Iterable[Mapping[str, Any]],
    innings: Optional[Iterable[Mapping[str, Any]]] = None,
    *,
    config: EloConfig = EloConfig(),
) -> Mapping[str, Any]:
    """Return source-cutoff team/venue snapshots for manual prediction.

    Synthetic no-result probe matches are placed one day after the source
    cutoff.  Because chronology updates are daily batches and probes have no
    outcome/innings, they expose the fully accumulated history without
    changing it.
    """

    match_rows = [dict(row) for row in matches]
    innings_rows = [dict(row) for row in (innings or ())]
    if not match_rows:
        return {"teams": {}, "venues": {}, "global": {}}
    cutoff = max(_date_key(_value(row, "match_date", "date")) for row in match_rows)
    probe_date = (cutoff + timedelta(days=1)).isoformat()
    teams = sorted({team for row in match_rows for team in _match_teams(row) if team != "Unknown"})
    venues = sorted({str(row.get("venue")) for row in match_rows if row.get("venue")})
    probes: List[Mapping[str, Any]] = []
    for index, team in enumerate(teams):
        probes.append(
            {
                "match_id": "__context_team_{:05d}".format(index),
                "match_date": probe_date,
                "team_1": team,
                "team_2": "__WASP_GLOBAL__",
                "venue": "__WASP_GLOBAL_VENUE__",
                "result": "no result",
            }
        )
    for index, venue in enumerate(venues):
        probes.append(
            {
                "match_id": "__context_venue_{:05d}".format(index),
                "match_date": probe_date,
                "team_1": "__WASP_VENUE_A__",
                "team_2": "__WASP_VENUE_B__",
                "venue": venue,
                "result": "no result",
            }
        )
    snapshots = build_prematch_features(
        match_rows + probes, innings_rows, config=config
    )
    by_key = {
        (str(row.get("match_id") or ""), str(row.get("team") or "")): row
        for row in snapshots
    }
    team_context: Dict[str, Mapping[str, Any]] = {}
    for index, team in enumerate(teams):
        row = by_key[("__context_team_{:05d}".format(index), team)]
        team_context[team] = {
            "elo": float(row["pre_match_elo"]),
            "batting_form": float(row["batting_form"]),
            "bowling_suppression": float(row["bowling_suppression"]),
            "cold_start": bool(row["team_cold_start"]),
            "era_trend": float(row["era_trend"]),
        }
    venue_context: Dict[str, Mapping[str, Any]] = {}
    global_context: Mapping[str, Any] = {}
    for index, venue in enumerate(venues):
        row = by_key[("__context_venue_{:05d}".format(index), "__WASP_VENUE_A__")]
        venue_context[venue] = {
            "venue_prior": float(row["venue_prior"]),
            "venue_sample_count": float(row["venue_sample_count"]),
        }
        global_context = {
            "elo": config.initial_rating,
            "batting_form": float(row["global_prior"]),
            "bowling_suppression": 0.0,
            "venue_prior": float(row["global_prior"]),
            "venue_sample_count": 0.0,
            "era_trend": float(row["era_trend"]),
        }
    if not global_context and team_context:
        example = next(iter(team_context.values()))
        global_context = {
            "elo": config.initial_rating,
            "batting_form": 150.0,
            "bowling_suppression": 0.0,
            "venue_prior": 150.0,
            "venue_sample_count": 0.0,
            "era_trend": example["era_trend"],
        }
    return {
        "cutoff": cutoff.isoformat(),
        "teams": team_context,
        "venues": venue_context,
        "global": global_context,
    }
