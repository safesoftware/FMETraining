#!/usr/bin/env python3
"""Fetch the Academy's structure from the Skilljar v1 API -> skilljar_snapshot.json

Uses only read endpoints for paths, path items, published courses and lessons. Never calls user,
enrolment or write endpoints, and never prints API responses (the repo is public, so workflow logs
are public). A read-only Skilljar API key is enough.

Environment:
  SKILLJAR_API_KEY   required (GitHub secret). Sent as HTTP Basic username, blank password.
  SKILLJAR_DOMAIN    optional, default academy.safe.com
  SKILLJAR_API_BASE  optional, default https://api.skilljar.com

Endpoints (see https://api.skilljar.com/docs/):
  GET /v1/domains/{domain}/published-paths
  GET /v1/domains/{domain}/published-paths/{id}/path-items   (returned in the path's configured order)
  GET /v1/domains/{domain}/published-courses
  GET /v1/lessons?course_id={id}

Output schema:
  {"fetched_at", "source", "paths": [{"published_path_id","path_id","slug","title","is_hidden","domain_id",
     "courses": [{"order","published_course_id","course_id","slug","title","live","is_hidden","lesson_count",
        "lessons": [{"id","title","order","type"}]}]}],
   "unlinked_courses": [...same course shape...]}
"""
import base64
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

BASE = os.environ.get("SKILLJAR_API_BASE", "https://api.skilljar.com").rstrip("/")
DOMAIN = os.environ.get("SKILLJAR_DOMAIN", "academy.safe.com")
KEY = os.environ.get("SKILLJAR_API_KEY")
CALLS = 0


def get(url, tries=5):
    global CALLS
    token = base64.b64encode(f"{KEY}:".encode()).decode()
    for attempt in range(tries):
        req = urllib.request.Request(url, headers={"Authorization": f"Basic {token}", "Accept": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                CALLS += 1
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503, 504) and attempt < tries - 1:
                time.sleep(int(e.headers.get("Retry-After") or 2 ** attempt))
                continue
            # status and path only: never echo the response body
            raise SystemExit(f"Skilljar API error {e.code} for {urllib.parse.urlsplit(url).path}")


def paged(path, **params):
    """All results of a paginated v1 list endpoint, following `next`."""
    params = {k: v for k, v in params.items() if v is not None}
    url = f"{BASE}{path}" + (f"?{urllib.parse.urlencode(params)}" if params else "")
    out = []
    while url:
        body = get(url)
        out += body.get("results", [])
        url = body.get("next")
        if url:
            time.sleep(0.2)
    return out


def main(out_path):
    if not KEY:
        raise SystemExit("SKILLJAR_API_KEY is not set")
    d = urllib.parse.quote(DOMAIN)

    pub_courses = paged(f"/v1/domains/{d}/published-courses")
    pc_by_course = {pc["course"]["id"]: pc for pc in pub_courses if pc.get("course")}

    lessons_cache = {}

    def lessons(course_id):
        if course_id not in lessons_cache:
            ls = paged("/v1/lessons", course_id=course_id, page_size=100)
            lessons_cache[course_id] = sorted(
                ({"id": l["id"], "title": l.get("title"), "order": l.get("order"), "type": l.get("type")} for l in ls),
                key=lambda l: (l["order"] if l["order"] is not None else 0, l["id"]))
        return lessons_cache[course_id]

    def course_entry(summary, order=None, slug=None):
        cid = summary["id"]
        pc = pc_by_course.get(cid, {})
        return {"order": order, "published_course_id": pc.get("id"), "course_id": cid,
                "slug": pc.get("slug") or slug, "title": summary.get("title"), "live": bool(pc),
                "is_hidden": pc.get("hidden"), "lesson_count": summary.get("lesson_count"),
                "lessons": lessons(cid)}

    out_paths, in_paths = [], set()
    for pp in paged(f"/v1/domains/{d}/published-paths"):
        items = paged(f"/v1/domains/{d}/published-paths/{pp['id']}/path-items")
        courses = []
        for i, it in enumerate(items):  # already in the path's configured order
            if not it.get("course"):
                continue
            in_paths.add(it["course"]["id"])
            courses.append(course_entry(it["course"], order=(i + 1) * 10, slug=it.get("slug")))
        path = pp.get("path") or {}
        out_paths.append({"published_path_id": pp["id"], "path_id": path.get("id"), "slug": pp.get("slug"),
                          "title": path.get("title"), "is_hidden": pp.get("hidden"), "domain_id": DOMAIN,
                          "courses": courses})

    unlinked = [course_entry(pc["course"], slug=pc.get("slug"))
                for cid, pc in pc_by_course.items() if cid not in in_paths]

    out = {"fetched_at": datetime.now(timezone.utc).isoformat(timespec="seconds"), "source": "skilljar-api-v1",
           "paths": out_paths, "unlinked_courses": unlinked}
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    Path(out_path).write_text(json.dumps(out, indent=1, ensure_ascii=False))
    # counts only (public logs)
    print(f"{len(out_paths)} published paths, {len(pub_courses)} published courses, "
          f"{sum(len(v) for v in lessons_cache.values())} lessons, {CALLS} API calls")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "data/skilljar_snapshot.json")
