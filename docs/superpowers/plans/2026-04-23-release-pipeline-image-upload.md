# Release Pipeline: Automatic Image Upload Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Automatically upload local lesson images to Skilljar during `execute_release`, replacing relative `src=` paths in the pushed HTML with hosted CDN URLs.

**Architecture:** Two new low-level helpers (`_upload_asset`, `_wait_for_asset_url`) go in `skilljar_push.py`. A new orchestration function (`_upload_and_rewrite_images`) in `skilljar_release.py` calls them per-image and rewrites HTML. `execute_release` calls this after `_rewrite_images` to handle any remaining relative paths.

**Tech Stack:** Python stdlib only — `urllib.request` (multipart POST), `mimetypes`, `uuid`, `time`. No new dependencies.

---

## File Map

| File | Change |
|---|---|
| `pipeline/config.py` | Add `SKILLJAR_IMAGE_UPLOAD_RETRIES` constant |
| `pipeline/skilljar_push.py` | Add `_upload_asset`, `_wait_for_asset_url`; add `import time, mimetypes, uuid` |
| `pipeline/skilljar_release.py` | Add `_upload_and_rewrite_images`; update `execute_release` signature and image-handling block; add `_upload_asset`, `_wait_for_asset_url` to import |
| `serve.py` | Pass `SKILLJAR_IMAGE_UPLOAD_RETRIES` to `execute_release` |
| `tests/unit/test_skilljar_push.py` | New — unit tests for `_upload_asset` and `_wait_for_asset_url` |
| `tests/unit/test_skilljar_release.py` | New — unit tests for `_upload_and_rewrite_images` |

---

## Task 1: Add config constant

**Files:**
- Modify: `pipeline/config.py:62-64`

- [ ] **Step 1: Add `SKILLJAR_IMAGE_UPLOAD_RETRIES` to config.py**

After the existing Skilljar constants (line 64), add:

```python
SKILLJAR_IMAGE_UPLOAD_RETRIES: int = int(os.getenv("SKILLJAR_IMAGE_UPLOAD_RETRIES", "10"))
```

The block should now read:

```python
# Skilljar API credentials (for Push to Skilljar feature)
SKILLJAR_API_KEY: str = os.getenv("SKILLJAR_API_KEY", "")
SKILLJAR_DOMAIN: str = os.getenv("SKILLJAR_DOMAIN", "")
SKILLJAR_MAPPING_PATH: Path = REPO_ROOT / "data" / "skilljar-mapping.json"
SKILLJAR_IMAGE_UPLOAD_RETRIES: int = int(os.getenv("SKILLJAR_IMAGE_UPLOAD_RETRIES", "10"))
```

- [ ] **Step 2: Verify import works**

```bash
cd /workspaces/fme-training-automation
python -c "from pipeline.config import SKILLJAR_IMAGE_UPLOAD_RETRIES; print(SKILLJAR_IMAGE_UPLOAD_RETRIES)"
```

Expected output: `10`

- [ ] **Step 3: Commit**

```bash
git add pipeline/config.py
git commit -m "feat: add SKILLJAR_IMAGE_UPLOAD_RETRIES config var"
```

---

## Task 2: Add `_upload_asset` and `_wait_for_asset_url` to skilljar_push.py

**Files:**
- Modify: `pipeline/skilljar_push.py`
- Create: `tests/unit/test_skilljar_push.py`

- [ ] **Step 1: Write failing tests**

Create `tests/unit/test_skilljar_push.py`:

```python
"""Unit tests for image upload helpers in skilljar_push.py."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, call, patch

import pytest

from pipeline.skilljar_push import _upload_asset, _wait_for_asset_url


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
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd /workspaces/fme-training-automation
python -m pytest tests/unit/test_skilljar_push.py -v 2>&1 | head -30
```

Expected: `ImportError` or `AttributeError` — `_upload_asset` and `_wait_for_asset_url` don't exist yet.

- [ ] **Step 3: Add imports to skilljar_push.py**

At the top of `pipeline/skilljar_push.py`, add `mimetypes`, `time`, and `uuid` to the existing stdlib imports:

```python
from __future__ import annotations

import base64
import json
import mimetypes
import re
import shutil
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path
```

- [ ] **Step 4: Add `_upload_asset` to skilljar_push.py**

Add after the `_get_content_items` function (after line ~76):

