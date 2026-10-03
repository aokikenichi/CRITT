"""Deterministic source and cricket-quality audit for Cricsheet CSV2 archives."""

from __future__ import annotations

import hashlib
import json
import warnings
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Mapping, Optional, Tuple, Union

from cricket_japan_bi.csv2_parser import (
    CSV2ParseError,
    CSV2RegistryWarning,
    iter_csv2_match_info,
    iter_csv2_matches,
)

from .rules import (
    KNOWN_DISMISSAL_KINDS,
    NON_TEAM_WICKET_KINDS,
    exceptional_chase_reason,
    normalize_dismissal_kind,
    parse_match_date,
    resolve_second_innings_target,
)


PathLike = Union[str, Path]


class AuditInvariantError(RuntimeError):
    """Raised when a caller-supplied source invariant does not match."""


@dataclass(frozen=True)
class AuditReport:
    source_path: str
    source_sha256: str
    source_size_bytes: int
    generated_at: str
    csv2_versions: Tuple[str, ...]
    first_match_date: Optional[str]
    last_match_date: Optional[str]
    japan_first_match_date: Optional[str]
    japan_last_match_date: Optional[str]
    counts: Mapping[str, int]
    method_counts: Mapping[str, int]
    result_counts: Mapping[str, int]
    dismissal_counts: Mapping[str, int]
    unknown_dismissal_counts: Mapping[str, int]
    japan_opponent_counts: Mapping[str, int]
    exclusion_counts: Mapping[str, int]
    team_labels: Tuple[str, ...]

    @property
    def match_count(self) -> int:
        return int(self.counts.get("matches", 0))

    @property
    def delivery_count(self) -> int:
        return int(self.counts.get("deliveries", 0))

    def to_dict(self) -> Dict[str, Any]:
        payload = asdict(self)
        payload["csv2_versions"] = list(self.csv2_versions)
        payload["team_labels"] = list(self.team_labels)
        payload["source_cohort"] = {
            "gender": "female",
            "team_type": "international",
            "match_type": "T20",
            "validated_matches": self.match_count,
            "mixed_cohort_allowed": False,
        }
        return payload


def sha256_file(path: PathLike, chunk_size: int = 1024 * 1024) -> str:
    source = Path(path)
    digest = hashlib.sha256()
    with source.open("rb") as handle:
        while True:
            chunk = handle.read(chunk_size)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def validate_womens_t20i_archive(zip_path: PathLike) -> int:
    """Reject a mixed or mislabelled archive before reading any deliveries.

    Every metadata member is checked, rather than merely excluding bad
    matches from model datasets: otherwise those matches could still enter
    Elo, form and venue chronology.  Missing required fields are rejected by
    the CSV2 parser and surfaced as the same source-invariant failure.
    """

    source = Path(zip_path).expanduser().resolve()
    expected = {"gender": "female", "team_type": "international", "match_type": "t20"}
    match_count = 0
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", CSV2RegistryWarning)
            for metadata in iter_csv2_match_info(source):
                for field, value in expected.items():
                    actual = str(getattr(metadata, field, None) or "").strip().casefold()
                    if actual != value:
                        raise AuditInvariantError(
                            "Women's T20I source cohort violation: match {} has {}={!r}; "
                            "required {!r}".format(
                                metadata.match_id, field, getattr(metadata, field, None), value
                            )
                        )
                match_count += 1
    except CSV2ParseError as exc:
        raise AuditInvariantError("Women's T20I source metadata invalid: {}".format(exc)) from exc
    if not match_count:
        raise AuditInvariantError("Women's T20I archive contains no matches")
    return match_count


def _exclusive_metadata_exclusion(metadata: Any) -> Optional[str]:
    reason = exceptional_chase_reason(metadata)
    if reason:
        return reason
    target = metadata.targets.get(2)
    if target is None or target.runs is None or target.balls is None:
        return "missing_or_incomplete_target"
    if target.balls != 120:
        return "reduced_target"
    if metadata.overs != 20 or metadata.balls_per_over != 6:
        return "nonstandard_scheduled_quota"
    return None


