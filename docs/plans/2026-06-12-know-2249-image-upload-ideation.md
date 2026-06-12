# KNOW-2249 — User-uploaded & pasted images in the WYSIWYG editor

**Status: DRAFT ideation — for Sam's review, not yet approved.**
Author: design pass (agent), 2026-06-12. Parent epic: **KNOW-2344** (core tool).
No code written. No branches/commits. This doc exists to drive a decision.

> **TL;DR for the impatient:** the *editor-side* of this ticket already shipped
> under KNOW-2279 (paste, upload, insert, replace, alt-text all work; images
> live as `data:` URIs in the draft). What KNOW-2249 *as originally written* asks
> for — a `/api/upload-image` endpoint that re-hosts to Skilljar in `serve.py` —
> is **stale**: `serve.py` is gone (replaced by the FastAPI app), and the real
> gap is **persistence at save-to-version time + a place to serve draft images
> from**, which is exactly the open TODO at `app/routes/drafts.py:52-58`. This
> ticket should be **re-scoped** accordingly.

---

## 1. Problem & goal

**Ticket (KNOW-2249, Story, In Backlog):** "When a user pastes or uploads an
image in the lesson HTML editor in the web app, it should be hosted
automatically rather than left as a local/base64 reference." Original scope:
intercept paste/drop → `POST /api/upload-image` in `serve.py` → backend uploads
to Skilljar `POST /v1/assets` → editor inserts the hosted URL.

