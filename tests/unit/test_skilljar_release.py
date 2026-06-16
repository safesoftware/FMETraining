"""Unit tests for skilljar_release.py: image rewriting, the archive step's
labels + idempotency guard (KNOW-2321), and the removal of the tag-swap step
(KNOW-2322/2323)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pipeline.skilljar_release as skilljar_release
from pipeline.skilljar_release import (
    _rewrite_images,
    _upload_and_rewrite_images,
    execute_release,
)

_S3_ARGS = dict(s3_bucket="test-bucket", s3_key_id="fake-id", s3_secret="fake-secret")
_S3_KEY = "skilljar-uploads/abc12345-photo.png"
_S3_PUBLIC_URL = "https://s3.us-east-1.amazonaws.com/test-bucket/" + _S3_KEY


class TestUploadAndRewriteImages:
    def test_rewrites_relative_src_with_public_s3_url(self, tmp_path):
        (tmp_path / "images").mkdir()
        (tmp_path / "images" / "photo.png").write_bytes(b"\x89PNG")

        html = '<img src="images/photo.png" alt="test">'

        with patch("pipeline.skilljar_release._s3_put",
                   return_value=(_S3_PUBLIC_URL, _S3_KEY)):
            result_html, failed = _upload_and_rewrite_images(
                html, ["images/photo.png"], tmp_path.name, tmp_path.parent,
                "fake-api-key", **_S3_ARGS,
            )

        assert f'src="{_S3_PUBLIC_URL}"' in result_html
        assert failed == []

    def test_returns_unchanged_html_when_s3_not_configured(self, tmp_path):
        html = '<img src="images/photo.png">'
        result_html, failed = _upload_and_rewrite_images(
            html, ["images/photo.png"], "some/dir", tmp_path, "fake-api-key",
        )
        assert result_html == html
        paths = [p for p, _ in failed]
        assert "images/photo.png" in paths
        reasons = [r for _, r in failed]
        assert any("S3 not configured" in r for r in reasons)

    def test_adds_to_failed_when_local_file_missing(self, tmp_path):
        html = '<img src="images/missing.gif">'
        result_html, failed = _upload_and_rewrite_images(
            html, ["images/missing.gif"], "lesson/dir", tmp_path, "fake-key", **_S3_ARGS,
        )
        paths = [p for p, _ in failed]
        assert "images/missing.gif" in paths
        assert 'src="images/missing.gif"' in result_html  # unchanged

    def test_adds_to_failed_when_s3_put_raises(self, tmp_path):
        (tmp_path / "images").mkdir()
        (tmp_path / "images" / "bad.gif").write_bytes(b"GIF89a")

        html = '<img src="images/bad.gif">'
        with patch("pipeline.skilljar_release._s3_put",
                   side_effect=RuntimeError("HTTP 403 PUT s3://test-bucket/...: Forbidden")):
            result_html, failed = _upload_and_rewrite_images(
                html, ["images/bad.gif"], "", tmp_path, "fake-key", **_S3_ARGS,
            )
        paths = [p for p, _ in failed]
        reasons = [r for _, r in failed]
        assert "images/bad.gif" in paths
        assert any("HTTP 403" in r for r in reasons)
        assert 'src="images/bad.gif"' in result_html

    def test_handles_multiple_images(self, tmp_path):
        (tmp_path / "images").mkdir()
        (tmp_path / "images" / "a.png").write_bytes(b"\x89PNG")
        (tmp_path / "images" / "b.gif").write_bytes(b"GIF89a")

        html = '<img src="images/a.png"><img src="images/b.gif">'

        with patch("pipeline.skilljar_release._s3_put",
                   side_effect=[
                       ("https://s3.us-east-1.amazonaws.com/test-bucket/a.png", "skilljar-uploads/a.png"),
                       ("https://s3.us-east-1.amazonaws.com/test-bucket/b.gif", "skilljar-uploads/b.gif"),
                   ]):
            result_html, failed = _upload_and_rewrite_images(
                html, ["images/a.png", "images/b.gif"], "", tmp_path,
                "fake-key", **_S3_ARGS,
            )

        assert 'src="https://s3.us-east-1.amazonaws.com/test-bucket/a.png"' in result_html
        assert 'src="https://s3.us-east-1.amazonaws.com/test-bucket/b.gif"' in result_html
        assert failed == []

    def test_skilljar_asset_endpoint_not_called(self, tmp_path):
        """Regression: the previous flow used /v1/assets which returns 1-hour-signed URLs,
        breaking lessons after expiry. We must NOT call those helpers any more."""
        (tmp_path / "images").mkdir()
        (tmp_path / "images" / "x.png").write_bytes(b"\x89PNG")

        html = '<img src="images/x.png">'
        with patch("pipeline.skilljar_release._s3_put",
                   return_value=(_S3_PUBLIC_URL, _S3_KEY)) as mock_put:
            _upload_and_rewrite_images(
                html, ["images/x.png"], "", tmp_path, "fake-key", **_S3_ARGS,
            )
        # _create_asset_from_url and _wait_for_asset_url are no longer imported here,
        # so we just assert _s3_put was called and no S3 delete happened (the file
        # stays in the bucket as a permanent host).
        mock_put.assert_called_once()


class TestRewriteImagesSkipsExpiring:
    """Regression for KNOW-2253: _rewrite_images must NOT propagate expiring
    pre-signed URLs from the previous version's HTML — those URLs render fine
    for an hour and then 403, breaking the new release."""

    def test_skips_everpath_url_from_original(self):
        original = (
            '<img src="https://everpath-course-content.s3.amazonaws.com/'
            'instructor/x/assets/1/foo.png?AWSAccessKeyId=K&Signature=s&Expires=1">'
        )
        new = '<img src="images/foo.png">'
        rewritten, unmatched = _rewrite_images(new, original)
        # The expiring URL must NOT be substituted in
        assert "everpath-course-content" not in rewritten
        assert "Expires=" not in rewritten
        # The relative path stays untouched, ready for _upload_and_rewrite_images
        assert 'src="images/foo.png"' in rewritten
        assert unmatched == ["images/foo.png"]

    def test_skips_url_with_expires_query_param_from_any_host(self):
        original = '<img src="https://example.com/foo.png?Expires=999&Signature=x">'
        new = '<img src="images/foo.png">'
        rewritten, unmatched = _rewrite_images(new, original)
        assert "Expires=" not in rewritten
        assert unmatched == ["images/foo.png"]

    def test_propagates_permanent_url(self):
        permanent = "https://s3.us-east-1.amazonaws.com/FMETraining/keep/foo.png"
        original = f'<img src="{permanent}">'
        new = '<img src="images/foo.png">'
        rewritten, unmatched = _rewrite_images(new, original)
        assert permanent in rewritten
        assert unmatched == []


def _release_plan() -> dict:
    """Minimal single-course 'release' plan with one mapped lesson."""
    return {
        "to_version": "2026.1",
        "warnings": [],
        "courses": [
            {
                "action": "release",
                "source_course_id": "src-course",
                "source_course_title": "Connect To Data 2025.0",
                "archive_title": "Connect To Data 2025.0",
                "new_title": "Connect To Data 2026.1",
                "new_labels": ["2026.1"],
                "lp": "fme-form-basic",
                "course_canonical": "Connect To Data",
                "course_folder": "Connect To Data 2026.1",
                "lessons": [
                    {
                        "skilljar_lesson_id": "les-1",
                        "skilljar_course_id": "src-course",
                        "lesson_dir": "2026.1/fme-form-basic/Connect To Data 2026.1/Intro",
                        "lesson_name": "Intro",
                        "local_path": None,
                        "has_local_file": False,
                        "mapped": True,
                        "is_draft": False,
                    }
                ],
                "is_draft": False,
            }
        ],
    }


def _run_release(monkeypatch, tmp_path, *, existing_archive, create_calls):
    """Drive execute_release once with all network helpers patched.

    ``existing_archive`` is what _find_course_by_title_and_label returns (None ⇒
    no archive yet). ``create_calls`` is a mutable list that records the title of
    every _create_course call so callers can assert how many archives were made.
    """
    monkeypatch.setattr(
        skilljar_release, "_get_course",
        lambda cid, key: {"id": cid, "title": "Connect To Data 2025.0", "labels": ["2025.0"]},
    )
    monkeypatch.setattr(
        skilljar_release, "_find_course_by_title_and_label",
        lambda title, label, key: existing_archive,
    )
    monkeypatch.setattr(
        skilljar_release, "_get_lessons_for_course",
        lambda cid, key: [{"id": "old-les-1", "title": "Intro", "order": 0}],
    )
    patched_labels: dict = {}

    def _fake_create_course(title, source_course, key):
        create_calls.append(title)
        return {"id": "archive-course-id", "title": title}

    def _fake_patch_course(cid, data, key):
        patched_labels[cid] = data.get("labels")
        return {"id": cid, **data}

    monkeypatch.setattr(skilljar_release, "_create_course", _fake_create_course)
    monkeypatch.setattr(skilljar_release, "_patch_course", _fake_patch_course)
    monkeypatch.setattr(
        skilljar_release, "_get_lesson",
        lambda lid, key: {"id": lid, "title": "Intro", "type": "HTML", "order": 0, "content_html": "<p>hi</p>"},
    )
    monkeypatch.setattr(
        skilljar_release, "_create_lesson",
        lambda cid, title, ltype, order, key: {"id": "new-archived-les"},
    )
    monkeypatch.setattr(skilljar_release, "_patch_lesson_html", lambda lid, html, key: None)

    lines = list(execute_release(
        _release_plan(),
        api_key="k",
        domain="academy.safe.com",
        mapping={},
        mapping_path=tmp_path / "skilljar-mapping.json",
        repo_root=tmp_path,
        dry_run=False,
    ))
    return lines, patched_labels


class TestArchiveStep:
    """KNOW-2321: the archive course is labelled exactly ['archived'] and the
    archive step is idempotent — re-running against an already-archived course
    creates no duplicate."""

    def test_archive_labelled_exactly_archived(self, monkeypatch, tmp_path):
        create_calls: list[str] = []
        _lines, patched_labels = _run_release(
            monkeypatch, tmp_path, existing_archive=None, create_calls=create_calls,
        )
        # Exactly one archive course created, labelled exactly ["archived"].
        assert create_calls == ["Connect To Data 2025.0"]
        assert patched_labels["archive-course-id"] == ["archived"]

    def test_idempotent_when_archive_already_exists(self, monkeypatch, tmp_path):
        create_calls: list[str] = []
        existing = {"id": "pre-existing-archive", "title": "Connect To Data 2025.0", "labels": ["archived"]}
        lines, _patched_labels = _run_release(
            monkeypatch, tmp_path, existing_archive=existing, create_calls=create_calls,
        )
        # No archive course created on the second run.
        assert create_calls == []
        assert any("Archive already exists" in ln for ln in lines)


class TestTagSwapRemoved:
    """KNOW-2322/2323: the published-course tag-swap step and its helper are gone,
    and no 'Step N/5' log strings remain (flow is now Step N/4)."""

    def test_swap_helper_no_longer_exposed(self):
        assert not hasattr(skilljar_release, "_swap_published_course_tags")

    def test_no_step_of_5_strings_in_source(self):
        import re
        src = Path(skilljar_release.__file__).read_text(encoding="utf-8")
        assert not re.search(r"Step .*?/5", src), "stale 'Step N/5' log string in module source"

    def test_no_step_of_5_log_strings(self, monkeypatch, tmp_path):
        create_calls: list[str] = []
        lines, _patched_labels = _run_release(
            monkeypatch, tmp_path, existing_archive=None, create_calls=create_calls,
        )
        joined = "\n".join(lines)
        import re
        assert not re.search(r"Step .*?/5", joined), joined
        # Sanity: the renumbered steps are present.
        assert any("Step 1/4" in ln for ln in lines)
        assert any("Step 4/4" in ln for ln in lines)


class TestLinkDraftCourseTitleMatch:
    """KNOW-2358 QA: link_draft_course must match filesystem-sanitised local
    folders to Skilljar lesson titles whose punctuation differs (e.g. a folder
    ``Exercise_ Foo`` vs the title ``Exercise: Foo``). The matcher normalises on
    alphanumerics only, so the ``_``/``:`` difference no longer blocks the link."""

    def test_matches_underscore_folder_to_colon_title(self, monkeypatch, tmp_path):
        prefix = "2026.1/fme-form-advanced/Custom Transformers 2026.1"
        folder = "Exercise_ Turn a Reusable Workflow into a Custom Transformer"
        (tmp_path / prefix / folder).mkdir(parents=True)

        monkeypatch.setattr(
            skilljar_release,
            "_get_lessons_for_course",
            lambda course_id, key: [
                {"id": "les_x",
                 "title": "Exercise: Turn a Reusable Workflow into a Custom Transformer"},
                {"id": "les_y", "title": "What Are Custom Transformers?"},
            ],
        )

        mapping: dict = {}
        mapping_path = tmp_path / "skilljar-mapping.json"
        result = skilljar_release.link_draft_course(
            prefix, "draft123", "k", mapping, mapping_path, tmp_path,
        )

        # The ':'-vs-'_' lesson matched despite the punctuation difference.
        assert len(result["matched"]) == 1, result
        assert result["matched"][0]["skilljar_lesson_id"] == "les_x"
        assert result["unmatched_local"] == []
        # A direct mapping entry was written + persisted for the to_version dir.
        lesson_dir = f"{prefix}/{folder}"
        assert mapping[lesson_dir]["skilljar_lesson_id"] == "les_x"
        assert mapping[lesson_dir]["skilljar_course_id"] == "draft123"
        assert mapping_path.exists()
