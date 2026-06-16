"""Hermetic tests for pipeline.content_source (KNOW-2360).

Covers:
- LocalFolderSource over a tmp tree (HTML read/exists, image list/read, escape
  guard, discovery + version/LP/course listing).
- The variant-dedupe rule directly.
- S3MirrorSource XML parsing, pagination, GET caching, key encoding, and
  discovery dedupe — all with a mocked httpx transport (no network).
- The config-driven factory.
"""
from __future__ import annotations

import httpx
import pytest

from pipeline import content_source as cs
from pipeline.content_source import (
    LessonContentNotFound,
    LocalFolderSource,
    S3MirrorSource,
    _dedupe_variant_dirs,
    _normalize_lesson_dir,
    build_content_source,
)


# ---------------------------------------------------------------------------
# Variant dedupe rule
# ---------------------------------------------------------------------------

def test_normalize_collapses_punctuation() -> None:
    a = "2021.0/lp/Course 2021.0/Exercise. Foo"
    b = "2021.0/lp/Course 2021.0/Exercise: Foo"
    c = "2021.0/lp/Course 2021.0/Exercise_ Foo"
    assert _normalize_lesson_dir(a) == _normalize_lesson_dir(b) == _normalize_lesson_dir(c)


def test_dedupe_prefers_filesystem_sanitised_variant() -> None:
    dirs = [
        "v/lp/c/Exercise: Foo",   # colon — illegal on disk
        "v/lp/c/Exercise_ Foo",   # underscore — the local/sanitised form
        "v/lp/c/Exercise. Foo",   # trailing-dot segment — awkward on disk
    ]
    out = _dedupe_variant_dirs(dirs)
    assert out == ["v/lp/c/Exercise_ Foo"]


def test_dedupe_trailing_question_mark_loses_to_underscore() -> None:
    dirs = [
        "v/lp/c/What Are List Attributes?",
        "v/lp/c/What Are List Attributes_",
        "v/lp/c/What Are List Attributes.",
    ]
    out = _dedupe_variant_dirs(dirs)
    assert out == ["v/lp/c/What Are List Attributes_"]


def test_dedupe_keeps_distinct_lessons() -> None:
    dirs = ["v/lp/c/Alpha", "v/lp/c/Beta"]
    assert _dedupe_variant_dirs(dirs) == ["v/lp/c/Alpha", "v/lp/c/Beta"]


# ---------------------------------------------------------------------------
# LocalFolderSource
# ---------------------------------------------------------------------------

@pytest.fixture()
def local_tree(tmp_path):
    """Build 2025.0/lp1/Course A 2025.0/Lesson 1 with html + two images."""
    lesson = tmp_path / "2025.0" / "lp1" / "Course A 2025.0" / "Lesson 1"
    (lesson / "images").mkdir(parents=True)
    (lesson / "index.html").write_text("<p>hello</p>", encoding="utf-8")
    (lesson / "images" / "a.png").write_bytes(b"\x89PNGdata")
    (lesson / "images" / "b.gif").write_bytes(b"GIF89a")
    # A second lesson with no index.html (must be skipped by discovery).
    (tmp_path / "2025.0" / "lp1" / "Course A 2025.0" / "NoIndex").mkdir()
    # A second version folder + a non-version dir.
    (tmp_path / "2026.1" / "lp2" / "Course B 2026.1" / "L").mkdir(parents=True)
    (tmp_path / "2026.1" / "lp2" / "Course B 2026.1" / "L" / "index.html").write_text(
        "<p>v2</p>", encoding="utf-8"
    )
    (tmp_path / "artifacts").mkdir()
    return tmp_path


def test_local_get_html_and_exists(local_tree):
    src = LocalFolderSource(local_tree)
    ld = "2025.0/lp1/Course A 2025.0/Lesson 1"
    assert src.get_lesson_html(ld) == "<p>hello</p>"
    assert src.lesson_html_exists(ld) is True
    assert src.lesson_html_exists("2025.0/lp1/Course A 2025.0/NoIndex") is False


def test_local_get_html_missing_raises(local_tree):
    src = LocalFolderSource(local_tree)
    with pytest.raises(LessonContentNotFound):
        src.get_lesson_html("2025.0/lp1/Course A 2025.0/Nope")


