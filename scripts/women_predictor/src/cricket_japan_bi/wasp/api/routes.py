"""JSON endpoints and five read-only HTML application screens."""

from __future__ import annotations

import inspect
from datetime import date
from typing import Annotated, Any, Callable

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from .dependencies import (
    PredictionServiceProtocol,
    get_prediction_service,
    translate_service_error,
)
from .schemas import (
    ApiDataResponse,
    ChasePrediction,
    ChaseRequest,
    FirstInningsPrediction,
    FirstInningsRequest,
    HealthResponse,
    MetadataPayload,
    ModelInfoPayload,
)

api_router = APIRouter(prefix="/api", tags=["WASP-style API"])
web_router = APIRouter(include_in_schema=False)
Service = Annotated[PredictionServiceProtocol, Depends(get_prediction_service)]


async def _invoke(callable_: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
    try:
        result = callable_(*args, **kwargs)
        if inspect.isawaitable(result):
            result = await result
        if hasattr(result, "model_dump"):
            return result.model_dump(mode="json", by_alias=True)
        return result
    except HTTPException:
        raise
    except Exception as exc:
        raise translate_service_error(exc) from exc


@api_router.get("/health", response_model=HealthResponse)
async def health(request: Request) -> HealthResponse:
    ready = getattr(request.app.state, "prediction_service", None) is not None
    return HealthResponse(
        status="ok" if ready else "degraded",
        ready=ready,
        detail=None if ready else getattr(request.app.state, "service_error", None),
    )


@api_router.get("/metadata", response_model=ApiDataResponse[MetadataPayload])
async def metadata(service: Service) -> dict[str, Any]:
    return {"data": await _invoke(service.metadata)}


@api_router.get("/model-info", response_model=ApiDataResponse[ModelInfoPayload])
async def model_info(service: Service) -> dict[str, Any]:
    return {"data": await _invoke(service.model_info)}


@api_router.get("/matches", response_model=ApiDataResponse[dict[str, Any]])
async def list_matches(
    service: Service,
    japan_only: bool = False,
    from_date: date | None = Query(default=None, alias="from_date"),
    to_date: date | None = None,
    cursor: str | None = Query(default=None, max_length=18, pattern=r"^[0-9]+$"),
    limit: int = Query(default=25, ge=1, le=100),
) -> dict[str, Any]:
    if from_date and to_date and from_date > to_date:
        raise HTTPException(
            status_code=422,
            detail={
                "code": "invalid_date_range",
                "message": "from_dateはto_date以前にしてください。",
            },
        )
    data = await _invoke(
        service.list_matches,
        japan_only=japan_only,
        from_date=from_date,
        to_date=to_date,
        cursor=cursor,
        limit=limit,
    )
    return {"data": data}


@api_router.get("/matches/{match_id}", response_model=ApiDataResponse[dict[str, Any]])
async def get_match(match_id: str, service: Service) -> dict[str, Any]:
    try:
        return {"data": await _invoke(service.get_match, match_id)}
    except HTTPException as exc:
        # Keep compatibility with simple repository implementations while the
        # concrete service exposes MatchNotFoundError explicitly.
        if exc.status_code == 503 and isinstance(exc.__cause__, KeyError):
            raise HTTPException(
                status_code=404,
                detail={
                    "code": "match_not_found",
                    "message": "指定した試合が見つかりません。",
                    "details": match_id,
                },
            ) from exc
        raise


@api_router.post(
    "/predict/first-innings",
    response_model=ApiDataResponse[FirstInningsPrediction],
)
async def predict_first_innings(
    request_data: FirstInningsRequest,
    service: Service,
) -> dict[str, Any]:
    payload = request_data.model_dump(mode="json")
    payload["completed_balls"] = request_data.completed.total_balls
    payload["innings_ball_limit"] = request_data.quota.total_balls
    return {"data": await _invoke(service.predict_first_innings, payload)}


@api_router.post("/predict/chase", response_model=ApiDataResponse[ChasePrediction])
async def predict_chase(
    request_data: ChaseRequest,
    service: Service,
) -> dict[str, Any]:
    payload = request_data.model_dump(mode="json")
    payload["innings_ball_limit"] = request_data.target_ball_limit.total_balls
    return {"data": await _invoke(service.predict_chase, payload)}


@api_router.get("/evaluation", response_model=ApiDataResponse[dict[str, Any]])
async def evaluation(
    service: Service,
    model: str | None = Query(default=None, max_length=80),
    scope: str | None = Query(default=None, max_length=80),
    phase: str | None = Query(default=None, max_length=80),
) -> dict[str, Any]:
    data = await _invoke(service.evaluation, model=model, scope=scope, phase=phase)
    return {"data": data}


def _templates(request: Request) -> Jinja2Templates:
    return request.app.state.templates


def _render(request: Request, template_name: str, active_page: str) -> HTMLResponse:
    return _templates(request).TemplateResponse(
        request=request,
        name=template_name,
        context={
            "active_page": active_page,
            "product_name": "日本男子代表 T20 WASP-style",
        },
    )


@web_router.get("/", response_class=HTMLResponse)
async def dashboard_page(request: Request) -> HTMLResponse:
    return _render(request, "dashboard.html", "dashboard")


@web_router.get("/first-innings", response_class=HTMLResponse)
async def first_innings_page(request: Request) -> HTMLResponse:
    return _render(request, "first_innings.html", "first-innings")


@web_router.get("/chase", response_class=HTMLResponse)
async def chase_page(request: Request) -> HTMLResponse:
    return _render(request, "chase.html", "chase")


@web_router.get("/replay", response_class=HTMLResponse)
async def replay_page(request: Request) -> HTMLResponse:
    return _render(request, "replay.html", "replay")


@web_router.get("/evaluation", response_class=HTMLResponse)
async def evaluation_page(request: Request) -> HTMLResponse:
    return _render(request, "evaluation.html", "evaluation")