def audit_csv2_archive(
    zip_path: PathLike,
    output_json: Optional[PathLike] = None,
    output_markdown: Optional[PathLike] = None,
    expected_sha256: Optional[str] = None,
) -> AuditReport:
    """Scan every match and return a reproducible audit summary.

    The scan counts physical delivery rows.  Legal balls are derived solely
    from the wide/no-ball flags and never from the display ``ball`` or
    ``actual_delivery`` identifiers.
    """

    source = Path(zip_path).expanduser().resolve()
    if not source.is_file():
        raise FileNotFoundError("CSV2 archive not found: {}".format(source))
    source_hash = sha256_file(source)
    if expected_sha256 and source_hash.casefold() != expected_sha256.casefold():
        raise AuditInvariantError(
            "source SHA-256 mismatch: expected {}, found {}".format(
                expected_sha256, source_hash
            )
        )

    validated_matches = validate_womens_t20i_archive(source)

    counts: Counter[str] = Counter()
    methods: Counter[str] = Counter()
    results: Counter[str] = Counter()
    dismissals: Counter[str] = Counter()
    unknown_dismissals: Counter[str] = Counter()
    opponents: Counter[str] = Counter()
    exclusions: Counter[str] = Counter()
    versions = set()
    teams = set()
    dates = []
    japan_dates = []

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", CSV2RegistryWarning)
        for match in iter_csv2_matches(source):
            metadata = match.metadata
            counts["matches"] += 1
            versions.add(metadata.format_version)
            teams.update(metadata.teams)
            parsed_date = parse_match_date(metadata.date)
            if parsed_date is not None:
                dates.append(parsed_date)

            is_japan = "Japan" in metadata.teams
            if is_japan:
                counts["japan_matches"] += 1
                if parsed_date is not None:
                    japan_dates.append(parsed_date)
                for team in metadata.teams:
                    if team != "Japan":
                        opponents[team] += 1

            method = (metadata.outcome.method or "").strip()
            result = (metadata.outcome.result or "").strip()
            methods[method or "none"] += 1
            results[result or "decisive"] += 1
            if method.casefold() in {"d/l", "dls"}:
                counts["dls_matches"] += 1
            if method.casefold() == "awarded" or result.casefold() == "awarded":
                counts["awarded_matches"] += 1
            if result.casefold() == "no result":
                counts["no_result_matches"] += 1
            if result.casefold() == "tie":
                counts["tie_matches"] += 1
            if metadata.super_over_innings or metadata.outcome.eliminator:
                counts["super_over_matches"] += 1
            if metadata.outcome.bowl_out:
                counts["bowl_out_matches"] += 1
            if metadata.overs == 50:
                counts["scheduled_overs_50"] += 1

            explicit_target = metadata.targets.get(2)
            if explicit_target is None:
                counts["targets_missing"] += 1
            else:
                counts["targets_present"] += 1
                if explicit_target.balls == 120:
                    counts["target_20_overs"] += 1
                elif explicit_target.balls is not None and explicit_target.balls < 120:
                    counts["target_under_20_overs"] += 1
                    if method.casefold() not in {"d/l", "dls"}:
                        counts["reduced_targets_without_method"] += 1

            reason = _exclusive_metadata_exclusion(metadata)
            if reason is None:
                counts["strict_full_chase_cohort"] += 1
                if is_japan:
                    counts["strict_full_chase_japan"] += 1
            else:
                exclusions[reason] += 1

            per_innings_runs: Counter[int] = Counter()
            per_innings_legal: Counter[int] = Counter()
            main_innings = set()
            for delivery in match.deliveries:
                counts["deliveries"] += 1
                per_innings_runs[delivery.innings] += delivery.total_runs
                if delivery.legal_ball:
                    counts["legal_balls"] += 1
                    per_innings_legal[delivery.innings] += 1
                if delivery.wides:
                    counts["wide_deliveries"] += 1
                if delivery.noballs:
                    counts["no_ball_deliveries"] += 1
                if delivery.is_main_innings:
                    main_innings.add(delivery.innings)
                for wicket in delivery.wickets:
                    counts["wicket_events"] += 1
                    kind = normalize_dismissal_kind(wicket.kind)
                    dismissals[kind] += 1
                    if kind in NON_TEAM_WICKET_KINDS:
                        counts["non_team_wicket_events"] += 1
                    elif kind in KNOWN_DISMISSAL_KINDS:
                        counts["team_wicket_events"] += 1
                    else:
                        unknown_dismissals[kind] += 1

            if any(
                legal > 120 for innings, legal in per_innings_legal.items()
                if innings in (1, 2)
            ):
                counts["matches_with_overlong_main_innings"] += 1
            if explicit_target is None:
                resolution = resolve_second_innings_target(
                    metadata,
                    per_innings_runs.get(1),
                    len(main_innings),
                )
                if resolution.source == "reconstructed":
                    counts["reconstructable_missing_targets"] += 1

    if counts["matches"] != validated_matches:
        raise AuditInvariantError(
            "source metadata/delivery match count mismatch: {} vs {}".format(
                validated_matches, counts["matches"]
            )
        )

    # Preserve important zero-valued keys so report consumers have a stable
    # contract even for tiny fixtures.
    stable_count_keys = (
        "matches",
        "deliveries",
        "legal_balls",
        "wide_deliveries",
        "no_ball_deliveries",
        "wicket_events",
        "team_wicket_events",
        "non_team_wicket_events",
        "teams",
        "japan_matches",
        "targets_present",
        "targets_missing",
        "reconstructable_missing_targets",
        "target_20_overs",
        "target_under_20_overs",
        "reduced_targets_without_method",
        "dls_matches",
        "awarded_matches",
        "no_result_matches",
        "tie_matches",
        "super_over_matches",
        "bowl_out_matches",
        "scheduled_overs_50",
        "strict_full_chase_cohort",
        "strict_full_chase_japan",
    )
    counts["teams"] = len(teams)
    normalized_counts = {key: int(counts.get(key, 0)) for key in stable_count_keys}
    for key in sorted(set(counts).difference(normalized_counts)):
        normalized_counts[key] = int(counts[key])

    report = AuditReport(
        source_path=str(source),
        source_sha256=source_hash,
        source_size_bytes=source.stat().st_size,
        generated_at=datetime.now(timezone.utc).isoformat(),
        csv2_versions=tuple(sorted(versions)),
        first_match_date=min(dates).isoformat() if dates else None,
        last_match_date=max(dates).isoformat() if dates else None,
        japan_first_match_date=min(japan_dates).isoformat() if japan_dates else None,
        japan_last_match_date=max(japan_dates).isoformat() if japan_dates else None,
        counts=normalized_counts,
        method_counts=dict(sorted(methods.items())),
        result_counts=dict(sorted(results.items())),
        dismissal_counts=dict(sorted(dismissals.items())),
        unknown_dismissal_counts=dict(sorted(unknown_dismissals.items())),
        japan_opponent_counts=dict(
            sorted(opponents.items(), key=lambda item: (-item[1], item[0]))
        ),
        exclusion_counts=dict(sorted(exclusions.items())),
        team_labels=tuple(sorted(teams)),
    )
    if output_json is not None or output_markdown is not None:
        write_audit_reports(report, output_json, output_markdown)
    return report


