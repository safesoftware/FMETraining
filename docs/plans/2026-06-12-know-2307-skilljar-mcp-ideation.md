# KNOW-2307 — Rework app to use Skilljar MCP — ideation

**Status: DRAFT ideation — for Sam's review, not yet approved**
Date: 2026-06-12 · Author: design/ideation pass (agent) · Epic: KNOW-2345 (Skilljar publishing & release lifecycle)

> This is a *design & ideation* document, not a plan of record and not an implementation.
> No code was written, no tickets were filed, nothing was committed. It exists so Sam can
> make the architecture decisions in §8 before any work is scheduled.

---

## 1. Problem & goal

**The ticket (KNOW-2307, Type: Task, parent KNOW-2345)** says only: *"Rework app to use Skilljar MCP"*, with one link in the description:
`https://support.gainsight.com/Skilljar/Integrate/MCP_Integration/Connect_Skilljar_to_Claude_Code`.

That link is the whole spec, and it's load-bearing — it tells us **"Skilljar MCP" is a real, first-party product**, not a metaphor. Gainsight/Skilljar ship a **hosted, remote MCP server at `https://mcp.skilljar.com/mcp`** (currently **beta**), powered by the **new Skilljar API v2**, authenticated with an **API v2 client ID + secret passed as HTTP headers**, connected via the Claude Code CLI (or any MCP client that supports custom headers). So the menu of interpretations collapses:

- **(a) Consume Skilljar's hosted first-party MCP server** — exists today, this is what the ticket links to. ✅ the real option.
- **(b) Build an in-house MCP server wrapping Skilljar's REST API** — possible but redundant now that (a) exists; only justified if we needed tools (a) doesn't expose (and as §2/§4 show, the tools we'd most want — publish/archive/version-tag — *aren't* exposed by anyone, including our own REST code's "Step 4").
- **(c) Agentic / LLM-driven Skilljar ops** — i.e. an LLM in the loop *calling* the MCP. This is the **only context in which an MCP actually does anything**: MCP is a protocol for **LLM agents** to discover and call tools. A FastAPI web app calling a deterministic endpoint does **not** benefit from MCP framing — it would just be HTTP-with-extra-handshake.

**The clarification that matters most:** *MCP is an agent-tool protocol.* The FME Training app's Skilljar interactions today are **deterministic, non-LLM** server actions (PATCH this lesson's HTML; list courses; create a course). Wrapping deterministic server-to-server calls in MCP adds a JSON-RPC/tool-discovery layer and an LLM (or an MCP client runtime) for **zero functional gain** over calling Skilljar's REST/v2 API directly. **MCP earns its keep only where a human is driving an LLM agent in natural language** — which is Claude Code itself, not the FastAPI app's request handlers.

**Designing-around decision:** I am designing primarily around interpretation **(a) + a narrow slice of (c)** — *adopt Skilljar API v2 as the integration substrate, and use the hosted Skilljar MCP as an **operator tool in Claude Code** for ad-hoc/manual Skilljar work — while the app's automated pushes call the v2 REST API directly (no MCP runtime embedded in the request path).* The honest finding (argued in §4) is that **the high-value work in this epic is the KNOW-2323 flow rework, not the MCP adoption per se.** The MCP is a nice operator convenience and a forcing function to migrate off the bespoke v1 client; it is not, by itself, a fix for the release-flow bugs.

---

## 2. Current state (grounded)

There are **two parallel Skilljar integrations** in the repo. This is the single most important fact for scoping KNOW-2307.

### 2a. Legacy path — the one that actually publishes (and has the bugs)

Used by the **old single-user launcher** (`serve.py`, stdlib `http.server`). This is where the Releases page and all write operations live.

