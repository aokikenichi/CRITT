"""Delivery-after-delivery WASP-style state reconstruction.

The functions accept plain mappings deliberately.  The normalized data layer
writes Parquet records with the same names, while small fixtures and callers
can pass dictionaries without importing a storage-specific schema.
"""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass
from typing import Any, Iterable, List, Mapping, Optional, Sequence, Tuple


NON_TEAM_WICKET_KINDS = frozenset(
    {"retired hurt", "retired not out", "absent hurt"}
)
KNOWN_WICKET_KINDS = frozenset(
    {
        "bowled",
        "caught",
        "caught and bowled",
        "lbw",
        "stumped",
        "hit wicket",
        "handled the ball",
        "hit the ball twice",
        "obstructing the field",
        "run out",
        "retired out",
        "timed out",
        "retired hurt",
        "retired not out",
        "absent hurt",
    }
)


def _value(row: Mapping[str, Any], *names: str, default: Any = None) -> Any:
    for name in names:
        value = row.get(name)
        if value is not None:
            return value
    return default


def _as_int(value: Any, default: int = 0) -> int:
    if value in (None, ""):
        return default
    return int(value)


def phase_absolute(legal_balls_bowled: int) -> str:
    """Return the fixed phase using completed legal balls.

    Ball 0--35 is Powerplay, 36--95 is Middle and 96 onward is Death.
    The innings-start state (zero completed balls) is therefore Powerplay.
    """

    if legal_balls_bowled < 0:
        raise ValueError("legal_balls_bowled cannot be negative")
    if legal_balls_bowled < 36:
        return "powerplay"
    if legal_balls_bowled < 96:
        return "middle"
    return "death"


def phase_relative(legal_balls_bowled: int, innings_ball_limit: int) -> str:
    """Return progress-normalized phase for reduced-overs comparisons."""

    if innings_ball_limit <= 0:
        raise ValueError("innings_ball_limit must be positive")
    if legal_balls_bowled < 0:
        raise ValueError("legal_balls_bowled cannot be negative")
    progress = min(1.0, legal_balls_bowled / float(innings_ball_limit))
    if progress < 0.30:
        return "powerplay"
    if progress < 0.80:
        return "middle"
    return "death"


def counts_as_team_wicket(kind: str) -> bool:
    """Classify a dismissal without silently guessing an unknown kind."""

    normalized = " ".join(str(kind or "").strip().casefold().split())
    if normalized not in KNOWN_WICKET_KINDS:
        raise ValueError("unknown dismissal kind: {!r}".format(kind))
    return normalized not in NON_TEAM_WICKET_KINDS


def wicket_count(value: Any) -> int:
    """Return team wickets from an integer or iterable of wicket records."""

    if value in (None, ""):
        return 0
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, (int, float)):
        return int(value)
    count = 0
    for wicket in value:
        if isinstance(wicket, Mapping):
            if wicket.get("counts_as_team_wicket") is not None:
                count += int(bool(wicket["counts_as_team_wicket"]))
            else:
                count += int(counts_as_team_wicket(str(wicket.get("kind") or "")))
        else:
            count += int(counts_as_team_wicket(str(wicket)))
    return count


def chase_terminal(
    *, score: int, target: int, wickets_lost: int, balls_remaining: int
) -> Tuple[Optional[str], Optional[float]]:
    """Return regulation chase terminal status and binary probability.

    Target reached has priority.  A level score at innings exhaustion is a
    regulation tie and deliberately has no binary win probability in v1.
    """

    if target < 1:
        raise ValueError("target must be at least 1")
    if score >= target:
        return "chase_won", 1.0
    exhausted = wickets_lost >= 10 or balls_remaining <= 0
    if exhausted and score == target - 1:
        return "tied_regulation", None
    if exhausted:
        return "chase_lost", 0.0
    return None, None


def event_type(row: Mapping[str, Any], wickets_on_delivery: int) -> str:
    if wickets_on_delivery:
        return "wicket"
    if _as_int(_value(row, "wides", "wide", default=0)):
        return "wide"
    if _as_int(_value(row, "noballs", "no_ball", "noball", default=0)):
        return "no_ball"
    runs_off_bat = _as_int(_value(row, "runs_off_bat", "batter_runs", default=0))
    if runs_off_bat == 6:
        return "six"
    if runs_off_bat == 4 and not bool(row.get("non_boundary")):
        return "four"
    return "delivery"


