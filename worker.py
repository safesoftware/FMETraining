"""Worker entrypoint. Run via ``python -m worker``.

The Dockerfile's ``docker/entrypoint.sh`` routes ``ENTRYPOINT_MODE=worker``
to this module. Reads ``RUN_ID``, ``MAX_RUN_USD``, ``RESUME`` from env;
delegates the lifecycle to :func:`app.services.worker_lifecycle.run_worker`.

Exit codes:
    0  — run finished (status=done, cancelled, or aborted_cost_ceiling)
    1  — run errored (status=error)
    2  — bad config (no RUN_ID, missing DATABASE_URL, etc.)
"""
from __future__ import annotations

import asyncio
import logging
import os
import sys

from app.db.engine import _get_or_create_session_factory
from app.services.worker_lifecycle import (
    TERMINAL_ERROR,
    run_worker,
)

_logger = logging.getLogger("worker")


def _parse_bool(raw: str | None) -> bool:
    return (raw or "").strip().lower() in {"1", "true", "yes", "on"}


def main() -> int:
    logging.basicConfig(
        level=os.environ.get("LOG_LEVEL", "INFO").upper(),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )

    run_id = os.environ.get("RUN_ID", "").strip()
    if not run_id:
        _logger.error("RUN_ID is required (env var)")
        return 2

    max_run_usd_raw = os.environ.get("MAX_RUN_USD")
    max_run_usd = float(max_run_usd_raw) if max_run_usd_raw else None
    resume = _parse_bool(os.environ.get("RESUME"))

    _logger.info(
        "Worker starting: run_id=%s resume=%s ceiling=%s",
        run_id,
        resume,
        max_run_usd,
    )

    try:
        session_factory = _get_or_create_session_factory()
    except RuntimeError as exc:
        # DATABASE_URL missing.
        _logger.error("Cannot start worker: %s", exc)
        return 2

    final_status = asyncio.run(
        run_worker(
            run_id,
            session_factory=session_factory,
            max_run_usd=max_run_usd,
            resume=resume,
        )
    )
    _logger.info("Worker exited with status=%s", final_status)

    if final_status == TERMINAL_ERROR:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
