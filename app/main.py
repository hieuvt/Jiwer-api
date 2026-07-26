"""FastAPI application entrypoint."""

import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app import __version__
from app.api.routes_wer import router as wer_router
from app.api.schemas import HealthResponse
from app.config import get_settings
from app.core.exceptions import AppError

settings = get_settings()

logging.basicConfig(level=settings.log_level.upper())
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Jiwer-api",
    description=(
        "REST API for Word Error Rate (WER) measurement using jiwer, "
        "with Gemini anchors + span_merge for batch alignment."
    ),
    version=settings.app_version or __version__,
)

app.include_router(wer_router)


@app.exception_handler(AppError)
async def app_error_handler(_request: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message},
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    _request: Request, exc: RequestValidationError
) -> JSONResponse:
    # Ensure ctx values (e.g. ValueError) are JSON-serializable.
    details = []
    for err in exc.errors():
        clean = dict(err)
        ctx = clean.get("ctx")
        if isinstance(ctx, dict):
            clean["ctx"] = {
                key: (str(value) if isinstance(value, BaseException) else value)
                for key, value in ctx.items()
            }
        details.append(clean)
    return JSONResponse(status_code=422, content={"detail": details})


@app.get("/health", response_model=HealthResponse, tags=["health"])
async def health() -> HealthResponse:
    return HealthResponse(status="ok", version=settings.app_version or __version__)
