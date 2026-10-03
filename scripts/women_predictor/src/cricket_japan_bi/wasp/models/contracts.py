"""Serializable model contracts shared by training, API and Web code."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Mapping, Optional, Protocol, Sequence, Tuple


ARTIFACT_SCHEMA_VERSION = "1.0"


class ArtifactSchemaError(ValueError):
    """A serving artifact is internally incomplete or schema-incompatible."""


class Regressor(Protocol):
    def predict(self, records: Any) -> Any:
        ...


class Classifier(Protocol):
    def predict_proba(self, records: Any) -> Any:
        ...


@dataclass(frozen=True)
class PredictionComparison:
    global_value: float
    team_adjusted: float
    japan_adjusted: float
    selected: float

    def as_dict(self) -> Dict[str, float]:
        return {
            "global": float(self.global_value),
            "team_adjusted": float(self.team_adjusted),
            "japan_adjusted": float(self.japan_adjusted),
            "selected": float(self.selected),
        }


@dataclass(frozen=True)
class CorrectionStatus:
    requested: bool
    applicable: bool
    applied: bool
    fallback_reason: Optional[str] = None
    match_count: int = 0
    ci80: Optional[Tuple[float, float]] = None
    ci95: Optional[Tuple[float, float]] = None

    def as_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ArtifactManifest:
    source_sha256: str
    config_sha256: str = ""
    schema_version: str = ARTIFACT_SCHEMA_VERSION
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    source_cutoff: Optional[str] = None
    bundle_role: str = "production_refit"
    evaluation_role: str = "frozen_oof_locked_test"
    split: Mapping[str, str] = field(default_factory=dict)
    feature_schema: Mapping[str, Sequence[str]] = field(default_factory=dict)
    selected_models: Mapping[str, str] = field(default_factory=dict)
    library_versions: Mapping[str, str] = field(default_factory=dict)
    run_parameters: Mapping[str, Any] = field(default_factory=dict)
    reduced_match_enabled: bool = False
    japan_gates: Mapping[str, Any] = field(default_factory=dict)
    metrics: Mapping[str, Any] = field(default_factory=dict)
    limitations: Sequence[str] = field(default_factory=tuple)
    bundle_sha256: str = ""

    def validate(self) -> None:
        if self.schema_version != ARTIFACT_SCHEMA_VERSION:
            raise ValueError(
                "artifact schema mismatch: expected {}, got {}".format(
                    ARTIFACT_SCHEMA_VERSION, self.schema_version
                )
            )
        if self.source_sha256 and len(self.source_sha256) != 64:
            raise ValueError("source_sha256 must be a 64-character SHA-256 digest")

    def validate_serving(self) -> None:
        self.validate()
        if len(self.source_sha256) != 64:
            raise ArtifactSchemaError("serving artifact source_sha256 is required")
        if len(self.config_sha256) != 64:
            raise ArtifactSchemaError("serving artifact config_sha256 is required")
        if len(self.bundle_sha256) != 64:
            raise ArtifactSchemaError("serving artifact bundle_sha256 is required")
        if self.bundle_role not in {"production_refit", "frozen_test"}:
            raise ArtifactSchemaError("unknown artifact bundle_role")
        required_models = {
            "first_innings_global",
            "first_innings_team",
            "chase_global",
            "chase_team",
        }
        missing_models = sorted(
            key for key in required_models if not self.selected_models.get(key)
        )
        if missing_models:
            raise ArtifactSchemaError(
                "serving artifact selected_models missing: {}".format(
                    ", ".join(missing_models)
                )
            )
        required_features = {
            "first_innings_model_0",
            "first_innings_model_1",
            "chase_model_0",
            "chase_model_1",
        }
        missing_features = sorted(
            key for key in required_features if not self.feature_schema.get(key)
        )
        if missing_features:
            raise ArtifactSchemaError(
                "serving artifact feature_schema missing: {}".format(
                    ", ".join(missing_features)
                )
            )

    def as_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "ArtifactManifest":
        allowed = {field.name for field in cls.__dataclass_fields__.values()}
        manifest = cls(**{key: item for key, item in value.items() if key in allowed})
        manifest.validate()
        return manifest


@dataclass
class ArtifactBundle:
    """Single atomic inference bundle written after offline training."""

    manifest: ArtifactManifest
    first_innings_global: Any
    first_innings_team: Any
    chase_global: Any
    chase_team: Any
    interval_model: Any = None
    japan_corrections: Mapping[str, Any] = field(default_factory=dict)
    known_teams: Sequence[str] = field(default_factory=tuple)
    known_venues: Sequence[str] = field(default_factory=tuple)
    latest_team_context: Mapping[str, Mapping[str, Any]] = field(default_factory=dict)
    latest_venue_context: Mapping[str, Mapping[str, Any]] = field(default_factory=dict)
    global_context: Mapping[str, Any] = field(default_factory=dict)
    matches: Sequence[Mapping[str, Any]] = field(default_factory=tuple)
    replays: Mapping[str, Any] = field(default_factory=dict)
    evaluation: Mapping[str, Any] = field(default_factory=dict)

    def validate_serving(self) -> None:
        """Validate the executable payload before the API reports readiness.

        The external manifest protects the serialized bytes, but it cannot by
        itself prove that those bytes contain usable estimators.  Validate the
        small serving surface here so corrupt or schema-incompatible bundles
        fail closed during application startup rather than on the first request.
        """

        self.manifest.validate_serving()
        model_contracts = {
            "first_innings_global": ("first_innings_model_0",),
            # Model 1 can legitimately fall back to the selected Model 0
            # structure when its validation gate fails.
            "first_innings_team": (
                "first_innings_model_0",
                "first_innings_model_1",
            ),
            "chase_global": ("chase_model_0",),
            "chase_team": ("chase_model_0", "chase_model_1"),
        }
        for attribute, schema_keys in model_contracts.items():
            model = getattr(self, attribute, None)
            if not callable(getattr(model, "predict", None)):
                raise ArtifactSchemaError(
                    "serving artifact {} must expose predict()".format(attribute)
                )
            model_features = getattr(model, "features", None)
            # Empirical/resource baselines intentionally have no explicit
            # feature vector.  Estimators that publish one must match a
            # manifest schema for their task and serving role exactly.
            if model_features is None:
                continue
            try:
                actual = tuple(str(value) for value in model_features)
            except TypeError as exc:
                raise ArtifactSchemaError(
                    "serving artifact {} features are not iterable".format(attribute)
                ) from exc
            expected = {
                tuple(str(value) for value in self.manifest.feature_schema[key])
                for key in schema_keys
            }
            if actual not in expected:
                raise ArtifactSchemaError(
                    "serving artifact {} feature schema mismatch".format(attribute)
                )

        interval = self.interval_model
        missing_interval_methods = [
            name
            for name in ("predict", "predict_one")
            if not callable(getattr(interval, name, None))
        ]
        if missing_interval_methods:
            raise ArtifactSchemaError(
                "serving artifact interval_model missing: {}".format(
                    ", ".join(missing_interval_methods)
                )
            )

    def save(self, directory: Path) -> Path:
        target = Path(directory)
        target.mkdir(parents=True, exist_ok=True)
        try:
            import joblib
        except ImportError as exc:  # pragma: no cover - required production dependency
            raise RuntimeError("joblib is required to save WASP-style artifacts") from exc
        bundle_path = target / "bundle.joblib"
        # Keep the digest outside the serialized payload.  This avoids a
        # self-referential hash while still making every payload byte covered
        # by manifest.json.
        self.manifest.bundle_sha256 = ""
        joblib.dump(self, bundle_path, compress=3)
        payload = bundle_path.read_bytes()
        digest = hashlib.sha256(payload).hexdigest()
        self.manifest.bundle_sha256 = digest
        manifest_path = target / "manifest.json"
        manifest_path.write_text(
            json.dumps(self.manifest.as_dict(), ensure_ascii=False, indent=2, sort_keys=True)
            + "\n",
            encoding="utf-8",
        )
        return bundle_path

    @classmethod
    def load(cls, directory: Path) -> "ArtifactBundle":
        target = Path(directory)
        manifest_path = target / "manifest.json"
        bundle_path = target / "bundle.joblib"
        if not manifest_path.is_file() or not bundle_path.is_file():
            raise FileNotFoundError("artifact manifest.json or bundle.joblib is missing")
        manifest = ArtifactManifest.from_dict(
            json.loads(manifest_path.read_text(encoding="utf-8"))
        )
        payload = bundle_path.read_bytes()
        actual_digest = hashlib.sha256(payload).hexdigest()
        if not manifest.bundle_sha256:
            raise ValueError("bundle SHA-256 is missing from artifact manifest")
        if manifest.bundle_sha256 != actual_digest:
            raise ValueError(
                "artifact bundle SHA-256 mismatch: expected {}, got {}".format(
                    manifest.bundle_sha256, actual_digest
                )
            )
        try:
            import joblib
        except ImportError as exc:  # pragma: no cover - required production dependency
            raise RuntimeError("joblib is required to load WASP-style artifacts") from exc
        bundle = joblib.load(bundle_path)
        if not isinstance(bundle, cls):
            raise TypeError("bundle.joblib does not contain an ArtifactBundle")
        bundle.manifest = manifest
        bundle.validate_serving()
        return bundle


def save_artifact(bundle: ArtifactBundle, directory: Any) -> Path:
    return bundle.save(Path(directory))


def load_artifact(directory: Any) -> ArtifactBundle:
    return ArtifactBundle.load(Path(directory))
