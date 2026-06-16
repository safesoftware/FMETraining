"""Shared lesson-content resolution layer (KNOW-2360, the S3-mirror keystone).

Every place that today reaches into the local filesystem corpus to read a
lesson's ``index.html``, list/read its ``images/``, or discover which lessons
exist under a version goes through *this* module instead. Two backends sit
behind one typed interface:

- :class:`LocalFolderSource` — the historical behaviour: walk
  ``content_root / {version} / {lp} / {course} / {lesson} / index.html`` on
  disk. This stays the dev/test/CLI default and is byte-for-byte what the
  pipeline did before.
- :class:`S3MirrorSource` — anonymous HTTPS reads against a public S3 mirror
  whose keys mirror the corpus layout exactly
  (``{base_url}/{urlquote(key)}``), and ListObjectsV2 (paginated, XML) for
  discovery. The bucket carries punctuation-variant *duplicate* lesson dirs
  (``Exercise. Foo`` / ``Exercise: Foo`` / ``Exercise_ Foo``); discovery
  dedupes them to the single filesystem-sanitised form the local corpus uses
  (see :func:`_dedupe_variant_dirs`).

The backend is selected by config (``CONTENT_SOURCE`` = ``local`` | ``s3mirror``
+ ``CONTENT_S3_BASE_URL``) via the :func:`get_content_source` factory, which all
call sites use.

**Layering rule:** this module lives in ``pipeline/`` and imports ONLY from
``pipeline`` + stdlib + ``httpx``. ``app/`` imports it (app already depends on
pipeline); pipeline must never import app. Do not add an ``app`` import here.

Concept glossary (stable across both backends):
- ``lesson_dir`` — repo-relative POSIX path to a lesson folder, i.e.
  ``{version}/{lp}/{course folder}/{lesson folder}`` (NO trailing
  ``/index.html``). This is the same string the pipeline already threads around
  as ``lesson_dir`` / the parent of ``manifest`` record ``path`` values.
- Image ``filename`` — the bare file name inside the lesson's ``images/`` dir
  (e.g. ``foo.png``), NOT the ``images/foo.png`` relative src.
"""
from __future__ import annotations

import abc
import html as _html
import logging
import re
import threading
import urllib.parse
from pathlib import Path

import httpx

from pipeline import config

_logger = logging.getLogger(__name__)

# Top-level FME version folder, e.g. "2025.0" / "2026.1".
_VERSION_FOLDER_RE = re.compile(r"^\d{4}\.\d+$")


class LessonContentNotFound(LookupError):
    """Raised when a requested lesson HTML / image does not exist in the source.

    Subclasses ``LookupError`` so existing call sites that catch ``LookupError``
    (e.g. ``app/services/content_files.py``) keep working.
    """


# ---------------------------------------------------------------------------
# Variant-dedupe rule (shared so tests can exercise it directly)
# ---------------------------------------------------------------------------

def _normalize_segment(segment: str) -> str:
    """Collapse every run of non-alphanumeric chars to a single space (lower).

    This is the same normalisation ``skilljar_release.link_draft_course`` uses
    to match filesystem-sanitised folder names against Skilljar titles
    (KNOW-2358), so ``Exercise. Foo`` / ``Exercise: Foo`` / ``Exercise_ Foo``
    all map to ``"exercise foo"``.
    """
    return re.sub(r"[^a-z0-9]+", " ", segment.lower()).strip()


def _normalize_lesson_dir(lesson_dir: str) -> str:
    """Normalise every path segment of a lesson_dir for variant grouping."""
    return "/".join(_normalize_segment(seg) for seg in lesson_dir.split("/") if seg)


# Characters that survive filesystem sanitisation in a lesson folder name:
# letters, digits, whitespace, and the few punctuation marks that are legal on
# disk and actually appear in real folder names (hyphen, underscore, parens,
# ampersand, comma, apostrophe). Everything else (``: ? . * " < > |`` etc.) is
# the kind of mark the corpus's on-disk form replaced with ``_``.
_SANITISED_PUNCT_RE = re.compile(r"[^0-9a-zA-Z\s\-_(),'&]")


