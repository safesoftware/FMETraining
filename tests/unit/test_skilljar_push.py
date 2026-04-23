"""Unit tests for image upload helpers in skilljar_push.py."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from pipeline.skilljar_push import (
    _upload_asset,
    _wait_for_asset_url,
    _create_skilljar_upload_url,
    _put_image_to_s3,
)


class TestUploadAsset:
    def test_returns_asset_id_on_success(self, tmp_path):
        img = tmp_path / "test.png"
        img.write_bytes(b"\x89PNG\r\n")

        response_body = json.dumps({"id": "abc123"}).encode()
        mock_resp = MagicMock()
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_resp.read.return_value = response_body

        with patch("urllib.request.urlopen", return_value=mock_resp):
            asset_id = _upload_asset(img, "fake-api-key")

        assert asset_id == "abc123"

    def test_raises_on_http_error(self, tmp_path):
        import urllib.error
        img = tmp_path / "test.gif"
        img.write_bytes(b"GIF89a")

        http_err = urllib.error.HTTPError(
            url="https://api.skilljar.com/v1/assets",
            code=400,
            msg="Bad Request",
            hdrs={},
            fp=MagicMock(read=lambda: b"bad request"),
        )
        with patch("urllib.request.urlopen", side_effect=http_err):
            with pytest.raises(RuntimeError, match="HTTP 400"):
                _upload_asset(img, "fake-api-key")

    def test_raises_on_url_error(self, tmp_path):
        import urllib.error
        img = tmp_path / "test.png"
        img.write_bytes(b"\x89PNG\r\n")

        url_err = urllib.error.URLError(reason="Name or service not known")
        with patch("urllib.request.urlopen", side_effect=url_err):
            with pytest.raises(RuntimeError, match="Network error POST /assets"):
                _upload_asset(img, "fake-api-key")

    def test_multipart_content_type_header(self, tmp_path):
        img = tmp_path / "test.png"
        img.write_bytes(b"\x89PNG\r\n")

        captured_req = {}
        response_body = json.dumps({"id": "xyz"}).encode()
        mock_resp = MagicMock()
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_resp.read.return_value = response_body

        def capture(req):
            captured_req["content_type"] = req.get_header("Content-type")
            return mock_resp

        with patch("urllib.request.urlopen", side_effect=capture):
            _upload_asset(img, "fake-api-key")

        assert "multipart/form-data" in captured_req["content_type"]


class TestCreateSkilljarUploadUrl:
    def test_returns_signed_and_public_url(self):
        response_body = json.dumps({
            "signed_request": "https://s3.example.com/bucket/file.png?sig=abc",
            "url": "https://cdn.example.com/file.png",
            "content_path": "org/public/123/file.png",
        }).encode()
        mock_resp = MagicMock()
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_resp.read.return_value = response_body

        with patch("urllib.request.urlopen", return_value=mock_resp):
            signed, public = _create_skilljar_upload_url("file.png", "image/png", "fake-key")

        assert signed == "https://s3.example.com/bucket/file.png?sig=abc"
        assert public == "https://cdn.example.com/file.png"

    def test_raises_on_http_error(self):
        import urllib.error
        http_err = urllib.error.HTTPError(
            url="https://dashboard.skilljar.com/asset/create_upload_url",
            code=403,
            msg="Forbidden",
            hdrs={},
            fp=MagicMock(read=lambda: b"forbidden"),
        )
        with patch("urllib.request.urlopen", side_effect=http_err):
            with pytest.raises(RuntimeError, match="HTTP 403 GET /asset/create_upload_url"):
                _create_skilljar_upload_url("file.png", "image/png", "fake-key")

    def test_uses_cookie_header_when_session_cookie_provided(self):
        response_body = json.dumps({
            "signed_request": "https://s3.example.com/signed",
            "url": "https://cdn.example.com/file.png",
        }).encode()
        mock_resp = MagicMock()
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_resp.read.return_value = response_body
        captured = {}

        def capture(req):
            captured["cookie"] = req.get_header("Cookie")
            captured["auth"] = req.get_header("Authorization")
            return mock_resp

        with patch("urllib.request.urlopen", side_effect=capture):
            _create_skilljar_upload_url("file.png", "image/png", "fake-key", "sessionid=abc123")

        assert captured["cookie"] == "sessionid=abc123"
        assert captured["auth"] is None

    def test_raises_when_response_missing_fields(self):
        response_body = json.dumps({"content_path": "org/public/123/file.png"}).encode()
        mock_resp = MagicMock()
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_resp.read.return_value = response_body

        with patch("urllib.request.urlopen", return_value=mock_resp):
            with pytest.raises(RuntimeError, match="missing fields"):
                _create_skilljar_upload_url("file.png", "image/png", "fake-key")


class TestPutImageToS3:
    def test_puts_file_data_to_signed_url(self):
        mock_resp = MagicMock()
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_resp.read.return_value = b""

        captured = {}

        def capture(req):
            captured["method"] = req.get_method()
            captured["content_type"] = req.get_header("Content-type")
            captured["acl"] = req.get_header("X-amz-acl")
            return mock_resp

        with patch("urllib.request.urlopen", side_effect=capture):
            _put_image_to_s3("https://s3.example.com/signed", b"\x89PNG", "image/png")

        assert captured["method"] == "PUT"
        assert captured["content_type"] == "image/png"
        assert captured["acl"] == "public-read"

    def test_raises_on_http_error(self):
        import urllib.error
        http_err = urllib.error.HTTPError(
            url="https://s3.example.com/signed",
            code=403,
            msg="Forbidden",
            hdrs={},
            fp=MagicMock(read=lambda: b"SignatureMismatch"),
        )
        with patch("urllib.request.urlopen", side_effect=http_err):
            with pytest.raises(RuntimeError, match="HTTP 403 PUT to S3"):
                _put_image_to_s3("https://s3.example.com/signed", b"\x89PNG", "image/png")


class TestWaitForAssetUrl:
    def test_returns_embed_link_url_when_ready(self):
        with patch("pipeline.skilljar_push._request") as mock_req:
            mock_req.return_value = {"id": "abc", "embed_link_url": "https://cdn.example.com/img.png"}
            url = _wait_for_asset_url("abc", "fake-api-key", max_retries=3)
        assert url == "https://cdn.example.com/img.png"
        mock_req.assert_called_once_with("GET", "/assets/abc", "fake-api-key")

    def test_falls_back_to_download_url(self):
        with patch("pipeline.skilljar_push._request") as mock_req:
            mock_req.return_value = {"id": "abc", "embed_link_url": None, "download_url": "https://cdn.example.com/dl.png"}
            url = _wait_for_asset_url("abc", "fake-api-key", max_retries=3)
        assert url == "https://cdn.example.com/dl.png"

    def test_retries_until_url_available(self):
        responses = [
            {"id": "abc"},
            {"id": "abc"},
            {"id": "abc", "embed_link_url": "https://cdn.example.com/img.png"},
        ]
        with patch("pipeline.skilljar_push._request", side_effect=responses):
            with patch("time.sleep"):
                url = _wait_for_asset_url("abc", "fake-api-key", max_retries=5)
        assert url == "https://cdn.example.com/img.png"

    def test_returns_none_when_retries_exhausted(self):
        with patch("pipeline.skilljar_push._request", return_value={"id": "abc"}):
            with patch("time.sleep"):
                url = _wait_for_asset_url("abc", "fake-api-key", max_retries=3)
        assert url is None
