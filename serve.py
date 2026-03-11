#!/usr/bin/env python3
"""
Local development server for FME Training Automation.

Serves static files from the project root and provides API endpoints:

  GET  /                           → launcher.html (browser UI)
  GET  /api/versions               → list of version folders
  GET  /api/content-tree?version=  → LP/course/lesson tree for a version
  GET  /api/runs                   → run history from artifacts/runs.json
  GET  /api/run-log?run_id=        → SSE stream of pipeline output
  POST /api/start-run              → write update-job.json + spawn pipeline
  POST /api/run-action             → regenerate-report / edit-suggestions / resume
  POST /api/save-lesson            → write accepted lesson edits to disk

Usage:
    python serve.py [PORT]          # default port: 8080
"""

from __future__ import annotations

import http.server
import json
import re
import shutil
import socketserver
import subprocess
import sys
import threading
import time
import urllib.parse
from pathlib import Path

REPO_ROOT = Path(__file__).parent.resolve()

_COURSE_VERSION_SUFFIX = re.compile(r"\s+\d{4}[\.\d]*$")
_VERSION_RE = re.compile(r"^\d{4}\.\d+$")

# ---------------------------------------------------------------------------
# Run process management
# ---------------------------------------------------------------------------

_active_runs: dict[str, dict] = {}   # key → {"process", "log", "status"}
_runs_lock = threading.Lock()


def _read_process_output(key: str) -> None:
    """Background thread: drain subprocess stdout into the log buffer."""
    with _runs_lock:
        entry = _active_runs.get(key)
    if not entry:
        return
    proc = entry["process"]
    try:
        for raw in proc.stdout:
            line = raw.rstrip("\n").rstrip("\r")
            with _runs_lock:
                entry["log"].append(line)
        proc.wait()
        with _runs_lock:
            entry["status"] = "done" if proc.returncode == 0 else "error"
    except Exception as exc:
        with _runs_lock:
            entry["log"].append(f"[server error reading output: {exc}]")
            entry["status"] = "error"


# ---------------------------------------------------------------------------
# Content tree builder
# ---------------------------------------------------------------------------

def _build_content_tree(version: str) -> list:
    version_dir = REPO_ROOT / version
    if not version_dir.is_dir():
        return []
    tree = []
    for lp_dir in sorted(version_dir.iterdir()):
        if not lp_dir.is_dir():
            continue
        lp_label = lp_dir.name.replace("-", " ").title()
        courses = []
        for course_dir in sorted(lp_dir.iterdir()):
            if not course_dir.is_dir():
                continue
            course_canonical = _COURSE_VERSION_SUFFIX.sub("", course_dir.name).strip()
            lessons = []
            for lesson_dir in sorted(course_dir.iterdir()):
                if not lesson_dir.is_dir():
                    continue
                if not (lesson_dir / "index.html").exists():
                    continue
                path = "/".join([
                    version, lp_dir.name, course_dir.name, lesson_dir.name, "index.html"
                ])
                label = lesson_dir.name.replace("_", " ").strip()
                lessons.append({"id": lesson_dir.name, "label": label, "path": path})
            if lessons:
                courses.append({
                    "id": course_canonical,
                    "label": course_canonical,
                    "lessons": lessons,
                })
        if courses:
            tree.append({
                "id": lp_dir.name,
                "label": lp_label,
                "courses": courses,
            })
    return tree


# ---------------------------------------------------------------------------
# HTTP server
# ---------------------------------------------------------------------------

class _ThreadedHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True