- **Routes** (`serve.py`): `/api/skilljar-push-info`, `/api/skilljar-push`, `/api/release-status`, `/api/release-plan`, `POST /api/release-execute`, `POST /api/link-draft-course`. The release runs on a background thread (`_handle_release_execute`, `serve.py:572-625`); the "paste-a-URL-to-link-a-draft" step is `_handle_link_draft_course` (`serve.py:629-655`).
- **HTTP client** (`pipeline/skilljar_push.py`): hand-rolled `urllib` against **API v1** (`SKILLJAR_API_BASE = "https://api.skilljar.com/v1"`, `skilljar_push.py:27`), HTTP Basic auth `api_key:` (`_basic_auth_header`, `skilljar_push.py:35-37`). Also does S3 image hosting with hand-written AWS SigV4 (`_s3_sign`/`_s3_put`, `skilljar_push.py:141-223`) because Skilljar `/v1/assets` only returns 1-hour-signed URLs.
- **Release orchestration** (`pipeline/skilljar_release.py`): `build_release_plan()` (`:269-389`) groups saved lessons by course and decides `release` vs `push_only` vs `no_mapping`; `execute_release()` (`:497-735`) is the 5-step generator: **1 Archive → 2 Push HTML → 3 Rename+labels → 4 Published-course tag swap → 5 Update `data/skilljar-mapping.json`**.
- **State**: a flat **307 KB `data/skilljar-mapping.json`** (lesson_dir → `{skilljar_lesson_id, skilljar_course_id, _title, _course_title}`), read-modify-written in place — concurrency-hazardous (the web-app plan flags this, `2026-04-29-multi-user-web-app.md:26`).

### 2b. New web-app path — read-only, no publish yet

Used by the **new FastAPI app** (`app/`, the one being deployed to EC2).

- **Async client** (`app/services/skilljar_client.py`): `httpx`, **API v1**, Basic auth, paginating generators for `list_courses` / `list_lessons` / `list_published_paths` **only** (`:126-137`). No write methods at all.
- **Sync** (`app/services/skilljar_sync.py`) + route (`app/routes/skilljar.py`): `POST /api/skilljar-inventory/sync` upserts the three list endpoints into Postgres (`SkilljarCourse/Lesson/PublishedPath`, `app/models/skilljar.py`), throttled 1/min. Extracts a `version:<x>` course tag into `version_label`.
- **Schema is already designed for the redesign** (`app/models/skilljar.py`): `lesson_drafts` (S3-backed, status `draft|promoted|archived`), `release_locks` (advisory locks keyed `lesson:<id>` / `draft:<id>`), `release_history` (append-only audit with `before_hash`/`after_hash` for conflict detection). **None of the write/release/lock logic is wired up yet** — the models and the read-only sync exist; the Releases UI does **not** exist in `app/templates/` (only `index.html` launcher, `drafts.html`). So in the new app, *publishing has not been ported at all.*

### 2c. Where bugs 2321 / 2322 come from (both in `execute_release`)

- **KNOW-2321 (duplicate archives + wrong tags).** The archive step (`skilljar_release.py:545-577`) calls `_create_course(archive_title, …)` **with no idempotency check**, so re-running creates a *second* archive course. And archive labels are `list({*existing_labels, "archived"})` (`:553`) — it keeps **all** the live course's labels (including the version label) and just adds `archived`, so the archive ends up tagged with the wrong/live version. **Status: open, unfixed.**
- **KNOW-2322 (Step 4 `KeyError 'id'`).** The published-course tag swap read `pt["id"]` on a tag-**association** record shaped `{"tag": {"id","name","slug"}}` (no top-level `id`), crashing mid-release after Steps 1-3 had already mutated. **Status: code-fixed** on `migrate/ec2-prod-prep` (commit `4bd8a3ed`): extracted `_swap_published_course_tags()` (`skilljar_release.py:453-486`), deletes by `tag_obj["id"]`, broadened the Step-4 `except` to `(RuntimeError, KeyError)`. **But the *operational recovery* of the half-applied "Leverage Ordered Data 2025.1→2026.1" release is still open**, and 2323 argues Step 4 *shouldn't run at all*.

