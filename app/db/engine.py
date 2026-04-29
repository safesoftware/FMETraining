"""Async SQLAlchemy engine + session factory.

Reads ``DATABASE_URL`` directly from the process environment.

TODO: switch to ``app.config.Settings`` once KNOW-2258 lands. For now we
read ``os.environ["DATABASE_URL"]`` directly so this module has no
dependency on the (not-yet-implemented) settings module. Tests / Alembic
can override the URL by setting the env var before import or by calling
:func:`make_engine` explicitly.

The URL must use one of SQLAlchemy's async drivers, e.g.

    postgresql+asyncpg://user:pass@host:5432/dbname

For Alembic (which runs synchronously) the same URL is reused via
``create_async_engine`` + ``run_sync`` in ``alembic/env.py``.
"""

from __future__ import annotations

import os
from typing import Optional

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)


def _resolve_database_url(url: Optional[str] = None) -> str:
    """Resolve the database URL from the argument or the environment.

    Raises ``RuntimeError`` if no URL is configured. We avoid silent
    fall-back to SQLite so that a missing config in production fails
    loudly instead of writing to an ephemeral file.
    """

    if url is not None:
        return url
    env_url = os.environ.get("DATABASE_URL")
    if not env_url:
        raise RuntimeError(
            "DATABASE_URL is not set. Configure it in the environment "
            "(e.g. postgresql+asyncpg://user:pass@host:5432/db) before "
            "creating the engine."
        )
    return env_url


def make_engine(url: Optional[str] = None, *, echo: bool = False) -> AsyncEngine:
    """Build a fresh ``AsyncEngine``.

    Useful for tests that need an isolated engine + URL without
    mutating the process-wide singleton.
    """

    return create_async_engine(
        _resolve_database_url(url),
        echo=echo,
        pool_pre_ping=True,
        future=True,
    )


def make_session_factory(bound_engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    """Build an ``async_sessionmaker`` bound to *bound_engine*."""

    return async_sessionmaker(
        bind=bound_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
        autocommit=False,
    )


# Process-wide singletons. These are created lazily on first access so
# that simply importing the module does not fail when DATABASE_URL is
# absent (e.g. during ``alembic --help`` or during unit tests that want
# to swap in their own engine).

_engine: Optional[AsyncEngine] = None
_session_factory: Optional[async_sessionmaker[AsyncSession]] = None


def _get_or_create_engine() -> AsyncEngine:
    global _engine, _session_factory
    if _engine is None:
        _engine = make_engine()
        _session_factory = make_session_factory(_engine)
    return _engine


def _get_or_create_session_factory() -> async_sessionmaker[AsyncSession]:
    global _session_factory
    if _session_factory is None:
        _get_or_create_engine()
    assert _session_factory is not None
    return _session_factory


async def dispose_engine() -> None:
    """Dispose the singleton engine.

    Call this on application shutdown so async connections are released
    cleanly.
    """

    global _engine, _session_factory
    if _engine is not None:
        await _engine.dispose()
        _engine = None
        _session_factory = None


class _EngineProxy:
    """Lazy proxy so ``from app.db import engine`` works without forcing
    DB connection at import time.
    """

    def __getattr__(self, item: str):  # pragma: no cover - thin shim
        return getattr(_get_or_create_engine(), item)

    def __repr__(self) -> str:  # pragma: no cover - thin shim
        return f"<EngineProxy resolved={_engine!r}>"


class _SessionFactoryProxy:
    """Lazy proxy for the session factory."""

    def __call__(self, *args, **kwargs) -> AsyncSession:
        return _get_or_create_session_factory()(*args, **kwargs)

    def __getattr__(self, item: str):  # pragma: no cover - thin shim
        return getattr(_get_or_create_session_factory(), item)

    def __repr__(self) -> str:  # pragma: no cover - thin shim
        return f"<SessionFactoryProxy resolved={_session_factory!r}>"


engine: AsyncEngine = _EngineProxy()  # type: ignore[assignment]
session_factory: async_sessionmaker[AsyncSession] = _SessionFactoryProxy()  # type: ignore[assignment]
