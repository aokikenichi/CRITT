"""Application factory for the Japan men's T20 WASP-style web service."""

from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, AsyncIterator

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .dependencies import PredictionServiceProtocol, initialise_prediction_service
from .routes import api_router, web_router

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
WEB_ROOT = PACKAGE_ROOT / "web"


def _error_payload(detail: Any, default_code: str, default_message: str) -> dict[str, Any]:
    if isinstance(detail, dict):
        return {
            "error": {
                "code": str(detail.get("code", default_code)),
                "message": str(detail.get("message", default_message)),
                "details": detail.get("details"),
            }
        }
    return {
        "error": {
            "code": default_code,
            "message": str(detail) if detail else default_message,
            "details": None,
        }
    }


def create_app(
    *,
    service: PredictionServiceProtocol | None = None,
    artifact_dir: str | Path | None = None,
) -> FastAPI:
    artifact_path = Path(artifact_dir).resolve() if artifact_dir else None

    @asynccontextmanager
    async def lifespan(application: FastAPI) -> AsyncIterator[None]:
        initialise_prediction_service(application, service, artifact_path)
        yield

    application = FastAPI(
        title="Japan Men's T20 WASP-style API",
        summary="収録されたCricsheet試合に基づくWASP型の得点・追走確率推定",
        description=(
            "公式WASPの再現ではありません。学習済みアーティファクトのみを読み込み、"
            "HTTPリクエスト中には学習しません。"
        ),
        version="1.0.0",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )
    application.state.prediction_service = None
    application.state.service_error = "application startup has not completed"
    application.state.templates = Jinja2Templates(directory=str(WEB_ROOT / "templates"))

    @application.exception_handler(RequestValidationError)
    async def validation_error_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        del request
        # FastAPI's RequestValidationError intentionally exposes a smaller
        # ``errors`` signature than Pydantic's ValidationError.  Normalise the
        # optional context ourselves so every supported FastAPI/Pydantic v2
        # combination returns a JSON-safe 422 body.
        details = []
        for error in exc.errors():
            item = {key: value for key, value in error.items() if key != "ctx"}
            if error.get("ctx"):
                item["ctx"] = {
                    str(key): str(value) for key, value in error["ctx"].items()
                }
            details.append(item)
        return JSONResponse(
            status_code=422,
            content={
                "error": {
                    "code": "validation_error",
                    "message": "入力値を確認してください。",
                    "details": details,
                }
            },
        )

    @application.exception_handler(HTTPException)
    async def http_error_handler(request: Request, exc: HTTPException) -> JSONResponse:
        del request
        payload = _error_payload(exc.detail, "http_error", "リクエストを処理できません。")
        return JSONResponse(status_code=exc.status_code, content=payload, headers=exc.headers)

    application.mount(
        "/static",
        StaticFiles(directory=str(WEB_ROOT / "static")),
        name="wasp-static",
    )
    application.include_router(api_router)
    application.include_router(web_router)
    return application


app = create_app()