@dataclass(frozen=True)
class WaspState:
    match_id: str
    match_date: str
    innings: int
    state_sequence: int
    source_sequence: Optional[int]
    batting_team: str
    bowling_team: str
    venue: str
    runs_so_far: int
    wickets_lost: int
    wickets_remaining: int
    legal_balls_bowled: int
    balls_remaining: int
    innings_ball_limit: int
    current_run_rate: float
    progress: float
    phase_absolute: str
    phase_relative: str
    is_reduced_match: bool
    target: Optional[int]
    runs_required: Optional[int]
    required_run_rate: Optional[float]
    rrr_minus_crr: Optional[float]
    toss_winner: Optional[str]
    toss_decision: Optional[str]
    batting_team_won_toss: Optional[bool]
    terminal_status: Optional[str]
    terminal_probability: Optional[float]
    previous_event_type: str
    final_score: Optional[int] = None
    chase_won: Optional[bool] = None

    def as_record(self) -> Mapping[str, Any]:
        return asdict(self)


def _base_state(
    *,
    match: Mapping[str, Any],
    innings: Mapping[str, Any],
    state_sequence: int,
    source_sequence: Optional[int],
    runs: int,
    wickets: int,
    legal_balls: int,
    previous_event_type: str,
) -> WaspState:
    number = _as_int(_value(innings, "innings", "number", default=1), 1)
    ball_limit = _as_int(
        _value(innings, "innings_ball_limit", "target_balls", "quota_balls", default=120),
        120,
    )
    if ball_limit <= 0:
        raise ValueError("innings_ball_limit must be positive")
    balls_remaining = max(0, ball_limit - legal_balls)
    target_raw = _value(innings, "target_runs", "target")
    target = int(target_raw) if target_raw not in (None, "") else None
    crr = runs * 6.0 / legal_balls if legal_balls else 0.0
    required = max(0, target - runs) if number == 2 and target is not None else None
    if required is None:
        rrr = None
    elif required == 0:
        rrr = 0.0
    elif balls_remaining:
        rrr = required * 6.0 / balls_remaining
    else:
        rrr = math.inf
    terminal_status: Optional[str] = None
    terminal_probability: Optional[float] = None
    if number == 2 and target is not None:
        terminal_status, terminal_probability = chase_terminal(
            score=runs,
            target=target,
            wickets_lost=wickets,
            balls_remaining=balls_remaining,
        )
    elif wickets >= 10:
        terminal_status = "all_out"
    elif balls_remaining == 0:
        terminal_status = "quota_reached"
    batting_team = str(_value(innings, "batting_team", "team", default="Unknown"))
    bowling_team = str(_value(innings, "bowling_team", default="Unknown"))
    toss_winner_raw = _value(match, "toss_winner")
    toss_winner = str(toss_winner_raw) if toss_winner_raw not in (None, "") else None
    final_score_raw = _value(innings, "final_runs", "final_score")
    final_score = int(final_score_raw) if final_score_raw not in (None, "") else None
    chase_won_raw = _value(innings, "chase_won")
    if chase_won_raw is None and number == 2 and match.get("winner"):
        chase_won_raw = str(match["winner"]) == batting_team
    return WaspState(
        match_id=str(_value(match, "match_id", default=_value(innings, "match_id", default=""))),
        match_date=str(_value(match, "match_date", "date", default="")),
        innings=number,
        state_sequence=state_sequence,
        source_sequence=source_sequence,
        batting_team=batting_team,
        bowling_team=bowling_team,
        venue=str(_value(match, "venue", default="Unknown") or "Unknown"),
        runs_so_far=runs,
        wickets_lost=wickets,
        wickets_remaining=max(0, 10 - wickets),
        legal_balls_bowled=legal_balls,
        balls_remaining=balls_remaining,
        innings_ball_limit=ball_limit,
        current_run_rate=crr,
        progress=min(1.0, legal_balls / float(ball_limit)),
        phase_absolute=phase_absolute(legal_balls),
        phase_relative=phase_relative(legal_balls, ball_limit),
        is_reduced_match=ball_limit < 120,
        target=target,
        runs_required=required,
        required_run_rate=rrr,
        rrr_minus_crr=(rrr - crr if rrr is not None else None),
        toss_winner=toss_winner,
        toss_decision=(str(match["toss_decision"]) if match.get("toss_decision") else None),
        batting_team_won_toss=(toss_winner == batting_team if toss_winner else None),
        terminal_status=terminal_status,
        terminal_probability=terminal_probability,
        previous_event_type=previous_event_type,
        final_score=final_score,
        chase_won=(bool(chase_won_raw) if chase_won_raw is not None else None),
    )


