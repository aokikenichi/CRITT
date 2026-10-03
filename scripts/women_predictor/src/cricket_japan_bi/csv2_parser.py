"""Streaming reader for Cricsheet's column-named ("Ashwin") CSV2 files.

The public entry points are :func:`iter_csv2_match_info`, which reads only the
small ``*_info.csv`` members, and :func:`iter_csv2_matches`, which yields one
fully parsed match at a time.  Delivery fields are read by header name; columns
unknown to this module are retained in ``CSV2Delivery.extra_fields``.

Cricsheet registry identifiers are used as player IDs whenever possible.  A
missing registry entry is deliberately not fatal: the parser emits a
``CSV2RegistryWarning`` and assigns a deterministic ``unregistered:<hash>`` ID.
"""

from __future__ import annotations

import csv
import hashlib
import io
import re
import unicodedata
import warnings as python_warnings
import zipfile
from collections import defaultdict
from dataclasses import dataclass, field, replace
from decimal import Decimal
from numbers import Integral
from pathlib import Path
from typing import (
    Dict,
    FrozenSet,
    Iterable,
    Iterator,
    List,
    Mapping,
    MutableMapping,
    Optional,
    Sequence,
    TextIO,
    Tuple,
    Union,
)


MINIMUM_FORMAT_VERSION = "2.3.0"

REQUIRED_INFO_FIELDS: FrozenSet[str] = frozenset(
    {
        "balls_per_over",
        "date",
        "gender",
        "match_id",
        "match_type",
        "player",
        "registry",
        "season",
        "team",
        "team_type",
        "toss_decision",
        "toss_winner",
    }
)

# ``venue`` and all columns below ``extras`` in the specification are optional
# values.  The names here are the columns whose absence makes a ball row
# impossible to interpret and includes ``actual_delivery``, introduced in 2.3.
REQUIRED_BALL_COLUMNS: FrozenSet[str] = frozenset(
    {
        "match_id",
        "season",
        "start_date",
        "innings",
        "ball",
        "actual_delivery",
        "batting_team",
        "bowling_team",
        "striker",
        "non_striker",
        "bowler",
        "runs_off_bat",
        "extras",
    }
)

KNOWN_BALL_COLUMNS: FrozenSet[str] = REQUIRED_BALL_COLUMNS | frozenset(
    {
        "venue",
        "wides",
        "noballs",
        "byes",
        "legbyes",
        "penalty",
        "non_boundary",
        "wicket_type",
        "player_dismissed",
        "other_wicket_type",
        "other_player_dismissed",
        "fielder_1",
        "fielder_2",
        "fielder_3",
    }
)

BOWLER_WICKET_KINDS: FrozenSet[str] = frozenset(
    {
        "bowled",
        "caught",
        "caught and bowled",
        "lbw",
        "stumped",
        "hit wicket",
        "hit the ball twice",
    }
)

ZipPath = Union[str, Path]
RawInfo = Mapping[str, Tuple[Tuple[str, ...], ...]]


class CSV2ParseError(ValueError):
    """Raised when a CSV2 archive or row cannot be interpreted safely."""


class MissingRequiredColumnsError(CSV2ParseError):
    """Raised when the ball header omits one or more required CSV2 columns."""

    def __init__(self, member: str, missing: Iterable[str]) -> None:
        self.member = member
        self.missing = tuple(sorted(missing))
        super().__init__(
            "{} is missing required CSV2 ball column(s): {}".format(
                member, ", ".join(self.missing)
            )
        )


class CSV2RegistryWarning(UserWarning):
    """A person had no Cricsheet registry identifier in the match info."""


@dataclass(frozen=True)
class CSV2Player:
    """A player listed in an info file.

    ``player_id`` is always populated.  It equals ``registry_id`` when the
    registry contains the name, otherwise it is a stable fallback ID.
    """

    team: str
    name: str
    player_id: str
    registry_id: Optional[str]

    @property
    def uses_fallback_id(self) -> bool:
        return self.registry_id is None


@dataclass(frozen=True)
class CSV2Outcome:
    winner: Optional[str]
    result: Optional[str]
    method: Optional[str]
    eliminator: Optional[str]
    bowl_out: Optional[str]
    winner_runs: Optional[int]
    winner_wickets: Optional[int]
    winner_innings: Optional[int]

    @property
    def is_no_result(self) -> bool:
        return (self.result or "").strip().casefold() == "no result"


