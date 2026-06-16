"""Auth middleware: hydrate ``request.state.user`` from the session cookie.

Runs once per HTTP request. The session cookie is managed by Starlette's
:class:`~starlette.middleware.sessions.SessionMiddleware`; this middleware
reads the small payload, looks up the user, and attaches the row to
``scope["state"]["user"]`` (which is what ``request.state.user`` resolves
to) so downstream routes can do ``request.state.user`` (or
``Depends(require_user)``).

Implemented as a pure ASGI middleware -- not :class:`BaseHTTPMiddleware`
-- because the latter has known issues propagating ``request.state``
mutations to the inner request. Mutating ``scope["state"]`` directly
side-steps the problem.

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
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from starlette.responses import JSONResponse, RedirectResponse
from starlette.types import ASGIApp, Receive, Scope, Send

from app.auth.dependencies import SESSION_USER_EPOCH, SESSION_USER_ID
from app.models.base import utc_now
from app.models.users import User

_logger = logging.getLogger(__name__)


class AuthMiddleware:
    """Look up the authenticated user (if any) for every HTTP request.

    Pure ASGI -- attach via ``app.add_middleware(AuthMiddleware,
    session_factory=...)``. SessionMiddleware MUST be mounted earlier
    (i.e. added later in user-middleware order, since the last add wraps
    the outermost) so that ``scope["session"]`` is populated before this
    middleware runs.

    After hydration it *gates the whole app default-deny*: an unauthenticated
    request to any non-public path is rejected before it reaches the route.
    Only a tiny explicit allowlist stays public -- the landing page (``/``),
    the sign-in flow (``/auth/*``), vendored assets (``/static/*``), and infra
    probes (``/health``, ``/_ping``). Everything else -- including the report
    HTML (``/artifacts/*``), lesson images (``/lesson-content/*``), and the
    ``/drafts`` / ``/release`` pages -- requires a signed-in user.

    Rejection shape depends on the path: ``/api/*`` gets a 401 JSON (so
    ``fetch()`` callers see a clean error); any other path gets a 302 redirect
    to the landing page, so a human following a deep link lands on sign-in
    rather than a raw error. Routes may still add ``Depends(require_user)`` for
    the user object; this middleware is the blanket backstop.
    """

    # Paths reachable WITHOUT authentication. Everything else requires a
    # signed-in user (default-deny). Keep this list tiny + explicit -- it is
    # the app's entire unauthenticated surface.
    #   /, /_ping, /health  landing + infra probes
    #   /auth/...           the Google sign-in flow itself (can't gate login)
    #   /static/...         vendored CSS/JS for the landing + login pages
    # NB: /artifacts (report HTML + AI edit plans) and /lesson-content (lesson
    # images) are deliberately NOT public -- a signed-in browser sends the
    # session cookie on those same-origin requests, so they still render.
    _PUBLIC_EXACT = frozenset({"/", "/_ping", "/health", "/favicon.ico"})
    _PUBLIC_PREFIXES = ("/auth/", "/static/")

    def __init__(
        self,
        app: ASGIApp,
        *,
        session_factory: Optional[async_sessionmaker[AsyncSession]] = None,
    ) -> None:
        self.app = app
        self._session_factory = session_factory

    async def __call__(
        self, scope: Scope, receive: Receive, send: Send
    ) -> None:
        if scope["type"] != "http":
            # Not an HTTP request (websocket, lifespan, etc.) -- no-op.
            await self.app(scope, receive, send)
            return

        # FastAPI / Starlette stash request-local state in scope["state"].
        # Default to None so request.state.user is always well-defined.
        scope.setdefault("state", {})
        scope["state"]["user"] = None

        await self._hydrate(scope)

        # Default-deny gate: an unauthenticated request to any non-public path
        # is rejected before it reaches the route. /api/* -> 401 JSON; any
        # other path -> 302 redirect to the landing page (sign-in). Fail-closed
        # -- if hydration couldn't run (no session/DB), the request is still
        # anonymous and is rejected.
        path = scope.get("path", "")
        if scope["state"]["user"] is None and not self._is_public(path):
            if path.startswith("/api/"):
                response = JSONResponse(
                    {"detail": "Authentication required"}, status_code=401
                )
            else:
                # Browser navigation to a protected page -> bounce to the
                # landing page, which offers Google sign-in.
                response = RedirectResponse("/", status_code=302)
            await response(scope, receive, send)
            return

        await self.app(scope, receive, send)

    def _is_public(self, path: str) -> bool:
        """True if ``path`` is reachable without authentication."""
        return path in self._PUBLIC_EXACT or path.startswith(
            self._PUBLIC_PREFIXES
        )

    async def _hydrate(self, scope: Scope) -> None:
        """Read the session payload and, if valid, attach the user row."""
        if self._session_factory is None:
            return

        session = scope.get("session")
        if not isinstance(session, dict):
            # SessionMiddleware not mounted, or session uninitialized.
            return

        user_id = session.get(SESSION_USER_ID)
        epoch_snapshot = session.get(SESSION_USER_EPOCH)
        if not isinstance(user_id, int) or not isinstance(epoch_snapshot, int):
            return

        try:
            async with self._session_factory() as db:
                user = await db.get(User, user_id)
                if (
                    user is None
                    or not user.is_active
                    or user.session_epoch != epoch_snapshot
                ):
                    # Stale or revoked session -- clear it so subsequent
                    # requests don't pay the DB lookup again.
                    session.clear()
                    return
                user.last_seen_at = utc_now()
                await db.commit()
                # Detach so downstream code can read from the instance
                # after the session closes. SQLAlchemy refreshes lazy
                # attrs on access otherwise, which would error post-close.
                db.expunge(user)
                scope["state"]["user"] = user
        except Exception:  # pragma: no cover - defensive
            _logger.exception("auth middleware: DB lookup failed; treating as anonymous")
