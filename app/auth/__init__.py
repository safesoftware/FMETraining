"""Authentication: Google OIDC sign-in restricted to ``@safe.com``.

Public surface:

* :func:`require_user` -- FastAPI dependency that returns the
  :class:`~app.models.users.User` row attached to the current request,
  or raises ``HTTPException(401)``.
* :func:`get_user_or_none` -- Same dependency but returns ``None``
  instead of raising; useful for routes that render different markup
  for signed-out vs signed-in users.
* :class:`AuthMiddleware` -- Hydrates ``request.state.user`` from the
  signed session cookie on every request. Mounted by ``app.main``.
* :func:`init_google_oauth` -- Registers the Google OIDC client with
  authlib using values from ``Settings``.

The login / callback / logout HTTP routes live in
``app.routes.auth``.

Design notes
------------

* The session cookie is Starlette's :class:`SessionMiddleware`, signed
  with ``Settings.session_signing_key`` via ``itsdangerous``. We set
  ``HttpOnly``, ``SameSite=Lax``, and ``Secure`` (in production).
* The session payload only stores ``{"user_id": int, "user_epoch": int}``.
  Each request, the middleware re-reads the user row and verifies the
  epoch matches. Bumping ``users.session_epoch`` invalidates every
  active session for that user without touching cookies.
* The Google ``hd`` claim (``hd == "safe.com"``) is the authoritative
  domain check. ``email`` is also a hint but Google docs caution against
  parsing it directly when ``hd`` is available.
"""
from __future__ import annotations

from app.auth.dependencies import (
    SESSION_USER_EPOCH,
    SESSION_USER_ID,
    get_user_or_none,
    require_user,
)
from app.auth.google import init_google_oauth
from app.auth.middleware import AuthMiddleware

__all__ = [
    "AuthMiddleware",
    "SESSION_USER_EPOCH",
    "SESSION_USER_ID",
    "get_user_or_none",
    "init_google_oauth",
    "require_user",
]
