---
name: editorial-guidelines
description: Interview the user to document FME Academy editorial conventions for lesson updates — when to add callout notes, edit in place, remove content, or flag for a new section or lesson. Writes output to prompts/EDITORIAL_GUIDELINES.md for injection into the edit-suggestions LLM prompt.
disable-model-invocation: true
allowed-tools: Read, Write, Glob, Grep
---

You are building `prompts/EDITORIAL_GUIDELINES.md` — a document injected into the LLM prompt that generates edit suggestions for FME training lessons. Its job is to give the LLM authoritative rules for handling different types of content changes, so it stops guessing about format and scope.

## Step 1 — Check for existing guidelines

Read `prompts/EDITORIAL_GUIDELINES.md` if it exists. If it does, summarize what is already documented and ask whether to update it or start fresh.

## Step 2 — Discover callout types from lesson HTML

Use Glob to find 4–6 `index.html` files spread across different courses and learning paths. Read each and identify:
- All CSS classes on block-level elements (`<div>`, `<aside>`, `<section>`, etc.) that appear to be callout boxes (tip, note, warning, caution, new-feature, etc.)
- The full HTML structure of each callout type — not just the class, but the complete template including any icon, heading, and body elements
- Any version-specific or "new in X.Y" callout patterns

Present your findings clearly: "I found these callout types: [list each with a sanitized HTML example]." Ask the user to confirm the list is complete and correct before continuing. If any class names are ambiguous, ask what they are for.

## Step 3 — Conduct the editorial interview

Ask these questions **one at a time**. Wait for a complete answer before asking the next. Do not combine questions.

**Q1 — Callout purpose:**
"For each callout type we found, what is it for? I need to know when the LLM should choose each type so it picks the right one rather than guessing. Walk me through the differences."

**Q2 — New features:**
"When a Jira issue introduces a significant new feature, should the lesson be updated in place (the text is rewritten to describe the new behavior as the current state) or should a 'New in X.Y' callout be added alongside the existing text? What makes a feature significant enough to need a callout rather than a direct text edit?"

**Q3 — Outdated or incorrect content:**
"When existing lesson content becomes wrong — for example, a parameter has moved, a dialog is renamed, a feature is removed — what is the preferred approach? Should the text be edited in place, a note added, the content removed, or some combination? Does the answer depend on how wrong or how prominently wrong the content is?"

**Q4 — Conceptual sections:**
"When a Jira issue is relevant to a conceptual section (one that explains principles, no exercise steps), what should the LLM do? Should it ever add callouts to conceptual sections, or should edits be restricted to instructional sections only?"

**Q5 — Scope: new section:**
"When does a change require adding a whole new section to a lesson rather than editing existing content? Give me a concrete example of the kind of Jira issue that would cross this threshold. The LLM would flag this rather than create the section itself — so I need to know what the flag should look like in its output."

**Q6 — Scope: new lesson:**
"When does a change require a completely new lesson? What does a Jira change need to look like to warrant this? Again, the LLM would flag it, not create it."

**Q7 — Human review with no suggestions:**
"Are there situations where the LLM should produce no edit suggestions at all and just flag the lesson for manual attention? If so, what should that flag look like in its output?"

**Q8 — Exercise step conventions:**
"Are there specific rules for how exercise steps should be written or updated? For example: voice, formatting, how to indicate a step has changed, whether to update the FME version string (e.g., 'Open FME Workbench 2024.2' → 'Open FME Workbench 2025.0'), etc."

## Step 4 — Synthesize and write

After collecting all answers, synthesize them into `prompts/EDITORIAL_GUIDELINES.md`. Write this document in the second person addressed to the LLM (e.g., "When a Jira issue…, you should…"). Structure:

1. **Purpose** (one paragraph): what this document is and how to use it
2. **Callout reference** (one subsection per type): name, purpose, when to use, complete HTML template with placeholder content
3. **Decision rules** (ordered from least to most intervention):
   - When to edit in place
   - When to add a callout (and which type)
   - When to flag for a new section (and what to output)
   - When to flag for a new lesson (and what to output)
   - When to flag for human review with no suggestions
4. **Conceptual section rule**
5. **Exercise step conventions**

Show the full draft to the user and ask for approval or corrections before writing the file.
