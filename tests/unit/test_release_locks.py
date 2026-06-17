"""Unit tests for the release lock + history helpers (WS-E, KNOW-2358).

Drives ``app/services/release_locks.py`` against the per-test SQLite engine
from ``conftest.async_session_factory``.
"""
from __future__ import annotations

from datetime import timedelta

import pytest

from app.models import ReleaseLock
from app.models.base import utc_now
from app.services import release_locks as rl


# ---- target_id helpers (pure) --------------------------------------------


def test_course_target_id_strips_lesson_segment() -> None:
    assert (
        rl.course_target_id(
            "2026.1/fme-form-basic/Connect To Data 2026.1/Read and Display Data"
        )
        == "course:2026.1/fme-form-basic/Connect To Data 2026.1"
    )


def test_course_target_ids_for_dedupes_and_sorts() -> None:
    lessons = [
        "2026.1/lp/Course A 2026.1/Lesson 2",
        "2026.1/lp/Course A 2026.1/Lesson 1",
        "2026.1/lp/Course B 2026.1/Lesson 1",
        "",
        "   ",
    ]
    assert rl.course_target_ids_for(lessons) == [
        "course:2026.1/lp/Course A 2026.1",
        "course:2026.1/lp/Course B 2026.1",
    ]


def test_parse_target_id_extracts_version_and_course() -> None:
    info = rl.parse_target_id("course:2026.1/fme-form-basic/Connect To Data 2026.1")
    assert info["to_version"] == "2026.1"
    assert info["course"] == "Connect To Data 2026.1"
    assert info["course_prefix"] == "2026.1/fme-form-basic/Connect To Data 2026.1"


# ---- locks ---------------------------------------------------------------

_A = "course:2026.1/lp/Course A 2026.1"
_B = "course:2026.1/lp/Course B 2026.1"


@pytest.mark.asyncio
async def test_acquire_then_conflict(async_session_factory, seeded_user) -> None:
    async with async_session_factory() as session:
        first = await rl.acquire_release_locks(session, [_A], user_id=seeded_user.id)
        await session.commit()
    assert first == []

    async with async_session_factory() as session:
        second = await rl.acquire_release_locks(session, [_A], user_id=seeded_user.id)
        await session.commit()
    assert second == [_A]


@pytest.mark.asyncio
async def test_acquire_takes_over_expired_lock(
    async_session_factory, seeded_user
) -> None:
    async with async_session_factory() as session:
        session.add(
            ReleaseLock(
                target_id=_A,
                locked_by=seeded_user.id,
                locked_at=utc_now() - timedelta(hours=2),
                expires_at=utc_now() - timedelta(hours=1),  # already expired
                intent="release",
            )
        )
        await session.commit()

    async with async_session_factory() as session:
        conflicts = await rl.acquire_release_locks(
            session, [_A], user_id=seeded_user.id
        )
        await session.commit()
    assert conflicts == []

    async with async_session_factory() as session:
        lock = await session.get(ReleaseLock, _A)
        assert lock is not None
        assert rl._aware(lock.expires_at) > utc_now()  # refreshed into the future


@pytest.mark.asyncio
async def test_acquire_is_all_or_nothing(async_session_factory, seeded_user) -> None:
    # Pre-lock B; acquiring [A, B] must conflict on B and NOT create A.
    async with async_session_factory() as session:
        await rl.acquire_release_locks(session, [_B], user_id=seeded_user.id)
        await session.commit()

    async with async_session_factory() as session:
        conflicts = await rl.acquire_release_locks(
            session, [_A, _B], user_id=seeded_user.id
        )
        await session.commit()
    assert conflicts == [_B]

    async with async_session_factory() as session:
        assert await session.get(ReleaseLock, _A) is None  # not partially acquired


@pytest.mark.asyncio
async def test_release_held_locks_respects_owner(
    async_session_factory, seeded_user
) -> None:
    async with async_session_factory() as session:
        await rl.acquire_release_locks(session, [_A], user_id=seeded_user.id)
        await session.commit()

    # A different user must NOT be able to release it.
    async with async_session_factory() as session:
        await rl.release_held_locks(session, [_A], user_id=seeded_user.id + 12345)
        await session.commit()
    async with async_session_factory() as session:
        assert await session.get(ReleaseLock, _A) is not None

    # The owner can.
    async with async_session_factory() as session:
        await rl.release_held_locks(session, [_A], user_id=seeded_user.id)
        await session.commit()
    async with async_session_factory() as session:
        assert await session.get(ReleaseLock, _A) is None


# ---- history -------------------------------------------------------------


@pytest.mark.asyncio
async def test_history_lifecycle_filter_and_idempotent_finish(
    async_session_factory, seeded_user
) -> None:
    v2026 = [_A, _B]
    v2027 = ["course:2027.0/lp/Course C 2027.0"]
    async with async_session_factory() as session:
        ids_2026 = await rl.start_release_history(
            session, v2026, user_id=seeded_user.id
        )
        await rl.start_release_history(session, v2027, user_id=seeded_user.id)
        await session.commit()
    assert len(ids_2026) == 2

    async with async_session_factory() as session:
        all_rows = await rl.list_release_history(session)
        assert len(all_rows) == 3
        assert all(r.status == "running" for r in all_rows)

        only_2026 = await rl.list_release_history(session, to_version="2026.1")
        assert len(only_2026) == 2
        assert all(r.target_id.startswith("course:2026.1/") for r in only_2026)

    # Finish the 2026 rows → success.
    async with async_session_factory() as session:
        await rl.finish_release_history(session, ids_2026, status="success")
        await session.commit()
    async with async_session_factory() as session:
        rows = await rl.list_release_history(session, to_version="2026.1")
        assert all(r.status == "success" and r.finished_at is not None for r in rows)

    # Re-finishing is a no-op (rows are no longer "running").
    async with async_session_factory() as session:
        await rl.finish_release_history(session, ids_2026, status="failed")
        await session.commit()
    async with async_session_factory() as session:
        rows = await rl.list_release_history(session, to_version="2026.1")
        assert all(r.status == "success" for r in rows)
