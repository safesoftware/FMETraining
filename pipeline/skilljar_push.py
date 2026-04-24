"""
Skilljar lesson push module.

Two entry points:
  push_with_version_check() — full flow: derives target lesson_dir from to_version,
      creates the Skilljar course/lesson if missing, pushes HTML, saves local file.
  push_lesson()             — simple direct PATCH for when the mapping already has the target.
"""

from __future__ import annotations

import base64
import datetime
import hashlib
import hmac
import json
import mimetypes
import re
import shutil
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from pathlib import Path

SKILLJAR_API_BASE = "https://api.skilljar.com/v1"
_VERSION_SUFFIX_RE = re.compile(r"\s+(\d{4}\.\d+)$")


# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------

def _basic_auth_header(api_key: str) -> str:
    token = base64.b64encode(f"{api_key}:".encode()).decode()
    return f"Basic {token}"


def _request(method: str, path: str, api_key: str, data: dict | None = None) -> dict:
    url = f"{SKILLJAR_API_BASE}{path}"
    payload = json.dumps(data).encode("utf-8") if data is not None else None
    headers = {"Authorization": _basic_auth_header(api_key), "Accept": "application/json"}
    if payload:
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=payload, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req) as resp:
            raw = resp.read()
            return json.loads(raw.decode("utf-8")) if raw.strip() else {}
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {exc.code} {method} {path}: {body}") from exc


def _get_course(course_id: str, api_key: str) -> dict:
    return _request("GET", f"/courses/{course_id}", api_key)


def _create_course(title: str, source_course: dict, api_key: str) -> dict:
    return _request("POST", "/courses", api_key, {
        "title": title,
        "enforce_sequential_navigation": source_course.get("enforce_sequential_navigation", False),
        "short_description": source_course.get("short_description", ""),
        "long_description_html": source_course.get("long_description_html", ""),
    })


def _get_lesson(lesson_id: str, api_key: str) -> dict:
    return _request("GET", f"/lessons/{lesson_id}", api_key)


def _create_lesson(course_id: str, title: str, lesson_type: str, order: int | None, api_key: str) -> dict:
    body: dict = {"course_id": course_id, "title": title, "type": lesson_type}
    if order is not None:
        body["order"] = order
    return _request("POST", "/lessons", api_key, body)


def _get_content_items(lesson_id: str, api_key: str) -> list[dict]:
    """Return all content items for a MODULAR lesson."""
    data = _request("GET", f"/lessons/{lesson_id}/content-items", api_key)
    return data.get("results", [])


def _upload_asset(file_path: Path, api_key: str) -> str:
    """Upload a local file to Skilljar as an asset. Returns the asset_id."""
    boundary = uuid.uuid4().hex
    filename = file_path.name
    mime_type = mimetypes.guess_type(filename)[0] or "application/octet-stream"
    file_data = file_path.read_bytes()

    multipart_body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'
        f"Content-Type: {mime_type}\r\n\r\n"
    ).encode("utf-8") + file_data + f"\r\n--{boundary}--\r\n".encode("utf-8")

    url = f"{SKILLJAR_API_BASE}/assets"
    headers = {
        "Authorization": _basic_auth_header(api_key),
        "Content-Type": f"multipart/form-data; boundary={boundary}",
        "Accept": "application/json",
    }
    req = urllib.request.Request(url, data=multipart_body, method="POST", headers=headers)
    try:
        with urllib.request.urlopen(req) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            asset_id = result.get("id")
            if not asset_id:
                raise RuntimeError(f"POST /assets response missing 'id': {result!r}")
            return asset_id
    except urllib.error.HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {exc.code} POST /assets: {error_body}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Network error POST /assets: {exc}") from exc


def _wait_for_asset_url(asset_id: str, api_key: str, max_retries: int = 10) -> str | None:
    """Poll GET /assets/{id} until embed_link_url is available. Returns None if exhausted."""
    for attempt in range(max_retries):
        asset = _request("GET", f"/assets/{asset_id}", api_key)
        url = asset.get("embed_link_url") or asset.get("download_url")
        if url:
            return url
        if attempt < max_retries - 1:
            time.sleep(2)
    return None