@dataclass(frozen=True)
class CSV2Target:
    """An innings target without treating cricket overs as decimal numbers.

    ``overs`` preserves Cricsheet's base-6 notation (for example ``"14.4"``)
    and ``balls`` is its unambiguous legal-ball representation.  Runs and
    overs are optional independently because experimental CSV2 archives can
    contain only one of the two target rows; callers can then audit the
    incomplete target instead of silently inventing a value.
    """

    innings: int
    runs: Optional[int]
    overs: Optional[str]
    balls: Optional[int]

    @property
    def target_runs(self) -> Optional[int]:
        return self.runs

    @property
    def target_overs(self) -> Optional[str]:
        return self.overs

    @property
    def target_balls(self) -> Optional[int]:
        return self.balls


@dataclass(frozen=True)
class CSV2MatchInfo:
    """Match metadata obtainable without opening the ball-by-ball member."""

    match_id: str
    source_name: str
    format_version: str
    date: Optional[str]
    dates: Tuple[str, ...]
    season: Optional[str]
    match_type: Optional[str]
    team_type: Optional[str]
    gender: Optional[str]
    balls_per_over: Optional[int]
    overs: Optional[int]
    teams: Tuple[str, ...]
    outcome: CSV2Outcome
    players: Tuple[CSV2Player, ...]
    registry: Mapping[str, str]
    super_over_innings: FrozenSet[int]
    raw_info: RawInfo
    warnings: Tuple[str, ...] = ()
    # New typed metadata is appended with defaults so positional construction
    # written against the original dataclass remains valid.
    venue: Optional[str] = None
    city: Optional[str] = None
    toss_winner: Optional[str] = None
    toss_decision: Optional[str] = None
    targets: Mapping[int, CSV2Target] = field(default_factory=dict)

    @property
    def winner(self) -> Optional[str]:
        return self.outcome.winner

    @property
    def method(self) -> Optional[str]:
        return self.outcome.method

    @property
    def outcome_label(self) -> Optional[str]:
        return self.outcome.result

    @property
    def is_no_result(self) -> bool:
        return self.outcome.is_no_result

    @property
    def has_super_over(self) -> bool:
        return bool(self.super_over_innings)

    @property
    def innings_targets(self) -> Mapping[int, CSV2Target]:
        """Compatibility-friendly descriptive alias for :attr:`targets`."""

        return self.targets

    def target_for_innings(self, innings: int) -> Optional[CSV2Target]:
        return self.targets.get(innings)


@dataclass(frozen=True)
class CSV2Wicket:
    kind: str
    player_dismissed: str
    player_dismissed_id: str
    player_dismissed_registry_id: Optional[str]
    is_bowler_wicket: bool
    is_secondary: bool
    fielder_names: Tuple[str, ...] = ()
    fielder_ids: Tuple[str, ...] = ()


@dataclass(frozen=True)
class CSV2Delivery:
    """A single CSV2 delivery, including both primary and secondary wickets."""

    match_id: str
    sequence: int
    innings: int
    ball: str
    actual_delivery: str
    over: int
    phase: str
    batting_team: str
    bowling_team: str
    striker: str
    striker_id: str
    non_striker: str
    non_striker_id: str
    bowler: str
    bowler_id: str
    runs_off_bat: int
    extras: int
    wides: int
    noballs: int
    byes: int
    legbyes: int
    penalty: int
    total_runs: int
    legal_ball: bool
    non_boundary: bool
    is_dot: bool
    is_boundary: bool
    wickets: Tuple[CSV2Wicket, ...]
    is_super_over: bool
    is_main_innings: bool
    extra_fields: Mapping[str, str] = field(default_factory=dict)
    # Appended for the same positional-constructor compatibility as metadata.
    venue: Optional[str] = None

    @property
    def is_legal_ball(self) -> bool:
        """Compatibility alias matching the existing JSON parser's naming."""

        return self.legal_ball


