"""Unit tests for extract_and_upload_data_uris in pipeline/data_uri_upload.py."""

from __future__ import annotations

import base64
from unittest.mock import patch

import pytest

from pipeline.data_uri_upload import extract_and_upload_data_uris

_S3_ARGS = dict(
    s3_bucket="test-bucket",
    s3_key_id="fake-id",
    s3_secret="fake-secret",
    s3_region="us-east-1",
)

_PNG_BYTES = b"\x89PNG\r\n\x1a\n" + b"\x00" * 16
_PNG_B64 = base64.b64encode(_PNG_BYTES).decode()
_PNG_DATA_URI = f"data:image/png;base64,{_PNG_B64}"

_JPG_BYTES = b"\xff\xd8\xff" + b"\x00" * 8
_JPG_B64 = base64.b64encode(_JPG_BYTES).decode()
_JPG_DATA_URI = f"data:image/jpeg;base64,{_JPG_B64}"


class TestExtractAndUploadDataUris:
    def test_no_data_uris_returns_html_unchanged(self):
        html = '<p>hello <img src="images/foo.png"> world <img src="https://cdn.example.com/x.jpg"></p>'
        result_html, log = extract_and_upload_data_uris(html, **_S3_ARGS)
        assert result_html == html
        assert log == []

    def test_single_data_uri_uploads_and_rewrites(self):
        html = f'<p>see <img src="{_PNG_DATA_URI}" alt="diagram"> for details.</p>'
        public_url = "https://s3.us-east-1.amazonaws.com/test-bucket/skilljar-uploads/abc-pasted-x.png"

        with patch("pipeline.data_uri_upload._s3_put",
                   return_value=(public_url, "skilljar-uploads/abc-pasted-x.png")) as mock_put:
            result_html, log = extract_and_upload_data_uris(html, **_S3_ARGS)

        assert _PNG_DATA_URI not in result_html
        assert f'src="{public_url}"' in result_html
        assert mock_put.call_count == 1
        assert len(log) == 1
        assert log[0]["mime"] == "image/png"
        assert log[0]["size"] == len(_PNG_BYTES)
        assert log[0]["url"] == public_url

    def test_duplicate_data_uris_uploaded_once(self):
        html = (
            f'<p><img src="{_PNG_DATA_URI}"> and again '
            f'<img src="{_PNG_DATA_URI}" class="thumb"></p>'
        )
        public_url = "https://s3.us-east-1.amazonaws.com/test-bucket/skilljar-uploads/abc-pasted-x.png"

        with patch("pipeline.data_uri_upload._s3_put",
                   return_value=(public_url, "skilljar-uploads/abc-pasted-x.png")) as mock_put:
            result_html, log = extract_and_upload_data_uris(html, **_S3_ARGS)

        assert _PNG_DATA_URI not in result_html
        assert result_html.count(f'src="{public_url}"') == 2
        assert mock_put.call_count == 1
        assert len(log) == 1

    def test_two_distinct_data_uris_both_uploaded(self):
        html = f'<p><img src="{_PNG_DATA_URI}"><img src="{_JPG_DATA_URI}"></p>'

        urls = iter([
            ("https://s3.us-east-1.amazonaws.com/test-bucket/png.png", "k1"),
            ("https://s3.us-east-1.amazonaws.com/test-bucket/jpg.jpg", "k2"),
        ])

        with patch("pipeline.data_uri_upload._s3_put",
                   side_effect=lambda *a, **kw: next(urls)):
            result_html, log = extract_and_upload_data_uris(html, **_S3_ARGS)

        assert _PNG_DATA_URI not in result_html
        assert _JPG_DATA_URI not in result_html
        assert "https://s3.us-east-1.amazonaws.com/test-bucket/png.png" in result_html
        assert "https://s3.us-east-1.amazonaws.com/test-bucket/jpg.jpg" in result_html
        assert len(log) == 2

    def test_upload_failure_raises(self):
        html = f'<p><img src="{_PNG_DATA_URI}"></p>'

        with patch("pipeline.data_uri_upload._s3_put",
                   side_effect=RuntimeError("HTTP 403 PUT s3://test-bucket/...: Forbidden")):
            with pytest.raises(RuntimeError, match="HTTP 403"):
                extract_and_upload_data_uris(html, **_S3_ARGS)

    def test_missing_s3_credentials_raises(self):
        html = f'<p><img src="{_PNG_DATA_URI}"></p>'
        args = {**_S3_ARGS, "s3_bucket": ""}
        with pytest.raises(RuntimeError, match="AWS_S3_BUCKET"):
            extract_and_upload_data_uris(html, **args)

    def test_missing_credentials_with_no_data_uris_does_not_raise(self):
        html = '<p>no images</p>'
        args = {**_S3_ARGS, "s3_bucket": ""}
        result_html, log = extract_and_upload_data_uris(html, **args)
        assert result_html == html
        assert log == []

    def test_invalid_base64_raises(self):
        html = '<img src="data:image/png;base64,!!!not-valid-base64!!!">'
        with patch("pipeline.data_uri_upload._s3_put"):
            with pytest.raises(RuntimeError, match="Invalid base64"):
                extract_and_upload_data_uris(html, **_S3_ARGS)

    def test_single_quoted_src_supported(self):
        html = f"<img src='{_PNG_DATA_URI}'>"
        public_url = "https://s3.us-east-1.amazonaws.com/test-bucket/skilljar-uploads/x.png"
        with patch("pipeline.data_uri_upload._s3_put",
                   return_value=(public_url, "skilljar-uploads/x.png")):
            result_html, _ = extract_and_upload_data_uris(html, **_S3_ARGS)
        assert _PNG_DATA_URI not in result_html
        assert public_url in result_html

    def test_skilljar_asset_endpoint_not_called(self):
        """Regression: ensure we don't go through /v1/assets, which returns
        1-hour-signed URLs that would expire in the rendered lesson."""
        html = f'<p><img src="{_PNG_DATA_URI}"></p>'
        public_url = "https://s3.us-east-1.amazonaws.com/test-bucket/skilljar-uploads/x.png"

        # data_uri_upload only imports _s3_put — the Skilljar asset helpers are
        # not in its namespace at all. If anyone re-introduces them, importing
        # them here would fail or the patch target wouldn't exist.
        import pipeline.data_uri_upload as mod
        assert not hasattr(mod, "_create_asset_from_url"), \
            "_create_asset_from_url must not be imported in data_uri_upload"
        assert not hasattr(mod, "_wait_for_asset_url"), \
            "_wait_for_asset_url must not be imported in data_uri_upload"
        assert not hasattr(mod, "_s3_delete"), \
            "_s3_delete must not be imported in data_uri_upload"

        with patch("pipeline.data_uri_upload._s3_put",
                   return_value=(public_url, "skilljar-uploads/x.png")):
            result_html, _ = extract_and_upload_data_uris(html, **_S3_ARGS)
        assert public_url in result_html
