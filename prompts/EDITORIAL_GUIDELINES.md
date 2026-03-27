# FME Academy Editorial Guidelines

These guidelines define how you should handle different types of content changes when producing edit suggestions for FME training lessons. Apply them in addition to the specificity and conceptual-section rules in the main prompt.

---

## Callout Reference

There is one callout structure used in FME Academy lessons:

**Note** — used for supplementary information: links to FME documentation, Knowledge Base articles, webinars, or safe.com pages; extra or advanced information that does not belong in the main lesson flow; warnings or hints for tricky exercise steps.

```html
<blockquote>
<p><img class="img mtm" role="presentation" src="images/safe_note.png" alt="Note" /></p>
<p>Note text here.</p>
</blockquote>
```

**"New for FME X.Y" note** — the same structure as a Note, but the text begins with a bold star prefix. Used for significant new features. See the "New for FME X.Y note" rules below for when to use this.

```html
<blockquote>
<p><img class="img mtm" role="presentation" src="images/safe_note.png" alt="Note" /></p>
<p><strong>⭐ New for FME {{TO_VERSION}}:</strong> Description of the new feature, including a link to the relevant documentation.</p>
</blockquote>
```

Do not use the `<div class="box message info">` wrapper when creating new callouts. That is legacy markup from a previous LMS. Always use the plain `<blockquote>` structure above.

---

## Decision Rules

### 1. Always edit text to be accurate

Whenever a Jira issue changes existing behavior — a renamed parameter, a moved dialog, a changed workflow step, a renamed window — **always edit the lesson text so it accurately describes the new version**. Never leave text that describes something that is no longer true, and never add a note explaining a change without also correcting the underlying text. The lesson must read correctly for a student using {{TO_VERSION}}.

### 2. When to add a "New for FME X.Y" note

After editing text in place, also add a "New for FME {{TO_VERSION}}" note when **all** of the following apply:

- The updated feature is a **primary focus** of the section being edited, not just incidentally mentioned.
- The change is significant enough to warrant one. Use this priority order to judge significance:
  1. **Highest:** Major FME Workbench or FME Flow UI changes — new panels, renamed windows, changed toolbars, new caching behaviors, significant dialog changes.
  2. **Medium:** Major changes to a transformer covered in the lesson — name changes, new or significantly changed functionality or ports.
  3. **Lowest:** Format-specific reader/writer changes — only include if the change directly affects exercise instructions (e.g., a new reader/writer that replaces one used in the exercise). Never include minor format-specific changes.
- Renames, icon changes, and purely cosmetic UI updates do not warrant a New note on their own — just edit the text.

It is acceptable to suggest a New note in more than one lesson or section; the author will decide where to place the canonical one.

### 3. Conceptual section rule

Distinguish between two types of non-exercise content:

- **Pure concept lessons** explain real-world principles unrelated to the FME UI — for example, what coordinate systems are, what geometry types exist, or how spatial analysis works. These lessons contain no FME UI strings, no transformer or dialog names, no product version references, and no Resources section with workspace or data links. **Do not suggest any UI-related edits to these lessons.**
- **UI-focused lessons without exercises** explain how to use FME features but have no interactive exercise steps — for example, "Read and Write Archive File Formats." **Edit these only if the specific changed item is explicitly mentioned in the lesson text.**

### 4. Scope escalation

Apply the following rules in order from least to most intervention. Stop at the first threshold that is clearly crossed.

---

#### Inline edit (+ optional New note)
**Default for all changes.** A renamed parameter, moved dialog, changed icon, new option in an existing workflow, or cosmetic change is handled entirely with text edits, screenshot updates, and optionally a New note as described above.

---

#### Flag for a new section
Flag when **all three** of the following apply:

1. A workflow has changed significantly, or a significant new capability has been added to a commonly used feature.
2. This workflow is already covered in Academy content (i.e., the lesson already teaches the relevant feature).
3. The feature is notable — use the release blog posts on community.safe.com/product-updates as a guideline. When in doubt, apply the priority order from rule 2 above.

For these cases: suggest the standard text edits and screenshot updates, add a New note, and include an additional `add` change at the most relevant location in the lesson. For this `add` change, **attempt to draft the section content** using the Jira issue description, any linked feature documentation, and the surrounding lesson context. Frame the draft as a starting point for the author to refine, not a finished product. Include a note in the explanation: *"This change may warrant a new section. A draft is provided below as a starting point."*

Examples that cross this threshold: the addition of the Spatial Definition Table to writer feature types; live caching.
Examples that do not: renaming Visual Preview to Data Preview; icon or toolbar changes.

---

#### Flag for a new lesson
Flag when a feature is complex enough to require a significant number of new click steps to demonstrate — roughly correlating with a feature that would warrant its own dedicated Knowledge Base article. The complexity bar is high: a feature that can be explained in a paragraph and demonstrated in two or three steps does not cross it.

For these cases: include the standard edits, and add an `add` change at the top of the most relevant existing lesson with this text: *"This feature may be significant enough to require a new dedicated lesson. Consider adding one before or after this lesson. A brief description of what it might cover: [draft outline based on the Jira issue and any available documentation]."*

Example that crosses this threshold: Dynamic Parameters for FME Flow apps.
Example that does not: live caching (new section only).

---

#### Flag for human review (uncertain placement)
When you believe a Jira change is related to the lesson's topic but are not certain where or whether it should be introduced, add an `add` change before the content of the first heading of the lesson with this text: *"This change may be relevant to this lesson, but the appropriate scope or placement is unclear. Please review."* Include the Jira issue key(s) in `issue_keys`. Use this sparingly — only when genuinely uncertain.

---

## Exercise Step Conventions

For every lesson that contains exercise steps (numbered headings such as `1) Start Workbench`):

1. **Check the first exercise step** for a mention of starting in a specific FME product (FME Workbench or FME Flow) and a version number — for example, *"Open FME Workbench (2024.2 or later)."* If this mention is absent, suggest adding it as the first sentence of that step.

2. **Search the full lesson** for any mention of a specific FME product version number that is **not inside a New note**. For every occurrence found, suggest updating it to `{{TO_VERSION}} or later`.
