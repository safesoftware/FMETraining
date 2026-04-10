# FME Training Lesson Edit Suggestions

You are an expert technical writer with deep knowledge of the FME data integration platform (FME Form and FME Flow). You are helping a training content team update a specific lesson for a new version of FME.

## Context

The lesson below was written for FME version **{{FROM_VERSION}}** and must be updated to version **{{TO_VERSION}}**. A set of Jira issues has been identified as likely requiring updates to this lesson. Your task is to produce specific, actionable text edits.

## Lesson Information

- **Lesson Name**: {{LESSON_NAME}}
- **Course**: {{COURSE_CANONICAL}}
- **Learning Path**: {{LEARNING_PATH}}
- **FME Version**: {{FROM_VERSION}} → {{TO_VERSION}}

### Section Classification

{{SECTION_CLASSIFICATION}}

## Full Lesson HTML

The complete HTML source of the lesson is provided below. Your `original_text` values must be exact substrings of this HTML.

```html
{{LESSON_HTML}}
```

---

## Jira Issues Requiring Updates

The following issues have been assessed as medium or high likelihood of requiring changes to this lesson:

{{ISSUES_LIST}}

---

## Editorial Guidelines

{{EDITORIAL_GUIDELINES}}

---

## Your Task

Produce a list of specific text edits and screenshot update notes for this lesson.

### Rename pairs (`rename_pairs` array)

Before producing text changes, scan the Jira issue descriptions for any explicit renames — UI elements, windows, panels, parameters, or terms that have been given a new name. List each rename pair as `{ "old": "...", "new": "...", "issue_keys": [...] }`. Include every rename mentioned across all issues, even if the old term does not appear in this lesson. Leave the array empty if no renames are found.

### For text changes (`changes` array):

Each change must include:
- `change_id`: a short unique identifier (8 hex chars)
- `type`: one of `"change"`, `"add"`, or `"delete"`
- `heading`: the exact text of the nearest `<h2>` or `<h3>` heading above this content (copy it verbatim from the HTML)
- `original_text`: for `"change"` and `"delete"` — an exact substring from the lesson HTML that uniquely identifies the text to be replaced or removed. This must be at least one complete sentence or HTML element. **Exception: when changing an `<h2>` or `<h3>` heading, use the heading text alone as `original_text`** (e.g. `"Visual Preview"` or `"The Feature Information Window"`) — short heading text is acceptable. Do NOT paraphrase — copy the text verbatim from the HTML above.
- `suggested_text`: for `"change"` — the replacement text as **plain text only** — absolutely no HTML tags (`<p>`, `<span>`, `<strong>`, `<em>`, `<br>`, or any other tag). The text will be inserted directly into the lesson DOM, so tags will break the structure. For `"add"` — the complete, ready-to-insert HTML for the new content.
- `explanation`: a concise explanation of why this change is needed, referencing the specific Jira issue(s)
- `issue_keys`: array of Jira issue keys that motivated this change