def _variant_rank(lesson_dir: str) -> tuple:
    """Sort key that elects the *filesystem-sanitised* variant as canonical.

    The local corpus on disk only ever contains ONE variant of a duplicated
    lesson dir: the form where filesystem-problematic punctuation (``:`` ``?``
    ``.`` …) has been replaced by ``_``. The S3 mirror keeps all of
    ``Exercise. Foo`` / ``Exercise: Foo`` / ``Exercise_ Foo``. To make S3
    discovery return the SAME lesson_dir the local backend would, candidates are
    ranked so the underscore form wins:

      1. Fewer "non-sanitised" punctuation marks (see ``_SANITISED_PUNCT_RE``)
         ranks first — the on-disk ``_`` form scores 0; ``.``/``:``/``?`` forms
         score higher and lose.
      2. Tie-break: lexicographically smallest, for determinism.

    Returned tuple sorts ascending; the minimum is canonical.
    """
    unsanitised = len(_SANITISED_PUNCT_RE.findall(lesson_dir))
    return (unsanitised, lesson_dir)


def _dedupe_variant_dirs(lesson_dirs: list[str]) -> list[str]:
    """Collapse punctuation-variant duplicate lesson_dirs to one canonical each.

    Groups by :func:`_normalize_lesson_dir` and, within each group, keeps the
    :func:`_variant_rank` winner (the filesystem-sanitised form). Returns the
    survivors sorted, so output is deterministic regardless of input order.
    """
    groups: dict[str, list[str]] = {}
    for d in lesson_dirs:
        groups.setdefault(_normalize_lesson_dir(d), []).append(d)
    winners = [min(group, key=_variant_rank) for group in groups.values()]
    return sorted(winners)


# ---------------------------------------------------------------------------
# Interface
# ---------------------------------------------------------------------------

class ContentSource(abc.ABC):
    """Read lesson HTML + images and discover lessons, backend-agnostic.

    All paths are repo-relative POSIX ``lesson_dir`` strings (see module
    docstring). Methods raise :class:`LessonContentNotFound` on a miss rather
    than returning sentinels, except the explicit ``*_exists`` probes.
    """

    # -- Lesson HTML --------------------------------------------------------

    @abc.abstractmethod
    def get_lesson_html(self, lesson_dir: str) -> str:
        """Return the lesson's ``index.html`` text.

        Raises :class:`LessonContentNotFound` if the lesson has no index.html.
        """

    @abc.abstractmethod
    def lesson_html_exists(self, lesson_dir: str) -> bool:
        """True if ``lesson_dir/index.html`` exists in this source."""

    # -- Images -------------------------------------------------------------

    @abc.abstractmethod
    def list_lesson_images(self, lesson_dir: str) -> list[str]:
        """Return the bare filenames in the lesson's ``images/`` dir (sorted).

        Empty list if the lesson has no images/ dir. Filenames only (no
        ``images/`` prefix), matching the on-disk ``iterdir`` of images/.
        """

    @abc.abstractmethod
    def read_image_bytes(self, lesson_dir: str, filename: str) -> bytes:
        """Return raw bytes of ``lesson_dir/images/{filename}``.

        ``filename`` is the bare file name (``foo.png``); a leading ``images/``
        is tolerated and stripped. Raises :class:`LessonContentNotFound` on a
        miss.
        """

    @abc.abstractmethod
    def image_exists(self, lesson_dir: str, filename: str) -> bool:
        """True if ``lesson_dir/images/{filename}`` exists in this source."""

    # -- Discovery ----------------------------------------------------------

    @abc.abstractmethod
    def list_versions(self) -> list[str]:
        """Return the version folder names (e.g. ``["2026.1", ...]``).

        Newest-first (descending numeric). Replaces the ``root.iterdir()``
        ``_VERSION_RE`` scan in ``app/routes/runs.py`` / ``manifest.py``.
        """

    @abc.abstractmethod
    def discover_lessons(
        self, version: str, learning_path: str | None = None
    ) -> list[str]:
        """Return every lesson_dir under ``version`` (optionally one LP).

        A lesson_dir is included only if it has an ``index.html``. Punctuation
        variants are deduped to one canonical (sanitised) dir. Sorted output.
        Replaces ``rglob("index.html")`` / nested ``iterdir`` discovery.
        """

    @abc.abstractmethod
    def list_learning_paths(self, version: str) -> list[str]:
        """Return the LP folder names directly under ``version`` (sorted)."""

    @abc.abstractmethod
    def list_courses(self, version: str, learning_path: str) -> list[str]:
        """Return the course folder names under ``version/lp`` (sorted)."""


