---
name: mbb-decks
description: Shape an evidence-led argument, storyline, action titles, and page plan for every V3 PPT design direction. Use after UI UX research and before design review or visual samples; do not impose an MBB visual theme.
---

# PPT Storyline Directions

Use the collection root named by `PPT_WORKFLOW_ROOT`; when it is unset, derive it from this installed package. Read `design-assets/mbb-decks/SKILL.md` as the authority. Work only in the task directory containing `workflow-state.json`.

1. Verify `design-research.md` exists and its recorded SHA-256 is current. Use the supplied evidence and intent bindings; do not invent claims.
2. Give each recipe a distinct argument, storyline, action-title treatment, page plan, and chart-expression choice. MBB discipline informs the story, not a mandatory consulting appearance.
3. Write `<task>/ghost-deck.md`. Include every recipe ID and `Input SHA-256: <design-research.md hash>`.
4. Register the current file SHA-256 as the third `decision.designOrchestration.artifacts` record. Do not choose a direction or render samples.
