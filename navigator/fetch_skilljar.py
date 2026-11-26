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
import http.client
import json
import os
import sys
import time
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path

BASE = os.environ.get("SKILLJAR_API_BASE", "https://api.skilljar.com").rstrip("/")
DOMAIN = os.environ.get("SKILLJAR_DOMAIN", "academy.safe.com")
KEY = os.environ.get("SKILLJAR_API_KEY")
TIMEOUT = float(os.environ.get("SKILLJAR_TIMEOUT", "20"))  # per request; a hung request is retried
PAUSE = float(os.environ.get("SKILLJAR_PAUSE", "0.25"))    # seconds between calls, to be gentle on the API
RETRIES = 6
CALLS = 0
_BASE = urllib.parse.urlsplit(BASE)
_conn = None


def connection():
    """One kept-alive connection for all calls, so there's one TLS handshake instead of ~300."""
    global _conn
    if _conn is None:
        cls = http.client.HTTPSConnection if _BASE.scheme == "https" else http.client.HTTPConnection
        _conn = cls(_BASE.hostname, _BASE.port, timeout=TIMEOUT)
    return _conn


def drop_connection():
    global _conn
    if _conn is not None:
        _conn.close()
    _conn = None


def get(url):
    """GET a JSON page, retrying rate limits, server errors and dropped or timed-out connections."""
    global CALLS
    u = urllib.parse.urlsplit(url)
    if (u.scheme, u.netloc) != (_BASE.scheme, _BASE.netloc):
        # never send the API key to another host, e.g. via an unexpected `next` link
        raise SystemExit(f"Refusing to call a different host: {u.netloc}")
    target = u.path + (f"?{u.query}" if u.query else "")
    token = base64.b64encode(f"{KEY}:".encode()).decode()
    headers = {"Authorization": f"Basic {token}", "Accept": "application/json", "Connection": "keep-alive"}
    for attempt in range(RETRIES):
        if CALLS:
            time.sleep(PAUSE)
        wait = min(2 ** attempt * 2, 60)
        try:
            conn = connection()
            conn.request("GET", target, headers=headers)
            resp = conn.getresponse()
            body = resp.read()
            if resp.will_close:
                drop_connection()
            if resp.status == 200:
                CALLS += 1
                return json.loads(body)
            if resp.status not in (429, 500, 502, 503, 504) or attempt == RETRIES - 1:
                # status and path only: never echo the response body
                raise SystemExit(f"Skilljar API error {resp.status} for {u.path}")
            wait = int(resp.getheader("Retry-After") or wait)
            reason = f"HTTP {resp.status}"
        except (OSError, http.client.HTTPException, ValueError) as e:
            # network trouble: TLS handshake or read timeouts, resets, dropped connections, truncated bodies
            drop_connection()
            if attempt == RETRIES - 1:
                raise SystemExit(f"Skilljar API unreachable for {u.path} after {RETRIES} tries: {type(e).__name__}")
            reason = type(e).__name__
        print(f"  retrying {u.path} in {wait}s ({reason})", flush=True)
        time.sleep(wait)


def paged(path, **params):
    """All results of a paginated v1 list endpoint, following `next`."""
    params = {k: v for k, v in params.items() if v is not None}
    url = f"{BASE}{path}" + (f"?{urllib.parse.urlencode(params)}" if params else "")
    out = []
    while url:
        body = get(url)
        out += body.get("results", [])
        url = body.get("next")
    return out


def main(out_path):
    if not KEY:
        raise SystemExit("SKILLJAR_API_KEY is not set")
    d = urllib.parse.quote(DOMAIN)

    pub_courses = paged(f"/v1/domains/{d}/published-courses")
    pc_by_course = {pc["course"]["id"]: pc for pc in pub_courses if pc.get("course")}
    pc_by_id = {pc["id"]: pc for pc in pub_courses}

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

    def item_course(it):
        """A domain path item is {id, order, published_course}; resolve it to the course summary."""
        ref = it.get("published_course")
        pc = pc_by_id.get(ref.get("id") if isinstance(ref, dict) else ref)
        if pc and pc.get("course"):
            return pc["course"]
        return it.get("course")  # shape of /v1/paths/{id}/path-items, just in case

    out_paths, in_paths = [], set()
    expected = resolved = unresolved = 0
    for pp in paged(f"/v1/domains/{d}/published-paths"):
        path = pp.get("path") or {}
        items = paged(f"/v1/domains/{d}/published-paths/{pp['id']}/path-items")
        items.sort(key=lambda it: it.get("order") if it.get("order") is not None else 0)
        expected += len(items)
        courses = []
        for i, it in enumerate(items):
            summary = item_course(it)
            if not summary:
                unresolved += 1
                continue
            in_paths.add(summary["id"])
            order = it.get("order") if it.get("order") is not None else (i + 1) * 10
            courses.append(course_entry(summary, order=order))
        resolved += len(courses)
        out_paths.append({"published_path_id": pp["id"], "path_id": path.get("id"), "slug": pp.get("slug"),
                          "title": path.get("title"), "is_hidden": pp.get("hidden"), "domain_id": DOMAIN,
                          "courses": courses})

    # Guard: if path items exist but none resolve to a course, the API shape has changed. Stop here,
    # rather than write a snapshot that would mark every course in every path as removed.
    if expected and not resolved:
        raise SystemExit(f"None of the {expected} path items resolved to a course; check the path-items response shape")
    if unresolved:
        print(f"  {unresolved} of {expected} path items did not resolve to a published course", flush=True)

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
