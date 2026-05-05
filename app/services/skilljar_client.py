"""Async HTTP client for the Skilljar REST API.

Plan section 5 calls for syncing courses, lessons, and published-paths
into our DB on demand. This module wraps the Skilljar v1 endpoints we
need and exposes them as ``async`` paginating generators.

Auth: HTTP Basic with ``api_key:`` (empty password). Same shape as the
existing legacy ``pipeline/skilljar_push.py`` uses.

Tests inject a stub `httpx.AsyncClient` (via the ``client`` parameter)
so they don't hit the live API. Production code constructs a default
client if none is provided.
"""
from __future__ import annotations

import base64
import logging
from typing import AsyncIterator, Optional

import httpx

_logger = logging.getLogger(__name__)

DEFAULT_BASE_URL = "https://api.skilljar.com/v1"
DEFAULT_TIMEOUT_S = 30.0
DEFAULT_PAGE_SIZE = 100


def _basic_auth_header(api_key: str) -> str:
    token = base64.b64encode(f"{api_key}:".encode()).decode()
    return f"Basic {token}"


class SkilljarClient:
    """Thin wrapper over httpx for the three list endpoints we need."""

    def __init__(
        self,
        api_key: str,
        *,
        base_url: str = DEFAULT_BASE_URL,
        client: Optional[httpx.AsyncClient] = None,
        timeout_s: float = DEFAULT_TIMEOUT_S,
        page_size: int = DEFAULT_PAGE_SIZE,
    ) -> None:
        if not api_key:
            raise ValueError("api_key is required")
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._page_size = page_size
        self._owns_client = client is None
        self._client = client or httpx.AsyncClient(
            base_url=self._base_url,
            timeout=timeout_s,
            headers={
                "Authorization": _basic_auth_header(api_key),
                "Accept": "application/json",
            },
        )
        # If the caller supplied a client without our base URL we still want
        # the auth header present, but we won't mutate the caller's headers.
        if not self._owns_client and "Authorization" not in self._client.headers:
            self._client.headers["Authorization"] = _basic_auth_header(api_key)

    async def __aenter__(self) -> "SkilljarClient":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        if self._owns_client:
            await self._client.aclose()

    async def aclose(self) -> None:
        if self._owns_client:
            await self._client.aclose()

    # ---- pagination ------------------------------------------------------

    async def _paginate(self, path: str) -> AsyncIterator[dict]:
        """Walk a paginated Skilljar collection, yielding one row at a time.

        Skilljar's pagination shape is::

            {"results": [...], "next": "https://api.skilljar.com/v1/...?cursor=..."}

        ``next`` is null on the last page. We pull just the query string off
        the ``next`` URL and reissue against the same path — this keeps the
        request URLs predictable for both our base-url'd httpx client and
        for ``respx`` mocks in tests.

        We always re-set ``page_size`` on every page so a missing
        ``page_size`` in Skilljar's ``next`` URL doesn't silently revert
        subsequent pages to Skilljar's default page size.

        If Skilljar's ``next`` URL points at a different path than the one
        we're paginating (e.g. an API version migration mid-rollout), we
        log a warning. We continue against the original path because
        switching mid-stream would require trusting an unsigned URL that
        the caller didn't ask for.
        """
        from urllib.parse import urlparse, parse_qs

        params: dict = {"page_size": self._page_size}
        while True:
            response = await self._client.get(path, params=params)
            response.raise_for_status()
            payload = response.json()
            for row in payload.get("results", []):
                yield row
            next_url = payload.get("next")
            if not next_url:
                return
            parsed = urlparse(next_url)
            if parsed.path and parsed.path.rstrip("/") != path.rstrip("/"):
                _logger.warning(
                    "Skilljar next URL points at a different path: "
                    "expected %s, got %s. Continuing against the expected path.",
                    path, parsed.path,
                )
            # Carry over Skilljar's cursor (or any other params it includes)
            # but always force page_size — Skilljar omits it from `next`.
            params = {k: v[0] for k, v in parse_qs(parsed.query).items()}
            params["page_size"] = self._page_size

    # ---- public list endpoints ------------------------------------------

    async def list_courses(self) -> AsyncIterator[dict]:
        async for row in self._paginate("/courses"):
            yield row

    async def list_lessons(self) -> AsyncIterator[dict]:
        async for row in self._paginate("/lessons"):
            yield row

    async def list_published_paths(self) -> AsyncIterator[dict]:
        async for row in self._paginate("/published-paths"):
            yield row
