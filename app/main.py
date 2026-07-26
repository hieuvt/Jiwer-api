"""FastAPI application entrypoint (Phase 0 skeleton)."""

import logging

from fastapi import FastAPI, Request
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
    description="REST API for Word Error Rate (WER) measurement using jiwer + Gemini batch alignment.",
    version=settings.app_version or __version__,
)

app.include_router(wer_router)


@app.exception_handler(AppError)
async def app_error_handler(_request: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message},
    )


@app.get("/health", response_model=HealthResponse, tags=["health"])
async def health() -> HealthResponse:
    return HealthResponse(status="ok", version=settings.app_version or __version__)
