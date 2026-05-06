"""Seed the ``jobs`` table from ``data/update-job.json``.

The legacy launcher persists the most recent "what should the next run
process" config to ``data/update-job.json``::

    {
      "to_version": "2026.1",
      "scope": {
        "lessons": [],
        "courses": [{"learning_path": "...", "course": "..."}, ...],
        "learning_paths": []
      }
    }

In the multi-user app this becomes a row per user under ``jobs.owner``.
At migration time we don't yet have any users (Google OIDC ships in a
later ticket), so we insert a single row with ``owner=NULL`` that the
first user to sign in will inherit.

Idempotent: if a Job row already exists with the same ``(owner=NULL,
to_version, scope_json)`` triple, the second invocation is a no-op.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import logging
import sys
from pathlib import Path
from typing import Any, Iterable, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.db.engine import _get_or_create_session_factory
from app.models.jobs import Job

_logger = logging.getLogger(__name__)


def _read_job_json(source: Path) -> dict[str, Any]:
    payload = json.loads(source.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{source} did not contain a JSON object")
    return payload


async def _find_existing(
    session: AsyncSession, *, to_version: Optional[str], scope: Any
) -> Optional[Job]:
    """Look up the matching ``owner=NULL`` row by ``(to_version, scope_json)``.

    The Job table has no UNIQUE constraint, so we filter in Python after
    selecting the owner-less rows. The volume here is tiny (one row per
    deploy) so a full scan is fine.
    """
    rows = await session.scalars(
        select(Job).where(Job.owner.is_(None), Job.to_version == to_version)
    )
    for row in rows:
        if row.scope_json == scope:
            return row
    return None


async def migrate(
    source: Path,
    session_factory: async_sessionmaker[AsyncSession],
    *,
    dry_run: bool = False,
) -> dict[str, int]:
    """Migrate the saved-job config from ``source`` into the ``jobs`` table.

    Returns ``{"jobs_inserted": int, "jobs_skipped": int}``.
    """
    payload = _read_job_json(source)
    to_version = payload.get("to_version")
    scope = payload.get("scope")

    inserted = 0
    skipped = 0

    async with session_factory() as session:
        existing = await _find_existing(session, to_version=to_version, scope=scope)
        if existing is not None:
            skipped = 1
        else:
            inserted = 1
            if not dry_run:
                session.add(Job(owner=None, to_version=to_version, scope_json=scope))
                await session.commit()

    return {"jobs_inserted": inserted, "jobs_skipped": skipped}


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Seed the jobs table from data/update-job.json.",
    )
    parser.add_argument(
        "--source",
        type=Path,
        default=Path("data/update-job.json"),
        help="Path to the legacy update-job.json (default: data/update-job.json).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Report what would be written, without touching the database.",
    )
    return parser


async def _amain(argv: Optional[Iterable[str]] = None) -> int:
    args = _build_arg_parser().parse_args(list(argv) if argv is not None else None)
    if not args.source.is_file():
        _logger.error("source not found: %s", args.source)
        return 2
    factory = _get_or_create_session_factory()
    counts = await migrate(args.source, factory, dry_run=args.dry_run)
    _logger.info("seed_jobs done (dry_run=%s): %s", args.dry_run, counts)
    return 0


def main(argv: Optional[Iterable[str]] = None) -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    return asyncio.run(_amain(argv))


if __name__ == "__main__":
    sys.exit(main())
