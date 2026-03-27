# Open

## App / UX

- 68. **Anchor-link deep linking between the Lesson Edits and Recommendations tabs.** Clicking "↗ View recommendation card" from an edit tooltip navigates away with no easy way to return. Fix: introduce a URL query-parameter deep-link scheme in `report.html`. Each recommendation card gets `id="card-{REC_ID}"` and each track-changes element gets `id="le-change-{CHANGE_ID}"`. The "view recommendation card" link opens with `?tab=recommendations&card=REC_ID` (or in a new browser tab). On page load, `report.html` reads these params and jumps to the correct tab, page, and element. The reverse direction — card's edit-suggestion list to a specific change — uses `?tab=lesson-edits&lesson=LESSON_ID&change=CHANGE_ID`. Ties into issues 51 and 67.

- 67. **Jumping to a recommendation card from an edit link is broken for cards on page > 1 or hidden by active filters.** `leGoToChange()` in `report.html` calls `scrollToCard()` without ensuring the card is visible. Fix: before scrolling, (1) navigate to the page containing the target card, and (2) reset or update any active filters that would hide it. The query-param scheme from issue 68 can make this robust by encoding the correct page and filter state in the link itself.

- 66. **Add copiable change IDs to edit suggestions.** Each text change already has a `change_id` in the edit-plans JSON. Add a click-to-copy chip (e.g. `#a1b2c3d4`) to each `tc-wrap` element in the Lesson Edits tab, styled consistently with the existing copy chips on recommendation cards (issue 15). Use `navigator.clipboard.writeText`. Also provides the stable ID needed for anchor links in issues 51 and 68.

- 65. **Edit suggestions occasionally render with literal HTML tags in the output text.** The LLM outputs `suggested_text` containing markup (e.g. `<p>…</p>`) despite `EDIT_SUGGESTIONS.md` specifying "plain text, not HTML." Fix with two layers: (1) Add explicit rule to `EDIT_SUGGESTIONS.md`: *"`suggested_text` must be plain text only — do not include HTML tags."* (2) Add a post-processing pass in `edit_suggestions.py` that strips HTML tags from `suggested_text` via `html.parser` as a defensive fallback.

- 64. **Edit suggestions incorrectly delete large blocks of text.** The LLM selects overly broad `original_text` for `delete` changes, removing content that should stay. Fix in `EDIT_SUGGESTIONS.md`: (1) *"Only use `type: 'delete'` for content that is factually incorrect in the new version with no corrected replacement — prefer `type: 'change'` with corrected text in almost all cases."* (2) *"For `delete`, `original_text` must be the minimum text needed to identify the specific sentence or phrase to remove — never an entire paragraph or section."*

- 63. **Neighboring edit tooltips can appear simultaneously and overlap.** Low-priority visual issue; no fix needed now. When addressed: in the tc-popup hover JS, dismiss all other visible popups before showing a new one.

- 62. **Screenshot update notes should also recommend alt text corrections.** When a depicted UI element is renamed (e.g., "Feature Information Window" → "Record Information Window"), the alt text likely needs updating too. Fix: add an optional `alt_text` field to the `screenshot_updates` schema in `EDIT_SUGGESTIONS.md` with instruction: *"If the alt text of this screenshot contains a term that has changed, populate `alt_text` with the corrected alt text."* Update `edit_suggestions.py` to store this field and `report.html` to display it in the screenshot update box.

- 61. **Screenshots are missing from the Lesson Edits tab (update box renders but image is broken).** Likely a path-resolution bug: the base-path logic in `report.html` (`../{lesson_dir}/`) may not cover all nested lesson directory structures. Investigate how `lesson_dir` is stored in the edit-plans JSON and how image URLs are constructed for the Lesson Edits tab. The path must be correct relative to `artifacts/` where `report.html` is served. Fix the path-construction logic in `report.html`.

- 60. **Track tool accuracy automatically using accept/reject data.** Per-change accept/reject state is already persisted in localStorage. A future enhancement could aggregate this by Jira project, issue type, and lesson type to surface accuracy trends without manual review. Log as future work; do not implement now.