@dataclass(frozen=True)
class CSV2Match:
    """One match yielded by :func:`iter_csv2_matches`.

    Metadata fields frequently used by aggregators are exposed as convenience
    properties so callers can use ``match.match_id``, ``match.teams``, etc.
    """

    metadata: CSV2MatchInfo
    deliveries: Tuple[CSV2Delivery, ...]
    warnings: Tuple[str, ...] = ()

    @property
    def match_id(self) -> str:
        return self.metadata.match_id

    @property
    def date(self) -> Optional[str]:
        return self.metadata.date

    @property
    def teams(self) -> Tuple[str, ...]:
        return self.metadata.teams

    @property
    def winner(self) -> Optional[str]:
        return self.metadata.winner

    @property
    def outcome(self) -> Optional[str]:
        return self.metadata.outcome_label

    @property
    def method(self) -> Optional[str]:
        return self.metadata.method

    @property
    def players(self) -> Tuple[CSV2Player, ...]:
        return self.metadata.players

    @property
    def registry(self) -> Mapping[str, str]:
        return self.metadata.registry

    @property
    def super_over_innings(self) -> FrozenSet[int]:
        return self.metadata.super_over_innings

    @property
    def has_super_over(self) -> bool:
        return self.metadata.has_super_over

    @property
    def venue(self) -> Optional[str]:
        return self.metadata.venue

    @property
    def city(self) -> Optional[str]:
        return self.metadata.city

    @property
    def toss_winner(self) -> Optional[str]:
        return self.metadata.toss_winner

    @property
    def toss_decision(self) -> Optional[str]:
        return self.metadata.toss_decision

    @property
    def targets(self) -> Mapping[int, CSV2Target]:
        return self.metadata.targets

    @property
    def is_no_result(self) -> bool:
        return self.metadata.is_no_result

    @property
    def main_deliveries(self) -> Tuple[CSV2Delivery, ...]:
        """Deliveries from innings 1-2, excluding any marked super over."""

        return tuple(delivery for delivery in self.deliveries if delivery.is_main_innings)


def phase_for_over(over: int) -> str:
    """Return the fixed T20 phase for a zero-based over number."""

    if over < 0:
        raise ValueError("over cannot be negative")
    if over < 6:
        return "powerplay"
    if over < 16:
        return "middle"
    return "death"


def overs_to_balls(
    overs: Union[str, int, float, Decimal], balls_per_over: int = 6
) -> int:
    """Convert cricket over notation to legal balls using base-``balls_per_over``.

    Cricket's ``14.4`` means 14 completed overs and four balls, *not* 14.4
    decimal overs.  Values are parsed textually to avoid binary floating-point
    multiplication.  A ball component equal to or larger than the configured
    over length is rejected (so ``14.6`` is invalid for six-ball overs).
    """

    if isinstance(balls_per_over, bool) or not isinstance(balls_per_over, Integral):
        raise TypeError("balls_per_over must be an integer")
    balls_per_over = int(balls_per_over)
    if balls_per_over <= 0:
        raise ValueError("balls_per_over must be positive")
    if isinstance(overs, bool):
        raise TypeError("overs must be a cricket over notation, not bool")

    if isinstance(overs, Integral):
        completed = int(overs)
        ball = 0
    else:
        text = str(overs).strip()
        if not text or text.count(".") > 1:
            raise ValueError("invalid cricket over notation: {!r}".format(overs))
        if "." in text:
            completed_text, ball_text = text.split(".", 1)
            if not completed_text or not ball_text:
                raise ValueError("invalid cricket over notation: {!r}".format(overs))
            # The suffix is a single base-N ball digit, not a decimal fraction.
            if not completed_text.isdigit() or not ball_text.isdigit() or len(ball_text) != 1:
                raise ValueError("invalid cricket over notation: {!r}".format(overs))
            completed = int(completed_text)
            ball = int(ball_text)
        else:
            if not text.isdigit():
                raise ValueError("invalid cricket over notation: {!r}".format(overs))
            completed = int(text)
            ball = 0

    if completed < 0 or ball < 0 or ball >= balls_per_over:
        raise ValueError(
            "invalid cricket over notation {!r} for {}-ball overs".format(
                overs, balls_per_over
            )
        )
    return completed * balls_per_over + ball


def fallback_player_id(name: str) -> str:
    """Return a stable, non-registry player key derived from a display name."""

    normalized = unicodedata.normalize("NFKC", name)
    normalized = " ".join(normalized.split()).casefold()
    digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:16]
    return "unregistered:{}".format(digest)


def _registry_variant_key(name: str) -> str:
    """Normalize only Cricsheet's trailing numeric name disambiguator."""

    normalized = unicodedata.normalize("NFKC", name)
    normalized = " ".join(normalized.split()).casefold()
    return re.sub(r"\s+\(\d+\)$", "", normalized)


def iter_csv2_match_info(
    zip_path: ZipPath, source_name: Optional[str] = None
) -> Iterator[CSV2MatchInfo]:
    """Yield metadata records while opening only ``*_info.csv`` members."""

    archive_path = Path(zip_path)
    source = source_name or archive_path.name
    with zipfile.ZipFile(archive_path) as archive:
        info_members = _info_members(archive)
        if not info_members:
            raise CSV2ParseError("{} contains no *_info.csv members".format(archive_path))
        for logical_name, member in sorted(info_members.items()):
            fallback_match_id = Path(logical_name).name
            with _text_member(archive, member) as handle:
                yield _parse_info_file(handle, fallback_match_id, source, member)


