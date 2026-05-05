"""Unit tests for the LocalDiskDraftStorage path-validation + round-trip."""
from __future__ import annotations

from pathlib import Path

import pytest

from app.services.draft_storage import (
    DraftStorageError,
    LocalDiskDraftStorage,
)


# ---- happy path ---------------------------------------------------------

@pytest.mark.asyncio
async def test_write_creates_file_at_expected_path(tmp_path: Path) -> None:
    storage = LocalDiskDraftStorage(tmp_path)
    loc = await storage.write(
        to_version="2026.1",
        path="fme-form-basic/Connect To Data 2026.1/Lesson 1",
        html="<p>hello</p>",
    )
    expected = (
        tmp_path
        / "2026.1"
        / "fme-form-basic"
        / "Connect To Data 2026.1"
        / "Lesson 1"
        / "index.html"
    )
    assert Path(loc.key) == expected
    assert expected.read_text() == "<p>hello</p>"


@pytest.mark.asyncio
async def test_write_then_read_round_trip(tmp_path: Path) -> None:
    storage = LocalDiskDraftStorage(tmp_path)
    loc = await storage.write(
        to_version="2026.1", path="lp/course/lesson", html="<p>round</p>"
    )
    assert await storage.read(loc.key) == "<p>round</p>"


@pytest.mark.asyncio
async def test_re_write_overwrites(tmp_path: Path) -> None:
    storage = LocalDiskDraftStorage(tmp_path)
    await storage.write(to_version="2026.1", path="lp/c/l", html="first")
    loc = await storage.write(to_version="2026.1", path="lp/c/l", html="second")
    assert await storage.read(loc.key) == "second"


# ---- validation ---------------------------------------------------------

@pytest.mark.asyncio
async def test_rejects_invalid_to_version(tmp_path: Path) -> None:
    storage = LocalDiskDraftStorage(tmp_path)
    for bad in ("", "abc", "2026", "2026.1.2", "../etc"):
        with pytest.raises(DraftStorageError):
            await storage.write(to_version=bad, path="lp/c/l", html="x")


@pytest.mark.asyncio
async def test_rejects_path_traversal_via_path(tmp_path: Path) -> None:
    storage = LocalDiskDraftStorage(tmp_path)
    bad_paths = [
        "../escape",
        "lp/../../escape",
        "lp/c/l/..",
        "/abs",
        "//double",
        "~/relative",
        "",
    ]
    for bad in bad_paths:
        with pytest.raises(DraftStorageError):
            await storage.write(to_version="2026.1", path=bad, html="x")


@pytest.mark.asyncio
async def test_read_rejects_keys_outside_root(tmp_path: Path) -> None:
    storage = LocalDiskDraftStorage(tmp_path)
    # /etc/passwd very much exists in the dev container; storage must refuse.
    with pytest.raises(LookupError):
        await storage.read("/etc/passwd")


@pytest.mark.asyncio
async def test_read_missing_file_raises_lookup_error(tmp_path: Path) -> None:
    storage = LocalDiskDraftStorage(tmp_path)
    fake = tmp_path / "2026.1" / "missing" / "index.html"
    with pytest.raises(LookupError):
        await storage.read(str(fake))


# ---- mkdir lazy + error surfacing ---------------------------------------

def test_init_does_not_mkdir(tmp_path: Path) -> None:
    """Constructing the storage must not actually mkdir — that's deferred
    to first write so a misconfigured root doesn't crash the app at
    import time / on every request."""
    target = tmp_path / "deferred-root"
    assert not target.exists()
    LocalDiskDraftStorage(target)
    assert not target.exists()


@pytest.mark.asyncio
async def test_unwritable_root_raises_DraftStorageUnavailable(tmp_path: Path) -> None:
    """Per the route contract: filesystem failures map to a different
    exception class so the route can return 503 instead of 400."""
    from app.services.draft_storage import DraftStorageUnavailable

    # Create a regular file where the storage expects a directory. mkdir
    # against the path will fail with NotADirectoryError, which the
    # storage wraps as DraftStorageUnavailable.
    blocker = tmp_path / "blocker"
    blocker.write_text("I am a file, not a directory")
    storage = LocalDiskDraftStorage(blocker / "drafts")
    with pytest.raises(DraftStorageUnavailable):
        await storage.write(to_version="2026.1", path="lp/c/l", html="x")