**Goal (restated for today's architecture):** let an editor add an image to a
lesson in the web app's "Lesson Edits" WYSIWYG by **uploading a file** or
**pasting from the clipboard** (screenshot), with sane insert/resize UX, and
have that image **persist correctly through the draft → saved-to-version flow**
and **render in the report** — without the image being a fragile inline base64
blob that bloats every draft autosave and can never be served back.

**Why the original framing no longer fits (read this before planning):**

- The web app was rewritten from `serve.py` (Flask-ish single file) to a FastAPI
  app under `app/`. There is **no `serve.py`** to add `/api/upload-image` to.
- KNOW-2249's sibling, **KNOW-2279, is already Closed** and shipped the entire
  *interactive* surface this ticket imagined: click-to-select, alt-text popover,
  Replace ▾ / Insert ▾ menu, paste-from-clipboard, upload-from-file, insert at
  caret. See §2.
- Skilljar re-hosting (`POST /v1/assets` / S3) was the old `serve.py` save path.
  In the FastAPI app that path is **not wired up** and "Save to Version Folder"
  is **deliberately disabled** (KNOW-2278 stopgap). So "automatically hosted on
  paste" has no backend to host to right now.

So KNOW-2249 is really: **"decide where pasted/uploaded image *bytes* live, and
make them survive the draft→save→report round-trip."** The clipboard/upload
*capture* is done.

---

## 2. Current state (grounded in code)

### 2.1 The editor already captures paste + upload (KNOW-2279, shipped)

All of the editor JS is emitted inline from the report generator
`pipeline/report.py` (one big f-string in `_build_html`). Relevant pieces:

- **Single funnel for paste & upload → `data:` URI:**
  `leImgApplyDataUri(dataUri, target, mode)` at `pipeline/report.py:2080`.
  Replace mode sets `target.src = dataUri`; insert mode creates a fresh
  `<img src="data:…" alt="">` at the caret (`leImgInsertAtCaret`,
  `pipeline/report.py:2057`). Then it calls `leScheduleAutosave(...)`.
- **Paste from clipboard:** `leImgReplaceFromClipboard()`
  `pipeline/report.py:2097` — `navigator.clipboard.read()` → first `image/*`
  item → `FileReader.readAsDataURL` → `leImgApplyDataUri`. Needs HTTPS/localhost
  (handled with a clear error).
- **Upload from file:** `leImgReplaceFromFile()` `pipeline/report.py:2127` +
  `leImgOnFileChosen()` `pipeline/report.py:2136`. Captures the target *before*
  the file dialog (the dialog clears selection), validates `file.type` starts
  with `image/`, `FileReader.readAsDataURL` → `leImgApplyDataUri`.
- **Insert vs replace mode:** `leEditImage()` `pipeline/report.py:2184` and
  `leOpenImgPopoverForInsert()` `pipeline/report.py:2156`. Toolbar **Image**
  button at `pipeline/report.py:388`.
- **Alt-text popover:** `leOpenImgPopover()` `pipeline/report.py:1987`,
  `leImgSave()` `pipeline/report.py:2021`; popover markup `#le-img-popover` at
  `pipeline/report.py:398`.
- **Sizing today:** `leImgStripDimensions(img)` `pipeline/report.py:2042`
  *removes* `width`/`height`/inline size on replace/insert. The QA decision in
  KNOW-2279 was "don't force a size; the editor CSS `.lesson-edit-body img {
  max-width:100% }` is display-only and Skilljar controls final size." **There is
  no resize handle / sizing UI today** — this is the genuinely open UX piece for
  KNOW-2249 (see §3.3).

> Note: the original KNOW-2249 description claims the old `serve.py`
> `_upload_lesson_images()` (lines 705-737) re-hosts these `data:` URIs to S3 on
> save. That code still exists in `pipeline/lesson_image_upload.py`
> (`upload_lesson_images`, 4-pass re-host: data-URI / relative / presigned /
> app-origin) but is only called from the **legacy `serve.py`**, which the
> FastAPI app does not run. In the deployed app this re-host never happens.

### 2.2 Path normalization (KNOW-2347) — the contract new code must respect

`pipeline/report.py:906-954` centralizes image-path forms:

- `leImgEncBase(lessonDir)` (913) — URL-encode each path segment.
- `leImgRelTail(src, encBase)` (918) — reduce *any* recognized src to its
  canonical relative tail (`images/foo.png`); returns `null` for
  `data:`/`blob:`/external → leaves them untouched.
- `leNormalizeImages(container, lessonDir)` (936) — rewrite every `<img>` to the
  display form `/lesson-content/{encBase}/images/…`; called after every
  `innerHTML` assignment.
- `leBodyHtmlForDraft(bodyEl, lessonDir)` (946) — **inverse**: reduce srcs back
  to relative before persisting a draft. **Crucially, `data:` URIs pass through
  unchanged** (relTail returns null), so a pasted image is stored as the full
  base64 blob in the draft `body_html`.

### 2.3 Draft persistence (DB, not disk for editor state)

- **Editor drafts** live in Postgres table `report_lesson_drafts`
  (`app/models/report_drafts.py`): `decisions_json`, `body_html` (Text),
  `saved_to_version_at`, `saved_to_version_path`, unique on `(run_id,
  lesson_dir)`.
- **Autosave:** `PUT /api/runs/{run_id}/report-drafts`
  (`app/routes/report_drafts.py`), service `upsert_draft()` in
  `app/services/report_drafts.py`, which runs `body_html` through
  `sanitize_report_html()` before persist.
- **Sanitizer** `app/services/html_sanitizer.py`: allowlists `img` with
  `src/alt/width/height` (`:61`), and `_img_src_is_safe` (`:90`) **explicitly
  permits `data:image/…`** (`:94-97`). So base64 images are an accepted,
  intentional draft format today.
- **`data:` blobs hit the DB on every autosave.** A 1–3 MB screenshot becomes a
  ~1.4–4 MB base64 string written to `body_html` on a 1 s debounce. There is
  **no upload size cap and no request-body limit** anywhere in the path
  (no cap in `report_drafts.py`, no client-side check in `report.py`). This is
  the main robustness/security gap (see §3.6).

### 2.4 Save-to-version + draft-image serving (the real gap)

- **"Save to Version Folder" is disabled** — `pipeline/report.py:371`
  (`#le-save-btn`, `leSave()`), per KNOW-2278 stopgap. The DB only *stamps*
  `mark_saved` (`app/services/report_drafts.py`); nothing writes lesson HTML to a
  version folder in the FastAPI app, and Critical Rule 3 forbids writing back to
  the read-only `{version}/…/index.html` + `images/` source anyway.
