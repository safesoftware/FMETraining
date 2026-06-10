"""Index route — launch UI (KNOW-2335).

Signed-out: shows a "Sign in with Google" link so unauthenticated users
have a clear entry point.

Signed-in: renders the full launch form porting the launcher.html scope
tree + options, backed by the new ``/api/runs``, ``/api/versions`` and
``/api/content-tree`` endpoints.
"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, PlainTextResponse

from app.auth.dependencies import get_user_or_none
from app.models.users import User
from app.templates import templates

router = APIRouter(tags=["index"])


@router.get("/", response_class=HTMLResponse)
async def index(request: Request) -> HTMLResponse:
    """Render the index page.

    * Signed-out → sign-in link.
    * Signed-in → launch form with scope tree + options.
    """
    user: Optional[User] = get_user_or_none(request)
    return templates.TemplateResponse(
        request,
        "index.html",
        {"user": user},
    )


@router.get("/_ping", response_class=PlainTextResponse)
def ping() -> PlainTextResponse:
    """Health-check target used by HTMX; kept for backwards compat."""
    return PlainTextResponse("pong")
