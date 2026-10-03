"""Normalize CSV2 matches into model-ready Parquet and an isolated DuckDB."""

from __future__ import annotations

import json
import hashlib
import warnings
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple, Union
from uuid import uuid4

from cricket_japan_bi.csv2_parser import (
    CSV2Delivery,
    CSV2Match,
    CSV2RegistryWarning,
    CSV2Target,
    iter_csv2_matches,
)

from .audit import audit_csv2_archive, sha256_file, write_audit_reports
from .rules import (
    UnknownDismissalKindError,
    chase_terminal_status,
    count_team_wickets,
    counts_as_team_wicket,
    determine_end_reason,
    exceptional_chase_reason,
    parse_match_date,
    phase_absolute,
    phase_relative,
    resolve_second_innings_target,
    split_for_date,
    target_is_suspected_revised,
)
from .schemas import DatasetManifest, SCHEMA_VERSION, TABLE_SCHEMAS
from .storage import (
    BufferedParquetWriter,
    NormalizedDatasetWriters,
    TABLE_NAMES,
    write_duckdb,
    write_json_atomic,
)


PathLike = Union[str, Path]


@dataclass
class _InningsSummary:
    number: int
    batting_team: str
    bowling_team: str
    deliveries: Sequence[CSV2Delivery]
    final_runs: int
    final_wickets: int
    legal_balls: int
    unknown_dismissals: Tuple[str, ...]
    target: Optional[CSV2Target] = None
    target_source: Optional[str] = None
    ball_limit: Optional[int] = None
    end_reason: str = "unknown"
    first_innings_eligible: bool = False
    chase_eligible: bool = False
    reduced_match_eligible: bool = False
    quality_flags: Tuple[str, ...] = ()

    @property
    def is_main(self) -> bool:
        return self.number in (1, 2)

    @property
    def is_reduced(self) -> bool:
        return self.ball_limit is not None and self.ball_limit < 120


def _opponent(teams: Sequence[str], batting_team: str) -> str:
    for team in teams:
        if team != batting_team:
            return team
    return "Unknown"


def _summarize_innings(match: CSV2Match) -> Mapping[int, _InningsSummary]:
    grouped: Dict[int, List[CSV2Delivery]] = defaultdict(list)
    for delivery in match.deliveries:
        grouped[delivery.innings].append(delivery)
    summaries: Dict[int, _InningsSummary] = {}
    for number, deliveries in sorted(grouped.items()):
        batting_team = deliveries[0].batting_team
        bowling_team = deliveries[0].bowling_team or _opponent(
            match.teams, batting_team
        )
        final_wickets = 0
        unknown = set()
        for delivery in deliveries:
            try:
                final_wickets += count_team_wickets(delivery.wickets)
            except UnknownDismissalKindError:
                for wicket in delivery.wickets:
                    try:
                        counts_as_team_wicket(wicket)
                    except UnknownDismissalKindError:
                        unknown.add(wicket.kind.strip().casefold())
        summaries[number] = _InningsSummary(
            number=number,
            batting_team=batting_team,
            bowling_team=bowling_team,
            deliveries=tuple(deliveries),
            final_runs=sum(delivery.total_runs for delivery in deliveries),
            final_wickets=final_wickets,
            legal_balls=sum(1 for delivery in deliveries if delivery.legal_ball),
            unknown_dismissals=tuple(sorted(unknown)),
        )
    return summaries


def _first_innings_exclusion(match: CSV2Match, summary: Optional[_InningsSummary]) -> Optional[str]:
    metadata = match.metadata
    if (metadata.gender or "").casefold() != "female":
        return "not_female"
    if (metadata.team_type or "").casefold() != "international":
        return "not_international"
    if (metadata.match_type or "").casefold() != "t20":
        return "not_t20"
    method = (metadata.outcome.method or "").strip().casefold()
    result = (metadata.outcome.result or "").strip().casefold()
    if method in {"d/l", "dls"}:
        return "dls"
    if method == "awarded" or result == "awarded":
        return "awarded"
    if result == "no result":
        return "no_result"
    if metadata.super_over_innings or metadata.outcome.eliminator:
        return "super_over"
    if metadata.overs != 20 or metadata.balls_per_over != 6:
        return "nonstandard_scheduled_quota"
    if summary is None:
        return "missing_first_innings"
    if summary.unknown_dismissals:
        return "unknown_dismissal_kind"
    if summary.legal_balls > 120:
        return "overlong_innings"
    if summary.end_reason == "unknown":
        return "unknown_first_innings_end"
    return None


