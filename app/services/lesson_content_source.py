"""Pluggable abstraction over "where lesson content comes from".

Plan section 1 calls for a ``LessonContentSource`` so the pipeline modules
can read lesson HTML from either the legacy local-folder layout (today)
or the Skilljar API (future v1 production). This lets us run integration
tests against synthetic content without hitting Skilljar.

This module ships:

- :class:`LessonRef` — opaque identifier the pipeline passes around.
- :class:`LessonContentSource` — abstract base.
- :class:`LocalFolderSource` — reads from the existing
  ``REPO_ROOT / {version} / {learning_path} / {course} / {lesson} / index.html``
  layout. Useful for dev, tests, and the legacy CLI path.
- :class:`SkilljarContentSource` — *skeleton only*. Real implementation
  lands in a follow-up ticket once the lesson content is being cached
  to disk by the sync endpoint (KNOW-2272 part 2).

Pipeline modules consume the interface, never the concrete classes, so
later changes to the storage layout (S3 vs local disk vs Skilljar API)
don't ripple through.
"""
from __future__ import annotations

import abc
import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

_logger = logging.getLogger(__name__)

_VERSION_FOLDER_RE = re.compile(r"^\d{4}\.\d+$")
_COURSE_VERSION_SUFFIX_RE = re.compile(r"\s+(\d{4}\.\d+)$")


@dataclass(frozen=True)
class LessonRef:
    """Stable identifier for a single lesson under a content source.

    ``source_id`` is opaque outside the source that produced it, but
    callers should treat it as a string they can store and later pass
    back to :meth:`LessonContentSource.get_html`.

    Examples::

        LessonRef(
            source_id="local:2025.0/fme-form-basic/Connect To Data 2025.0/Lesson 1",
            title="Lesson 1",
            course_title="Connect To Data",
            learning_path_title="fme-form-basic",
            version="2025.0",
        )

        LessonRef(
            source_id="skilljar:abcdef1234567890",
            title="Connect to a Database",
            course_title="Connect To Data 2026.1",
            learning_path_title="FME Form Basic",
            version="2026.1",
        )
    """

    source_id: str
    title: str
    course_title: Optional[str] = None
    learning_path_title: Optional[str] = None
    version: Optional[str] = None


class LessonContentSource(abc.ABC):
    """Read lesson metadata + HTML, regardless of storage backend."""

    @abc.abstractmethod
    async def list_lessons(
        self, *, version: Optional[str] = None
    ) -> list[LessonRef]:
        """Return every lesson the source knows about.

        If ``version`` is passed, return only lessons that match that
        version label. Sources that don't track versions (e.g. an
        un-versioned dev folder) should ignore the filter.
        """

    @abc.abstractmethod
    async def get_html(self, source_id: str) -> str:
        """Return the lesson's HTML body. Raises ``LookupError`` if
        ``source_id`` isn't known to this source."""


# ---------------------------------------------------------------------------
# Local-folder implementation
# ---------------------------------------------------------------------------


class LocalFolderSource(LessonContentSource):
    """Walks ``REPO_ROOT / <version> / <learning_path> / <course> / <lesson> /
    index.html`` to expose lessons. Matches the layout the legacy CLI
    expects and that the dev container has on disk today.
    """

    _SOURCE_PREFIX = "local:"

    def __init__(self, repo_root: Path) -> None:
        self._repo_root = Path(repo_root).resolve()

    async def list_lessons(
        self, *, version: Optional[str] = None
    ) -> list[LessonRef]:
        results: list[LessonRef] = []
        for version_dir in sorted(self._repo_root.iterdir()):
            if not version_dir.is_dir() or not _VERSION_FOLDER_RE.match(version_dir.name):
                continue
            if version is not None and version_dir.name != version:
                continue
            for lp_dir in sorted(p for p in version_dir.iterdir() if p.is_dir()):
                for course_dir in sorted(p for p in lp_dir.iterdir() if p.is_dir()):
                    course_canonical = _COURSE_VERSION_SUFFIX_RE.sub(
                        "", course_dir.name
                    )
                    for lesson_dir in sorted(
                        p for p in course_dir.iterdir() if p.is_dir()
                    ):
                        index_html = lesson_dir / "index.html"
                        if not index_html.is_file():
                            continue
                        rel = lesson_dir.relative_to(self._repo_root).as_posix()
                        results.append(
                            LessonRef(
                                source_id=f"{self._SOURCE_PREFIX}{rel}",
                                title=lesson_dir.name,
                                course_title=course_canonical,
                                learning_path_title=lp_dir.name,
                                version=version_dir.name,
                            )
                        )
        return results

    async def get_html(self, source_id: str) -> str:
        if not source_id.startswith(self._SOURCE_PREFIX):
            raise LookupError(
                f"source_id {source_id!r} is not owned by LocalFolderSource"
            )
        rel = source_id[len(self._SOURCE_PREFIX):]
        path = (self._repo_root / rel / "index.html").resolve()
        # Defensive: refuse to escape repo_root. A crafted source_id with
        # ".." segments would otherwise read arbitrary files.
        if not str(path).startswith(str(self._repo_root) + "/") and path != self._repo_root:
            raise LookupError(
                f"source_id {source_id!r} resolves outside the repo root"
            )
        if not path.is_file():
            raise LookupError(f"source_id {source_id!r}: no such file")
        return path.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Skilljar implementation (skeleton)
# ---------------------------------------------------------------------------


class SkilljarContentSource(LessonContentSource):
    """Reads lesson HTML from the cached Skilljar content blobs.

    Real implementation lands once the sync endpoint persists per-lesson
    HTML to disk and we know the cache key shape. Until then, raising
    NotImplementedError is the safer default — accidental selection in
    config fails loudly rather than returning empty data.
    """

    def __init__(self, *, content_root: Optional[Path] = None) -> None:
        self._content_root = Path(content_root) if content_root else None

    async def list_lessons(  # pragma: no cover — placeholder
        self, *, version: Optional[str] = None
    ) -> list[LessonRef]:
        raise NotImplementedError(
            "SkilljarContentSource lands when the sync endpoint persists "
            "lesson HTML to disk. See KNOW-2272 follow-up."
        )

    async def get_html(self, source_id: str) -> str:  # pragma: no cover — placeholder
        raise NotImplementedError(
            "SkilljarContentSource lands when the sync endpoint persists "
            "lesson HTML to disk. See KNOW-2272 follow-up."
        )
