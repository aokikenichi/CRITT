"""Dependency wiring kept independent from concrete model implementations."""

from __future__ import annotations

import inspect
import logging
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

from fastapi import HTTPException, Request, status

LOGGER = logging.getLogger(__name__)


@runtime_checkable
class PredictionServiceProtocol(Protocol):
    """Small boundary used by HTTP routes and their contract tests."""

    def metadata(self) -> Any: ...

    def model_info(self) -> Any: ...

    def list_matches(self, **filters: Any) -> Any: ...

    def get_match(self, match_id: str) -> Any: ...

    def evaluation(self, **filters: Any) -> Any: ...

    def predict_first_innings(self, payload: dict[str, Any]) -> Any: ...

    def predict_chase(self, payload: dict[str, Any]) -> Any: ...


def _safe_error_message(exc: BaseException) -> str:
    message = str(exc).strip()
    return message if message else exc.__class__.__name__


def initialise_prediction_service(
    app: Any,
    provided_service: PredictionServiceProtocol | None = None,
    artifact_dir: Path | None = None,
) -> None:
    """Load and validate the read-only artifact bundle once at application startup."""

    app.state.prediction_service = None
    app.state.service_error = None
    if provided_service is not None:
        app.state.prediction_service = provided_service
        return

    try:
        # The import is intentionally lazy: package metadata, documentation, and the
        # degraded health endpoint remain usable when ML dependencies/artifacts are absent.
        from cricket_japan_bi.wasp.models.service import PredictionService

        loader = PredictionService.load_default
        parameters = inspect.signature(loader).parameters
        if artifact_dir is not None and "artifact_dir" in parameters:
            service = loader(artifact_dir=artifact_dir)
        elif artifact_dir is not None and "artifacts_dir" in parameters:
            service = loader(artifacts_dir=artifact_dir)
        else:
            service = loader()
        app.state.prediction_service = service
    except Exception as exc:  # startup must expose a deterministic degraded state
        app.state.service_error = _safe_error_message(exc)
        LOGGER.warning("WASP-style artifacts are unavailable: %s", app.state.service_error)


def get_prediction_service(request: Request) -> PredictionServiceProtocol:
    service = getattr(request.app.state, "prediction_service", None)
    if service is None:
        detail = getattr(request.app.state, "service_error", None)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "code": "artifact_unavailable",
                "message": "予測アーティファクトを検証して読み込めませんでした。",
                "details": detail,
            },
        )
    return service


def translate_service_error(exc: Exception) -> HTTPException:
    """Map model-layer domain errors without importing that layer eagerly."""

    name = exc.__class__.__name__
    message = _safe_error_message(exc)
    if name in {"ArtifactUnavailableError", "ArtifactSchemaError"}:
        return HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "code": "artifact_unavailable",
                "message": "予測アーティファクトを利用できません。",
                "details": message,
            },
        )
    if name in {"UnsupportedReducedMatchError", "ReducedMatchNotEnabledError"}:
        return HTTPException(
            status_code=422,
            detail={
                "code": "unsupported_reduced_match",
                "message": "短縮試合の手動予測は検証gateを通過していません。",
                "details": message,
            },
        )
    if name == "MatchNotFoundError":
        return HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "match_not_found",
                "message": "指定した試合が見つかりません。",
                "details": message,
            },
        )
    if name == "InvalidMatchStateError":
        return HTTPException(
            status_code=422,
            detail={
                "code": "invalid_match_state",
                "message": "予測できない試合状態です。",
                "details": message,
            },
        )
    # Once Pydantic and explicit domain validation have accepted a request,
    # KeyError/ValueError/shape failures normally indicate an incompatible or
    # corrupt artifact.  Do not misreport those as user input errors.
    return HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail={
            "code": "artifact_runtime_error",
            "message": "予測アーティファクトで推論を完了できませんでした。",
            "details": message,
        },
    )