def _chase_exclusion(
    match: CSV2Match,
    summaries: Mapping[int, _InningsSummary],
    target_resolution: Any,
) -> Optional[str]:
    metadata = match.metadata
    exceptional = exceptional_chase_reason(metadata)
    if exceptional:
        return exceptional
    if metadata.overs != 20 or metadata.balls_per_over != 6:
        return "nonstandard_scheduled_quota"
    if set(number for number in summaries if number in (1, 2)) != {1, 2}:
        return "not_two_main_innings"
    if target_resolution.target is None or target_resolution.issue:
        return target_resolution.issue or "missing_target"
    first = summaries[1]
    chase = summaries[2]
    if target_is_suspected_revised(
        target_resolution.target, first.final_runs, metadata.outcome.method
    ):
        return "suspected_revised_target"
    if first.unknown_dismissals or chase.unknown_dismissals:
        return "unknown_dismissal_kind"
    if chase.ball_limit is not None and chase.legal_balls > chase.ball_limit:
        return "overlong_innings"
    if chase.end_reason == "unknown":
        return "unknown_chase_end"
    return None


def _prepare_match(
    match: CSV2Match,
) -> Tuple[Mapping[int, _InningsSummary], List[Mapping[str, str]], Tuple[str, ...]]:
    summaries = dict(_summarize_innings(match))
    metadata = match.metadata
    main_numbers = [number for number in summaries if number in (1, 2)]
    first_score = summaries[1].final_runs if 1 in summaries else None
    target_resolution = resolve_second_innings_target(
        metadata, first_score, len(main_numbers)
    )

    for number, summary in summaries.items():
        explicit = metadata.targets.get(number)
        if number == 2:
            summary.target = target_resolution.target
            summary.target_source = target_resolution.source
        else:
            summary.target = explicit
            summary.target_source = "explicit" if explicit is not None else None

        if number == 1:
            if metadata.overs is not None and metadata.balls_per_over is not None:
                summary.ball_limit = metadata.overs * metadata.balls_per_over
        elif summary.target is not None:
            summary.ball_limit = summary.target.balls
        elif number in metadata.super_over_innings:
            summary.ball_limit = metadata.balls_per_over

        summary.end_reason = determine_end_reason(
            number,
            summary.final_runs,
            summary.final_wickets,
            summary.legal_balls,
            summary.ball_limit,
            summary.target.runs if summary.target is not None else None,
        )
        # A side can be unable to continue with fewer than ten recorded team
        # wickets when it named fewer than eleven players or when a batter has
        # retired hurt/not out.  These events remain non-wickets; they are used
        # only to explain why the completed innings legitimately stopped.
        roster_size = sum(
            1 for player in metadata.players if player.team == summary.batting_team
        )
        unavailable = sum(
            1
            for delivery in summary.deliveries
            for wicket in delivery.wickets
            if wicket.kind.strip().casefold()
            in {"retired hurt", "retired not out", "absent hurt"}
        )
        roster_wicket_limit = min(10, max(0, roster_size - 1)) if roster_size else 10
        if summary.end_reason == "unknown" and (
            summary.final_wickets >= roster_wicket_limit
            or summary.final_wickets + unavailable >= 10
        ):
            summary.end_reason = "all_out_or_unavailable"

    first_reason = _first_innings_exclusion(match, summaries.get(1))
    chase_reason = _chase_exclusion(match, summaries, target_resolution)
    target = target_resolution.target
    stable_chase = chase_reason is None and target is not None and target.balls == 120
    reduced_chase = (
        chase_reason is None
        and target is not None
        and target.balls is not None
        and target.balls < 120
    )
    if 1 in summaries:
        summaries[1].first_innings_eligible = first_reason is None
    if 2 in summaries:
        summaries[2].chase_eligible = stable_chase
        summaries[2].reduced_match_eligible = reduced_chase

    flags = set()
    if parse_match_date(metadata.date) is None:
        flags.add("invalid_match_date")
    if len(main_numbers) != 2:
        flags.add("not_two_main_innings")
    if metadata.overs != 20 or metadata.balls_per_over != 6:
        flags.add("nonstandard_scheduled_quota")
    if metadata.overs == 50:
        flags.add("scheduled_overs_50")
    if target_resolution.issue:
        flags.add(target_resolution.issue)
    if target_is_suspected_revised(target, first_score, metadata.outcome.method):
        flags.add("suspected_revised_target")
    for summary in summaries.values():
        innings_flags = set()
        if summary.unknown_dismissals:
            innings_flags.add("unknown_dismissal_kind")
            flags.add("unknown_dismissal_kind")
        if summary.ball_limit is not None and summary.legal_balls > summary.ball_limit:
            innings_flags.add("legal_balls_exceed_limit")
            flags.add("legal_balls_exceed_limit")
        if summary.is_main and summary.end_reason == "unknown":
            innings_flags.add("unknown_end_reason")
            flags.add("unknown_end_reason")
        summary.quality_flags = tuple(sorted(innings_flags))

    exclusions: List[Mapping[str, str]] = []
    if first_reason:
        exclusions.append(
            {
                "model_scope": "first_innings",
                "reason": first_reason,
                "detail": "exclusive first failing rule",
            }
        )
    if chase_reason or (target is not None and target.balls != 120):
        reason = chase_reason or "reduced_target"
        exclusions.append(
            {
                "model_scope": "chase_full_20",
                "reason": reason,
                "detail": "exclusive first failing rule",
            }
        )
    if not reduced_chase:
        reduced_reason = chase_reason
        if reduced_reason is None:
            reduced_reason = "not_reduced_target"
        exclusions.append(
            {
                "model_scope": "chase_reduced",
                "reason": reduced_reason,
                "detail": "exclusive first failing rule",
            }
        )
    return summaries, exclusions, tuple(sorted(flags))