## AI Accuracy

- 69. **Optimize model to reduce API costs.** I chose `gpt-4o-mini` in initial testing, but we could do additional benchmarking to look for a cheaper model that meets our needs.

- 59. **LLM suggests version-specific edits inside conceptual sections.** `EDIT_SUGGESTIONS.md` sends the full lesson HTML but gives the LLM no signal about which sections are instructional vs. conceptual. Fix: in `edit_suggestions.py/_build_prompt()`, inject a **Section Classification** block derived from manifest data — listing each h2/h3 heading alongside `has_exercise_steps: true/false`, computed from whether exercise steps fall under that heading in the manifest. Add rule to `EDIT_SUGGESTIONS.md`: *"Sections with no exercise steps and no Resources block are conceptual — they explain general principles. Do not suggest inserting version-specific feature details into them. Place version-specific changes in instructional sections only."*

- 58. **The specificity rule from `ASSESSMENT.md` is absent from `EDIT_SUGGESTIONS.md`.** The rule — *"if a Jira issue names a specific transformer/format/dialog, only act where that item is explicitly referenced"* — was never added to the edit-suggestions prompt. The LLM therefore generates edits for thematically related sections that don't mention the specific item. Fix: add an equivalent rule to `EDIT_SUGGESTIONS.md`: *"If a Jira issue names a specific transformer, data format, dialog, or UI element, only suggest changes to sections of the lesson HTML where that exact item is explicitly mentioned. Do not suggest changes based on topic proximity alone."* This is the single highest-impact accuracy fix.

- 57. **Decorative callout/note images are incorrectly flagged for screenshot updates.** Tip boxes, warning icons, and conceptual diagrams have no FME UI content but get flagged because the surrounding section topic is related to the Jira change. Fix: in `manifest.py`, detect images inside callout containers (e.g. elements with class `tip`, `note`, `warning`, `caution`) and tag them `is_callout: true` in the image list passed to the prompt. In `ASSESSMENT.md`, add: *"Images tagged `is_callout: true` are decorative — they never depict interactive FME UI and must never appear in `affected_screenshots`."* Also reinforce: *"Only flag a screenshot if its alt text or immediately surrounding text explicitly names the UI element changed by the Jira issue."* Note that screenshots within notes might contain FME UI. The main one to ignore is note.png.

- 56. **Exercise version strings (e.g., "FME Workbench 2024.2") are consistently missed.** Fix with two layers: (1) Add explicit instruction to `EDIT_SUGGESTIONS.md`: *"Search all exercise steps for occurrences of the FROM_VERSION string. If found (e.g., 'Open FME Workbench 2024.2'), always generate a `change` edit to replace it with TO_VERSION. If no exercise step contains the FME version string, note this as a potentially missing instruction."* (2) Add a post-processing pass in `edit_suggestions.py` that scans lesson HTML for the FROM_VERSION string in exercise-step elements and auto-inserts a change if the LLM missed it.


- 53. **Generic screenshot alt text makes it impossible for the LLM to identify affected screenshots.** When alt text says "Inspecting points and attributes" instead of naming the window or dialog, the LLM can't connect a UI rename to that screenshot. Short-term fix in `ASSESSMENT.md`: *"Use alt text as the primary description of the image. Only flag a screenshot if its alt text or immediately surrounding text explicitly names the UI element changed by the Jira issue — do not infer from the general section topic."* Long-term: add an optional pipeline step that passes actual images to a multimodal LLM call to generate descriptive alt text for screenshots with generic alt text.

- 52. **No framework for determining the scope of a required update.** *(Requires user-contributed procedure.)* The LLM defaults to inline edits for everything, including cases where a new callout, new section, new lesson, or new course is more appropriate. The correct scope is an editorial judgment the author must define: when a "New in X.Y" callout is sufficient; when a new paragraph or section is needed; when a new lesson is needed; when a new course is needed. Once documented, this belongs in `EDIT_SUGGESTIONS.md`. **Candidate for a Claude Code skill** (`/update-scope`) that walks through these criteria interactively for a given Jira issue and lesson.