```python
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
            return result["id"]
    except urllib.error.HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {exc.code} POST /assets: {error_body}") from exc


def _wait_for_asset_url(asset_id: str, api_key: str, max_retries: int = 10) -> str | None:
    """Poll GET /assets/{id} until embed_link_url is available. Returns None if exhausted."""
    for _ in range(max_retries):
        asset = _request("GET", f"/assets/{asset_id}", api_key)
        url = asset.get("embed_link_url") or asset.get("download_url")
        if url:
            return url
        time.sleep(2)
    return None
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
cd /workspaces/fme-training-automation
python -m pytest tests/unit/test_skilljar_push.py -v
```

Expected: all 6 tests PASS.

- [ ] **Step 6: Commit**

```bash
git add pipeline/skilljar_push.py tests/unit/test_skilljar_push.py
git commit -m "feat: add _upload_asset and _wait_for_asset_url to skilljar_push"
```

---

## Task 3: Add `_upload_and_rewrite_images` to skilljar_release.py

**Files:**
- Modify: `pipeline/skilljar_release.py`
- Create: `tests/unit/test_skilljar_release.py`

- [ ] **Step 1: Write failing tests**

Create `tests/unit/test_skilljar_release.py`:

```python
"""Unit tests for _upload_and_rewrite_images in skilljar_release.py."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from pipeline.skilljar_release import _upload_and_rewrite_images


class TestUploadAndRewriteImages:
    def test_rewrites_relative_src_with_hosted_url(self, tmp_path):
        (tmp_path / "images").mkdir()
        (tmp_path / "images" / "photo.png").write_bytes(b"\x89PNG")

        html = '<img src="images/photo.png" alt="test">'

        with patch("pipeline.skilljar_release._upload_asset", return_value="asset1"):
            with patch("pipeline.skilljar_release._wait_for_asset_url", return_value="https://cdn.example.com/photo.png"):
                result_html, failed = _upload_and_rewrite_images(
                    html, ["images/photo.png"], tmp_path.name,
                    tmp_path.parent, "fake-key", max_retries=3,
                )

        assert 'src="https://cdn.example.com/photo.png"' in result_html
        assert failed == []

    def test_adds_to_failed_when_local_file_missing(self, tmp_path):
        html = '<img src="images/missing.gif">'
        result_html, failed = _upload_and_rewrite_images(
            html, ["images/missing.gif"], "lesson/dir",
            tmp_path, "fake-key", max_retries=3,
        )
        assert failed == ["images/missing.gif"]
        assert 'src="images/missing.gif"' in result_html  # unchanged

    def test_adds_to_failed_when_upload_raises(self, tmp_path):
        (tmp_path / "images").mkdir()
        (tmp_path / "images" / "bad.gif").write_bytes(b"GIF89a")

        html = '<img src="images/bad.gif">'
        with patch("pipeline.skilljar_release._upload_asset", side_effect=RuntimeError("HTTP 500")):
            result_html, failed = _upload_and_rewrite_images(
                html, ["images/bad.gif"], "",
                tmp_path, "fake-key", max_retries=3,
            )
        assert failed == ["images/bad.gif"]
        assert 'src="images/bad.gif"' in result_html

    def test_adds_to_failed_when_url_times_out(self, tmp_path):
        (tmp_path / "images").mkdir()
        (tmp_path / "images" / "slow.png").write_bytes(b"\x89PNG")

        html = '<img src="images/slow.png">'
        with patch("pipeline.skilljar_release._upload_asset", return_value="asset1"):
            with patch("pipeline.skilljar_release._wait_for_asset_url", return_value=None):
                result_html, failed = _upload_and_rewrite_images(
                    html, ["images/slow.png"], "",
                    tmp_path, "fake-key", max_retries=3,
                )
        assert failed == ["images/slow.png"]

    def test_handles_multiple_images(self, tmp_path):
        (tmp_path / "images").mkdir()
        (tmp_path / "images" / "a.png").write_bytes(b"\x89PNG")
        (tmp_path / "images" / "b.gif").write_bytes(b"GIF89a")

        html = '<img src="images/a.png"><img src="images/b.gif">'
        hosted = {"asset_a": "https://cdn.example.com/a.png", "asset_b": "https://cdn.example.com/b.gif"}

        upload_calls = iter(["asset_a", "asset_b"])
        url_calls = iter(["https://cdn.example.com/a.png", "https://cdn.example.com/b.gif"])

        with patch("pipeline.skilljar_release._upload_asset", side_effect=upload_calls):
            with patch("pipeline.skilljar_release._wait_for_asset_url", side_effect=url_calls):
                result_html, failed = _upload_and_rewrite_images(
                    html, ["images/a.png", "images/b.gif"], "",
                    tmp_path, "fake-key", max_retries=3,
                )

        assert 'src="https://cdn.example.com/a.png"' in result_html
        assert 'src="https://cdn.example.com/b.gif"' in result_html
        assert failed == []
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd /workspaces/fme-training-automation
python -m pytest tests/unit/test_skilljar_release.py -v 2>&1 | head -20
```

