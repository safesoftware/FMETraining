"""
Skilljar Release module.

Entry points:
  scan_saved_lessons(to_version, repo_root) → set[str]
      Walk the to_version folder for saved index.html files.
  build_release_plan(scope_lesson_dirs, to_version, mapping, repo_root) → dict
      Group selected lessons by Skilljar course and produce a release plan.
  execute_release(plan, api_key, domain, mapping, mapping_path, repo_root, dry_run) → Iterator[str]
      Generator yielding log lines for the full archive→push→rename→tag→mapping flow.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Iterator

from pipeline.skilljar_push import (
    _VERSION_SUFFIX_RE,
    _request,
    _patch_lesson_html,
    _get_course,
    _create_course,
    _create_lesson,
    _get_lesson,
    _s3_put,
    _s3_delete,
    _create_asset_from_url,
    _wait_for_asset_url,
)


# ---------------------------------------------------------------------------
# HTML utilities
# ---------------------------------------------------------------------------

_RELATIVE_SRC_RE = re.compile(r'(src=["\'])(?!https?://|data:)([^"\']+)(["\'])', re.IGNORECASE)
_SRC_RE = re.compile(r'src=["\']([^"\']+)["\']', re.IGNORECASE)


def _rewrite_images(new_html: str, original_html: str) -> tuple[str, list[str]]:
    """
    Replace relative src= paths in new_html with absolute URLs extracted from original_html,
    matched by filename. Returns (rewritten_html, list_of_unmatched_relative_paths).
    """
    # Build filename → absolute URL map from original HTML
    original_urls: dict[str, str] = {}
    for src in _SRC_RE.findall(original_html):
        if src.startswith(("http://", "https://", "data:")):
            original_urls[Path(src.split("?")[0]).name] = src

    unmatched: list[str] = []

    def _replace(m: re.Match) -> str:
        quote_open, rel_path, quote_close = m.group(1), m.group(2), m.group(3)
        filename = Path(rel_path.split("?")[0]).name
        if filename in original_urls:
            return f"{quote_open}{original_urls[filename]}{quote_close}"
        unmatched.append(rel_path)
        return m.group(0)

    rewritten = _RELATIVE_SRC_RE.sub(_replace, new_html)
    return rewritten, unmatched


_IMAGE_UPLOAD_RETRIES = 10


def _upload_and_rewrite_images(
    html: str,
    relative_paths: list[str],
    lesson_dir: str,
    repo_root: Path,
    api_key: str,
    s3_bucket: str = "",
    s3_key_id: str = "",
    s3_secret: str = "",
    s3_region: str = "us-east-1",
) -> tuple[str, list[tuple[str, str]]]:
    """Upload local images via S3 → Skilljar asset and rewrite their src= paths in html.

    Flow per image: PUT to caller's S3 bucket (public-read) → POST /v1/assets with
    content_url → poll for Skilljar CDN URL → DELETE from S3.

    Returns (rewritten_html, failed) where failed is a list of (rel_path, reason).
    """
    if not (s3_bucket and s3_key_id and s3_secret):
        return html, [
            (p, "S3 not configured — set AWS_S3_BUCKET, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY in .env")
            for p in relative_paths
        ]

    url_map: dict[str, str] = {}
    failed: list[tuple[str, str]] = []

    for rel_path in relative_paths:
        filename = Path(rel_path.split("?")[0]).name
        local_file = repo_root / lesson_dir / "images" / filename

        if not local_file.exists():
            failed.append((rel_path, f"local file not found: {local_file}"))
            continue

        s3_key: str | None = None
        hosted_url: str | None = None
        try:
            _, s3_key = _s3_put(local_file, s3_bucket, s3_key_id, s3_secret, s3_region)
            s3_url = f"https://{s3_bucket}.s3.{s3_region}.amazonaws.com/{s3_key}"
            asset_id = _create_asset_from_url(s3_url, api_key)
            hosted_url = _wait_for_asset_url(asset_id, api_key, _IMAGE_UPLOAD_RETRIES)
        except RuntimeError as exc:
            failed.append((rel_path, str(exc)))
            continue
        finally:
            if s3_key:
                try:
                    _s3_delete(s3_key, s3_bucket, s3_key_id, s3_secret, s3_region)
                except RuntimeError:
                    pass

        if hosted_url:
            url_map[rel_path] = hosted_url
        else:
            failed.append((rel_path, "timed out waiting for Skilljar CDN URL"))

    if url_map:
        def _replace_uploaded(m: re.Match) -> str:
            quote_open, path, quote_close = m.group(1), m.group(2), m.group(3)
            return f"{quote_open}{url_map.get(path, path)}{quote_close}"
        html = _RELATIVE_SRC_RE.sub(_replace_uploaded, html)

    return html, failed


# ---------------------------------------------------------------------------
# Local file helpers
# ---------------------------------------------------------------------------

def lesson_local_path(lesson_dir: str, repo_root: Path) -> Path | None:
    """Return absolute path to index.html for a lesson_dir if it exists, else None."""
    p = repo_root / lesson_dir / "index.html"
    return p if p.exists() else None


def scan_saved_lessons(to_version: str, repo_root: Path) -> set[str]:
    """Return lesson_dirs with new or modified index.html files according to git."""
    import subprocess
    version_dir = repo_root / to_version
    if not version_dir.is_dir():
        return set()
    result = set()
    try:
        proc = subprocess.run(
            ["git", "status", "--porcelain", "--", to_version],
            cwd=repo_root, capture_output=True, text=True, timeout=30,
        )
        for line in proc.stdout.splitlines():
            if len(line) < 4:
                continue
            path = line[3:].strip()
            # Untracked directories: git shows "dir/" — scan inside for index.html
            if path.endswith("/"):
                for idx in (repo_root / path).rglob("index.html"):
                    result.add(str(idx.parent.relative_to(repo_root)).replace("\\", "/"))
            elif path.endswith("index.html"):
                result.add(str(Path(path).parent).replace("\\", "/"))
    except Exception:
        pass
    return result


# ---------------------------------------------------------------------------
# Mapping lookup
# ---------------------------------------------------------------------------

def _find_source_entry(lesson_dir: str, mapping: dict) -> tuple[str, dict] | tuple[None, None]:
    """
    Find the best matching source entry in mapping for a given lesson_dir.

    Matches on LP + canonical course name + lesson suffix regardless of version.
    Returns the match with the most recent version string.
    """
    if lesson_dir in mapping:
        return lesson_dir, mapping[lesson_dir]

    parts = Path(lesson_dir).parts
    if len(parts) < 4:
        return None, None
    lp = parts[1]
    course_canonical = _VERSION_SUFFIX_RE.sub("", parts[2]).strip()
    lesson_suffix = "/".join(parts[3:])

    matches: list[tuple[str, dict]] = []
    for k, v in mapping.items():
        kp = Path(k).parts
        if len(kp) < 4:
            continue
        if kp[1] != lp:
            continue
        if _VERSION_SUFFIX_RE.sub("", kp[2]).strip() != course_canonical:
            continue
        if "/".join(kp[3:]) != lesson_suffix:
            continue
        matches.append((k, v))

    if not matches:
        return None, None

    def _version_key(item: tuple[str, dict]) -> tuple[int, int]:
        m = re.match(r"^(\d+)\.(\d+)/", item[0])
        return (int(m.group(1)), int(m.group(2))) if m else (0, 0)

    return max(matches, key=_version_key)


def _find_prev_version_entry(lesson_dir: str, to_version: str, mapping: dict) -> tuple[str, dict] | tuple[None, None]:
    """
    Find the most recent mapping entry for the same lesson from a version OTHER than to_version.
    Used to borrow hosted image URLs when pushing to a draft with no existing content.
    """
    parts = Path(lesson_dir).parts
    if len(parts) < 4:
        return None, None
    lp = parts[1]
    course_canonical = _VERSION_SUFFIX_RE.sub("", parts[2]).strip()
    lesson_suffix = "/".join(parts[3:])

    matches: list[tuple[str, dict]] = []
    for k, v in mapping.items():
        kp = Path(k).parts
        if len(kp) < 4 or kp[0] == to_version:
            continue
        if kp[1] != lp:
            continue
        if _VERSION_SUFFIX_RE.sub("", kp[2]).strip() != course_canonical:
            continue
        if "/".join(kp[3:]) != lesson_suffix:
            continue
        matches.append((k, v))

    if not matches:
        return None, None

    def _version_key(item: tuple[str, dict]) -> tuple[int, int]:
        m = re.match(r"^(\d+)\.(\d+)/", item[0])
        return (int(m.group(1)), int(m.group(2))) if m else (0, 0)

    return max(matches, key=_version_key)


def is_lesson_mapped(lesson_dir: str, mapping: dict) -> bool:
    """Return True if a source mapping entry exists for this lesson_dir."""
    _, entry = _find_source_entry(lesson_dir, mapping)
    return entry is not None


# ---------------------------------------------------------------------------
# Release plan builder
# ---------------------------------------------------------------------------

def build_release_plan(
    scope_lesson_dirs: list[str],
    to_version: str,
    mapping: dict,
    repo_root: Path,
) -> dict:
    """
    Group selected lessons by Skilljar course and produce a release plan dict:

    {
        "to_version": "2026.1",
        "courses": [
            {
                "action": "release" | "no_mapping",
                "source_course_id": "...",
                "source_course_title": "Connect To Data 2025.0",
                "archive_title": "Connect To Data 2025.0",
                "new_title": "Connect To Data 2026.1",
                "new_labels": ["2026.1"],
                "lp": "fme-form-basic",
                "course_canonical": "Connect To Data",
                "course_folder": "Connect To Data 2026.1",
                "lessons": [...],
            }
        ],
        "warnings": [...],
    }
    """
    warnings: list[str] = []
    course_groups: dict[str, list[str]] = {}

    for lesson_dir in scope_lesson_dirs:
        parts = Path(lesson_dir).parts
        if len(parts) < 4:
            warnings.append(f"Skipping invalid lesson_dir: {lesson_dir}")
            continue
        course_key = "/".join([parts[0], parts[1], parts[2]])
        course_groups.setdefault(course_key, []).append(lesson_dir)

    courses = []
    for course_key, lesson_dirs in sorted(course_groups.items()):
        parts = Path(course_key).parts
        lp = parts[1]
        course_folder = parts[2]
        course_canonical = _VERSION_SUFFIX_RE.sub("", course_folder).strip()
        new_title = course_folder

        lessons = []
        source_course_id: str | None = None
        source_course_title: str | None = None
        all_direct_matches = True  # True if every mapped lesson key IS the to_version path

        for lesson_dir in sorted(lesson_dirs):
            lparts = Path(lesson_dir).parts
            lesson_name = "/".join(lparts[3:])
            local = lesson_local_path(lesson_dir, repo_root)

            source_key, source_entry = _find_source_entry(lesson_dir, mapping)
            if source_entry is None:
                lessons.append({
                    "skilljar_lesson_id": "",
                    "lesson_dir": lesson_dir,
                    "lesson_name": lesson_name,
                    "local_path": str(local) if local else None,
                    "has_local_file": local is not None,
                    "mapped": False,
                    "is_draft": False,
                })
            else:
                is_direct = source_key == lesson_dir  # key IS the to_version path
                if not is_direct:
                    all_direct_matches = False
                if source_course_id is None:
                    source_course_id = source_entry["skilljar_course_id"]
                    source_course_title = source_entry.get("_course_title", "") or ""
                lessons.append({
                    "skilljar_lesson_id": source_entry["skilljar_lesson_id"],
                    "skilljar_course_id": source_entry["skilljar_course_id"],
                    "lesson_dir": lesson_dir,
                    "lesson_name": lesson_name,
                    "local_path": str(local) if local else None,
                    "has_local_file": local is not None,
                    "mapped": True,
                    "is_draft": is_direct,
                })

        if source_course_id is None:
            warnings.append(f"No Skilljar mapping found for course: {course_folder}")
            courses.append({
                "action": "no_mapping",
                "source_course_id": "",
                "source_course_title": "",
                "archive_title": "",
                "new_title": new_title,
                "new_labels": [to_version],
                "lp": lp,
                "course_canonical": course_canonical,
                "course_folder": course_folder,
                "lessons": lessons,
                "is_draft": False,
            })
        else:
            # push_only when every mapped lesson was found via a direct to_version key
            # (means a draft/pre-linked course — archive step would be wrong)
            action = "push_only" if all_direct_matches else "release"
            archive_title = source_course_title or course_canonical
            courses.append({
                "action": action,
                "source_course_id": source_course_id,
                "source_course_title": source_course_title or archive_title,
                "archive_title": archive_title,
                "new_title": new_title,
                "new_labels": [to_version],
                "lp": lp,
                "course_canonical": course_canonical,
                "course_folder": course_folder,
                "lessons": lessons,
                "is_draft": action == "push_only",
            })

    return {"to_version": to_version, "courses": courses, "warnings": warnings}


# ---------------------------------------------------------------------------
# Additional Skilljar API helpers
# ---------------------------------------------------------------------------

def _get_lessons_for_course(course_id: str, api_key: str) -> list[dict]:
    """Return all lessons for a course, following pagination."""
    from urllib.parse import urlparse
    results: list[dict] = []
    path: str | None = f"/lessons?course_id={course_id}&limit=100"
    while path:
        data = _request("GET", path, api_key)
        results.extend(data.get("results", []))
        next_url = data.get("next")
        if next_url:
            parsed = urlparse(next_url)
            path = parsed.path + ("?" + parsed.query if parsed.query else "")
        else:
            path = None
    return results


def _patch_course(course_id: str, data: dict, api_key: str) -> dict:
    return _request("PATCH", f"/courses/{course_id}", api_key, data)


def _get_tags(api_key: str) -> list[dict]:
    data = _request("GET", "/tags?limit=200", api_key)
    return data.get("results", [])


def _create_tag(name: str, api_key: str) -> dict:
    return _request("POST", "/tags", api_key, {"name": name})


def _get_published_courses(domain: str, course_id: str, api_key: str) -> list[dict]:
    data = _request(
        "GET",
        f"/domains/{domain}/published-courses?course__id={course_id}&limit=100",
        api_key,
    )
    return data.get("results", [])


def _get_published_course_tags(domain: str, pub_course_id: str, api_key: str) -> list[dict]:
    data = _request("GET", f"/domains/{domain}/published-courses/{pub_course_id}/tags", api_key)
    return data.get("results", [])


def _add_published_course_tag(domain: str, pub_course_id: str, tag_id: str, api_key: str) -> None:
    _request(
        "POST",
        f"/domains/{domain}/published-courses/{pub_course_id}/tags",
        api_key,
        {"tag": {"id": tag_id}},
    )


def _delete_published_course_tag(domain: str, pub_course_id: str, assoc_id: str, api_key: str) -> None:
    _request("DELETE", f"/domains/{domain}/published-courses/{pub_course_id}/tags/{assoc_id}", api_key)


def _delete_lesson(lesson_id: str, api_key: str) -> None:
    _request("DELETE", f"/lessons/{lesson_id}", api_key)


# ---------------------------------------------------------------------------
# Execute release
# ---------------------------------------------------------------------------

def execute_release(
    plan: dict,
    api_key: str,
    domain: str,
    mapping: dict,
    mapping_path: Path,
    repo_root: Path,
    dry_run: bool = False,
    s3_bucket: str = "",
    s3_key_id: str = "",
    s3_secret: str = "",
    s3_region: str = "us-east-1",
) -> Iterator[str]:
    """
    Generator yielding log lines for the full release flow.

    For each "release" course:
      Step 1 — Archive: copy all existing lessons to a new archive course
      Step 2 — Push:    PATCH lesson HTML with new to_version content
      Step 3 — Rename:  PATCH course title + labels
      Step 4 — Tags:    update published-course tags on the domain
      Step 5 — Mapping: add new to_version entries to skilljar-mapping.json
    """
    to_version = plan["to_version"]
    dry = "[DRY RUN] " if dry_run else ""

    for course in plan["courses"]:
        if course["action"] == "no_mapping":
            yield f"SKIP (no Skilljar mapping): {course['new_title']}"
            continue

        source_course_id: str = course["source_course_id"]
        archive_title: str = course["archive_title"]
        new_title: str = course["new_title"]
        new_labels: list[str] = course["new_labels"]
        lessons: list[dict] = course["lessons"]
        is_push_only: bool = course["action"] == "push_only"

        yield f"=== Course: {new_title} (id={source_course_id}) ==="

        # ------------------------------------------------------------------
        # Step 1 — Archive (skipped for push_only / draft courses)
        # ------------------------------------------------------------------
        if is_push_only:
            yield "Step 1/5: Skipping archive (target is an existing draft/linked course)."
        else:
            yield f"{dry}Step 1/5: Archiving '{archive_title}'…"

        if not is_push_only:
            if not dry_run:
                try:
                    source_course = _get_course(source_course_id, api_key)
                    old_lesson_stubs = _get_lessons_for_course(source_course_id, api_key)
                    yield f"  {len(old_lesson_stubs)} lesson(s) to copy."

                    existing_labels = source_course.get("labels") or []
                    archive_labels = list({*existing_labels, "archived"})

                    archive_course_resp = _create_course(archive_title, source_course, api_key)
                    archive_course_id: str = archive_course_resp["id"]
                    _patch_course(archive_course_id, {"labels": archive_labels}, api_key)
                    yield f"  Created archive course id={archive_course_id}"

                    for stub in sorted(old_lesson_stubs, key=lambda l: l.get("order", 0)):
                        detail = _get_lesson(stub["id"], api_key)
                        new_archived_lesson = _create_lesson(
                            archive_course_id,
                            detail.get("title", stub.get("title", "")),
                            detail.get("type", "HTML"),
                            detail.get("order", 0),
                            api_key,
                        )
                        html_content = detail.get("content_html", "")
                        if html_content:
                            _patch_lesson_html(new_archived_lesson["id"], html_content, api_key)

                    yield "  Archive complete."
                except RuntimeError as exc:
                    yield f"  ERROR during archive: {exc}"
                    yield "  Aborting this course — no changes made to live lessons."
                    continue
            else:
                yield "  Would GET all lessons, POST archive course, POST+PATCH each lesson copy."

        # ------------------------------------------------------------------
        # Step 2 — Push new content
        # ------------------------------------------------------------------
        yield f"{dry}Step 2/5: Pushing new {to_version} content…"
        push_errors: list[str] = []
        new_mapping_entries: dict[str, dict] = {}

        for lesson in lessons:
            lname = lesson["lesson_name"]
            if not lesson.get("mapped"):
                yield f"  SKIP (not mapped): {lname}"
                continue
            if not lesson.get("has_local_file"):
                yield f"  SKIP (no local file): {lname}"
                continue

            lesson_id: str = lesson["skilljar_lesson_id"]
            local_path: str = lesson["local_path"]

            try:
                html = Path(local_path).read_text(encoding="utf-8")
            except Exception as exc:
                yield f"  ERROR reading {local_path}: {exc}"
                push_errors.append(lname)
                continue

            if not dry_run:
                ref_html = ""
                if not is_push_only:
                    try:
                        ref_html = _get_lesson(lesson_id, api_key).get("content_html", "") or ""
                    except RuntimeError:
                        pass
                else:
                    prev_key, prev_entry = _find_prev_version_entry(lesson["lesson_dir"], to_version, mapping)
                    if prev_entry:
                        try:
                            ref_html = _get_lesson(prev_entry["skilljar_lesson_id"], api_key).get("content_html", "") or ""
                        except RuntimeError:
                            pass

                html, unresolved = _rewrite_images(html, ref_html)
                if unresolved:
                    html, failed_uploads = _upload_and_rewrite_images(
                        html, unresolved, lesson["lesson_dir"], repo_root, api_key,
                        s3_bucket=s3_bucket, s3_key_id=s3_key_id,
                        s3_secret=s3_secret, s3_region=s3_region,
                    )
                    for path, reason in failed_uploads:
                        yield f"  WARNING: could not upload {path}: {reason}"

            if not dry_run:
                try:
                    _patch_lesson_html(lesson_id, html, api_key)
                    yield f"  Pushed: {lname} (lesson_id={lesson_id})"
                except RuntimeError as exc:
                    yield f"  ERROR pushing '{lname}' (lesson_id={lesson_id}): {exc}"
                    push_errors.append(lname)
                    continue

            new_mapping_entries[lesson["lesson_dir"]] = {
                "skilljar_lesson_id": lesson_id,
                "skilljar_course_id": source_course_id,
                "_title": lname,
                "_course_title": new_title,
            }

        if push_errors:
            yield f"  {len(push_errors)} lesson(s) had push errors: {', '.join(push_errors)}"
        if dry_run:
            yield f"  Would PATCH {len([l for l in lessons if l.get('mapped') and l.get('has_local_file')])} lesson(s)."

        # ------------------------------------------------------------------
        # Step 3 — Rename course (skipped for drafts — already has correct name)
        # ------------------------------------------------------------------
        if is_push_only:
            yield "Step 3/5: Skipping rename (draft already has correct title/labels)."
        else:
            yield f"{dry}Step 3/5: Renaming course → '{new_title}', labels={new_labels}…"
            if not dry_run:
                try:
                    _patch_course(source_course_id, {"title": new_title, "labels": new_labels}, api_key)
                    yield "  Course renamed and labels updated."
                except RuntimeError as exc:
                    yield f"  ERROR renaming course: {exc}"
            else:
                yield f"  Would PATCH /v1/courses/{source_course_id} title='{new_title}' labels={new_labels}"

        # ------------------------------------------------------------------
        # Step 4 — Update published-course tags (skipped for drafts — not published)
        # ------------------------------------------------------------------
        if is_push_only:
            yield "Step 4/5: Skipping tag update (draft course is not yet published)."
        elif domain:
            yield f"{dry}Step 4/5: Updating published-course tags on domain '{domain}'…"
            old_version_match = _VERSION_SUFFIX_RE.search(course.get("source_course_title", ""))
            old_version: str | None = old_version_match.group(1) if old_version_match else None

            if not dry_run:
                try:
                    all_tags = _get_tags(api_key)
                    tag_by_name: dict[str, str] = {t["name"]: t["id"] for t in all_tags}

                    new_tag_name = to_version
                    if new_tag_name not in tag_by_name:
                        new_tag = _create_tag(new_tag_name, api_key)
                        tag_by_name[new_tag_name] = new_tag["id"]
                        yield f"  Created new org tag: '{new_tag_name}'"
                    new_tag_id = tag_by_name[new_tag_name]

                    pub_courses = _get_published_courses(domain, source_course_id, api_key)
                    yield f"  Found {len(pub_courses)} published course record(s)."

                    for pub in pub_courses:
                        pub_id: str = pub["id"]
                        pub_tags = _get_published_course_tags(domain, pub_id, api_key)

                        if old_version:
                            old_tag_id = tag_by_name.get(old_version)
                            for pt in pub_tags:
                                tag_obj = pt.get("tag", {})
                                if tag_obj.get("id") == old_tag_id or tag_obj.get("name") == old_version:
                                    _delete_published_course_tag(domain, pub_id, pt["id"], api_key)
                                    yield f"  Removed tag '{old_version}' from pub course {pub_id}"

                        _add_published_course_tag(domain, pub_id, new_tag_id, api_key)
                        yield f"  Added tag '{new_tag_name}' to pub course {pub_id}"

                except RuntimeError as exc:
                    yield f"  ERROR updating tags: {exc}"
            else:
                old_v = old_version or "(unknown)"
                yield f"  Would remove tag '{old_v}' and add tag '{to_version}' on published courses."
        else:
            yield "Step 4/5: Skipped — SKILLJAR_DOMAIN not configured."

        # ------------------------------------------------------------------
        # Step 5 — Update mapping
        # ------------------------------------------------------------------
        yield f"{dry}Step 5/5: Updating skilljar-mapping.json…"
        if new_mapping_entries:
            mapping.update(new_mapping_entries)
            if not dry_run:
                mapping_path.write_text(
                    json.dumps(mapping, indent=2, ensure_ascii=False), encoding="utf-8"
                )
                yield f"  Wrote {len(new_mapping_entries)} new mapping entries."
            else:
                yield f"  Would write {len(new_mapping_entries)} new mapping entries (dry run — skipped)."
        else:
            yield "  No new mapping entries to write."

        yield f"Done: {new_title}"

    if plan["warnings"]:
        yield ""
        yield "Warnings:"
        for w in plan["warnings"]:
            yield f"  • {w}"

    yield ""
    yield "Release complete."


# ---------------------------------------------------------------------------
# Link draft course
# ---------------------------------------------------------------------------

def link_draft_course(
    to_version_course_prefix: str,
    skilljar_course_id: str,
    api_key: str,
    mapping: dict,
    mapping_path: Path,
    repo_root: Path,
) -> dict:
    """
    Fetch lessons from an existing Skilljar course (e.g. a manually-created draft),
    match them to local lesson dirs under to_version_course_prefix by title, and
    write the matched entries into skilljar-mapping.json.

    to_version_course_prefix: e.g. "2026.1/fme-form-basic/Connect To Data 2026.1"

    Returns:
        {
            "matched":            [{"local_dir": ..., "skilljar_lesson_id": ..., "title": ...}],
            "unmatched_local":    [folder_name, ...],
            "unmatched_skilljar": [lesson_title, ...],
        }
    """
    course_prefix = to_version_course_prefix.rstrip("/")
    course_dir = repo_root / course_prefix

    # Collect local lesson folders (any subdir — doesn't require index.html)
    local_folders: list[str] = []
    if course_dir.is_dir():
        local_folders = [d.name for d in sorted(course_dir.iterdir()) if d.is_dir()]

    # Fetch lessons from Skilljar
    skilljar_lessons = _get_lessons_for_course(skilljar_course_id, api_key)

    def _normalise(s: str) -> str:
        return s.lower().strip()

    skilljar_by_title: dict[str, dict] = {_normalise(l.get("title", "")): l for l in skilljar_lessons}
    local_by_normalised: dict[str, str] = {_normalise(f): f for f in local_folders}

    matched = []
    unmatched_local = []
    unmatched_skilljar = list(skilljar_by_title.keys())

    course_folder_name = Path(course_prefix).parts[-1] if course_prefix else ""

    for norm_local, folder in local_by_normalised.items():
        if norm_local in skilljar_by_title:
            sj_lesson = skilljar_by_title[norm_local]
            title = sj_lesson.get("title", folder)
            lesson_id = sj_lesson["id"]

            lesson_dir = f"{course_prefix}/{folder}"
            mapping[lesson_dir] = {
                "skilljar_lesson_id": lesson_id,
                "skilljar_course_id": skilljar_course_id,
                "_title": title,
                "_course_title": course_folder_name,
            }
            matched.append({
                "local_dir": lesson_dir,
                "skilljar_lesson_id": lesson_id,
                "title": title,
            })
            if norm_local in unmatched_skilljar:
                unmatched_skilljar.remove(norm_local)
        else:
            unmatched_local.append(folder)

    mapping_path.write_text(json.dumps(mapping, indent=2, ensure_ascii=False), encoding="utf-8")

    return {
        "matched": matched,
        "unmatched_local": unmatched_local,
        "unmatched_skilljar": [skilljar_by_title[k].get("title", k) for k in unmatched_skilljar],
    }