def _match_row(
    match: CSV2Match,
    summaries: Mapping[int, _InningsSummary],
    quality_flags: Tuple[str, ...],
) -> Mapping[str, Any]:
    metadata = match.metadata
    teams = list(metadata.teams) + [None, None]
    return {
        "match_id": metadata.match_id,
        "match_date": (
            parse_match_date(metadata.date).isoformat()
            if parse_match_date(metadata.date) is not None
            else metadata.date
        ),
        "season": metadata.season,
        "match_type": metadata.match_type,
        "team_type": metadata.team_type,
        "gender": metadata.gender,
        "team_1": teams[0],
        "team_2": teams[1],
        "venue": metadata.venue,
        "city": metadata.city,
        "toss_winner": metadata.toss_winner,
        "toss_decision": metadata.toss_decision,
        "winner": metadata.outcome.winner,
        "result": metadata.outcome.result,
        "method": metadata.outcome.method,
        "eliminator": metadata.outcome.eliminator,
        "bowl_out": metadata.outcome.bowl_out,
        "scheduled_overs": metadata.overs,
        "balls_per_over": metadata.balls_per_over,
        "has_super_over": bool(metadata.super_over_innings or metadata.outcome.eliminator),
        "has_bowl_out": bool(metadata.outcome.bowl_out),
        "is_japan_match": "Japan" in metadata.teams,
        "split": split_for_date(metadata.date),
        "quality_flags": list(quality_flags),
        "first_innings_eligible": bool(
            summaries.get(1) and summaries[1].first_innings_eligible
        ),
        "chase_eligible": bool(summaries.get(2) and summaries[2].chase_eligible),
        "reduced_match_eligible": bool(
            summaries.get(2) and summaries[2].reduced_match_eligible
        ),
    }


