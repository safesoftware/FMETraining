"""Seed the ``jira_cache`` table from ``.cache/jira_api_cache.json``.

The legacy pipeline cached the latest Jira filter response on disk under
``.cache/jira_api_cache.json``. In the multi-user app the metadata moves
to a row in ``jira_cache`` while the actual issues payload lives outside
the database -- in the original plan that was S3, in the EC2 deployment
it's a file under the drafts/scratch root.

Source shape::

    {
        "fetched_at": "2026-03-04T22:41:00Z",
        "filter_id": "12345",
        "total": 1700,
        "issues": [...]
    }

Mapping:

* ``filter_id``  -> ``jira_cache.filter_id`` (PK)
* ``fetched_at`` -> ``jira_cache.fetched_at``
* ``total``      -> ``jira_cache.issue_count``
* The full ``issues`` payload (re-wrapped with the same outer keys) is
  written to ``<scratch_root>/jira-cache/<filter_id>.json`` so the
  worker / SSE log streamer can read it back. The relative path is
  stored in ``jira_cache.payload_s3_key`` -- the column name is a
  carryover from the S3 plan; on EC2 it doubles as a filesystem path.

Idempotent: if a row already exists for ``filter_id``, we UPDATE the
metadata + overwrite the payload file. Use ``--dry-run`` to preview.
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
from app.models.cache import JiraCache

_logger = logging.getLogger(__name__)


def _parse_fetched_at(raw: Optional[str]) -> datetime:
    if not raw:
        return datetime.utcnow()
    return datetime.fromisoformat(raw.replace("Z", "+00:00"))


def _read_cache_json(source: Path) -> dict[str, Any]:
    payload = json.loads(source.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{source} did not contain a JSON object")
    if "filter_id" not in payload:
        raise ValueError(f"{source} is missing required key 'filter_id'")
    return payload


async def migrate(
    source: Path,
    session_factory: async_sessionmaker[AsyncSession],
    *,
    scratch_root: Path,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Migrate the Jira cache file into the DB + scratch root.

    Returns counts plus the resolved payload path so the caller / tests
    can verify the file landed where expected.
    """
    payload = _read_cache_json(source)
    filter_id = str(payload["filter_id"])
    fetched_at = _parse_fetched_at(payload.get("fetched_at"))
    issue_count = payload.get("total")
    if issue_count is None and isinstance(payload.get("issues"), list):
        issue_count = len(payload["issues"])

    payload_dir = (scratch_root / "jira-cache").resolve()
    payload_path = payload_dir / f"{filter_id}.json"

    rows_inserted = 0
    rows_updated = 0

    async with session_factory() as session:
        existing = await session.get(JiraCache, filter_id)
        if existing is None:
            rows_inserted = 1
            if not dry_run:
                session.add(
                    JiraCache(
                        filter_id=filter_id,
                        fetched_at=fetched_at,
                        payload_s3_key=str(payload_path),
                        issue_count=issue_count,
                    )
                )
        else:
            rows_updated = 1
            if not dry_run:
                existing.fetched_at = fetched_at
                existing.payload_s3_key = str(payload_path)
                existing.issue_count = issue_count

        if not dry_run:
            # Commit the DB row first so a write-then-commit-fails sequence
            # can't leave a stale payload file pointing at a row that
            # doesn't exist. If the file write fails after commit, the row
            # still references the intended path and a re-run will rewrite
            # it.
            await session.commit()
            payload_dir.mkdir(parents=True, exist_ok=True)
            payload_path.write_text(
                json.dumps(payload, ensure_ascii=False),
                encoding="utf-8",
            )

    return {
        "rows_inserted": rows_inserted,
        "rows_updated": rows_updated,
        "payload_path": str(payload_path),
    }


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Seed jira_cache from .cache/jira_api_cache.json.",
    )
    parser.add_argument(
        "--source",
        type=Path,
        default=Path(".cache/jira_api_cache.json"),
        help="Path to the legacy jira_api_cache.json (default: .cache/jira_api_cache.json).",
    )
    parser.add_argument(
        "--scratch-root",
        type=Path,
        default=Path("/var/lib/fme-train"),
        help="Root for scratch files (default: /var/lib/fme-train). The "
             "payload is written under <root>/jira-cache/<filter_id>.json.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Report what would be written, without touching the database "
             "or the filesystem.",
    )
    return parser


async def _amain(argv: Optional[Iterable[str]] = None) -> int:
    args = _build_arg_parser().parse_args(list(argv) if argv is not None else None)
    if not args.source.is_file():
        _logger.error("source not found: %s", args.source)
        return 2
    factory = _get_or_create_session_factory()
    result = await migrate(
        args.source,
        factory,
        scratch_root=args.scratch_root,
        dry_run=args.dry_run,
    )
    _logger.info("seed_jira_cache done (dry_run=%s): %s", args.dry_run, result)
    return 0


def main(argv: Optional[Iterable[str]] = None) -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    return asyncio.run(_amain(argv))


if __name__ == "__main__":
    sys.exit(main())