def test_local_images(local_tree):
    src = LocalFolderSource(local_tree)
    ld = "2025.0/lp1/Course A 2025.0/Lesson 1"
    assert src.list_lesson_images(ld) == ["a.png", "b.gif"]
    assert src.read_image_bytes(ld, "a.png") == b"\x89PNGdata"
    # tolerate an images/ prefix on the filename
    assert src.read_image_bytes(ld, "images/b.gif") == b"GIF89a"
    assert src.image_exists(ld, "a.png") is True
    assert src.image_exists(ld, "missing.png") is False
    with pytest.raises(LessonContentNotFound):
        src.read_image_bytes(ld, "missing.png")


def test_local_images_empty_when_no_dir(local_tree):
    src = LocalFolderSource(local_tree)
    assert src.list_lesson_images("2026.1/lp2/Course B 2026.1/L") == []


def test_local_discovery_and_listing(local_tree):
    src = LocalFolderSource(local_tree)
    assert src.list_versions() == ["2026.1", "2025.0"]
    assert src.list_learning_paths("2025.0") == ["lp1"]
    assert src.list_courses("2025.0", "lp1") == ["Course A 2025.0"]
    assert src.discover_lessons("2025.0") == ["2025.0/lp1/Course A 2025.0/Lesson 1"]
    assert src.discover_lessons("2025.0", "lp1") == [
        "2025.0/lp1/Course A 2025.0/Lesson 1"
    ]
    # NoIndex (no index.html) excluded.
    assert "NoIndex" not in " ".join(src.discover_lessons("2025.0"))


def test_local_escape_guard(local_tree):
    src = LocalFolderSource(local_tree)
    assert src.lesson_html_exists("../../etc/passwd") is False
    with pytest.raises(LessonContentNotFound):
        src.get_lesson_html("../../../etc/passwd")


# ---------------------------------------------------------------------------
# S3MirrorSource (mocked transport)
# ---------------------------------------------------------------------------

# Two LP keys, a course with 3 punctuation-variant lessons (each with index.html
# + one image), to exercise discovery dedupe + reads.
_LESSON_BASE = "2021.0/fme-form-basic/Lists 2021.0"
_VARIANTS = ["Exercise. Foo", "Exercise: Foo", "Exercise_ Foo"]
_OBJECT_KEYS = []
for _v in _VARIANTS:
    _OBJECT_KEYS.append(f"{_LESSON_BASE}/{_v}/index.html")
    _OBJECT_KEYS.append(f"{_LESSON_BASE}/{_v}/images/pic.png")

_HTML_BODY = "<h2>Exercise Foo</h2>"
_IMG_BODY = b"\x89PNG-mock-image"


def _xml_list_keys(keys, *, truncated=False, token=""):
    contents = "".join(
        f"<Contents><Key>{k}</Key><Size>1</Size></Contents>" for k in keys
    )
    trunc = "true" if truncated else "false"
    tok = f"<NextContinuationToken>{token}</NextContinuationToken>" if truncated else ""
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        f"<ListBucketResult><IsTruncated>{trunc}</IsTruncated>{tok}{contents}"
        "</ListBucketResult>"
    )


def _xml_list_prefixes(prefixes):
    cps = "".join(f"<CommonPrefixes><Prefix>{p}</Prefix></CommonPrefixes>" for p in prefixes)
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        f"<ListBucketResult><IsTruncated>false</IsTruncated>{cps}</ListBucketResult>"
    )


def _make_mock_client() -> httpx.Client:
    """An httpx.Client whose transport answers list + GET requests from memory.

    Drives one pagination boundary: the first recursive listing page is
    truncated and returns half the keys, the second returns the rest.
    """
    recursive_pages = {
        None: _xml_list_keys(_OBJECT_KEYS[:3], truncated=True, token="PAGE2"),
        "PAGE2": _xml_list_keys(_OBJECT_KEYS[3:], truncated=False),
    }

    def handler(request: httpx.Request) -> httpx.Response:
        params = dict(request.url.params)
        if params.get("list-type") == "2":
            prefix = params.get("prefix", "")
            if params.get("delimiter") == "/":
                # CommonPrefixes listing — answer version + lp + course levels.
                if prefix == "":
                    return httpx.Response(200, text=_xml_list_prefixes(["2021.0/"]))
                if prefix == "2021.0/":
                    return httpx.Response(
                        200, text=_xml_list_prefixes(["2021.0/fme-form-basic/"])
                    )
                if prefix == "2021.0/fme-form-basic/":
                    return httpx.Response(
                        200,
                        text=_xml_list_prefixes([f"{_LESSON_BASE}/"]),
                    )
                return httpx.Response(200, text=_xml_list_prefixes([]))
            # Recursive (no delimiter) — paginated.
            token = params.get("continuation-token")
            page = recursive_pages.get(token, _xml_list_keys([]))
            return httpx.Response(200, text=page)
        # Object GET — decode the key from the path.
        key = httpx.URL(str(request.url)).path.lstrip("/")
        import urllib.parse

        key = urllib.parse.unquote(key)
        if key.endswith("/index.html"):
            return httpx.Response(200, text=_HTML_BODY)
        if key.endswith("/images/pic.png"):
            return httpx.Response(200, content=_IMG_BODY)
        return httpx.Response(404, text="not found")

    return httpx.Client(transport=httpx.MockTransport(handler))