def iter_csv2_matches(
    zip_path: ZipPath,
    source_name: Optional[str] = None,
    match_ids: Optional[Iterable[str]] = None,
) -> Iterator[CSV2Match]:
    """Yield fully parsed CSV2 matches, retaining only one match at a time.

    When ``match_ids`` is provided, unrelated ball members are skipped before
    they are opened.  This keeps period-specific dashboard builds fast and
    memory-efficient while preserving the default full-archive behaviour.
    """

    archive_path = Path(zip_path)
    source = source_name or archive_path.name
    selected_ids = {str(match_id) for match_id in match_ids} if match_ids is not None else None
    with zipfile.ZipFile(archive_path) as archive:
        ball_members, info_members = _paired_members(archive)
        for logical_name in sorted(ball_members):
            fallback_match_id = Path(logical_name).name
            if selected_ids is not None and fallback_match_id not in selected_ids:
                continue
            info_member = info_members[logical_name]
            ball_member = ball_members[logical_name]

            with _text_member(archive, info_member) as handle:
                metadata = _parse_info_file(
                    handle, fallback_match_id, source, info_member
                )

            warning_messages = list(metadata.warnings)
            resolver = _PlayerResolver(
                metadata.match_id, metadata.registry, warning_messages
            )
            # Resolve known players into the same resolver so its warning cache
            # prevents a repeated warning if that player appears on many balls.
            for player in metadata.players:
                resolver.mark_already_resolved(player.name)

            with _text_member(archive, ball_member) as handle:
                deliveries = tuple(
                    _parse_ball_file(
                        handle,
                        ball_member,
                        metadata,
                        resolver,
                    )
                )

            final_warnings = tuple(warning_messages)
            replacement_fields = {}
            if final_warnings != metadata.warnings:
                replacement_fields["warnings"] = final_warnings
            if metadata.venue is None:
                delivery_venues = {
                    delivery.venue for delivery in deliveries if delivery.venue
                }
                if len(delivery_venues) == 1:
                    replacement_fields["venue"] = next(iter(delivery_venues))
            if replacement_fields:
                metadata = replace(metadata, **replacement_fields)
            yield CSV2Match(
                metadata=metadata,
                deliveries=deliveries,
                warnings=final_warnings,
            )


class _PlayerResolver:
    def __init__(
        self,
        match_id: str,
        registry: Mapping[str, str],
        warning_messages: List[str],
    ) -> None:
        self.match_id = match_id
        self.registry = registry
        self.warning_messages = warning_messages
        self._warned_names: set[str] = set()
        variant_ids: MutableMapping[str, set[str]] = defaultdict(set)
        for registered_name, registry_id in registry.items():
            variant_ids[_registry_variant_key(registered_name)].add(registry_id)
        # Resolve a Cricsheet numeric disambiguator variation only when it has
        # one possible registry ID in this match. This covers real rows where
        # info says e.g. ``Sultan Ahmed (2)`` while a fielder cell says
        # ``Sultan Ahmed``, without guessing when two people would collide.
        self._unambiguous_variant_ids = {
            key: next(iter(ids)) for key, ids in variant_ids.items() if len(ids) == 1
        }

    def mark_already_resolved(self, name: str) -> None:
        if name not in self.registry:
            self._warned_names.add(name)

    def resolve(self, name: str) -> Tuple[str, Optional[str]]:
        registry_id = self.registry.get(name)
        if not registry_id:
            registry_id = self._unambiguous_variant_ids.get(
                _registry_variant_key(name)
            )
        if registry_id:
            return registry_id, registry_id

        player_id = fallback_player_id(name)
        if name not in self._warned_names:
            message = (
                "match {}: {!r} is missing from the Cricsheet registry; "
                "using {}"
            ).format(self.match_id, name, player_id)
            self.warning_messages.append(message)
            self._warned_names.add(name)
            python_warnings.warn(message, CSV2RegistryWarning, stacklevel=4)
        return player_id, None


