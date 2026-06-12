"""Resolve a relative lesson-content path to a local file (KNOW-2347).

Backs ``GET /lesson-content/{rel_path}`` (see ``app/routes/lesson_content.py``),
which serves the lesson images the report references. The report points
``<img>`` at a stable, same-origin ``/lesson-content/{lesson_dir}/images/{file}``
URL instead of the old relative ``../{lesson_dir}/...`` form that only resolved
under the legacy "serve from project root" model and 404'd after the EC2
cutover.

``content_root`` is ``Settings.lesson_content_root`` — the *same* root the
pipeline reads lesson HTML from (``app/routes/runs.py``,
``app/services/pipeline_runner.py``), so what the report displays and what the
pipeline processes stay consistent by construction.

**Swap point.** When lesson content stops living in the repo and moves to a
Skilljar/backup cache (the planned migration), only this resolver changes — the
route path and the report's URL format stay the same.
"""
from __future__ import annotations

from pathlib import Path


def resolve_content_path(rel_path: str, *, content_root: Path) -> Path:
    """Return the file at ``content_root / rel_path``, guarding against escape.

    Raises ``LookupError`` if ``rel_path`` escapes ``content_root`` (``..``
    segments, an absolute path, or a symlink pointing outside) or if no regular
    file exists there. The route turns ``LookupError`` into a 404 — this is a
    public, unauthenticated endpoint, so it must never read arbitrary files.
    """
    root = Path(content_root).resolve()
    candidate = (root / rel_path).resolve()
    # Refuse anything that isn't strictly inside the content root.
    if candidate != root and root not in candidate.parents:
        raise LookupError(f"{rel_path!r} resolves outside the content root")
    if not candidate.is_file():
        raise LookupError(f"{rel_path!r}: no such file under the content root")
    return candidate
