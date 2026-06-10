"""Application settings loaded via pydantic-settings.

In local dev, values come from a `.env` file at the repo root. In production
(single EC2), values come from `/etc/fme-train/env` which systemd reads via
`EnvironmentFile=` and exposes as plain env vars — there is no secrets-store
lookup in the hot path.

Reference: docs/plans/2026-04-29-multi-user-web-app.md sections 1–5 (app
design) and docs/plans/2026-05-05-multi-user-web-app-ec2-alternative.md
(deployment).
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
    database_url: Optional[str] = Field(
        default=None,
        description="postgresql+asyncpg://user:pass@host/db. Optional at startup; "
                    "required before the scheduler dispatches anything.",
    )

    # ---- Run scheduler / worker -----------------------------------------
    # Team-wide concurrency cap on simultaneously running pipeline runs.
    # See plan section 3 — the scheduler enforces this before dispatch.
    run_concurrency: int = Field(default=2, ge=1)
    # How often the scheduler polls runs.status='queued' (seconds).
    scheduler_poll_interval_s: float = Field(default=2.0, gt=0)
    # Selects how the scheduler dispatches workers:
    #   'stub'       — in-process callable (tests, ad-hoc dev)
    #   'in-process' — runs the worker as an asyncio task in the same
    #                  Python process. Local dev default when DATABASE_URL
    #                  is set but no real systemd is available.
    #   'systemd'    — production: spawns a templated systemd user unit
    #                  per run via `systemctl --user start`. See
    #                  docs/plans/2026-05-05-multi-user-web-app-ec2-alternative.md.
    task_dispatcher: str = Field(default="stub")

    # ---- Draft storage ---------------------------------------------------
    # Where lesson-draft HTML bodies are persisted on disk. The original
    # plan stored these in S3; the EC2 deployment keeps them on the box
    # under /var/lib/fme-train/drafts so backups are part of the EBS
    # snapshot. Tests override this to a temp dir.
    drafts_root: str = Field(default="/var/lib/fme-train/drafts")

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

    # ---- Artifact storage ------------------------------------------------
    # Root directory for per-run pipeline artifacts (manifests, changelogs,
    # reports, edit plans). Plan B (single EC2): local disk only; no S3.
    # Tests override this to a temp dir via the ARTIFACTS_ROOT env var.
    artifacts_root: str = Field(
        default="/var/lib/fme-train/artifacts",
        description="Root dir for per-run artifacts (<artifacts_root>/<run_id>/). "
                    "Set ARTIFACTS_ROOT=./artifacts in .env.compose for local dev.",
    )

    # Root of the lesson content tree (versioned HTML files). The worker
    # resolves lesson paths relative to this. Defaults to the repo root.
    lesson_content_root: str = Field(
        default=".",
        description="Absolute or relative path to the repo root containing "
                    "versioned lesson folders (e.g. 2025.0/, 2026.1/). "
                    "Set LESSON_CONTENT_ROOT=/app in the container.",
    )

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
