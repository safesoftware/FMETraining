"""FastAPI dependencies for authenticated routes.

* :func:`require_user` -- raises ``HTTPException(401)`` if no user is
  attached to ``request.state``.
* :func:`get_user_or_none` -- returns ``None`` instead of raising. Useful
  for index pages that render different markup signed-in vs signed-out.

The actual hydration happens in :class:`app.auth.middleware.AuthMiddleware`,
so by the time these dependencies run the user (or ``None``) is on
``request.state``.
"""
from __future__ import annotations

from typing import Optional

from fastapi import HTTPException, Request, status

from app.models.users import User

# Session keys. Constants so route + middleware code can't drift apart.
SESSION_USER_ID = "user_id"
SESSION_USER_EPOCH = "user_epoch"


def get_user_or_none(request: Request) -> Optional[User]:
    """Return the authenticated user, or ``None`` if anonymous."""
    return getattr(request.state, "user", None)


def require_user(request: Request) -> User:
    """Return the authenticated user, or raise 401."""
    user = getattr(request.state, "user", None)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )
    return user
