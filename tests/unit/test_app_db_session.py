"""Tests for the ``app.db.session.get_session`` FastAPI dependency.

These prove the dependency:
- yields a working ``AsyncSession`` to its caller
- ``commit()`` runs on normal completion
- ``rollback()`` runs when the caller raises
- ``close()`` runs in either case

The session factory is patched to a stub so no real database is required.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.db import session as session_module
from app.db.session import get_session


def _stub_session_factory(monkeypatch: pytest.MonkeyPatch) -> AsyncMock:
    """Patch the module-level factory and return the AsyncSession mock."""
    stub_session = AsyncMock(name="AsyncSession")
    stub_session.commit = AsyncMock()
    stub_session.rollback = AsyncMock()
    stub_session.close = AsyncMock()

    factory = MagicMock(return_value=stub_session)
    monkeypatch.setattr(
        session_module,
        "_get_or_create_session_factory",
        lambda: factory,
    )
    return stub_session


@pytest.mark.asyncio
async def test_get_session_yields_then_commits(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    stub = _stub_session_factory(monkeypatch)
    gen = get_session()
    yielded = await gen.__anext__()
    assert yielded is stub

    # Drive the generator to completion (StopAsyncIteration signals end).
    with pytest.raises(StopAsyncIteration):
        await gen.__anext__()

    stub.commit.assert_awaited_once()
    stub.rollback.assert_not_awaited()
    stub.close.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_session_rolls_back_on_caller_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    stub = _stub_session_factory(monkeypatch)
    gen = get_session()
    await gen.__anext__()  # caller now "has" the session

    boom = RuntimeError("caller failed")
    with pytest.raises(RuntimeError):
        await gen.athrow(boom)

    stub.rollback.assert_awaited_once()
    stub.commit.assert_not_awaited()
    stub.close.assert_awaited_once()


def test_get_session_works_through_fastapi_depends(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """End-to-end: FastAPI's Depends() must iterate the async-yield
    dependency correctly, hand the route a real session object, and run
    the post-yield ``commit()`` after the response.

    This test is intentionally synchronous: ``TestClient`` is a sync
    client (it spins its own event loop internally), and calling it
    from an already-running ``async def`` test under pytest-asyncio is
    fragile across asyncio backends.
    """
    pytest.importorskip("fastapi")
    pytest.importorskip("httpx")

    from fastapi import Depends, FastAPI
    from fastapi.testclient import TestClient

    stub = _stub_session_factory(monkeypatch)

    app = FastAPI()

    @app.get("/probe")
    async def probe(session=Depends(get_session)) -> dict:
        # If FastAPI passed us the generator object instead of the
        # yielded value, this attribute lookup would hit the generator's
        # attributes — `commit` would not be an awaitable mock.
        assert session is stub
        return {"ok": True}

    with TestClient(app) as client:
        response = client.get("/probe")

    assert response.status_code == 200
    stub.commit.assert_awaited_once()
    stub.close.assert_awaited_once()
    stub.rollback.assert_not_awaited()
