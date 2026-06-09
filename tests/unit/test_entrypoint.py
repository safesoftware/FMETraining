"""Regression tests for docker/entrypoint.sh (KNOW-2263).

The container entrypoint must:

  (a) honor an explicit command passed to the container, so
      ``docker compose run app <cmd>`` — i.e. ``make migrate`` / ``make test`` /
      ``make lint`` / ``make format`` — actually runs ``<cmd>``; and
  (b) fall back to the ENTRYPOINT_MODE dispatch (web|worker) when no command
      is given (the path used by ``app`` and ``worker-runner``).

A prior version ignored ``"$@"`` entirely and always launched uvicorn, which
silently turned every ``docker compose run app <cmd>`` target into "start the
web server" — migrate/test/lint/format never executed.

These tests run the script directly with fake ``uvicorn``/``python`` shims on
PATH, so they assert which branch executed without needing a built image.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
ENTRYPOINT = REPO_ROOT / "docker" / "entrypoint.sh"


def _run(args, mode, tmp_path):
    """Run entrypoint.sh with stubbed uvicorn/python on PATH.

    The shims echo a marker and exit 0 so we can tell from stdout which code
    path the entrypoint took.
    """
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    (bin_dir / "uvicorn").write_text('#!/usr/bin/env bash\necho UVICORN_RAN "$@"\n')
    (bin_dir / "python").write_text('#!/usr/bin/env bash\necho PYTHON "$@"\n')
    for shim in bin_dir.iterdir():
        shim.chmod(0o755)

    env = dict(os.environ, PATH=f"{bin_dir}:{os.environ['PATH']}")
    if mode is not None:
        env["ENTRYPOINT_MODE"] = mode
    else:
        env.pop("ENTRYPOINT_MODE", None)

    return subprocess.run(
        ["bash", str(ENTRYPOINT), *args],
        capture_output=True,
        text=True,
        env=env,
        timeout=30,
    )


def test_explicit_command_is_executed(tmp_path):
    # Regression: a passed command must run; it must NOT be swallowed by the
    # default web-mode dispatch.
    result = _run(["/bin/echo", "ARG_EXEC_WORKS"], mode="web", tmp_path=tmp_path)
    assert result.returncode == 0, result.stderr
    assert "ARG_EXEC_WORKS" in result.stdout
    assert "UVICORN_RAN" not in result.stdout


def test_web_mode_starts_uvicorn_when_no_command(tmp_path):
    result = _run([], mode="web", tmp_path=tmp_path)
    assert result.returncode == 0, result.stderr
    assert "UVICORN_RAN" in result.stdout


def test_worker_mode_runs_worker_when_no_command(tmp_path):
    result = _run([], mode="worker", tmp_path=tmp_path)
    assert result.returncode == 0, result.stderr
    assert "-m worker" in result.stdout


def test_unknown_mode_exits_64(tmp_path):
    result = _run([], mode="bogus", tmp_path=tmp_path)
    assert result.returncode == 64
