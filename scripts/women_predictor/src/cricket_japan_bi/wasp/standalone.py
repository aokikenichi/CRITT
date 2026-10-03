"""Build the self-contained, offline Japan Women T20 WASP-style application.

The production artifact remains the source of truth.  This module extracts
its browser-safe inference representation and only the Japan match replays,
then asks :mod:`cricket_japan_bi.wasp.export.web` to compose one HTML file.
No raw CSV2 data or Python estimator objects are included in the output.
"""

from __future__ import annotations

import json
import math
import os
import tempfile
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping, Optional, Sequence

from .export import (
    browser_runtime_source,
    canonical_json,
    predict_chase,
    predict_first,
    serialize_bundle_inference,
)
from .export.web import render_standalone_html
from .models.contracts import ArtifactBundle
from .models.service import PredictionService


STANDALONE_PAYLOAD_SCHEMA_VERSION = "japan-t20-wasp-standalone/1.0"
PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_ARTIFACT_DIR = PROJECT_ROOT / "artifacts" / "wasp"
DEFAULT_OUTPUT_PATH = PROJECT_ROOT.parents[1] / "japan-women-t20-predictor.html"
DEFAULT_TITLE = "日本女子代表 T20 WASP-style オフライン分析"

_MATCH_FIELDS = (
    "match_id",
    "match_date",
    "team_1",
    "team_2",
    "venue",
    "city",
    "winner",
    "result",
    "method",
    "scheduled_overs",
    "balls_per_over",
    "toss_winner",
    "toss_decision",
    "has_super_over",
    "has_bowl_out",
    "split",
    "gender",
    "team_type",
    "match_type",
    "first_innings_eligible",
    "chase_eligible",
    "reduced_match_eligible",
    "quality_flags",
    "model_exclusions",
)


class StandaloneParityError(RuntimeError):
    """Raised when portable inference differs from the Python service."""


def _json_safe(value: Any) -> Any:
    """Normalize NumPy scalars/arrays and reject non-finite JSON values."""

    return json.loads(canonical_json(value))


def _is_japan_match(row: Mapping[str, Any]) -> bool:
    teams = {
        str(row.get("team_1") or ""),
        str(row.get("team_2") or ""),
        *(str(team) for team in (row.get("teams") or ())),
    }
    return bool(row.get("is_japan_match")) or "Japan" in teams


def _compact_match(row: Mapping[str, Any]) -> Mapping[str, Any]:
    return _json_safe({field: row.get(field) for field in _MATCH_FIELDS})


def _compact_replay_rows(
    rows: Iterable[Mapping[str, Any]], *, innings: int, prediction_supported: bool = True
) -> Sequence[Mapping[str, Any]]:
    compact = []
    for row in rows:
        value: Dict[str, Any] = {
            "legal_balls_bowled": int(row.get("legal_balls_bowled") or 0),
            "runs_so_far": int(row.get("runs_so_far") or 0),
            "wickets_lost": int(row.get("wickets_lost") or 0),
            "event": str(row.get("event") or ""),
            "selected": (
                float(row["selected"])
                if prediction_supported
                and row.get("selected") is not None
                and math.isfinite(float(row["selected"]))
                else None
            ),
        }
        if innings == 2:
            value["terminal_status"] = row.get("terminal_status")
            value["experimental_reduced"] = bool(
                row.get("experimental_reduced", False)
            )
        compact.append(value)
    return compact


def _compact_replay(
    replay: Mapping[str, Any],
    match: Mapping[str, Any],
    *,
    reduced_enabled: bool,
) -> Mapping[str, Any]:
    first_supported = bool(match.get("first_innings_eligible", True))
    chase_supported = bool(match.get("chase_eligible", True)) or (
        reduced_enabled and bool(match.get("reduced_match_eligible", False))
    )
    return {
        "first_innings": _compact_replay_rows(
            replay.get("first_innings") or (),
            innings=1,
            prediction_supported=first_supported,
        ),
        "chase": _compact_replay_rows(
            replay.get("chase") or (),
            innings=2,
            prediction_supported=chase_supported,
        ),
    }