def _create_asset_from_url(url: str, api_key: str) -> str:
    """Create a Skilljar asset by providing a public URL. Returns the asset_id."""
    result = _request("POST", "/assets", api_key, {"content_url": url})
    asset_id = result.get("id")
    if not asset_id:
        raise RuntimeError(f"POST /assets response missing 'id': {result!r}")
    return asset_id


def _s3_sign(
    method: str,
    bucket: str,
    s3_key: str,
    file_data: bytes,
    extra_headers: dict[str, str],
    key_id: str,
    secret: str,
    region: str,
) -> tuple[str, dict[str, str]]:
    """Build a signed URL and headers for an S3 request using AWS v4 signatures.

    Uses path-style URLs (s3.region.amazonaws.com/bucket/key) so the bucket name
    appears in the URL path rather than the hostname, preserving its casing.
    """
    host = f"s3.{region}.amazonaws.com"
    now = datetime.datetime.now(datetime.timezone.utc)
    amz_date = now.strftime("%Y%m%dT%H%M%SZ")
    date_stamp = now.strftime("%Y%m%d")
    payload_hash = hashlib.sha256(file_data).hexdigest()

    to_sign: dict[str, str] = {
        "host": host,
        "x-amz-content-sha256": payload_hash,
        "x-amz-date": amz_date,
    }
    for k, v in extra_headers.items():
        to_sign[k.lower()] = v

    sorted_keys = sorted(to_sign)
    canonical_headers = "".join(f"{k}:{to_sign[k]}\n" for k in sorted_keys)
    signed_headers_str = ";".join(sorted_keys)

    encoded_key = urllib.parse.quote(s3_key, safe="/")
    canonical_uri = f"/{bucket}/{encoded_key}"
    canonical_request = "\n".join([
        method, canonical_uri, "",
        canonical_headers, signed_headers_str, payload_hash,
    ])

    credential_scope = f"{date_stamp}/{region}/s3/aws4_request"
    string_to_sign = "\n".join([
        "AWS4-HMAC-SHA256", amz_date, credential_scope,
        hashlib.sha256(canonical_request.encode()).hexdigest(),
    ])

    k_bytes = ("AWS4" + secret).encode()
    for part in (date_stamp.encode(), region.encode(), b"s3", b"aws4_request"):
        k_bytes = hmac.new(k_bytes, part, hashlib.sha256).digest()
    sig = hmac.new(k_bytes, string_to_sign.encode(), hashlib.sha256).hexdigest()

    auth = (
        f"AWS4-HMAC-SHA256 Credential={key_id}/{credential_scope}, "
        f"SignedHeaders={signed_headers_str}, Signature={sig}"
    )
    headers: dict[str, str] = {
        "Authorization": auth,
        "x-amz-content-sha256": payload_hash,
        "x-amz-date": amz_date,
    }
    headers.update(extra_headers)
    return f"https://{host}/{bucket}/{encoded_key}", headers


def _s3_put(file_path: Path, bucket: str, key_id: str, secret: str, region: str) -> tuple[str, str]:
    """Upload a local file to S3 with public-read ACL. Returns (public_url, s3_key)."""
    filename = file_path.name
    s3_key = f"skilljar-uploads/{uuid.uuid4().hex[:8]}-{filename}"
    mime = mimetypes.guess_type(filename)[0] or "application/octet-stream"
    data = file_path.read_bytes()
    url, headers = _s3_sign("PUT", bucket, s3_key, data,
                            {"Content-Type": mime, "x-amz-acl": "public-read"},
                            key_id, secret, region)
    req = urllib.request.Request(url, data=data, method="PUT", headers=headers)
    try:
        with urllib.request.urlopen(req) as resp:
            resp.read()
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {exc.code} PUT s3://{bucket}/{s3_key}: {body}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Network error PUT s3://{bucket}/{s3_key}: {exc}") from exc
    return url, s3_key


