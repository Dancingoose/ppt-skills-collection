---
name: ui-ux-pro-max
description: Research color, typography, charts, accessibility, and interaction constraints for all V3 PPT design directions. Use after claude-design directions exist and before MBB storyline work or visual samples.
---

# PPT Design Research

Use the collection root named by `PPT_WORKFLOW_ROOT`; when it is unset, derive it from this installed package. Read `design-assets/ui-ux-pro-max/SKILL.md` as the authority. Work only in the task directory containing `workflow-state.json`.

1. Verify `design-directions.md` exists and its recorded SHA-256 is current. Read every direction; do not collapse them into one generic UI style.
2. For each recipe, research and translate usable palette, type, chart, motion, and accessibility decisions into local PPT constraints. Preserve the three directions' distinct signatures.
3. Write `<task>/design-research.md`. Include every recipe ID, specific adopted constraints, and `Input SHA-256: <design-directions.md hash>` for the work reviewed.
4. Register the current file SHA-256 as the second `decision.designOrchestration.artifacts` record. Do not select a recipe or produce a sample.
