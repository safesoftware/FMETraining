"""GET /release — the Release-tab page (WS-D).

Thin server route: it only renders the shell. All data is fetched
client-side against the frozen ``/api/release-*`` contract (see
``docs/plans/release-sprint-api-contract.md``) so this module stays
decoupled from the Skilljar service and the content filesystem.

The page mirrors the ``/drafts`` page-route pattern
(``templates.TemplateResponse(request, "x.html", {...})``).
"""
from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from app.templates import templates

router = APIRouter(tags=["release-page"])


@router.get("/release", response_class=HTMLResponse)
async def release_page(request: Request) -> HTMLResponse:
    """Render the Release-tab shell.

    The page asks the (already-authenticated) browser to fetch the
    available content versions from ``GET /api/versions`` and lets the
    user type a version as a fallback, so the server side carries no
    state here.
    """
    return templates.TemplateResponse(request, "release.html", {})
