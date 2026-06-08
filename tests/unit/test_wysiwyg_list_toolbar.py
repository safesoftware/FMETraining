"""Regression tests for KNOW-2275 - bullet / numbered list support in the
Lesson Edits WYSIWYG toolbar.

The feature is browser-side JavaScript living in pipeline/report.py. These
tests cover:

1. The rendered report HTML contains the new toolbar buttons.
2. The rendered report HTML contains the keydown handler with the
   recognizable command and regex signatures (asserts on RENDERED HTML,
   not the Python source — Python f-string escaping has bitten this
   feature before, see test_markdown_ol_regex_present_in_rendered_js).
3. Server-side ``_sanitize_lesson_html`` does not strip <ul>/<ol>/<li>.
   Note: the sanitizer is not an allowlist filter; it only removes
   specific report-UI classes. These tests verify list tags survive,
   not that the sanitizer is broadly safe.
"""

from __future__ import annotations

from pathlib import Path

from pipeline.report import _build_html
from serve import _sanitize_lesson_html


# Source text — used only by tests that assert against the Python source
# itself (e.g., button wiring). Tests of how the JS is actually rendered
# should use _RENDERED_HTML below so f-string escaping bugs surface.
_REPORT_PY = (Path(__file__).resolve().parents[2] / "pipeline" / "report.py").read_text()


def _build_minimal_html() -> str:
    """Build the report HTML with stub arguments. Used by tests that need to
    inspect what the browser actually receives (post-f-string)."""
    return _build_html(
        run_id="test-run",
        json_filename="recommendations-test-run.json",
        model="gpt-4o-mini",
        total_pairs=0,
        completed_pairs=0,
        generated_at="2026-05-05T00:00:00Z",
    )


_RENDERED_HTML = _build_minimal_html()


class TestListToolbarButtons:
    def test_bullet_list_button_present(self):
        assert "leFormatList('ul')" in _REPORT_PY, \
            "expected bullet-list button calling leFormatList('ul')"

    def test_numbered_list_button_present(self):
        assert "leFormatList('ol')" in _REPORT_PY, \
            "expected numbered-list button calling leFormatList('ol')"

    def test_bullet_button_has_keyboard_shortcut_in_title(self):
        # Title attribute documents the Ctrl+Shift+8 shortcut for discoverability.
        assert "Ctrl+Shift+8" in _REPORT_PY

    def test_numbered_button_has_keyboard_shortcut_in_title(self):
        assert "Ctrl+Shift+7" in _REPORT_PY


