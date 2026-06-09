"""Structural tests for .github/workflows/deploy-prod.yml (KNOW-2293).

These tests don't run the workflow — they parse the YAML and assert the
contract that makes it safe to land:

* Both triggers (push to main + workflow_dispatch with a `ref` input) are
  wired correctly.
* Concurrency is set so two deploys can't race.
* All third-party actions (anything with `owner/repo@…` that isn't a
  re-usable workflow inside this repo) are pinned to a 40-char commit
  SHA, never a floating tag like `@v1` or `@main`.
* The DEPLOY_HOST guard exists and gates the SSH steps, so the workflow
  exits 0 cleanly when the secret isn't set (i.e. before EC2 lands).
* An `if: failure()` rollback step exists and invokes
  `bin/deploy-prod.sh --rollback`.

If any of these regress (e.g. someone bumps an action to a floating tag
in a hurry), CI fails before the change reaches prod.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

WORKFLOW_PATH = (
    Path(__file__).resolve().parents[1] / ".github" / "workflows" / "deploy-prod.yml"
)

# Match an exact 40-char lowercase hex git SHA.
SHA_RE = re.compile(r"^[a-f0-9]{40}$")


@pytest.fixture(scope="module")
def workflow() -> dict:
    """Parse the workflow YAML once per test module."""
    assert WORKFLOW_PATH.exists(), f"workflow file missing: {WORKFLOW_PATH}"
    with WORKFLOW_PATH.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    assert isinstance(data, dict), "workflow YAML must parse to a mapping"
    return data


def _on(workflow: dict) -> dict:
    """
    Return the `on:` block, regardless of whether PyYAML parsed it as the
    string "on" or the boolean True (YAML 1.1 treats `on` as truthy).
    """
    if "on" in workflow:
        return workflow["on"]
    if True in workflow:
        return workflow[True]
    raise AssertionError("workflow has no `on:` block")


def _all_steps(workflow: dict) -> list[dict]:
    """Flatten every step across every job."""
    steps: list[dict] = []
    for job in workflow.get("jobs", {}).values():
        steps.extend(job.get("steps", []) or [])
    return steps


def test_triggers_include_push_main_and_workflow_dispatch(workflow: dict) -> None:
    on = _on(workflow)
    assert "workflow_dispatch" in on, "missing workflow_dispatch trigger"
    assert "push" in on, "missing push trigger"
    branches = on["push"].get("branches") or []
    assert "main" in branches, f"push trigger must include main, got {branches!r}"


def test_workflow_dispatch_has_ref_input_with_main_default(workflow: dict) -> None:
    on = _on(workflow)
    inputs = (on["workflow_dispatch"] or {}).get("inputs") or {}
    assert "ref" in inputs, "workflow_dispatch must accept a `ref` input"
    assert inputs["ref"].get("default") == "main", (
        "default ref must be 'main' so a button-click with no input deploys main"
    )


def test_concurrency_serialises_deploys(workflow: dict) -> None:
    concurrency = workflow.get("concurrency")
    assert concurrency, "workflow must declare a concurrency block"
    assert concurrency.get("group") == "deploy-prod", (
        f"expected concurrency group 'deploy-prod', got {concurrency.get('group')!r}"
    )
    # Must be False — true would let a fresh push abort an in-flight deploy
    # mid-migration. We want the second one to wait, not stomp.
    assert concurrency.get("cancel-in-progress") is False, (
        "cancel-in-progress must be false so deploys serialise"
    )


def test_all_third_party_actions_pinned_to_sha(workflow: dict) -> None:
    """Every `uses: owner/repo@ref` must pin `ref` to a 40-char SHA."""
    offenders: list[str] = []
    for step in _all_steps(workflow):
        uses = step.get("uses")
        if not uses or "@" not in uses:
            continue
        # Skip same-repo reusable workflows / composite actions (they
        # start with "./" and don't have owner/repo@sha shape).
        if uses.startswith("./"):
            continue
        ref = uses.rsplit("@", 1)[1]
        if not SHA_RE.match(ref):
            offenders.append(uses)
    assert not offenders, (
        "third-party actions must be pinned to commit SHAs, found floating refs: "
        + ", ".join(offenders)
    )


def test_guard_step_gates_subsequent_steps(workflow: dict) -> None:
    """The DEPLOY_HOST guard must exist and at least one later step must depend on it."""
    steps = _all_steps(workflow)
    guard_steps = [s for s in steps if s.get("id") == "guard"]
    assert len(guard_steps) == 1, "expected exactly one step with id: guard"

    guard_run = guard_steps[0].get("run", "")
    assert "DEPLOY_HOST" in guard_run, "guard step must reference DEPLOY_HOST"
    assert "DEPLOY_HOST not set; skipping deploy" in guard_run, (
        "guard step must log the exact 'DEPLOY_HOST not set; skipping deploy' line"
    )
    assert "ok=true" in guard_run and "ok=false" in guard_run, (
        "guard step must set ok=true/ok=false on $GITHUB_OUTPUT"
    )

    gated = [
        s
        for s in steps
        if isinstance(s.get("if"), str) and "steps.guard.outputs.ok" in s["if"]
    ]
    assert gated, "no later step is gated on steps.guard.outputs.ok"


def test_rollback_step_runs_on_failure(workflow: dict) -> None:
    steps = _all_steps(workflow)
    failure_steps = [
        s for s in steps if isinstance(s.get("if"), str) and "failure()" in s["if"]
    ]
    assert failure_steps, "expected at least one step with `if: failure()`"

    rollback = failure_steps[-1]
    script = rollback.get("with", {}).get("script", "") if rollback.get("uses") else ""
    if not script:
        # Fallback for `run:`-style rollback steps.
        script = rollback.get("run", "")
    assert "--rollback" in script, (
        "the failure() step must invoke `bin/deploy-prod.sh --rollback` "
        "(KNOW-2296 contract)"
    )


def test_ssh_steps_use_required_secrets(workflow: dict) -> None:
    """Every SSH step must source host/user/key from the documented secrets."""
    ssh_steps = [
        s
        for s in _all_steps(workflow)
        if isinstance(s.get("uses"), str) and s["uses"].startswith("appleboy/ssh-action@")
    ]
    assert ssh_steps, "expected at least one appleboy/ssh-action step"
    for step in ssh_steps:
        with_block = step.get("with", {})
        for key, secret in (
            ("host", "DEPLOY_HOST"),
            ("username", "DEPLOY_USER"),
            ("key", "DEPLOY_SSH_KEY"),
        ):
            value = with_block.get(key, "")
            assert f"secrets.{secret}" in value, (
                f"SSH step '{step.get('name')!r}' must wire `{key}` to "
                f"secrets.{secret}, got {value!r}"
            )
