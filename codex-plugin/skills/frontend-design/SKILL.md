---
name: frontend-design
description: Review V3 PPT design directions for a distinctive visual signature, anti-template risks, usable type, and implementation realism. Use after MBB storyline work and before visual samples.
---

# PPT Direction Review

Use the collection root named by `PPT_WORKFLOW_ROOT`; when it is unset, derive it from this installed package. Read `design-assets/frontend-design/SKILL.md` as the authority. Work only in the task directory containing `workflow-state.json`.

1. Verify `ghost-deck.md` exists and its recorded SHA-256 is current. Review all three directions together.
2. Identify whether a direction is generic, converging with another direction, over-using cards, default typography, decorative gradients, or impractical for HTML-first PowerPoint conversion. Specify repairs while preserving meaningful variation.
3. Write `<task>/frontend-design-review.md`. Include every recipe ID, its signature, concrete risks and repairs, plus `Input SHA-256: <ghost-deck.md hash>`.
4. Register the current file SHA-256 as the fourth `decision.designOrchestration.artifacts` record. Do not render or select a sample.
