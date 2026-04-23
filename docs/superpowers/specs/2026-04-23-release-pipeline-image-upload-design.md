# Release Pipeline: Automatic Image Upload to Skilljar

**Date:** 2026-04-23  
**Jira:** KNOW-2247  
**Status:** Approved

## Problem

When the release pipeline pushes lesson HTML to Skilljar, images referenced as relative paths (e.g. `images/1712770556258.gif`) are not displayed — Skilljar cannot resolve local repo paths. Previously the pipeline warned and pushed broken HTML.

## Goal

Images are automatically uploaded to Skilljar during the release push. The lesson HTML delivered to Skilljar contains hosted CDN URLs, not relative paths.

## User Experience

When you run a release, any local images in the lesson are silently uploaded to Skilljar before the HTML is patched. The `Pushed: <lesson>` confirmation means images are working. If an image takes a moment to process, the pipeline waits and retries (up to `SKILLJAR_IMAGE_UPLOAD_RETRIES`). If a specific image fails, a warning names it and the lesson push still completes with everything else intact.

## Scope

**In scope:**
- Automatic upload of local image files during `execute_release` (both standard release and draft/push-only)
- Retry/poll until Skilljar finishes processing the uploaded asset
- Rewrite relative `src=` paths in HTML with the Skilljar-hosted URL before patching
- `SKILLJAR_IMAGE_UPLOAD_RETRIES` config var (default 10, already in `.env.sample`)
- Non-fatal per-image failures: warn and continue

**Out of scope:**
- WYSIWYG editor image upload (tracked in KNOW-2249)
- Images already resolved from existing lesson HTML (existing `_rewrite_images` handles these)

## Architecture

### New primitives in `skilljar_push.py`

**`_upload_asset(file_path, api_key) → str`**  
Multipart POST to `POST /v1/assets` with the image file. Returns the Skilljar `asset_id`.

**`_wait_for_asset_url(asset_id, api_key, max_retries) → str | None`**  
Polls `GET /v1/assets/{id}` with a 2-second sleep between attempts. Returns `embed_link_url` once available. Returns `None` if `max_retries` is exhausted.

### New orchestration function in `skilljar_release.py`

**`_upload_and_rewrite_images(html, relative_paths, lesson_dir, repo_root, api_key, max_retries) → (str, list[str])`**  
For each relative path:
1. Resolve the local file at `{lesson_dir}/images/{filename}`
2. Upload via `_upload_asset`
3. Poll via `_wait_for_asset_url`
4. Replace the relative `src=` in HTML with the hosted URL

Returns `(rewritten_html, failed_paths)`. Failed paths are images that couldn't be uploaded or timed out.

### Config

`SKILLJAR_IMAGE_UPLOAD_RETRIES: int` added to `config.py`, read from env (default 10). Passed through `execute_release` → `_upload_and_rewrite_images` → `_wait_for_asset_url`.

## Data Flow in `execute_release`

```
Read local HTML
    ↓
_rewrite_images(html, ref_html)
    → html with known URLs substituted + list of unresolved relative paths
    ↓ (if any unresolved)
_upload_and_rewrite_images(html, unresolved, ...)
    → html with uploaded CDN URLs substituted + list of failed paths
    ↓ (if any failed)
WARNING logged per failed image
    ↓
_patch_lesson_html(lesson_id, html, api_key)
```

## Error Handling

| Scenario | Behaviour |
|---|---|
| Local image file missing | Warning: "could not find local file for `images/foo.gif`", image skipped |
| Skilljar upload fails (HTTP error) | Warning: "failed to upload `images/foo.gif`", image skipped |
| Asset URL not ready within max_retries | Warning: "timed out waiting for hosted URL for `images/foo.gif`", image skipped |
| `_patch_lesson_html` fails | ERROR, lesson counted as push error (existing behaviour) |

All image failures are non-fatal to the lesson push.
