"""Compact replay payloads derived from historical state predictions."""

from __future__ import annotations

from typing import Any, Dict, List, Mapping, Sequence


def build_replay_payload(
    match: Mapping[str, Any],
    states: Sequence[Mapping[str, Any]],
    *,
    first_predictions: Mapping[int, float] = {},
    chase_predictions: Mapping[int, float] = {},
) -> Mapping[str, Any]:
    points: List[Mapping[str, Any]] = []
    for row in sorted(states, key=lambda item: (int(item.get("innings") or 0), int(item.get("state_sequence") or 0))):
        sequence = int(row.get("state_sequence") or 0)
        innings = int(row.get("innings") or 0)
        point: Dict[str, Any] = {
            "innings": innings,
            "state_sequence": sequence,
            "source_sequence": row.get("source_sequence"),
            "runs": int(row.get("runs_so_far") or 0),
            "wickets": int(row.get("wickets_lost") or 0),
            "legal_balls": int(row.get("legal_balls_bowled") or 0),
            "event": row.get("previous_event_type"),
            "terminal_status": row.get("terminal_status"),
        }
        if innings == 1:
            point["predicted_final_score"] = first_predictions.get(sequence)
        elif innings == 2:
            point["win_probability"] = chase_predictions.get(sequence)
        points.append(point)
    return {
        "match_id": str(match.get("match_id") or ""),
        "match_date": match.get("match_date") or match.get("date"),
        "teams": match.get("teams") or [match.get("team_1"), match.get("team_2")],
        "winner": match.get("winner"),
        "venue": match.get("venue"),
        "points": points,
    }


def group_replays(
    matches: Sequence[Mapping[str, Any]], states: Sequence[Mapping[str, Any]]
) -> Mapping[str, Any]:
    by_match: Dict[str, List[Mapping[str, Any]]] = {}
    for row in states:
        by_match.setdefault(str(row.get("match_id") or ""), []).append(row)
    return {
        str(match.get("match_id") or ""): build_replay_payload(
            match, by_match.get(str(match.get("match_id") or ""), [])
        )
        for match in matches
    }
