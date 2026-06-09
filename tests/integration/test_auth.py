"""End-to-end auth tests: sign-in (via the testable seam), session
hydration, hd-claim enforcement, logout, and tampered cookies.

The OAuth dance with Google is bypassed via :func:`app.routes.auth.complete_login`
so we don't need a real authlib OAuth client or live JWKS endpoint. The
contract under test is everything *after* the ID token is validated:

* hd=safe.com enforcement (and rejection of non-safe domains).
* email_verified enforcement.
* Just-in-time user upsert.
* Session cookie hydrate -> request.state.user.
* Logout bumps users.session_epoch and invalidates other active sessions.
* Tampered session cookies fall through to anonymous.
"""
from __future__ import annotations

from typing import Any, Optional

import pytest
from fastapi import Depends, FastAPI, Request
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from starlette.middleware.sessions import SessionMiddleware

from app.auth import AuthMiddleware
from app.auth.dependencies import require_user
from app.models.users import User
from app.routes import auth as auth_routes


# ---- Test helper route, defined at module scope so FastAPI can introspect ---


def _claims(
    *,
    email: str = "alice@safe.com",
    hd: Optional[str] = "safe.com",
    verified: bool = True,
    name: str = "Alice",
    picture: Optional[str] = None,
) -> dict[str, Any]:
    return {
        "sub": f"google-sub-{email}",
        "email": email,
        "email_verified": verified,
        "hd": hd,
        "name": name,
        "picture": picture or f"https://example.test/{email}.png",
    }


def _make_app(session_factory) -> FastAPI:
    """Build a FastAPI app with the auth stack mounted plus helper routes
    that drive ``complete_login`` directly with synthetic claims.
    """
    app = FastAPI()
    # Note ordering: in Starlette, the FIRST-added middleware is the
    # INNERMOST. AuthMiddleware needs to run AFTER SessionMiddleware
    # populates scope["session"], so it must be added first.
    app.add_middleware(AuthMiddleware, session_factory=session_factory)
    app.add_middleware(
        SessionMiddleware,
        secret_key="unit-test-key",
        session_cookie="fme_session",
        same_site="lax",
        https_only=False,
    )

    # Point the route module's session_factory at our test factory; the
    # /auth/logout route uses it to bump session_epoch.
    auth_routes.session_factory = session_factory  # type: ignore[assignment]

    app.include_router(auth_routes.router)

    @app.post("/_test/login")
    async def _test_login(request: Request) -> dict:
        body = await request.json() if await _has_body(request) else {}
        async with session_factory() as db:
            user = await auth_routes.complete_login(
                request, db, claims=_claims(**body)
            )
        return {"user_id": user.id, "email": user.email, "name": user.name}

    @app.get("/me")
    def me(user: User = Depends(require_user)) -> dict:
        return {"id": user.id, "email": user.email, "name": user.name}

    @app.get("/whoami-or-anon")
    def whoami_or_anon(request: Request) -> dict:
        u = getattr(request.state, "user", None)
        return {"signed_in": bool(u), "email": getattr(u, "email", None)}

    @app.get("/api/ping")
    def api_ping() -> dict:
        # A bare /api/* route with NO Depends(require_user): proves the
        # middleware's blanket gate is what protects it, not a per-route dep.
        return {"pong": True}

    return app


async def _has_body(request: Request) -> bool:
    """Return True if the request has a JSON body."""
    try:
        return bool(await request.body())
    except Exception:
        return False


# ---- Fixtures ------------------------------------------------------------


@pytest.fixture
async def app(async_session_factory):
    return _make_app(async_session_factory)