### 2d. How KNOW-2323's rework idea relates

KNOW-2323 ("[Idea] Rework the Skilljar archive + publishing flow incl. draft-linking UX", Story, In Backlog) is the **real design ticket** for this whole area. Its domain model (must be preserved):

- A Skilljar course has a **live published version + an editable draft**. New content is pushed into the **draft**; the live course keeps serving old content until someone **publishes the draft** — **manually, in the Skilljar dashboard** (confirmed: the REST API has **no publish-draft endpoint**; the v2 MCP exposes **no** publish/draft/archive tool either — see §4).
- **Archiving = clone the existing course** as a backup; **tags don't need to change** for it.
- **The tool must NOT manage published-course tags.** ⇒ The current **Step 4 is the wrong operation** and should be **removed**, not just de-crashed. (KNOW-2322 only band-aids the crash.)
- The **"paste-a-URL-to-link-a-draft"** UX (`link_draft_course`, `skilljar_release.py:742-816`; `serve.py:629`) is the specific unintuitive thing to redesign.

---

## 3. Key decisions / constraints (honored)

From project memory (`project_skilljar_publish_lifecycle`) and KNOW-2323 — **honored as hard constraints** unless flagged as an open question:

| Decision | Status in this design |
|---|---|
| Draft / publish / archive lifecycle model | **Kept.** All options below preserve it. |
| **Tool must NOT manage version tags** | **Kept.** Every option **deletes** the current Step-4 published-course tag swap (`_swap_published_course_tags` + the `_get_tags`/`_create_tag`/`_add`/`_delete_published_course_tag` helpers). This supersedes KNOW-2322 rather than shipping it. |
| **Publishing is manual** (dashboard) for now | **Kept.** The app pushes into the draft and *stops*; a human publishes. Auto-publish is explicitly an open question (§8), not built. |
| Archiving = clone, tags unchanged | **Kept**, plus the missing **idempotency guard** (fixes KNOW-2321's duplicate). |
| 5-user internal tool, not SaaS | **Kept.** Drives the "don't build our own MCP server" call and the proportionate phasing. |

**What changes vs. stays:**
- **Stays:** the S3 image-hosting via SigV4 (`_s3_put`) — Skilljar still only mints 1-hour asset URLs, MCP or not; the draft-as-target push model; the `LessonContentSource` abstraction; the already-designed `lesson_drafts`/`release_locks`/`release_history` tables.
- **Changes:** Step 4 (tag swap) is **deleted**. The archive step gets an **idempotency guard** + a deliberate label set. The bespoke **v1** clients (`pipeline/skilljar_push.py` urllib + `app/services/skilljar_client.py` httpx) get **consolidated onto one v2-capable client**. The "paste-a-URL" linking UX is **replaced** (see §4 sketch).

---

## 4. Architecture options

First, the **decisive capability check** (this gates everything):

> **The Skilljar MCP / API v2 exposes: list/search courses, get course, create course, update course, list/search lessons, get lesson, create HTML lesson, update lesson** (plus student/enrollment/group management we don't need). It does **NOT** expose publish-draft, archive-course, or version-tag operations. Those remain **dashboard-only** (Skilljar Help Center "Course Drafts" / "Archive Courses"). The v1 REST API likewise has no publish-draft endpoint.

So the operations the app automates split cleanly:

- **Content push (PATCH/create lesson HTML, create course)** → *covered* by MCP/v2 **and** by direct v2 REST. This is the deterministic happy path.
- **Publish / archive / version-tag** → *not covered by any API*. Publish stays manual; archive is a clone (doable via create-course + create-lessons, which v2 has); tags we've decided not to touch.

**Conclusion up front:** because the buggy part (publish/archive/tag) is *not* an MCP capability, **"adopt the MCP" cannot by itself fix 2321/2322/2323.** The bug fixes are flow-logic changes regardless of transport. The MCP question is really *"which transport/auth do we standardize on, and do we expose Skilljar to operators via Claude Code?"*

### Option A — Refactored direct-API v2 service (NO embedded MCP in the app) + adopt the hosted MCP as an operator tool

- One `SkilljarService` in `app/services/`, talking **API v2** over `httpx` (v2 client-id/secret headers), replacing both `pipeline/skilljar_push.py` and the read-only `app/services/skilljar_client.py`. Async list/get + write (create/update course, create/update lesson HTML).
- The app's automated pushes call this service **directly** — no MCP runtime, no LLM in the request path.
- **Separately**, register the **hosted Skilljar MCP** (`mcp.skilljar.com/mcp`) in the team's Claude Code config so Sam can do ad-hoc Skilljar ops ("find the 2025.1 draft for Connect To Data", "create an HTML lesson") in natural language. This is the literal thing the ticket's linked doc describes.
- Release flow (`skilljar_release.py` logic, ported into a service): **Step 4 deleted**; archive gets idempotency guard + deliberate labels (fixes 2321); push targets the draft and stops (publish manual).
- **Tradeoffs:** + Simplest, most honest, proportionate to 5 users. + Migrates to v2 (futureproof; v1 is the old API). + Gets operators the MCP convenience for free. − "Use the MCP" is only *partially* satisfied in the literal sense (the app doesn't *call* the MCP) — needs Sam's buy-in that this is the right reading.

### Option B — App drives the hosted Skilljar MCP programmatically (MCP client embedded in FastAPI)

- The FastAPI app embeds an MCP client (e.g. via the Agent SDK / an MCP client lib) and performs Skilljar writes **through `mcp.skilljar.com/mcp`** tool calls instead of REST.
- **Tradeoffs:** − Adds an MCP client runtime + tool-call marshalling to a server that just needs deterministic HTTP — **complexity with no functional payoff** (§1). − Beta server: HTTP-header-auth only, surface still expanding, no SLA implied. − Still doesn't cover publish/archive/tag (so you keep REST/dashboard for those anyway → *two* Skilljar transports). − Pulls an LLM-agent dependency into a deterministic pipeline. − Only makes sense if you also want the app to *reason* over Skilljar in NL, which it doesn't. **Not recommended** for the automated path.

### Option C — Build our own in-house MCP server wrapping Skilljar

- A small MCP server (FastMCP) exposing our *domain* operations (push-lesson-draft, plan-release, archive-clone) so Claude Code / agents can drive *our* workflow, not raw Skilljar.
- **Tradeoffs:** + Could encode our guardrails (idempotent archive, no tag-touch, draft-only push) as agent tools. − Redundant with the hosted Skilljar MCP for raw ops; − a server to build, host, secure, and maintain for ~5 users; − only valuable if we expect heavy *agent-driven* release work, which isn't the current workflow. **Over-engineered for now** — revisit only if agent-driven releases become a real workflow (note as a future epic, not v1).

### Releases-page UX sketch (applies to whichever option; this is the KNOW-2323 win)

Replace the "paste-a-URL-to-link-a-draft" step. The redesigned Release tab (in the **new** FastAPI app, since it isn't ported yet) for a target version:

```
Release  →  [ Target version: 2026.1 ▼ ]              [ Sync Skilljar ↻ ]

Course: Connect To Data                         live: 2025.0 ·  draft: ● linked
  ├ ☑ Connect a Database          draft target ▼  ▸ pick from this course's Skilljar drafts
  │     · (no paste-a-URL — dropdown of the course's existing drafts/lessons,
  │        populated from synced inventory; "＋ new lesson" if net-new)
  ├ ☑ Run a Workspace             draft target ▼
  └ ☐ (unchanged lessons hidden)
  Archive on release:  ◉ Clone current live course as backup (idempotent — skips if exists)
  Publish:             ⚠ manual — after push, publish the draft in Skilljar ↗ (deep link)
  [ Preview plan ]   [ Push to draft ]            ← no tag management, no auto-publish
```

Key UX moves: (1) **draft selection is a dropdown sourced from synced inventory**, not a pasted URL; (2) **explicit "publish is manual" affordance** with a deep link to the Skilljar dashboard; (3) **archive is a labelled, idempotent toggle**; (4) **no tag UI at all** (honors "don't manage tags").

---

## 5. Recommended approach

**Option A**, with the framing made explicit to Sam:

1. **Treat KNOW-2307 as "migrate the Skilljar integration to API v2 + adopt the hosted MCP as an operator tool in Claude Code,"** *not* "make the FastAPI app call an MCP at runtime." For a deterministic 5-user internal tool, embedding an MCP client in request handlers is complexity with no payoff (§1, §4-B). The MCP's genuine value here is **operator ergonomics in Claude Code** and a **forcing function to consolidate onto v2**.
2. **Do the KNOW-2323 flow rework as the substance of the work** — it's where the user-visible value and the bug fixes live: delete Step 4 (supersedes KNOW-2322's band-aid), add the archive idempotency guard + deliberate labels (fixes KNOW-2321), replace the paste-a-URL linking UX, and finally **port the Releases flow into the new FastAPI app** (it's currently only in legacy `serve.py`).
3. **Consolidate the two clients into one v2 `SkilljarService`** backed by the existing `lesson_drafts`/`release_locks`/`release_history` tables (locks + remote-hash conflict guard the web-app plan already designed).

This is proportionate: one service, one transport, a real UX fix, three bugs retired, and the operator gets the MCP in Claude Code without the app taking an LLM dependency.

---

## 6. Integration model — what's affected & how it supersedes 2321/2322/2323

**New / changed:**
- `app/services/skilljar_service.py` (**new**, v2) — absorbs `pipeline/skilljar_push.py` write logic + `app/services/skilljar_client.py` read logic. Add v2 client-id/secret auth (new settings `SKILLJAR_API_V2_CLIENT_ID`/`_SECRET`; keep `SKILLJAR_API_KEY` only if any v1-only endpoint remains).
- `app/routes/skilljar.py` — add release/push/plan/link endpoints (port from `serve.py:480-655`), gated behind the app's Google OIDC auth (the route already TODOs this).
- `app/templates/` — **new** Releases page (§4 sketch). Wire `release_locks` + `release_history` + `before_hash`/`after_hash` conflict guard.
- Release-flow logic ported to a service module: **delete `_swap_published_course_tags` and Step 4 entirely** (supersedes **KNOW-2322** — close it noting Step 4 is removed, recovery handled separately); **add archive idempotency + deliberate labels** (resolves **KNOW-2321**); **replace paste-a-URL linking** with inventory-dropdown selection (resolves the **KNOW-2323** UX ask).
- Migrate `data/skilljar-mapping.json` reliance → the `skilljar_*` + `lesson_drafts` tables (the mapping file is the legacy `serve.py` store; the new app already has the schema).

**Retired:** legacy `serve.py` Skilljar handlers + `pipeline/skilljar_release.py` Step-4 path + `pipeline/skilljar_push.py` v1 client, once the FastAPI Releases page reaches parity (consistent with the web-app plan's "web-only cutover, retire the local launcher").

**Operational leftover to carry forward (not code):** the half-applied **"Leverage Ordered Data 2025.1→2026.1"** release from KNOW-2322 still needs manual finishing (mapping/tag state) — track it on 2322 or a small recovery ticket; the Step-4 deletion doesn't auto-heal it.

---

## 7. Rough phasing + proposed child tickets

**Should KNOW-2307 stay its own thing or fold into KNOW-2323?**
Recommendation: **keep KNOW-2307 as the "v2 client + MCP operator adoption" task, and make KNOW-2323 the flow-rework story** — they're separable (transport migration vs. flow/UX redesign) and both already sit under epic KNOW-2345. Don't fold; **sequence** them (2307 unblocks/feeds 2323). Re-scope 2307's title/description so it's not misread as "embed an MCP in the app at runtime."

Proposed children under **KNOW-2345** (file when approved — not filed yet):
- **Phase 1 — KNOW-2307 (re-scoped):** consolidate to one **API v2 `SkilljarService`**; register the hosted Skilljar MCP in Claude Code for operators; document v2 client-id/secret in `.env.example` + `/etc/fme-train/env`.
- **Phase 2 — (under KNOW-2323) Delete Step-4 tag management** + close/ supersede KNOW-2322; small recovery ticket for the half-applied release.
- **Phase 2 — (under KNOW-2323) Idempotent archive + deliberate labels** — resolves **KNOW-2321** (with the test coverage 2321 asks for: re-run creates no duplicate, labels asserted).
- **Phase 3 — Port Releases page into FastAPI app** with the inventory-dropdown linking UX (resolves KNOW-2323 UX), locks + remote-hash conflict guard, draft-only push, manual-publish affordance.
- **Phase 3 (optional) — retire legacy `serve.py` Skilljar path** after parity.
- **Backlog/idea — auto-publish & in-house MCP server** — only if agent-driven releases become a real workflow (would warrant its own epic; see §8 Q2/Q5).

---

## 8. Open questions for Sam (numbered decision points)

1. **MCP interpretation.** Do you agree "Skilljar MCP" here means **(a) adopt API v2 + use the hosted MCP as an operator tool in Claude Code**, and that the FastAPI app should **call v2 REST directly** rather than embed an MCP client at runtime? If you actually want the app to drive the MCP programmatically (Option B), that's a different — and, I'd argue, worse — build.
2. **Auto-publish.** Memory says publish is manual for now. Keep it manual (app pushes to draft + deep-links the dashboard), or is automating publish in-scope for this epic? (Note: no REST/MCP publish endpoint exists today, so auto-publish may not even be possible without dashboard automation.)
3. **Step 4 deletion.** Confirm we **delete** the published-course tag swap entirely (per KNOW-2323) and **close KNOW-2322** as superseded, rather than ship its crash band-aid. OK?
4. **v1 → v2 migration scope.** Migrate **both** the read path (`app/services/skilljar_client.py`) and the write path (`pipeline/skilljar_push.py`) onto v2 in one consolidated service — or leave the read sync on v1 until v2 list endpoints are confirmed at parity? (Beta API risk.)
5. **In-house MCP server (Option C).** Park it as a future idea, or is exposing *our* release workflow as agent tools something you want explored sooner?
6. **2307 vs 2323 relationship.** Keep them as separate sequenced tickets under KNOW-2345 (my rec), or fold 2307 into 2323?
7. **Half-applied release recovery.** Who/when finishes the "Leverage Ordered Data 2025.1→2026.1" cleanup, and should it be its own small ticket?

---

### Sources (MCP capability research)
- Skilljar MCP setup / capabilities / hosted endpoint / API v2 auth: https://support.gainsight.com/Skilljar/Integrate/MCP_Integration/Connect_Skiljar_to_Claude_Code
- Gainsight beta announcement (Skilljar/CC/PX MCP servers): https://communities.gainsight.com/product-updates/gainsight-digital-customer-hub-skilljar-cc-and-px-mcp-servers-now-in-beta-30976
- Skilljar Help Center — Course Drafts (publishing is dashboard-driven): https://support.skilljar.com/hc/en-us/articles/38190184381069-Course-Drafts
- Skilljar Help Center — Archive Courses: https://support.skilljar.com/hc/en-us/articles/360002462933-Archive-Courses
- Local: `docs/skilljar-api-04-20-2026.yaml` (v1 REST spec — no publish-draft endpoint).