def _innings_row(match_id: str, summary: _InningsSummary) -> Mapping[str, Any]:
    target = summary.target
    return {
        "match_id": match_id,
        "innings": summary.number,
        "batting_team": summary.batting_team,
        "bowling_team": summary.bowling_team,
        "target_runs": target.runs if target is not None else None,
        "target_overs": target.overs if target is not None else None,
        "target_balls": target.balls if target is not None else None,
        "target_source": summary.target_source,
        "innings_ball_limit": summary.ball_limit,
        "final_runs": summary.final_runs,
        "final_wickets": summary.final_wickets,
        "legal_balls": summary.legal_balls,
        "physical_deliveries": len(summary.deliveries),
        "end_reason": summary.end_reason,
        "is_main_innings": summary.is_main and summary.number not in (),
        "is_reduced_match": summary.is_reduced,
        "first_innings_eligible": summary.first_innings_eligible,
        "chase_eligible": summary.chase_eligible,
        "quality_flags": list(summary.quality_flags),
    }


def _delivery_event(delivery: CSV2Delivery, team_wickets: int) -> str:
    if team_wickets:
        return "wicket"
    if delivery.wides:
        return "wide"
    if delivery.noballs:
        return "no_ball"
    if delivery.runs_off_bat == 6 and delivery.is_boundary:
        return "six"
    if delivery.runs_off_bat == 4 and delivery.is_boundary:
        return "four"
    return "delivery"


def _state_row(
    match: CSV2Match,
    summary: _InningsSummary,
    state_sequence: int,
    source_sequence: Optional[int],
    runs: int,
    wickets: int,
    legal_balls: int,
    previous_event: str,
) -> Mapping[str, Any]:
    ball_limit = summary.ball_limit
    balls_remaining = (
        max(0, ball_limit - legal_balls) if ball_limit is not None else None
    )
    crr = runs * 6.0 / legal_balls if legal_balls else 0.0
    progress = (
        min(1.0, legal_balls / float(ball_limit))
        if ball_limit is not None and ball_limit > 0
        else None
    )
    target = summary.target.runs if summary.target is not None else None
    runs_required = max(0, target - runs) if target is not None else None
    required_rate = None
    if runs_required is not None and balls_remaining is not None:
        if balls_remaining > 0:
            required_rate = runs_required * 6.0 / balls_remaining
        elif runs_required == 0:
            required_rate = 0.0
    terminal = None
    if summary.number == 2 and target is not None and balls_remaining is not None:
        terminal = chase_terminal_status(runs, wickets, balls_remaining, target)
    elif state_sequence == len(summary.deliveries) and summary.end_reason != "unknown":
        terminal = "innings_complete"
    terminal_probability = None
    if terminal == "chase_won":
        terminal_probability = 1.0
    elif terminal == "chase_lost":
        terminal_probability = 0.0

    chase_label = None
    if summary.number == 2 and (
        summary.chase_eligible or summary.reduced_match_eligible
    ):
        chase_label = match.winner == summary.batting_team

    return {
        "match_id": match.match_id,
        "match_date": (
            parse_match_date(match.date).isoformat()
            if parse_match_date(match.date) is not None
            else match.date
        ),
        "innings": summary.number,
        "state_sequence": state_sequence,
        "source_sequence": source_sequence,
        "batting_team": summary.batting_team,
        "bowling_team": summary.bowling_team,
        "venue": match.venue,
        "runs_so_far": runs,
        "wickets_lost": wickets,
        "wickets_remaining": max(0, 10 - wickets),
        "legal_balls_bowled": legal_balls,
        "balls_remaining": balls_remaining,
        "innings_ball_limit": ball_limit,
        "current_run_rate": crr,
        "progress": progress,
        "phase_absolute": phase_absolute(legal_balls),
        "phase_relative": (
            phase_relative(legal_balls, ball_limit)
            if ball_limit is not None and ball_limit > 0
            else None
        ),
        "is_reduced_match": summary.is_reduced,
        "target": target,
        "runs_required": runs_required,
        "required_run_rate": required_rate,
        "rrr_minus_crr": required_rate - crr if required_rate is not None else None,
        "toss_winner": match.toss_winner,
        "toss_decision": match.toss_decision,
        "batting_team_won_toss": (
            summary.batting_team == match.toss_winner
            if match.toss_winner is not None
            else None
        ),
        "terminal_status": terminal,
        "terminal_probability": terminal_probability,
        "previous_event_type": previous_event,
        "previous_event": previous_event,
        "final_score": summary.final_runs,
        "remaining_runs": max(0, summary.final_runs - runs),
        "chase_won": chase_label,
        "split": split_for_date(match.date),
        "first_innings_eligible": summary.first_innings_eligible,
        "chase_eligible": summary.chase_eligible,
        "is_japan_batting": summary.batting_team == "Japan",
        "is_japan_bowling": summary.bowling_team == "Japan",
        "is_japan_chasing": summary.number == 2 and summary.batting_team == "Japan",
        "is_japan_defending": summary.number == 2 and summary.bowling_team == "Japan",
        "sample_weight": 1.0 / (len(summary.deliveries) + 1),
    }