- 51. **Edit suggestions have no deep-link URL to a specific change within a lesson.** The `change_id` exists on every edit but there's no way to share or navigate to a specific one. Fix: assign `id="le-change-{change_id}"` to each `tc-wrap` element in the rendered lesson. The popup "view recommendation card" link and the card's edit-suggestions expansion (issue 37) should both expose a copyable URL using the scheme from issue 68. Closely tied to issue 66.


# Fixed

- 55. Editorial guidelines documented via the `/editorial-guidelines` skill interview and written to `prompts/EDITORIAL_GUIDELINES.md`. Injected into `EDIT_SUGGESTIONS.md` via `{{EDITORIAL_GUIDELINES}}` placeholder, populated in `edit_suggestions.py/_build_prompt()`.
- 54. `EDIT_SUGGESTIONS.md` now requires `suggested_text` for `type: "add"` changes to be complete, ready-to-insert HTML using the callout templates from the Editorial Guidelines. Inconsistency in the `suggested_text` field description (previously said "plain text, not HTML" for all types) also corrected.

- 43. Build a browser-based launcher UI so users don't need the CLI. See [memory/issue-43-plan.md](memory/issue-43-plan.md) for the full implementation plan.
- 50. "Gen Edits" button renamed to "Generate Edit Suggestions"; history "Report" renamed to "View Report".
- 49. Step 6 now runs when checked: `getOptions()` always sends an explicit `--steps` string, so step 6 is included when its checkbox is ticked.
- 48. "View Report" console button now does a HEAD request first and only appears if the report file actually exists (suppresses it on dry runs and runs without step 5).
- 47. Add next edit, previous edit buttons to the Edit tab to facilitate quickly jumping between edits. I think it would make sense for these to float in the bottom right of the window at all times.
- 46. Step 6 now automatically regenerates the report after writing edit plans, so `EDIT_PLANS_FILE` is populated in the HTML and the Lesson Edits tab is enabled without needing `--report-only`.
- 45. Saved image paths now stripped correctly: was using `img.src` (absolute URL) for comparison against a relative `lessonBase` string — switched to `img.getAttribute('src')` with `startsWith()`.
- 44. Screenshot accept/reject popup now triggers on hover: the screenshot `tc-wrap` was a `<span>` containing a `<div class="screenshot-note">`, which is invalid HTML — the browser restructured the DOM, moving the note outside the `<span>` so `leBindPopups()` couldn't find `.tc-popup` inside `.tc-wrap`. Fixed by using `<div>` for the screenshot wrapper.
- 42. Images in Lesson Edits tab now preserve aspect ratio via `height: auto` on `.lesson-edit-body img`.
- 41. Rejecting an `add`-type change now correctly restores original text. `data-orig` was always `""` for add changes; now stores the anchor text. `leApplyState` and `leSave()` updated to use orig on reject/pending. Accepted add produces `orig + sugg`.
- 38. Saving edited HTML now calls `serve.py`'s `/api/save-lesson` endpoint, which writes the file to the correct versioned folder and copies images. Falls back to browser download if `serve.py` is not running.
- 37. Update suggestion cards have an expandable "✏ N edit suggestions" section that links to each suggested change in the Lesson Edits tab.
- 36. Added "FME Terminology Disambiguation" section to `prompts/ASSESSMENT.md` listing known confusable pairs (e.g., "Feature Inspector" window vs "Inspector" transformer).
- 35. Popup reordered so Accept/Reject buttons appear at the top, explanation text below.
- 34. JS-driven hover with 300ms delay; popup gap closed to 0 so mouse can reach it reliably.
- 33. Post-processing filter in `edit_suggestions.py` removes `add` changes whose `suggested_text` is already present in the lesson HTML.
- 32. Screenshot update suggestions wrapped in `tc-wrap` with Accept/Reject popup identical to text changes.
- 31. Rejected wraps now show original text in a gray box; yellow dotted underline replaced with gray, removing the red-strikethrough appearance.
- 30. Marking a card as Incorrect from the Recommendations tab records the issue key in `leRejectedIssueKeys`; changes for that key are auto-rejected whenever a lesson is rendered in the Lesson Edits tab.
- 29. Accept/Reject popup includes "↗ View recommendation card" link that switches to the Recommendations tab and scrolls to the card.
- 28. "✗✗ Reject all for KEY" button in popup rejects all changes for that issue key and marks the card as Incorrect.
- 27. HTML preview images now use `../{lesson_dir}/` as the base path so images resolve correctly when served from `artifacts/`.
- 26. Build system to suggest edits to lesson content.
    - 26A. New Step 6: edit plan backend.
        - New `pipeline/edit_suggestions.py` module (analogous to `assessment.py`).
        - New `prompts/EDIT_SUGGESTIONS.md` prompt template.
        - Output: `artifacts/edit-plans-{RUN_ID}.json`.
        - Groups medium+high assessments by lesson; makes one LLM call per lesson.
        - Uses `gpt-4o` by default for higher-quality text edits (separate config setting `EDIT_SUGGESTIONS_MODEL`).
        - Schema per lesson: `{ lesson_id, lesson_html, issues_addressed, changes: [{change_id, type, heading, original_text, suggested_text, explanation, issue_keys}], screenshot_updates: [{src, explanation, issue_keys}] }`.
        - Integrated with CLI (`--steps 6`) and `runs.json` artifact registry.
    - 26B. Phase 1: Read-only track changes tab in the existing report.
        - New "Lesson Edits" tab alongside the existing "Recommendations" tab in `report.html`.
        - Lesson selector: learning path → course → lesson dropdowns.
        - Renders the full lesson HTML with inline track-changes markup: green additions, red/strikethrough deletions, yellow+red changes showing old and new text.
        - Hover tooltip on each change shows the explanation and issue key link(s).
        - Screenshot update notes displayed as yellow comment boxes below the affected image.
    - 26C. Phase 2: Interactive accept/reject and save.
        - Hover over any change to show Accept / Reject popup buttons.
        - Undo and redo buttons in the toolbar.
        - Save button generates a downloadable `index.html` with accepted changes applied; a banner shows the correct target version path where the file should be placed.
