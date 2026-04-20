"""Unit tests for pipeline/utils.py — all pure functions, no I/O or mocking needed."""

import pytest

from pipeline.utils import (
    lesson_id,
    parse_lesson_path,
    parse_version,
    sort_key_version,
    strip_course_version,
    version_in_range,
)


class TestParseVersion:
    def test_standard_version(self):
        assert parse_version("2025.0") == 2025.0

    def test_minor_version(self):
        assert parse_version("2025.1") == 2025.1

    def test_patch_trimmed(self):
        assert parse_version("2025.2.1") == 2025.2

    def test_build_number_rejected(self):
        # Minor component > 99 is a build number, not a real minor version
        assert parse_version("2025.025058") is None

    def test_none_input(self):
        assert parse_version(None) is None

    def test_empty_string(self):
        assert parse_version("") is None

    def test_garbage_string(self):
        assert parse_version("abc") is None

    def test_single_number(self):
        assert parse_version("2025") is None

    def test_quarterly_release(self):
        assert parse_version("2026.1") == 2026.1

    def test_quarterly_release_q4(self):
        assert parse_version("2026.4") == 2026.4

    def test_non_string_int(self):
        assert parse_version(2025) is None

    def test_leading_trailing_whitespace(self):
        assert parse_version("  2025.0  ") == 2025.0


class TestVersionInRange:
    def test_inclusive_upper_bound(self):
        assert version_in_range(2026.1, 2025.0, 2026.1) is True

    def test_exclusive_lower_bound(self):
        # from_version itself is excluded
        assert version_in_range(2025.0, 2025.0, 2026.1) is False

    def test_midrange(self):
        assert version_in_range(2025.1, 2025.0, 2026.1) is True

    def test_below_range(self):
        assert version_in_range(2024.2, 2025.0, 2026.1) is False

    def test_above_range(self):
        assert version_in_range(2027.0, 2025.0, 2026.1) is False


class TestParseLessonPath:
    def test_valid_path(self):
        path = "2025.0/fme-form-basic/Connect To Data 2025.0/My Lesson/index.html"
        result = parse_lesson_path(path)
        assert result["version_str"] == "2025.0"
        assert result["from_version"] == 2025.0
        assert result["learning_path"] == "fme-form-basic"
        assert result["course"] == "Connect To Data 2025.0"
        assert result["course_canonical"] == "Connect To Data"
        assert result["lesson_name"] == "My Lesson"

    def test_path_too_shallow(self):
        with pytest.raises(ValueError, match="too shallow"):
            parse_lesson_path("2025.0/fme-form-basic/index.html")

    def test_invalid_version_in_path(self):
        with pytest.raises(ValueError, match="Cannot parse version"):
            parse_lesson_path("invalid/fme-form-basic/Course/Lesson/index.html")

    def test_quarterly_version_path(self):
        path = "2026.1/fme-form-basic/Connect To Data 2026.1/Lesson/index.html"
        result = parse_lesson_path(path)
        assert result["from_version"] == 2026.1


class TestStripCourseVersion:
    def test_version_suffix_stripped(self):
        assert strip_course_version("Connect To Data 2025.0") == "Connect To Data"

    def test_multi_word_course(self):
        assert strip_course_version(
            "Build a Library of Custom Transformers 2025.1"
        ) == "Build a Library of Custom Transformers"

    def test_no_version_suffix(self):
        assert strip_course_version("No Version Suffix") == "No Version Suffix"

    def test_empty_string(self):
        assert strip_course_version("") == ""


class TestLessonId:
    def test_format(self):
        lid = lesson_id("2025.0", "fme-form-basic", "Connect To Data", "My Lesson")
        assert lid == "2025.0/fme-form-basic/Connect To Data/My Lesson"

    def test_uses_forward_slashes(self):
        # Must use forward slashes regardless of OS
        lid = lesson_id("2026.1", "lp", "course", "lesson")
        assert "/" in lid
        assert "\\" not in lid


class TestSortKeyVersion:
    def test_valid_version(self):
        assert sort_key_version("2025.0") == 2025.0

    def test_unparseable_returns_negative(self):
        assert sort_key_version("garbage") == -1.0

    def test_empty_returns_negative(self):
        assert sort_key_version("") == -1.0
