"""
Integration tests for pipeline/manifest.py — Step 1.

Creates a temporary version tree from the sample fixture HTML, then calls
build_manifest() and asserts the output structure. No API calls required.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

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
            lesson_version = float(lesson["version"].replace(".", "", 1).zfill(6))
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