- 25. Each card currently has a section below the Jira issue name that says, "Affects: n/a" I am not sure what this is supposed to capture, but it's n/a for all cards. Please fix it show it actually shows whatever it is you are trying to show. Maybe the changelog version?
    - Shows fixed version now.
- 24. Cards should provide a link to the Jira issue. You can dynamically form those according to the following template: {JIRA_BASE_URL}/browse/{JIRA_ISSUE_KEY}, e.g., https://safesoftware.atlassian.net/browse/FMEFORM-33646. Please use the JIRA_BASE_URL from .env and JIRA_ISSUE_KEY from the returned Jira issues.
- 23. I'd like more detail in the suggested edits. Let's start by adding the following features:
    - 23A. Cards should identify if they impact an exercise or not. This should be available as a toggle in the card filter, "Impacts Exercise" It should be shown as a chip on the card like the current "Screenshots needed" chip as well.
    - 23B. Add the Screenshots Needed chip as a togglable filter on the cards as well.
    - 23C. The section on the right that reports how the issue might impact the lesson and lists the impacted sections needs to be more detailed. Steps:
        - Divide the Assessment section up into collapsible/expandable sections.
        - First section, open by default: Summary. This should be the current paragraph at the top of the Assessment section that summarizes the issue's potential impact on the lesson.
        - Second section, collapsed by default: Affected Headings. This replaces the current "affected elements" list, but only captures the impacted headings. When clicked, it shows the list of impacted headings. This is the same list as the current method.
        - Third section, collapsed by default: Affected Screenshots. This section should be expanded and should actually show all potentially impacted screenshots. Each screenshot should have its own explanation as to why it needs to be updated and what update needs to be made.
