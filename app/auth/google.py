"""authlib Google OIDC client setup.

We expose a single registered client (``oauth.google``) that the
``/auth/login`` and ``/auth/callback`` routes drive via authlib's
Starlette integration. The OIDC discovery doc is loaded lazily on the
first authorize call so importing this module in tests doesn't require
network access.
"""
from __future__ import annotations

import logging
from typing import Optional

from authlib.integrations.starlette_client import OAuth

from app.config import Settings, get_settings

_logger = logging.getLogger(__name__)

GOOGLE_DISCOVERY_URL = "https://accounts.google.com/.well-known/openid-configuration"

# Module-level OAuth registry. authlib expects a single shared registry
# in a process; tests can monkeypatch ``oauth`` to install a stub.
oauth = OAuth()


class GoogleOAuthMisconfigured(RuntimeError):
    """Raised when ``/auth/login`` is hit but Google credentials aren't set."""


def init_google_oauth(settings: Optional[Settings] = None) -> None:
    """Register the Google OIDC client. Idempotent.

    Reads ``GOOGLE_OAUTH_CLIENT_ID`` and ``GOOGLE_OAUTH_CLIENT_SECRET``
    from :class:`~app.config.Settings`. If either is unset, registration
    is skipped -- the auth routes will return 503 instead of crashing
    at startup. This lets the skeleton boot in dev/test without secrets.
    """
    settings = settings or get_settings()
    client_id = settings.google_oauth_client_id
    client_secret = settings.google_oauth_client_secret
    if not client_id or not client_secret:
        _logger.warning(
            "Google OAuth not registered: client id or secret missing. "
            "Auth routes will return 503 until set."
        )
        return
    if "google" in oauth._clients:  # type: ignore[attr-defined]
        return
    oauth.register(
        name="google",
        server_metadata_url=GOOGLE_DISCOVERY_URL,
        client_id=client_id,
        client_secret=client_secret,
        client_kwargs={"scope": "openid email profile"},
    )


def get_google_client():
    """Return the registered ``oauth.google`` client.

    Raises :class:`GoogleOAuthMisconfigured` if it hasn't been registered
    (i.e. the environment is missing the OAuth client id/secret).
    """
    client = oauth.create_client("google")
    if client is None:
        raise GoogleOAuthMisconfigured(
            "Google OAuth client is not registered. Set "
            "GOOGLE_OAUTH_CLIENT_ID and GOOGLE_OAUTH_CLIENT_SECRET."
        )
    return client
