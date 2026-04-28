"""Unit tests for serve.py:_sanitize_lesson_html."""

from __future__ import annotations

from serve import _sanitize_lesson_html


class TestEmptyParagraphStripping:
    def test_removes_empty_p_after_image(self):
        # The exact pattern contenteditable produces when pasting an image+enter
        html = '<p><img src="https://example.com/x.png"/></p><p></p>\n<h2>next</h2>'
        cleaned = _sanitize_lesson_html(html)
        assert "<p></p>" not in cleaned
        assert '<img src="https://example.com/x.png"/>' in cleaned
        assert "<h2>next</h2>" in cleaned

    def test_removes_whitespace_only_p(self):
        html = '<p>real</p><p>   </p><p>\n\t</p><p>more</p>'
        cleaned = _sanitize_lesson_html(html)
        # Only the two real paragraphs survive
        assert cleaned.count("<p>") == 2
        assert "<p>real</p>" in cleaned
        assert "<p>more</p>" in cleaned

    def test_keeps_p_with_text(self):
        html = '<p>hello</p>'
        cleaned = _sanitize_lesson_html(html)
        assert "<p>hello</p>" in cleaned

    def test_keeps_p_with_br(self):
        # <p><br></p> is intentional vertical spacing — don't remove it
        html = '<p>before</p><p><br/></p><p>after</p>'
        cleaned = _sanitize_lesson_html(html)
        assert "<p><br/></p>" in cleaned

    def test_keeps_p_with_img_only(self):
        html = '<p><img src="x.png"/></p>'
        cleaned = _sanitize_lesson_html(html)
        assert '<img src="x.png"/>' in cleaned
        assert cleaned.count("<p>") == 1

    def test_existing_track_changes_stripping_still_works(self):
        # Regression: ensure the empty-p pass doesn't break the original sanitizer features.
        html = (
            '<p>text<span class="tc-popup">popup-content</span></p>'
            '<p></p>'
            '<p><a href="?tab=recommendations">jump</a></p>'
        )
        cleaned = _sanitize_lesson_html(html)
        assert "tc-popup" not in cleaned
        assert "popup-content" not in cleaned
        assert "?tab=" not in cleaned
        assert "<p></p>" not in cleaned
        assert "<p>text</p>" in cleaned
