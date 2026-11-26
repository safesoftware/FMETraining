#!/usr/bin/env python3
"""List every lesson copy in the public safeskilljar bucket.

A lesson copy is any key shaped  <version>/<path-folder>/<course-folder>/<lesson-folder>/index.html
The bucket allows anonymous listing (the same access sync_s3.yml uses), so no credentials are needed.

Writes data/s3_lessons.json:
  {"listed_at": ..., "bucket_url": ..., "lessons": [{"version","path_folder","course_folder","lesson_folder","key","last_modified","url"}],
   "other_index_keys": [...]}   # index.html keys at an unexpected depth, for the report
"""
import json
import re
import sys
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

BUCKET_URL = "https://safeskilljar.s3.us-west-2.amazonaws.com"
NS = {"s3": "http://s3.amazonaws.com/doc/2006-03-01/"}
VERSION_RE = re.compile(r"^\d{4}\.\d+$")


def list_keys():
    token = None
    while True:
        q = {"list-type": "2", "max-keys": "1000"}
        if token:
            q["continuation-token"] = token
        url = f"{BUCKET_URL}/?{urllib.parse.urlencode(q)}"
        with urllib.request.urlopen(url, timeout=60) as r:
            root = ET.fromstring(r.read())
        for c in root.findall("s3:Contents", NS):
            yield c.findtext("s3:Key", namespaces=NS), c.findtext("s3:LastModified", namespaces=NS)
        if root.findtext("s3:IsTruncated", namespaces=NS) != "true":
            return
        token = root.findtext("s3:NextContinuationToken", namespaces=NS)


def main(out_path):
    lessons, other = [], []
    for key, modified in list_keys():
        if not key.endswith("/index.html"):
            continue
        parts = key.split("/")
        if len(parts) == 5 and VERSION_RE.match(parts[0]):
            lessons.append({
                "version": parts[0],
                "path_folder": parts[1],
                "course_folder": parts[2],
                "lesson_folder": parts[3],
                "key": key,
                "last_modified": modified,
                "url": f"{BUCKET_URL}/{urllib.parse.quote(key)}",
            })
        else:
            other.append(key)
    out = {
        "listed_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "bucket_url": BUCKET_URL,
        "lessons": sorted(lessons, key=lambda l: l["key"]),
        "other_index_keys": sorted(other),
    }
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    Path(out_path).write_text(json.dumps(out, indent=1, ensure_ascii=False))
    print(f"{len(lessons)} lesson copies, {len(other)} other index.html keys -> {out_path}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "data/s3_lessons.json")
