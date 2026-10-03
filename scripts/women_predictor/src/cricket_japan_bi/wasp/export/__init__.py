"""Offline, browser-safe export helpers for WASP-style artifacts.

The serving bundle deliberately remains a Python/joblib artifact.  This
package extracts only the deterministic inference surface into plain JSON and
ships a dependency-free JavaScript evaluator for a single-file HTML export.
"""

from .javascript import browser_runtime_source
from .reference import (
    build_state,
    predict_chase,
    predict_first,
    predict_interval,
)
from .serialization import (
    STANDALONE_MODEL_SCHEMA_VERSION,
    canonical_json,
    serialize_bundle_inference,
)

__all__ = [
    "STANDALONE_MODEL_SCHEMA_VERSION",
    "browser_runtime_source",
    "build_state",
    "canonical_json",
    "predict_chase",
    "predict_first",
    "predict_interval",
    "serialize_bundle_inference",
]