def audit_markdown(report: AuditReport) -> str:
    counts = report.counts
    lines = [
        "# Cricsheet CSV2 WASP-style data audit",
        "",
        "- Source: `{}`".format(report.source_path),
        "- SHA-256: `{}`".format(report.source_sha256),
        "- Period: {} to {}".format(
            report.first_match_date or "unknown", report.last_match_date or "unknown"
        ),
        "- Matches: {:,}".format(counts["matches"]),
        "- Source cohort: female / international / T20 (all metadata validated; mixed cohorts rejected)",
        "- Physical deliveries: {:,}".format(counts["deliveries"]),
        "- Legal balls: {:,}".format(counts["legal_balls"]),
        "- Japan matches: {:,}".format(counts["japan_matches"]),
        "- Strict full-20-over chase cohort: {:,}".format(
            counts["strict_full_chase_cohort"]
        ),
        "",
        "## Counts",
        "",
        "| Metric | Count |",
        "|---|---:|",
    ]
    lines.extend(
        "| `{}` | {:,} |".format(key, value)
        for key, value in sorted(counts.items())
    )
    lines.extend(["", "## Exclusive chase exclusions", "", "| Reason | Count |", "|---|---:|"])
    lines.extend(
        "| `{}` | {:,} |".format(key, value)
        for key, value in report.exclusion_counts.items()
    )
    if report.unknown_dismissal_counts:
        lines.extend(
            [
                "",
                "## Audit errors: unknown dismissal kinds",
                "",
                "Unknown kinds are never guessed and must be classified before training.",
                "",
            ]
        )
        lines.extend(
            "- `{}`: {:,}".format(key, value)
            for key, value in report.unknown_dismissal_counts.items()
        )
    lines.append("")
    return "\n".join(lines)


def write_audit_reports(
    report: AuditReport,
    output_json: Optional[PathLike],
    output_markdown: Optional[PathLike],
) -> None:
    if output_json is not None:
        json_path = Path(output_json)
        json_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(
            json.dumps(report.to_dict(), ensure_ascii=False, indent=2, sort_keys=True)
            + "\n",
            encoding="utf-8",
        )
    if output_markdown is not None:
        markdown_path = Path(output_markdown)
        markdown_path.parent.mkdir(parents=True, exist_ok=True)
        markdown_path.write_text(audit_markdown(report), encoding="utf-8")


__all__ = [
    "AuditInvariantError",
    "AuditReport",
    "audit_csv2_archive",
    "audit_markdown",
    "sha256_file",
    "validate_womens_t20i_archive",
    "write_audit_reports",
]
