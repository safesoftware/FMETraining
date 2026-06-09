"""Allowlist HTML sanitizer for report-draft ``body_html``.

Stage-6 security review found a stored cross-user XSS: the WYSIWYG editor's
raw ``innerHTML`` was persisted verbatim by ``report_drafts.upsert_draft`` and
re-rendered into the DOM via ``innerHTML`` on report load, with one shared
draft per ``(run_id, lesson_dir)``. Any ``@safe.com`` user could plant an
event-handler payload (e.g. ``<img onerror=...>``) that executes in another
``@safe.com`` user's authenticated, same-origin session.

This module sanitizes ``body_html`` on the write path. It is an *allowlist*:
only known-safe tags/attributes survive; everything else is stripped. The
allowlist is deliberately broad enough to round-trip the editor's own markup
— headings, lists, links, images (including pasted ``data:image/...`` URIs),
basic emphasis, and the contenteditable track-change ``tc-wrap`` spans — so
sanitizing on save does not corrupt a user's in-progress edits.

Uses BeautifulSoup's ``html.parser`` (no network, no lxml-specific behaviour),
matching the existing ``serve._sanitize_lesson_html`` track-change cleaner.
"""

from __future__ import annotations

from typing import Optional

from bs4 import BeautifulSoup
from bs4.element import Tag

# Tags removed entirely, *including* their text content — they have no place
# in lesson body HTML and are the usual script-execution / data-exfil vectors.
_DROP_WITH_CONTENT = frozenset(
    {
        "script", "style", "iframe", "object", "embed", "applet",
        "link", "meta", "base", "frame", "frameset", "noscript",
        "form", "input", "textarea", "select", "button", "option",
        "svg", "math", "template",
    }
)

# Tags allowed to remain. Anything not here (and not in _DROP_WITH_CONTENT) is
# *unwrapped* — its tag is removed but its text/children are kept.
_ALLOWED_TAGS = frozenset(
    {
        "p", "div", "span", "br", "hr",
        "h1", "h2", "h3", "h4", "h5", "h6",
        "ul", "ol", "li",
        "a", "img",
        "b", "strong", "i", "em", "u", "s", "strike", "sub", "sup",
        "blockquote", "pre", "code",
        "table", "thead", "tbody", "tfoot", "tr", "td", "th", "caption",
    }
)

# Attributes allowed on any tag. ``data-*`` is handled by prefix below.
_GLOBAL_ATTRS = frozenset(
    {"class", "style", "id", "title", "dir", "lang", "contenteditable"}
)

# Extra per-tag attributes.
_TAG_ATTRS = {
    "a": frozenset({"href", "target", "rel"}),
    "img": frozenset({"src", "alt", "width", "height"}),
    "td": frozenset({"colspan", "rowspan"}),
    "th": frozenset({"colspan", "rowspan", "scope"}),
}

# URL schemes permitted in href. (Relative URLs and ``#anchors`` have no
# scheme and are always allowed.)
_SAFE_HREF_SCHEMES = ("http:", "https:", "mailto:", "tel:")


def _normalise_url(value: str) -> str:
    """Lower-cased, control-char-stripped URL for scheme matching.

    Defeats obfuscation like ``Java\\tScript:`` / leading spaces / newlines
    that browsers tolerate but a naive ``startswith`` would miss.
    """
    return "".join(c for c in value if c.isprintable() and not c.isspace()).lower()


def _href_is_safe(value: str) -> bool:
    norm = _normalise_url(value)
    if not norm:
        return False
    if ":" not in norm.split("/", 1)[0]:
        # No scheme before the first path segment → relative URL or #anchor.
        return True
    return norm.startswith(_SAFE_HREF_SCHEMES)


def _img_src_is_safe(value: str) -> bool:
    norm = _normalise_url(value)
    if not norm:
        return False
    if norm.startswith("data:"):
        # Only inline *images* (the editor pastes data:image/...); never
        # data:text/html or other executable payloads.
        return norm.startswith("data:image/")
    if ":" not in norm.split("/", 1)[0]:
        return True
    return norm.startswith(("http:", "https:"))


def _clean_attrs(tag: Tag) -> None:
    allowed = _GLOBAL_ATTRS | _TAG_ATTRS.get(tag.name, frozenset())
    for attr in list(tag.attrs):
        lname = attr.lower()
        # Strip every event handler outright.
        if lname.startswith("on"):
            del tag[attr]
            continue
        if lname.startswith("data-"):
            continue  # editor track-change metadata — keep
        if lname not in allowed:
            del tag[attr]
            continue
        # Scheme-check URL-bearing attributes.
        if tag.name == "a" and lname == "href":
            if not _href_is_safe(str(tag[attr])):
                del tag[attr]
        elif tag.name == "img" and lname == "src":
            if not _img_src_is_safe(str(tag[attr])):
                del tag[attr]


def sanitize_report_html(html: Optional[str]) -> Optional[str]:
    """Return *html* with only allowlisted tags/attributes/URL schemes.

    ``None`` and ``""`` pass through unchanged (a draft with no body).
    """
    if html is None or html == "":
        return html

    soup = BeautifulSoup(html, "html.parser")

    # 1. Remove dangerous elements together with their content.
    for el in soup.find_all(lambda t: t.name in _DROP_WITH_CONTENT):
        el.decompose()

    # 2. Walk the rest. Unwrap non-allowlisted tags (keep their text); scrub
    #    attributes on the survivors. Iterate over a materialised list because
    #    unwrap()/decompose() mutate the tree.
    for el in list(soup.find_all(True)):
        if el.name in _DROP_WITH_CONTENT:
            # A nested one re-parented under a survivor; drop it too.
            el.decompose()
            continue
        if el.name not in _ALLOWED_TAGS:
            el.unwrap()
            continue
        _clean_attrs(el)

    return str(soup)