class TestListKeydownHandler:
    def test_format_list_helper_defined(self):
        assert "function leFormatList(kind)" in _REPORT_PY

    def test_uses_insertUnorderedList_command(self):
        assert "insertUnorderedList" in _REPORT_PY

    def test_uses_insertOrderedList_command(self):
        assert "insertOrderedList" in _REPORT_PY

    def test_tab_indents(self):
        # The keydown handler runs execCommand('indent') / 'outdent' on Tab / Shift+Tab.
        assert "'indent'" in _REPORT_PY
        assert "'outdent'" in _REPORT_PY

    def test_shift_tab_guards_against_top_level_outdent(self):
        # Reviewer-flagged data-loss path: Chrome's execCommand('outdent') on
        # a top-level <li> SILENTLY UNWRAPS it from its <ul>/<ol>, destroying
        # the list. The handler must check that the <li>'s grandparent is
        # itself a list before calling outdent.
        assert "isNested" in _RENDERED_HTML
        # The exact guard: bail if not nested.
        assert "if (!isNested) return" in _RENDERED_HTML

    def test_markdown_ul_regex_present(self):
        # /^[-*]$/ matches a bare hyphen or asterisk before the space.
        # No backslashes here, so the source and the rendered JS agree.
        assert "/^[-*]$/" in _REPORT_PY
        assert "/^[-*]$/" in _RENDERED_HTML

    def test_markdown_ol_regex_present_in_rendered_js(self):
        # /^\d+\.$/ matches "1.", "2.", ... before the space.
        # The Python source doubles the backslashes (\\d, \\.) inside the
        # f-string so Python emits the literal regex unchanged. Asserting
        # on _RENDERED_HTML (the actual string the browser receives) means
        # if anyone ever drops a backslash and breaks the f-string escaping,
        # this test fails — not a vacuous source-string match.
        assert r"/^\d+\.$/" in _RENDERED_HTML

    def test_handler_bound_in_render(self):
        # The handler is rebound on every leRenderLesson() call.
        assert "leHandleListKeydown" in _REPORT_PY
        assert "addEventListener('keydown', leHandleListKeydown)" in _REPORT_PY

    def test_tc_wrap_guard_in_markdown_branch(self):
        # KNOW-2275 review fix: blocks containing track-change spans must be
        # exempt from Markdown auto-conversion so range.deleteContents() can't
        # cross a .tc-wrap and destroy its data-* attributes.
        assert "block.querySelector('.tc-wrap')" in _REPORT_PY

    def test_default_paragraph_separator_is_paragraph(self):
        # KNOW-2275 QA issue 1: toggling a multi-line list OFF must restore the
        # original paragraph spacing. Chrome unwraps <li> into the editor's
        # default paragraph separator, which defaults to <div> (no margin in
        # .lesson-edit-body). Forcing 'p' preserves the inter-paragraph spacing.
        assert "defaultParagraphSeparator" in _RENDERED_HTML
        assert "execCommand('defaultParagraphSeparator', false, 'p')" in _RENDERED_HTML

    def test_markdown_conversion_does_not_use_native_list_command(self):
        # KNOW-2275 QA issue 2: '- ' on an empty line above a paragraph must NOT
        # pull that paragraph into the new list. execCommand('insertUnorderedList')
        # on an empty block makes Chrome absorb the following block, so the
        # Markdown branch builds the single-item list directly and swaps in only
        # that block via replaceChild, leaving the paragraph below in place.
        assert "block.parentNode.replaceChild(listEl, block)" in _RENDERED_HTML
        # The created list carries exactly one empty <li> (a bullet on its own line).
        assert "createElement(kind === 'ol' ? 'ol' : 'ul')" in _RENDERED_HTML


class TestSanitizerPreservesLists:
    """KNOW-2275: <ul>/<ol>/<li> must survive _sanitize_lesson_html unchanged.

    Note on scope: ``_sanitize_lesson_html`` is NOT a tag allowlist. It only
    decomposes specific report-UI classes (``tc-popup``, ``tc-btns``, etc.)
    and strips empty/duplicate paragraphs. These tests confirm the
    list-tag pass-through specifically — they do not (and cannot) assert
    that the sanitizer is broadly safe against arbitrary HTML. If we ever
    need a real allowlist sanitizer, that's a separate ticket.
    """

    def test_unordered_list_passes_through(self):
        html = '<p>before</p><ul><li>x</li><li>y</li></ul><p>after</p>'
        cleaned = _sanitize_lesson_html(html)
        assert "<ul>" in cleaned
        assert "<li>x</li>" in cleaned
        assert "<li>y</li>" in cleaned
        assert "</ul>" in cleaned

    def test_ordered_list_passes_through(self):
        html = '<p>before</p><ol><li>step 1</li><li>step 2</li></ol>'
        cleaned = _sanitize_lesson_html(html)
        assert "<ol>" in cleaned
        assert "<li>step 1</li>" in cleaned
        assert "<li>step 2</li>" in cleaned
        assert "</ol>" in cleaned

    def test_mixed_lists_pass_through(self):
        # Both kinds in the same payload, plus surrounding content.
        html = (
            '<h2>Steps</h2>'
            '<ul><li>x</li></ul>'
            '<ol><li>y</li></ol>'
            '<p>tail</p>'
        )
        cleaned = _sanitize_lesson_html(html)
        assert "<ul><li>x</li></ul>" in cleaned
        assert "<ol><li>y</li></ol>" in cleaned
        assert "<h2>Steps</h2>" in cleaned
        assert "<p>tail</p>" in cleaned

    def test_nested_list_passes_through(self):
        html = '<ul><li>parent<ul><li>child</li></ul></li></ul>'
        cleaned = _sanitize_lesson_html(html)
        # Nested structure preserved; html.parser may add some whitespace but
        # the tag structure is intact.
        assert "<ul>" in cleaned
        assert "parent" in cleaned
        assert "child" in cleaned
        # The inner <ul> survives.
        assert cleaned.count("<ul>") == 2
        assert cleaned.count("<li>") == 2
