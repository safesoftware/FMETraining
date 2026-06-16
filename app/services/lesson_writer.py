"""Write accepted lesson edits into the on-disk version tree.

Ports the legacy ``serve.py`` "Save to Version" flow
(``_compute_target_path`` / ``_sanitize_lesson_html`` /
``_upload_lesson_images`` / ``_handle_save_lesson``) into the FastAPI app.

The critical seam vs. the legacy implementation: we write under
``Settings.lesson_content_root`` rather than the repo root. The release
flow's ``scan_saved_lessons`` and the report's "saved" badge both read
*that* tree, so the FastAPI port must target the same root the worker and
report use — not the directory ``serve.py`` happens to live in.
"""
from __future__ import annotations

import re
import shutil
from pathlib import Path

from bs4 import BeautifulSoup

# Trailing course-version suffix, e.g. "Connect To Data 2025.0" → "Connect To Data".
# Matches " 2025", " 2025.0", " 2025.0.1", etc. (serve.py:44).
_COURSE_VERSION_SUFFIX = re.compile(r"\s+\d{4}[\.\d]*$")

# An <img src> that is NOT already a permanent (non-expiring) https URL needs
# re-hosting: data: URIs, relative paths, and expiring pre-signed URLs.
# (serve.py:699-702)
_NEEDS_IMAGE_UPLOAD_RE = re.compile(
    r'<img\b[^>]*?\bsrc=["\'](?!https?://[^"\']*(?<!\?Expires=))[^"\']+["\']',
    re.IGNORECASE,
)


def compute_target_path(lesson_dir: str, to_version: str) -> Path:
    """Map a source ``lesson_dir`` to its destination under ``to_version``.

    ``lesson_dir`` is ``<srcver>/<lp>/<course_folder>/<lesson...>`` (>= 4
    parts). Returns ``<to_version>/<lp>/<course_canonical> <to_version>/<lesson...>``
    as a relative ``Path`` (caller joins it onto the content root).

    Raises ``ValueError`` if ``lesson_dir`` has fewer than 4 path parts.
    Ported from ``serve.py:_compute_target_path``.
    """
    parts = Path(lesson_dir).parts
    if len(parts) < 4:
        raise ValueError(f"lesson_dir too shallow (expected 4 parts): {lesson_dir!r}")
    learning_path = parts[1]
    course_folder = parts[2]
    lesson_folder = "/".join(parts[3:])
    course_canonical = _COURSE_VERSION_SUFFIX.sub("", course_folder).strip()
    new_course_folder = f"{course_canonical} {to_version}"
    return Path(to_version) / learning_path / new_course_folder / lesson_folder


def sanitize_lesson_html(html: str) -> str:
    """Strip track-changes report chrome that must never reach saved lessons.

    Removes ``tc-*`` popup/button/explanation markup, card-link wrappers,
    ``?tab=`` links, popup-injected Jira links (``color:#93c5fd``), now-empty
    card-link spans, and empty ``<p></p>`` separators left by contenteditable
    paste. Ported from ``serve.py:_sanitize_lesson_html``.
    """
    soup = BeautifulSoup(html, "html.parser")
    # Cover both the nested-popup case and the orphan case (KNOW-2255), where
    # a wrap rendered inside an <a> caused the parser to re-parent buttons /
    # inner links out of .tc-popup. Also strip the buttons by their own class
    # in case .tc-btns was decomposed before reaching them.
    for cls in (
        "tc-popup", "tc-btns", "tc-explanation", "tc-issue-links",
        "tc-accept", "tc-reject", "card-link", "card-link-wrap", "rec-id",
    ):
        for el in soup.find_all(class_=cls):
            el.decompose()
    for a in soup.find_all("a", href=True):
        if a["href"].startswith("?tab="):
            a.decompose()
        elif "color:#93c5fd" in (a.get("style") or ""):
            # Popup-injected Jira issue links use this specific colour; never in lesson content
            a.decompose()
    # Remove the card-link wrapper span left empty after its <a> was stripped
    for span in soup.find_all("span", style=True):
        if "display:block" in span.get("style", "") and not span.get_text(strip=True):
            span.decompose()
    # Strip empty <p></p> separators left behind by contenteditable when pasting.
    # Browsers wrap pasted images in <p>...</p> and append an empty <p></p> after,
    # which Skilljar renders as an extra blank line. Only remove paragraphs with
    # no element children and no text — keeps intentional <p><br></p> spacing.
    for p in soup.find_all("p"):
        if not p.find() and not p.get_text(strip=True):
            p.decompose()
    return str(soup)