def build_standalone_payload(bundle: ArtifactBundle) -> Mapping[str, Any]:
    """Return a deterministic, JSON-safe payload for the standalone UI."""

    bundle.validate_serving()
    service = PredictionService(bundle)
    inference = dict(serialize_bundle_inference(bundle))

    japan_rows = sorted(
        (dict(row) for row in bundle.matches if _is_japan_match(row)),
        key=lambda row: (
            str(row.get("match_date") or row.get("date") or ""),
            str(row.get("match_id") or ""),
        ),
        reverse=True,
    )
    japan_matches = [_compact_match(row) for row in japan_rows]
    replay_ids = [str(row.get("match_id") or "") for row in japan_rows]
    matches_by_id = {str(row.get("match_id") or ""): row for row in japan_rows}
    replays = {
        match_id: _compact_replay(
            bundle.replays[match_id],
            matches_by_id[match_id],
            reduced_enabled=bool(bundle.manifest.reduced_match_enabled),
        )
        for match_id in replay_ids
        if match_id in bundle.replays
        and isinstance(bundle.replays[match_id], Mapping)
    }

    metadata = dict(service.metadata())
    metadata.update(
        {
            "generated_at": bundle.manifest.created_at,
            "standalone_scope": "japan_matches",
            "standalone_match_count": len(japan_matches),
            "standalone_replay_count": len(replays),
            "model_content_sha256": inference["content_sha256"],
        }
    )
    if metadata.get("date_from") and metadata.get("date_to"):
        metadata["period"] = "{}〜{}".format(
            metadata["date_from"], metadata["date_to"]
        )

    reduced_gate = {}
    if isinstance(bundle.evaluation, Mapping):
        candidate = bundle.evaluation.get("reduced_match_gate")
        if isinstance(candidate, Mapping):
            reduced_gate = dict(candidate)
    reduced_gate["enabled"] = bool(bundle.manifest.reduced_match_enabled)

    # Keep the comparatively large executable model spec in one place.  The
    # browser runtime consumes ``inference`` while the small duplicated option
    # lists make the UI contract explicit and independent of model internals.
    payload: Dict[str, Any] = {
        "standalone_schema_version": STANDALONE_PAYLOAD_SCHEMA_VERSION,
        "generated_at": bundle.manifest.created_at,
        "metadata": metadata,
        "model_info": service.model_info(),
        "models": dict(bundle.manifest.selected_models),
        "known_teams": list(inference.get("known_teams") or ()),
        "known_venues": list(inference.get("known_venues") or ()),
        "reduced_match_enabled": bool(bundle.manifest.reduced_match_enabled),
        "japan_matches": japan_matches,
        "replays": replays,
        "evaluation": bundle.evaluation,
        "japan_gates": bundle.manifest.japan_gates,
        "reduced_match_gate": reduced_gate,
        "inference": inference,
    }
    return _json_safe(payload)


def _known_pair(bundle: ArtifactBundle) -> tuple[str, str]:
    teams = [str(team) for team in bundle.known_teams]
    batting = "Japan" if "Japan" in teams else (teams[0] if teams else "Japan")
    preferred = "Indonesia" if "Indonesia" in teams else None
    bowling = preferred or next(
        (team for team in teams if team != batting), "Opponent"
    )
    return batting, bowling


def _assert_close(left: Any, right: Any, label: str) -> None:
    if left is None or right is None:
        if left is not None or right is not None:
            raise StandaloneParityError(
                "{} differs: Python={!r}, portable={!r}".format(label, left, right)
            )
        return
    if not math.isclose(float(left), float(right), rel_tol=1e-9, abs_tol=1e-9):
        raise StandaloneParityError(
            "{} differs: Python={!r}, portable={!r}".format(label, left, right)
        )