def _s3_delete(s3_key: str, bucket: str, key_id: str, secret: str, region: str) -> None:
    """Delete an object from S3."""
    url, headers = _s3_sign("DELETE", bucket, s3_key, b"", {}, key_id, secret, region)
    req = urllib.request.Request(url, method="DELETE", headers=headers)
    try:
        with urllib.request.urlopen(req) as resp:
            resp.read()
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {exc.code} DELETE s3://{bucket}/{s3_key}: {body}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Network error DELETE s3://{bucket}/{s3_key}: {exc}") from exc


def _create_skilljar_upload_url(
    filename: str,
    mime_type: str,
    api_key: str,
    session_cookie: str = "",
) -> tuple[str, str]:
    """Request a pre-signed S3 upload URL from the Skilljar dashboard.

    Returns (signed_request_url, public_url).
    Uses session_cookie if provided (required by dashboard.skilljar.com),
    otherwise falls back to API key auth.
    """
    params = urllib.parse.urlencode({
        "s3_object_type": mime_type,
        "s3_object_name": filename,
        "preserve_filename": "true",
        "public_read": "true",
    })
    url = f"https://dashboard.skilljar.com/asset/create_upload_url?{params}"
    if session_cookie:
        headers = {"Cookie": session_cookie, "Accept": "application/json"}
    else:
        headers = {"Authorization": _basic_auth_header(api_key), "Accept": "application/json"}
    req = urllib.request.Request(url, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {exc.code} GET /asset/create_upload_url: {body}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Network error GET /asset/create_upload_url: {exc}") from exc
    signed_request = data.get("signed_request")
    public_url = data.get("url")
    if not signed_request or not public_url:
        raise RuntimeError(f"create_upload_url response missing fields: {data!r}")
    return signed_request, public_url


def _put_image_to_s3(signed_url: str, file_data: bytes, mime_type: str) -> None:
    """PUT image bytes to a Skilljar pre-signed S3 URL."""
    headers = {
        "Content-Type": mime_type,
        "x-amz-acl": "public-read",
        "x-amz-server-side-encryption": "AES256",
    }
    req = urllib.request.Request(signed_url, data=file_data, method="PUT", headers=headers)
    try:
        with urllib.request.urlopen(req) as resp:
            resp.read()
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {exc.code} PUT to S3: {body}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Network error PUT to S3: {exc}") from exc


def _patch_lesson_html(lesson_id: str, html: str, api_key: str) -> None:
    """Patch HTML content — handles both HTML-type and MODULAR-type lessons.

    For MODULAR lessons, patches the largest HTML content item instead of the lesson directly.
    """
    lesson = _get_lesson(lesson_id, api_key)
    if lesson.get("type") != "MODULAR":
        _request("PATCH", f"/lessons/{lesson_id}", api_key, {"content_html": html})
        return

    items = _get_content_items(lesson_id, api_key)
    html_items = [i for i in items if i.get("type", "").upper() == "HTML"]
    if not html_items:
        raise RuntimeError(f"MODULAR lesson {lesson_id} has no HTML content items to update.")
    # Use the content item with the largest existing HTML content
    target = max(html_items, key=lambda i: len(i.get("content_html", "") or ""))
    _request("PATCH", f"/lessons/{lesson_id}/content-items/{target['id']}", api_key, {"content_html": html})


# ---------------------------------------------------------------------------
# Path helpers
# ---------------------------------------------------------------------------

def _target_lesson_dir(source_lesson_dir: str, to_version: str) -> str:
    """
    Derive the to_version lesson_dir from a source lesson_dir.
    "2025.0/fme-form-basic/Connect To Data 2025.0/My Lesson"
    → "2026.1/fme-form-basic/Connect To Data 2026.1/My Lesson"
    """
    parts = Path(source_lesson_dir).parts
    if len(parts) < 4:
        raise ValueError(f"lesson_dir too shallow (expected ≥4 parts): {source_lesson_dir!r}")
    lp = parts[1]
    course_folder = parts[2]
    lesson_folder = "/".join(parts[3:])
    course_canonical = _VERSION_SUFFIX_RE.sub("", course_folder).strip()
    return str(Path(to_version) / lp / f"{course_canonical} {to_version}" / lesson_folder)


def _find_course_id_in_mapping(course_dir_prefix: str, mapping: dict) -> str | None:
    """Return an existing Skilljar course_id for the target course if any lesson is already mapped."""
    prefix = course_dir_prefix if course_dir_prefix.endswith("/") else course_dir_prefix + "/"
    for k, v in mapping.items():
        if k.startswith(prefix):
            return v.get("skilljar_course_id")
    return None


# ---------------------------------------------------------------------------
# Pre-flight info (for confirmation dialog)
# ---------------------------------------------------------------------------

def get_push_info(lesson_dir: str, to_version: str, mapping: dict) -> dict:
    """
    Return what a push_with_version_check() call would do, without actually doing it.

    Returns:
        {
            "target_dir": str,
            "course_title": str,
            "lesson_title": str,
            "action": "update_lesson" | "create_lesson" | "create_course_and_lesson"
                      | "source_not_mapped" | "invalid_lesson_dir",
        }
    """
    try:
        target_dir = _target_lesson_dir(lesson_dir, to_version)
    except ValueError as exc:
        return {"target_dir": "", "course_title": "", "lesson_title": "", "action": "invalid_lesson_dir", "error": str(exc)}

    parts = Path(target_dir).parts
    course_title = parts[2] if len(parts) > 2 else ""
    lesson_title = parts[3] if len(parts) > 3 else ""

    # Target already mapped → simple update
    if target_dir in mapping:
        return {"target_dir": target_dir, "course_title": course_title, "lesson_title": lesson_title, "action": "update_lesson"}

    # Need source entry to proceed
    if lesson_dir not in mapping:
        return {"target_dir": target_dir, "course_title": course_title, "lesson_title": lesson_title, "action": "source_not_mapped"}

    target_course_prefix = f"{parts[0]}/{parts[1]}/{parts[2]}"
    existing_course_id = _find_course_id_in_mapping(target_course_prefix, mapping)

    if existing_course_id:
        return {"target_dir": target_dir, "course_title": course_title, "lesson_title": lesson_title, "action": "create_lesson"}
    return {"target_dir": target_dir, "course_title": course_title, "lesson_title": lesson_title, "action": "create_course_and_lesson"}


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def push_with_version_check(
    lesson_dir: str,
    html: str,
    to_version: str,
    api_key: str,
    mapping: dict,
    mapping_path: Path,
    repo_root: Path,
) -> dict:
    """
    Push accepted HTML to Skilljar for the to_version of the given lesson,
    creating the Skilljar course and/or lesson if they don't exist yet.
    Also writes the HTML to the local to_version folder.

    lesson_dir: source path like "2025.0/lp/Course 2025.0/Lesson" (with version in course folder)
    Returns {"ok", "course_created", "lesson_created", "local_path", "skilljar_lesson_id", "error"}.
    """
    # --- Derive target ---
    try:
        target_dir = _target_lesson_dir(lesson_dir, to_version)
    except ValueError as exc:
        return {"ok": False, "course_created": False, "lesson_created": False,
                "local_path": "", "skilljar_lesson_id": "", "error": str(exc)}

    # --- Save local file ---
    target_file = repo_root / target_dir / "index.html"
    target_file.parent.mkdir(parents=True, exist_ok=True)
    target_file.write_text(html, encoding="utf-8")
    source_images = repo_root / lesson_dir / "images"
    if source_images.is_dir():
        shutil.copytree(source_images, repo_root / target_dir / "images", dirs_exist_ok=True)
    local_path = str(Path(target_dir) / "index.html").replace("\\", "/")

    # --- Skilljar: target lesson already mapped ---
    target_entry = mapping.get(target_dir)
    if target_entry:
        skilljar_lesson_id = target_entry["skilljar_lesson_id"]
        try:
            _patch_lesson_html(skilljar_lesson_id, html, api_key)
        except RuntimeError as exc:
            return {"ok": False, "course_created": False, "lesson_created": False,
                    "local_path": local_path, "skilljar_lesson_id": skilljar_lesson_id,
                    "error": str(exc)}
        return {"ok": True, "course_created": False, "lesson_created": False,
                "local_path": local_path, "skilljar_lesson_id": skilljar_lesson_id, "error": None}

    # --- Source must be in mapping to proceed ---
    source_entry = mapping.get(lesson_dir)
    if not source_entry:
        return {"ok": False, "course_created": False, "lesson_created": False,
                "local_path": local_path, "skilljar_lesson_id": "",
                "error": f"Source lesson not in Skilljar mapping: {lesson_dir}. "
                         "Run skilljar_sync.py --generate-mapping first."}

    source_course_id = source_entry["skilljar_course_id"]
    source_skilljar_lesson_id = source_entry["skilljar_lesson_id"]

    try:
        # --- Resolve or create the target course ---
        target_parts = Path(target_dir).parts
        target_course_folder = target_parts[2]  # e.g. "Connect To Data 2026.1"
        target_course_prefix = f"{target_parts[0]}/{target_parts[1]}/{target_course_folder}"

        existing_course_id = _find_course_id_in_mapping(target_course_prefix, mapping)
        course_created = False
        if existing_course_id:
            new_course_id = existing_course_id
        else:
            source_course = _get_course(source_course_id, api_key)
            new_course = _create_course(target_course_folder, source_course, api_key)
            new_course_id = new_course["id"]
            course_created = True

        # --- Create the lesson in the target course ---
        source_lesson = _get_lesson(source_skilljar_lesson_id, api_key)
        lesson_title = source_lesson.get("title", target_parts[3])
        lesson_type = source_lesson.get("type", "HTML")
        lesson_order = source_lesson.get("order", 0)

        new_lesson = _create_lesson(new_course_id, lesson_title, lesson_type, lesson_order, api_key)
        new_lesson_id = new_lesson["id"]

        # --- Push content ---
        _patch_lesson_html(new_lesson_id, html, api_key)

    except RuntimeError as exc:
        return {"ok": False, "course_created": course_created, "lesson_created": False,
                "local_path": local_path, "skilljar_lesson_id": "", "error": str(exc)}

    # --- Persist new mapping entry ---
    mapping[target_dir] = {
        "skilljar_lesson_id": new_lesson_id,
        "skilljar_course_id": new_course_id,
        "_title": lesson_title,
        "_course_title": target_course_folder,
    }
    mapping_path.write_text(json.dumps(mapping, indent=2, ensure_ascii=False), encoding="utf-8")

    return {"ok": True, "course_created": course_created, "lesson_created": True,
            "local_path": local_path, "skilljar_lesson_id": new_lesson_id,
            "skilljar_course_id": new_course_id, "error": None}


# ---------------------------------------------------------------------------
# Simple direct push (legacy / when target is already in mapping)
# ---------------------------------------------------------------------------

def push_lesson(lesson_id: str, html: str, api_key: str, mapping: dict) -> dict:
    entry = mapping.get(lesson_id)
    if not entry:
        return {"ok": False, "skilljar_lesson_id": "",
                "error": f"No Skilljar mapping entry for lesson: {lesson_id}. "
                         "Add it to data/skilljar-mapping.json."}
    skilljar_id = entry.get("skilljar_lesson_id", "")
    if not skilljar_id:
        return {"ok": False, "skilljar_lesson_id": "",
                "error": f"skilljar_lesson_id is empty in mapping for: {lesson_id}"}
    try:
        _patch_lesson_html(skilljar_id, html, api_key)
        return {"ok": True, "skilljar_lesson_id": skilljar_id, "error": None}
    except RuntimeError as exc:
        return {"ok": False, "skilljar_lesson_id": skilljar_id, "error": str(exc)}


def load_mapping(mapping_path: Path) -> dict:
    if not mapping_path.exists():
        return {}
    with open(mapping_path, encoding="utf-8") as f:
        return json.load(f)
