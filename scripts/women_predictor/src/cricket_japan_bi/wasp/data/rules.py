"""Cricket-specific rules used consistently by audit and normalization."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Iterable, Optional, Sequence, Tuple, Union

from cricket_japan_bi.csv2_parser import CSV2MatchInfo, CSV2Target, CSV2Wicket


NON_TEAM_WICKET_KINDS = frozenset(
    {"retired hurt", "retired not out", "absent hurt"}
)

KNOWN_DISMISSAL_KINDS = frozenset(
    {
        "bowled",
        "caught",
        "caught and bowled",
        "handled the ball",
        "hit the ball twice",
        "hit wicket",
        "lbw",
        "obstructing the field",
        "retired hurt",
        "retired not out",
        "retired out",
        "run out",
        "stumped",
        "timed out",
        "absent hurt",
    }
)


class UnknownDismissalKindError(ValueError):
    """Raised when an unseen dismissal cannot safely be classified."""


@dataclass(frozen=True)
class TargetResolution:
    target: Optional[CSV2Target]
    source: Optional[str]
    issue: Optional[str]


def normalize_dismissal_kind(kind: str) -> str:
    return " ".join(str(kind or "").strip().casefold().split())


def counts_as_team_wicket(wicket_or_kind: Union[CSV2Wicket, str]) -> bool:
    kind = normalize_dismissal_kind(
        wicket_or_kind.kind if isinstance(wicket_or_kind, CSV2Wicket) else wicket_or_kind
    )
    if kind not in KNOWN_DISMISSAL_KINDS:
        raise UnknownDismissalKindError("unknown dismissal kind: {!r}".format(kind))
    return kind not in NON_TEAM_WICKET_KINDS


def count_team_wickets(wickets: Iterable[CSV2Wicket]) -> int:
    return sum(1 for wicket in wickets if counts_as_team_wicket(wicket))


def parse_match_date(value: Optional[str]) -> Optional[date]:
    text = str(value or "").strip()
    if not text:
        return None
    for candidate in (text, text.replace("/", "-")):
        try:
            return date.fromisoformat(candidate)
        except ValueError:
            pass
    for fmt in ("%Y/%m/%d", "%Y-%m-%d"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            pass
    return None


def split_for_date(value: Optional[str]) -> str:
    parsed = parse_match_date(value)
    if parsed is None:
        return "unknown"
    if parsed <= date(2022, 12, 31):
        return "train"
    if parsed <= date(2024, 12, 31):
        return "validation"
    return "test"


def phase_absolute(legal_balls_bowled: int) -> str:
    if legal_balls_bowled < 0:
        raise ValueError("legal_balls_bowled cannot be negative")
    if legal_balls_bowled < 36:
        return "powerplay"
    if legal_balls_bowled < 96:
        return "middle"
    return "death"


def phase_relative(legal_balls_bowled: int, ball_limit: int) -> str:
    if legal_balls_bowled < 0 or ball_limit <= 0:
        raise ValueError("invalid innings progress")
    progress = min(1.0, legal_balls_bowled / float(ball_limit))
    if progress < 0.30:
        return "powerplay"
    if progress < 0.80:
        return "middle"
    return "death"


def resolve_second_innings_target(
    metadata: CSV2MatchInfo,
    first_innings_score: Optional[int],
    main_innings_count: int,
) -> TargetResolution:
    """Resolve an explicit target or the narrow safe reconstruction case."""

    explicit = metadata.targets.get(2)
    if explicit is not None:
        if explicit.runs is None or explicit.balls is None:
            return TargetResolution(explicit, "explicit", "incomplete_target")
        return TargetResolution(explicit, "explicit", None)

    method = (metadata.outcome.method or "").strip().casefold()
    result = (metadata.outcome.result or "").strip().casefold()
    exceptional = bool(
        method in {"d/l", "dls", "awarded"}
        or result in {"tie", "no result", "awarded"}
        or metadata.super_over_innings
        or metadata.outcome.bowl_out
        or metadata.outcome.eliminator
    )
    if (
        first_innings_score is not None
        and main_innings_count == 2
        and metadata.overs == 20
        and metadata.balls_per_over == 6
        and not exceptional
    ):
        return TargetResolution(
            CSV2Target(
                innings=2,
                runs=first_innings_score + 1,
                overs="20",
                balls=120,
            ),
            "reconstructed",
            None,
        )
    return TargetResolution(None, None, "missing_target")


def determine_end_reason(
    innings: int,
    final_runs: int,
    final_wickets: int,
    legal_balls: int,
    ball_limit: Optional[int],
    target_runs: Optional[int] = None,
) -> str:
    if innings == 2 and target_runs is not None and final_runs >= target_runs:
        return "target_reached"
    if final_wickets >= 10:
        return "all_out"
    if ball_limit is not None and legal_balls >= ball_limit:
        return "quota_reached"
    return "unknown"


def chase_terminal_status(
    score: int,
    wickets: int,
    balls_remaining: int,
    target: int,
) -> Optional[str]:
    if score >= target:
        return "chase_won"
    if wickets >= 10 or balls_remaining <= 0:
        if score == target - 1:
            return "tied_regulation"
        return "chase_lost"
    return None


def exceptional_chase_reason(metadata: CSV2MatchInfo) -> Optional[str]:
    """Return the first exclusive v1 chase exclusion reason."""

    if (metadata.gender or "").casefold() != "female":
        return "not_female"
    if (metadata.team_type or "").casefold() != "international":
        return "not_international"
    if (metadata.match_type or "").casefold() != "t20":
        return "not_t20"
    if metadata.super_over_innings or metadata.outcome.eliminator:
        return "super_over"
    method = (metadata.outcome.method or "").strip().casefold()
    result = (metadata.outcome.result or "").strip().casefold()
    if method in {"d/l", "dls"}:
        return "dls"
    if method == "awarded" or result == "awarded":
        return "awarded"
    if result == "no result":
        return "no_result"
    if result == "tie":
        return "tie"
    if metadata.outcome.bowl_out:
        return "bowl_out"
    return None


def target_is_suspected_revised(
    target: Optional[CSV2Target], first_innings_score: Optional[int], method: Optional[str]
) -> bool:
    if target is None or target.runs is None or first_innings_score is None:
        return False
    if (method or "").strip():
        return False
    return target.runs != first_innings_score + 1


__all__ = [
    "KNOWN_DISMISSAL_KINDS",
    "NON_TEAM_WICKET_KINDS",
    "TargetResolution",
    "UnknownDismissalKindError",
    "chase_terminal_status",
    "count_team_wickets",
    "counts_as_team_wicket",
    "determine_end_reason",
    "exceptional_chase_reason",
    "normalize_dismissal_kind",
    "parse_match_date",
    "phase_absolute",
    "phase_relative",
    "resolve_second_innings_target",
    "split_for_date",
    "target_is_suspected_revised",
]
