"""Pluggable task dispatcher used by the run scheduler.

Plan section 3 calls for the API to ``boto3.client("ecs").run_task()`` per
queued run. To keep the scheduler unit-testable and dev-friendly, the
dispatch step lives behind this abstraction with three concrete forms:

- :class:`StubTaskDispatcher`     — records dispatched run_ids; tests use this.
- :class:`InProcessTaskDispatcher` — runs the worker as an in-process asyncio
                                     task. Local dev default.
- :class:`EcsRunTaskDispatcher`    — boto3 ``run_task``. Production default.
                                     Skeleton today; filled in once we have
                                     the deployed Fargate cluster + task def.

Choose at startup time via ``Settings.task_dispatcher``.
"""
from __future__ import annotations

import abc
import asyncio
import logging
from typing import Any, Awaitable, Callable

_logger = logging.getLogger(__name__)


class TaskDispatcher(abc.ABC):
    """A scheduler-side interface for spawning a worker for a given run_id."""

    @abc.abstractmethod
    async def dispatch(self, run_id: str) -> str:
        """Spawn a worker for ``run_id``. Return a task handle (e.g. ECS task
        ARN, in-process task name) that gets persisted to ``runs.fargate_task_arn``.

        Implementations must be safe to call from the scheduler's loop and
        must not block the loop on long-running I/O.
        """


# ---------------------------------------------------------------------------
# Stub (tests)
# ---------------------------------------------------------------------------

class StubTaskDispatcher(TaskDispatcher):
    """Records calls without doing anything. Tests inspect ``.dispatched``."""

    def __init__(self) -> None:
        self.dispatched: list[str] = []

    async def dispatch(self, run_id: str) -> str:
        self.dispatched.append(run_id)
        return f"stub:{run_id}"


# ---------------------------------------------------------------------------
# In-process (local dev)
# ---------------------------------------------------------------------------

class InProcessTaskDispatcher(TaskDispatcher):
    """Runs ``worker_callable(run_id)`` as a fire-and-forget asyncio task.

    Useful for ``docker compose up`` style local development where there's
    no real ECS cluster to dispatch against. The worker still uses the same
    DB and S3 (or MinIO) the API does, so the integration is real apart
    from the cross-process boundary.

    The dispatcher does not await the worker; the scheduler relies on the
    worker writing ``runs.status`` transitions for visibility.
    """

    def __init__(
        self,
        worker_callable: Callable[[str], Awaitable[Any]],
    ) -> None:
        self._worker_callable = worker_callable
        # Hold on to spawned tasks so they don't get GC'd mid-run.
        # Tasks are cleaned out on completion via the done callback.
        self._spawned: set[asyncio.Task] = set()

    async def dispatch(self, run_id: str) -> str:
        task_name = f"in-process-worker:{run_id}"
        task = asyncio.create_task(self._worker_callable(run_id), name=task_name)
        self._spawned.add(task)
        task.add_done_callback(self._on_task_done)
        return task_name

    def _on_task_done(self, task: asyncio.Task) -> None:
        """Drop the task from the spawn set AND surface exceptions.

        ``run_worker`` already updates ``runs.status`` from its own
        ``finally`` block, so the DB record is correct even when this
        callback runs. What we don't want is the task's exception getting
        silently dropped on the floor — that hides bugs in the dispatcher
        wiring or the worker callable itself.
        """
        self._spawned.discard(task)
        if task.cancelled():
            return
        exc = task.exception()
        if exc is not None:
            _logger.error(
                "In-process worker task %r ended with %s: %s",
                task.get_name(),
                type(exc).__name__,
                exc,
                exc_info=(type(exc), exc, exc.__traceback__),
            )


# ---------------------------------------------------------------------------
# systemd (production — single-EC2 deployment)
# ---------------------------------------------------------------------------

class SystemdTaskDispatcher(TaskDispatcher):
    """Production dispatcher for the single-EC2 deployment shape.

    Each pipeline run spawns a fresh systemd user-mode service via the
    template unit ``fme-train-worker@<run_id>.service``. The unit reads
    ``EnvironmentFile=/etc/fme-train/env`` for shared secrets and gets
    ``RUN_ID=<run_id>`` injected via the systemd ``%i`` instance specifier.

    The dispatcher itself doesn't run as root — it shells out to
    ``systemctl --user start --no-block`` against the same user systemd
    manager that runs the FastAPI app. Lingering must be enabled for the
    app user (``loginctl enable-linger fmetrain``) so user-mode systemd
    survives logout and starts at boot.

    Args:
      unit_template: systemd template unit name with ``%s`` where the
        run_id goes. Default: ``fme-train-worker@%s.service``.
      command: list of argv tokens to invoke. The dispatcher appends the
        formatted unit name. Default: systemctl user-mode start.
      runner: async-callable matching ``asyncio.create_subprocess_exec``'s
        signature. Defaults to the real subprocess module; tests inject a
        stub so they don't actually fork systemctl.

    See ``docs/plans/2026-05-05-multi-user-web-app-ec2-alternative.md``
    for the broader deployment context.
    """

    def __init__(
        self,
        *,
        unit_template: str = "fme-train-worker@%s.service",
        command: tuple[str, ...] = ("systemctl", "--user", "start", "--no-block"),
        runner: Callable[..., Awaitable[Any]] | None = None,
    ) -> None:
        if "%s" not in unit_template:
            raise ValueError("unit_template must contain '%s' for the run_id")
        self._unit_template = unit_template
        self._command = tuple(command)
        self._runner = runner or asyncio.create_subprocess_exec

    async def dispatch(self, run_id: str) -> str:
        unit_name = self._unit_template % (run_id,)
        argv = (*self._command, unit_name)
        proc = await self._runner(
            *argv,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        if proc.returncode != 0:
            raise RuntimeError(
                f"systemctl exited {proc.returncode} for {unit_name}: "
                f"stderr={stderr.decode(errors='replace').strip()!r}"
            )
        _logger.info("Started systemd unit %s for run %s", unit_name, run_id)
        return unit_name
