"""
HTML parsing logic for FME training lesson index.html files.

Extracts structured information needed for the lesson manifest:
  - headings (h2, h3, h4)
  - exercise_steps (numbered h2 headings)
  - ui_strings (text from <strong>, <b>, <code> elements)
  - images (src, alt, nearby step/heading context)
"""

from __future__ import annotations

import re
from pathlib import Path

from bs4 import BeautifulSoup, NavigableString, Tag

from pipeline.config import EXERCISE_STEP_PATTERN

# Maximum character length for a ui_string to be considered a label (not prose)
_UI_STRING_MAX_LEN = 120

# Pattern to detect prose sentences: a period followed by space + uppercase letter
_PROSE_SENTENCE_PATTERN = re.compile(r"\.\s+[A-Z]")


def parse_lesson_html(html_path: Path) -> dict:
    """
    Parse a single lesson index.html file and return extracted fields.

    Returns:
        {
            "headings": [...],
            "exercise_steps": [...],
            "ui_strings": [...],
            "images": [...]
        }
    """
    with open(html_path, encoding="utf-8", errors="replace") as f:
        content = f.read()

    soup = BeautifulSoup(content, "lxml")

    headings = _extract_headings(soup)
    exercise_steps = _extract_exercise_steps(headings)
    ui_strings = _extract_ui_strings(soup)
    images = _extract_images(soup, headings)

    return {
        "headings": headings,
        "exercise_steps": exercise_steps,
        "ui_strings": ui_strings,
        "images": images,
    }


def _extract_headings(soup: BeautifulSoup) -> list[dict]:
    """
    Walk all h2, h3, h4 elements in document order.

    Returns a list of {"level": int, "text": str, "id": str | None}.
    """
    headings = []
    for tag in soup.find_all(["h2", "h3", "h4"]):
        level = int(tag.name[1])
        text = tag.get_text(separator=" ", strip=True)
        # Collapse multiple spaces (from inline elements)
        text = re.sub(r"\s+", " ", text).strip()
        heading_id = tag.get("id") or None
        if text:
            headings.append({"level": level, "text": text, "id": heading_id})
    return headings


def _extract_exercise_steps(headings: list[dict]) -> list[dict]:
    """
    Filter headings to those that are level-2 and match the exercise step pattern.

    Pattern: starts with one or more digits followed by ) or .
    E.g. "1) Open Workspace", "2. Add Reader"

    Returns a list of {"step_number": int, "title": str, "id": str | None}.
    """
    steps = []
    for h in headings:
        if h["level"] != 2:
            continue
        m = EXERCISE_STEP_PATTERN.match(h["text"])
        if m:
            steps.append({
                "step_number": int(m.group(1)),
                "title": h["text"],
                "id": h["id"],
            })
    return steps


def _extract_ui_strings(soup: BeautifulSoup) -> list[str]:
    """
    Extract text from <strong>, <b>, and <code> elements as potential UI labels.

    Filtering rules:
      - Skip empty strings
      - Skip strings longer than _UI_STRING_MAX_LEN characters
      - Skip strings that look like prose sentences (period + space + uppercase)
      - Skip the literal "Note" (from note icon alt text)
    Deduplicate while preserving first-occurrence order.
    """
    seen: set[str] = set()
    results: list[str] = []

    for tag in soup.find_all(["strong", "b", "code"]):
        text = tag.get_text(separator=" ", strip=True)
        text = re.sub(r"\s+", " ", text).strip()

        if not text:
            continue
        if len(text) > _UI_STRING_MAX_LEN:
            continue
        if text.lower() == "note":
            continue
        if _PROSE_SENTENCE_PATTERN.search(text):
            continue
        if text not in seen:
            seen.add(text)
            results.append(text)

    return results


def _extract_images(soup: BeautifulSoup, headings: list[dict]) -> list[dict]:
    """
    Extract all <img> elements with context about their surrounding heading.

    For each image, record:
      - src: the src attribute (relative path or URL)
      - alt: the alt attribute
      - nearby_step: step_number of the nearest preceding h2 exercise step (or None)
      - nearby_heading: text of the nearest preceding h2 heading (or None)

    Strategy: walk all tags in document order; maintain running state for the
    last-seen h2 heading and last-seen exercise step number.
    """
    # Build a quick lookup: heading text → step_number for exercise steps
    step_by_heading: dict[str, int] = {}
    for tag in soup.find_all("h2"):
        text = re.sub(r"\s+", " ", tag.get_text(separator=" ", strip=True)).strip()
        m = EXERCISE_STEP_PATTERN.match(text)
        if m:
            step_by_heading[text] = int(m.group(1))

    images = []
    last_h2_text: str | None = None
    last_step_number: int | None = None

    for tag in soup.descendants:
        if not isinstance(tag, Tag):
            continue

        if tag.name == "h2":
            text = re.sub(r"\s+", " ", tag.get_text(separator=" ", strip=True)).strip()
            if text:
                last_h2_text = text
                last_step_number = step_by_heading.get(text)

        elif tag.name == "img":
            src = tag.get("src", "")
            alt = tag.get("alt", "")

            # Skip decorative/icon images that are tiny or have no real src
            if not src or src.endswith("safe_note.png"):
                continue

            images.append({
                "src": src,
                "alt": alt,
                "nearby_step": last_step_number,
                "nearby_heading": last_h2_text,
            })

    return images
