"""Pytest wrapper for tests/test_deploy_script.sh — KNOW-2296.

The actual assertions live in the shell script (so an EC2 operator can run
it directly with `bash tests/test_deploy_script.sh`). This wrapper just
shells out so the smoke test runs as part of `python -m pytest tests/`.
"""

from __future__ import annotations

import pathlib
import shutil
import subprocess

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
SMOKE_SH = REPO_ROOT / "tests" / "test_deploy_script.sh"


@pytest.mark.skipif(
    shutil.which("bash") is None or shutil.which("git") is None,
    reason="bash and git are both required to build the throwaway deploy fixture",
)
def test_deploy_prod_dry_run_smoke() -> None:
    assert SMOKE_SH.exists(), f"smoke script missing: {SMOKE_SH}"
    result = subprocess.run(
        ["bash", str(SMOKE_SH)],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    if result.returncode != 0:
        pytest.fail(
            "deploy-prod.sh smoke test failed\n"
            f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )
    assert "deploy-prod.sh smoke test OK" in result.stdout