# ---------------------------------------------------------------------------
# Local-folder backend
# ---------------------------------------------------------------------------

class LocalFolderSource(ContentSource):
    """Filesystem backend over ``content_root`` — preserves legacy behaviour.

    ``content_root`` is ``config.LESSON_CONTENT_ROOT`` (= REPO_ROOT on the box /
    CLI, ``/content`` in the container). All reads resolve against it and are
    guarded against escaping it via crafted ``..`` segments.
    """

    def __init__(self, content_root: Path | str | None = None) -> None:
        root = content_root if content_root is not None else config.LESSON_CONTENT_ROOT
        self._root = Path(root).resolve()

    # -- internal path resolution ------------------------------------------

    def _resolve(self, *parts: str) -> Path:
        """Join + resolve under root, refusing anything that escapes it."""
        candidate = (self._root.joinpath(*parts)).resolve()
        if candidate != self._root and self._root not in candidate.parents:
            raise LessonContentNotFound(
                f"{'/'.join(parts)!r} resolves outside the content root"
            )
        return candidate

    # -- HTML ---------------------------------------------------------------

    def get_lesson_html(self, lesson_dir: str) -> str:
        path = self._resolve(lesson_dir, "index.html")
        if not path.is_file():
            raise LessonContentNotFound(f"{lesson_dir}/index.html: no such file")
        return path.read_text(encoding="utf-8")

    def lesson_html_exists(self, lesson_dir: str) -> bool:
        try:
            return self._resolve(lesson_dir, "index.html").is_file()
        except LessonContentNotFound:
            return False

    # -- Images -------------------------------------------------------------

    @staticmethod
    def _strip_images_prefix(filename: str) -> str:
        return filename[len("images/"):] if filename.startswith("images/") else filename

    def list_lesson_images(self, lesson_dir: str) -> list[str]:
        try:
            images_dir = self._resolve(lesson_dir, "images")
        except LessonContentNotFound:
            return []
        if not images_dir.is_dir():
            return []
        return sorted(p.name for p in images_dir.iterdir() if p.is_file())

    def read_image_bytes(self, lesson_dir: str, filename: str) -> bytes:
        filename = self._strip_images_prefix(filename)
        path = self._resolve(lesson_dir, "images", filename)
        if not path.is_file():
            raise LessonContentNotFound(
                f"{lesson_dir}/images/{filename}: no such file"
            )
        return path.read_bytes()

    def image_exists(self, lesson_dir: str, filename: str) -> bool:
        filename = self._strip_images_prefix(filename)
        try:
            return self._resolve(lesson_dir, "images", filename).is_file()
        except LessonContentNotFound:
            return False

    # -- Discovery ----------------------------------------------------------

    def list_versions(self) -> list[str]:
        if not self._root.is_dir():
            return []
        versions = [
            d.name
            for d in self._root.iterdir()
            if d.is_dir() and _VERSION_FOLDER_RE.match(d.name)
        ]
        return sorted(versions, key=_version_sort_key, reverse=True)

    def list_learning_paths(self, version: str) -> list[str]:
        try:
            version_dir = self._resolve(version)
        except LessonContentNotFound:
            return []
        if not version_dir.is_dir():
            return []
        return sorted(d.name for d in version_dir.iterdir() if d.is_dir())

    def list_courses(self, version: str, learning_path: str) -> list[str]:
        try:
            lp_dir = self._resolve(version, learning_path)
        except LessonContentNotFound:
            return []
        if not lp_dir.is_dir():
            return []
        return sorted(d.name for d in lp_dir.iterdir() if d.is_dir())

    def discover_lessons(
        self, version: str, learning_path: str | None = None
    ) -> list[str]:
        lps = (
            [learning_path]
            if learning_path is not None
            else self.list_learning_paths(version)
        )
        found: list[str] = []
        for lp in lps:
            try:
                lp_dir = self._resolve(version, lp)
            except LessonContentNotFound:
                continue
            if not lp_dir.is_dir():
                continue
            for course_dir in lp_dir.iterdir():
                if not course_dir.is_dir():
                    continue
                for lesson_dir in course_dir.iterdir():
                    if not lesson_dir.is_dir():
                        continue
                    if not (lesson_dir / "index.html").is_file():
                        continue
                    rel = lesson_dir.relative_to(self._root).as_posix()
                    found.append(rel)
        # Local disk has only one variant per lesson, but dedupe anyway so both
        # backends share identical post-conditions.
        return _dedupe_variant_dirs(found)