Expected: `ImportError` — `_upload_and_rewrite_images` doesn't exist yet.

- [ ] **Step 3: Add `_upload_asset` and `_wait_for_asset_url` to the import in skilljar_release.py**

Update the existing import block at the top of `pipeline/skilljar_release.py`:

```python
from pipeline.skilljar_push import (
    _VERSION_SUFFIX_RE,
    _request,
    _patch_lesson_html,
    _get_course,
    _create_course,
    _create_lesson,
    _get_lesson,
    _upload_asset,
    _wait_for_asset_url,
)
```

- [ ] **Step 4: Add `_upload_and_rewrite_images` to skilljar_release.py**

Add after the `_rewrite_images` function (after line ~61):

```python
def _upload_and_rewrite_images(
    html: str,
    relative_paths: list[str],
    lesson_dir: str,
    repo_root: Path,
    api_key: str,
    max_retries: int,
) -> tuple[str, list[str]]:
    """Upload local images to Skilljar and rewrite their src= paths in html.

    Returns (rewritten_html, failed_paths) where failed_paths are images that
    could not be uploaded or whose hosted URL could not be obtained.
    """
    url_map: dict[str, str] = {}
    failed: list[str] = []

    for rel_path in relative_paths:
        filename = Path(rel_path.split("?")[0]).name
        local_file = repo_root / lesson_dir / "images" / filename

        if not local_file.exists():
            failed.append(rel_path)
            continue

        try:
            asset_id = _upload_asset(local_file, api_key)
            hosted_url = _wait_for_asset_url(asset_id, api_key, max_retries)
        except RuntimeError:
            failed.append(rel_path)
            continue

        if hosted_url:
            url_map[rel_path] = hosted_url
        else:
            failed.append(rel_path)

    if url_map:
        def _replace_uploaded(m: re.Match) -> str:
            quote_open, path, quote_close = m.group(1), m.group(2), m.group(3)
            return f"{quote_open}{url_map.get(path, path)}{quote_close}"
        html = _RELATIVE_SRC_RE.sub(_replace_uploaded, html)

    return html, failed
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
cd /workspaces/fme-training-automation
python -m pytest tests/unit/test_skilljar_release.py -v
```

Expected: all 5 tests PASS.

- [ ] **Step 6: Commit**

```bash
git add pipeline/skilljar_release.py tests/unit/test_skilljar_release.py
git commit -m "feat: add _upload_and_rewrite_images to skilljar_release"
```

---

## Task 4: Wire `_upload_and_rewrite_images` into `execute_release`

**Files:**
- Modify: `pipeline/skilljar_release.py` (the `execute_release` function, lines ~382-626)

- [ ] **Step 1: Add `max_retries` parameter to `execute_release`**

Update the function signature from:

```python
def execute_release(
    plan: dict,
    api_key: str,
    domain: str,
    mapping: dict,
    mapping_path: Path,
    repo_root: Path,
    dry_run: bool = False,
) -> Iterator[str]:
```

To:

```python
def execute_release(
    plan: dict,
    api_key: str,
    domain: str,
    mapping: dict,
    mapping_path: Path,
    repo_root: Path,
    dry_run: bool = False,
    max_retries: int = 10,
) -> Iterator[str]:
```

- [ ] **Step 2: Replace the image-handling block in `execute_release`**

Find this block (around lines 488–513):

