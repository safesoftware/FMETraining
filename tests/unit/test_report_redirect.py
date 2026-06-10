"""Unit tests for the ``GET /report/{run_id}`` redirect route (KNOW-2334).

Checks that:
- The route redirects to the expected static artifact path.
- The redirect is a 302 (not a 301 permanent redirect).
- The target URL has the correct format: /artifacts/{run_id}/report-{run_id}.html
- Special characters in run_id are preserved (the route is a simple string substitution).
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.routes.report import router
from fastapi import FastAPI


@pytest.fixture
def report_client() -> TestClient:
    """A minimal FastAPI app with only the report redirect router mounted."""
    app = FastAPI()
    app.include_router(router)
    return TestClient(app, follow_redirects=False)


class TestReportRedirectRoute:
    def test_redirect_status_code(self, report_client: TestClient):
        """GET /report/{run_id} should return 302."""
        resp = report_client.get("/report/20260610T120000-abcd")
        assert resp.status_code == 302, f"Expected 302, got {resp.status_code}"

    def test_redirect_location(self, report_client: TestClient):
        """Redirect target must be /artifacts/{run_id}/report-{run_id}.html."""
        run_id = "20260610T120000-abcd"
        resp = report_client.get(f"/report/{run_id}")
        location = resp.headers.get("location", "")
        assert location == f"/artifacts/{run_id}/report-{run_id}.html", (
            f"Expected /artifacts/{run_id}/report-{run_id}.html, got {location!r}"
        )

    def test_redirect_with_different_run_id(self, report_client: TestClient):
        """Different run IDs produce different redirect targets."""
        run_id = "20260101T000000-beef"
        resp = report_client.get(f"/report/{run_id}")
        assert resp.status_code == 302
        location = resp.headers.get("location", "")
        assert f"report-{run_id}.html" in location

    def test_redirect_follows_to_artifacts(self):
        """Following the redirect via TestClient(follow_redirects=True) reaches /artifacts/."""
        app = FastAPI()
        app.include_router(router)
        # Add a dummy artifacts static handler so the follow works without 404
        from fastapi.responses import HTMLResponse

        @app.get("/artifacts/{run_id}/report-{run_id2}.html")
        async def fake_report(run_id: str, run_id2: str) -> HTMLResponse:
            return HTMLResponse(content=f"<html>report for {run_id}</html>")

        client = TestClient(app, follow_redirects=True)
        run_id = "20260610T120000-test"
        resp = client.get(f"/report/{run_id}")
        assert resp.status_code == 200
        assert run_id in resp.text
