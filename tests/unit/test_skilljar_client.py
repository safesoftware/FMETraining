"""Unit tests for the async SkilljarClient.

Uses ``respx`` to mock httpx responses — no real Skilljar API calls.
"""
from __future__ import annotations

import base64

import httpx
import pytest

from app.services.skilljar_client import SkilljarClient

# respx is already in the test deps via pytest-mock / httpx; import lazily so
# missing-driver errors surface clearly if it's gone.
respx = pytest.importorskip("respx")


# ---- auth ----------------------------------------------------------------

def test_api_key_is_required() -> None:
    with pytest.raises(ValueError):
        SkilljarClient(api_key="")


@pytest.mark.asyncio
async def test_basic_auth_header_uses_api_key_with_empty_password() -> None:
    """Skilljar's docs require ``api_key:`` (note the trailing colon)."""
    expected = base64.b64encode(b"k123:").decode()
    async with SkilljarClient(api_key="k123") as client:
        # Headers are configured on the underlying httpx client.
        assert client._client.headers["Authorization"] == f"Basic {expected}"


# ---- pagination ---------------------------------------------------------

@pytest.mark.asyncio
async def test_paginates_courses_via_next_link() -> None:
    """Skilljar returns ``{"results": [...], "next": "..."}`` until next is null."""
    def _handler(request: httpx.Request) -> httpx.Response:
        # Route by query string: the second call carries cursor=abc, the
        # first does not. respx route ordering on a shared path is fiddly
        # so we use a single callback to disambiguate explicitly.
        if "cursor=abc" in str(request.url):
            return httpx.Response(
                200,
                json={"results": [{"id": "c3", "title": "Course 3"}], "next": None},
            )
        return httpx.Response(
            200,
            json={
                "results": [
                    {"id": "c1", "title": "Course 1"},
                    {"id": "c2", "title": "Course 2"},
                ],
                "next": "https://api.skilljar.com/v1/courses?cursor=abc",
            },
        )

    async with respx.mock(base_url="https://api.skilljar.com/v1") as router:
        router.get("/courses").mock(side_effect=_handler)
        async with SkilljarClient(api_key="k") as client:
            ids = [row["id"] async for row in client.list_courses()]
        assert ids == ["c1", "c2", "c3"]


@pytest.mark.asyncio
async def test_list_lessons_and_published_paths_use_separate_endpoints() -> None:
    async with respx.mock(base_url="https://api.skilljar.com/v1") as router:
        router.get("/lessons").mock(
            return_value=httpx.Response(200, json={"results": [{"id": "l1"}], "next": None})
        )
        router.get("/published-paths").mock(
            return_value=httpx.Response(200, json={"results": [{"id": "p1"}], "next": None})
        )

        async with SkilljarClient(api_key="k") as client:
            lessons = [row async for row in client.list_lessons()]
            paths = [row async for row in client.list_published_paths()]
        assert [r["id"] for r in lessons] == ["l1"]
        assert [r["id"] for r in paths] == ["p1"]


@pytest.mark.asyncio
async def test_http_error_propagates_as_httpx_exception() -> None:
    async with respx.mock(base_url="https://api.skilljar.com/v1") as router:
        router.get("/courses").mock(return_value=httpx.Response(500, text="oops"))
        async with SkilljarClient(api_key="k") as client:
            with pytest.raises(httpx.HTTPStatusError):
                async for _ in client.list_courses():
                    pass


@pytest.mark.asyncio
async def test_empty_results_list_finishes_cleanly() -> None:
    async with respx.mock(base_url="https://api.skilljar.com/v1") as router:
        router.get("/courses").mock(
            return_value=httpx.Response(200, json={"results": [], "next": None})
        )
        async with SkilljarClient(api_key="k") as client:
            collected = [row async for row in client.list_courses()]
        assert collected == []
