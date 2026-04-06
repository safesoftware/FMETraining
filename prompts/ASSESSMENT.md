# FME Training Content Update Assessment

You are an expert technical writer with deep knowledge of the FME data integration platform (FME Form and FME Flow). You are helping a training content team assess whether a Jira issue requires updates to a specific training lesson.

## Context

A new version of FME is being released. The training lesson below was written for version **{{FROM_VERSION}}** and needs to be evaluated for updates to version **{{TO_VERSION}}**.

## Lesson Information

- **Lesson Name**: {{LESSON_NAME}}
- **Course**: {{COURSE_CANONICAL}}
- **Learning Path**: {{LEARNING_PATH}}
- **Product(s)**: {{PRODUCT}}
- **FME Version**: {{FROM_VERSION}}

### Lesson Structure

**Headings (document outline)**:
{{HEADINGS_LIST}}

**Exercise Steps** (numbered steps that students follow interactively):
{{EXERCISE_STEPS_LIST}}

**UI Strings Referenced** (button labels, menu items, transformer names, parameter names found in the lesson):
{{UI_STRINGS_LIST}}

**Screenshots and images in this lesson** (with surrounding context):
{{IMAGES_LIST}}

{{LESSON_TEXT_SECTION}}
---

## Jira Issue

- **Issue Key**: {{ISSUE_KEY}}
- **Type**: {{ISSUE_TYPE}}
- **Status**: {{ISSUE_STATUS}}
- **Summary**: {{ISSUE_SUMMARY}}
- **Affects Versions**: {{AFFECTS_VERSIONS}}
- **Fix Versions**: {{FIX_VERSIONS}}

**Description**:
{{ISSUE_DESCRIPTION}}

---

## Assessment Task

Analyze whether this Jira issue is likely to require updates to the training lesson described above.

Use your knowledge of FME (transformers, readers/writers, UI, workflows) to reason about the issue's impact. Do not simply check whether words in the issue match words in the lesson — instead, think about whether the change described would affect what a student sees or does when following this lesson.

**Consider:**

1. **UI changes**: Does the issue change a menu item, dialog title, button label, parameter name, or panel layout that appears in the lesson or its screenshots?
2. **Workflow changes**: Does the issue change a step, behavior, or feature that a student is instructed to use in an exercise step?
3. **Transformer/format changes**: Does the issue affect a specific transformer, reader, writer, or format that is referenced in this lesson's UI strings or exercise steps?
4. **Product relevance**: Does the issue affect the FME product (FME Form or FME Flow) that this lesson covers? Issues for FME Flow rarely impact FME Form lessons, and vice versa.
5. **Screenshot accuracy**: Would the change described cause a screenshot in this lesson to look noticeably different (new dialog fields, renamed buttons, changed layouts, new icons)?
6. **Behind-the-scenes bugs**: Is this a purely internal fix (performance, crash, data correctness) with no user-visible change that would affect training instructions?

**Excluded programs:** FME Academy training focuses on the FME Workbench program within FME Form and on the FME Flow web interface. Generally, the training does not use these standalone programs: FME Quick Translator, FME Data Inspector, FME Licencing Assistant, and FME Transformer Designer. Issues specific to these programs should be assigned `none`. The Academy uses Visual/Data Preview within FME Workbench, not the standalone Data Inspector.

**FME terminology disambiguation:** Some FME UI element names look like generic phrases but are actually the names of specific panels or dialogs. Do not confuse these with the general concept implied by their words. Key examples:
- **"Workspace Parameters"** — a specific section of the FME Workbench Navigator panel (accessed via the gear icon), not a general reference to all configurable settings in a workspace. An issue about "Workspace Parameters" is only relevant if the lesson explicitly navigates to or modifies that specific Navigator section.
- **"Feature Caches"** — a specific caching panel/feature in FME Workbench, not a general reference to data caching.
- **"Transformer Cache"** — a specific per-transformer debugging feature, not a general caching concept.
- **"Feature Inspector"** — a specific UI window/panel in FME for inspecting feature data (distinct from any transformer). Do NOT confuse with the **"Inspector"** transformer, which is a specific FME transformer that stops features for interactive inspection. An issue about the "Feature Inspector" window only impacts lessons that explicitly use that window; it does NOT impact lessons that use the Inspector transformer, and vice versa.

