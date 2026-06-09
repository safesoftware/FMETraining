# Plan: Edit alt text + replace images in the Lesson Edits WYSIWYG

**Jira:** [KNOW-2279](https://safesoftware.atlassian.net/browse/KNOW-2279)
**Branch:** `feature/KNOW-2279-wysiwyg-image-edit` (off `main`)
**Approved:** 2026-05-05

## Context

The Lesson Edits tab (`pipeline/report.py`) is a custom `contenteditable` editor with a small toolbar (Bold / Italic / H1–H4 / Link). Today, when a user wants to swap an image, the only path is: delete the existing `<img>` (which had hand-curated alt text), then paste a new image from the clipboard. The browser inserts a fresh `<img>` with **empty alt** and there is no UI for setting it. Result: lost alt text, no way to write new alt text without hand-editing the HTML.

LLM-generated alt-text *suggestions* exist (`pipeline/enrich_alt_text.py` → cards rendered at `pipeline/report.py:1027-1040`), but they only cover images present at run time, not user-pasted ones, and they aren't editable.

This plan adds:

1. **Click any image → a floating popover** with an alt-text input and a "Replace…" control (paste from clipboard / upload from file).
2. **An "Image" button** in the format toolbar that opens the same popover for the currently-selected image (fallback affordance).
3. **Old alt is preserved** through a replace and pre-filled into the input so the user can keep it, tweak it, or rewrite it.

No backend changes are needed. Replaced images become `data:` URIs, which the existing `pipeline/lesson_image_upload.py` flow already re-hosts to S3 on save (`serve.py:_upload_lesson_images()` at `serve.py:705-737`, called from the `/api/save-lesson` handler).

## Sibling work to be aware of

`feature/KNOW-2275-wysiwyg-lists` is also editing the Lesson Edits toolbar to add bullet/numbered list support. Both branches touch the toolbar HTML at `pipeline/report.py:350-360` and the `leRenderLesson()` body around line 1058. Whichever lands second will resolve a small conflict in those two regions.

## Files to modify

- `pipeline/report.py` — **only file touched**. All changes live inside the lesson-edits tab UI:
  - HTML: toolbar button + popover + hidden file input (around lines 350-360 / new sibling near line 363).
  - CSS: a few rules for the popover, selected-image outline, hidden file input.
  - JS: image click handler, popover open/close/position, alt save, replace flows, toolbar-button handler, save-time cleanup hook.

## UX flow

**Click on image** (inside `#le-lesson-body`):
- Image gets a blue selection outline (`.le-img-selected`).
- Popover anchors below the image with: alt input pre-filled, **Replace…** button, **Save**, **Cancel**.
- Clicking outside the popover, pressing Esc, or clicking another image dismisses it (Esc / outside-click = cancel; explicit Save commits).

**Toolbar "Image" button**:
- If an image is currently selected, opens the popover for it.
- If not, briefly flashes a hint in the save banner ("Click an image first to edit it") and otherwise no-ops.

**Replace…** dropdown menu (two items):
- **Paste from clipboard** → `navigator.clipboard.read()`, finds the first `image/*` blob, reads it as a data URI, swaps `img.src`. If no image on clipboard, shows inline error in the popover.
- **Upload from file…** → triggers a hidden `<input type="file" accept="image/*">`, FileReader → data URI → swap `img.src`.

After replace, the alt input keeps the old alt (user can edit). On **Save**, both `alt` and `src` are committed to the DOM. The popover closes.

## Implementation details

### State (top-level in the existing IIFE-ish script block)
```js
let leSelectedImage = null;   // currently-selected <img> element, or null
```

### CSS additions (near existing `.fmt-toolbar` / `.tc-popup` styles)
```css
#le-lesson-body img.le-img-selected { outline: 2px solid #2563eb; outline-offset: 2px; cursor: pointer; }
.le-img-popover {
  position: absolute; z-index: 1000; background: #fff; border: 1px solid #d1d5db;
  border-radius: 6px; box-shadow: 0 4px 12px rgba(0,0,0,0.15); padding: 10px;
  min-width: 320px; display: none; font-size: 13px;
}
.le-img-popover.visible { display: block; }
.le-img-popover label { display:block; font-weight: 600; margin-bottom: 4px; }
.le-img-popover input[type=text] { width: 100%; padding: 6px 8px; box-sizing: border-box; }
.le-img-popover .le-img-actions { display:flex; gap:6px; margin-top:8px; align-items:center; }
.le-img-popover .le-img-err { color:#b91c1c; margin-top:6px; min-height:1.2em; }
.le-img-popover .le-img-replace-menu { position:relative; display:inline-block; }
.le-img-popover .le-img-replace-menu > div {
  position:absolute; top:100%; left:0; background:#fff; border:1px solid #d1d5db;
  border-radius:4px; box-shadow:0 2px 6px rgba(0,0,0,0.1); display:none; min-width:180px; z-index:1;
}
.le-img-popover .le-img-replace-menu.open > div { display:block; }
.le-img-popover .le-img-replace-menu button { display:block; width:100%; text-align:left; border:none; background:none; padding:6px 10px; cursor:pointer; }
.le-img-popover .le-img-replace-menu button:hover { background:#f3f4f6; }
#le-img-file-input { display:none; }
```

### HTML additions

Toolbar button — append to `#le-fmt-toolbar` at `pipeline/report.py:359`:
```html
<button onclick="leEditImage()" title="Edit image (alt text / replace)">Image</button>
```

Popover + hidden file input — add as a sibling of `#le-lesson-body`, right after line 365:
```html
<div id="le-img-popover" class="le-img-popover" role="dialog" aria-label="Edit image">
  <label for="le-img-alt">Alt text</label>
  <input type="text" id="le-img-alt" placeholder="Describe the image" />
  <div class="le-img-actions">
    <span class="le-img-replace-menu" id="le-img-replace-menu">
      <button type="button" onclick="leImgToggleReplaceMenu()">Replace ▾</button>
      <div>
        <button type="button" onclick="leImgReplaceFromClipboard()">Paste from clipboard</button>
        <button type="button" onclick="leImgReplaceFromFile()">Upload from file…</button>
      </div>
    </span>
    <span style="flex:1"></span>
    <button type="button" onclick="leImgSave()">Save</button>
    <button type="button" onclick="leImgClosePopover()">Cancel</button>
  </div>
  <div class="le-img-err" id="le-img-err"></div>
</div>
<input type="file" id="le-img-file-input" accept="image/*" />
```

### JS additions (placed near `leInsertLink()` at line 1530)

```js
function leOnImageClick(e) {
  const img = e.target.closest('img');
  if (!img) return;
  if (!document.getElementById('le-lesson-body').contains(img)) return;
  e.preventDefault();
  leOpenImgPopover(img);
}

function leOpenImgPopover(img) {
  document.querySelectorAll('#le-lesson-body img.le-img-selected')
          .forEach(el => el.classList.remove('le-img-selected'));
  img.classList.add('le-img-selected');
  leSelectedImage = img;

  const pop = document.getElementById('le-img-popover');
  document.getElementById('le-img-alt').value = img.getAttribute('alt') || '';
  document.getElementById('le-img-err').textContent = '';

  // Anchor below the image, clamped to viewport horizontally
  const r = img.getBoundingClientRect();
  const top = window.scrollY + r.bottom + 6;
  const left = window.scrollX + Math.max(8, Math.min(r.left, window.innerWidth - 340));
  pop.style.top = top + 'px';
  pop.style.left = left + 'px';
  pop.classList.add('visible');
  document.getElementById('le-img-alt').focus();
}

function leImgClosePopover() {
  document.getElementById('le-img-popover').classList.remove('visible');
  document.getElementById('le-img-replace-menu').classList.remove('open');
  if (leSelectedImage) leSelectedImage.classList.remove('le-img-selected');
  leSelectedImage = null;
}

function leImgSave() {
  if (!leSelectedImage) return leImgClosePopover();
  const alt = document.getElementById('le-img-alt').value;
  leSelectedImage.setAttribute('alt', alt);
  leImgClosePopover();
}

function leImgToggleReplaceMenu() {
  document.getElementById('le-img-replace-menu').classList.toggle('open');
}

async function leImgReplaceFromClipboard() {
  const err = document.getElementById('le-img-err');
  err.textContent = '';
  try {
    const items = await navigator.clipboard.read();
    for (const item of items) {
      const type = item.types.find(t => t.startsWith('image/'));
      if (!type) continue;
      const blob = await item.getType(type);
      const dataUri = await new Promise((res, rej) => {
        const fr = new FileReader();
        fr.onload = () => res(fr.result);
        fr.onerror = () => rej(fr.error);
        fr.readAsDataURL(blob);
      });
      leSelectedImage.setAttribute('src', dataUri);
      document.getElementById('le-img-replace-menu').classList.remove('open');
      return;
    }
    err.textContent = 'No image on the clipboard.';
  } catch (e) {
    err.textContent = 'Clipboard read failed: ' + (e.message || e);
  }
}

function leImgReplaceFromFile() {
  document.getElementById('le-img-replace-menu').classList.remove('open');
  document.getElementById('le-img-file-input').click();
}

function leImgOnFileChosen(e) {
  const f = e.target.files && e.target.files[0];
  if (!f || !leSelectedImage) return;
  const fr = new FileReader();
  fr.onload = () => leSelectedImage.setAttribute('src', fr.result);
  fr.readAsDataURL(f);
  e.target.value = ''; // allow re-picking the same file
}

function leEditImage() {
  if (leSelectedImage && document.getElementById('le-lesson-body').contains(leSelectedImage)) {
    leOpenImgPopover(leSelectedImage);
    return;
  }
  // Try to find an image inside the current text selection
  const sel = window.getSelection();
  if (sel && sel.rangeCount) {
    const c = sel.getRangeAt(0).commonAncestorContainer;
    const root = (c.nodeType === 1 ? c : c.parentElement);
    const img = root && root.querySelector && root.querySelector('img');
    if (img && document.getElementById('le-lesson-body').contains(img)) {
      leOpenImgPopover(img);
      return;
    }
  }
  const banner = document.getElementById('le-save-banner');
  banner.style.display = 'block';
  banner.innerHTML = 'Click an image in the editor first, then press the Image button.';
  setTimeout(() => { banner.style.display = 'none'; }, 2500);
}
```

### Wiring (one-time, at the end of `leRenderLesson()` at line 1058 just after `leUpdateNavFloat();`)

```js
// Image-edit popover wiring (idempotent)
if (!_lessonBodyEl.dataset.imgEditWired) {
  _lessonBodyEl.addEventListener('click', leOnImageClick);
  document.getElementById('le-img-file-input').addEventListener('change', leImgOnFileChosen);
  document.addEventListener('click', (e) => {
    const pop = document.getElementById('le-img-popover');
    if (!pop.classList.contains('visible')) return;
    if (pop.contains(e.target)) return;
    if (e.target.closest('#le-lesson-body img')) return;
    leImgClosePopover();
  });
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && document.getElementById('le-img-popover').classList.contains('visible')) {
      leImgClosePopover();
    }
  });
  _lessonBodyEl.dataset.imgEditWired = '1';
}
```

### Save-time cleanup

Inside `leGetCleanHtml()` (around `pipeline/report.py:1383-1388`, where the function already strips popups and helper UI), strip the selection class so it doesn't leak into saved HTML. Add right before the `return { html: body.innerHTML, plan }` at line 1435:

```js
body.querySelectorAll('img.le-img-selected').forEach(img => img.classList.remove('le-img-selected'));
```

The popover, file input, and toolbar button live **outside** `#le-lesson-body`, so they're already excluded from the cloned `body` that `leGetCleanHtml` operates on — no extra work needed for them.

### Interaction with existing alt-text suggestion cards

When an image has a pending suggestion card from `enrich_alt_text.py`, manual editing via the popover still works (it just sets `alt` on the `<img>`). The suggestion card remains until the user accepts/rejects it via existing UI. This is the least-surprising behavior and adds no extra logic.

## Out of scope (intentionally)

- **Undo/redo for image edits.** The existing `leUndoStack`/`leRedoStack` only tracks suggestion accept/reject. Browser-native Ctrl+Z does not undo `setAttribute`. Not adding now — user can re-replace to revert.
- **Drag-and-drop replace.** Skipped per user choice during planning.
- **Backend changes.** None — `pipeline/lesson_image_upload.py` already re-hosts data-URI `<img>` tags to S3.

## Verification

1. **Generate a report** for a run that has lesson edits, then start the server:
   ```bash
   python serve.py 8080
   # open http://localhost:8080
   # open http://localhost:8080/artifacts/report-{RUN_ID}.html → Lesson Edits tab
   ```

2. **Click an image** in the editor → popover appears with the existing alt text pre-filled. Edit it, click Save → the `<img alt>` updates (verify via DevTools).

3. **Replace flow (file)** — click an image, Replace ▾ → Upload from file…, pick a PNG. The image swaps; alt input still shows old alt. Click Save.

4. **Replace flow (clipboard)** — copy an image from anywhere (screenshot tool, browser image), click an editor image, Replace ▾ → Paste from clipboard. The image swaps. (Clipboard API requires HTTPS or `localhost`; on failure the popover surfaces a clear error.)

5. **Toolbar fallback** — click an image to select it, click outside, then click the **Image** toolbar button → popover re-opens for that image. With no image selected, button shows the inline hint.

6. **Esc / outside-click** dismisses the popover with no DOM mutation.

7. **Save end-to-end** — make an alt edit and a replace, click "Save to Version Folder". Confirm in the saved `index.html`:
   - `alt="…"` reflects the new value.
   - The replaced `<img>` has an `https://s3.…amazonaws.com/…` URL (re-hosted by `_upload_lesson_images`), **not** a `data:` URI.
   - No `class="le-img-selected"` leaks into the file.

8. **Pre-existing alt-text suggestion cards** still render and accept/reject correctly when the image is one with a suggestion (sanity check — no regression).
