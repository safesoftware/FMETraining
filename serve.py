#!/usr/bin/env python3
"""
Local development server for FME Training Automation reports.

Extends Python's built-in HTTP server with a /api/save-lesson endpoint that:
  - Receives the cleaned lesson HTML + source lesson_dir + target to_version
  - Computes the correct target path (updating course folder version suffix)
  - Writes the HTML file and copies lesson images to the new location
  - Returns the target path on success; 409 if the file exists (unless force=True)

Usage:
    python serve.py [PORT]

Default port: 8080. Serve from project root, then open:
    http://localhost:8080/artifacts/report-{RUN_ID}.html
"""

from __future__ import annotations

import http.server
import json
import re
import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.resolve()

# Pattern to strip version suffix from a course folder name, e.g. " 2024.2"
_COURSE_VERSION_SUFFIX = re.compile(r"\s+\d{4}[\.\d]*$")


def _compute_target_path(lesson_dir: str, to_version: str) -> Path:
    """
    Compute the target lesson directory for the new version.

    lesson_dir example:
        2024.2/integrate-spatial-data/Analyze Spatial Data 2024.2/Exercise_ Analyze Spatial Data

    to_version example: 2026.1

    Returns Path to the target lesson directory (relative to repo root).
    """
    parts = Path(lesson_dir).parts
    if len(parts) < 4:
        raise ValueError(f"lesson_dir too shallow (expected 4 parts): {lesson_dir!r}")

    # parts[0] = source version, parts[1] = learning_path,
    # parts[2] = course folder (with old version suffix), parts[3] = lesson folder
    learning_path = parts[1]
    course_folder = parts[2]
    lesson_folder = "/".join(parts[3:])  # may be deeper than one level

    # Strip existing version suffix from course folder and re-append to_version
    course_canonical = _COURSE_VERSION_SUFFIX.sub("", course_folder).strip()
    new_course_folder = f"{course_canonical} {to_version}"

    return Path(to_version) / learning_path / new_course_folder / lesson_folder


class _Handler(http.server.SimpleHTTPRequestHandler):
    """HTTP handler that adds a /api/save-lesson POST endpoint."""

    def do_POST(self) -> None:  # noqa: N802
        if self.path == "/api/save-lesson":
            self._handle_save_lesson()
        else:
            self.send_error(404, "Not Found")

    def _handle_save_lesson(self) -> None:
        try:
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length))
        except Exception as exc:
            self._json_response(400, {"error": f"Bad request: {exc}"})
            return

        lesson_dir = body.get("lesson_dir", "").strip()
        to_version = body.get("to_version", "").strip()
        html_content = body.get("html_content", "")
        force = bool(body.get("force", False))

        if not lesson_dir or not to_version:
            self._json_response(400, {"error": "lesson_dir and to_version are required"})
            return

        try:
            target_dir = _compute_target_path(lesson_dir, to_version)
        except ValueError as exc:
            self._json_response(400, {"error": str(exc)})
            return

        target_file = REPO_ROOT / target_dir / "index.html"
        target_path_str = str(target_dir / "index.html").replace("\\", "/")

        if target_file.exists() and not force:
            self._json_response(409, {
                "error": "File already exists",
                "target_path": target_path_str,
                "exists": True,
            })
            return

        # Write the HTML file
        target_file.parent.mkdir(parents=True, exist_ok=True)
        target_file.write_text(html_content, encoding="utf-8")

        # Copy images from source lesson dir to target dir
        source_images = REPO_ROOT / lesson_dir / "images"
        if source_images.is_dir():
            target_images = REPO_ROOT / target_dir / "images"
            shutil.copytree(source_images, target_images, dirs_exist_ok=True)

        self._json_response(200, {"target_path": target_path_str})

    def _json_response(self, status: int, data: dict) -> None:
        body = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt: str, *args: object) -> None:  # noqa: N802
        # Suppress noisy GET request logs; keep POST logs
        if args and str(args[0]).startswith("POST"):
            super().log_message(fmt, *args)


def main() -> None:
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
    server = http.server.HTTPServer(("", port), _Handler)
    print(f"Serving from: {REPO_ROOT}")
    print(f"Open: http://localhost:{port}/artifacts/")
    print("Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()
