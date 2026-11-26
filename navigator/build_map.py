#!/usr/bin/env python3
"""Merge the Skilljar structure, the S3 lesson copies and the previous map into academy-map.json.

usage: build_map.py SNAPSHOT S3_LESSONS PREVIOUS_MAP OUT_MAP [CONFIG]

Rules
- Version = first folder of the S3 key. Copies of the same lesson that differ only in punctuation
  (older scraper runs wrote "?", "." or "_") are collapsed, keeping the most recently modified one.
- Courses are matched by title across all path folders (the scraper stores a course once, even when
  it is in several paths), so one copy can appear under every path that contains that course.
- Versioned paths (slug ends -YYYY-N) use copies whose course folder equals the course title exactly.
- Current paths use every copy whose course folder equals the course title with its version suffix
  removed. The highest version is "current"; the rest are listed as older versions.
- Courses not in any path (standalone / live courses) match the same way.
- Copies no course uses go to "unmatched".
- Paths, courses and lessons in the previous map that Skilljar no longer returns are kept, marked
  "removed", so older material never disappears from the page.
- Hidden paths and paths on other domains are left out entirely (this file is committed to a public repo).
"""
import json
import re
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

VERSION_SUFFIX = re.compile(r"\s+\d{4}\.\d+\s*$")
SLUG_VERSION = re.compile(r"-(\d{4})-(\d+)$")
LESSON_TYPES_WITHOUT_COPY = {"QUIZ", "VILT", "IE_EXAM", "WIDGET", "ASSET", "WEB_PACKAGE"}


def norm(s):
    return re.sub(r"[^a-z0-9]+", " ", s.lower()).strip()


def strip_version(s):
    return VERSION_SUFFIX.sub("", s)


def vkey(v):
    return tuple(int(x) for x in v.split("."))


def load(p, default=None):
    p = Path(p)
    return json.loads(p.read_text()) if p.exists() else default


def collapse_copies(s3_lessons):
    """One entry per (version, path_folder, course, lesson) after punctuation normalisation."""
    best = {}
    variants = defaultdict(int)
    for c in s3_lessons:
        k = (c["version"], c["path_folder"], norm(c["course_folder"]), norm(c["lesson_folder"]))
        variants[k] += 1
        if k not in best or (c.get("last_modified") or "") > (best[k].get("last_modified") or ""):
            best[k] = c
    return list(best.values()), sum(n - 1 for n in variants.values())


class Index:
    """S3 copies indexed by course folder, both exactly and with the version suffix removed.

    The scraper stores each course once, under one path folder, even when Skilljar puts the course in
    several paths. So courses are matched by title across all path folders, and one copy can serve every
    path that contains the course. The path folder is only used to prefer one copy when the same
    course version was stored under more than one folder.
    """

    def __init__(self, copies, aliases):
        self.exact = defaultdict(list)
        self.stripped = defaultdict(list)
        for c in copies:
            c["_base"] = aliases.get(c["path_folder"], c["path_folder"])
            c["_used"] = False
            cf = norm(c["course_folder"])
            self.exact[cf].append(c)
            self.stripped[strip_version_norm(cf)].append(c)

    def take(self, base, course_title, exact):
        """Copies for a course, one per (version, lesson). exact=True matches the full title incl. version."""
        found = self.exact.get(norm(course_title), []) if exact else \
            self.stripped.get(strip_version_norm(norm(course_title)), [])
        best = {}
        for c in found:
            k = (c["version"], norm(c["lesson_folder"]))
            rank = (c["_base"] == base, c.get("last_modified") or "")
            if k not in best or rank > best[k][0]:
                best[k] = (rank, c)
        for c in found:
            c["_used"] = True
        return [c for _, c in best.values()]

    def unused(self):
        return [c for cs in self.exact.values() for c in cs if not c["_used"]]


def strip_version_norm(normalised):
    # "learn spatial data concepts 2026 1" -> "learn spatial data concepts"
    return re.sub(r"\s+\d{4}\s+\d+$", "", normalised)


