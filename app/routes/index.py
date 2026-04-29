"""Placeholder index route.

Renders a small page that proves HTMX + Alpine are wired up correctly. This
route gets replaced by the real run-list / dashboard view in a later ticket;
keeping it tiny here so reviewers can see HTMX working end-to-end.
"""
from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, PlainTextResponse

from app.templates import templates

router = APIRouter(tags=["index"])


@router.get("/", response_class=HTMLResponse)
def index(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request, "index.html", {})


@router.get("/_ping", response_class=PlainTextResponse)
def ping() -> PlainTextResponse:
    """HTMX target used by the placeholder index page to prove the wire-up."""
    return PlainTextResponse("pong")
