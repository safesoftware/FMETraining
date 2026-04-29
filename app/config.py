"""Application settings loaded via pydantic-settings.

In local dev, values come from a `.env` file at the repo root. In production
(App Runner / Fargate), AWS Secrets Manager values are injected as plain env
vars by the task definition — there is no boto3 lookup in the hot path.

Reference: docs/plans/2026-04-29-multi-user-web-app.md sections 1, 6.
"""
from __future__ import annotations

from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Environment-driven app settings.

    Anything that is *required at startup* should be a non-default field so
    pydantic raises a clear error if it's missing. Anything that is only
    needed when a particular feature runs (e.g. Skilljar push, OpenAI calls)
    is `Optional` here — feature code is responsible for asserting presence.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",  # legacy .env vars from serve.py shouldn't break startup
    )

    # ---- App / runtime ---------------------------------------------------
    environment: str = Field(default="local", description="local | staging | production")
    app_version: str = Field(
        default="dev",
        description="Surfaced in /health. CI/CD overrides this with the git SHA.",
    )
    log_level: str = Field(default="INFO")

    # ---- Database --------------------------------------------------------
    # Phase 0 leaves the actual SQLAlchemy engine wiring to KNOW-2260; we just
    # read the URL here so the rest of the stack can pick it up later.
    database_url: Optional[str] = Field(
        default=None,
        description="postgresql+psycopg://user:pass@host/db. Optional in Phase 0.",
    )

    # ---- Sessions / auth -------------------------------------------------
    # Required once auth lands (KNOW-2259); optional in Phase 0 so the skeleton
    # boots without secrets present.
    session_signing_key: Optional[str] = None
    google_oauth_client_id: Optional[str] = None
    google_oauth_client_secret: Optional[str] = None

    # ---- OpenAI ----------------------------------------------------------
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-4o-mini"

    # ---- Jira ------------------------------------------------------------
    jira_base_url: Optional[str] = None
    jira_user: Optional[str] = None
    jira_api_key: Optional[str] = None
    jira_filter_id: Optional[str] = None

    # ---- Skilljar --------------------------------------------------------
    skilljar_api_key: Optional[str] = None
    skilljar_domain: Optional[str] = None

    # ---- AWS / S3 --------------------------------------------------------
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    aws_s3_bucket: Optional[str] = None
    aws_s3_region: str = "us-west-2"

    # ---- Cost ceiling ----------------------------------------------------
    # Per-run dollar cap for OpenAI spend; enforced by the worker (KNOW-2261).
    max_run_usd: float = 50.0


_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Return a cached Settings instance.

    Using a module-level cache (rather than `lru_cache` on a free function)
    keeps the FastAPI dependency injection simple and lets tests reset state
    via `reset_settings()` if they need to.
    """
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def reset_settings() -> None:
    """Clear the cached Settings instance. Intended for tests only."""
    global _settings
    _settings = None