def _parse_info_file(
    handle: TextIO,
    fallback_match_id: str,
    source_name: str,
    member: str,
) -> CSV2MatchInfo:
    grouped: MutableMapping[str, List[Tuple[str, ...]]] = defaultdict(list)
    reader = csv.reader(handle)
    declared_version: Optional[str] = None
    saw_content = False
    for row_number, row in enumerate(reader, start=1):
        if not row or not any(cell.strip() for cell in row):
            continue
        row_kind = row[0].strip()
        if row_kind == "version":
            if saw_content or declared_version is not None:
                raise CSV2ParseError(
                    "{} row {} has a non-leading or duplicate version row".format(
                        member, row_number
                    )
                )
            if len(row) != 2 or not row[1].strip():
                raise CSV2ParseError(
                    "{} row {} has a malformed version row".format(
                        member, row_number
                    )
                )
            declared_version = row[1].strip()
            _validate_format_version(declared_version, member, row_number)
            saw_content = True
            continue
        saw_content = True
        if len(row) < 3 or row[0].strip() != "info":
            raise CSV2ParseError(
                "{} row {} is not an info row".format(member, row_number)
            )
        key = row[1].strip()
        if not key:
            raise CSV2ParseError(
                "{} row {} has an empty info field name".format(member, row_number)
            )
        grouped[key].append(tuple(cell.strip() for cell in row[2:]))

    if declared_version is None:
        raise CSV2ParseError(
            "{} has no leading version row (CSV2 {}+ required)".format(
                member, MINIMUM_FORMAT_VERSION
            )
        )

    # One official CSV2 archive member (1251954_info.csv) uses the experimental
    # plural spelling ``players``.  Accept it as a semantic alias while keeping
    # the original unknown field in ``raw_info`` for forward compatibility.
    if not grouped.get("player") and grouped.get("players"):
        grouped["player"] = list(grouped["players"])

    missing_info = sorted(
        key
        for key in REQUIRED_INFO_FIELDS
        if not grouped.get(key)
        or not any(any(cell for cell in values) for values in grouped[key])
    )
    if missing_info:
        raise CSV2ParseError(
            "{} is missing required CSV2 info field(s): {}".format(
                member, ", ".join(missing_info)
            )
        )

    def first(key: str) -> Optional[str]:
        values = grouped.get(key)
        if not values or not values[0]:
            return None
        return values[0][0] or None

    match_id = first("match_id")
    if not match_id:
        raise CSV2ParseError(
            "{} has no info,match_id row required by CSV2 {}+".format(
                member, MINIMUM_FORMAT_VERSION
            )
        )
    if fallback_match_id and match_id != fallback_match_id:
        raise CSV2ParseError(
            "{} declares match_id {!r}, expected {!r}".format(
                member, match_id, fallback_match_id
            )
        )

    teams = tuple(
        values[0]
        for values in grouped.get("team", [])
        if values and values[0]
    )
    registry: Dict[str, str] = {}
    for values in grouped.get("registry", []):
        if (
            len(values) < 3
            or values[0] != "people"
            or not values[1]
            or not values[2]
        ):
            raise CSV2ParseError("{} contains a malformed registry row".format(member))
        name, registry_id = values[1], values[2]
        if name in registry and registry[name] != registry_id:
            raise CSV2ParseError(
                "{} gives conflicting registry IDs for {!r}".format(member, name)
            )
        registry[name] = registry_id

    warning_messages: List[str] = []
    resolver = _PlayerResolver(match_id, registry, warning_messages)
    players: List[CSV2Player] = []
    for values in grouped.get("player", []):
        if len(values) < 2 or not values[0] or not values[1]:
            raise CSV2ParseError("{} contains a malformed player row".format(member))
        team, name = values[0], values[1]
        if team not in teams:
            raise CSV2ParseError(
                "{} lists player {!r} for unknown team {!r}".format(
                    member, name, team
                )
            )
        player_id, registry_id = resolver.resolve(name)
        players.append(
            CSV2Player(
                team=team,
                name=name,
                player_id=player_id,
                registry_id=registry_id,
            )
        )

    result = first("outcome")
    outcome = CSV2Outcome(
        winner=first("winner"),
        result=result,
        method=first("method"),
        eliminator=first("eliminator"),
        bowl_out=first("bowl_out"),
        winner_runs=_optional_int(first("winner_runs"), member, "winner_runs"),
        winner_wickets=_optional_int(
            first("winner_wickets"), member, "winner_wickets"
        ),
        winner_innings=_optional_int(
            first("winner_innings"), member, "winner_innings"
        ),
    )
    dates = tuple(
        values[0]
        for values in grouped.get("date", [])
        if values and values[0]
    )
    super_over_innings = frozenset(
        value
        for value in (
            _optional_int(values[0] if values else None, member, "super_over")
            for values in grouped.get("super_over", [])
        )
        if value is not None
    )
    raw_info: Dict[str, Tuple[Tuple[str, ...], ...]] = {
        key: tuple(values) for key, values in grouped.items()
    }

    balls_per_over = _optional_int(
        first("balls_per_over"), member, "balls_per_over"
    )
    if balls_per_over is None or balls_per_over <= 0:
        raise CSV2ParseError(
            "{} has an invalid required balls_per_over value".format(member)
        )
    targets = _parse_targets(grouped, member, balls_per_over)

    return CSV2MatchInfo(
        match_id=match_id,
        source_name=source_name,
        format_version=declared_version,
        date=dates[0] if dates else None,
        dates=dates,
        season=first("season"),
        match_type=first("match_type"),
        team_type=first("team_type"),
        gender=first("gender"),
        balls_per_over=balls_per_over,
        overs=_optional_int(first("overs"), member, "overs"),
        teams=teams,
        venue=first("venue"),
        city=first("city"),
        toss_winner=first("toss_winner"),
        toss_decision=first("toss_decision"),
        targets=targets,
        outcome=outcome,
        players=tuple(players),
        registry=registry,
        super_over_innings=super_over_innings,
        raw_info=raw_info,
        warnings=tuple(warning_messages),
    )