- **The Save-Draft API** (`POST /api/drafts`, `app/routes/drafts.py`) writes
  lesson HTML via `LocalDiskDraftStorage` to
  `{drafts_root}/{to_version}/{path}/index.html`
  (`drafts_root = /var/lib/fme-train/drafts`, `app/config.py:72`).
- **There is an explicit, named open question in the code** —
  `app/routes/drafts.py:52-58`:
  > "drafts saved via this API can contain `<img src="images/foo.png">`
  > references. Today there is no matching `/api/drafts/{id}/images/{name}`
  > endpoint to serve them … Decide between (a) S3 image bucket via the existing
  > pipeline/lesson_image_upload flow, or (b) local
  > `/var/lib/fme-train/drafts/<...>/images` served by Nginx."

  **KNOW-2249 is the ticket that should resolve this TODO.**

- **Report image serving** that *does* work: `GET /lesson-content/{rel_path}`
  (`app/routes/lesson_content.py:29`) → `resolve_content_path()`
  (`app/services/content_files.py`) streams from `lesson_content_root`
  (`app/config.py:113`, default repo root / `/app` in container) with
  path-traversal hardening (resolve + must-be-inside-root). This serves the
  *original* version-folder `images/` dirs. It has **no notion of
  user-uploaded images** — those aren't under `lesson_content_root`.

### 2.5 Undo/redo (related, KNOW-2314, not this ticket)