# ---------------------------------------------------------------------------
# S3-mirror backend
# ---------------------------------------------------------------------------

def _version_sort_key(version: str) -> list[int]:
    try:
        return [int(x) for x in version.split(".")]
    except ValueError:
        return [-1]


# Minimal ListObjectsV2 XML extraction. The bucket returns a flat, predictable
# schema; a namespace-agnostic regex pass is robust and avoids a parser dep.
_KEY_RE = re.compile(r"<Key>(.*?)</Key>", re.DOTALL)
_COMMON_PREFIX_RE = re.compile(
    r"<CommonPrefixes>\s*<Prefix>(.*?)</Prefix>\s*</CommonPrefixes>", re.DOTALL
)
_NEXT_TOKEN_RE = re.compile(
    r"<NextContinuationToken>(.*?)</NextContinuationToken>", re.DOTALL
)
_IS_TRUNCATED_RE = re.compile(r"<IsTruncated>(.*?)</IsTruncated>", re.DOTALL)


def _parse_list_keys(xml: str) -> list[str]:
    """Return the decoded <Key> values from one ListObjectsV2 response page."""
    return [_html.unescape(m) for m in _KEY_RE.findall(xml)]


def _parse_list_prefixes(xml: str) -> list[str]:
    """Return the decoded <CommonPrefixes><Prefix> values from one page."""
    return [_html.unescape(m) for m in _COMMON_PREFIX_RE.findall(xml)]


def _parse_next_token(xml: str) -> str | None:
    """Return the continuation token if the listing is truncated, else None."""
    truncated = _IS_TRUNCATED_RE.search(xml)
    if not (truncated and truncated.group(1).strip().lower() == "true"):
        return None
    m = _NEXT_TOKEN_RE.search(xml)
    return _html.unescape(m.group(1)) if m else None


