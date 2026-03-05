#!/usr/bin/env python3
"""
FME Training Update Automation Pipeline — CLI Entry Point

Usage:
  python pipeline.py                          # Full run using data/update-job.json
  python pipeline.py --dry-run               # Show scope + pair counts, no API calls
  python pipeline.py --steps 1,2            # Run only steps 1 and 2
  python pipeline.py --resume <RUN_ID>       # Resume an interrupted run
  python pipeline.py --report-only <RUN_ID>  # Regenerate HTML report only
  python pipeline.py --job path/to/job.json  # Use a custom job file
  python pipeline.py --jira-source api       # Fetch issues from Jira API (uses cache)
  python pipeline.py --jira-source api --refresh-jira  # Force re-fetch from Jira API
  python pipeline.py --steps 6 --resume <RUN_ID>       # Generate edit suggestions for an existing run
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from pipeline import config
from pipeline.config import UPDATE_JOB_PATH, get_artifacts_dir
from pipeline.utils import (
    edit_plans_path,
    generate_run_id,
    get_completed_steps,
    get_run_job,
    manifest_path,
    changelog_path,
    recommendations_path,
    mark_step_complete,
    register_run,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="FME Training Update Automation Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--job",
        type=Path,
        default=None,
        metavar="PATH",
        help="Path to update-job.json (default: data/update-job.json)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show scope + pair counts without making API calls or writing files",
    )
    parser.add_argument(
        "--steps",
        type=str,
        default="1,2,3,4,5",
        metavar="N[,N]",
        help="Comma-separated step numbers to run (default: 1,2,3,4,5). "
             "Steps 3 and 4 are always run together. Step 6 generates edit suggestions.",
    )
    parser.add_argument(
        "--resume",
        type=str,
        default=None,
        metavar="RUN_ID",
        help="Resume an interrupted run by run ID (skips already-completed steps)",
    )
    parser.add_argument(
        "--report-only",
        type=str,
        default=None,
        metavar="RUN_ID",
        help="Regenerate the HTML report for an existing run (no other steps run)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        metavar="PATH",
        help="Override the artifacts output directory (default: ./artifacts)",
    )
    parser.add_argument(
        "--jira-source",
        choices=["csv", "api"],
        default="csv",
        help="Source for Jira issues: 'csv' (default) reads inputs/jira_export.csv; "
             "'api' fetches from the Jira REST API using credentials in .env",
    )
    parser.add_argument(
        "--refresh-jira",
        action="store_true",
        help="When --jira-source api is set, force a fresh fetch from the Jira API "
             "even if a local cache (inputs/jira_api_cache.json) already exists",
    )

    args = parser.parse_args()

    # Validate mutually exclusive flags
    if args.resume and args.report_only:
        parser.error("--resume and --report-only cannot be used together.")

    output_dir = get_artifacts_dir(args.output_dir)

    # ---------------------------------------------------------------------------
    # --report-only: regenerate report for an existing run and exit
    # ---------------------------------------------------------------------------
    if args.report_only:
        from pipeline.report import build_report
        ep = edit_plans_path(args.report_only, output_dir)
        try:
            build_report(
                args.report_only, output_dir,
                edit_plans_path=ep if ep.exists() else None,
            )
        except FileNotFoundError as e:
            print(f"ERROR: {e}", file=sys.stderr)
            return 1
        return 0

    # ---------------------------------------------------------------------------
    # Determine steps to run
    # ---------------------------------------------------------------------------
    try:
        requested_steps = _parse_steps(args.steps)
    except ValueError as e:
        parser.error(str(e))

    # ---------------------------------------------------------------------------
    # Load job file
    # ---------------------------------------------------------------------------
    job_path = args.job or UPDATE_JOB_PATH
    if not job_path.exists():
        print(f"ERROR: Job file not found: {job_path}", file=sys.stderr)
        print("Create or update data/update-job.json before running.", file=sys.stderr)
        return 1

    with open(job_path, encoding="utf-8") as f:
        job = json.load(f)

    _validate_job(job)

    # ---------------------------------------------------------------------------
    # Determine run_id
    # ---------------------------------------------------------------------------
    if args.resume:
        run_id = args.resume
        completed = get_completed_steps(run_id, output_dir)
        if not completed and not _run_exists(run_id, output_dir):
            print(f"ERROR: Run ID '{run_id}' not found in runs.json.", file=sys.stderr)
            return 1
        steps_to_run = [s for s in requested_steps if s not in completed]
        if not steps_to_run:
            print(f"Run {run_id} is already complete (steps: {completed}).")
            return 0
        print(f"Resuming run {run_id} — completed: {completed}, remaining: {steps_to_run}")
    else:
        run_id = generate_run_id()
        steps_to_run = requested_steps
        if not args.dry_run:
            register_run(run_id, job, output_dir)
        print(f"Run ID: {run_id}")

    print(f"Steps to run: {steps_to_run}")
    if args.dry_run:
        print("Mode: DRY RUN (no API calls, no files written)\n")

    repo_root = config.REPO_ROOT

    # ---------------------------------------------------------------------------
    # Step 1: Build manifest
    # ---------------------------------------------------------------------------
    if 1 in steps_to_run:
        from pipeline.manifest import build_manifest
        manifest = build_manifest(run_id, job, repo_root, output_dir, dry_run=args.dry_run)
        if not args.dry_run:
            mark_step_complete(run_id, 1, output_dir)
    else:
        # Load existing manifest for downstream steps
        mp = manifest_path(run_id, output_dir)
        if not mp.exists():
            print(f"ERROR: Manifest not found for run {run_id}: {mp}", file=sys.stderr)
            print("Run step 1 first, or use --resume.", file=sys.stderr)
            return 1
        with open(mp, encoding="utf-8") as f:
            manifest = json.load(f)
        print(f"\n[Step 1] Using existing manifest: {mp.name}")

    # ---------------------------------------------------------------------------
    # Step 2: Build changelog
    # ---------------------------------------------------------------------------
    if 2 in steps_to_run:
        from pipeline.changelog import build_changelog
        changelog = build_changelog(
            run_id, manifest, output_dir,
            dry_run=args.dry_run,
            jira_source=args.jira_source,
            refresh_jira=args.refresh_jira,
        )
        if not args.dry_run:
            mark_step_complete(run_id, 2, output_dir)
    else:
        cp = changelog_path(run_id, output_dir)
        if not cp.exists() and (3 in steps_to_run or 4 in steps_to_run):
            print(f"ERROR: Changelog not found for run {run_id}: {cp}", file=sys.stderr)
            return 1
        if cp.exists():
            with open(cp, encoding="utf-8") as f:
                changelog = json.load(f)
            print(f"\n[Step 2] Using existing changelog: {cp.name}")
        else:
            changelog = {"issues": []}

    # ---------------------------------------------------------------------------
    # Steps 3+4: Assessment (always run together)
    # ---------------------------------------------------------------------------
    run_assessment = 3 in steps_to_run or 4 in steps_to_run
    if run_assessment:
        from pipeline.assessment import run_assessment as do_assessment
        recs = do_assessment(run_id, manifest, changelog, output_dir, dry_run=args.dry_run)
        if not args.dry_run:
            mark_step_complete(run_id, 3, output_dir)
            mark_step_complete(run_id, 4, output_dir)
    else:
        rp = recommendations_path(run_id, output_dir)
        if rp.exists():
            with open(rp, encoding="utf-8") as f:
                recs = json.load(f)
            print(f"\n[Steps 3+4] Using existing recommendations: {rp.name}")
        else:
            recs = None

    # ---------------------------------------------------------------------------
    # Step 6: Edit suggestions (per-lesson LLM edit plans)
    # ---------------------------------------------------------------------------
    if 6 in steps_to_run:
        from pipeline.edit_suggestions import run_edit_suggestions
        if recs is None:
            rp = recommendations_path(run_id, output_dir)
            if not rp.exists():
                print(f"ERROR: Recommendations not found for run {run_id}: {rp}", file=sys.stderr)
                print("Run steps 3+4 first.", file=sys.stderr)
                return 1
            with open(rp, encoding="utf-8") as f:
                recs = json.load(f)
        run_edit_suggestions(run_id, recs, output_dir, dry_run=args.dry_run)
        if not args.dry_run:
            mark_step_complete(run_id, 6, output_dir)

    # ---------------------------------------------------------------------------
    # Step 5: Report
    # ---------------------------------------------------------------------------
    if 5 in steps_to_run and not args.dry_run:
        from pipeline.report import build_report
        rp = recommendations_path(run_id, output_dir)
        ep = edit_plans_path(run_id, output_dir)
        if not rp.exists():
            print("WARNING: No recommendations file found, skipping report generation.")
        else:
            build_report(
                run_id, output_dir,
                recs_path=rp,
                edit_plans_path=ep if ep.exists() else None,
            )
            mark_step_complete(run_id, 5, output_dir)

    print(f"\nDone. Run ID: {run_id}")
    if not args.dry_run:
        print(f"Artifacts: {output_dir}")
    return 0


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parse_steps(steps_str: str) -> list[int]:
    """Parse '1,2,3,4,5' into [1, 2, 3, 4, 5]."""
    try:
        steps = [int(s.strip()) for s in steps_str.split(",") if s.strip()]
    except ValueError:
        raise ValueError(f"Invalid --steps value: {steps_str!r}. Expected comma-separated integers.")
    invalid = [s for s in steps if s not in {1, 2, 3, 4, 5, 6}]
    if invalid:
        raise ValueError(f"Invalid step number(s): {invalid}. Valid steps are 1-6.")
    return sorted(set(steps))


def _validate_job(job: dict) -> None:
    """Basic validation of the job JSON structure."""
    if "to_version" not in job:
        print("ERROR: update-job.json is missing 'to_version'.", file=sys.stderr)
        sys.exit(1)
    if "scope" not in job:
        print("ERROR: update-job.json is missing 'scope'.", file=sys.stderr)
        sys.exit(1)
    scope = job["scope"]
    if not isinstance(scope, dict):
        print("ERROR: 'scope' in update-job.json must be an object.", file=sys.stderr)
        sys.exit(1)


def _run_exists(run_id: str, output_dir: Path) -> bool:
    """Check if a run_id exists in runs.json."""
    runs_path = output_dir / "runs.json"
    if not runs_path.exists():
        return False
    try:
        with open(runs_path, encoding="utf-8") as f:
            data = json.load(f)
        return any(r["run_id"] == run_id for r in data.get("runs", []))
    except Exception:
        return False


if __name__ == "__main__":
    sys.exit(main())
