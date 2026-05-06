"""Auth routes: ``/auth/login``, ``/auth/callback``, ``/auth/logout``.

The OAuth code-exchange + JWKS verification is delegated to authlib's
Starlette integration. After authlib hands us the verified claims,
:func:`complete_login` performs:

1. ``hd == "safe.com"`` enforcement (the authoritative domain check).
2. ``email_verified == True`` enforcement.
3. Just-in-time upsert into ``users``.
4. Stash ``{user_id, user_epoch}`` in the signed session cookie.

Tests skip authlib entirely by calling :func:`complete_login` with a
synthetic claims dict -- this is the seam that keeps the unit tests
free of network mocks while still exercising the domain check, the
upsert, and the session write.
"""
from __future__ import annotations

import logging
from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import SESSION_USER_EPOCH, SESSION_USER_ID
from app.auth.google import GoogleOAuthMisconfigured, get_google_client
from app.db.engine import session_factory
from app.models.base import utc_now
from app.models.users import User

_logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])

ALLOWED_HD = "safe.com"


class LoginRejected(HTTPException):
    """Caller authenticated with Google but doesn't meet our policy."""

    def __init__(self, reason: str) -> None:
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=reason)


# ---------------------------------------------------------------------------
# Pure logic — testable without authlib / network
# ---------------------------------------------------------------------------


async def complete_login(
    request: Request,
    db: AsyncSession,
    *,
    claims: dict[str, Any],
) -> User:
    """Validate Google ID token claims + upsert the user + write session.

    Raises :class:`LoginRejected` (HTTP 403) when the claims fail the
    domain policy. Returns the persisted :class:`User`.
    """
    hd = claims.get("hd")
    if hd != ALLOWED_HD:
        raise LoginRejected(
            f"Sign-in rejected: account is not part of {ALLOWED_HD!r} "
            f"(got hd={hd!r})."
        )
    if not claims.get("email_verified"):
        raise LoginRejected("Sign-in rejected: Google reports email not verified.")

    email = claims.get("email")
    if not email:
        raise LoginRejected("Sign-in rejected: Google did not return an email claim.")

    name = claims.get("name")
    picture = claims.get("picture")

    user = await db.scalar(select(User).where(User.email == email))
    if user is None:
        user = User(
            email=email,
            name=name,
            picture_url=picture,
            role="member",
            is_active=True,
            session_epoch=0,
            last_seen_at=utc_now(),
        )
        db.add(user)
        await db.flush()
        _logger.info("auth: created user %s (id=%s)", email, user.id)
    else:
        # Refresh display fields on every sign-in so the UI keeps up
        # when the user changes their Google avatar / name.
        user.name = name
        user.picture_url = picture
        user.is_active = True
        user.last_seen_at = utc_now()

    await db.commit()

    # The session cookie is opaque to the browser; we only stash the
    # user id + epoch snapshot. The middleware re-reads the user every
    # request and re-checks the epoch against the live DB row.
    request.session[SESSION_USER_ID] = user.id
    request.session[SESSION_USER_EPOCH] = user.session_epoch

    return user


# ---------------------------------------------------------------------------
# HTTP routes
# ---------------------------------------------------------------------------


def _redirect_uri(request: Request) -> str:
    return str(request.url_for("auth_callback"))


@router.get("/login", name="auth_login")
async def login(request: Request, next: Optional[str] = "/"):
    """Kick off the Google OIDC dance.

    Stores ``next`` in the session so we can land the user back where
    they came from after callback. Defaults to ``/``.
    """
    try:
        client = get_google_client()
    except GoogleOAuthMisconfigured as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)
        ) from exc

    if next and next.startswith("/") and not next.startswith("//"):
        request.session["post_login_redirect"] = next

    return await client.authorize_redirect(request, _redirect_uri(request))


@router.get("/callback", name="auth_callback")
async def callback(request: Request):
    """Finish the OAuth dance.

    On success: upserts the user, sets the session, redirects to the
    stashed ``post_login_redirect`` (or ``/``).
    """
    try:
        client = get_google_client()
    except GoogleOAuthMisconfigured as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)
        ) from exc

    token = await client.authorize_access_token(request)
    # authlib returns the parsed ID token claims under ``userinfo`` for
    # OIDC servers that include it, plus the raw token. We trust authlib
    # to have validated the JWS signature, ``iss``, ``aud``, and ``exp``
    # against Google's JWKS.
    claims = token.get("userinfo")
    if not claims:
        # Fallback: some authlib versions / OIDC providers stash claims
        # at the top level of ``token``.
        claims = {
            k: token[k]
            for k in ("sub", "email", "email_verified", "hd", "name", "picture")
            if k in token
        }

    async with session_factory() as db:
        await complete_login(request, db, claims=claims)

    next_url = request.session.pop("post_login_redirect", "/") or "/"
    return RedirectResponse(url=next_url, status_code=status.HTTP_302_FOUND)


@router.post("/logout", name="auth_logout")
async def logout(request: Request):
    """Clear the session and bump ``users.session_epoch`` so any other
    active sessions for this user (different browsers, different
    devices) get rejected on their next request.
    """
    user_id = request.session.get(SESSION_USER_ID)
    request.session.clear()

    if isinstance(user_id, int):
        async with session_factory() as db:
            await db.execute(
                update(User)
                .where(User.id == user_id)
                .values(session_epoch=User.session_epoch + 1)
            )
            await db.commit()

    return RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