def _parse_ball_file(
    handle: TextIO,
    member: str,
    metadata: CSV2MatchInfo,
    resolver: _PlayerResolver,
) -> Iterator[CSV2Delivery]:
    reader = csv.reader(handle)
    try:
        raw_header = next(reader)
    except StopIteration as exc:
        raise CSV2ParseError("{} is empty".format(member)) from exc

    header = tuple(column.strip() for column in raw_header)
    if not header or not any(header):
        raise CSV2ParseError("{} has an empty header".format(member))
    if len(set(header)) != len(header):
        raise CSV2ParseError("{} has duplicate column names".format(member))
    missing = REQUIRED_BALL_COLUMNS.difference(header)
    if missing:
        raise MissingRequiredColumnsError(member, missing)

    unknown_columns = tuple(
        column for column in header if column not in KNOWN_BALL_COLUMNS
    )
    for row_number, cells in enumerate(reader, start=2):
        if not cells or not any(cell.strip() for cell in cells):
            continue
        if len(cells) != len(header):
            raise CSV2ParseError(
                "{} row {} has {} values for {} columns".format(
                    member, row_number, len(cells), len(header)
                )
            )
        row = {name: value.strip() for name, value in zip(header, cells)}
        row_match_id = _required_text(row, "match_id", member, row_number)
        if row_match_id != metadata.match_id:
            raise CSV2ParseError(
                "{} row {} has match_id {!r}, expected {!r}".format(
                    member, row_number, row_match_id, metadata.match_id
                )
            )

        innings = _required_int(row, "innings", member, row_number)
        ball = _required_text(row, "ball", member, row_number)
        actual_delivery = _required_text(
            row, "actual_delivery", member, row_number
        )
        over = _over_from_ball(ball, member, row_number)
        striker = _required_text(row, "striker", member, row_number)
        non_striker = _required_text(row, "non_striker", member, row_number)
        bowler = _required_text(row, "bowler", member, row_number)
        striker_id, _ = resolver.resolve(striker)
        non_striker_id, _ = resolver.resolve(non_striker)
        bowler_id, _ = resolver.resolve(bowler)

        runs_off_bat = _required_int(row, "runs_off_bat", member, row_number)
        extras = _required_int(row, "extras", member, row_number)
        wides = _row_optional_int(row, "wides", member, row_number)
        noballs = _row_optional_int(row, "noballs", member, row_number)
        byes = _row_optional_int(row, "byes", member, row_number)
        legbyes = _row_optional_int(row, "legbyes", member, row_number)
        penalty = _row_optional_int(row, "penalty", member, row_number)
        legal_ball = wides == 0 and noballs == 0
        non_boundary = _true_value(row.get("non_boundary"))
        total_runs = runs_off_bat + extras

        fielders = tuple(
            value
            for value in (row.get("fielder_1"), row.get("fielder_2"), row.get("fielder_3"))
            if value
        )
        fielder_ids = tuple(resolver.resolve(name)[0] for name in fielders)
        wickets: List[CSV2Wicket] = []
        _append_wicket(
            wickets,
            row.get("wicket_type", ""),
            row.get("player_dismissed", ""),
            False,
            fielders,
            fielder_ids,
            resolver,
            member,
            row_number,
        )
        _append_wicket(
            wickets,
            row.get("other_wicket_type", ""),
            row.get("other_player_dismissed", ""),
            True,
            (),
            (),
            resolver,
            member,
            row_number,
        )

        is_super_over = innings in metadata.super_over_innings
        yield CSV2Delivery(
            match_id=metadata.match_id,
            sequence=row_number - 1,
            innings=innings,
            ball=ball,
            actual_delivery=actual_delivery,
            over=over,
            phase=phase_for_over(over),
            batting_team=_required_text(
                row, "batting_team", member, row_number
            ),
            bowling_team=_required_text(
                row, "bowling_team", member, row_number
            ),
            venue=(row.get("venue") or None),
            striker=striker,
            striker_id=striker_id,
            non_striker=non_striker,
            non_striker_id=non_striker_id,
            bowler=bowler,
            bowler_id=bowler_id,
            runs_off_bat=runs_off_bat,
            extras=extras,
            wides=wides,
            noballs=noballs,
            byes=byes,
            legbyes=legbyes,
            penalty=penalty,
            total_runs=total_runs,
            legal_ball=legal_ball,
            non_boundary=non_boundary,
            is_dot=legal_ball and total_runs == 0,
            is_boundary=(
                legal_ball and not non_boundary and runs_off_bat in (4, 6)
            ),
            wickets=tuple(wickets),
            is_super_over=is_super_over,
            is_main_innings=innings in (1, 2) and not is_super_over,
            extra_fields={
                column: row[column]
                for column in unknown_columns
                if row.get(column)
            },
        )


