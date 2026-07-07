"""Central runtime configuration, loaded from environment / .env.

Nothing outside this module should read os.environ directly or hardcode
a model name — the M1 outage (calls 404ing on a stale model string with
no one noticing) happened because the model id was buried inline in the
classification worker.
"""
from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="MEDIAPULSE_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    env: str = "development"
    log_level: str = "INFO"
    secret_key: str = "change-me"

    database_url: str = "sqlite:///./mediapulse.db"

    # Anthropic — read without the MEDIAPULSE_ prefix since it's a
    # conventional SDK env var name.
    anthropic_api_key: str = Field(default="", alias="ANTHROPIC_API_KEY")

    classify_model: str = "claude-sonnet-4-6"
    synthesis_model: str = "claude-opus-4-8"
    vision_model: str = "claude-sonnet-4-6"

    ai_max_retries: int = 5
    ai_retry_backoff_seconds: float = 2.0

    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = "briefs@mediapulse.bw"
    smtp_use_tls: bool = True


@lru_cache
def get_settings() -> Settings:
    return Settings()
