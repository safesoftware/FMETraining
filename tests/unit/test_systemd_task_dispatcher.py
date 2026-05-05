"""Tests for SystemdTaskDispatcher.

The dispatcher shells out to ``systemctl --user start --no-block`` —
we don't actually want unit tests forking real subprocesses, so the
``runner`` parameter accepts an awaitable stub matching
``asyncio.create_subprocess_exec``'s signature.
"""
from __future__ import annotations

import asyncio
from typing import Any

import pytest

from app.services.task_dispatcher import SystemdTaskDispatcher


class _FakeProc:
    """Bare-minimum stand-in for ``asyncio.subprocess.Process``."""

    def __init__(self, returncode: int = 0, stdout: bytes = b"", stderr: bytes = b"") -> None:
        self.returncode = returncode
        self._stdout = stdout
        self._stderr = stderr

    async def communicate(self) -> tuple[bytes, bytes]:
        return self._stdout, self._stderr


class _RunnerSpy:
    """Records every call to the dispatcher's runner without spawning real procs."""

    def __init__(self, *, returncode: int = 0, stderr: bytes = b"") -> None:
        self.calls: list[tuple[Any, ...]] = []
        self._returncode = returncode
        self._stderr = stderr

    async def __call__(self, *argv: str, **kwargs: Any) -> _FakeProc:
        self.calls.append(argv)
        return _FakeProc(returncode=self._returncode, stderr=self._stderr)


# ---- happy path ---------------------------------------------------------

@pytest.mark.asyncio
async def test_dispatch_invokes_systemctl_with_unit_name() -> None:
    runner = _RunnerSpy()
    dispatcher = SystemdTaskDispatcher(runner=runner)

    result = await dispatcher.dispatch("20260505T120000-abcd")

    assert result == "fme-train-worker@20260505T120000-abcd.service"
    assert len(runner.calls) == 1
    argv = runner.calls[0]
    assert argv == (
        "systemctl",
        "--user",
        "start",
        "--no-block",
        "fme-train-worker@20260505T120000-abcd.service",
    )


@pytest.mark.asyncio
async def test_custom_unit_template_is_honoured() -> None:
    runner = _RunnerSpy()
    dispatcher = SystemdTaskDispatcher(
        unit_template="custom-worker@%s.service",
        runner=runner,
    )
    result = await dispatcher.dispatch("r-1")
    assert result == "custom-worker@r-1.service"
    assert runner.calls[0][-1] == "custom-worker@r-1.service"


@pytest.mark.asyncio
async def test_custom_command_prefix_is_honoured() -> None:
    """Lets the deploy override e.g. to use sudo + system-mode systemctl."""
    runner = _RunnerSpy()
    dispatcher = SystemdTaskDispatcher(
        command=("sudo", "systemctl", "start", "--no-block"),
        runner=runner,
    )
    await dispatcher.dispatch("r-1")
    argv = runner.calls[0]
    assert argv[:4] == ("sudo", "systemctl", "start", "--no-block")
    assert argv[4] == "fme-train-worker@r-1.service"


# ---- failure path -------------------------------------------------------

@pytest.mark.asyncio
async def test_nonzero_exit_raises_with_stderr_in_message() -> None:
    runner = _RunnerSpy(
        returncode=5,
        stderr=b"Failed to start fme-train-worker@r-1.service: Unit not found",
    )
    dispatcher = SystemdTaskDispatcher(runner=runner)

    with pytest.raises(RuntimeError) as exc_info:
        await dispatcher.dispatch("r-1")
    msg = str(exc_info.value)
    assert "exited 5" in msg
    assert "Unit not found" in msg


# ---- input validation ---------------------------------------------------

def test_unit_template_must_contain_format_marker() -> None:
    with pytest.raises(ValueError):
        SystemdTaskDispatcher(unit_template="no-format-marker")


# ---- integration with the abstract base --------------------------------

def test_systemd_dispatcher_is_a_task_dispatcher() -> None:
    """Catches the case where someone removes the abstract base accidentally."""
    from app.services.task_dispatcher import TaskDispatcher
    assert issubclass(SystemdTaskDispatcher, TaskDispatcher)
