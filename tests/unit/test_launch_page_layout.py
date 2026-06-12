"""Launch page renders full-width, not the 720px reading column (KNOW-2340).

base.html wraps content in ``.site-main`` (default ``max-width: 720px``, sized
for the report/drafts reading view). The index template overrides that for the
launch page only. KNOW-2340 first widened it to a fixed ``1200px``, but on wide
/ ultrawide monitors that still reads as ~1/3 of the viewport while the
full-bleed header spans 100% — the QA finding that kept KNOW-2340 open. The
launch grid should fill the width like the header (``max-width: none``),
bounded only by ``.site-main``'s own side padding.
"""
from __future__ import annotations

from pathlib import Path

_INDEX_HTML = (
    Path(__file__).resolve().parents[2] / "app" / "templates" / "index.html"
).read_text(encoding="utf-8")


def test_launch_page_site_main_is_full_width():
    """The per-page override removes the reading-width cap entirely."""
    assert ".site-main { max-width: none; }" in _INDEX_HTML


def test_launch_page_drops_fixed_1200px_cap():
    """The old fixed 1200px cap read as ~1/3 width on wide monitors (KNOW-2340 QA)."""
    assert "max-width: 1200px" not in _INDEX_HTML
