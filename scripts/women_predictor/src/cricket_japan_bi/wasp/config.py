"""Typed access to the fixed WASP-style configuration contract."""

from __future__ import annotations

import hashlib
import json
import tomllib
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any, Mapping, Optional


PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "config" / "wasp.toml"


class WaspConfigError(ValueError):
    """Raised before any output is changed when configuration is unsupported."""


@dataclass(frozen=True)
class WaspConfig:
    path: Path
    values: Mapping[str, Any]
    sha256: str
    project_root: Path

    def section(self, name: str) -> Mapping[str, Any]:
        value = self.values.get(name)
        if not isinstance(value, Mapping):
            raise WaspConfigError("missing config section: {}".format(name))
        return value

    def resolve_path(self, key: str) -> Path:
        raw = self.section("paths").get(key)
        if not raw:
            raise WaspConfigError("missing config path: paths.{}".format(key))
        path = Path(str(raw)).expanduser()
        return path.resolve() if path.is_absolute() else (self.project_root / path).resolve()

    @property
    def random_seed(self) -> int:
        return int(self.values.get("project", {}).get("random_seed", 20260731))

    @property
    def expected_source_sha256(self) -> str:
        return str(self.section("source").get("expected_sha256") or "")

    @property
    def buffer_rows(self) -> int:
        return int(self.section("source").get("stream_buffer_rows", 50_000))

    def canonical_values_sha256(self) -> str:
        """Hash parsed values for diagnostics independent of TOML whitespace."""

        def normalize(value: Any) -> Any:
            if isinstance(value, Mapping):
                return {str(key): normalize(item) for key, item in sorted(value.items())}
            if isinstance(value, (list, tuple)):
                return [normalize(item) for item in value]
            if isinstance(value, date):
                return value.isoformat()
            return value

        payload = json.dumps(
            normalize(self.values), ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")
        return hashlib.sha256(payload).hexdigest()


def _expect(values: Mapping[str, Any], dotted: str, expected: Any) -> None:
    current: Any = values
    for part in dotted.split("."):
        if not isinstance(current, Mapping) or part not in current:
            raise WaspConfigError("missing config value: {}".format(dotted))
        current = current[part]
    if isinstance(expected, tuple):
        current = tuple(current)
    if current != expected:
        raise WaspConfigError(
            "unsupported config value {}={!r}; implementation requires {!r}".format(
                dotted, current, expected
            )
        )


def validate_implementation_contract(values: Mapping[str, Any]) -> None:
    """Fail loudly if the checked-in fixed policy and executable code diverge.

    The first version deliberately fixes the split and cricket rules.  Keeping
    these assertions in one place prevents a TOML edit from silently changing
    only the provenance hash while leaving model behavior unchanged.
    """

    fixed = {
        "source.gender": "female",
        "source.team_type": "international",
        "source.match_type": "T20",
        "splits.train_end": date(2022, 12, 31),
        "splits.validation_start": date(2023, 1, 1),
        "splits.validation_end": date(2024, 12, 31),
        "splits.test_start": date(2025, 1, 1),
        "splits.correction_fit_end": date(2024, 12, 31),
        "splits.correction_gate_start": date(2025, 1, 1),
        "splits.correction_gate_end": date(2025, 12, 31),
        "splits.correction_audit_start": date(2026, 1, 1),
        "eligibility.full_match_balls": 120,
        "phases.absolute.powerplay_end_ball": 35,
        "phases.absolute.middle_end_ball": 95,
        "phases.relative.powerplay_end_fraction": 0.30,
        "phases.relative.middle_end_fraction": 0.80,
        "features.elo_initial": 1500.0,
        "features.elo_k_candidates": (16, 24, 32),
        "features.form_half_life_days": 365,
        "features.form_prior_innings": 8,
        "features.venue_prior_innings": 20,
        "models.resource_pseudo_counts": (12, 24, 48, 96),
        "models.chase_pseudo_counts": (12, 24, 48, 96),
        "models.tweedie_powers": (1.1, 1.5),
        "models.quantiles": (0.10, 0.25, 0.75, 0.90),
        "reduced_match_gate.minimum_development_matches": 50,
        "japan_correction.bootstrap_iterations": 500,
        "japan_correction.minimum_history_matches": 12,
        "japan_correction.minimum_gate_matches": 8,
        "japan_correction.minimum_chase_wins": 3,
        "japan_correction.minimum_chase_losses": 3,
        "api.default_page_size": 25,
        "api.maximum_page_size": 100,
    }
    for dotted, expected in fixed.items():
        _expect(values, dotted, expected)


def load_wasp_config(
    path: Optional[Path] = None, *, validate_contract: bool = True
) -> WaspConfig:
    resolved = Path(path or DEFAULT_CONFIG_PATH).expanduser().resolve()
    if not resolved.is_file():
        raise FileNotFoundError("WASP config not found: {}".format(resolved))
    payload = resolved.read_bytes()
    values = tomllib.loads(payload.decode("utf-8"))
    if validate_contract:
        validate_implementation_contract(values)
    # Checked-in paths are project-relative.  A custom config next to a
    # ``config`` directory follows the same convention.
    project_root = resolved.parent.parent if resolved.parent.name == "config" else PROJECT_ROOT
    return WaspConfig(
        path=resolved,
        values=values,
        sha256=hashlib.sha256(payload).hexdigest(),
        project_root=project_root,
    )


__all__ = [
    "DEFAULT_CONFIG_PATH",
    "PROJECT_ROOT",
    "WaspConfig",
    "WaspConfigError",
    "load_wasp_config",
    "validate_implementation_contract",
]
