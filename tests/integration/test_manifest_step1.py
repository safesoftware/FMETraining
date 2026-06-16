"""
Integration tests for pipeline/manifest.py — Step 1.

Creates a temporary version tree from the sample fixture HTML, then calls
build_manifest() and asserts the output structure. No API calls required.

Also includes a content-source-backed suite (KNOW-2360 / S3-mirror migration)
that drives build_manifest entirely through an in-memory ContentSource, with a
repo_root that does NOT exist on disk — proving no direct filesystem read of
SOURCE content remains in pipeline/manifest.py.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from pipeline.content_source import ContentSource, LessonContentNotFound
from pipeline.manifest import build_manifest


class TestBuildManifestLessonScope:
    def test_lesson_count(self, tmp_version_tree):
        tree = tmp_version_tree
        job = {
            "to_version": "2026.1",
            "scope": {"lessons": [], "courses": [], "learning_paths": [tree["lp"]]},
        }
        manifest = build_manifest(
            run_id="test-run-001",
            job=job,
            repo_root=tree["repo_root"],
            output_dir=tree["repo_root"],
            dry_run=False,
        )
        assert len(manifest["lessons"]) == len(tree["lessons"])

    def test_lesson_id_format(self, tmp_version_tree):
        tree = tmp_version_tree
        job = {
            "to_version": "2026.1",
            "scope": {"lessons": [], "courses": [], "learning_paths": [tree["lp"]]},
        }
        manifest = build_manifest(
            run_id="test-run-002",
            job=job,
            repo_root=tree["repo_root"],
            output_dir=tree["repo_root"],
            dry_run=False,
        )
        for lesson in manifest["lessons"]:
            lid = lesson["lesson_id"]
            parts = lid.split("/")
            assert len(parts) == 4, f"lesson_id should have 4 parts: {lid}"
            assert parts[0] == tree["version"]
            assert parts[1] == tree["lp"]

    def test_lesson_fields_present(self, tmp_version_tree):
        tree = tmp_version_tree
        job = {
            "to_version": "2026.1",
            "scope": {"lessons": [], "courses": [], "learning_paths": [tree["lp"]]},
        }
        manifest = build_manifest(
            run_id="test-run-003",
            job=job,
            repo_root=tree["repo_root"],
            output_dir=tree["repo_root"],
            dry_run=False,
        )
        required_fields = {
            "lesson_id", "path", "version", "learning_path",
            "course", "course_canonical", "lesson_name",
            "headings", "exercise_steps", "ui_strings", "images", "lesson_text",
        }
        for lesson in manifest["lessons"]:
            assert required_fields <= lesson.keys(), (
                f"Missing fields in lesson entry: {required_fields - lesson.keys()}"
            )

    def test_manifest_json_written(self, tmp_version_tree):
        tree = tmp_version_tree
        run_id = "test-run-004"
        job = {
            "to_version": "2026.1",
            "scope": {"lessons": [], "courses": [], "learning_paths": [tree["lp"]]},
        }
        output_dir = tree["repo_root"]
        build_manifest(
            run_id=run_id,
            job=job,
            repo_root=tree["repo_root"],
            output_dir=output_dir,
            dry_run=False,
        )
        manifest_file = output_dir / f"manifest-{run_id}.json"
        assert manifest_file.exists()
        data = json.loads(manifest_file.read_text())
        assert data["run_id"] == run_id

    def test_explicit_lesson_scope(self, tmp_version_tree):
        tree = tmp_version_tree
        job = {
            "to_version": "2026.1",
            "scope": {
                "lessons": [tree["lesson1_path"]],
                "courses": [],
                "learning_paths": [],
            },
        }
        manifest = build_manifest(
            run_id="test-run-005",
            job=job,
            repo_root=tree["repo_root"],
            output_dir=tree["repo_root"],
            dry_run=False,
        )
        # Only the explicitly listed lesson should be resolved
        assert len(manifest["lessons"]) == 1

    def test_dry_run_skips_file_write(self, tmp_version_tree):
        tree = tmp_version_tree
        run_id = "test-run-006"
        job = {
            "to_version": "2026.1",
            "scope": {"lessons": [], "courses": [], "learning_paths": [tree["lp"]]},
        }
        output_dir = tree["repo_root"]
        build_manifest(
            run_id=run_id,
            job=job,
            repo_root=tree["repo_root"],
            output_dir=output_dir,
            dry_run=True,
        )
        manifest_file = output_dir / f"manifest-{run_id}.json"
        assert not manifest_file.exists()

    def test_lesson_from_version_below_to_version(self, tmp_version_tree):
        tree = tmp_version_tree
        job = {
            "to_version": "2026.1",
            "scope": {"lessons": [], "courses": [], "learning_paths": [tree["lp"]]},
        }
        manifest = build_manifest(
            run_id="test-run-007",
            job=job,
            repo_root=tree["repo_root"],
            output_dir=tree["repo_root"],
            dry_run=True,
        )
        for lesson in manifest["lessons"]:
            # Simpler check: version string in lesson should be 2024.2, not 2026.1+
            assert lesson["version"] == tree["version"]

    def test_version_at_or_above_to_version_excluded(self, tmp_version_tree):
        tree = tmp_version_tree
        # Set to_version equal to the lesson version so lessons should be excluded
        job = {
            "to_version": tree["version"],  # 2024.2 == lesson version → excluded
            "scope": {"lessons": [], "courses": [], "learning_paths": [tree["lp"]]},
        }
        manifest = build_manifest(
            run_id="test-run-008",
            job=job,
            repo_root=tree["repo_root"],
            output_dir=tree["repo_root"],
            dry_run=True,
        )
        assert len(manifest["lessons"]) == 0


# ---------------------------------------------------------------------------
# Content-source-backed manifest build (no direct filesystem SOURCE reads)
# ---------------------------------------------------------------------------

_HTML_A = "<h2>1) Open Workspace</h2><p><strong>Reader</strong> step.</p>"
_HTML_B = "<h2>2) Add Reader</h2><p>Read and display the data.</p>"


class InMemorySource(ContentSource):
    """A ContentSource backed entirely by a dict — zero filesystem access.

    Maps ``lesson_dir -> html`` for lessons that have an index.html. Discovery
    methods derive versions / LPs / courses / lessons from those keys, mirroring
    the real backends' post-conditions (sorted, newest-first versions, etc.).
    """

    def __init__(self, lessons: dict[str, str]) -> None:
        self._lessons = dict(lessons)

    # -- HTML ---------------------------------------------------------------
    def get_lesson_html(self, lesson_dir: str) -> str:
        try:
            return self._lessons[lesson_dir]
        except KeyError as e:
            raise LessonContentNotFound(lesson_dir) from e

    def lesson_html_exists(self, lesson_dir: str) -> bool:
        return lesson_dir in self._lessons

    # -- Images (unused by manifest, but the ABC requires them) -------------
    def list_lesson_images(self, lesson_dir: str) -> list[str]:
        return []

    def read_image_bytes(self, lesson_dir: str, filename: str) -> bytes:
        raise LessonContentNotFound(f"{lesson_dir}/images/{filename}")

    def image_exists(self, lesson_dir: str, filename: str) -> bool:
        return False

    # -- Discovery ----------------------------------------------------------
    def list_versions(self) -> list[str]:
        versions = {ld.split("/")[0] for ld in self._lessons}
        return sorted(versions, key=lambda v: [int(x) for x in v.split(".")], reverse=True)

    def discover_lessons(self, version: str, learning_path: str | None = None) -> list[str]:
        prefix = f"{version}/{learning_path}/" if learning_path is not None else f"{version}/"
        return sorted(ld for ld in self._lessons if ld.startswith(prefix))

    def list_learning_paths(self, version: str) -> list[str]:
        lps = {ld.split("/")[1] for ld in self._lessons if ld.startswith(f"{version}/")}
        return sorted(lps)

    def list_courses(self, version: str, learning_path: str) -> list[str]:
        prefix = f"{version}/{learning_path}/"
        courses = {ld.split("/")[2] for ld in self._lessons if ld.startswith(prefix)}
        return sorted(courses)


@pytest.fixture()
def in_memory_corpus(monkeypatch):
    """Inject an InMemorySource into build_manifest and return its lesson map.

    The corpus spans two versions of one course (the older 2024.2 is the most
    recent < to_version=2026.1), a 'Clone of' course (must be skipped), and a
    lesson with no index.html is represented simply by being absent from the
    map. repo_root will be a nonexistent path, so any stray filesystem read of
    SOURCE content would fail the test.
    """
    lp = "fme-form-basic"
    lessons = {
        # Most-recent (< to_version) version of "Connect To Data".
        f"2024.2/{lp}/Connect To Data 2024.2/Exercise_ Connect to a Database": _HTML_A,
        f"2024.2/{lp}/Connect To Data 2024.2/Read and Display Data": _HTML_B,
        # An OLDER version of the same lessons — must be shadowed by 2024.2.
        f"2021.0/{lp}/Connect To Data 2021.0/Exercise_ Connect to a Database": "<h2>old</h2>",
        f"2021.0/{lp}/Connect To Data 2021.0/Read and Display Data": "<h2>old</h2>",
        # A "Clone of" course in the recent version — must be skipped entirely.
        f"2024.2/{lp}/Clone of Connect To Data 2024.2/Exercise_ Connect to a Database": _HTML_A,
    }

    def _fake_source_for(_repo_root):
        return InMemorySource(lessons)

    monkeypatch.setattr("pipeline.manifest._content_source_for", _fake_source_for)
    return {"lp": lp, "lessons": lessons}


class TestBuildManifestViaContentSource:
    """Proves manifest building reads SOURCE content only via the resolver."""

    # A repo_root that does not exist: any direct FS read of source content
    # would raise FileNotFoundError, failing these tests.
    NONEXISTENT_ROOT = Path("/nonexistent-content-root-for-test")

    def test_learning_path_scope_builds_from_source(self, in_memory_corpus, tmp_path):
        lp = in_memory_corpus["lp"]
        job = {
            "to_version": "2026.1",
            "scope": {"lessons": [], "courses": [], "learning_paths": [lp]},
        }
        manifest = build_manifest(
            run_id="cs-run-001",
            job=job,
            repo_root=self.NONEXISTENT_ROOT,
            output_dir=tmp_path,
            dry_run=False,
        )
        # Two distinct lessons; the 'Clone of' course and the older 2021.0
        # duplicates are excluded.
        names = sorted(entry["lesson_name"] for entry in manifest["lessons"])
        assert names == ["Exercise_ Connect to a Database", "Read and Display Data"]
        for lesson in manifest["lessons"]:
            assert lesson["version"] == "2024.2"  # most-recent < to_version wins
            assert lesson["course"] == "Connect To Data 2024.2"
            assert lesson["course_canonical"] == "Connect To Data"
            assert lesson["learning_path"] == lp
            # path keeps the historical .../index.html convention.
            assert lesson["path"].endswith("/index.html")
            # HTML was actually parsed via the resolver (not a disk read).
            assert "headings" in lesson and lesson["headings"]

    def test_course_scope_builds_from_source(self, in_memory_corpus, tmp_path):
        lp = in_memory_corpus["lp"]
        job = {
            "to_version": "2026.1",
            "scope": {
                "lessons": [],
                "courses": [{"learning_path": lp, "course": "Connect To Data"}],
                "learning_paths": [],
            },
        }
        manifest = build_manifest(
            run_id="cs-run-002",
            job=job,
            repo_root=self.NONEXISTENT_ROOT,
            output_dir=tmp_path,
            dry_run=False,
        )
        assert len(manifest["lessons"]) == 2
        assert all(entry["version"] == "2024.2" for entry in manifest["lessons"])

    def test_explicit_lesson_scope_uses_source_existence(self, in_memory_corpus, tmp_path):
        lp = in_memory_corpus["lp"]
        present = f"2024.2/{lp}/Connect To Data 2024.2/Read and Display Data/index.html"
        missing = f"2024.2/{lp}/Connect To Data 2024.2/Does Not Exist/index.html"
        job = {
            "to_version": "2026.1",
            "scope": {"lessons": [present, missing], "courses": [], "learning_paths": []},
        }
        manifest = build_manifest(
            run_id="cs-run-003",
            job=job,
            repo_root=self.NONEXISTENT_ROOT,
            output_dir=tmp_path,
            dry_run=False,
        )
        # Only the lesson the source reports as existing is kept.
        assert len(manifest["lessons"]) == 1
        assert manifest["lessons"][0]["path"] == present