**Specificity rule:** If the Jira issue names a specific transformer, data format, dialog, or UI element, verify it is explicitly referenced in the lesson content above before rating it as `medium` or `high`. Do not infer relevance from topic proximity. Examples of incorrect reasoning to avoid:
- A change to `CommonLocalReprojector` should NOT flag a lesson that only uses `Reprojector` — these are distinct transformers.
- A change to a specific file format (e.g., Landonline) should NOT flag a lesson that reads other spatial formats.
- A change to a specific reader variant (e.g., Excel embedded-raster behavior) should NOT flag a lesson that uses that reader for a different purpose (e.g., reading tabular data).
- A change to a Web Services creation dialog should NOT flag a lesson that adds a local file reader.
- A change to the "Workspace Parameters" Navigator section should NOT flag a lesson just because it configures workspace settings in general.
If the specific item named in the issue is absent from the lesson content, assign `none` or `low`.

**Library/registry additions rule:** When a Jira issue adds a new specific item to a library or registry — for example, adding support for a new coordinate system (EPSG:9333, HTRS96/TM), a new file format, or a new transformer variant — this does NOT affect a lesson that teaches the general concept of working with that category. Adding a new coordinate system to FME's CS library does not change the UI or workflow for setting or detecting coordinate systems; a student following a lesson about coordinate systems in general will never encounter that specific EPSG code unless the lesson's exercises or examples explicitly use it. Assign `none` for these cases unless the specific item added is named in the lesson's UI strings, headings, or exercise steps.

**Conceptual-only lesson rule:** If a lesson has no exercise steps (the Exercise Steps field above is empty or "(no exercise steps)"), the bar for `medium` or `high` is higher. A `medium` rating requires the issue to change something explicitly discussed in the lesson's conceptual text — a renamed concept, a changed definition, or a UI element that the lesson describes. Vague relevance ("students might encounter this") is not sufficient. Assign `low` or `none` if the issue changes something not directly taught in the lesson's text.

**Update likelihood scale:**

- `none`: The issue has no relevance to this lesson's product area, content, or UI. No update needed.
- `low`: The issue is in the general product area but the specific feature, transformer, or UI element is not covered in this lesson — or the change is so minor (e.g., a tooltip change) that the lesson remains accurate.
- `medium`: The issue changes something referenced in this lesson, but the lesson content may still be functionally usable. For example: a dialog has a new optional parameter, a behavior subtly changed but the instructed steps still work, or a UI element was renamed but the old name would still be recognizable.
- `high`: The issue directly changes a UI element, workflow step, or behavior that this lesson explicitly teaches. A student following the lesson with the new FME version would encounter a visible mismatch, error, or confusing discrepancy.

**For `impacts_exercise`:**
Set to `true` if the issue affects one or more exercise steps (the numbered steps students follow interactively). Set to `false` if the issue only affects non-exercise (conceptual/reading) content, or if `update_likelihood` is `none`.

**For `affected_headings`:**
List the specific section headings from the lesson structure above that are affected by this issue. Reference their exact text as shown in the Headings list. Leave the array empty if `update_likelihood` is `none` or `low`.

**For `screenshots_need_retaking`:**
Set to `true` if any screenshot in this lesson would look visibly different after this change (new dialog fields, renamed buttons, changed layouts, new ports/icons, etc.).

**For `affected_screenshots`:**
If `screenshots_need_retaking` is true, list each affected screenshot as an object with:
- `src`: the image filename (from the images list, e.g. `images/1234567890.png`)
- `explanation`: a specific description of what will look different in that screenshot and what update needs to be made (e.g. "The PointOnRasterValueExtractor dialog now shows a Rejected port — retake showing the new port visible on the transformer")
Leave the array empty if no screenshots are affected.
- **Never include `safe_note.png`** in `affected_screenshots`. This is a decorative callout icon and never depicts interactive FME UI.

Respond only with valid JSON matching the required schema. Do not include any explanation or text outside the JSON.
