# Release-sprint API-shape contract (barrier C1 — FROZEN)

Frozen HTTP contract for the new router `app/routes/skilljar_release.py`. WS-D
builds its Release-tab UI against these shapes; WS-C must match them exactly.
The shapes are ported verbatim from the legacy launcher `serve.py` handlers
(lines 540-655) so the existing front-end JS contract carries over unchanged.

**Source of truth:** `serve.py` `_handle_release_status` / `_handle_release_plan`
/ `_handle_release_execute` / `_handle_link_draft_course` / `_api_run_log`, plus
the response dicts from `pipeline/skilljar_release.py`
(`build_release_plan`, `link_draft_course`).

## Conventions

- All endpoints are mounted on the FastAPI app via a dedicated router
  (`app/routes/skilljar_release.py`), a **disjoint sibling** of the existing
  sync router in `app/routes/skilljar.py` — no shared router object.
- Content-Type: `application/json` for all requests/responses.
- Errors use the FastAPI/Starlette convention `{"detail": "<message>"}` with the
  documented status code (this is the app-native shape; the legacy server used
  `{"error": ...}` — WS-D must read `detail`, NOT `error`).
- `to_version` must match `^\d{4}\.\d+$`; an invalid/missing value → **400**.
- Auth: these live under `/api/*`, which the `AuthMiddleware` gates with 401 for
  unauthenticated requests (KNOW-2259). Tests authenticate via the `authenticate`
  fixture.
- When `SKILLJAR_API_KEY` is unset, mutating endpoints return **503**
  (`{"detail": "SKILLJAR_API_KEY is not configured"}`) — matching the existing
  `app/routes/skilljar.py` precedent (lines 49-53).

---

## `GET /api/release-status`

Saved + mapped lesson dirs for a target version. (serve.py 540-553)

**Query params**

| name        | type   | required | notes                          |
|-------------|--------|----------|--------------------------------|
| `to_version`| string | yes      | e.g. `2026.1`; `\d{4}\.\d+`    |

**200 response**

```json
{
  "saved":  ["2026.1/fme-form-basic/Connect To Data 2026.1/Read and Display Data", "..."],
  "mapped": ["..."],
  "direct": ["..."]
}
```

- `saved`  — `string[]`, sorted. Lesson dirs with new/modified `index.html`
  (git-detected) under `to_version`.
- `mapped` — `string[]`, sorted. Subset of `saved` that has a Skilljar mapping
  entry.
- `direct` — `string[]`, sorted. Subset of `mapped` whose mapping key IS the
  to_version path itself (draft/linked courses, where the archive step is
  skipped).

**400** — invalid/missing `to_version`.

---

## `GET /api/release-plan`

Pre-flight plan for the selected lessons. (serve.py 557-568)

**Query params**

| name        | type     | required | notes                                                   |
|-------------|----------|----------|---------------------------------------------------------|
| `to_version`| string   | yes      | `\d{4}\.\d+`                                            |
| `lessons`   | string[] | no       | repeated query param; lesson-dir strings. Empty → empty plan. |

> Legacy accepted both `lessons[]` and `lessons`. The new router SHOULD accept
> repeated `lessons` query params (FastAPI `lessons: list[str] = Query(default=[])`).
> WS-D emits `?to_version=2026.1&lessons=<dir1>&lessons=<dir2>`.

**200 response** — the plan dict from `build_release_plan`:

```json
{
  "to_version": "2026.1",
  "courses": [
    {
      "action": "release",
      "source_course_id": "abc123",
      "source_course_title": "Connect To Data 2025.0",
      "archive_title": "Connect To Data 2025.0",
      "new_title": "Connect To Data 2026.1",
      "new_labels": ["2026.1"],
      "lp": "fme-form-basic",
      "course_canonical": "Connect To Data",
      "course_folder": "Connect To Data 2026.1",
      "is_draft": false,
      "lessons": [
        {
          "skilljar_lesson_id": "les_456",
          "skilljar_course_id": "abc123",
          "lesson_dir": "2026.1/fme-form-basic/Connect To Data 2026.1/Read and Display Data",
          "lesson_name": "Read and Display Data",
          "local_path": "/abs/path/.../index.html",
          "has_local_file": true,
          "mapped": true,
          "is_draft": false
        }
      ]
    }
  ],
  "warnings": ["No Skilljar mapping found for course: ..."]
}
```

Field types:

- `to_version`: string.
- `courses`: array of objects. Per course:
  - `action`: `"release" | "push_only" | "no_mapping"`.
  - `source_course_id`: string (`""` when `no_mapping`).
  - `source_course_title`: string.
  - `archive_title`: string (`""` when `no_mapping`).
  - `new_title`: string.
  - `new_labels`: `string[]` (e.g. `["2026.1"]`).
  - `lp`: string (learning-path folder).
  - `course_canonical`: string (title minus version suffix).
  - `course_folder`: string.
  - `is_draft`: boolean (true ⇔ `action == "push_only"`).
  - `lessons`: array of objects:
    - `skilljar_lesson_id`: string (`""` when not mapped).
    - `skilljar_course_id`: string (present only when `mapped`).
    - `lesson_dir`: string.
    - `lesson_name`: string.
    - `local_path`: string | null.
    - `has_local_file`: boolean.
    - `mapped`: boolean.
    - `is_draft`: boolean.
- `warnings`: `string[]`.

**400** — invalid/missing `to_version`.

---

## `POST /api/release-execute`

Spawn a background release; return the poll key. (serve.py 572-625)

**Request body**

```json
{ "to_version": "2026.1", "lessons": ["<dir>", "..."], "dry_run": false }
```

| field        | type     | required | default | notes                                   |
|--------------|----------|----------|---------|-----------------------------------------|
| `to_version` | string   | yes      | —       | `\d{4}\.\d+`                            |
| `lessons`    | string[] | no       | `[]`    | lesson-dir strings to release           |
| `dry_run`    | boolean  | no       | `false` | log intended actions; mutate nothing    |

**200 response**

```json
{ "action_key": "release:2026.1:1718000000000" }
```

- `action_key`: string, shaped `release:{to_version}:{epoch_ms}`. Poll it via
  `GET /api/release-log`.

**400** — invalid/missing `to_version`.
**503** — `SKILLJAR_API_KEY` not configured.

---

## `POST /api/link-draft-course`

Match a local draft course folder to an existing Skilljar course and write the
mapping. (serve.py 629-655)

**Request body**

```json
{ "course_prefix": "2026.1/fme-form-basic/Connect To Data 2026.1",
  "skilljar_course_id": "abc123" }
```

| field                | type   | required | notes                                              |
|----------------------|--------|----------|----------------------------------------------------|
| `course_prefix`      | string | yes      | `<to_version>/<lp>/<course_folder>`                |
| `skilljar_course_id` | string | yes      | Skilljar course whose lessons we match against     |

**200 response** — from `link_draft_course`:

```json
{
  "matched": [
    { "local_dir": "2026.1/fme-form-basic/Connect To Data 2026.1/Read and Display Data",
      "skilljar_lesson_id": "les_789",
      "title": "Read and Display Data" }
  ],
  "unmatched_local":    ["Some Folder Without A Match"],
  "unmatched_skilljar": ["A Skilljar Lesson Title With No Local Folder"]
}
```

- `matched`: array of `{ "local_dir": string, "skilljar_lesson_id": string, "title": string }`.
- `unmatched_local`: `string[]` (local folder names with no Skilljar match).
- `unmatched_skilljar`: `string[]` (Skilljar lesson titles with no local match).

**400** — missing `course_prefix`/`skilljar_course_id`, OR pipeline `RuntimeError`.
**503** — `SKILLJAR_API_KEY` not configured.

---

## `GET /api/release-log`

Poll the in-process buffer for a running/finished release. (serve.py 232-268 +
the release-thread buffering at 601-625)

**Query params**

| name         | type   | required | notes                                            |
|--------------|--------|----------|--------------------------------------------------|
| `action_key` | string | yes      | the key from `POST /api/release-execute`         |

> The legacy `_api_run_log` used the param name `run_id` and was an SSE stream.
> For the new router the param is **`action_key`** and the canonical shape is a
> JSON poll (below). An optional SSE variant may reuse the existing `sse` router
> pattern, but the JSON poll is the frozen contract WS-D codes against.

**200 response**

```json
{ "action_key": "release:2026.1:1718000000000",
  "status": "running",
  "log": ["=== Course: Connect To Data 2026.1 (id=abc123) ===", "Step 1/5: ...", "..."] }
```

- `action_key`: string (echoed back).
- `status`: `"running" | "done" | "error"`.
- `log`: `string[]` — all log lines buffered so far, in order. WS-D renders the
  full buffer or diffs against its last-seen length.

**404** — unknown `action_key` (`{"detail": "No log for key: <action_key>"}`).
