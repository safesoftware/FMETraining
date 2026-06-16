"""Live tests against the real public S3 content mirror (KNOW-2360).

These hit ``https://safeskilljar.s3.us-west-2.amazonaws.com`` over the network.
Marked ``live_mirror`` so the hermetic suite can deselect them
(``-m 'not live_mirror'``); they also auto-skip when the mirror is unreachable
(offline CI) rather than failing.

Run explicitly with:  pytest -m live_mirror -q
"""
from __future__ import annotations

import httpx
import pytest

from pipeline.content_source import S3MirrorSource

pytestmark = pytest.mark.live_mirror

_BASE = "https://safeskilljar.s3.us-west-2.amazonaws.com"

# A lesson dir verified to exist on the mirror (2025.0, no punctuation variant).
_KNOWN_LESSON = (
    "2025.0/fme-form-basic/Clone of Connect To Data 2025.0/Bring Together Multiple Streams"
)


@pytest.fixture(scope="module")
def live_source():
    src = S3MirrorSource(_BASE, disk_cache=False)
    # Probe reachability; skip the whole module if offline.
    try:
        src.list_versions()
    except (httpx.HTTPError, OSError) as exc:  # pragma: no cover - network dependent
        pytest.skip(f"S3 mirror unreachable: {exc}")
    yield src
    src.close()


def test_live_list_versions(live_source):
    versions = live_source.list_versions()
    assert "2025.0" in versions
    assert "2026.1" in versions
    # Newest-first ordering.
    assert versions == sorted(versions, key=lambda v: [int(x) for x in v.split(".")], reverse=True)


def test_live_get_lesson_html(live_source):
    html = live_source.get_lesson_html(_KNOWN_LESSON)
    assert isinstance(html, str)
    assert len(html) > 100
    assert "<" in html  # real HTML body
    assert live_source.lesson_html_exists(_KNOWN_LESSON) is True


def test_live_discover_lessons_deduped(live_source):
    # A version+LP known to contain punctuation-variant duplicate dirs upstream
    # (2021.0/fme-form-basic). Discovery must collapse them.
    lessons = live_source.discover_lessons("2021.0", "fme-form-basic")
    assert lessons, "expected at least one lesson"
    # No two returned dirs may normalise to the same logical lesson.
    from pipeline.content_source import _normalize_lesson_dir

    norms = [_normalize_lesson_dir(d) for d in lessons]
    assert len(norms) == len(set(norms)), "variant dirs were not deduped"
    # The survivors must be the filesystem-sanitised form (no ':' or '?').
    assert all(":" not in d and "?" not in d for d in lessons)


def test_live_image_read(live_source):
    images = live_source.list_lesson_images(_KNOWN_LESSON)
    assert images, "expected the known lesson to have images"
    data = live_source.read_image_bytes(_KNOWN_LESSON, images[0])
    assert isinstance(data, bytes)
    assert len(data) > 0
    assert live_source.image_exists(_KNOWN_LESSON, images[0]) is True
    assert live_source.image_exists(_KNOWN_LESSON, "definitely-not-real.png") is False
