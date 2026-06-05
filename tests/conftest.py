"""Shared pytest fixtures for the FME Training Automation test suite."""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import AsyncIterator

import pytest
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.models import Base

FIXTURES_DIR = Path(__file__).parent / "fixtures"
SAMPLE_LESSON_HTML = FIXTURES_DIR / "sample_lesson.html"


@pytest.fixture
def sample_lesson_path() -> Path:
    """Return the path to the fixture lesson HTML."""
    return SAMPLE_LESSON_HTML


@pytest.fixture
def sample_lesson_content() -> str:
    """Return the content of the fixture lesson HTML."""
    return SAMPLE_LESSON_HTML.read_text(encoding="utf-8")


@pytest.fixture
def tmp_version_tree(tmp_path: Path) -> dict:
    """
    Create a minimal versioned lesson tree under tmp_path.

    Returns a dict with useful paths and expected values for assertions.

    Tree layout:
      tmp_path/
        2024.2/
          fme-form-basic/
            Connect To Data 2024.2/
              Exercise_ Connect to a Database/
                index.html
                images/
                  workbench_overview.png
              Read and Display Data/
                index.html
    """
    version = "2024.2"
    lp = "fme-form-basic"
    course_folder = "Connect To Data 2024.2"
    course_canonical = "Connect To Data"

    lesson1 = "Exercise_ Connect to a Database"
    lesson2 = "Read and Display Data"

    for lesson in (lesson1, lesson2):
        lesson_dir = tmp_path / version / lp / course_folder / lesson
        lesson_dir.mkdir(parents=True)
        # Copy the sample lesson HTML
        shutil.copy(SAMPLE_LESSON_HTML, lesson_dir / "index.html")
        # Create a dummy image dir
        (lesson_dir / "images").mkdir()

    return {
        "repo_root": tmp_path,
        "version": version,
        "lp": lp,
        "course_folder": course_folder,
        "course_canonical": course_canonical,
        "lessons": [lesson1, lesson2],
        "lesson1_path": f"{version}/{lp}/{course_folder}/{lesson1}/index.html",
    }


# ---- DB fixtures (KNOW-2269 / KNOW-2270 onward) ---------------------------

@pytest.fixture
async def async_session_factory() -> AsyncIterator[async_sessionmaker[AsyncSession]]:
    """Per-test SQLite-backed async session factory with the schema applied.

    Each test gets its own engine, so writes from one test never leak into
    another. The Postgres-only column types (JSONB) fall back to JSON via
    the ``with_variant`` declarations in the SQLAlchemy models.
    """
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    try:
        yield factory
    finally:
        await engine.dispose()


# ---- Auth helpers (KNOW-2259) -------------------------------------------
# The AuthMiddleware gates /api/* with 401 for unauthenticated requests, so
# integration tests that drive /api through ``create_app()`` must present a
# valid session. These helpers mint a SessionMiddleware-compatible signed
# cookie and seed the backing user, without driving the real Google OAuth.


def mint_session_cookie(secret: str, data: dict) -> str:
    """Mint a cookie value Starlette's SessionMiddleware will accept.

    Mirrors SessionMiddleware's own serialization: ``base64(json(data))``
    signed with an itsdangerous ``TimestampSigner`` over ``secret``.
    """
    import base64
    import json

    from itsdangerous import TimestampSigner

    signer = TimestampSigner(str(secret))
    payload = base64.b64encode(json.dumps(data).encode("utf-8"))
    return signer.sign(payload).decode("utf-8")


def auth_cookie_for(user_id: int, *, secret: str, epoch: int = 0) -> str:
    """Signed ``fme_session`` cookie value for the given user id + epoch."""
    from app.auth.dependencies import SESSION_USER_EPOCH, SESSION_USER_ID

    return mint_session_cookie(
        secret, {SESSION_USER_ID: user_id, SESSION_USER_EPOCH: epoch}
    )


async def seed_active_user(
    session_factory, *, email: str = "qa-auth@safe.com"
):
    """Insert an active @safe.com user via ``session_factory`` and return a
    handle with ``id`` / ``epoch`` / ``email``. Call from the same event loop
    that owns the factory's engine."""
    from types import SimpleNamespace

    from app.models.users import User

    async with session_factory() as session:
        user = User(
            email=email, name="QA Auth", is_active=True, session_epoch=0
        )
        session.add(user)
        await session.flush()
        uid = user.id
        await session.commit()
    return SimpleNamespace(id=uid, epoch=0, email=email)


@pytest.fixture
async def seeded_user(async_session_factory):
    """An active user seeded into ``async_session_factory`` (in the test
    event loop, alongside schema creation, so the app under test sees it)."""
    return await seed_active_user(async_session_factory)


@pytest.fixture
def authenticate():
    """Return ``auth(client, user_id, epoch=0)`` that attaches a valid signed
    session cookie to a TestClient so its /api requests pass the auth gate."""
    from app.config import get_settings

    def _auth(client, user_id: int, *, epoch: int = 0) -> None:
        client.cookies.set(
            "fme_session",
            auth_cookie_for(
                user_id,
                secret=get_settings().session_signing_key,
                epoch=epoch,
            ),
        )

    return _auth
