---
name: axi-front-design
description: Render three auditable V3 PPT visual-direction samples from the completed design orchestration, then render the approved recipe as preview and full HTML. Use after frontend-design review before visual-sample confirmation, and again after the creator selects a recipe.
---

# PPT Visual Direction Samples And Delivery

Use the collection root named by `PPT_WORKFLOW_ROOT`; when it is unset, derive it from this installed package. Read `axi-front-design/SKILL.md` as the authority. Work only in the task directory containing `workflow-state.json`.

1. Verify `frontend-design-review.md` exists and its recorded SHA-256 is current. Render all three reviewed directions, never a single default solution.
2. Write `<task>/visual-direction-preview.html` with exactly one sample for each recipe. Each sample must carry `data-design-profile`, `data-design-recipe`, and its composition-family marker. Keep it as an inspection sample, not `preview.html` or `design.html`.
3. Include `Input SHA-256: <frontend-design-review.md hash>` in an HTML comment. Register it as `inputSha256`, register the current sample SHA-256 as the fifth `decision.designOrchestration.artifacts` record, and write `design-orchestration.json` plus matching `decision.designRecipes`.
4. Run `check_workflow_state.py --layer design` before asking the creator the 13th confirmation question. A failed gate means no visual selection, authoring, or conversion.

After the creator confirms one recipe, run this skill again as the HTML-first renderer:

5. Read only the confirmed `decision.designProfile`, matching `decision.designRecipes` entry, locked passport, and review constraints. Do not change the selected recipe's theme, typography, signature, chart language, or motion strategy.
6. Render the representative `preview.html` first and record creator approval in `decision.preview`. After the formal decision gate passes, render `design.html`; every slide must carry `data-design-recipe` for the confirmed recipe.
