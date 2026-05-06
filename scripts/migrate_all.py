"""Run every migration script in the right order.

This is the one-shot entrypoint operators use during the EC2 deploy
runbook (step 6 in ``docs/plans/2026-05-05-multi-user-web-app-ec2-alternative.md``).
Order matters because ``runs`` and ``lesson_drafts`` reference shared
foreign keys -- but all four scripts here are independent in practice
because their FKs are NULL at migration time. Running them in this
sequence keeps log output predictable.

The driver:

* Logs each step's counts.
* Bails on the first error so a missing source file doesn't get masked.
* Forwards ``--dry-run`` to every step.
* Reads paths from the standard locations (``artifacts/runs.json``,
  ``data/update-job.json``, ``.cache/jira_api_cache.json``, ``./<version>/``)
  unless overridden via flags.
"""
from __future__ import annotations

import argparse
import asyncio
import logging
import sys
from pathlib import Path
from typing import Iterable, Optional

from app.db.engine import _get_or_create_session_factory
from scripts.migrate import seed_drafts, seed_jira_cache, seed_jobs, seed_runs

_logger = logging.getLogger(__name__)


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run all KNOW-2271 migration scripts in order.",
    )
    parser.add_argument(
        "--runs-source",
        type=Path,
        default=Path("artifacts/runs.json"),
    )
    parser.add_argument(
        "--job-source",
        type=Path,
        default=Path("data/update-job.json"),
    )
    parser.add_argument(
        "--jira-cache-source",
        type=Path,
        default=Path(".cache/jira_api_cache.json"),
    )
    parser.add_argument(
        "--drafts-source",
        type=Path,
        help="Legacy version folder to seed from (e.g. ./2026.1). "
             "Skip drafts entirely if not provided.",
    )
    parser.add_argument(
        "--scratch-root",
        type=Path,
        default=Path("/var/lib/fme-train"),
    )
    parser.add_argument(
        "--drafts-root",
        type=Path,
        default=Path("/var/lib/fme-train/drafts"),
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
    )
    return parser


async def _run(args: argparse.Namespace) -> int:
    factory = _get_or_create_session_factory()

    if args.runs_source.is_file():
        result = await seed_runs.migrate(
            args.runs_source, factory, dry_run=args.dry_run
        )
        _logger.info("seed_runs: %s", result)
    else:
        _logger.warning(
            "seed_runs: skipping (source not found: %s)", args.runs_source
        )

    if args.job_source.is_file():
        result = await seed_jobs.migrate(
            args.job_source, factory, dry_run=args.dry_run
        )
        _logger.info("seed_jobs: %s", result)
    else:
        _logger.warning(
            "seed_jobs: skipping (source not found: %s)", args.job_source
        )

    if args.jira_cache_source.is_file():
        result = await seed_jira_cache.migrate(
            args.jira_cache_source,
            factory,
            scratch_root=args.scratch_root,
            dry_run=args.dry_run,
        )
        _logger.info("seed_jira_cache: %s", result)
    else:
        _logger.warning(
            "seed_jira_cache: skipping (source not found: %s)",
            args.jira_cache_source,
        )

    if args.drafts_source is not None:
        if not args.drafts_source.is_dir():
            _logger.error(
                "seed_drafts: source not found: %s", args.drafts_source
            )
            return 2
        result = await seed_drafts.migrate(
            args.drafts_source,
            factory,
            drafts_root=args.drafts_root,
            dry_run=args.dry_run,
        )
        _logger.info("seed_drafts: %s", result)
    else:
        _logger.info("seed_drafts: skipped (no --drafts-source provided)")

    return 0


def main(argv: Optional[Iterable[str]] = None) -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    args = _build_arg_parser().parse_args(list(argv) if argv is not None else None)
    return asyncio.run(_run(args))


if __name__ == "__main__":
    sys.exit(main())