def verify_prediction_parity(
    bundle: ArtifactBundle, inference: Optional[Mapping[str, Any]] = None
) -> None:
    """Check portable inference against representative Python predictions."""

    exported = inference or serialize_bundle_inference(bundle)
    service = PredictionService(bundle)
    batting, bowling = _known_pair(bundle)
    venue = str(bundle.known_venues[0]) if bundle.known_venues else None
    first_input = {
        "batting_team": batting,
        "bowling_team": bowling,
        "runs": 62,
        "wickets": 3,
        "completed": {"overs": 10, "balls": 0},
        "quota": {"overs": 20, "balls": 0},
        "venue": venue,
        "use_japan_correction": True,
    }
    chase_input = {
        "chasing_team": batting,
        "defending_team": bowling,
        "toss_winner": batting,
        "target": 130,
        "current_score": 76,
        "wickets": 4,
        "target_ball_limit": {"overs": 20, "balls": 0},
        "balls_remaining": 48,
        "venue": venue,
        "use_japan_correction": True,
    }

    python_first = service.predict_first_innings(first_input)
    portable_first = predict_first(exported, first_input)
    for name in ("global", "team_adjusted", "japan_adjusted", "selected"):
        _assert_close(
            python_first["comparison"].get(name),
            portable_first["comparison"].get(name),
            "first.comparison.{}".format(name),
        )
    for coverage in ("p50", "p80"):
        for bound in ("lower", "upper"):
            _assert_close(
                python_first["intervals"][coverage][bound],
                portable_first["intervals"][coverage][bound],
                "first.intervals.{}.{}".format(coverage, bound),
            )

    python_chase = service.predict_chase(chase_input)
    portable_chase = predict_chase(exported, chase_input)
    for name in ("global", "team_adjusted", "japan_adjusted", "selected"):
        _assert_close(
            python_chase["comparison"].get(name),
            portable_chase["comparison"].get(name),
            "chase.comparison.{}".format(name),
        )
    if len(python_chase["scenarios"]) != len(portable_chase["scenarios"]):
        raise StandaloneParityError("chase scenario count differs")
    for index, (python_row, portable_row) in enumerate(
        zip(python_chase["scenarios"], portable_chase["scenarios"])
    ):
        _assert_close(
            python_row.get("win_probability"),
            portable_row.get("win_probability"),
            "chase.scenarios[{}]".format(index),
        )


def render_standalone_document(
    bundle: ArtifactBundle,
    *,
    title: str = DEFAULT_TITLE,
    verify_parity: bool = True,
) -> str:
    """Render a complete HTML document from a validated artifact bundle."""

    payload = build_standalone_payload(bundle)
    if verify_parity:
        verify_prediction_parity(bundle, payload["inference"])
    return render_standalone_html(payload, browser_runtime_source(), title=title)


def _atomic_write_text(path: Path, value: str) -> Path:
    destination = Path(path).expanduser().resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=".{}.".format(destination.name),
        suffix=".tmp",
        dir=str(destination.parent),
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="") as handle:
            handle.write(value)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary, 0o644)
        os.replace(temporary, destination)
    except BaseException:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass
        raise
    return destination


def export_standalone_html(
    *,
    artifact_dir: Path = DEFAULT_ARTIFACT_DIR,
    output_path: Path = DEFAULT_OUTPUT_PATH,
    title: str = DEFAULT_TITLE,
    verify_parity: bool = True,
) -> Path:
    """Load an artifact and atomically write the standalone HTML file."""

    bundle = ArtifactBundle.load(Path(artifact_dir).expanduser().resolve())
    html = render_standalone_document(
        bundle, title=title, verify_parity=verify_parity
    )
    return _atomic_write_text(output_path, html)


__all__ = [
    "DEFAULT_ARTIFACT_DIR",
    "DEFAULT_OUTPUT_PATH",
    "DEFAULT_TITLE",
    "STANDALONE_PAYLOAD_SCHEMA_VERSION",
    "StandaloneParityError",
    "build_standalone_payload",
    "export_standalone_html",
    "render_standalone_document",
    "verify_prediction_parity",
]