@pytest.fixture
async def client(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as c:
        yield c


# ---- complete_login: domain enforcement ----------------------------------


@pytest.mark.asyncio
async def test_complete_login_creates_user_and_signs_in(
    async_session_factory, client: AsyncClient
) -> None:
    """A first-time @safe.com user gets a row + a signed session cookie."""
    resp = await client.post("/_test/login")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["email"] == "alice@safe.com"

    # The session cookie should now hydrate /me on subsequent requests.
    me = await client.get("/me")
    assert me.status_code == 200
    assert me.json()["email"] == "alice@safe.com"

    async with async_session_factory() as db:
        rows = (await db.scalars(select(User))).all()
    assert len(rows) == 1
    assert rows[0].is_active is True
    assert rows[0].session_epoch == 0


@pytest.mark.asyncio
async def test_complete_login_rejects_wrong_domain(
    async_session_factory, client: AsyncClient
) -> None:
    resp = await client.post(
        "/_test/login",
        json={"email": "mallory@gmail.com", "hd": "gmail.com"},
    )
    assert resp.status_code == 403
    assert "safe.com" in resp.text

    # No session was set, no user was created.
    async with async_session_factory() as db:
        assert (await db.scalars(select(User))).all() == []
    me = await client.get("/me")
    assert me.status_code == 401


@pytest.mark.asyncio
async def test_complete_login_rejects_unverified_email(
    client: AsyncClient,
) -> None:
    resp = await client.post("/_test/login", json={"verified": False})
    assert resp.status_code == 403
    assert "not verified" in resp.text.lower()


@pytest.mark.asyncio
async def test_complete_login_refreshes_existing_user_fields(
    async_session_factory, client: AsyncClient
) -> None:
    """Second sign-in for the same email updates name + picture, doesn't dupe."""
    first = await client.post("/_test/login", json={"name": "Alice One"})
    second = await client.post("/_test/login", json={"name": "Alice Two"})
    assert first.status_code == 200, first.text
    assert second.status_code == 200, second.text
    assert first.json()["user_id"] == second.json()["user_id"]
    assert second.json()["name"] == "Alice Two"

    async with async_session_factory() as db:
        users = (await db.scalars(select(User))).all()
    assert len(users) == 1
    assert users[0].name == "Alice Two"


@pytest.mark.asyncio
async def test_deactivated_user_cannot_sign_in_again(
    async_session_factory, client: AsyncClient
) -> None:
    """An admin-deactivated account stays locked out; signing in via
    Google must NOT silently flip is_active back to True."""
    # First sign-in creates the row.
    first = await client.post("/_test/login")
    assert first.status_code == 200

    # Admin deactivates the user out-of-band.
    async with async_session_factory() as db:
        user = (await db.scalars(select(User))).one()
        user.is_active = False
        await db.commit()

    # Fresh client (no session cookie). Google still returns valid
    # claims, but the upsert path must reject.
    transport = ASGITransport(app=client._transport.app)  # type: ignore[attr-defined]
    async with AsyncClient(transport=transport, base_url="http://testserver") as fresh:
        again = await fresh.post("/_test/login")
    assert again.status_code == 403
    assert "deactivated" in again.text.lower()

    async with async_session_factory() as db:
        user = (await db.scalars(select(User))).one()
    assert user.is_active is False  # NOT silently re-activated.


# ---- Open-redirect guard ------------------------------------------------


@pytest.mark.parametrize(
    "next_value,expected",
    [
        ("/", True),
        ("/runs/123", True),
        ("/runs/123?tab=logs", True),
        ("//evil.example", False),       # protocol-relative
        ("https://evil.example", False), # absolute URL
        ("http://evil.example/", False),
        ("javascript:alert(1)", False),  # XSS-y scheme
        ("ftp://x", False),
        ("", False),                     # empty
        (None, False),
    ],
)
def test_is_safe_local_redirect_only_accepts_same_origin_paths(
    next_value: Optional[str], expected: bool
) -> None:
    """Pure-function check on the helper that gates both the storage
    side (``/auth/login``) and the consumption side (``/auth/callback``).
    """
    from app.routes.auth import _is_safe_local_redirect
    assert _is_safe_local_redirect(next_value) is expected


# ---- Session middleware: tamper + epoch invalidation ---------------------


@pytest.mark.asyncio
async def test_tampered_cookie_falls_through_to_anonymous(
    client: AsyncClient,
) -> None:
    """A cookie that doesn't match the SessionMiddleware signature is
    silently treated as no session. Same response as if no cookie at all."""
    client.cookies.set("fme_session", "definitely-not-a-valid-signed-session")
    resp = await client.get("/whoami-or-anon")
    assert resp.status_code == 200
    assert resp.json() == {"signed_in": False, "email": None}

    me = await client.get("/me")
    assert me.status_code == 401


@pytest.mark.asyncio
async def test_logout_bumps_session_epoch_and_invalidates_other_sessions(
    async_session_factory, app: FastAPI
) -> None:
    """Logout from one client invalidates every other active session for
    the same user via the session_epoch snapshot check."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as c1, \
            AsyncClient(transport=transport, base_url="http://testserver") as c2:
        await c1.post("/_test/login")
        await c2.post("/_test/login")

        assert (await c1.get("/me")).status_code == 200
        assert (await c2.get("/me")).status_code == 200

        # c1 logs out -> session_epoch on the user row goes from 0 -> 1.
        logout = await c1.post("/auth/logout", follow_redirects=False)
        assert logout.status_code == 302

        async with async_session_factory() as db:
            user = (await db.scalars(select(User))).one()
        assert user.session_epoch == 1

        # c2 still has the old (epoch=0) snapshot. The next request
        # should fail the epoch check and become anonymous.
        assert (await c2.get("/me")).status_code == 401
        assert (await c1.get("/me")).status_code == 401


# ---- Blanket /api/* gate -------------------------------------------------


@pytest.mark.asyncio
async def test_api_path_rejects_anonymous_with_401(client: AsyncClient) -> None:
    """An unauthenticated request to /api/* is rejected with 401 by the
    middleware, even when the route itself has no require_user dependency."""
    resp = await client.get("/api/ping")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_api_path_allows_authenticated_user(client: AsyncClient) -> None:
    """After sign-in the same /api/* route is reachable."""
    await client.post("/_test/login")
    resp = await client.get("/api/ping")
    assert resp.status_code == 200
    assert resp.json() == {"pong": True}


# ---- /auth/login when Google not configured ------------------------------


@pytest.mark.asyncio
async def test_auth_login_returns_503_when_google_misconfigured(
    client: AsyncClient,
) -> None:
    """If GOOGLE_OAUTH_CLIENT_ID / SECRET aren't set, /auth/login should
    fail loudly with 503 rather than producing a confusing redirect."""
    # ``oauth`` is a process-wide authlib singleton. Another test (or app
    # startup when a placeholder GOOGLE_OAUTH_CLIENT_ID is set, as in
    # .env.compose) may have registered the google client. authlib's
    # create_client() re-creates the client from ``_registry`` even after
    # ``_clients`` is cleared, so both must be cleared to simulate "not
    # configured". Save and restore so this test does not leak its teardown
    # into later tests.
    from app.auth.google import oauth as google_oauth
    saved_client = google_oauth._clients.pop("google", None)  # type: ignore[attr-defined]
    saved_registry = google_oauth._registry.pop("google", None)  # type: ignore[attr-defined]
    try:
        resp = await client.get("/auth/login", follow_redirects=False)
        assert resp.status_code == 503
        assert "google" in resp.text.lower()
    finally:
        if saved_client is not None:
            google_oauth._clients["google"] = saved_client  # type: ignore[attr-defined]
        if saved_registry is not None:
            google_oauth._registry["google"] = saved_registry  # type: ignore[attr-defined]