class S3MirrorSource(ContentSource):
    """Anonymous HTTPS backend over a public S3 mirror of the corpus.

    Reads: ``GET {base_url}/{urlquote(key)}`` (anonymous). Discovery:
    ListObjectsV2 ``GET {base_url}/?list-type=2&prefix=&delimiter=/`` with
    continuation-token pagination, parsing the XML.

    GET responses are cached (in-memory; optionally to ``config.CACHE_ROOT`` for
    HTML/image bytes) so a single run doesn't refetch the same key. Listings are
    cached in-memory for the life of the instance.
    """

    def __init__(
        self,
        base_url: str | None = None,
        *,
        client: httpx.Client | None = None,
        disk_cache: bool = True,
        timeout: float = 30.0,
    ) -> None:
        raw = base_url if base_url is not None else config.CONTENT_S3_BASE_URL
        if not raw:
            raise ValueError(
                "S3MirrorSource requires a base URL. Set CONTENT_S3_BASE_URL "
                "(or CONTENT_SOURCE=local to use the filesystem backend)."
            )
        self._base_url = raw.rstrip("/")
        self._client = client or httpx.Client(timeout=timeout, follow_redirects=True)
        self._owns_client = client is None
        self._lock = threading.Lock()
        self._get_cache: dict[str, bytes] = {}
        self._list_cache: dict[tuple[str, bool], list[str]] = {}
        self._disk_cache = disk_cache
        self._cache_dir = Path(config.CACHE_ROOT) / "content_s3" if disk_cache else None

    # -- low-level HTTP -----------------------------------------------------

    @staticmethod
    def _encode_key(key: str) -> str:
        # Percent-encode each path segment but keep "/" separators intact.
        return urllib.parse.quote(key, safe="/")

    def _disk_cache_path(self, key: str) -> Path | None:
        if self._cache_dir is None:
            return None
        # Mirror the key layout under the cache dir; segments are filesystem-safe
        # except the punctuation variants — quote the leaf to be safe.
        safe = urllib.parse.quote(key, safe="")
        return self._cache_dir / safe

    def _get_bytes(self, key: str) -> bytes:
        """GET an object by key, with in-memory + optional disk caching.

        Raises :class:`LessonContentNotFound` on 404, ``RuntimeError`` on other
        HTTP errors.
        """
        with self._lock:
            if key in self._get_cache:
                return self._get_cache[key]
        disk_path = self._disk_cache_path(key)
        if disk_path is not None and disk_path.is_file():
            data = disk_path.read_bytes()
            with self._lock:
                self._get_cache[key] = data
            return data

        url = f"{self._base_url}/{self._encode_key(key)}"
        resp = self._client.get(url)
        if resp.status_code == 404:
            raise LessonContentNotFound(f"{key}: 404 from mirror")
        if resp.status_code != 200:
            raise RuntimeError(f"HTTP {resp.status_code} GET {key}")
        data = resp.content
        with self._lock:
            self._get_cache[key] = data
        if disk_path is not None:
            try:
                disk_path.parent.mkdir(parents=True, exist_ok=True)
                disk_path.write_bytes(data)
            except OSError:
                pass  # cache is best-effort
        return data

    def _head_ok(self, key: str) -> bool:
        """True if the key exists (cached GET hit, or a HEAD/GET 200)."""
        with self._lock:
            if key in self._get_cache:
                return True
        disk_path = self._disk_cache_path(key)
        if disk_path is not None and disk_path.is_file():
            return True
        url = f"{self._base_url}/{self._encode_key(key)}"
        try:
            resp = self._client.head(url)
        except httpx.HTTPError:
            return False
        # Some S3 setups disallow HEAD; fall back to a ranged GET probe.
        if resp.status_code == 405:
            try:
                resp = self._client.get(url, headers={"Range": "bytes=0-0"})
            except httpx.HTTPError:
                return False
        return resp.status_code in (200, 206)

    def _list(self, prefix: str, *, delimiter: bool) -> list[str]:
        """ListObjectsV2 under ``prefix``.

        With ``delimiter=True`` returns CommonPrefixes (immediate "subfolders",
        each ending in ``/``); with ``delimiter=False`` returns all object Keys
        recursively. Paginated via continuation-token. Cached per (prefix,
        delimiter).
        """
        cache_key = (prefix, delimiter)
        with self._lock:
            if cache_key in self._list_cache:
                return list(self._list_cache[cache_key])

        out: list[str] = []
        token: str | None = None
        while True:
            params = {"list-type": "2", "prefix": prefix}
            if delimiter:
                params["delimiter"] = "/"
            if token:
                params["continuation-token"] = token
            resp = self._client.get(self._base_url, params=params)
            if resp.status_code != 200:
                raise RuntimeError(
                    f"HTTP {resp.status_code} LIST prefix={prefix!r}"
                )
            xml = resp.text
            out.extend(
                _parse_list_prefixes(xml) if delimiter else _parse_list_keys(xml)
            )
            token = _parse_next_token(xml)
            if not token:
                break

        with self._lock:
            self._list_cache[cache_key] = list(out)
        return out

    @staticmethod
    def _strip_images_prefix(filename: str) -> str:
        return filename[len("images/"):] if filename.startswith("images/") else filename

    # -- HTML ---------------------------------------------------------------

    def get_lesson_html(self, lesson_dir: str) -> str:
        key = f"{lesson_dir.strip('/')}/index.html"
        return self._get_bytes(key).decode("utf-8")

    def lesson_html_exists(self, lesson_dir: str) -> bool:
        try:
            self.get_lesson_html(lesson_dir)
            return True
        except LessonContentNotFound:
            return False

    # -- Images -------------------------------------------------------------

    def list_lesson_images(self, lesson_dir: str) -> list[str]:
        prefix = f"{lesson_dir.strip('/')}/images/"
        keys = self._list(prefix, delimiter=False)
        names = [k[len(prefix):] for k in keys if k.startswith(prefix)]
        # images/ is flat in the corpus; ignore any nested keys defensively.
        return sorted(n for n in names if n and "/" not in n)

    def read_image_bytes(self, lesson_dir: str, filename: str) -> bytes:
        filename = self._strip_images_prefix(filename)
        key = f"{lesson_dir.strip('/')}/images/{filename}"
        return self._get_bytes(key)

    def image_exists(self, lesson_dir: str, filename: str) -> bool:
        filename = self._strip_images_prefix(filename)
        key = f"{lesson_dir.strip('/')}/images/{filename}"
        return self._head_ok(key)

    # -- Discovery ----------------------------------------------------------

    def list_versions(self) -> list[str]:
        prefixes = self._list("", delimiter=True)  # e.g. "2025.0/"
        versions = [
            p.rstrip("/") for p in prefixes if _VERSION_FOLDER_RE.match(p.rstrip("/"))
        ]
        return sorted(versions, key=_version_sort_key, reverse=True)

    def list_learning_paths(self, version: str) -> list[str]:
        prefixes = self._list(f"{version}/", delimiter=True)
        return sorted(p.rstrip("/").split("/")[-1] for p in prefixes)

    def list_courses(self, version: str, learning_path: str) -> list[str]:
        prefixes = self._list(f"{version}/{learning_path}/", delimiter=True)
        return sorted(p.rstrip("/").split("/")[-1] for p in prefixes)

    def discover_lessons(
        self, version: str, learning_path: str | None = None
    ) -> list[str]:
        prefix = (
            f"{version}/{learning_path}/"
            if learning_path is not None
            else f"{version}/"
        )
        # One recursive listing, then keep dirs that have an index.html.
        keys = self._list(prefix, delimiter=False)
        lesson_dirs = [
            k[: -len("/index.html")] for k in keys if k.endswith("/index.html")
        ]
        return _dedupe_variant_dirs(lesson_dirs)

    def close(self) -> None:
        if self._owns_client:
            self._client.close()


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

