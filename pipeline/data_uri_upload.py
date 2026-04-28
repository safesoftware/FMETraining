"""
Extract <img src='data:image/...;base64,...'> tags from HTML, upload each
image to our public-read S3 bucket, and rewrite the src to the permanent S3
URL.

Used by serve.py to clean up data URIs that arrive in the WYSIWYG editor when
users paste content from external sources (Word, Slack, web pages, etc.).
The browser inserts those images as inline base64 blobs which Skilljar cannot
render — this module turns them into proper hosted images.

Skilljar's /v1/assets endpoint is intentionally avoided here: per the Skilljar
API spec, GET /v1/assets/{id} returns a `download_url` that is "a signed
download URL valid for 1 hour" — fine for API-side downloads, but useless for
embedding in lesson `content_html`. We host on our own bucket instead, which
serves objects publicly with no expiration.
"""

from __future__ import annotations

import base64
import hashlib
import mimetypes
import re
import tempfile
from pathlib import Path

from pipeline.skilljar_push import _s3_put

_DATA_URI_IMG_RE = re.compile(
    r'''<img\b[^>]*?\bsrc=(?P<q>["'])(?P<uri>data:image/(?P<subtype>[^;"']+);base64,[^"']+)(?P=q)''',
    re.IGNORECASE,
)


def extract_and_upload_data_uris(
    html: str,
    *,
    s3_bucket: str,
    s3_key_id: str,
    s3_secret: str,
    s3_region: str,
) -> tuple[str, list[dict]]:
    """Find every <img src='data:image/...;base64,...'> in html, upload each to
    our S3 bucket as public-read, and return (rewritten_html, upload_log).

    Identical data URIs are uploaded once and reused. Raises RuntimeError if
    credentials are missing or any upload fails.

    upload_log entries: {"mime": str, "size": int, "url": str}
    """
    matches = list(_DATA_URI_IMG_RE.finditer(html))
    if not matches:
        return html, []

    if not (s3_bucket and s3_key_id and s3_secret):
        raise RuntimeError(
            "Cannot upload pasted images: AWS_S3_BUCKET, AWS_ACCESS_KEY_ID, "
            "and AWS_SECRET_ACCESS_KEY must be set in .env."
        )

    url_map: dict[str, str] = {}
    upload_log: list[dict] = []

    for m in matches:
        uri = m.group("uri")
        if uri in url_map:
            continue

        subtype = m.group("subtype").lower()
        _, _, b64data = uri.partition(",")
        try:
            image_bytes = base64.b64decode(b64data, validate=True)
        except (ValueError, base64.binascii.Error) as exc:
            raise RuntimeError(f"Invalid base64 data URI for image/{subtype}: {exc}") from exc

        mime = f"image/{subtype}"
        ext = mimetypes.guess_extension(mime) or f".{subtype}"
        digest = hashlib.sha256(image_bytes).hexdigest()[:12]
        filename = f"pasted-{digest}{ext}"

        with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
            tmp.write(image_bytes)
            tmp_path = Path(tmp.name)
        try:
            named_path = tmp_path.with_name(filename)
            tmp_path.rename(named_path)
        except OSError:
            named_path = tmp_path

        try:
            public_url, _s3_key = _s3_put(named_path, s3_bucket, s3_key_id, s3_secret, s3_region)
        finally:
            try:
                named_path.unlink()
            except OSError:
                pass

        url_map[uri] = public_url
        upload_log.append({"mime": mime, "size": len(image_bytes), "url": public_url})

    rewritten = html
    for uri, public_url in url_map.items():
        rewritten = rewritten.replace(uri, public_url)

    return rewritten, upload_log
