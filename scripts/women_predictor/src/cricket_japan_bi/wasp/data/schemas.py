"""Stable normalized-table contracts.

Schemas are represented with dependency-free descriptors at import time.  The
``arrow_schema`` helper imports PyArrow lazily, allowing parser-only users to
import the package without the data-engineering extras installed.
"""

from __future__ import annotations

from collections import OrderedDict
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, Mapping, Optional, Tuple


SCHEMA_VERSION = "1.0.0"


MATCH_COLUMNS = OrderedDict(
    [
        ("match_id", "string"),
        ("match_date", "string"),
        ("season", "string"),
        ("match_type", "string"),
        ("team_type", "string"),
        ("gender", "string"),
        ("team_1", "string"),
        ("team_2", "string"),
        ("venue", "string"),
        ("city", "string"),
        ("toss_winner", "string"),
        ("toss_decision", "string"),
        ("winner", "string"),
        ("result", "string"),
        ("method", "string"),
        ("eliminator", "string"),
        ("bowl_out", "string"),
        ("scheduled_overs", "int32"),
        ("balls_per_over", "int16"),
        ("has_super_over", "bool"),
        ("has_bowl_out", "bool"),
        ("is_japan_match", "bool"),
        ("split", "string"),
        ("quality_flags", "list_string"),
        ("first_innings_eligible", "bool"),
        ("chase_eligible", "bool"),
        ("reduced_match_eligible", "bool"),
    ]
)

INNINGS_COLUMNS = OrderedDict(
    [
        ("match_id", "string"),
        ("innings", "int16"),
        ("batting_team", "string"),
        ("bowling_team", "string"),
        ("target_runs", "int32"),
        ("target_overs", "string"),
        ("target_balls", "int32"),
        ("target_source", "string"),
        ("innings_ball_limit", "int32"),
        ("final_runs", "int32"),
        ("final_wickets", "int16"),
        ("legal_balls", "int32"),
        ("physical_deliveries", "int32"),
        ("end_reason", "string"),
        ("is_main_innings", "bool"),
        ("is_reduced_match", "bool"),
        ("first_innings_eligible", "bool"),
        ("chase_eligible", "bool"),
        ("quality_flags", "list_string"),
    ]
)

DELIVERY_COLUMNS = OrderedDict(
    [
        ("match_id", "string"),
        ("innings", "int16"),
        ("state_sequence", "int32"),
        ("source_sequence", "int32"),
        ("ball", "string"),
        ("actual_delivery", "string"),
        ("over", "int16"),
        ("batting_team", "string"),
        ("bowling_team", "string"),
        ("striker", "string"),
        ("striker_id", "string"),
        ("non_striker", "string"),
        ("non_striker_id", "string"),
        ("bowler", "string"),
        ("bowler_id", "string"),
        ("runs_off_bat", "int16"),
        ("extras", "int16"),
        ("total_runs", "int16"),
        ("wides", "int16"),
        ("noballs", "int16"),
        ("byes", "int16"),
        ("legbyes", "int16"),
        ("penalty", "int16"),
        ("legal_ball", "bool"),
        ("team_wickets", "int16"),
        ("is_boundary", "bool"),
        ("is_super_over", "bool"),
        ("extra_fields_json", "string"),
    ]
)

WICKET_COLUMNS = OrderedDict(
    [
        ("match_id", "string"),
        ("innings", "int16"),
        ("source_sequence", "int32"),
        ("wicket_index", "int16"),
        ("kind", "string"),
        ("player_dismissed", "string"),
        ("player_dismissed_id", "string"),
        ("is_secondary", "bool"),
        ("is_bowler_wicket", "bool"),
        ("counts_as_team_wicket", "bool"),
        ("fielder_names", "list_string"),
        ("fielder_ids", "list_string"),
    ]
)

STATE_COLUMNS = OrderedDict(
    [
        ("match_id", "string"),
        ("match_date", "string"),
        ("innings", "int16"),
        ("state_sequence", "int32"),
        ("source_sequence", "int32"),
        ("batting_team", "string"),
        ("bowling_team", "string"),
        ("venue", "string"),
        ("runs_so_far", "int32"),
        ("wickets_lost", "int16"),
        ("wickets_remaining", "int16"),
        ("legal_balls_bowled", "int32"),
        ("balls_remaining", "int32"),
        ("innings_ball_limit", "int32"),
        ("current_run_rate", "float64"),
        ("progress", "float64"),
        ("phase_absolute", "string"),
        ("phase_relative", "string"),
        ("is_reduced_match", "bool"),
        ("target", "int32"),
        ("runs_required", "int32"),
        ("required_run_rate", "float64"),
        ("rrr_minus_crr", "float64"),
        ("toss_winner", "string"),
        ("toss_decision", "string"),
        ("batting_team_won_toss", "bool"),
        ("terminal_status", "string"),
        ("terminal_probability", "float64"),
        ("previous_event_type", "string"),
        ("previous_event", "string"),
        ("final_score", "int32"),
        ("remaining_runs", "int32"),
        ("chase_won", "bool"),
        ("split", "string"),
        ("first_innings_eligible", "bool"),
        ("chase_eligible", "bool"),
        ("is_japan_batting", "bool"),
        ("is_japan_bowling", "bool"),
        ("is_japan_chasing", "bool"),
        ("is_japan_defending", "bool"),
        ("sample_weight", "float64"),
    ]
)