def build_course(course, copies, academy_url, no_backup_titles=()):
    """Attach copies to the course's lessons; return the course entry."""
    by_lesson = defaultdict(list)
    for c in copies:
        by_lesson[norm(c["lesson_folder"])].append(c)
    lessons = []
    for les in course["lessons"]:
        found = by_lesson.pop(norm(les["title"]), [])
        found.sort(key=lambda c: vkey(c["version"]), reverse=True)
        lessons.append({
            "lesson_id": les["id"],
            "title": les["title"],
            "order": les["order"],
            "type": les.get("type"),
            "status": "live",
            "expects_copy": les.get("type") not in LESSON_TYPES_WITHOUT_COPY and les["title"] not in no_backup_titles,
            "copies": [{"version": c["version"], "url": c["url"]} for c in found],
        })
    # copies whose lesson is no longer in the course (renamed or removed lessons)
    extra = []
    for _, cs in sorted(by_lesson.items()):
        cs.sort(key=lambda c: vkey(c["version"]), reverse=True)
        extra.append({
            "title": cs[0]["lesson_folder"],
            "copies": [{"version": c["version"], "url": c["url"]} for c in cs],
        })
    versions = sorted({c["version"] for c in copies}, key=vkey, reverse=True)
    return {
        "course_id": course["course_id"],
        "title": course["title"],
        "slug": course.get("slug"),
        "url": f"{academy_url}/{course['slug']}" if course.get("slug") else None,
        "order": course.get("order"),
        "status": "live",
        "versions": versions,
        "lessons": lessons,
        "other_backups": extra,
    }


def same(a, b, key, alt):
    """Same item if the IDs match, or (when IDs differ between API versions) the slug/title matches."""
    if a.get(key) is not None and a.get(key) == b.get(key):
        return True
    return bool(a.get(alt)) and norm(a.get(alt) or "") == norm(b.get(alt) or "")


def find(items, old, key, alt):
    return next((i for i in items if same(i, old, key, alt)), None)


def merge_removed(new_items, old_items, key, alt):
    """Append items from the previous map that are missing now, marked removed."""
    for old in old_items or []:
        if find(new_items, old, key, alt) is None:
            old = dict(old)
            old["status"] = "removed"
            new_items.append(old)


