---
name: update-scope
description: Given a Jira issue key or description and optionally a lesson name, applies the editorial guidelines to recommend the correct scope of update — inline edit, callout, new section, new lesson, or human-review flag. Run this when a Jira change seems significant enough that a simple inline edit may not be sufficient.
disable-model-invocation: true
allowed-tools: Read, Glob, Grep
argument-hint: [JIRA-KEY or description] [lesson name (optional)]
---

You are helping determine the correct scope of update for an FME training lesson change. You will apply the editorial decision framework documented in `prompts/EDITORIAL_GUIDELINES.md` to produce a clear recommendation and a concrete instruction the LLM can act on.

## Step 1 — Load the editorial guidelines

Read `prompts/EDITORIAL_GUIDELINES.md`. If it does not exist, stop and tell the user: "Run `/editorial-guidelines` first to build the editorial conventions document before using this skill."

## Step 2 — Get issue context

If `$ARGUMENTS` starts with a Jira-style key (e.g., `FMEFORM-12345`):
- Use Grep to search the `artifacts/` directory for a changelog JSON containing this key
- If found, read the issue summary and description
- If not found, ask the user to paste the issue summary and a brief description of the change

If `$ARGUMENTS` is a plain description, use it as-is.

If nothing was provided, ask: "What Jira issue or change should I evaluate? Provide the issue key or describe the change."

## Step 3 — Get lesson context

Ask: "Which lesson or course is this for? If you know, provide the lesson name. If the change is cross-cutting, say so and I will give general guidance."

If a lesson is named, use Glob to find its `index.html` and read its heading structure and exercise steps to inform the recommendation.

## Step 4 — Apply the decision framework

Using the guidelines from Step 1 and the context from Steps 2–3, work through the following in order. Think out loud as you go — show your reasoning at each step.

1. **Is this change relevant to the lesson at all?** If the specific transformer, dialog, or feature is not referenced in the lesson, say so and stop.
2. **Which sections of the lesson are affected?** Are these conceptual sections, instructional sections, or both? Apply the conceptual section rule.
3. **Is this a change to existing behavior, a new addition, or a removal?** This determines whether to edit in place, add a callout, or remove content.
4. **How significant is the change?** Work up the scope escalation ladder from the guidelines: inline edit → callout → new section → new lesson → human review. Stop at the first threshold that is clearly crossed.
5. **Are exercise steps involved?** If so, apply the exercise step conventions.

## Step 5 — Present the recommendation

Output the recommendation in this format:

---
**Recommended scope:** [inline edit / callout (type) / new section / new lesson / human review]

**Reasoning:** [2–4 sentences applying the specific editorial rules from the guidelines to this issue — cite the rule by name where possible]

**Suggested instruction for the LLM:** [A concrete directive that could be added as a note in the edit-suggestions prompt for this issue, e.g.: "Add a Note callout after the 'Reprojector' heading explaining that a Rejected port was added in TO_VERSION." Or: "Flag this lesson for a new section on multiple geometry columns — do not attempt inline edits."]
---

Ask the user if they agree or want to adjust the recommendation before taking any further action.