def build_innings_states(
    deliveries: Iterable[Mapping[str, Any]],
    innings: Mapping[str, Any],
    match: Optional[Mapping[str, Any]] = None,
    *,
    include_start: bool = True,
) -> List[Mapping[str, Any]]:
    """Build a synthetic start state and one state per physical delivery.

    Legal balls are incremented only from ``legal_ball``/``is_legal_ball``.
    The source ``ball`` and ``actual_delivery`` labels are never parsed to infer
    ball counts.
    """

    match_record = dict(match or {})
    if "match_id" not in match_record and innings.get("match_id") is not None:
        match_record["match_id"] = innings["match_id"]
    rows = sorted(
        list(deliveries),
        key=lambda row: _as_int(_value(row, "source_sequence", "sequence", "state_sequence")),
    )
    runs = _as_int(_value(innings, "penalty_runs_pre", "initial_runs", default=0))
    wickets = 0
    legal_balls = 0
    states: List[Mapping[str, Any]] = []
    if include_start:
        states.append(
            _base_state(
                match=match_record,
                innings=innings,
                state_sequence=0,
                source_sequence=None,
                runs=runs,
                wickets=wickets,
                legal_balls=legal_balls,
                previous_event_type="innings_start",
            ).as_record()
        )
    for index, row in enumerate(rows, start=1):
        runs += _as_int(_value(row, "total_runs", default=0))
        wickets_on_delivery = wicket_count(
            _value(row, "team_wickets", "wickets", default=0)
        )
        wickets += wickets_on_delivery
        if wickets > 10:
            raise ValueError("team wickets cannot exceed 10")
        legal = _value(row, "legal_ball", "is_legal_ball")
        if legal is None:
            legal = not bool(_as_int(row.get("wides"), 0) or _as_int(row.get("noballs"), 0))
        legal_balls += int(bool(legal))
        source_sequence = _as_int(_value(row, "source_sequence", "sequence", default=index))
        states.append(
            _base_state(
                match=match_record,
                innings=innings,
                state_sequence=index,
                source_sequence=source_sequence,
                runs=runs,
                wickets=wickets,
                legal_balls=legal_balls,
                previous_event_type=event_type(row, wickets_on_delivery),
            ).as_record()
        )
    final_runs = _value(innings, "final_runs", "final_score")
    if final_runs is not None and states and int(final_runs) != states[-1]["runs_so_far"]:
        raise ValueError(
            "final score mismatch: normalized={} reconstructed={}".format(
                final_runs, states[-1]["runs_so_far"]
            )
        )
    final_wickets = innings.get("final_wickets")
    if final_wickets is not None and states and int(final_wickets) != states[-1]["wickets_lost"]:
        raise ValueError(
            "final wicket mismatch: normalized={} reconstructed={}".format(
                final_wickets, states[-1]["wickets_lost"]
            )
        )
    return states


def build_match_states(
    match: Mapping[str, Any],
    innings_rows: Sequence[Mapping[str, Any]],
    deliveries: Sequence[Mapping[str, Any]],
) -> List[Mapping[str, Any]]:
    """Build all main-innings states for a normalized match."""

    result: List[Mapping[str, Any]] = []
    match_id = str(match.get("match_id") or "")
    for innings in innings_rows:
        if not bool(innings.get("is_main_innings", True)):
            continue
        number = _as_int(_value(innings, "innings", "number"), 1)
        subset = [
            row
            for row in deliveries
            if str(row.get("match_id") or match_id) == match_id
            and _as_int(row.get("innings"), 1) == number
            and not bool(row.get("is_super_over", False))
        ]
        result.extend(build_innings_states(subset, innings, match))
    return result
