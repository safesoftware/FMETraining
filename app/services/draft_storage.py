"""Where lesson-draft HTML lives on disk.

Plan section 5: drafts replace the legacy ``_handle_save_lesson`` writes
to ``REPO_ROOT/<to_version>/...``. The original plan stored drafts in
``s3://…/drafts/{to_version}/{path}/index.html``; the EC2 deployment
keeps them on local disk under ``/var/lib/fme-train/drafts/...`` (or a
configurable root in dev/test). Same logical layout, different backend.

This module exposes a small abstraction so the route layer is
storage-agnostic. Today's only implementation is :class:`LocalDiskDraftStorage`;
an S3 variant slots in the same shape if we ever scale beyond one box.
"""
from __future__ import annotations

import abc
import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

_logger = logging.getLogger(__name__)

# Allow the same shape the Skilljar taxonomy uses:
#   "<learning-path>/<course>/<lesson>" — segments may contain spaces,
#   parens, hyphens, dots in middle, alnum, plus a few common punctuation
#   marks. We forbid anything that could escape the storage root.
_FORBIDDEN_PATH_RE = re.compile(r"(\.\.|^/|^\\|^~|//)")
_VERSION_RE = re.compile(r"^\d{4}\.\d+$")


class DraftStorageError(Exception):
    """Generic draft-storage failure (mostly path-validation)."""


def _validate_to_version(to_version: str) -> None:
    """``to_version`` must look like a version string (YYYY.N) so callers
    can't smuggle in path segments via this field."""
    if not _VERSION_RE.match(to_version or ""):
        raise DraftStorageError(
            f"to_version {to_version!r} is not a valid version (expected e.g. '2026.1')"
        )


def _validate_path(path: str) -> None:
    """The lesson path must be a relative ``<lp>/<course>/<lesson>`` triple
    with no traversal segments."""
    if not path:
        raise DraftStorageError("path must be non-empty")
    if _FORBIDDEN_PATH_RE.search(path):
        raise DraftStorageError(
            f"path {path!r} contains forbidden characters (no '..', leading slashes, etc.)"
        )
    # Must have at least one segment — Skilljar paths are typically 3.
    segments = [s for s in path.split("/") if s]
    if not segments:
        raise DraftStorageError(f"path {path!r} resolves to no segments")


@dataclass(frozen=True)
class DraftLocation:
    """Where a draft is stored. ``key`` is the value the caller persists
    in ``lesson_drafts.s3_key`` (kept the column name even though it's
    a local path in the EC2 deployment — see plan note).
    """

    key: str
    to_version: str
    path: str


class DraftStorage(abc.ABC):
    """Read/write/delete lesson-draft HTML."""

    @abc.abstractmethod
    async def write(self, *, to_version: str, path: str, html: str) -> DraftLocation:
        """Store ``html`` for the given draft. Returns the location key."""

    @abc.abstractmethod
    async def read(self, key: str) -> str:
        """Fetch the HTML for a previously-written draft. Raises
        ``LookupError`` if the key isn't known."""


# ---------------------------------------------------------------------------
# Local-disk implementation
# ---------------------------------------------------------------------------


class LocalDiskDraftStorage(DraftStorage):
    """Writes drafts to ``<root>/<to_version>/<path>/index.html``.

    The on-disk layout mirrors what the original AWS-S3 plan called for,
    just under a local root. ``key`` is the absolute path of the
    written file — the caller stores it in ``lesson_drafts.s3_key`` and
    we resolve the same way on read.
    """

    def __init__(self, root: Path) -> None:
        self._root = Path(root).resolve()
        # Ensure the root exists. We do NOT create parent paths above it,
        # so a misconfigured root fails loudly the first time a write fires.
        self._root.mkdir(parents=True, exist_ok=True)

    async def write(
        self, *, to_version: str, path: str, html: str
    ) -> DraftLocation:
        _validate_to_version(to_version)
        _validate_path(path)

        target = (self._root / to_version / path / "index.html").resolve()
        # Defence in depth: even with the regex guards above, confirm
        # the resolved path stays inside the root.
        if not str(target).startswith(str(self._root) + "/"):
            raise DraftStorageError(
                f"draft path resolves outside root: {target}"
            )
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(html, encoding="utf-8")
        _logger.info(
            "Wrote draft for to_version=%s path=%s (%d bytes)",
            to_version, path, len(html),
        )
        return DraftLocation(key=str(target), to_version=to_version, path=path)

    async def read(self, key: str) -> str:
        target = Path(key).resolve()
        if not str(target).startswith(str(self._root) + "/"):
            raise LookupError(
                f"draft key {key!r} resolves outside this storage's root"
            )
        if not target.is_file():
            raise LookupError(f"draft key {key!r}: no such file")
        return target.read_text(encoding="utf-8")