def _upload_lesson_images(
    html: str,
    lesson_dir: str,
    *,
    content_root: Path,
    s3_bucket,
    s3_key_id,
    s3_secret,
    s3_region,
) -> str:
    """Re-host every ``<img src>`` that is not already a permanent S3 URL.

    No-op when the HTML contains nothing that needs uploading. Raises
    ``RuntimeError`` if uploads are needed but credentials are missing, the
    local file is missing, or any upload fails — the caller surfaces this as
    a 500/503. Ported from ``serve.py:_upload_lesson_images``, but with S3
    credentials threaded from app ``Settings`` rather than ``pipeline.config``
    globals (so the app's ``aws_s3_region`` default of ``us-west-2`` is what
    we honor here — NOT pipeline's ``us-east-1``).
    """
    needs_upload = (
        "data:image/" in html
        or "everpath-course-content" in html
        or "Expires=" in html
        or _NEEDS_IMAGE_UPLOAD_RE.search(html) is not None
    )
    if not needs_upload:
        return html
    # Imported lazily so the module imports cleanly even where pipeline deps
    # (boto/requests config) aren't fully wired, matching serve.py's pattern.
    from pipeline.lesson_image_upload import upload_lesson_images

    rewritten, _log = upload_lesson_images(
        html,
        lesson_dir=lesson_dir,
        # The legacy code passes REPO_ROOT here so relative/expiring images
        # resolve under <root>/<lesson_dir>/images. We pass the content root
        # instead, which is where the source lesson tree actually lives.
        repo_root=content_root,
        s3_bucket=s3_bucket,
        s3_key_id=s3_key_id,
        s3_secret=s3_secret,
        s3_region=s3_region,
    )
    return rewritten


def write_lesson(
    lesson_dir: str,
    to_version: str,
    html: str,
    *,
    force: bool,
    content_root: Path,
    s3_bucket,
    s3_key_id,
    s3_secret,
    s3_region,
) -> str:
    """Write sanitized lesson HTML into the version tree under ``content_root``.

    Returns the relative ``<target_dir>/index.html`` path string
    (forward-slashed), suitable for the API ``target_path`` field and for the
    report's "saved" badge / overwrite-confirm JS.

    Raises:
      ``ValueError`` — ``lesson_dir`` too shallow (caller → 400).
      ``FileExistsError`` — target exists and ``force`` is False (caller → 409).
                            The exception's ``filename`` carries the relative
                            ``target_path`` so the caller can echo it.
      ``RuntimeError`` — image upload / credential failure (caller → 500/503).

    Ported from ``serve.py:_handle_save_lesson``.
    """
    target_dir = compute_target_path(lesson_dir, to_version)
    target_file = content_root / target_dir / "index.html"
    target_path_str = str(target_dir / "index.html").replace("\\", "/")

    if target_file.exists() and not force:
        exc = FileExistsError(f"File already exists: {target_path_str}")
        # Stash the relative path on the exception so the route can return it
        # as the top-level `target_path` the report's overwrite-confirm JS reads.
        exc.filename = target_path_str
        raise exc

    # Upload images BEFORE writing anything so a failed upload leaves no
    # partially-written target on disk (matches serve.py ordering).
    html = _upload_lesson_images(
        html,
        lesson_dir,
        content_root=content_root,
        s3_bucket=s3_bucket,
        s3_key_id=s3_key_id,
        s3_secret=s3_secret,
        s3_region=s3_region,
    )

    target_file.parent.mkdir(parents=True, exist_ok=True)
    target_file.write_text(sanitize_lesson_html(html), encoding="utf-8")

    source_images = content_root / lesson_dir / "images"
    if source_images.is_dir():
        target_images = content_root / target_dir / "images"
        # Copy image BYTES only, not metadata. shutil.copytree defaults to
        # copy2, whose copystat() (timestamps/permissions/xattrs) raises
        # EPERM ("Operation not permitted") on bind-mounted / non-owner
        # filesystems — Docker volumes, WSL2 mounts, and the prod /content
        # mount all hit this. The lesson only needs the image bytes, so we
        # walk + shutil.copyfile (data only, no copystat) instead.
        for src_img in source_images.rglob("*"):
            if src_img.is_file():
                dst_img = target_images / src_img.relative_to(source_images)
                dst_img.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(src_img, dst_img)

    return target_path_str