class _Handler(http.server.SimpleHTTPRequestHandler):

    # -- Routing -----------------------------------------------------------

    def do_GET(self) -> None:  # noqa: N802
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        qs = urllib.parse.parse_qs(parsed.query)

        if path in ("/", "/index.html"):
            self._serve_launcher()
        elif path == "/api/versions":
            self._api_versions()
        elif path == "/api/content-tree":
            self._api_content_tree(qs)
        elif path == "/api/runs":
            self._api_runs()
        elif path == "/api/run-log":
            self._api_run_log(qs)
        else:
            super().do_GET()

    def do_POST(self) -> None:  # noqa: N802
        path = urllib.parse.urlparse(self.path).path
        if path == "/api/save-lesson":
            self._handle_save_lesson()
        elif path == "/api/start-run":
            self._api_start_run()
        elif path == "/api/run-action":
            self._api_run_action()
        else:
            self.send_error(404, "Not Found")

    # -- Launcher ----------------------------------------------------------

    def _serve_launcher(self) -> None:
        launcher = REPO_ROOT / "launcher.html"
        if not launcher.exists():
            self.send_error(404, "launcher.html not found")
            return
        content = launcher.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    # -- API: content discovery --------------------------------------------

    def _api_versions(self) -> None:
        versions = sorted(
            [d.name for d in REPO_ROOT.iterdir() if d.is_dir() and _VERSION_RE.match(d.name)],
            key=lambda v: [int(x) for x in v.split(".")],
            reverse=True,
        )
        self._json_response(200, versions)

    def _api_content_tree(self, qs: dict) -> None:
        version = (qs.get("version") or [None])[0]
        if not version or not _VERSION_RE.match(version):
            self._json_response(400, {"error": "valid version parameter required"})
            return
        self._json_response(200, _build_content_tree(version))

    # -- API: run history --------------------------------------------------

    def _api_runs(self) -> None:
        runs_path = REPO_ROOT / "artifacts" / "runs.json"
        if not runs_path.exists():
            self._json_response(200, {"runs": []})
            return
        with open(runs_path, encoding="utf-8") as f:
            data = json.load(f)
        with _runs_lock:
            for run in data.get("runs", []):
                entry = _active_runs.get(run["run_id"])
                if entry:
                    run["live_status"] = entry["status"]
        self._json_response(200, data)

    # -- API: SSE log stream -----------------------------------------------

    def _api_run_log(self, qs: dict) -> None:
        key = (qs.get("run_id") or [None])[0]
        if not key:
            self._json_response(400, {"error": "run_id required"})
            return
        with _runs_lock:
            entry = _active_runs.get(key)
        if not entry:
            self._json_response(404, {"error": f"No log for key: {key}"})
            return

        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("X-Accel-Buffering", "no")
        self.end_headers()

        idx = 0
        try:
            while True:
                with _runs_lock:
                    new_lines = entry["log"][idx:]
                    is_done = entry["status"] != "running"
                for line in new_lines:
                    self.wfile.write(f"data: {json.dumps(line)}\n\n".encode())
                self.wfile.flush()
                idx += len(new_lines)
                if is_done:
                    if not new_lines:
                        self.wfile.write(b"event: done\ndata: \n\n")
                        self.wfile.flush()
                        break
                else:
                    time.sleep(0.2)
        except (BrokenPipeError, ConnectionResetError):
            pass  # client disconnected

    # -- API: start run ----------------------------------------------------

    def _api_start_run(self) -> None:
        try:
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length))
        except Exception as exc:
            self._json_response(400, {"error": f"Bad request: {exc}"})
            return

        to_version = body.get("to_version", "").strip()
        scope = body.get("scope", {})
        options = body.get("options", {})

        if not to_version:
            self._json_response(400, {"error": "to_version is required"})
            return

        job = {"to_version": to_version, "scope": scope}
        try:
            job_path = REPO_ROOT / "data" / "update-job.json"
            job_path.write_text(json.dumps(job, indent=2), encoding="utf-8")
        except Exception as exc:
            self._json_response(500, {"error": f"Could not write update-job.json: {exc}"})
            return

        cmd = [sys.executable, "-u", str(REPO_ROOT / "pipeline.py")]
        jira_source = options.get("jira_source", "csv")
        if jira_source == "api":
            cmd += ["--jira-source", "api"]
            if options.get("refresh_jira"):
                cmd.append("--refresh-jira")
        if options.get("dry_run"):
            cmd.append("--dry-run")
        steps = options.get("steps")
        if steps:
            cmd += ["--steps", steps]
        resume = options.get("resume")
        if resume:
            cmd += ["--resume", resume]

        try:
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                cwd=str(REPO_ROOT),
            )
        except Exception as exc:
            self._json_response(500, {"error": f"Failed to start pipeline: {exc}"})
            return

        # Read output until "Run ID: <id>" appears
        run_id = None
        initial_lines: list[str] = []
        for _ in range(50):
            raw = proc.stdout.readline()
            if not raw:
                break
            line = raw.rstrip("\n").rstrip("\r")
            initial_lines.append(line)
            m = re.search(r"Run ID:\s*(\S+)", line)
            if m:
                run_id = m.group(1)
                break

        if not run_id:
            proc.terminate()
            self._json_response(500, {
                "error": "Could not determine run ID from pipeline output.",
                "output": "\n".join(initial_lines),
            })
            return

        with _runs_lock:
            _active_runs[run_id] = {
                "process": proc,
                "log": list(initial_lines),
                "status": "running",
            }
        threading.Thread(
            target=_read_process_output, args=(run_id,), daemon=True
        ).start()

        self._json_response(200, {"run_id": run_id})

    # -- API: run action ---------------------------------------------------

    def _api_run_action(self) -> None:
        try:
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length))
        except Exception as exc:
            self._json_response(400, {"error": f"Bad request: {exc}"})
            return

        run_id = body.get("run_id", "").strip()
        action = body.get("action", "").strip()
        if not run_id or not action:
            self._json_response(400, {"error": "run_id and action are required"})
            return

        cmd = [sys.executable, "-u", str(REPO_ROOT / "pipeline.py")]
        if action == "regenerate-report":
            cmd += ["--report-only", run_id]
        elif action == "edit-suggestions":
            cmd += ["--steps", "6", "--resume", run_id]
        elif action == "resume":
            cmd += ["--resume", run_id]
        else:
            self._json_response(400, {"error": f"Unknown action: {action}"})
            return

        try:
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                cwd=str(REPO_ROOT),
            )
        except Exception as exc:
            self._json_response(500, {"error": f"Failed to start process: {exc}"})
            return

        action_key = f"{run_id}:{action}"
        with _runs_lock:
            _active_runs[action_key] = {
                "process": proc,
                "log": [],
                "status": "running",
            }
        threading.Thread(
            target=_read_process_output, args=(action_key,), daemon=True
        ).start()

        self._json_response(200, {"action_key": action_key})

    # -- Existing: save lesson ---------------------------------------------

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

        target_file.parent.mkdir(parents=True, exist_ok=True)
        target_file.write_text(html_content, encoding="utf-8")

        source_images = REPO_ROOT / lesson_dir / "images"
        if source_images.is_dir():
            target_images = REPO_ROOT / target_dir / "images"
            shutil.copytree(source_images, target_images, dirs_exist_ok=True)

        self._json_response(200, {"target_path": target_path_str})

    # -- Utility -----------------------------------------------------------

    def _json_response(self, status: int, data: object) -> None:
        body = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt: str, *args: object) -> None:  # noqa: N802
        if args and str(args[0]).startswith("POST"):
            super().log_message(fmt, *args)


# ---------------------------------------------------------------------------
# Path computation (for save-lesson)
# ---------------------------------------------------------------------------

def _compute_target_path(lesson_dir: str, to_version: str) -> Path:
    parts = Path(lesson_dir).parts
    if len(parts) < 4:
        raise ValueError(f"lesson_dir too shallow (expected 4 parts): {lesson_dir!r}")
    learning_path = parts[1]
    course_folder = parts[2]
    lesson_folder = "/".join(parts[3:])
    course_canonical = _COURSE_VERSION_SUFFIX.sub("", course_folder).strip()
    new_course_folder = f"{course_canonical} {to_version}"
    return Path(to_version) / learning_path / new_course_folder / lesson_folder


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
    server = _ThreadedHTTPServer(("", port), _Handler)
    print(f"Serving from: {REPO_ROOT}")
    print(f"Open:  http://localhost:{port}/")
    print("Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()
