"""Regression tests for KNOW-2255 — popup chrome must not leak into saved HTML.

The browser-side fix lives in JavaScript (pipeline/report.py's leRenderLesson
and leGetCleanHtml). These tests cover the server-side belt-and-braces:
serve.py's _sanitize_lesson_html must strip every popup-template descendant
class so an HTML payload that already contains parser-orphaned popup chrome
cannot reach disk or Skilljar.

Plus a couple of static checks on the report.py template confirming the new
KNOW-2255 hooks are present (anchor expansion, dual data-orig attributes).
"""

from __future__ import annotations

from pathlib import Path

from serve import _sanitize_lesson_html


_REPORT_PY = Path("/workspaces/fme-training-automation/pipeline/report.py").read_text()


class TestSanitizeStripsPopupChrome:
    def test_strips_full_nested_popup(self):
        # The well-formed case — popup nested inside the wrap.
        html = (
            '<p>before <span class="tc-wrap" data-id="x" data-state="pending">'
            '<del class="tc-del">Foo</del><ins class="tc-ins"> Bar</ins>'
            '<span class="tc-popup">'
            '<span class="tc-btns">'
            '<button class="tc-accept">Accept</button>'
            '<button class="tc-reject">Reject</button>'
            '</span>'
            '<span class="tc-explanation">why</span>'
            '<span class="tc-issue-links">'
            '<a href="https://x/browse/PROJ-1">PROJ-1</a>'
            '<span class="rec-id">#abc12345</span>'
            '<span class="card-link-wrap">'
            '<a class="card-link" href="?tab=recommendations">card</a>'
            '</span>'
            '</span>'
            '</span></span> after</p>'
        )
        cleaned = _sanitize_lesson_html(html)
        for chrome in (
            "tc-popup", "tc-btns", "tc-explanation", "tc-issue-links",
            "tc-accept", "tc-reject", "card-link", "rec-id",
            "Accept", "Reject", "card", "PROJ-1", "abc12345",
        ):
            assert chrome not in cleaned, f"chrome leaked: {chrome!r} in {cleaned!r}"

    def test_strips_orphaned_popup_descendants(self):
        # The pathological case — parser re-parented the buttons and links
        # OUT of .tc-popup (because a tc-wrap nested inside an <a> in the
        # source HTML). Empty .tc-popup remains plus orphan buttons/links.
        # Real popup-injected Jira links carry style="color:#93c5fd" — that's
        # the existing fingerprint serve.py uses to spot them as chrome.
        html = (
            '<p>looks in the Record Information'
            '<span class="tc-popup"></span>'
            '<a href="https://x/browse/FMEFORM-33652" target="_blank" '
            'rel="noopener" style="color:#93c5fd">FMEFORM-33652</a>'
            '<span class="rec-id">#821e61f7</span>'
            '<span class="card-link-wrap">'
            '<a class="card-link" href="?tab=recommendations&card=R-1">'
            '↗ View recommendation card (FMEFORM-33652)</a>'
            '</span>'
            ' window.</p>'
        )
        cleaned = _sanitize_lesson_html(html)
        # Only the body text should survive.
        assert "looks in the Record Information" in cleaned
        assert "window." in cleaned
        # No popup chrome — including links, chips, buttons.
        for chrome in (
            "FMEFORM-33652", "821e61f7", "View recommendation card",
            "card-link", "rec-id", "tc-popup",
        ):
            assert chrome not in cleaned, f"orphan chrome leaked: {chrome!r}"

    def test_strips_orphaned_buttons_without_tc_btns_parent(self):
        # The tc-btns wrapper is gone but the buttons survived as siblings.
        html = (
            '<p>text'
            '<button class="tc-accept">✓ Accept</button>'
            '<button class="tc-reject">✗ Reject</button>'
            ' more text</p>'
        )
        cleaned = _sanitize_lesson_html(html)
        assert "Accept" not in cleaned
        assert "Reject" not in cleaned
        assert "<button" not in cleaned
        assert "text more text" in cleaned

    def test_keeps_unrelated_links_and_text(self):
        # Sanity: non-chrome content is preserved.
        html = (
            '<p><a href="https://example.com">External link</a> and '
            '<strong>bold</strong> text.</p>'
        )
        cleaned = _sanitize_lesson_html(html)
        assert 'href="https://example.com"' in cleaned
        assert "External link" in cleaned
        assert "<strong>bold</strong>" in cleaned


class TestReportTemplateHasKnow2255Hooks:
    """Static checks on pipeline/report.py — proves the JS-side fix shipped.

    These don't exercise the JS, but they break loudly if a future refactor
    drops the dual-attribute scheme or the anchor-expansion helper.
    """

    def test_findEnclosingAnchor_helper_exists(self):
        assert "function findEnclosingAnchor" in _REPORT_PY

    def test_makeMarkup_helper_exists(self):
        assert "function makeMarkup(ch, origHtml, origText)" in _REPORT_PY

    def test_dual_data_attributes_present(self):
        # Both attributes must be emitted on every wrap variant.
        assert _REPORT_PY.count("data-orig-text=") >= 3, \
            "expected data-orig-text on every wrap variant (delete/add/change)"

    def test_leApplyState_uses_origText_for_visible(self):
        assert "wrap.dataset.origText" in _REPORT_PY

    def test_leGetCleanHtml_strips_orphan_chrome(self):
        # The selector must include the orphan classes added by KNOW-2255.
        assert ".tc-accept" in _REPORT_PY
        assert ".tc-reject" in _REPORT_PY
        assert ".card-link" in _REPORT_PY

    def test_leGetCleanHtml_inserts_html_not_text(self):
        # Switched from createTextNode to insertAdjacentHTML so reject can
        # restore an <a>.
        assert "insertAdjacentHTML('beforebegin', replacement)" in _REPORT_PY
