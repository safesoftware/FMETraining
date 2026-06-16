"""Unit tests for pipeline.enrich_alt_text's content-source migration (KNOW-2360).

These prove that alt-text enrichment reads lesson HTML, probes/reads images, and
discovers lessons through ``pipeline.content_source`` (so it works against the S3
mirror), rather than reaching into the local filesystem directly. The LLM call is
stubbed throughout — only the I/O wiring is under test.
"""
from __future__ import annotations

import asyncio

import pytest

from pipeline import enrich_alt_text as eat
from pipeline.content_source import ContentSource, LessonContentNotFound


# ---------------------------------------------------------------------------
# A spying in-memory ContentSource
# ---------------------------------------------------------------------------

class FakeSource(ContentSource):
    """Backend-agnostic stub that records which resolver methods were hit.

    HTML and images live in plain dicts keyed by lesson_dir, so a test never
    touches the filesystem (this is exactly what the S3 backend buys us).
    """

    def __init__(
        self,
        *,
        html: dict[str, str] | None = None,
        images: dict[str, set[str]] | None = None,
        lessons: dict[tuple[str, str | None], list[str]] | None = None,
    ) -> None:
        self._html = html or {}
        self._images = images or {}
        self._lessons = lessons or {}
        self.calls: list[tuple] = []

    # -- HTML --
    def get_lesson_html(self, lesson_dir: str) -> str:
        self.calls.append(("get_lesson_html", lesson_dir))
        try:
            return self._html[lesson_dir]
        except KeyError:
            raise LessonContentNotFound(lesson_dir) from None

    def lesson_html_exists(self, lesson_dir: str) -> bool:
        self.calls.append(("lesson_html_exists", lesson_dir))
        return lesson_dir in self._html

    # -- Images --
    def list_lesson_images(self, lesson_dir: str) -> list[str]:
        return sorted(self._images.get(lesson_dir, set()))

    def read_image_bytes(self, lesson_dir: str, filename: str) -> bytes:
        filename = filename[len("images/"):] if filename.startswith("images/") else filename
        self.calls.append(("read_image_bytes", lesson_dir, filename))
        if filename not in self._images.get(lesson_dir, set()):
            raise LessonContentNotFound(f"{lesson_dir}/images/{filename}")
        return b"\x89PNG" + filename.encode()

    def image_exists(self, lesson_dir: str, filename: str) -> bool:
        filename = filename[len("images/"):] if filename.startswith("images/") else filename
        self.calls.append(("image_exists", lesson_dir, filename))
        return filename in self._images.get(lesson_dir, set())

    # -- Discovery --
    def list_versions(self) -> list[str]:
        return []

    def discover_lessons(self, version, learning_path=None) -> list[str]:
        self.calls.append(("discover_lessons", version, learning_path))
        return list(self._lessons.get((version, learning_path), []))

    def list_learning_paths(self, version: str) -> list[str]:
        return []

    def list_courses(self, version: str, learning_path: str) -> list[str]:
        return []


@pytest.fixture
def patch_source(monkeypatch):
    """Install a FakeSource as the module's content source and return it."""

    def _install(src: FakeSource) -> FakeSource:
        monkeypatch.setattr(eat, "get_content_source", lambda: src)
        return src

    return _install


# ---------------------------------------------------------------------------
# _src_to_filename — bare-filename normalisation
# ---------------------------------------------------------------------------

def test_src_to_filename_strips_dir_and_query():
    assert eat._src_to_filename("images/foo.png") == "foo.png"
    assert eat._src_to_filename("images/foo.png?v=2") == "foo.png"
    assert eat._src_to_filename("images/sub/bar.gif?cache=123#frag") == "bar.gif"


# ---------------------------------------------------------------------------
# _extract_candidates — reads HTML + probes images via the resolver
# ---------------------------------------------------------------------------

_LD = "2025.0/lp/Course 2025.0/Lesson 1"


def test_extract_candidates_reads_html_and_probes_images_via_resolver(patch_source):
    html = (
        '<img src="images/canvas.png" alt="">'            # absent alt -> candidate
        '<img src="images/long.png" alt="A fully descriptive sentence about this dialog window">'  # good alt -> skip
        '<img src="images/safe_note.png" alt="">'         # decorative -> skip
        '<img src="https://cdn.example/x.png" alt="">'    # non-local -> skip
        '<img src="images/missing.png" alt="image">'      # generic alt but image absent -> skip
    )
    src = patch_source(FakeSource(
        html={_LD: html},
        images={_LD: {"canvas.png", "long.png"}},  # note: missing.png absent
    ))

    cands = eat._extract_candidates(_LD)

    assert [c["src"] for c in cands] == ["images/canvas.png"]
    assert cands[0]["filename"] == "canvas.png"
    assert cands[0]["lesson_dir"] == _LD
    # HTML was read through the resolver, not the filesystem.
    assert ("get_lesson_html", _LD) in src.calls
    # Image existence was probed through the resolver (by bare filename).
    assert ("image_exists", _LD, "canvas.png") in src.calls
    # The absent image was probed and correctly excluded.
    assert ("image_exists", _LD, "missing.png") in src.calls


def test_extract_candidates_strips_query_before_probing(patch_source):
    src = patch_source(FakeSource(
        html={_LD: '<img src="images/shot.png?rev=9" alt="">'},
        images={_LD: {"shot.png"}},
    ))

    cands = eat._extract_candidates(_LD)

    assert len(cands) == 1
    assert cands[0]["filename"] == "shot.png"
    # The bare filename (query stripped) is what gets probed.
    assert ("image_exists", _LD, "shot.png") in src.calls


