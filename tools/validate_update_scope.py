#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys

from common import load_json
from generate_update_queue import normalize_course_scope, parse_scope_file, select_scoped_lessons


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", default="artifacts/lesson_manifest.json")
    ap.add_argument("--scope-file", required=True)
    ap.add_argument("--from-version")
    ap.add_argument("--to-version")
    ap.add_argument("--courses", help="Comma-separated source course paths/patterns")
    args = ap.parse_args()

    try:
        manifest = load_json(args.manifest)
        scope = parse_scope_file(args.scope_file)
        from_version = args.from_version or scope.get("from_version")
        to_version = args.to_version or scope.get("to_version")
        courses = normalize_course_scope(args.courses) or normalize_course_scope(scope.get("courses"))
        _, summary = select_scoped_lessons(manifest.get("lessons", []), from_version, courses)
    except Exception as exc:
        print(f"INVALID: {exc}")
        sys.exit(1)

    print("VALID update scope")
    print(f"- from_version: {from_version}")
    print(f"- target_to_version_intent: {to_version}")
    print(f"- from_version_lesson_count: {summary['from_version_lesson_count']}")
    print(f"- matched_source_course_count: {summary['matched_source_course_count']}")
    print(f"- matched_source_lesson_count: {summary['matched_source_lesson_count']}")


if __name__ == "__main__":
    main()
