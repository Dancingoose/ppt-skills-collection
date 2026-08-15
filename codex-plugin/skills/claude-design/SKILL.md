---
name: claude-design
description: Create the first, divergent design directions for a V3 PPT Workflow Studio task. Use only after the first 12 creator-confirmed intent answers pass and before UI UX research, MBB storyline work, review, or visual samples.
---

# PPT Design Directions

Use the collection root named by `PPT_WORKFLOW_ROOT`; when it is unset, derive it from this installed package. Read `design-assets/claude-design/SKILL.md` as the authority. Work only in the task directory containing `workflow-state.json`.

1. Confirm the first 12 V3 intent answers and `decision.intentBindings` pass the intent gate. Do not ask the creator another question or select a direction.
2. Produce exactly three genuinely different directions. Map the source guidance to the local theme and layout library without forcing one house style.
3. Write `<task>/design-directions.md`. For every recipe ID, record its theme, narrative stance, composition geometry, visual temperature, typography, information structure, image treatment, chart language, motion strategy, signature, and the local-theme mapping.
4. Include `Input SHA-256: <canonical decision.intentBindings hash>` in the artifact. Register it as `inputSha256`, then register the file SHA-256 as the first `decision.designOrchestration.artifacts` record. Do not create later-stage artifacts.
