"""SSE endpoints. Today: ``GET /api/runs/{run_id}/logs/stream``.

The browser opens an ``EventSource`` against this URL; the FastAPI app
reads ``run_logs`` rows in a polling loop and re-emits them. Reconnect
is supported: clients send ``Last-Event-ID`` and we resume from the row
after that id.

See :mod:`app.services.log_streamer` for the encoder + tail logic.
"""
from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse

from app.db.engine import _get_or_create_session_factory
from app.services.log_streamer import stream_logs

_logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/api/runs/{run_id}/logs/stream")
async def stream_run_logs(run_id: str, request: Request) -> StreamingResponse:
    """Server-Sent Events stream of every ``run_logs`` row for the given run.

    TODO(KNOW-2259): once Google OIDC lands, gate this behind the same
    cookie-based auth as the rest of the app. For now it's open — fine
    in local dev with a non-public box.
    """
    last_event_id: Optional[int] = None
    raw = request.headers.get("Last-Event-ID")
    if raw is not None:
        try:
            last_event_id = int(raw)
        except ValueError:
            # Spec says servers should ignore malformed Last-Event-ID.
            _logger.debug("Ignoring malformed Last-Event-ID: %r", raw)

    try:
        session_factory = _get_or_create_session_factory()
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))

    return StreamingResponse(
        stream_logs(
            session_factory=session_factory,
            run_id=run_id,
            last_event_id=last_event_id,
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            # Nginx-specific: don't buffer the SSE response, flush as we go.
            # Harmless for non-Nginx fronts.
            "X-Accel-Buffering": "no",
        },
    )