def _write_match_rows(
    writers: NormalizedDatasetWriters,
    match: CSV2Match,
    summaries: Mapping[int, _InningsSummary],
    exclusions: Sequence[Mapping[str, str]],
    quality_flags: Tuple[str, ...],
) -> Tuple[Mapping[str, Any], List[Mapping[str, Any]]]:
    normalized_match = _match_row(match, summaries, quality_flags)
    normalized_innings: List[Mapping[str, Any]] = []
    writers.append("matches", normalized_match)
    for exclusion in exclusions:
        writers.append(
            "exclusions",
            {
                "match_id": match.match_id,
                "model_scope": exclusion["model_scope"],
                "reason": exclusion["reason"],
                "detail": exclusion["detail"],
            },
        )

    for number, summary in sorted(summaries.items()):
        innings_row = _innings_row(match.match_id, summary)
        normalized_innings.append(innings_row)
        writers.append("innings", innings_row)
        writers.append(
            "states",
            _state_row(match, summary, 0, None, 0, 0, 0, "start"),
        )
        runs = 0
        wickets = 0
        legal_balls = 0
        for state_sequence, delivery in enumerate(summary.deliveries, start=1):
            delivery_team_wickets = 0
            for wicket_index, wicket in enumerate(delivery.wickets, start=1):
                try:
                    team_wicket = counts_as_team_wicket(wicket)
                except UnknownDismissalKindError:
                    team_wicket = False
                delivery_team_wickets += int(team_wicket)
                writers.append(
                    "wickets",
                    {
                        "match_id": match.match_id,
                        "innings": number,
                        "source_sequence": delivery.sequence,
                        "wicket_index": wicket_index,
                        "kind": wicket.kind,
                        "player_dismissed": wicket.player_dismissed,
                        "player_dismissed_id": wicket.player_dismissed_id,
                        "is_secondary": wicket.is_secondary,
                        "is_bowler_wicket": wicket.is_bowler_wicket,
                        "counts_as_team_wicket": team_wicket,
                        "fielder_names": list(wicket.fielder_names),
                        "fielder_ids": list(wicket.fielder_ids),
                    },
                )
            writers.append(
                "deliveries",
                {
                    "match_id": match.match_id,
                    "innings": number,
                    "state_sequence": state_sequence,
                    "source_sequence": delivery.sequence,
                    "ball": delivery.ball,
                    "actual_delivery": delivery.actual_delivery,
                    "over": delivery.over,
                    "batting_team": delivery.batting_team,
                    "bowling_team": delivery.bowling_team,
                    "striker": delivery.striker,
                    "striker_id": delivery.striker_id,
                    "non_striker": delivery.non_striker,
                    "non_striker_id": delivery.non_striker_id,
                    "bowler": delivery.bowler,
                    "bowler_id": delivery.bowler_id,
                    "runs_off_bat": delivery.runs_off_bat,
                    "extras": delivery.extras,
                    "total_runs": delivery.total_runs,
                    "wides": delivery.wides,
                    "noballs": delivery.noballs,
                    "byes": delivery.byes,
                    "legbyes": delivery.legbyes,
                    "penalty": delivery.penalty,
                    "legal_ball": delivery.legal_ball,
                    "team_wickets": delivery_team_wickets,
                    "is_boundary": delivery.is_boundary,
                    "is_super_over": delivery.is_super_over,
                    "extra_fields_json": (
                        json.dumps(
                            delivery.extra_fields,
                            ensure_ascii=False,
                            sort_keys=True,
                            separators=(",", ":"),
                        )
                        if delivery.extra_fields
                        else None
                    ),
                },
            )
            runs += delivery.total_runs
            wickets += delivery_team_wickets
            legal_balls += int(delivery.legal_ball)
            writers.append(
                "states",
                _state_row(
                    match,
                    summary,
                    state_sequence,
                    delivery.sequence,
                    runs,
                    wickets,
                    legal_balls,
                    _delivery_event(delivery, delivery_team_wickets),
                ),
            )
    return normalized_match, normalized_innings