def main(snapshot_p, s3_p, prev_p, out_p, config_p="config.json"):
    cfg = load(config_p, {})
    academy_url = cfg.get("academy_url", "https://academy.safe.com")
    aliases = cfg.get("path_folder_aliases", {})
    domains = set(cfg.get("domain_ids", []))
    no_backup = set(cfg.get("lesson_titles_not_backed_up", []))
    excluded = cfg.get("exclude_course_title_patterns", [])
    snap = load(snapshot_p)
    s3 = load(s3_p)
    prev = load(prev_p, {}) or {}
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")

    copies, collapsed = collapse_copies(s3["lessons"])
    idx = Index(copies, aliases)

    # choose paths: right domain, not hidden, one entry per path_id
    paths, seen, skipped = [], set(), []
    for p in snap["paths"]:
        if domains and p.get("domain_id") not in domains:
            skipped.append((p["slug"], "other domain"))
            continue
        if cfg.get("exclude_hidden_paths", True) and p.get("is_hidden"):
            skipped.append((p["slug"], "hidden"))
            continue
        if p["path_id"] in seen:
            continue
        seen.add(p["path_id"])
        paths.append(p)

    def path_entry(p, claim_exact):
        m = SLUG_VERSION.search(p["slug"])
        base = SLUG_VERSION.sub("", p["slug"])
        courses = []
        for c in sorted(p["courses"], key=lambda c: c.get("order") or 0):
            got = idx.take(base, c["title"], exact=claim_exact)
            courses.append(build_course(c, got, academy_url, no_backup))
        return {
            "path_id": p["path_id"],
            "slug": p["slug"],
            "base_slug": base,
            "title": p["title"],
            "kind": "versioned" if m else "current",
            "version": f"{m.group(1)}.{m.group(2)}" if m else None,
            "url": f"{academy_url}/path/{p['slug']}",
            "status": "live",
            "courses": courses,
        }

    # versioned paths first (exact course titles), then current paths (version-stripped)
    versioned = [p for p in paths if SLUG_VERSION.search(p["slug"])]
    current = [p for p in paths if not SLUG_VERSION.search(p["slug"])]
    out_paths = [path_entry(p, True) for p in versioned] + [path_entry(p, False) for p in current]

    # standalone courses (not in any path): match on any path folder
    standalone = []
    for c in snap.get("unlinked_courses", []):
        if not c.get("title") or any(re.search(x, c["title"]) for x in excluded):
            continue  # course deleted in Skilljar, or a test/clone course
        got = idx.take(None, c["title"], exact=False)
        if got:
            standalone.append(build_course(c, got, academy_url, no_backup))

    # unmatched copies, grouped by folder
    groups = defaultdict(list)
    for c in idx.unused():
        groups[(c["version"], c["path_folder"], c["course_folder"])].append(c)
    unmatched = [
        {"version": v, "path_folder": pf, "course_folder": cf,
         "lessons": [{"title": c["lesson_folder"], "url": c["url"]} for c in sorted(cs, key=lambda c: c["lesson_folder"])]}
        for (v, pf, cf), cs in sorted(groups.items(), key=lambda kv: (vkey(kv[0][0]), kv[0][1], kv[0][2]))
    ]

    # keep what the previous map knew about but Skilljar no longer returns
    prev_paths = prev.get("paths", [])
    for p in out_paths:
        old = find(prev_paths, p, "path_id", "slug")
        p["first_seen"] = (old or {}).get("first_seen", now[:10])
        if old:
            merge_removed(p["courses"], old.get("courses"), "course_id", "title")
            for c in p["courses"]:
                oc = find(old.get("courses", []), c, "course_id", "title") if c["status"] == "live" else None
                if oc:
                    merge_removed(c["lessons"], oc.get("lessons"), "lesson_id", "title")
    for old in prev_paths:
        if find(out_paths, old, "path_id", "slug") is None:
            old = dict(old)
            old["status"] = "removed"
            out_paths.append(old)

    order = {"current": 0, "versioned": 1}
    out_paths.sort(key=lambda p: (p["status"] != "live", order.get(p["kind"], 2), p["base_slug"],
                                  tuple(-x for x in vkey(p["version"])) if p.get("version") else ()))

    def count(pred):
        return sum(1 for p in out_paths for c in p["courses"] for l in c["lessons"] if pred(l))

    stats = {
        "paths": len(out_paths),
        "paths_current": sum(1 for p in out_paths if p["kind"] == "current" and p["status"] == "live"),
        "paths_versioned": sum(1 for p in out_paths if p["kind"] == "versioned" and p["status"] == "live"),
        "paths_removed": sum(1 for p in out_paths if p["status"] == "removed"),
        "lessons_in_paths": count(lambda l: True),
        "lessons_with_copy": count(lambda l: l["copies"]),
        "lessons_missing_copy": count(lambda l: l["expects_copy"] and not l["copies"]),
        "standalone_courses": len(standalone),
        "s3_copies": len(s3["lessons"]),
        "s3_punctuation_duplicates_collapsed": collapsed,
        "s3_copies_unmatched": sum(len(u["lessons"]) for u in unmatched),
        # counts only: hidden path names must not appear in this public file or in the logs
        "paths_skipped_hidden": sum(1 for _, why in skipped if why == "hidden"),
        "paths_skipped_other_domain": sum(1 for _, why in skipped if why == "other domain"),
    }
    # run timestamps go in a separate, uncommitted file so the map only changes when structure changes
    run = {"generated_at": now, "skilljar_fetched_at": snap.get("fetched_at"), "s3_listed_at": s3.get("listed_at")}
    Path(out_p).with_name("run.json").write_text(json.dumps(run, indent=1))
    out = {
        "bucket_url": s3.get("bucket_url"),
        "stats": stats,
        "paths": out_paths,
        "standalone_courses": standalone,
        "unmatched": unmatched,
    }
    Path(out_p).write_text(json.dumps(out, indent=1, ensure_ascii=False))
    print(json.dumps(stats, indent=1))


if __name__ == "__main__":
    main(*sys.argv[1:])
