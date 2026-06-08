"""
Ensure every <img src> in lesson HTML points at a permanent URL on our
public-read S3 bucket. Four passes:

  1. data:image/...;base64,... URIs        → decode + upload (extract_and_upload_data_uris)
  2. relative paths (images/foo.png)       → upload from <repo>/<lesson_dir>/images/<file>
  3. expiring pre-signed URLs (everpath /  → match by filename to local images/<file>,
     ?Expires=)                              upload local file. If no local match, raise.
  4. absolute app-origin URLs              → a contenteditable edit can serialise a
     (http://localhost:8080/.../images/      relative src into an absolute URL against
     <file>, or the prod host)               the page origin. Re-host by filename match.
                                             Defensive: if no local match, leave it alone.

Permanent URLs (https://s3.{region}.amazonaws.com/<our-bucket>/... and any
other http(s):// URL with no `Expires=` query param) are left alone.

Skilljar's /v1/assets endpoint is intentionally avoided: per the Skilljar API
spec, GET /v1/assets/{id} returns a `download_url` that is "a signed download
URL valid for 1 hour", useless for embedding in lesson `content_html`. We host
on our own bucket which serves objects publicly with no expiration.
"""

from __future__ import annotations

import base64
import hashlib
import mimetypes
import re
import tempfile
import urllib.parse
from pathlib import Path

from pipeline.skilljar_push import _s3_put

_DATA_URI_IMG_RE = re.compile(
    r'''<img\b[^>]*?\bsrc=(?P<q>["'])(?P<uri>data:image/(?P<subtype>[^;"']+);base64,[^"']+)(?P=q)''',
    re.IGNORECASE,
)

_RELATIVE_SRC_RE = re.compile(
    r'(src=["\'])(?!https?://|data:)([^"\']+)(["\'])', re.IGNORECASE,
)

_HTTP_SRC_RE = re.compile(r'src=["\'](https?://[^"\']+)["\']', re.IGNORECASE)

_EXPIRING_HOST = "everpath-course-content.s3.amazonaws.com"


def _is_expiring_url(src: str) -> bool:
    """True for any S3 pre-signed URL we should re-host before saving."""
    parsed = urllib.parse.urlparse(src)
    if parsed.netloc == _EXPIRING_HOST:
        return True
    qs = urllib.parse.parse_qs(parsed.query)
    return "Expires" in qs or "X-Amz-Expires" in qs


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


