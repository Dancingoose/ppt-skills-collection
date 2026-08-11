---
name: ppt-workflow-review
description: Review an evidence-led PPT design before preview approval. Use for PPT Workflow Studio tasks after intent and a design passport exist, or when checking whether a proposed deck misreads supplied material, drifts into a template, uses weak typography, or mismatches a layout to its content.
---

# PPT Workflow Review

Use the collection named by `PPT_WORKFLOW_ROOT`, or `D:\GPTworkspace\ppt-skills-collection`. Work inside the task directory containing `workflow-state.json` and `content-inventory.md`.

1. Confirm `check_workflow_state.py --layer intent` passes before review. Read the inventory, the creator-confirmed `decision.intentQuestionnaire`, Phase 1/2 decision fields, locked or proposed passport, and the relevant portions of `references/quick-reference-card.md`, `references/layout-library.md`, and `references/theme-tokens.md`.
2. Review five areas: `intent`, `evidence`, `theme`, `typography`, and `layouts`. Verify every material claim has a source, the proposed canvas serves the audience, the theme does not contradict the source or requested tone, typography is legible and not a default fallback, and each proposed layout fits its information shape.
3. Identify concrete defects and correct the passport or page plan before preview. Do not merely name a generic design skill as proof of review.
4. Write `<task>/anti-template-review.json` before the preview decision gate:

```json
{
  "schemaVersion": 1,
  "skill": "ppt-workflow-review",
  "result": "pass",
  "reviewedAreas": ["intent", "evidence", "theme", "typography", "layouts"],
  "notes": "Specific evidence, decision, and any revision made."
}
```

5. Copy its result, notes, and filename into `decision.antiTemplateReview`, with both `reviewer` and `skill` set to `ppt-workflow-review`. The workflow validator must pass before the preview is shown.

## Post-Build Color Continuity Review

After every planned slide exists and before effects or conversion, render the source HTML at its native canvas and inspect the deck in sequence. This is a separate review from the pre-preview review.

1. Group slides by their intended light/dark mode. For each group, inspect the actual perceived canvas, not only the CSS variable: background base color, visual temperature, dominant surface treatment, and the proportion of warm/cool imagery or callouts. A page may use the same CSS base color yet appear to have a different background because its large surfaces shift the visual temperature.
2. Repair a false background shift by changing the conflicting surface, frame, callout, or image treatment. Do not silently accept it because the literal CSS background happens to match.
3. Give every `.slide` a `data-color-system` value. All slides in one reviewed light/dark system must use the matching value.
4. Write `<task>/color-continuity-review.json` after the repair and before conversion:

```json
{
  "schemaVersion": 1,
  "skill": "ppt-workflow-review",
  "result": "pass",
  "reviewedSlides": [1, 2],
  "htmlSha256": "[SHA-256 of design.html]",
  "notes": "Reviewed the sequence for false background shifts.",
  "colorSystems": [
    {"id": "coastal-dark", "mode": "dark", "slides": [1], "baseColor": "#10283C", "temperature": "cool", "dominantSurface": "ink and aqua", "notes": "Cover system."},
    {"id": "coastal-light", "mode": "light", "slides": [2], "baseColor": "#F2FBFA", "temperature": "cool", "dominantSurface": "foam and aqua", "notes": "Content system."}
  ]
}
```

5. Copy its filename, result, slide IDs, HTML hash, and notes into `execution.colorContinuityReview`. Any later HTML change invalidates this review. The execution gate must pass before conversion.
