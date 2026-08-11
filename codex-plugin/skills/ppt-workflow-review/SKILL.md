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
