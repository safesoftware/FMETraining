"""Unit tests for app.services.html_sanitizer.sanitize_report_html.

Security fix (Stage-6 review): report-draft body_html was stored verbatim
and re-rendered into the DOM via innerHTML, so a @safe.com user could plant
a stored XSS payload that runs in another @safe.com user's authenticated
session. This sanitizer is the server-side write-path defense: it must strip
script/style/iframe, all on* event-handler attributes, and javascript:/
non-image data: URLs, while preserving the legitimate WYSIWYG editor markup
(headings, lists, links, images incl. pasted data:image URIs, and the
track-change `tc-wrap` spans the editor round-trips).
"""

from __future__ import annotations

from app.services.html_sanitizer import sanitize_report_html


class TestStripsDangerousContent:
    def test_strips_script_tag_and_its_content(self):
        out = sanitize_report_html('<p>hi</p><script>alert(1)</script>')
        assert "<script" not in out
        assert "alert(1)" not in out
        assert "hi" in out

    def test_strips_onerror_event_handler_but_keeps_element(self):
        out = sanitize_report_html('<img src="images/a.png" onerror="alert(1)">')
        assert "onerror" not in out
        assert "alert(1)" not in out
        assert "images/a.png" in out  # the element itself survives

    def test_strips_onclick_and_onload_handlers(self):
        out = sanitize_report_html('<div onclick="x()" onload="y()">text</div>')
        assert "onclick" not in out
        assert "onload" not in out
        assert "text" in out

    def test_strips_javascript_scheme_href(self):
        out = sanitize_report_html('<a href="javascript:alert(1)">click</a>')
        assert "javascript:" not in out
        assert "click" in out  # link text preserved, href dropped

    def test_strips_javascript_scheme_obfuscated(self):
        # leading whitespace / mixed case / embedded control char
        out = sanitize_report_html('<a href=" JaVaScript:alert(1)">x</a>')
        assert "javascript" not in out.lower()

    def test_strips_data_text_html_href(self):
        out = sanitize_report_html('<a href="data:text/html,<script>alert(1)</script>">x</a>')
        assert "data:text/html" not in out

    def test_strips_iframe_object_style_tags(self):
        out = sanitize_report_html(
            '<iframe src="evil"></iframe><object data="x"></object>'
            '<style>body{x:1}</style><p>keep</p>'
        )
        assert "<iframe" not in out
        assert "<object" not in out
        assert "<style" not in out
        assert "keep" in out

    def test_unwraps_unknown_tag_keeping_text(self):
        out = sanitize_report_html('<marquee>hello</marquee>')
        assert "<marquee" not in out
        assert "hello" in out

    def test_strips_svg_with_onload(self):
        out = sanitize_report_html('<svg onload="alert(1)"><a>x</a></svg>')
        assert "<svg" not in out
        assert "onload" not in out
        assert "alert(1)" not in out


class TestPreservesLegitimateEditorMarkup:
    def test_allows_headings_lists_links_emphasis(self):
        html = (
            '<h2>Title</h2><p>Intro <strong>bold</strong> <em>it</em></p>'
            '<ul><li>one</li><li>two</li></ul>'
            '<ol><li>a</li></ol>'
            '<p><a href="https://safe.com/docs">link</a></p>'
            '<p>line<br>break</p>'
        )
        out = sanitize_report_html(html)
        for needle in (
            "<h2", "<strong>", "<em>", "<ul>", "<ol>", "<li>", "two",
            'href="https://safe.com/docs"', "<br",
        ):
            assert needle in out, f"missing {needle!r} in sanitized output"

    def test_allows_relative_and_http_image_src(self):
        out = sanitize_report_html('<img src="images/a.png" alt="a">')
        assert 'src="images/a.png"' in out
        assert 'alt="a"' in out

    def test_allows_data_image_src_from_paste(self):
        # The editor inserts pasted/uploaded images as data:image/... URIs.
        uri = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCA',=="
        out = sanitize_report_html(f'<img src="{uri}" alt="">')
        assert "data:image/png;base64," in out

    def test_strips_non_image_data_uri_on_img(self):
        out = sanitize_report_html('<img src="data:text/html,<script>alert(1)</script>">')
        assert "data:text/html" not in out

    def test_preserves_track_change_wrap_span(self):
        html = (
            '<span class="tc-wrap tc-ins" data-change-id="c12" '
            'contenteditable="false">new text</span>'
        )
        out = sanitize_report_html(html)
        assert 'class="tc-wrap tc-ins"' in out
        assert 'data-change-id="c12"' in out
        assert 'contenteditable="false"' in out
        assert "new text" in out


class TestEdgeCases:
    def test_none_returns_none(self):
        assert sanitize_report_html(None) is None

    def test_empty_string_returns_empty(self):
        assert sanitize_report_html("") == ""
