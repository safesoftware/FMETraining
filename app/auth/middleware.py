"""Auth middleware: hydrate ``request.state.user`` from the session cookie.

Runs once per request. The session cookie is managed by Starlette's
:class:`~starlette.middleware.sessions.SessionMiddleware`; this
middleware reads the small payload, looks up the user, and attaches
the row to ``request.state`` so downstream routes can do
``request.state.user`` (or ``Depends(require_user)``).

Invalidation rules:

* If the session has no ``user_id`` -> anonymous.
* If the user row no longer exists -> clear the session, anonymous.
* If ``user.is_active`` is False -> clear the session, anonymous.
* If ``user.session_epoch`` doesn't match the snapshot in the session
  -> clear the session, anonymous. (Logout bumps epoch, which boots
  every other active session for that user.)

The middleware updates ``users.last_seen_at`` on each authenticated
request (best-effort -- a transient DB error during hydration
downgrades the request to anonymous rather than 500ing).
"""
from __future__ import annotations

import logging
from typing import Awaitable, Callable, Optional

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp

from app.auth.dependencies import SESSION_USER_EPOCH, SESSION_USER_ID
from app.models.base import utc_now
from app.models.users import User

_logger = logging.getLogger(__name__)


class AuthMiddleware(BaseHTTPMiddleware):
    """Look up the authenticated user (if any) for every request."""

    def __init__(
        self,
        app: ASGIApp,
        *,
        session_factory: Optional[async_sessionmaker[AsyncSession]] = None,
    ) -> None:
        super().__init__(app)
        self._session_factory = session_factory

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        request.state.user = None

        session_factory = self._session_factory
        if session_factory is None:
            # No DB configured -- skeleton mode (e.g. dev container with
            # nothing wired up). Treat as anonymous.
            return await call_next(request)

        # Starlette's SessionMiddleware sets request.session lazily; if
        # it isn't installed we fall through to anonymous.
        try:
            session = request.session
        except AssertionError:
            return await call_next(request)

        user_id = session.get(SESSION_USER_ID)
        epoch_snapshot = session.get(SESSION_USER_EPOCH)
        if not isinstance(user_id, int) or not isinstance(epoch_snapshot, int):
            return await call_next(request)

        try:
            async with session_factory() as db:
                user = await db.get(User, user_id)
                if user is None or not user.is_active or user.session_epoch != epoch_snapshot:
                    # Stale or revoked session -- clear it so subsequent
                    # requests don't pay the DB lookup again.
                    session.clear()
                    return await call_next(request)
                user.last_seen_at = utc_now()
                await db.commit()
                # Detach so downstream code can use the instance after
                # the session closes. SQLAlchemy refreshes lazy attrs on
                # access otherwise, which would error post-close.
                db.expunge(user)
                request.state.user = user
        except Exception:  # pragma: no cover - defensive
            _logger.exception("auth middleware: DB lookup failed; treating as anonymous")
            return await call_next(request)

        return await call_next(request)
