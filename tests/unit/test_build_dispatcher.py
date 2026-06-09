"""Tests for ``app.main._build_dispatcher`` (KNOW-2292).

After the 2026-05-05 EC2 deployment pivot, the only supported dispatcher
keys are ``stub``, ``in-process``, and ``systemd``. These tests pin that
contract and assert the helpful unknown-key error message.
"""
from __future__ import annotations

import pytest

from app.main import _build_dispatcher
from app.services.task_dispatcher import StubTaskDispatcher


def test_build_dispatcher_unknown_kind_lists_supported_values() -> None:
    """An unrecognised dispatcher key should raise ``ValueError`` whose
    message names the three supported values, so misconfigured deployments
    fail with a clear pointer instead of a cryptic stack trace."""
    with pytest.raises(ValueError) as exc_info:
        _build_dispatcher("banana", session_factory=None)  # type: ignore[arg-type]
    msg = str(exc_info.value)
    assert "stub" in msg
    assert "in-process" in msg
    assert "systemd" in msg


def test_build_dispatcher_legacy_ecs_value_raises_value_error() -> None:
    """The legacy ``ecs`` key (left over from the abandoned Fargate plan)
    is no longer special-cased post-KNOW-2292 and must fall through to the
    generic unknown-kind ValueError, naming the supported values."""
    with pytest.raises(ValueError) as exc_info:
        _build_dispatcher("ecs", session_factory=None)  # type: ignore[arg-type]
    msg = str(exc_info.value)
    assert "stub" in msg
    assert "in-process" in msg
    assert "systemd" in msg


def test_build_dispatcher_stub_returns_stub() -> None:
    """Sanity check that the happy path for the test dispatcher still
    works — guards against a regression while we're touching the helper."""
    dispatcher = _build_dispatcher("stub", session_factory=None)  # type: ignore[arg-type]
    assert isinstance(dispatcher, StubTaskDispatcher)