def _materialize_model_ready_states(
    destination: Path,
    prematch_features: Sequence[Mapping[str, Any]],
    buffer_size: int,
) -> int:
    """Join context to states in bounded batches and write model-ready rows."""

    try:
        import pyarrow.parquet as parquet
    except ImportError as exc:  # pragma: no cover - required preparation dependency
        raise RuntimeError("PyArrow is required to materialize model-ready states") from exc

    feature_fields = (
        "pre_match_elo",
        "opponent_pre_match_elo",
        "elo_diff",
        "batting_form",
        "batting_form_delta",
        "bowling_suppression",
        "bowling_suppression_delta",
        "venue_prior",
        "venue_sample_count",
        "team_cold_start",
        "opponent_cold_start",
        "global_prior",
        "global_sample_count",
        "era_trend",
    )
    lookup = {
        (str(row["match_id"]), str(row["team"])): row
        for row in prematch_features
    }
    writer = BufferedParquetWriter(
        "model_ready_states",
        destination / "model_ready_states.parquet",
        buffer_size=buffer_size,
    )
    try:
        states_file = parquet.ParquetFile(destination / "states.parquet")
        for batch in states_file.iter_batches(batch_size=buffer_size):
            for state in batch.to_pylist():
                snapshot = lookup.get(
                    (str(state["match_id"]), str(state["batting_team"])), {}
                )
                merged = dict(state)
                for field in feature_fields:
                    merged[field] = snapshot.get(field)
                writer.append(merged)
        return writer.close()
    except Exception:
        writer.abort()
        raise


