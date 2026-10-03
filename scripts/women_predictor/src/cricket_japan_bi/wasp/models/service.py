"""Read-only artifact-backed prediction service used by every UI surface."""

from __future__ import annotations

import math
import os
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from ..features.states import chase_terminal, phase_absolute, phase_relative
from .chase import next_ball_scenarios, predict_win_probability
from .contracts import ArtifactBundle, CorrectionStatus, PredictionComparison
from .first_innings import predict_final_score
from .japan import chase_role, correction_for_role, first_innings_role


class ArtifactUnavailableError(RuntimeError):
    """Raised when a validated offline artifact cannot be loaded."""


class UnsupportedReducedMatchError(ValueError):
    """Raised when the shortened-match activation gate did not pass."""

    code = "unsupported_reduced_match"


class MatchNotFoundError(LookupError):
    """Requested replay/match identifier is absent from the artifact."""


def _mapping(value: Any) -> Mapping[str, Any]:
    if value is None:
        return {}
    if isinstance(value, Mapping):
        return value
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    if hasattr(value, "dict"):
        return value.dict()
    raise TypeError("expected mapping-like prediction payload")


def _json_safe(value: Any) -> Any:
    """Normalize Parquet/NumPy scalar and list values at the service boundary."""

    if isinstance(value, Mapping):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_json_safe(item) for item in value]
    module = value.__class__.__module__ if value is not None else ""
    if module.startswith("numpy") and hasattr(value, "tolist"):
        return _json_safe(value.tolist())
    if hasattr(value, "isoformat") and not isinstance(value, str):
        try:
            return value.isoformat()
        except (TypeError, ValueError):
            pass
    return value


def _value(payload: Mapping[str, Any], *names: str, default: Any = None) -> Any:
    for name in names:
        value = payload.get(name)
        if value is not None:
            return value
    return default


def _quota_balls(value: Any, *, default: int = 120) -> int:
    if value is None:
        return default
    if isinstance(value, (int, float)):
        return int(value)
    quota = _mapping(value)
    if quota.get("total_balls") is not None:
        return int(quota["total_balls"])
    return int(quota.get("overs") or 0) * 6 + int(quota.get("balls") or 0)


def _completed_balls(payload: Mapping[str, Any]) -> int:
    structured = _value(payload, "completed", "current", "completed_quota")
    if structured is not None:
        return _quota_balls(structured, default=0)
    if payload.get("legal_balls_bowled") is not None:
        return int(payload["legal_balls_bowled"])
    return int(_value(payload, "completed_overs", "overs", default=0)) * 6 + int(
        _value(payload, "completed_balls", "balls", default=0)
    )


def _predict_probability(model: Any, state: Mapping[str, Any]) -> Optional[float]:
    return predict_win_probability(model, state)


