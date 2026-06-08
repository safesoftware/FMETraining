"""Seed the ``runs`` and ``run_steps`` tables from ``artifacts/runs.json``.

The legacy launcher writes one entry per pipeline run into
``artifacts/runs.json`` via ``pipeline.utils.register_run``; the shape is::

    {
        "runs": [
            {
                "run_id": "20260304T225238-fe4b",
                "started_at": "2026-03-04T22:52:38.317691+00:00",
                "job": {"to_version": "2026.1", "scope": {...}},
                "steps_completed": [1, 2],
                "artifacts": {"manifest": "...", "changelog": "...", ...}
            },
            ...
        ]
    }

Migration mapping:

* ``run_id`` -> ``runs.id``
* ``started_at`` -> ``runs.created_at``, ``runs.started_at``, ``runs.finished_at``
  (the legacy file only stores one timestamp per run)
* ``job.to_version`` -> ``runs.to_version``
* ``job.scope`` -> ``runs.scope_json``
* ``artifacts`` map -> ``runs.options_json["artifacts"]`` for traceability
* ``status`` is hard-coded to ``"done"`` because every entry in the legacy
  file represents a completed run -- failures never made it past the
  in-memory state.
* For each step in ``steps_completed``, a ``RunStep(status="done")`` row is
  written with ``started_at`` / ``finished_at`` both equal to the run's
  timestamp (we don't have per-step timing in the legacy data).

Idempotent: any ``runs.id`` that already exists in the database is left
untouched. Use ``--dry-run`` to preview without writing.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable, Optional

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.db.engine import _get_or_create_session_factory
from app.models.runs import Run, RunStep

_logger = logging.getLogger(__name__)


def _parse_started_at(raw: str) -> datetime:
    """Parse ISO-8601 timestamps with or without trailing 'Z'."""
    s = raw.replace("Z", "+00:00")
    return datetime.fromisoformat(s)


def _read_runs_json(source: Path) -> list[dict[str, Any]]:
    payload = json.loads(source.read_text(encoding="utf-8"))
    if isinstance(payload, list):
        # Tolerate the older "bare list" shape just in case.
        return payload
    runs = payload.get("runs")
    if not isinstance(runs, list):
        raise ValueError(
            f"{source} does not have the expected shape; "
            f"top-level keys: {list(payload.keys())}"
        )
    return runs


async def migrate(
    source: Path,
    session_factory: async_sessionmaker[AsyncSession],
    *,
    dry_run: bool = False,
) -> dict[str, int]:
    """Migrate runs + run_steps from ``source`` into the DB.

    Returns a counts dict: ``{"runs_inserted", "runs_skipped", "steps_inserted"}``.
    """
    entries = _read_runs_json(source)
    runs_inserted = 0
    runs_skipped = 0
    steps_inserted = 0

    async with session_factory() as session:
        for entry in entries:
            run_id = entry.get("run_id")
            if not run_id:
                _logger.warning("skipping entry with no run_id: %r", entry)
                continue

            existing = await session.get(Run, run_id)
            if existing is not None:
                runs_skipped += 1
                continue

            ts_raw = entry.get("started_at")
            ts = _parse_started_at(ts_raw) if ts_raw else datetime.utcnow()
            job = entry.get("job") or {}
            scope = job.get("scope")
            to_version = job.get("to_version")
            artifacts = entry.get("artifacts") or {}

            if not dry_run:
                run = Run(
                    id=run_id,
                    created_by=None,
                    to_version=to_version,
                    scope_json=scope,
                    options_json={"artifacts": artifacts} if artifacts else None,
                    status="done",
                    started_at=ts,
                    finished_at=ts,
                    created_at=ts,
                )
                session.add(run)
                # Flush so the FK from RunStep -> runs.id resolves before commit.
                await session.flush()

            for step_num in entry.get("steps_completed") or []:
                if not dry_run:
                    session.add(
                        RunStep(
                            run_id=run_id,
                            step_num=int(step_num),
                            status="done",
                            started_at=ts,
                            finished_at=ts,
                        )
                    )
                steps_inserted += 1

            runs_inserted += 1

        if not dry_run:
            await session.commit()

    return {
        "runs_inserted": runs_inserted,
        "runs_skipped": runs_skipped,
        "steps_inserted": steps_inserted,
    }


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Seed the runs/run_steps tables from artifacts/runs.json.",
    )
    parser.add_argument(
        "--source",
        type=Path,
        default=Path("artifacts/runs.json"),
        help="Path to the legacy runs.json file (default: artifacts/runs.json).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Read the source and report what would be written, without "
             "touching the database.",
    )
    return parser


async def _amain(argv: Optional[Iterable[str]] = None) -> int:
    args = _build_arg_parser().parse_args(list(argv) if argv is not None else None)
    if not args.source.is_file():
        _logger.error("source not found: %s", args.source)
        return 2
    factory = _get_or_create_session_factory()
    counts = await migrate(args.source, factory, dry_run=args.dry_run)
    _logger.info("seed_runs done (dry_run=%s): %s", args.dry_run, counts)
    return 0


def main(argv: Optional[Iterable[str]] = None) -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    return asyncio.run(_amain(argv))


if __name__ == "__main__":
    sys.exit(main())