def test_extract_candidates_missing_html_returns_empty(patch_source):
    src = patch_source(FakeSource(html={}, images={}))
    assert eat._extract_candidates("no/such/lesson") == []
    assert ("get_lesson_html", "no/such/lesson") in src.calls


def test_extract_candidates_dedupes_repeated_src(patch_source):
    html = '<img src="images/dup.png" alt=""><img src="images/dup.png" alt="step">'
    patch_source(FakeSource(html={_LD: html}, images={_LD: {"dup.png"}}))
    cands = eat._extract_candidates(_LD)
    assert [c["src"] for c in cands] == ["images/dup.png"]


# ---------------------------------------------------------------------------
# _enrich_image — reads image bytes via the resolver (LLM stubbed)
# ---------------------------------------------------------------------------

def test_enrich_image_reads_bytes_via_resolver(patch_source, monkeypatch):
    src = patch_source(FakeSource(images={_LD: {"canvas.png"}}))

    captured = {}

    class _FakeMessage:
        content = "Canvas — output table with feature attributes"

    class _FakeChoice:
        message = _FakeMessage()

    class _FakeResp:
        choices = [_FakeChoice()]

    class _FakeCompletions:
        async def create(self, **kwargs):
            captured["url"] = kwargs["messages"][0]["content"][1]["image_url"]["url"]
            return _FakeResp()

    class _FakeChat:
        completions = _FakeCompletions()

    class _FakeClient:
        chat = _FakeChat()

    candidate = {
        "src": "images/canvas.png",
        "original_alt": "",
        "filename": "canvas.png",
        "lesson_dir": _LD,
    }

    async def _go():
        return await eat._enrich_image(_FakeClient(), asyncio.Semaphore(1), candidate)

    result = asyncio.run(_go())

    assert result["src"] == "images/canvas.png"
    assert result["suggested_alt"] == "Canvas — output table with feature attributes"
    # bytes came through the resolver, by bare filename
    assert ("read_image_bytes", _LD, "canvas.png") in src.calls
    # ext was derived from the filename and threaded into the data URL
    assert captured["url"].startswith("data:image/png;base64,")


def test_enrich_image_missing_bytes_returns_none(patch_source):
    patch_source(FakeSource(images={_LD: set()}))  # no bytes for the file
    candidate = {
        "src": "images/gone.png",
        "original_alt": "",
        "filename": "gone.png",
        "lesson_dir": _LD,
    }

    async def _go():
        return await eat._enrich_image(object(), asyncio.Semaphore(1), candidate)

    assert asyncio.run(_go()) is None


# ---------------------------------------------------------------------------
# _run — discovery goes through the resolver (LLM + client stubbed)
# ---------------------------------------------------------------------------

def _stub_openai(monkeypatch):
    """Stop _run from constructing a real OpenAI client / needing a key."""
    monkeypatch.setattr(eat.config, "get_openai_api_key", lambda: "test-key")
    monkeypatch.setattr(eat, "AsyncOpenAI", lambda **kw: object())


def test_run_version_lp_uses_discover_lessons(patch_source, monkeypatch, capsys):
    _stub_openai(monkeypatch)
    lessons = ["2025.0/lp/Course 2025.0/A", "2025.0/lp/Course 2025.0/B"]
    src = patch_source(FakeSource(
        html={ld: "<p>no images</p>" for ld in lessons},
        lessons={("2025.0", "lp"): lessons},
    ))

    eat.main(version="2025.0", learning_path="lp", dry_run=True)

    # Discovery went through the resolver with the version + LP.
    assert ("discover_lessons", "2025.0", "lp") in src.calls
    # Each discovered lesson's HTML was read through the resolver.
    for ld in lessons:
        assert ("get_lesson_html", ld) in src.calls
    out = capsys.readouterr().out
    assert "Scanning 2 lesson HTML files" in out


def test_run_version_lp_no_lessons_errors(patch_source, monkeypatch, capsys):
    _stub_openai(monkeypatch)
    src = patch_source(FakeSource(lessons={}))

    eat.main(version="9999.9", learning_path="nope", dry_run=True)

    assert ("discover_lessons", "9999.9", "nope") in src.calls
    assert "no lessons found" in capsys.readouterr().out


def test_run_run_id_filters_via_lesson_html_exists(patch_source, monkeypatch, tmp_path, capsys):
    _stub_openai(monkeypatch)
    import json

    present = "2025.0/lp/Course 2025.0/Present"
    absent = "2025.0/lp/Course 2025.0/Absent"
    plans = {"lessons": [{"lesson_dir": present}, {"lesson_dir": absent}, {"lesson_dir": ""}]}
    plans_file = tmp_path / "edit_plans.json"
    plans_file.write_text(json.dumps(plans), encoding="utf-8")
    monkeypatch.setattr(eat, "edit_plans_path", lambda run_id: plans_file)

    src = patch_source(FakeSource(html={present: "<p>x</p>"}))

    eat.main(run_id="RUN123", dry_run=True)

    # Existence of each plan lesson is probed through the resolver.
    assert ("lesson_html_exists", present) in src.calls
    assert ("lesson_html_exists", absent) in src.calls
    # Only the present lesson's HTML is then read.
    assert ("get_lesson_html", present) in src.calls
    assert ("get_lesson_html", absent) not in src.calls
    assert "Scanning 1 lesson HTML files" in capsys.readouterr().out