- 22. Add a hover effect on the Active, Done, and Incorrect buttons.
- 21. #80c27790 is a false positive. It refers to Workspace Parameters, a specific section of the Navigator UI. It does not mean "all parameters you can set in the workspace." I realize that is a bit confusing, so I'm not sure we can fix this one. Any ideas welcome.
- 20. Add support for reading Jira issues directly using the Jira API. I have added a Jira API key to .env. The CSV currently in use (`jira_export.csv`) pulls issues from a Jira Filter called Public Changelog. I've added the filter ID in .env as well. The API approach should retrieve the issues from that filter. They are the full list of all Jira changes that should be considered for training updates; we've already built in the filtering that accounts for pulling the relevant issues. I'll leave it up to you which approach you want to use; pulling all issues and keeping them in a local file similar to the CSV, or pulling Jira issues only. In either case, I think there should be a CLI option that determines if the user is supplying the issues via a Jira export CSV or wants to use the API. Please let me know what other information you need.
- 19. Add support for a very basic "checklist" function in the HTML page. The goal here is to allow the user to manually set each recommendation card's status as "done" or "incorrect" on the HTML page. They default to a status of "active." Once checked off, the card disappears from view. Please add filters for "active" "done" and "incorrect" that allow the user to filter the list of cards by their status.
- 18. Store recommendation status so the HTML page is persistent between sessions. This is so the user can continue to refer to these as they do the updates over multiple working days. I suppose this would include adding status to the recommendation JSON. This status is per-run and per-HTML file; it's expected to always have a default value of "active" on new runs.
- 16. Add documentation of the CLI tool to README.md, including the existing commands and how to run the full pipeline. Also include instructions to install any prerequisites, including Python and requirements.txt for non-technical users. Also note that the user should provide API keys and other configuration settings in .env.
- 15. Add behavior to the update recommendation tags #xxxxxx to allow for quick copying and pasting of the ID. So if you hover it animates and suggests Copy, click to copy to clipboard.
- 14. False positives fixed (full lesson text + specificity rule in prompt + excluded programs pre-filter):
    - #2c92070d #d4220140 #a673fbb7 #045ecab1 = User Parameter Manager issues → `none` (full lesson text showed UPM dialog never referenced)
    - #3acefb2b = Quick Translator pre-filtered from changelog before reaching LLM (`EXCLUDED_SUMMARY_PREFIXES` in config)
    - #e3bef7aa = Data Inspector → `none` (excluded programs rule in prompt)
    - #796fff1e = Oracle Autonomous format → `none` (full lesson text confirmed format not in lesson)
