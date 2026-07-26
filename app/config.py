"""Application settings loaded from environment / .env."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_version: str = "0.1.0"
    log_level: str = "INFO"
    port: int = 10000

    # Gemini (used from Phase 3 / batch alignment)
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-2.0-flash"
    gemini_timeout_seconds: float = 30.0
    gemini_max_retries: int = 2
    gemini_min_confidence: float = 0.0
    alignment_strategy: str = "span_merge"

    # API limits (Phase 2)
    max_batch_size: int = 100


@lru_cache
def get_settings() -> Settings:
    return Settings()