def prepare_dataset(
    zip_path: PathLike,
    output_dir: PathLike,
    buffer_size: int = 50_000,
    create_duckdb: bool = True,
    config_path: Optional[PathLike] = None,
    expected_sha256: Optional[str] = None,
) -> Mapping[str, Any]:
    """Build the complete normalized dataset and return its manifest dict."""

    source = Path(zip_path).expanduser().resolve()
    destination = Path(output_dir).expanduser().resolve()
    config_hash = None
    effective_config_hash = None
    loaded_config = None
    if config_path is not None:
        from cricket_japan_bi.wasp.config import load_wasp_config

        loaded_config = load_wasp_config(Path(config_path))
        config_hash = loaded_config.sha256
        effective_config_hash = loaded_config.canonical_values_sha256()
        if expected_sha256 is None:
            expected_sha256 = loaded_config.expected_source_sha256
    audit_json = destination / "audit.json"
    audit_markdown = destination / "audit.md"
    audit = audit_csv2_archive(source, expected_sha256=expected_sha256)
    if audit.unknown_dismissal_counts:
        raise UnknownDismissalKindError(
            "archive contains unknown dismissal kind(s): {}".format(
                ", ".join(audit.unknown_dismissal_counts)
            )
        )
    # Source integrity and the female/international/T20 cohort must pass
    # before any destination or normalized history is created.
    destination.mkdir(parents=True, exist_ok=True)
    generation_id = uuid4().hex
    incomplete_path = destination / ".build-in-progress.json"
    write_json_atomic(
        incomplete_path,
        {
            "generation_id": generation_id,
            "source_sha256": audit.source_sha256,
            "started_at": datetime.now(timezone.utc).isoformat(),
        },
    )
    write_audit_reports(audit, audit_json, audit_markdown)

    writers = NormalizedDatasetWriters(destination, buffer_size=buffer_size)
    exclusion_counts: Counter[str] = Counter()
    chronology_matches: List[Mapping[str, Any]] = []
    chronology_innings: List[Mapping[str, Any]] = []
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", CSV2RegistryWarning)
            for match in iter_csv2_matches(source):
                summaries, exclusions, quality_flags = _prepare_match(match)
                for exclusion in exclusions:
                    exclusion_counts[
                        "{}:{}".format(
                            exclusion["model_scope"], exclusion["reason"]
                        )
                    ] += 1
                normalized_match, normalized_innings = _write_match_rows(
                    writers, match, summaries, exclusions, quality_flags
                )
                chronology_matches.append(normalized_match)
                chronology_innings.extend(normalized_innings)
        # These inputs are match/innings summaries (not delivery states), so
        # retaining them for the date sort remains small while the 781k-row
        # delivery/state paths stay bounded and streaming.
        from cricket_japan_bi.wasp.features.chronology import (
            EloConfig,
            build_prematch_features,
            select_elo_k,
        )

        elo_selection = select_elo_k(chronology_matches)
        prematch_features = build_prematch_features(
            chronology_matches,
            chronology_innings,
            config=EloConfig(k_factor=elo_selection.selected_k),
        )
        for feature_row in prematch_features:
            writers.append("prematch_team_features", feature_row)
        row_counts = dict(writers.close())
        row_counts["model_ready_states"] = _materialize_model_ready_states(
            destination, prematch_features, buffer_size
        )
    except Exception:
        writers.abort()
        raise

    paths: Dict[str, str] = {
        name: str(destination / "{}.parquet".format(name)) for name in TABLE_NAMES
    }
    paths["audit_json"] = str(audit_json)
    paths["audit_markdown"] = str(audit_markdown)
    if create_duckdb:
        database = write_duckdb(destination)
        paths["duckdb"] = str(database)

    # Detect a source archive replacement during the long normalization pass.
    final_source_hash = sha256_file(source)
    if final_source_hash != audit.source_sha256:
        raise RuntimeError(
            "source archive changed during preparation: {} -> {}".format(
                audit.source_sha256, final_source_hash
            )
        )

    file_metadata: Dict[str, Mapping[str, Any]] = {}
    for name in TABLE_NAMES:
        path = destination / "{}.parquet".format(name)
        descriptor = json.dumps(
            list(TABLE_SCHEMAS[name].items()), separators=(",", ":")
        ).encode("utf-8")
        file_metadata[name] = {
            "path": path.name,
            "sha256": sha256_file(path),
            "size_bytes": path.stat().st_size,
            "rows": int(row_counts[name]),
            "schema_sha256": hashlib.sha256(descriptor).hexdigest(),
        }
    if create_duckdb:
        database_path = Path(paths["duckdb"])
        file_metadata["duckdb"] = {
            "path": database_path.name,
            "sha256": sha256_file(database_path),
            "size_bytes": database_path.stat().st_size,
        }
    for name, path in (("audit_json", audit_json), ("audit_markdown", audit_markdown)):
        file_metadata[name] = {
            "path": path.name,
            "sha256": sha256_file(path),
            "size_bytes": path.stat().st_size,
        }

    manifest = DatasetManifest(
        schema_version=SCHEMA_VERSION,
        source_path=str(source),
        source_sha256=audit.source_sha256,
        source_size_bytes=audit.source_size_bytes,
        generated_at=datetime.now(timezone.utc).isoformat(),
        csv2_versions=audit.csv2_versions,
        row_counts=row_counts,
        paths=paths,
        exclusion_counts=dict(sorted(exclusion_counts.items())),
        audit=audit.to_dict(),
        config_hash=config_hash,
        effective_config_hash=effective_config_hash,
        generation_id=generation_id,
        files=file_metadata,
        chronology={
            "selected_elo_k": elo_selection.selected_k,
            "validation_brier_by_k": dict(elo_selection.validation_brier),
            "evaluated_matches": elo_selection.evaluated_matches,
        },
    ).to_dict()
    manifest_path = destination / "manifest.json"
    paths["manifest"] = str(manifest_path)
    manifest["paths"] = dict(paths)
    write_json_atomic(manifest_path, manifest)
    incomplete_path.unlink(missing_ok=True)
    return manifest


__all__ = ["prepare_dataset"]