def _append_wicket(
    destination: List[CSV2Wicket],
    kind: str,
    player_dismissed: str,
    is_secondary: bool,
    fielder_names: Sequence[str],
    fielder_ids: Sequence[str],
    resolver: _PlayerResolver,
    member: str,
    row_number: int,
) -> None:
    if not kind and not player_dismissed:
        return
    if not kind or not player_dismissed:
        label = "secondary wicket" if is_secondary else "wicket"
        raise CSV2ParseError(
            "{} row {} has an incomplete {}".format(member, row_number, label)
        )
    player_id, registry_id = resolver.resolve(player_dismissed)
    destination.append(
        CSV2Wicket(
            kind=kind,
            player_dismissed=player_dismissed,
            player_dismissed_id=player_id,
            player_dismissed_registry_id=registry_id,
            is_bowler_wicket=kind.casefold() in BOWLER_WICKET_KINDS,
            is_secondary=is_secondary,
            fielder_names=tuple(fielder_names),
            fielder_ids=tuple(fielder_ids),
        )
    )


def _paired_members(
    archive: zipfile.ZipFile,
) -> Tuple[Mapping[str, str], Mapping[str, str]]:
    ball_members: Dict[str, str] = {}
    info_members = _info_members(archive)
    for member in archive.namelist():
        if member.endswith("/") or not member.casefold().endswith(".csv"):
            continue
        if member.casefold().endswith("_info.csv"):
            continue
        logical_name = member[:-4]
        if logical_name in ball_members:
            raise CSV2ParseError("duplicate ball member for {}".format(logical_name))
        ball_members[logical_name] = member

    if not ball_members:
        raise CSV2ParseError("archive contains no ball-by-ball CSV members")
    missing_info = sorted(set(ball_members).difference(info_members))
    orphan_info = sorted(set(info_members).difference(ball_members))
    if missing_info or orphan_info:
        details = []
        if missing_info:
            details.append("missing info: {}".format(", ".join(missing_info)))
        if orphan_info:
            details.append("missing balls: {}".format(", ".join(orphan_info)))
        raise CSV2ParseError("unpaired CSV2 members ({})".format("; ".join(details)))
    return ball_members, info_members


def _info_members(archive: zipfile.ZipFile) -> Mapping[str, str]:
    members: Dict[str, str] = {}
    for member in archive.namelist():
        if member.endswith("/") or not member.casefold().endswith("_info.csv"):
            continue
        logical_name = member[: -len("_info.csv")]
        if logical_name in members:
            raise CSV2ParseError("duplicate info member for {}".format(logical_name))
        members[logical_name] = member
    return members


def _text_member(archive: zipfile.ZipFile, member: str) -> TextIO:
    # TextIOWrapper is a context manager and closes the underlying ZipExtFile.
    return io.TextIOWrapper(
        archive.open(member), encoding="utf-8-sig", newline=""
    )


def _required_text(
    row: Mapping[str, str], key: str, member: str, row_number: int
) -> str:
    value = row.get(key, "").strip()
    if not value:
        raise CSV2ParseError(
            "{} row {} has no value for required column {}".format(
                member, row_number, key
            )
        )
    return value


def _required_int(
    row: Mapping[str, str], key: str, member: str, row_number: int
) -> int:
    value = _required_text(row, key, member, row_number)
    parsed = _optional_int(value, member, key)
    assert parsed is not None
    return parsed


