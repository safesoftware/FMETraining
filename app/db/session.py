"""FastAPI-style ``get_session`` dependency.

Yields an ``AsyncSession`` and guarantees rollback + close on error,
commit on success. Routes/services declare their dependency as::

    async def handler(session: AsyncSession = Depends(get_session)):
        ...
"""

from __future__ import annotations

from typing import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.engine import _get_or_create_session_factory


async def get_session() -> AsyncIterator[AsyncSession]:
    """Yield a SQLAlchemy async session bound to the app's engine.

    Behaviour mirrors the conventional FastAPI dependency:

    * On normal completion, the caller's writes are committed.
    * On exception, the session is rolled back and the exception is
      re-raised so FastAPI's exception handlers can take over.
    * The session is closed in either case.
    """

    factory = _get_or_create_session_factory()
    session: AsyncSession = factory()
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()
