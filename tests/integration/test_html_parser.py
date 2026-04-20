"""
Integration tests for pipeline/html_parser.py.

Parses the fixture sample_lesson.html and asserts structural extraction.
Requires file I/O but no API calls.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from pipeline.html_parser import parse_lesson_html

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"
SAMPLE_LESSON = FIXTURES_DIR / "sample_lesson.html"


@pytest.fixture
def parsed():
    return parse_lesson_html(SAMPLE_LESSON)


class TestHeadings:
    def test_headings_extracted(self, parsed):
        assert len(parsed["headings"]) > 0

    def test_h2_headings_present(self, parsed):
        h2s = [h for h in parsed["headings"] if h["level"] == 2]
        assert len(h2s) >= 3

    def test_h3_headings_present(self, parsed):
        h3s = [h for h in parsed["headings"] if h["level"] == 3]
        assert len(h3s) >= 1

    def test_heading_text_nonempty(self, parsed):
        for h in parsed["headings"]:
            assert h["text"].strip() != ""


class TestExerciseSteps:
    def test_exercise_steps_extracted(self, parsed):
        assert len(parsed["exercise_steps"]) >= 2

    def test_step_numbers_sequential(self, parsed):
        steps = parsed["exercise_steps"]
        numbers = [s["step_number"] for s in steps]
        assert numbers == sorted(numbers)
        assert numbers[0] == 1

    def test_exercise_step_titles_nonempty(self, parsed):
        for step in parsed["exercise_steps"]:
            assert step["title"].strip() != ""

    def test_resources_heading_not_an_exercise_step(self, parsed):
        step_titles = [s["title"] for s in parsed["exercise_steps"]]
        assert not any("Resources" in t for t in step_titles)


class TestUiStrings:
    def test_ui_strings_extracted(self, parsed):
        assert len(parsed["ui_strings"]) > 0

    def test_run_translation_button_present(self, parsed):
        assert "Run Translation" in parsed["ui_strings"]

    def test_navigator_present(self, parsed):
        assert "Navigator" in parsed["ui_strings"]

    def test_no_empty_strings(self, parsed):
        for s in parsed["ui_strings"]:
            assert s.strip() != ""

    def test_no_duplicates(self, parsed):
        assert len(parsed["ui_strings"]) == len(set(parsed["ui_strings"]))


class TestImages:
    def test_images_extracted(self, parsed):
        assert len(parsed["images"]) > 0

    def test_safe_note_excluded(self, parsed):
        srcs = [img["src"] for img in parsed["images"]]
        assert not any("safe_note.png" in src for src in srcs)

    def test_real_images_have_src(self, parsed):
        for img in parsed["images"]:
            assert img["src"] != ""

    def test_nearby_heading_populated(self, parsed):
        # At least one image should have a nearby_heading
        headings_found = [img.get("nearby_heading") for img in parsed["images"]]
        assert any(h is not None for h in headings_found)


class TestLessonText:
    def test_lesson_text_nonempty(self, parsed):
        assert len(parsed["lesson_text"]) > 0

    def test_lesson_text_contains_content(self, parsed):
        text = parsed["lesson_text"]
        assert "FME" in text or "workspace" in text.lower()

    def test_lesson_text_is_string(self, parsed):
        assert isinstance(parsed["lesson_text"], str)