def upload_lesson_images(
    html: str,
    *,
    lesson_dir: str,
    repo_root: Path,
    s3_bucket: str,
    s3_key_id: str,
    s3_secret: str,
    s3_region: str,
) -> tuple[str, list[dict]]:
    """Walk every <img src> in html and ensure each src is a permanent URL on
    our S3 bucket. Returns (rewritten_html, upload_log).

    Raises RuntimeError on any unrecoverable case: missing credentials, upload
    error, or expiring URL whose filename has no match in the local
    <repo_root>/<lesson_dir>/images/ folder.

    upload_log entries: {"mime": str, "size": int | None, "url": str, "source": str}
    where source ∈ {"data_uri", "relative", "expiring_url", "absolute_url"}.
    """
    upload_log: list[dict] = []

    # Pass 1 — data: URIs
    html, data_log = extract_and_upload_data_uris(
        html,
        s3_bucket=s3_bucket, s3_key_id=s3_key_id,
        s3_secret=s3_secret, s3_region=s3_region,
    )
    for entry in data_log:
        upload_log.append({**entry, "source": "data_uri"})

    # Pass 2 — relative paths (e.g. images/foo.png). Reuse the release helper.
    relative_paths = list({m.group(2) for m in _RELATIVE_SRC_RE.finditer(html)
                           if not m.group(2).startswith("#")})
    if relative_paths:
        # Imported lazily to avoid a circular import via skilljar_release → skilljar_push.
        from pipeline.skilljar_release import _upload_and_rewrite_images
        html, failed = _upload_and_rewrite_images(
            html, relative_paths, lesson_dir, repo_root,
            api_key="",  # unused since we removed the Skilljar asset step
            s3_bucket=s3_bucket, s3_key_id=s3_key_id,
            s3_secret=s3_secret, s3_region=s3_region,
        )
        if failed:
            details = "; ".join(f"{p}: {r}" for p, r in failed)
            raise RuntimeError(f"Could not upload local images: {details}")
        for rel in relative_paths:
            upload_log.append({"source": "relative", "rel_path": rel})

    # Pass 3 — expiring pre-signed URLs. Match by filename against local images/.
    expiring_urls = []
    for m in _HTTP_SRC_RE.finditer(html):
        url = m.group(1).replace("&amp;", "&")
        if _is_expiring_url(url):
            expiring_urls.append(url)
    if expiring_urls:
        if not (s3_bucket and s3_key_id and s3_secret):
            raise RuntimeError(
                "Cannot re-host expiring image URLs: AWS_S3_BUCKET, "
                "AWS_ACCESS_KEY_ID, and AWS_SECRET_ACCESS_KEY must be set in .env."
            )
        images_dir = repo_root / lesson_dir / "images"
        seen: dict[str, str] = {}
        for url in expiring_urls:
            if url in seen:
                continue
            filename = Path(urllib.parse.urlparse(url).path).name
            local_file = images_dir / filename
            if not local_file.exists():
                raise RuntimeError(
                    f"Cannot re-host expiring URL — no matching local file at "
                    f"{local_file}. Add the original image to the lesson's "
                    f"images/ folder so it can be re-uploaded."
                )
            public_url, _key = _s3_put(local_file, s3_bucket, s3_key_id, s3_secret, s3_region)
            seen[url] = public_url
            upload_log.append({
                "source": "expiring_url",
                "filename": filename,
                "url": public_url,
            })
        for original, replacement in seen.items():
            # The HTML may have HTML-encoded the ampersands when serialised;
            # replace both forms so we hit it regardless.
            html = html.replace(original, replacement)
            html = html.replace(original.replace("&", "&amp;"), replacement)

    # Pass 4 — absolute URLs a contenteditable edit serialised against the page
    # origin (e.g. http://localhost:8080/<dir>/images/<file>, or the prod host).
    # These are unreachable for live viewers. Re-host by filename match against
    # the local images/ folder. Defensive belt-and-braces: if there is no local
    # match we leave the URL alone (unlike the expiring pass, which raises) —
    # an unrelated external image must survive untouched.
    images_dir = repo_root / lesson_dir / "images"
    absolute_local: list[tuple[str, str]] = []
    for m in _HTTP_SRC_RE.finditer(html):
        url = m.group(1).replace("&amp;", "&")
        parsed = urllib.parse.urlparse(url)
        if parsed.netloc.endswith("amazonaws.com"):
            continue  # permanent (or already re-hosted) S3 URL — leave alone
        path = urllib.parse.unquote(parsed.path)
        if "/images/" not in path:
            continue
        filename = Path(path).name
        if (images_dir / filename).exists():
            absolute_local.append((url, filename))
    if absolute_local:
        if not (s3_bucket and s3_key_id and s3_secret):
            raise RuntimeError(
                "Cannot re-host absolute image URLs: AWS_S3_BUCKET, "
                "AWS_ACCESS_KEY_ID, and AWS_SECRET_ACCESS_KEY must be set in .env."
            )
        seen_abs: dict[str, str] = {}
        for url, filename in absolute_local:
            if url in seen_abs:
                continue
            public_url, _key = _s3_put(
                images_dir / filename, s3_bucket, s3_key_id, s3_secret, s3_region
            )
            seen_abs[url] = public_url
            upload_log.append({
                "source": "absolute_url",
                "filename": filename,
                "url": public_url,
            })
        for original, replacement in seen_abs.items():
            html = html.replace(original, replacement)
            html = html.replace(original.replace("&", "&amp;"), replacement)

    return html, upload_log