PREMATCH_TEAM_FEATURE_COLUMNS = OrderedDict(
    [
        ("match_id", "string"),
        ("match_date", "string"),
        ("team", "string"),
        ("opponent", "string"),
        ("pre_match_elo", "float64"),
        ("opponent_pre_match_elo", "float64"),
        ("elo_diff", "float64"),
        ("batting_form", "float64"),
        ("batting_form_delta", "float64"),
        ("bowling_suppression", "float64"),
        ("bowling_suppression_delta", "float64"),
        ("venue_prior", "float64"),
        ("venue_sample_count", "float64"),
        ("team_cold_start", "bool"),
        ("opponent_cold_start", "bool"),
        ("global_prior", "float64"),
        ("global_sample_count", "float64"),
        ("era_trend", "float64"),
    ]
)

MODEL_READY_STATE_COLUMNS = OrderedDict(STATE_COLUMNS)
MODEL_READY_STATE_COLUMNS.update(
    [
        ("pre_match_elo", "float64"),
        ("opponent_pre_match_elo", "float64"),
        ("elo_diff", "float64"),
        ("batting_form", "float64"),
        ("batting_form_delta", "float64"),
        ("bowling_suppression", "float64"),
        ("bowling_suppression_delta", "float64"),
        ("venue_prior", "float64"),
        ("venue_sample_count", "float64"),
        ("team_cold_start", "bool"),
        ("opponent_cold_start", "bool"),
        ("global_prior", "float64"),
        ("global_sample_count", "float64"),
        ("era_trend", "float64"),
    ]
)

EXCLUSION_COLUMNS = OrderedDict(
    [
        ("match_id", "string"),
        ("model_scope", "string"),
        ("reason", "string"),
        ("detail", "string"),
    ]
)

TABLE_SCHEMAS: Mapping[str, Mapping[str, str]] = {
    "matches": MATCH_COLUMNS,
    "innings": INNINGS_COLUMNS,
    "deliveries": DELIVERY_COLUMNS,
    "wickets": WICKET_COLUMNS,
    "states": STATE_COLUMNS,
    "prematch_team_features": PREMATCH_TEAM_FEATURE_COLUMNS,
    "model_ready_states": MODEL_READY_STATE_COLUMNS,
    "exclusions": EXCLUSION_COLUMNS,
}


@dataclass(frozen=True)
class DatasetManifest:
    schema_version: str
    source_path: str
    source_sha256: str
    source_size_bytes: int
    generated_at: str
    csv2_versions: Tuple[str, ...]
    row_counts: Mapping[str, int]
    paths: Mapping[str, str]
    exclusion_counts: Mapping[str, int]
    audit: Mapping[str, Any]
    config_hash: Optional[str] = None
    effective_config_hash: Optional[str] = None
    generation_id: Optional[str] = None
    files: Mapping[str, Mapping[str, Any]] = field(default_factory=dict)
    chronology: Mapping[str, Any] = field(default_factory=dict)
    warnings: Tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result["csv2_versions"] = list(self.csv2_versions)
        result["warnings"] = list(self.warnings)
        return result


def arrow_schema(table_name: str) -> Any:
    """Return the explicit :class:`pyarrow.Schema` for a normalized table."""

    try:
        import pyarrow as pa
    except ImportError as exc:  # pragma: no cover - depends on installation
        raise RuntimeError(
            "PyArrow is required to prepare the WASP-style dataset"
        ) from exc

    primitive = {
        "string": pa.string(),
        "int16": pa.int16(),
        "int32": pa.int32(),
        "float64": pa.float64(),
        "bool": pa.bool_(),
        "list_string": pa.list_(pa.string()),
    }
    try:
        descriptor = TABLE_SCHEMAS[table_name]
    except KeyError as exc:
        raise KeyError("unknown normalized table: {}".format(table_name)) from exc
    return pa.schema([pa.field(name, primitive[kind]) for name, kind in descriptor.items()])


def conform_row(table_name: str, row: Mapping[str, Any]) -> Dict[str, Any]:
    """Return a row ordered and limited to the public schema columns."""

    try:
        columns = TABLE_SCHEMAS[table_name]
    except KeyError as exc:
        raise KeyError("unknown normalized table: {}".format(table_name)) from exc
    unknown = sorted(set(row).difference(columns))
    if unknown:
        raise ValueError(
            "{} row contains unknown column(s): {}".format(
                table_name, ", ".join(unknown)
            )
        )
    return {column: row.get(column) for column in columns}


__all__ = [
    "DELIVERY_COLUMNS",
    "DatasetManifest",
    "EXCLUSION_COLUMNS",
    "INNINGS_COLUMNS",
    "MATCH_COLUMNS",
    "MODEL_READY_STATE_COLUMNS",
    "PREMATCH_TEAM_FEATURE_COLUMNS",
    "SCHEMA_VERSION",
    "STATE_COLUMNS",
    "TABLE_SCHEMAS",
    "WICKET_COLUMNS",
    "arrow_schema",
    "conform_row",
]