_DEFAULT_SOURCE: ContentSource | None = None
_DEFAULT_SOURCE_LOCK = threading.Lock()


def build_content_source(
    *,
    source: str | None = None,
    content_root: Path | str | None = None,
    base_url: str | None = None,
) -> ContentSource:
    """Construct a fresh ContentSource from config (or explicit overrides).

    ``source`` defaults to ``config.CONTENT_SOURCE`` (``local`` | ``s3mirror``).
    For ``local``, ``content_root`` defaults to ``config.LESSON_CONTENT_ROOT``.
    For ``s3mirror``, ``base_url`` defaults to ``config.CONTENT_S3_BASE_URL``.
    """
    selected = (source or config.CONTENT_SOURCE or "local").strip().lower()
    if selected == "local":
        return LocalFolderSource(content_root)
    if selected == "s3mirror":
        return S3MirrorSource(base_url)
    raise ValueError(
        f"Unknown CONTENT_SOURCE {selected!r}; expected 'local' or 's3mirror'."
    )


def get_content_source() -> ContentSource:
    """Return a process-wide cached ContentSource selected by config.

    Call sites that just need "the configured source" use this. Tests that need
    isolation construct their own via :func:`build_content_source` or
    :func:`reset_content_source` between cases.
    """
    global _DEFAULT_SOURCE
    if _DEFAULT_SOURCE is None:
        with _DEFAULT_SOURCE_LOCK:
            if _DEFAULT_SOURCE is None:
                _DEFAULT_SOURCE = build_content_source()
    return _DEFAULT_SOURCE


def reset_content_source() -> None:
    """Clear the cached default source (tests / config reloads only)."""
    global _DEFAULT_SOURCE
    with _DEFAULT_SOURCE_LOCK:
        _DEFAULT_SOURCE = None


# Re-export the env var names so callers/tests reference one source of truth.
CONTENT_SOURCE_ENV = "CONTENT_SOURCE"
CONTENT_S3_BASE_URL_ENV = "CONTENT_S3_BASE_URL"