def _row_optional_int(
    row: Mapping[str, str], key: str, member: str, row_number: int
) -> int:
    try:
        return _optional_int(row.get(key), member, key) or 0
    except CSV2ParseError as exc:
        raise CSV2ParseError(
            "{} (row {})".format(str(exc), row_number)
        ) from exc


def _optional_int(value: Optional[str], member: str, field_name: str) -> Optional[int]:
    if value is None or not str(value).strip():
        return None
    try:
        return int(str(value).strip())
    except ValueError as exc:
        raise CSV2ParseError(
            "{} has a non-integer {} value: {!r}".format(
                member, field_name, value
            )
        ) from exc


def _parse_targets(
    grouped: Mapping[str, Sequence[Tuple[str, ...]]],
    member: str,
    balls_per_over: int,
) -> Mapping[int, CSV2Target]:
    target_values: Dict[int, Dict[str, object]] = {}
    for key, value_name in (("target_runs", "runs"), ("target_overs", "overs")):
        for values in grouped.get(key, ()):
            if len(values) < 2 or not values[0] or not values[1]:
                raise CSV2ParseError(
                    "{} contains a malformed {} row".format(member, key)
                )
            innings = _optional_int(values[0], member, "{}_innings".format(key))
            assert innings is not None
            if innings <= 0:
                raise CSV2ParseError(
                    "{} has a non-positive target innings: {}".format(
                        member, innings
                    )
                )
            target = target_values.setdefault(innings, {})
            if value_name in target:
                raise CSV2ParseError(
                    "{} contains duplicate {} rows for innings {}".format(
                        member, key, innings
                    )
                )
            if key == "target_runs":
                runs = _optional_int(values[1], member, key)
                assert runs is not None
                if runs <= 0:
                    raise CSV2ParseError(
                        "{} has a non-positive target_runs value".format(member)
                    )
                target[value_name] = runs
            else:
                notation = values[1].strip()
                try:
                    balls = overs_to_balls(notation, balls_per_over)
                except (TypeError, ValueError) as exc:
                    raise CSV2ParseError(
                        "{} has invalid target_overs notation {!r}".format(
                            member, notation
                        )
                    ) from exc
                target[value_name] = notation
                target["balls"] = balls

    return {
        innings: CSV2Target(
            innings=innings,
            runs=(int(values["runs"]) if "runs" in values else None),
            overs=(str(values["overs"]) if "overs" in values else None),
            balls=(int(values["balls"]) if "balls" in values else None),
        )
        for innings, values in sorted(target_values.items())
    }


def _validate_format_version(version: str, member: str, row_number: int) -> None:
    parts = version.split(".")
    if len(parts) != 3 or any(not part.isdigit() for part in parts):
        raise CSV2ParseError(
            "{} row {} has invalid CSV2 version {!r}".format(
                member, row_number, version
            )
        )
    parsed = tuple(int(part) for part in parts)
    minimum = tuple(int(part) for part in MINIMUM_FORMAT_VERSION.split("."))
    if parsed < minimum:
        raise CSV2ParseError(
            "{} uses CSV2 version {}; {}+ is required".format(
                member, version, MINIMUM_FORMAT_VERSION
            )
        )


def _over_from_ball(ball: str, member: str, row_number: int) -> int:
    over_text, separator, _ = ball.partition(".")
    if not separator:
        raise CSV2ParseError(
            "{} row {} has invalid ball identifier {!r}".format(
                member, row_number, ball
            )
        )
    try:
        over = int(over_text)
    except ValueError as exc:
        raise CSV2ParseError(
            "{} row {} has invalid ball identifier {!r}".format(
                member, row_number, ball
            )
        ) from exc
    if over < 0:
        raise CSV2ParseError(
            "{} row {} has negative over in {!r}".format(member, row_number, ball)
        )
    return over


def _true_value(value: Optional[str]) -> bool:
    return (value or "").strip().casefold() == "true"


__all__ = [
    "BOWLER_WICKET_KINDS",
    "CSV2Delivery",
    "CSV2Match",
    "CSV2MatchInfo",
    "CSV2Outcome",
    "CSV2ParseError",
    "CSV2Player",
    "CSV2RegistryWarning",
    "CSV2Target",
    "CSV2Wicket",
    "KNOWN_BALL_COLUMNS",
    "MINIMUM_FORMAT_VERSION",
    "MissingRequiredColumnsError",
    "REQUIRED_BALL_COLUMNS",
    "REQUIRED_INFO_FIELDS",
    "fallback_player_id",
    "iter_csv2_match_info",
    "iter_csv2_matches",
    "overs_to_balls",
    "phase_for_over",
]
