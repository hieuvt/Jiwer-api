"""Request/response schemas — Phase 0 stubs; full WER schemas in later phases."""

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = Field(examples=["ok"])
    version: str = Field(examples=["0.1.0"])