def test_s3_requires_base_url():
    with pytest.raises(ValueError):
        S3MirrorSource("")


def test_s3_get_html_and_caching():
    client = _make_mock_client()
    src = S3MirrorSource("https://mirror.example", client=client, disk_cache=False)
    ld = f"{_LESSON_BASE}/Exercise_ Foo"
    assert src.get_lesson_html(ld) == _HTML_BODY
    assert src.lesson_html_exists(ld) is True
    # Cached: a second read must not re-hit the (now-closed) transport.
    client.close()
    assert src.get_lesson_html(ld) == _HTML_BODY


def test_s3_key_encoding_for_spaces_and_punctuation():
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["raw_path"] = str(request.url).split("mirror.example", 1)[1]
        return httpx.Response(200, text=_HTML_BODY)

    client = httpx.Client(transport=httpx.MockTransport(handler))
    src = S3MirrorSource("https://mirror.example", client=client, disk_cache=False)
    src.get_lesson_html("2021.0/lp/Course 2021.0/Exercise: Foo")
    # Spaces and ':' must be percent-encoded, '/' separators preserved.
    assert "%20" in captured["raw_path"]
    assert "%3A" in captured["raw_path"]
    assert "/2021.0/lp/" in captured["raw_path"]


def test_s3_read_image_bytes():
    src = S3MirrorSource("https://mirror.example", client=_make_mock_client(), disk_cache=False)
    ld = f"{_LESSON_BASE}/Exercise_ Foo"
    assert src.read_image_bytes(ld, "pic.png") == _IMG_BODY
    assert src.read_image_bytes(ld, "images/pic.png") == _IMG_BODY


def test_s3_list_images():
    src = S3MirrorSource("https://mirror.example", client=_make_mock_client(), disk_cache=False)
    ld = f"{_LESSON_BASE}/Exercise_ Foo"
    assert src.list_lesson_images(ld) == ["pic.png"]


def test_s3_discovery_dedupes_variants_with_pagination():
    src = S3MirrorSource("https://mirror.example", client=_make_mock_client(), disk_cache=False)
    found = src.discover_lessons("2021.0")
    # 3 variants collapse to the single sanitised form.
    assert found == [f"{_LESSON_BASE}/Exercise_ Foo"]


def test_s3_list_versions_and_lps_and_courses():
    src = S3MirrorSource("https://mirror.example", client=_make_mock_client(), disk_cache=False)
    assert src.list_versions() == ["2021.0"]
    assert src.list_learning_paths("2021.0") == ["fme-form-basic"]
    assert src.list_courses("2021.0", "fme-form-basic") == ["Lists 2021.0"]


def test_s3_get_html_404_raises():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, text="nope")

    client = httpx.Client(transport=httpx.MockTransport(handler))
    src = S3MirrorSource("https://mirror.example", client=client, disk_cache=False)
    with pytest.raises(LessonContentNotFound):
        src.get_lesson_html("x/y/z/L")
    assert src.lesson_html_exists("x/y/z/L") is False


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

def test_factory_default_is_local(monkeypatch):
    monkeypatch.setattr(cs.config, "CONTENT_SOURCE", "local")
    src = build_content_source()
    assert isinstance(src, LocalFolderSource)


def test_factory_s3_selection(monkeypatch):
    monkeypatch.setattr(cs.config, "CONTENT_SOURCE", "s3mirror")
    monkeypatch.setattr(cs.config, "CONTENT_S3_BASE_URL", "https://mirror.example")
    src = build_content_source()
    assert isinstance(src, S3MirrorSource)


def test_factory_explicit_override_wins(monkeypatch):
    monkeypatch.setattr(cs.config, "CONTENT_SOURCE", "s3mirror")
    src = build_content_source(source="local")
    assert isinstance(src, LocalFolderSource)


def test_factory_unknown_raises():
    with pytest.raises(ValueError):
        build_content_source(source="bogus")
