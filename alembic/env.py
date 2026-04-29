"""Alembic environment for the multi-user web app.

Reads ``DATABASE_URL`` from the process environment (so the same
connection string is used by the app and by migrations), and binds
``target_metadata`` to ``app.models.base.Base.metadata`` so
``alembic revision --autogenerate`` sees every model.

TODO: switch to ``app.config.Settings`` once KNOW-2258 lands.
"""

from __future__ import annotations

import asyncio
import os
import sys
from logging.config import fileConfig
from pathlib import Path

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# Make sure the repo root is on sys.path so ``app.models`` imports
# regardless of the cwd from which alembic is invoked.
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.models import Base  # noqa: E402  -- import after sys.path tweak
import app.models  # noqa: F401, E402  -- registers all tables on Base.metadata

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Inject DATABASE_URL into the alembic config so the same env var
# drives both runtime and migrations. Falls back to the value already
# in alembic.ini (typically a local-dev placeholder) for offline use.
_db_url_from_env = os.environ.get("DATABASE_URL")
if _db_url_from_env:
    config.set_main_option("sqlalchemy.url", _db_url_from_env)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode (emits SQL without a DBAPI)."""

    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Create an async engine, run migrations on a sync connection."""

    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""

    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