class PredictionService:
    """Serve predictions without touching the raw ZIP or fitting models."""

    def __init__(self, bundle: ArtifactBundle, artifact_dir: Optional[Path] = None) -> None:
        bundle.validate_serving()
        self.bundle = bundle
        self.artifact_dir = Path(artifact_dir) if artifact_dir else None
        self._matches = {
            str(row.get("match_id") or ""): _json_safe(dict(row))
            for row in bundle.matches
        }

    @classmethod
    def load_default(cls, artifact_dir: Optional[Any] = None) -> "PredictionService":
        candidates: List[Path] = []
        if artifact_dir is not None:
            candidates.append(Path(artifact_dir))
        environment_path = os.environ.get("CRICKET_WASP_ARTIFACT_DIR")
        if environment_path:
            candidates.append(Path(environment_path))
        project_root = Path(__file__).resolve().parents[4]
        candidates.extend(
            [
                Path.cwd() / "artifacts" / "wasp",
                project_root / "artifacts" / "wasp",
            ]
        )
        seen = set()
        errors: List[str] = []
        for candidate in candidates:
            resolved = candidate.resolve()
            if resolved in seen:
                continue
            seen.add(resolved)
            try:
                bundle = ArtifactBundle.load(resolved)
                config_override = os.environ.get("CRICKET_WASP_CONFIG")
                config_path = (
                    Path(config_override).expanduser().resolve()
                    if config_override
                    else project_root / "config" / "wasp.toml"
                )
                if config_path.is_file():
                    from ..config import load_wasp_config

                    config = load_wasp_config(config_path)
                    if bundle.manifest.config_sha256 != config.sha256:
                        raise ArtifactUnavailableError(
                            "artifact/config SHA-256 mismatch"
                        )
                return cls(bundle, resolved)
            except Exception as exc:
                errors.append("{}: {}".format(resolved, exc))
        raise ArtifactUnavailableError(
            "validated WASP-style artifacts are unavailable ({})".format(
                "; ".join(errors) if errors else "no artifact path"
            )
        )

    def metadata(self) -> Mapping[str, Any]:
        manifest = self.bundle.manifest
        dates = [str(row.get("match_date") or row.get("date") or "") for row in self.bundle.matches]
        japan_matches = sum(
            1
            for row in self.bundle.matches
            if "Japan" in {
                str(row.get("team_1") or ""),
                str(row.get("team_2") or ""),
                *(str(team) for team in (row.get("teams") or ())),
            }
        )
        return {
            "product": "日本女子代表向け T20 WASP-style 分析",
            "source": "Cricsheet Women's T20 International CSV2",
            "gender": "female",
            "team_type": "international",
            "match_type": "T20",
            "cohort": {
                "gender": "female",
                "team_type": "international",
                "match_type": "T20",
            },
            "replay_model_role": "production_refit_all_periods",
            "replay_note": (
                "Replayは女子T20I全期間で再学習したproductionモデルによる振り返りです。"
                "チーム情報は試合前日のsnapshotを使いますが、未学習試合の性能評価ではありません。"
                "評価画面には2024年末までで学習した別モデルのlocked testを表示します。"
            ),
            "official_wasp_reproduction": False,
            "source_sha256": manifest.source_sha256,
            "source_cutoff": manifest.source_cutoff,
            "schema_version": manifest.schema_version,
            "created_at": manifest.created_at,
            "bundle_role": manifest.bundle_role,
            "evaluation_role": manifest.evaluation_role,
            "match_count": len(self.bundle.matches),
            "japan_match_count": japan_matches,
            "date_from": min((value for value in dates if value), default=None),
            "date_to": max((value for value in dates if value), default=None),
            "selected_models": dict(manifest.selected_models),
            "reduced_match_enabled": manifest.reduced_match_enabled,
            "counts": dict(
                (manifest.metrics.get("data") or {}).get("audit_counts", {})
                if isinstance(manifest.metrics, Mapping)
                else {}
            ),
            "row_counts": dict(
                (manifest.metrics.get("data") or {}).get("row_counts", {})
                if isinstance(manifest.metrics, Mapping)
                else {}
            ),
            "exclusions": dict(
                (manifest.metrics.get("data") or {}).get("exclusion_counts", {})
                if isinstance(manifest.metrics, Mapping)
                else {}
            ),
            "limitations": list(manifest.limitations),
        }

    def model_info(self) -> Mapping[str, Any]:
        manifest = self.bundle.manifest
        return {
            "schema_version": manifest.schema_version,
            "bundle_role": manifest.bundle_role,
            "evaluation_role": manifest.evaluation_role,
            "selected_models": dict(manifest.selected_models),
            "feature_schema": {
                key: list(value) for key, value in manifest.feature_schema.items()
            },
            "split": dict(manifest.split),
            "library_versions": dict(manifest.library_versions),
            "japan_gates": dict(manifest.japan_gates),
            "limitations": list(manifest.limitations),
        }

    def list_matches(
        self,
        *,
        japan_only: bool = False,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        cursor: Optional[str] = None,
        limit: int = 50,
    ) -> Mapping[str, Any]:
        rows = sorted(
            self._matches.values(),
            key=lambda row: (str(row.get("match_date") or row.get("date") or ""), str(row.get("match_id") or "")),
            reverse=True,
        )
        if japan_only:
            rows = [
                row
                for row in rows
                if "Japan"
                in {
                    str(row.get("team_1") or ""),
                    str(row.get("team_2") or ""),
                    *(str(team) for team in (row.get("teams") or ())),
                }
            ]
        from_text = (
            from_date.isoformat() if hasattr(from_date, "isoformat") else str(from_date)
        ) if from_date else None
        to_text = (
            to_date.isoformat() if hasattr(to_date, "isoformat") else str(to_date)
        ) if to_date else None
        if from_text:
            rows = [row for row in rows if str(row.get("match_date") or row.get("date") or "") >= from_text]
        if to_text:
            rows = [row for row in rows if str(row.get("match_date") or row.get("date") or "") <= to_text]
        start = int(cursor or 0)
        page_limit = min(200, max(1, int(limit)))
        page = rows[start : start + page_limit]
        next_cursor = str(start + page_limit) if start + page_limit < len(rows) else None
        return {"items": page, "next_cursor": next_cursor, "total": len(rows)}

    def get_match(self, match_id: str) -> Mapping[str, Any]:
        key = str(match_id)
        if key not in self._matches and key not in self.bundle.replays:
            raise MatchNotFoundError("unknown match_id: {}".format(key))
        result = dict(self._matches.get(key, {"match_id": key}))
        if key in self.bundle.replays:
            result["replay"] = self.bundle.replays[key]
        return result

    def evaluation(
        self,
        *,
        model: Optional[str] = None,
        scope: Optional[str] = None,
        phase: Optional[str] = None,
    ) -> Mapping[str, Any]:
        root: Any = self.bundle.evaluation
        payload: Any = root.get(model, {}) if model and isinstance(root, Mapping) else root

        def filter_payload(value: Any) -> Mapping[str, Any]:
            if not isinstance(value, Mapping):
                return {}
            slices = value.get("by_slice", {})
            filtered: Dict[str, Any] = {}
            if scope:
                if scope in {"full", "reduced"}:
                    filtered["scope"] = (
                        slices.get("match_format", {}).get(scope, {})
                        if isinstance(slices, Mapping)
                        else {}
                    )
                elif scope == "japan":
                    roles = slices.get("japan_role", {}) if isinstance(slices, Mapping) else {}
                    filtered["scope"] = {
                        key: value
                        for key, value in roles.items()
                        if str(key).startswith("japan_")
                    }
                else:
                    filtered["scope"] = (
                        slices.get("japan_role", {}).get(scope, {})
                        if isinstance(slices, Mapping)
                        else {}
                    )
            if phase:
                filtered["phase"] = (
                    slices.get("phase_absolute", {}).get(phase, {})
                    if isinstance(slices, Mapping)
                    else {}
                )
            return filtered

        if not isinstance(payload, Mapping):
            return {"items": payload}
        result = dict(payload)
        if scope or phase:
            if model:
                filtered: Mapping[str, Any] = filter_payload(payload)
            elif isinstance(root, Mapping):
                filtered = {
                    key: filter_payload(value)
                    for key, value in root.items()
                    if key in {"first_innings", "chase"}
                    and isinstance(value, Mapping)
                }
            else:
                filtered = {}
            result["filters"] = {
                "model": model,
                "scope": scope,
                "phase": phase,
            }
            result["filtered"] = filtered
        elif model:
            result["filters"] = {"model": model, "scope": None, "phase": None}
        return result

    def _warnings(self, batting_team: str, bowling_team: str, venue: str) -> List[str]:
        warnings: List[str] = []
        known_teams = set(self.bundle.known_teams)
        known_venues = set(self.bundle.known_venues)
        if known_teams and batting_team not in known_teams:
            warnings.append("{} は学習時に未収録のためglobal priorへfallbackしました".format(batting_team))
        if known_teams and bowling_team not in known_teams:
            warnings.append("{} は学習時に未収録のためglobal priorへfallbackしました".format(bowling_team))
        if known_venues and venue not in known_venues:
            warnings.append("venue未収録のためglobal venue priorへfallbackしました")
        return warnings

    def _base_state(
        self,
        payload: Mapping[str, Any],
        *,
        innings: int,
        batting_team: str,
        bowling_team: str,
        runs: int,
        wickets: int,
        legal_balls: int,
        ball_limit: int,
        target: Optional[int] = None,
        balls_remaining_override: Optional[int] = None,
    ) -> Dict[str, Any]:
        balls_remaining = (
            max(0, int(balls_remaining_override))
            if balls_remaining_override is not None
            else max(0, ball_limit - legal_balls)
        )
        crr = runs * 6.0 / legal_balls if legal_balls else 0.0
        required = max(0, target - runs) if target is not None else None
        rrr = (
            required * 6.0 / balls_remaining
            if required and balls_remaining
            else (0.0 if required == 0 else math.inf if required is not None else None)
        )
        global_context = dict(self.bundle.global_context or {})
        batting_context = dict(
            self.bundle.latest_team_context.get(batting_team, global_context)
        )
        bowling_context = dict(
            self.bundle.latest_team_context.get(bowling_team, global_context)
        )
        venue_name = str(payload.get("venue") or "Unknown")
        venue_context = dict(
            self.bundle.latest_venue_context.get(venue_name, global_context)
        )
        batting_elo = float(batting_context.get("elo", global_context.get("elo", 1500.0)))
        bowling_elo = float(bowling_context.get("elo", global_context.get("elo", 1500.0)))
        batting_form = float(
            batting_context.get("batting_form", global_context.get("batting_form", 0.0))
        )
        opponent_form = float(
            bowling_context.get("batting_form", global_context.get("batting_form", 0.0))
        )
        batting_suppression = float(
            batting_context.get(
                "bowling_suppression", global_context.get("bowling_suppression", 0.0)
            )
        )
        opponent_suppression = float(
            bowling_context.get(
                "bowling_suppression", global_context.get("bowling_suppression", 0.0)
            )
        )
        return {
            "match_id": "manual",
            "match_date": str(_value(payload, "prediction_date", "match_date", default=self.bundle.manifest.source_cutoff or "")),
            "innings": innings,
            "batting_team": batting_team,
            "bowling_team": bowling_team,
            "venue": venue_name,
            "runs_so_far": runs,
            "wickets_lost": wickets,
            "wickets_remaining": max(0, 10 - wickets),
            "legal_balls_bowled": legal_balls,
            "balls_remaining": balls_remaining,
            "innings_ball_limit": ball_limit,
            "current_run_rate": crr,
            "progress": min(1.0, legal_balls / float(ball_limit)),
            "phase_absolute": phase_absolute(legal_balls),
            "phase_relative": phase_relative(legal_balls, ball_limit),
            "is_reduced_match": ball_limit < 120,
            "target": target,
            "runs_required": required,
            "required_run_rate": rrr,
            "rrr_minus_crr": (rrr - crr if rrr is not None else None),
            "batting_team_won_toss": (
                str(payload.get("toss_winner")) == batting_team
                if payload.get("toss_winner")
                else None
            ),
            "elo_diff": float(payload.get("elo_diff", batting_elo - bowling_elo)),
            "batting_form_delta": float(
                payload.get("batting_form_delta", batting_form - opponent_form)
            ),
            "bowling_suppression_delta": float(
                payload.get(
                    "bowling_suppression_delta",
                    batting_suppression - opponent_suppression,
                )
            ),
            "venue_prior": float(
                payload.get(
                    "venue_prior",
                    venue_context.get(
                        "venue_prior", global_context.get("venue_prior", 0.0)
                    ),
                )
            ),
            "venue_sample_count": float(
                payload.get(
                    "venue_sample_count", venue_context.get("venue_sample_count", 0.0)
                )
            ),
            "team_cold_start": float(
                batting_team not in self.bundle.latest_team_context
                or batting_context.get("cold_start", False)
            ),
            "opponent_cold_start": float(
                bowling_team not in self.bundle.latest_team_context
                or bowling_context.get("cold_start", False)
            ),
            "era_trend": float(
                payload.get(
                    "era_trend",
                    global_context.get(
                        "era_trend",
                        float(str(_value(payload, "prediction_date", default="2026"))[:4] or 2026),
                    ),
                )
            ),
        }

    def predict_first_innings(self, payload: Mapping[str, Any]) -> Mapping[str, Any]:
        request = _mapping(payload)
        batting = str(_value(request, "batting_team", "team", default=""))
        bowling = str(_value(request, "bowling_team", "opponent", default=""))
        runs = int(_value(request, "runs", "runs_so_far", default=0))
        wickets = int(_value(request, "wickets", "wickets_lost", default=0))
        legal_balls = _completed_balls(request)
        ball_limit = _quota_balls(_value(request, "quota", "innings_quota", "ball_limit"), default=120)
        if ball_limit < 120 and not self.bundle.manifest.reduced_match_enabled:
            raise UnsupportedReducedMatchError("unsupported_reduced_match")
        state = self._base_state(
            request,
            innings=1,
            batting_team=batting,
            bowling_team=bowling,
            runs=runs,
            wickets=wickets,
            legal_balls=legal_balls,
            ball_limit=ball_limit,
        )
        global_value = predict_final_score(self.bundle.first_innings_global, state)
        known_teams = set(self.bundle.known_teams)
        unknown_team = bool(known_teams) and (
            batting not in known_teams or bowling not in known_teams
        )
        team_value = (
            global_value
            if unknown_team
            else predict_final_score(self.bundle.first_innings_team, state)
        )
        requested = bool(_value(request, "use_japan_correction", "japan_correction", default=False))
        role = first_innings_role(state)
        correction = correction_for_role(self.bundle.japan_corrections, role)
        applicable = correction is not None
        if correction is not None:
            japan_value = max(runs, correction.apply(team_value))
            status = correction.status(requested, applicable)
        else:
            japan_value = team_value
            status = CorrectionStatus(
                requested=requested,
                applicable=False,
                applied=False,
                fallback_reason="not_a_japan_role" if role is None else "correction_unavailable",
            )
        selected = japan_value if status.applied else team_value
        if self.bundle.interval_model is not None:
            intervals = self.bundle.interval_model.predict_one(state, selected)
        else:
            intervals = {
                "p50": {"lower": selected, "upper": selected},
                "p80": {"lower": selected, "upper": selected},
            }
        return {
            "comparison": PredictionComparison(global_value, team_value, japan_value, selected).as_dict(),
            "intervals": intervals,
            "correction": status.as_dict(),
            "warnings": self._warnings(batting, bowling, state["venue"]),
        }

    def predict_chase(self, payload: Mapping[str, Any]) -> Mapping[str, Any]:
        request = _mapping(payload)
        batting = str(_value(request, "chasing_team", "batting_team", default=""))
        bowling = str(_value(request, "defending_team", "bowling_team", default=""))
        target = int(_value(request, "target", "target_runs", default=0))
        runs = int(_value(request, "current_score", "runs", "runs_so_far", default=0))
        wickets = int(_value(request, "wickets", "wickets_lost", default=0))
        ball_limit = _quota_balls(
            _value(request, "target_ball_limit", "quota", "ball_limit"), default=120
        )
        balls_remaining_raw = request.get("balls_remaining")
        if balls_remaining_raw is not None:
            balls_remaining = _quota_balls(balls_remaining_raw, default=ball_limit)
            legal_balls = max(0, ball_limit - balls_remaining)
        else:
            legal_balls = _completed_balls(request)
            balls_remaining = max(0, ball_limit - legal_balls)
        if ball_limit < 120 and not self.bundle.manifest.reduced_match_enabled:
            raise UnsupportedReducedMatchError("unsupported_reduced_match")
        state = self._base_state(
            request,
            innings=2,
            batting_team=batting,
            bowling_team=bowling,
            runs=runs,
            wickets=wickets,
            legal_balls=legal_balls,
            ball_limit=ball_limit,
            target=target,
            balls_remaining_override=balls_remaining,
        )
        terminal_status, terminal_probability = chase_terminal(
            score=runs, target=target, wickets_lost=wickets, balls_remaining=balls_remaining
        )
        requested = bool(
            _value(request, "use_japan_correction", "japan_correction", default=False)
        )
        role = chase_role(state)
        correction = correction_for_role(self.bundle.japan_corrections, role)
        applicable = correction is not None
        if terminal_status is not None:
            terminal_correction = CorrectionStatus(
                requested=requested,
                applicable=applicable,
                applied=False,
                fallback_reason="terminal_rule",
                match_count=(correction.match_count if correction is not None else 0),
            )
            return {
                "comparison": {
                    "global": terminal_probability,
                    "team_adjusted": terminal_probability,
                    "japan_adjusted": terminal_probability,
                    "selected": terminal_probability,
                },
                "scenarios": [],
                "terminal": {
                    "is_terminal": True,
                    "status": terminal_status,
                    "probability": terminal_probability,
                },
                "correction": terminal_correction.as_dict(),
                "warnings": self._warnings(batting, bowling, state["venue"]),
            }
        global_value = _predict_probability(self.bundle.chase_global, state)
        # A missing toss is not evidence that the chasing team lost the toss.
        unknown_toss = request.get("toss_winner") not in {batting, bowling}
        if unknown_toss:
            state["batting_team_won_toss"] = None
        warnings = self._warnings(batting, bowling, state["venue"])
        if unknown_toss:
            warnings.append("トス結果が不明のため、チーム補正モデルではなくglobalモデルを使用しました")
        known_teams = set(self.bundle.known_teams)
        unknown_team = bool(known_teams) and (
            batting not in known_teams or bowling not in known_teams
        )
        team_value = (
            global_value
            if unknown_team or unknown_toss
            else _predict_probability(self.bundle.chase_team, state)
        )
        if team_value is None:
            japan_value = None
        elif correction is not None and not unknown_toss:
            japan_value = correction.apply(team_value)
        else:
            japan_value = team_value
        if correction is not None:
            correction_status = correction.status(requested, applicable)
        else:
            correction_status = CorrectionStatus(
                requested=requested,
                applicable=False,
                applied=False,
                fallback_reason="not_a_japan_role" if role is None else "correction_unavailable",
            )
        if unknown_toss and correction_status.applied:
            # Japan corrections were fitted on team-model residuals.
            correction_status = CorrectionStatus(
                requested=requested, applicable=applicable, applied=False,
                fallback_reason="unknown_toss", match_count=correction.match_count,
            )
        selected = japan_value if correction_status.applied else team_value
        comparison = {
            "global": global_value,
            "team_adjusted": team_value,
            "japan_adjusted": japan_value,
            "selected": selected,
        }
        scenarios: List[Mapping[str, Any]] = []
        if terminal_status is None:
            scenario_model = (
                self.bundle.chase_global if unknown_team or unknown_toss else self.bundle.chase_team
            )
            scenarios = next_ball_scenarios(scenario_model, state)
            if correction_status.applied and correction is not None:
                scenarios = [
                    dict(item, win_probability=correction.apply(item["win_probability"]))
                    if item.get("win_probability") is not None
                    else item
                    for item in scenarios
                ]
        return {
            "comparison": comparison,
            "scenarios": scenarios,
            "terminal": {
                "is_terminal": terminal_status is not None,
                "status": terminal_status,
                "probability": terminal_probability,
            },
            "correction": correction_status.as_dict(),
            "warnings": warnings,
        }
