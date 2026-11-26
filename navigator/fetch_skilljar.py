#!/usr/bin/env python3
"""Fetch the Academy's structure from the Skilljar API -> data/skilljar_snapshot.json

Reads only structural endpoints (paths, path items, published courses, courses, lessons).
Never calls user, enrolment or write endpoints, and never prints API responses (the repo is public,
so workflow logs are public).

Environment:
  SKILLJAR_API_KEY   required (GitHub secret)
  SKILLJAR_API_BASE  optional, default https://api.skilljar.com/v2
  SKILLJAR_AUTH      optional, "basic" (key as username, default) or "bearer"

Output schema (same as the prototype snapshot):
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

BASE = os.environ.get("SKILLJAR_API_BASE", "https://api.skilljar.com/v2").rstrip("/")
KEY = os.environ.get("SKILLJAR_API_KEY")
AUTH = os.environ.get("SKILLJAR_AUTH", "basic").lower()


def headers():
    if AUTH == "bearer":
        return {"Authorization": f"Bearer {KEY}", "Accept": "application/vnd.api+json"}
    token = base64.b64encode(f"{KEY}:".encode()).decode()
    return {"Authorization": f"Basic {token}", "Accept": "application/vnd.api+json"}


def get(url, tries=5):
    for attempt in range(tries):
        req = urllib.request.Request(url, headers=headers())
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503, 504) and attempt < tries - 1:
                time.sleep(int(e.headers.get("Retry-After", 2 ** attempt)))
                continue
            # status only: never echo the body
            raise SystemExit(f"Skilljar API error {e.code} for {urllib.parse.urlsplit(url).path}")


def paged(path, **params):
    """Yield (data, included) pages following links.next."""
    params.setdefault("page[size]", "100")
    url = f"{BASE}{path}?{urllib.parse.urlencode(params)}"
    pages = 0
    while url:
        body = get(url)
        pages += 1
        yield body.get("data", []), body.get("included", [])
        nxt = (body.get("links") or {}).get("next")
        if not nxt:
            break
        # links are relative to the API host, e.g. /v2/lessons/?page[cursor]=...
        url = urllib.parse.urljoin(BASE + "/", nxt) if not nxt.startswith("http") else nxt
        time.sleep(0.2)


def rel_id(rec, name):
    return (((rec.get("relationships") or {}).get(name) or {}).get("data") or {}).get("id")


def main(out_path):
    if not KEY:
        raise SystemExit("SKILLJAR_API_KEY is not set")

    # published paths + path titles
    pub_paths, path_titles = [], {}
    for data, inc in paged("/published-paths/", include="path"):
        pub_paths += data
        for i in inc:
            if i.get("type") == "paths":
                path_titles[i["id"]] = i["attributes"].get("title")

    # published courses + course titles
    pub_courses, courses = {}, {}
    for data, inc in paged("/published-courses/", include="course"):
        for d in data:
            pub_courses[d["id"]] = d
        for i in inc:
            if i.get("type") == "courses":
                courses[i["id"]] = i["attributes"]

    # all lessons, grouped by course
    lessons = {}
    for data, _ in paged("/lessons/"):
        for l in data:
            a = l["attributes"]
            lessons.setdefault(a.get("course_id"), []).append(
                {"id": l["id"], "title": a.get("title"), "order": a.get("order"), "type": a.get("type")})
    for ls in lessons.values():
        ls.sort(key=lambda l: l["order"] or 0)

    def course_entry(pc_id, order=None):
        pc = pub_courses.get(pc_id)
        if not pc:
            return None
        cid = rel_id(pc, "course")
        a, ca = pc["attributes"], courses.get(cid, {})
        return {"order": order, "published_course_id": pc_id, "course_id": cid, "slug": a.get("slug"),
                "title": ca.get("title"), "live": a.get("live"), "is_hidden": a.get("is_hidden"),
                "lesson_count": ca.get("lesson_count"), "lessons": lessons.get(cid, [])}

    out_paths, in_paths, missing = [], set(), 0
    for pp in pub_paths:
        items = []
        for data, _ in paged(f"/published-paths/{pp['id']}/path-items/"):
            items += data
        cs = []
        for it in sorted(items, key=lambda i: i["attributes"].get("order") or 0):
            pc_id = rel_id(it, "published_course")
            c = course_entry(pc_id, it["attributes"].get("order"))
            if c is None:
                missing += 1
                continue
            in_paths.add(pc_id)
            cs.append(c)
        a = pp["attributes"]
        out_paths.append({"published_path_id": pp["id"], "path_id": rel_id(pp, "path"), "slug": a.get("slug"),
                          "title": path_titles.get(rel_id(pp, "path")), "is_hidden": a.get("is_hidden"),
                          "domain_id": rel_id(pp, "domain"), "courses": cs})

    seen, unlinked = set(), []
    for pc_id in pub_courses:
        if pc_id in in_paths:
            continue
        c = course_entry(pc_id)
        if c and c["course_id"] not in seen:
            seen.add(c["course_id"])
            unlinked.append(c)

    out = {"fetched_at": datetime.now(timezone.utc).isoformat(timespec="seconds"), "source": "skilljar-api",
           "paths": out_paths, "unlinked_courses": unlinked}
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    Path(out_path).write_text(json.dumps(out, indent=1, ensure_ascii=False))
    print(f"{len(out_paths)} published paths, {len(pub_courses)} published courses, "
          f"{sum(len(v) for v in lessons.values())} lessons, {missing} path items without a course")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "data/skilljar_snapshot.json")
