---
name: axi-front-design
description: Render three auditable, distinct V3 PPT visual-direction samples from the completed design orchestration. Use after frontend-design review and before the creator confirms the final visual sample.
---

# PPT Visual Direction Samples

Use the collection root named by `PPT_WORKFLOW_ROOT`; when it is unset, derive it from this installed package. Read `axi-front-design/SKILL.md` as the authority. Work only in the task directory containing `workflow-state.json`.

1. Verify `frontend-design-review.md` exists and its recorded SHA-256 is current. Render all three reviewed directions, never a single default solution.
2. Write `<task>/visual-direction-preview.html` with exactly one sample for each recipe. Each sample must carry `data-design-profile`, `data-design-recipe`, and its composition-family marker. Keep it as an inspection sample, not `preview.html` or `design.html`.
3. Include `Input SHA-256: <frontend-design-review.md hash>` in an HTML comment. Register it as `inputSha256`, register the current sample SHA-256 as the fifth `decision.designOrchestration.artifacts` record, and write `design-orchestration.json` plus matching `decision.designRecipes`.
4. Run the decision gate before asking the creator the 13th confirmation question. A failed gate means no visual selection, authoring, or conversion.
