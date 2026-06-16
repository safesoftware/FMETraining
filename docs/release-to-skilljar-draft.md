# Publishing a lesson to a Skilljar draft (Releases tab)

Team runbook for taking an edited lesson from the web app into a **Skilljar draft**,
then publishing it manually. This is the **safe** path — it pushes content into a
**draft** and never renames or overwrites the live published course.

> **⚠ Status / where this works today (2026-06-16).** This runs from a **local repo
> checkout** with the app in publish mode. It does **not** yet work on the shared
> `fme-train` box — the box has no on-disk content corpus / git work tree
> (KNOW-2359), and the release flow's saved-lesson detection needs `git` present
> (KNOW-2362). Until those land, **publish from a local checkout.**
>
> **You need:** the repo checked out (it contains the version content corpus and is a
> git work tree); the app running locally (`make up`, then **http://localhost:8000**);
> and valid **Skilljar** (`SKILLJAR_API_KEY`, `SKILLJAR_DOMAIN`) + **AWS** credentials
> (for image re-hosting) configured for the app. The local publish setup is being
> streamlined under KNOW-2361/2362.
>
> The Releases-tab UX is intentionally bare right now (redesign tracked in KNOW-2323) —
> **follow these steps in order.**

---

## Overview

1. **Skilljar (manual):** archive the outgoing version, following our normal archive procedure.
2. **Skilljar (manual):** prepare the **draft** that will receive the new version, and copy its **Course ID**.
3. **App — report:** accept your edits and **Save to Version Folder**.
4. **App — `/release`:** **Link draft course** so the app pushes to *your* draft (not the live course).
5. **App — `/release`:** dry-run, then **Execute** the push to the draft.
6. **Skilljar (manual):** verify the draft, then **publish** it.

Throughout, the worked example is the course we tested:
*Design Modular and Maintainable Workspaces with Custom Transformers*, version **2025.1 → 2026.1**.

---

## Step 1 — Skilljar: archive the outgoing version (our normal archive procedure)

> **⚠ Confirm the bracketed bits against our actual archive convention** — the exact
> clone action, label names, and titles are our internal standard, not invented here.

1. In Skilljar admin, open the **currently-published** course for the outgoing version
   (e.g. *Design Modular… Custom Transformers* **2025.1**).
2. **Clone / duplicate** the course `[Skilljar action per our procedure]`. The clone is the
   archived backup of the outgoing version.
3. **Label the clone** per our archive convention — e.g. add the **`archived`** label
   `[+ the outgoing version label, e.g. "2025.1"]`, and remove any "current/live" label so
   it doesn't surface as the live version.
4. **Title** the clone clearly, e.g. `[<Course> <old version> — archived]`.

This preserves the old version. The app's automated archive step is **skipped** on the
draft path (Step 5), which is why we archive manually here.

## Step 2 — Skilljar: prepare the draft + get its Course ID

1. Create / open the **draft** that will hold the **new** version's content
   `[per our procedure — e.g. a new draft on the course, or the new-version course]`.
2. Make sure the draft's **lesson titles match** the lesson folder names you'll save
   locally. The app matches them ignoring punctuation/case, so
   `Exercise: Turn a Reusable Workflow…` (Skilljar title) matches
   `Exercise_ Turn a Reusable Workflow…` (local folder) — but the **words must match**.
3. Copy the draft's **Course ID** (the Skilljar course identifier, e.g. `10pjvfnwodw7i`).
   You'll paste it into the app in Step 4.

## Step 3 — App: edit the lesson and Save to Version

1. Open the run's **report** → **Lesson Edits** tab → accept/reject suggestions and make
   any WYSIWYG edits.
   - If the **Save to Version Folder** button is greyed out, the report is an older
     artifact — **Regenerate Report** from Recent Runs first (free), then reopen it.
2. Click **Save to Version Folder**. On success you'll see
   **"✓ Saved to: `<new version>/<lp>/<course> <new version>/<lesson>/index.html`"**.
   This writes the cleaned lesson HTML to the version folder and re-hosts its images to S3
   (so the published lesson has permanent image URLs).

## Step 4 — App `/release`: link the draft

Open **http://localhost:8000/release**.

1. **Target version** → type the new version (e.g. `2026.1`) → **Check status**.
   You should see your lesson counted under **Saved** / **Mapped**.
2. Scroll to **Link draft course** and enter:
   - **Course prefix:** `<version>/<lp>/<course folder>` — e.g.
     `2026.1/fme-form-advanced/Design Modular and Maintainable Workspaces with Custom Transformers 2026.1`
   - **Skilljar course id:** the draft ID from Step 2 (e.g. `10pjvfnwodw7i`)
   - Click **Link draft course**.
3. Confirm the result shows **`Matched: 1`** (or however many lessons you saved), mapping
   your local lesson(s) to the draft's lesson IDs. Lessons with no local folder appear under
   *Unmatched Skilljar* — that's fine.
4. **Check status** again → it should now show your lesson under **Direct** (this is what
   tells the app to push to the **draft**, not the live course).

## Step 5 — App `/release`: dry-run, then push to the draft

1. **Preview plan** → select your lesson(s) → confirm the course shows **`push_only`**
   (and `draft`). `push_only` = **content-only push into the draft; no archive, no rename**.
2. **Execute release** with **Dry run ON** first. The log should show:
   - `Step 1/4: Skipping archive (target is an existing draft/linked course).`
   - `Step 2/4: Pushing new <version> content… Would PATCH N lesson(s).`
   - `Step 3/4: Skipping rename (draft already has correct title/labels).`
   - `Step 4/4: Updating skilljar-mapping.json…`
   Dry-run changes nothing.
3. If the plan looks right, **uncheck Dry run** and **Execute** again. The log is the same
   minus the `[DRY RUN]` prefixes — Step 2 actually **PATCHes** the lesson(s) into the draft,
   Step 4 records the mapping.

## Step 6 — Skilljar: verify and publish the draft

1. In Skilljar, open the **draft** course → the lesson(s) you pushed → confirm the new
   content is present and **images render** (they load from our S3 bucket).
2. The **live published** version is still unchanged at this point.
3. When you're happy, **publish the draft manually** in Skilljar. The app intentionally does
   **not** auto-publish.

---

## Troubleshooting

- **`Matched: 0` when linking** → the lesson titles don't match. Compare the Skilljar lesson
  title to your local folder name (ignoring punctuation/case). Fix the title or folder so the
  words line up, then re-link.
- **`Check status` shows nothing** → the lesson wasn't saved to the version folder (Step 3),
  or the content tree isn't a git work tree / `git` isn't available (KNOW-2362). Re-save and
  confirm the file exists under the new-version folder.
- **Save fails on images** → the app's AWS credentials aren't set for image re-hosting
  (KNOW-2361). Confirm `AWS_*` creds are configured.
- **Status shows the lesson under `Mapped`/`Direct: 0` and the plan says `release` (not
  `push_only`)** → you haven't linked a draft yet (Step 4), so the app would target the **live
  course** (archive + **rename**). **Do not execute that** unless you intend a full live
  release — link the draft first.

## Important notes

- **`push_only` (draft) vs `release` (live).** This runbook is the **draft** path. The other
  path, `release`, archives + pushes + **renames the live course** — only use it for a real
  live cutover, and only knowingly. (Making the draft path the clear default and guarding the
  live path is tracked in KNOW-2323.)
- **One lesson or many.** You can save several lessons under the same course before linking;
  `Matched`/the plan will cover all of them.
- **Publishing is always manual** in Skilljar (by design, for now).