- 13. Add a dropdown to filter update recommendations by lesson as well.
- 12. Add an update recommendation ID to all recommendation cards. That way I can refer to a specific issue x lesson intersection when debugging.
- 11. Update recommendation cards currently mention the specific lesson, but nothing more detailed than that. These updates occur to sometimes a single sentence in the lesson. The identification of where the update needs to occur should be more specific. Instead of just the lesson name, include the specific heading and screenshots that might be impacted.
- 10. How much more would it cost to include the _entire_ lesson text content in the API calls? I ask because my review indicates some very obvious false positives are being generated. I think if the LLM had access to the entire lesson context, it would not generate these false positives. It sounds like it is guessing what steps are in these lessons instead of actually checking the exact step content. The remaining issues below may be addressed if we provide more context.
- 9. FMEFORM-34424 should not be flagged for this lesson. The Add Reader dialog is different from the Web Service creation dialog. That should be pretty evident from the context. How can I provide more information so that is more obvious? Let's think of a systematic change we can make to avoid this kind of mistake.
- 8. For FMEENGINE-67308, the CommonLocalReprojector is a _super_ niche transformer. Why did you think it was relevant for this lesson? We make no mention of this transformer in this lesson. We may mention a Reprojector, but that's a different transformer. Come up with a systematic way to avoid misrecognizing specific changes like this for more general ones, or for incorrectly matching transformers like this.
- 7. For FMEENGINE-87516, you really misunderstood the issue. The issue is about a _specific_ spatial format, Landonline, but you mistook it for a _general_ change impacting all spatial formats. I'm not sure why - it seems to me from the issue pretty clear this impacts only this specific format. This format is not used anywhere in the Academy. Why did you think it was general? Do you think providing the entire lesson context would help you avoid such a mistake in the future?
- 6. For FMEENGINE-85392, again a super specific change you mistook for a more general one. The lesson content never describes reading embedded rasters in Excel. It does read from Excel, but it's obvious from the lesson this is just a table, no raster. Again, I think this mistake can be avoided if we send the entire lesson text in the API call.
- 5. Please completely ignore Jira issues where Issue Type = Bug. The vast majority of Bugs will not impact training. This should reduce false positives and the number of API calls required. FMEENGINE-87432 is an example of an issue that can safely be ignored.
- 4. The current run found a High likelihood Bug from the FMEFLOW project and thought it would impact the Connect to Data course. That is a problem. That course does not cover any FME Flow functionality; it might mention it in passing, but no FME Flow issues should impact that course. It sounds like the LLM was not given sufficient context to understand this lesson does not use FME Flow. Therefore, I think we should make a new rule. If a course does not map onto a product according to the product-mapping.json file, issues from that product's project should not be included at all. So for FME Form Basic, no FMEFLOW issues should be considered. If any project or course mapping is unclear there, let me know and we can work on it.
- 3. Most of the major functionality changes that I know will impact this update are not included in the report. That means we have a serious false negative problem. For example, the entire Epic FMEFORM-32764 ("Workbench: Reorganized menus for clearer structure and usability") will impact most FME Form lessons. Investigate why it and its child issues were not detected. Another Epic has the same problem: FMEFORM-34707 ("Workbench: Visualize live feature caches 26.1"). I don't see any of the child issues for these Epics in the None category, suggesting no API call was ever made for these issues. Why not?
- 2. The "Course" drop-down in the HTML report only shows "All" when the pipeline ran on one course. It should instead show the name of the course.
- 1. Please add the pagination buttons at the top of the page as well.

# Won't Do

- 17. Ideas for verification. What do you think about making the following changes? Will they improve the speed of execution and reduce API costs? Do you think there will be any quality changes?
    - Generate MD copies of the HTML.
    - Then use https://github.com/tobi/qmd?tab=readme-ov to generate embeddings for all training content.
    - Use the Jira MCP server to fetch issues and use the local embeddings database instead of including lesson text in the API calls. I suppose this would look like one Jira issue at a time compared to whatever embeddings were in the subset of content defined in update-job.json.
    - REASONING: this path would reduce the LLM API calls, but would likely reduce the quality of the results. I will not pursue it unless cost becomes a concern.

# Future Work (Out of Scope)

- 39. Use the RDS transformer/format name database to inject a list of relevant transformer and format names into the assessment and edit suggestion prompts, so the LLM can more accurately distinguish specific transformer names from general concepts or UI elements. FME has ~500 transformers and ~1000 formats — this context could significantly reduce false positives like issues 8, 36, etc.
- 40. Maintain a `data/fme-terminology.json` file of known confusable term pairs (e.g., "Feature Inspector" window vs "Inspector" transformer) that gets injected into prompts dynamically. This would be extensible as new false positives are discovered, and could be populated semi-automatically from the RDS database and manual review.
- ~~43. Build a front-end that allows for the generation of reports in the browser so the user doesn't have to use the command line to use this tool. This means a page that lets the user choose the learning path/lesson/course in a multi-select tree, choose the to version, and generate the update recommendations and edit recommendations. The progress should be shown in the browser. Steps like regenerating the report or running using the Jira cache should be exposed. Basically just build a front end for the existing CLI commands.~~ → Moved to Open.