"""Resolve a relative lesson-content path to served bytes (KNOW-2347 / -2360).

Backs ``GET /lesson-content/{rel_path}`` (see ``app/routes/lesson_content.py``),
which serves the lesson images the report references. The report points
``<img>`` at a stable, same-origin ``/lesson-content/{lesson_dir}/images/{file}``
URL instead of the old relative ``../{lesson_dir}/...`` form that only resolved
under the legacy "serve from project root" model and 404'd after the EC2
cutover.

**Swap point (KNOW-2360).** Reads now go through a
:class:`pipeline.content_source.ContentSource` instead of touching the local
filesystem directly, so the same route serves content from the on-disk corpus
(``content_source='local'`` — today's default) *or* the public S3 mirror
(``'s3mirror'``), where there is no local file to ``FileResponse``. The route
path and the report's URL format stay the same across both backends.

``resolve_content_path`` is kept as the local-only path resolver (it still
guards against escaping the content root, and the local backend ultimately
reads under that same root). :func:`read_content_bytes` is the
backend-agnostic entry point the route uses: it parses ``rel_path`` into a
``lesson_dir`` + image filename / ``index.html`` and dispatches to the source's
``read_image_bytes`` / ``get_lesson_html``, returning ``(bytes, media_type)``.
"""
from __future__ import annotations

import mimetypes
from pathlib import Path, PurePosixPath

from pipeline.content_source import ContentSource, LessonContentNotFound

# Default content type for bytes we can't classify from the extension. Matches
# what FileResponse/Starlette falls back to for an unknown suffix.
_DEFAULT_MEDIA_TYPE = "application/octet-stream"


def resolve_content_path(rel_path: str, *, content_root: Path) -> Path:
    """Return the file at ``content_root / rel_path``, guarding against escape.

    Raises ``LookupError`` if ``rel_path`` escapes ``content_root`` (``..``
    segments, an absolute path, or a symlink pointing outside) or if no regular
    file exists there. The route turns ``LookupError`` into a 404 — this is a
    public, unauthenticated endpoint, so it must never read arbitrary files.

    Used directly by the local backend path and retained for callers/tests that
    need a concrete filesystem path; :func:`read_content_bytes` is the
    backend-agnostic served-bytes entry point.
    """
    root = Path(content_root).resolve()
    candidate = (root / rel_path).resolve()
    # Refuse anything that isn't strictly inside the content root.
    if candidate != root and root not in candidate.parents:
        raise LookupError(f"{rel_path!r} resolves outside the content root")
    if not candidate.is_file():
        raise LookupError(f"{rel_path!r}: no such file under the content root")
    return candidate


def _guess_media_type(filename: str) -> str:
    """Best-effort content type from a filename's extension.

    Mirrors what ``FileResponse`` did before (Starlette uses ``mimetypes`` /
    ``guess_type`` on the path), falling back to ``application/octet-stream`` for
    unknown suffixes so a download is offered rather than a mislabelled body.
    """
    media_type, _encoding = mimetypes.guess_type(filename)
    return media_type or _DEFAULT_MEDIA_TYPE


def _reject_unsafe(rel_path: str) -> str:
    """Normalise + path-safety-check a POSIX ``rel_path`` for public serving.

    Raises ``LookupError`` for absolute paths or any ``..`` traversal. Returns
    the cleaned, leading-slash-stripped POSIX path. This guard is backend-
    agnostic (the S3 mirror has no filesystem to resolve against), and the local
    backend additionally re-checks containment inside the content root.
    """
    if not rel_path:
        raise LookupError("empty content path")
    pure = PurePosixPath(rel_path)
    if pure.is_absolute() or ".." in pure.parts:
        raise LookupError(f"{rel_path!r} is not a safe content path")
    cleaned = pure.as_posix().lstrip("/")
    if not cleaned or cleaned == ".":
        raise LookupError(f"{rel_path!r} is not a safe content path")
    return cleaned


def read_content_bytes(
    rel_path: str, *, source: ContentSource
) -> tuple[bytes, str]:
    """Return ``(bytes, media_type)`` for a ``/lesson-content/`` request.

    Parses ``rel_path`` into a ``lesson_dir`` + leaf and dispatches to the
    content source:

    - ``{lesson_dir}/images/{file}``  → ``source.read_image_bytes`` (the report's
      image URLs; the common case).
    - ``{lesson_dir}/index.html``     → ``source.get_lesson_html`` (utf-8 encoded).

    Raises ``LookupError`` (which the route maps to 404) for unsafe paths,
    shapes this route doesn't serve, or a content miss. Works identically over
    the local-folder and S3-mirror backends — under ``s3mirror`` there is no
    local file, so bytes come straight from the mirror.
    """
    cleaned = _reject_unsafe(rel_path)

    # Image: split on the LAST '/images/' so a lesson dir literally named with
    # "images" earlier in the path can't be misparsed; filename is the bare leaf.
    marker = "/images/"
    if marker in cleaned:
        lesson_dir, _, filename = cleaned.rpartition(marker)
        if not lesson_dir or not filename or "/" in filename:
            raise LookupError(f"{rel_path!r}: not a lesson image path")
        try:
            data = source.read_image_bytes(lesson_dir, filename)
        except LessonContentNotFound as exc:
            raise LookupError(str(exc)) from exc
        return data, _guess_media_type(filename)

    # Lesson HTML: anything ending in index.html.
    if cleaned == "index.html" or cleaned.endswith("/index.html"):
        lesson_dir = cleaned[: -len("/index.html")] if "/" in cleaned else ""
        try:
            html = source.get_lesson_html(lesson_dir)
        except LessonContentNotFound as exc:
            raise LookupError(str(exc)) from exc
        return html.encode("utf-8"), "text/html; charset=utf-8"

    # The route serves only lesson images + index.html. Anything else is a miss
    # (and, importantly, the S3 backend has no notion of an arbitrary file).
    raise LookupError(f"{rel_path!r}: not a served lesson-content path")
