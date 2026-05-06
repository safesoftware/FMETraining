"""Seed lesson drafts from local ``<version>/<lp>/<course>/<lesson>/index.html``.

The legacy launcher writes regenerated lessons into a per-version folder
at the repo root (e.g. ``2026.1/fme-form-basic/<course>/<lesson>/index.html``).
The multi-user app stores drafts under
``<drafts_root>/<to_version>/<lp>/<course>/<lesson>/index.html`` and tracks
them in the ``lesson_drafts`` table.

For each ``index.html`` we find under the source directory:

1. Derive ``to_version`` from the top-level folder name (must match
   ``YYYY.N`` -- the same format the route accepts).
2. Derive ``path = "<lp>/<course>/<lesson>"`` from the next three segments.
3. Write the HTML body to the new drafts root via :class:`LocalDiskDraftStorage`.
4. Insert a ``LessonDraft`` row with ``status='draft'``,
   ``source_skilljar_lesson_id=NULL`` (we don't have a Skilljar mapping yet),
   ``created_by=NULL`` (no users at migration time).

Idempotent via the ``UNIQUE(to_version, path)`` constraint introduced in
Alembic revision ``0003``: a second invocation skips drafts that already
have a row in ``lesson_drafts``. Use ``--dry-run`` to preview.
"""
from __future__ import annotations

import argparse
import asyncio
import logging
import re
import sys
from pathlib import Path
from typing import Iterable, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.db.engine import _get_or_create_session_factory
from app.models.skilljar import LessonDraft
from app.services.draft_storage import LocalDiskDraftStorage

_logger = logging.getLogger(__name__)

_VERSION_RE = re.compile(r"^\d{4}\.\d+$")


def _iter_legacy_drafts(version_root: Path) -> Iterable[tuple[str, str, Path]]:
    """Yield ``(to_version, path, html_file)`` for each draft under ``version_root``.

    Expects the layout ``<version_root>/<lp>/<course>/<lesson>/index.html``.
    Skips any deeper or shallower placements with a warning.
    """
    if not version_root.is_dir():
        return
    to_version = version_root.name
    if not _VERSION_RE.match(to_version):
        _logger.warning(
            "skipping %s: top-level folder name %r is not a valid version",
            version_root, to_version,
        )
        return

    for index_file in sorted(version_root.rglob("index.html")):
        rel = index_file.relative_to(version_root).parent
        parts = rel.parts
        if len(parts) != 3:
            _logger.warning(
                "skipping %s: expected <lp>/<course>/<lesson>/index.html, got %s",
                index_file, "/".join(parts),
            )
            continue
        path = "/".join(parts)
        yield to_version, path, index_file


async def migrate(
    source: Path,
    session_factory: async_sessionmaker[AsyncSession],
    *,
    drafts_root: Path,
    dry_run: bool = False,
) -> dict[str, int]:
    """Migrate every legacy draft under ``source`` into ``drafts_root`` + DB.

    Returns ``{"drafts_inserted", "drafts_skipped"}``. Skips any draft
    whose ``(to_version, path)`` row already exists.
    """
    storage = LocalDiskDraftStorage(drafts_root)

    inserted = 0
    skipped = 0

    async with session_factory() as session:
        for to_version, path, html_file in _iter_legacy_drafts(source):
            existing = await session.scalar(
                select(LessonDraft).where(
                    LessonDraft.to_version == to_version,
                    LessonDraft.path == path,
                )
            )
            if existing is not None:
                skipped += 1
                continue

            html = html_file.read_text(encoding="utf-8")
            if dry_run:
                inserted += 1
                continue

            location = await storage.write(
                to_version=to_version, path=path, html=html
            )
            session.add(
                LessonDraft(
                    to_version=to_version,
                    source_skilljar_lesson_id=None,
                    path=path,
                    s3_key=location.key,
                    created_by=None,
                    updated_by=None,
                    run_id=None,
                    status="draft",
                )
            )
            inserted += 1

        if not dry_run:
            await session.commit()

    return {"drafts_inserted": inserted, "drafts_skipped": skipped}


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Seed lesson_drafts from a legacy <version>/ folder.",
    )
    parser.add_argument(
        "--source",
        type=Path,
        required=True,
        help="Path to the legacy version folder (e.g. ./2026.1).",
    )
    parser.add_argument(
        "--drafts-root",
        type=Path,
        default=Path("/var/lib/fme-train/drafts"),
        help="Where the new draft files are written (default: "
             "/var/lib/fme-train/drafts).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Walk the source and report what would be written.",
    )
    return parser


async def _amain(argv: Optional[Iterable[str]] = None) -> int:
    args = _build_arg_parser().parse_args(list(argv) if argv is not None else None)
    if not args.source.is_dir():
        _logger.error("source directory not found: %s", args.source)
        return 2
    factory = _get_or_create_session_factory()
    counts = await migrate(
        args.source,
        factory,
        drafts_root=args.drafts_root,
        dry_run=args.dry_run,
    )
    _logger.info("seed_drafts done (dry_run=%s): %s", args.dry_run, counts)
    return 0


def main(argv: Optional[Iterable[str]] = None) -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    return asyncio.run(_amain(argv))


if __name__ == "__main__":
    sys.exit(main())