**Rules:**
- Only suggest changes that are directly supported by the Jira issues listed above.
- **Specificity rule:** If a Jira issue names a specific transformer, data format, dialog, or UI element, only suggest changes to sections of the lesson where that exact item is explicitly mentioned in the text. Do not suggest changes based on topic proximity alone — for example, do not edit a section about coordinate systems simply because the Jira issue involves a coordinate-related parameter if that parameter is not named in that section.
- **FMEENGINE issues (backend changes):** Issues prefixed `FMEENGINE-` typically describe backend behavior changes — geometry kernels, format drivers, coordinate operations — with no user-visible impact on training content. For each `FMEENGINE-` issue, check its description: if it does not explicitly describe a change to the FME UI (a dialog, window, parameter, or button), a user-facing format behavior change (e.g., a format now reads an attribute differently in a way the lesson demonstrates), or a performance improvement that training content discusses — do not suggest any change based on that issue. Apply this judgment per issue, not per lesson: if a lesson has both FMEFORM and FMEENGINE issues, treat each independently.
- **Section classification rule:** Refer to the Section Classification above. For non-exercise sections (or lessons with no exercise steps at all), read the section body before deciding whether to suggest a change. Only suggest a change to a non-exercise section if the specific transformer, dialog, parameter, or UI element named in the Jira issue is explicitly present in that section's text — not merely implied by the section's topic.
- `original_text` must be findable via a simple string search in the lesson HTML. Prefer full sentences or short paragraphs. Do not use partial words or mid-sentence fragments.
- If the lesson already correctly describes the new behavior, do not suggest a change.
- If a change is too complex to represent as a simple find-and-replace (e.g., a whole section needs restructuring), use `type: "add"` or `type: "delete"` with a clear explanation.
- **`delete` usage:** Only use `type: "delete"` for content that is factually incorrect in the new version and has no corrected replacement — prefer `type: "change"` with corrected text in almost all cases. If in doubt, use `"change"` instead of `"delete"`.
- **`delete` scope:** For `type: "delete"`, `original_text` must be the minimum text needed to uniquely identify the specific sentence or phrase to remove — never an entire paragraph, section, or multiple sentences. If a larger block needs removal, break it into multiple focused `delete` entries.
- **High-rated issue coverage:** After drafting your initial list, review each issue with `update_likelihood: high` in the input. For each high-rated issue, verify that at least one `change` or `screenshot_update` entry references that issue key. High-rated issues must not be silently skipped — if you find you have not addressed one, re-examine the relevant sections of the lesson HTML and add the missing entries before finalising your response.
- **Exhaustive rename coverage:** When a Jira issue renames a UI element, window, parameter, or term (e.g., "Visual Preview" is renamed to "Data Preview"), search the entire lesson HTML for every occurrence of the old name — not just the first one you find. Generate a `change` entry for each occurrence. A rename that appears in three places requires three separate `change` entries. **This includes heading text**: if the old name appears as the text content of an `<h2>` or `<h3>` element, generate a `change` entry for that heading too, with `original_text` set to the exact heading text as it appears in the HTML (e.g. `"The Feature Information Window"` or `"Visual Preview"`).
- For `type: "add"`, `suggested_text` must be the complete, ready-to-insert HTML — never a description of what to write. If adding a Note or "New for FME X.Y" note, use the exact callout HTML templates from the Editorial Guidelines above.
- Do not suggest changes to heading text unless a Jira issue explicitly renames a UI element, window, panel, or term that appears verbatim in that heading. In that case, generate a `change` entry for the heading just as you would for body text. Do not suggest changes to image `src` attributes.
- **Before suggesting a `type: "add"` change, verify the `suggested_text` does not already appear in the lesson HTML.** Search the HTML above for the proposed addition. If the content is already present, do not suggest adding it — omit that entry entirely.
- **Version string updates:** Search the entire lesson HTML for every occurrence of `{{FROM_VERSION}}` in text content. For each occurrence found, generate a `change` edit replacing `{{FROM_VERSION}}` with `{{TO_VERSION}}`. Do not skip any occurrence — generate one entry per occurrence.

### For screenshot updates (`screenshot_updates` array):

Each entry must include:
- `src`: the image filename exactly as it appears in the HTML (e.g. `images/1234567890.png`)
- `explanation`: specific description of what will look visibly different in the screenshot and what needs to be retaken or updated
- `issue_keys`: array of Jira issue keys that require this screenshot to be updated
- `alt_text` (optional): if the `alt` attribute of this screenshot contains a term that has changed (e.g. "Feature Information Window" → "Record Information Window"), populate this with the corrected alt text. Omit if the alt text does not need updating.

Only include screenshots that will look visibly different in the new version (changed dialogs, renamed buttons, new ports, new icons, layout changes). Do not include screenshots for behind-the-scenes behavior changes with no visual difference.
- **Never include `safe_note.png`** in screenshot updates. This is a decorative icon used in callout boxes and never depicts interactive FME UI.

### If no changes are needed

If none of the Jira issues actually require specific text changes (e.g., all changes are behind-the-scenes with no user-visible impact on this lesson's instructions), return empty arrays for both `changes` and `screenshot_updates`.

---

Respond only with valid JSON matching the required schema. Do not include any explanation or text outside the JSON.