Undo/redo (`leUndo`/`leRedo`, `leUndoStack`/`leRedoStack`,
`pipeline/report.py:1750-1774`) currently tracks **only** accept/reject
decisions, **not** content edits or image insert/replace. KNOW-2314 (In Backlog)
owns unifying this onto native undo. **KNOW-2249 should not try to make image
ops undoable** — defer to 2314, but avoid designs that make 2314 harder (e.g.,
don't do irreversible DOM surgery on insert).

---

## 3. Key decisions & constraints

### 3.1 Storage location — THE central question
Where do the bytes of a pasted/uploaded image live? Today: inline base64 in the
DB. Options weighed in §4. Constraint: **not** under the read-only version
`images/` dir (Critical Rule 3). Must be servable by a same-origin URL the
report can load (matching the `/lesson-content` posture: public route behind the
office-IP firewall).

### 3.2 Paste/upload handling
Capture is done (§2.1). The only question is *when* the `data:` blob gets turned
into a hosted reference: **eagerly on paste** (upload immediately, insert hosted
URL — the original ticket's model) vs **lazily at save** (keep `data:` in the
draft, re-host once when persisting). Eager keeps drafts small and is closest to
the ticket; lazy is simpler and matches the old `serve.py` behavior. See §5.

### 3.3 Sizing UX
Today dimensions are stripped and Skilljar decides final size. For an internal
tool that's defensible, but pasted screenshots can render huge in the report
preview. Realistic options, cheapest first:
1. **Status quo** — strip dims, rely on `max-width:100%` (display-only). Zero
   work. Preview can look oversized but the saved HTML is clean.
2. **Preset width chips** in the popover ("S / M / L / Full" → sets `width=` on
   the `<img>`, which the sanitizer already allows). ~30 lines of JS.
3. **Drag-resize handles** — significantly more JS, interacts with
   contenteditable selection and undo (KNOW-2314). **Out of proportion** for 5
   users; not recommended.

### 3.4 Draft persistence
Whatever the format, `leBodyHtmlForDraft` must keep producing something
`sanitize_report_html` accepts and that survives the `(run_id, lesson_dir)`
upsert. If we move to hosted URLs, they must be a form `leImgRelTail` recognizes
or deliberately leaves alone, so normalization round-trips cleanly.

### 3.5 Report rendering
The report loads draft `body_html` and calls `leNormalizeImages`. For uploaded
images to render, either (a) the hosted URL is absolute/same-origin and
`leImgRelTail` returns `null` (left untouched — renders directly), or (b) it's a
new relative form `leImgRelTail`/`leNormalizeImages` learn to map to a new
serving route. (a) is simpler.

### 3.6 Security / robustness
- **Size cap.** Add a client-side cap (reject > N MB before insert) **and** a
  server-side body/size limit. Today neither exists — a few big screenshots can
  bloat `body_html` unboundedly and slow every autosave. This is the single
  most important robustness fix and should land regardless of which option.
- **Content-type validation.** Client checks `file.type`/clipboard type; server
  must re-validate by sniffing magic bytes (don't trust the declared type) and
  allowlist `png/jpeg/gif/webp`.
- **Path traversal.** Any new uploads dir reuses the resolve-inside-root pattern
  from `content_files.resolve_content_path` / `LocalDiskDraftStorage`.
- **XSS.** `sanitize_report_html` already blocks `data:text/html`, `onerror=`,
  etc. Keep routing all persisted HTML through it. If we stop allowing `data:`
  in saved drafts (after re-hosting), tighten the sanitizer to drop `data:`
  except transiently.
- **Auth posture.** An upload endpoint **must** be under `/api/` (auth-gated),
  unlike the public read-only `/lesson-content`. Writes need a logged-in user;
  associate uploads with `run_id` + user.

---

## 4. Design options (storage)

ASCII flows (shared by all options — capture is unchanged from KNOW-2279):

```
PASTE                                   UPLOAD
─────                                   ──────
Ctrl+V / Image▾ → Paste                 Image▾ → Upload from file…
   │                                       │
   ▼                                       ▼
navigator.clipboard.read()              <input type=file accept=image/*>
   │  first image/* item                   │  validate file.type + SIZE (new)
   ▼                                        ▼
FileReader.readAsDataURL ───────┬───────────┘
                                ▼
                       leImgApplyDataUri(dataUri, target, mode)
                                │
                 ┌──────────────┴───────────────┐
          replace mode                      insert mode
       target.src = …                    new <img> at caret
       stripDimensions                   leImgInsertAtCaret
                 └──────────────┬───────────────┘
                                ▼
                       leScheduleAutosave()   ← divergence point (§5)
```

Resize popover sketch (Option = preset chips, §3.3 opt 2):

```
┌─ Image ───────────────────────────────┐
│ Alt text: [ A person clicking Run     ]│
│ Size:  ( S ) ( M ) (•L•) ( Full )      │   ← sets width= ; Full removes width
│ [ Replace ▾ ]                  [ Save ]│
└────────────────────────────────────────┘
```

### Option A — Per-draft uploads dir on disk, served by a new route
Bytes written to `{drafts_root}/_uploads/{run_id}/{uuid}.{ext}` (or under the
existing draft path). New `GET /lesson-content/...` sibling or
`/api/runs/{run_id}/uploads/{name}` serves them. Editor inserts a same-origin
URL; draft stores that URL (not base64).

- **Pros:** drafts stay small; reuses `LocalDiskDraftStorage` + the resolve-
  inside-root hardening; backed up by the EBS snapshot like other draft state;
  no cloud creds needed; matches "keep state on the box" decision
  (`app/config.py:68-72`). Same-origin URL → `leImgRelTail` leaves it alone →
  renders directly.
- **Cons:** new write endpoint + new serve route + cleanup/GC of orphaned
  uploads when a draft is reset/deleted; two image roots to reason about
  (version `images/` vs uploads).

### Option B — S3/MinIO via the existing `lesson_image_upload` flow
Wire the FastAPI app to call `pipeline/lesson_image_upload.upload_lesson_images`
(or its `_upload_and_rewrite_images` helper) so `data:` URIs / files go to
`aws_s3_bucket` (MinIO locally — buckets already declared in compose, incl.
`fme-train-prod-images`). Editor/draft store the S3 URL.

- **Pros:** durable, CDN-able, closest to the *original* ticket and to how
  Skilljar ultimately wants hosted URLs; re-host logic already written & tested.
- **Cons:** **disproportionate for 5 users** — requires live AWS creds in the
  app process (today only the legacy pipeline touches S3; `app/config.py:95-99`
  exists but the app doesn't use it), bucket lifecycle/perms, egress; MinIO in
  dev adds a moving part. Heavier ops for marginal benefit at this scale.

### Option C — Keep base64 inline (status quo) + just add guards
Don't add storage at all. Keep `data:` in the draft (sanitizer already allows
it), but add the size cap + content sniff (§3.6) and call it done. Re-hosting to
hosted URLs only happens later, at the eventual Skilljar push (KNOW-2247), not in
the editor.

- **Pros:** least code; nothing new to serve, secure, GC, or back up beyond the
  DB; the editor already does this. Defensible for an internal preview tool.
- **Cons:** DB `body_html` bloats with base64; every autosave ships MBs;
  doesn't resolve the `drafts.py:52-58` TODO (saved-draft preview still can't
  serve `images/foo.png` for *file-referenced* images — though pasted ones are
  inline). Doesn't actually "host" anything, so it under-delivers the ticket's
  intent if Sam wants hosted URLs now.

---

## 5. Recommended approach

**Recommend Option A (per-draft uploads dir on disk + serve route), with the
re-host done *lazily* (at autosave/persist, not eagerly on paste), plus the §3.6
guards as a mandatory slice — and ship the size-cap guard *first* on its own.**

Rationale, proportionate to a 5-user internal tool:
- It keeps all user state on the box (consistent with the deliberate
  "drafts on disk, backed by EBS snapshot" decision at `app/config.py:68-72`),
  needs **no AWS creds in the app**, and reuses the existing path-hardening and
  `LocalDiskDraftStorage`. That's the right weight — Option B's cloud machinery
  is SaaS-grade overkill here, and Option C leaves the DB-bloat and
  `drafts.py:52-58` TODO unresolved.
- **Lazy** (re-host on persist) over **eager** (upload on paste): paste/upload
  capture already produces a `data:` URI and triggers autosave. The smallest
  change is to have the persist path (a) extract `data:` blobs, (b) write them to
  the uploads dir, (c) rewrite the stored `body_html` to same-origin URLs. The
  editor stays untouched; one server-side function does the work; matches the
  old `serve.py` mental model. Eager upload-on-paste means new client wiring,
  loading/error states mid-paste, and orphan management for blobs whose draft is
  never saved — more surface for little gain at 5 users.
- **Sizing:** ship **status quo (strip dims)** for v1; add **preset width chips**
  (§3.3 opt 2) only if Sam wants it. No drag handles.
- **Sequencing:** the size cap + content sniff (§3.6) is independently valuable
  and unblocks nothing else — land it first as a tiny PR so the DB-bloat risk is
  capped even before storage work begins.

If Sam wants hosted URLs *now* because Skilljar push is imminent, Option B
becomes more attractive — but I'd still wire it lazily and gate it behind the
same guards.

---

## 6. Data / storage & integration model (for Option A)

**Where bytes live:**
`{drafts_root}/_uploads/{run_id}/{sha256-or-uuid}.{ext}` (new subtree under the
existing `drafts_root`, kept *outside* any `{version}/.../images/` dir).
Content-addressed names dedupe identical pastes and avoid collisions.

**How referenced in draft HTML:**
A new canonical relative form, e.g. `_uploads/{name}.png`, OR a same-origin
absolute URL `/run-uploads/{run_id}/{name}.png`. Extend the KNOW-2347 helpers:
- `leImgRelTail` learns the `/run-uploads/{run_id}/` prefix (or we use an
  absolute same-origin URL it already leaves untouched — simpler, no helper
  change).
- `leNormalizeImages` / `leBodyHtmlForDraft` round-trip it like any other image.

**At autosave/persist time (server-side, new):**
In `app/services/report_drafts.py:upsert_draft` (or a helper it calls), before
`sanitize_report_html`: find `<img src="data:image/…">`, validate (sniff +
size), write bytes to the uploads dir, rewrite `src` to the hosted same-origin
URL. Then sanitize (now tighten to drop residual `data:`). This mirrors
`pipeline/lesson_image_upload.extract_and_upload_data_uris` but writes to local
disk instead of S3.

**Serving (new route):**
`GET /run-uploads/{run_id}/{name}` (public, firewall-perimeter, mirroring
`lesson_content.py`'s posture) → resolve-inside-`{drafts_root}/_uploads/{run_id}`
→ `FileResponse`. Reuse the `resolve_content_path` traversal guard pattern.

**Routes/services that change:**
- `app/services/report_drafts.py` — add the extract-and-host step in the persist
  path; add a GC hook on reset/delete.
- new `app/routes/run_uploads.py` (or extend `lesson_content.py`) — serve route.
- `app/config.py` — `uploads_root` (default under `drafts_root`) + `max_upload_bytes`.
- `app/services/html_sanitizer.py` — keep allowing `data:image/` transiently;
  after re-host, persisted HTML should be hosted URLs only.
- `pipeline/report.py` — client-side size cap in `leImgApplyDataUri` /
  `leImgOnFileChosen`; (optional) preset-width chips; **resolves the
  `drafts.py:52-58` TODO** conceptually.
- **No change** to the read-only version-folder serving via `/lesson-content`.

---

## 7. Rough phasing + proposed child tickets (under KNOW-2344)

This is a multi-ticket package but **not** a new epic — it fits squarely under
KNOW-2344 (core tool / report & editor), alongside KNOW-2279/2314/2347.

1. **KNOW-2249a — Guard rails (size cap + content sniff).** Client-side reject
   > N MB; server-side body/size limit + magic-byte sniff in the draft persist
   path. *Independent, ship first.* Small.
2. **KNOW-2249b — Per-draft uploads store + serve route.** `uploads_root`,
   write on persist (extract `data:` → disk), `GET /run-uploads/...` with
   traversal guard, sanitizer tightening, GC on reset/delete. Medium.
3. **KNOW-2249c — Path-helper integration + report round-trip.** Teach
   `leImgRelTail`/`leNormalizeImages`/`leBodyHtmlForDraft` the uploads form;
   verify draft→reload→report render round-trips (KNOW-2279 + KNOW-2347
   regression checks). Small–medium.
4. **KNOW-2249d (optional) — Preset width chips.** Only if Sam wants sizing UX.
   Small.
5. **Deferred / linked:** undo-redo of image ops → **KNOW-2314** (do not bundle).
   Skilljar re-host of the final saved lesson → **KNOW-2247** (release pipeline,
   separate from editor). Save-to-Version full port → **KNOW-2278**.

Note: KNOW-2249 is currently a **Story**; the above can be Sub-tasks of it, or
2249 becomes the umbrella and a/b/c/d are Tasks parented to KNOW-2344. Sam's
call (see Q7).

---

## 8. Open questions for Sam

1. **Hosting now or later?** Do you want pasted/uploaded images turned into
   hosted URLs *in the editor/draft flow now* (Option A/B), or is keeping them
   inline base64 + adding guards (Option C) good enough until the Skilljar push
   (KNOW-2247) re-hosts everything anyway?
2. **Storage backend:** local per-draft uploads dir (Option A, recommended) vs
   S3/MinIO (Option B)? I.e., do you want the app process to hold AWS creds, or
   keep all user state on the box?
3. **Eager vs lazy re-host:** upload-on-paste (small drafts, more client code,
   orphan management) vs re-host-at-save (simplest, matches old `serve.py`)?
   I recommend lazy.
4. **Sizing UX:** status quo (strip dims, rely on `max-width:100%`), or add
   preset width chips (S/M/L/Full)? Drag-resize handles are off the table for a
   5-user tool unless you insist.
5. **Size cap value:** what's a sane per-image cap (e.g. 5 MB) and total
   per-draft cap? And should the cap PR (KNOW-2249a) land independently first?
6. **Re-scope the ticket:** OK to rewrite KNOW-2249's description to drop the
   stale `serve.py` / `/api/upload-image` / Skilljar framing and point it at the
   real gap (the `drafts.py:52-58` TODO + persistence)? The interactive capture
   it asked for is already done in KNOW-2279.
7. **Ticket shape:** split into Sub-tasks of KNOW-2249, or Tasks parented to
   KNOW-2344 with 2249 as the umbrella Story?