```python
            if not dry_run:
                # Rewrite relative image paths using absolute URLs from the existing
                # Skilljar lesson (standard release) or its previous version (draft).
                # If neither has hosted URLs (e.g. source is MODULAR), push as-is and warn.
                ref_html = ""
                if not is_push_only:
                    try:
                        ref_html = _get_lesson(lesson_id, api_key).get("content_html", "") or ""
                    except RuntimeError:
                        pass
                else:
                    prev_key, prev_entry = _find_prev_version_entry(lesson["lesson_dir"], to_version, mapping)
                    if prev_entry:
                        try:
                            ref_html = _get_lesson(prev_entry["skilljar_lesson_id"], api_key).get("content_html", "") or ""
                        except RuntimeError:
                            pass

                if ref_html:
                    html, unmatched = _rewrite_images(html, ref_html)
                    if unmatched:
                        yield f"  WARNING: {len(unmatched)} image(s) could not be resolved and will be broken: {', '.join(unmatched)}"
                else:
                    _, relative = _rewrite_images(html, "")
                    if relative:
                        yield f"  WARNING: {len(relative)} image(s) have relative paths and will not display in Skilljar (images are not yet hosted)."
```

Replace with:

```python
            if not dry_run:
                ref_html = ""
                if not is_push_only:
                    try:
                        ref_html = _get_lesson(lesson_id, api_key).get("content_html", "") or ""
                    except RuntimeError:
                        pass
                else:
                    prev_key, prev_entry = _find_prev_version_entry(lesson["lesson_dir"], to_version, mapping)
                    if prev_entry:
                        try:
                            ref_html = _get_lesson(prev_entry["skilljar_lesson_id"], api_key).get("content_html", "") or ""
                        except RuntimeError:
                            pass

                html, unresolved = _rewrite_images(html, ref_html)
                if unresolved:
                    html, failed_uploads = _upload_and_rewrite_images(
                        html, unresolved, lesson["lesson_dir"], repo_root, api_key, max_retries,
                    )
                    if failed_uploads:
                        yield f"  WARNING: {len(failed_uploads)} image(s) could not be uploaded to Skilljar: {', '.join(failed_uploads)}"
```

- [ ] **Step 3: Run existing tests to verify nothing is broken**

```bash
cd /workspaces/fme-training-automation
python -m pytest tests/unit/ -v
```

Expected: all existing tests PASS.

- [ ] **Step 4: Commit**

```bash
git add pipeline/skilljar_release.py
git commit -m "feat: upload unresolved images to Skilljar during execute_release"
```

---

## Task 5: Pass `SKILLJAR_IMAGE_UPLOAD_RETRIES` from serve.py

**Files:**
- Modify: `serve.py` (around line 575)

- [ ] **Step 1: Update the config import in serve.py**

Find the import near line 575:

```python
        from pipeline.config import SKILLJAR_API_KEY, SKILLJAR_DOMAIN, SKILLJAR_MAPPING_PATH
```

Add `SKILLJAR_IMAGE_UPLOAD_RETRIES`:

```python
        from pipeline.config import SKILLJAR_API_KEY, SKILLJAR_DOMAIN, SKILLJAR_MAPPING_PATH, SKILLJAR_IMAGE_UPLOAD_RETRIES
```

- [ ] **Step 2: Pass `max_retries` to `execute_release` in serve.py**

Find the call at lines 593–595:

```python
                for line in execute_release(
                    plan, SKILLJAR_API_KEY, SKILLJAR_DOMAIN,
                    mapping, SKILLJAR_MAPPING_PATH, REPO_ROOT, dry_run=dry_run,
                ):
```

Update to:

```python
                for line in execute_release(
                    plan, SKILLJAR_API_KEY, SKILLJAR_DOMAIN,
                    mapping, SKILLJAR_MAPPING_PATH, REPO_ROOT,
                    dry_run=dry_run, max_retries=SKILLJAR_IMAGE_UPLOAD_RETRIES,
                ):
```

- [ ] **Step 3: Run all unit tests**

```bash
cd /workspaces/fme-training-automation
python -m pytest tests/unit/ -v
```

Expected: all tests PASS.

- [ ] **Step 4: Verify the server imports cleanly**

```bash
cd /workspaces/fme-training-automation
python -c "import serve; print('OK')"
```

Expected: `OK`

- [ ] **Step 5: Commit**

```bash
git add serve.py
git commit -m "feat: pass SKILLJAR_IMAGE_UPLOAD_RETRIES into execute_release"
```
