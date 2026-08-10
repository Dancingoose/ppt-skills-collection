---
name: ppt-workflow-studio
description: Create or revise a presentation, slide deck, or editable PPTX using the local PPT Skills Collection. Use for requests to make PPTs from a topic, document, PDF, existing deck, images, or mixed materials. Capture the audience and intended decision before design; use the collection's themes and layout library; preserve evidence in a task manifest; and validate every stage before delivery.
---

# PPT Workflow Studio

Use the collection at `D:\GPTworkspace\ppt-skills-collection` unless `PPT_WORKFLOW_ROOT` names another valid collection root. Treat `ppt-workflow/templates/workflow-state.example.json` as the task contract and `ppt-workflow/scripts/check_workflow_state.py` as the gatekeeper.

1. Create `<workspace>/workflow-runs/<task-slug>/`. Copy the state template to `workflow-state.json`. Record extracted material in `content-inventory.md`.
2. For a user topic without source material, research factual claims and record source URLs. For supplied material, extract it first and record its path, facts, images, and uncertainty. Do not invent data.
3. Capture audience, intended decision, core claim, and canvas before choosing a visual direction. Ask only unresolved questions; show concise options grounded in the material.
4. Choose a theme from `references/theme-tokens.md` and layouts from `references/layout-library.md`. Read `references/quick-reference-card.md` first, then only the needed sections. Record every slide's content type, layout, data sources, background mode, and visual-effect decision in the manifest.
5. Build HTML first. Give the user a cover plus representative content-page preview before expanding the deck. Put `data-slide-id` and `data-layout` on every `.slide` container.
6. Use image generation only when the material benefits from an image and an available raster generator exists. For data, prefer an evidence-backed chart. Document skipped visual effects with a reason.
7. Run the validator after preparation, design decision, execution, and delivery. Resolve every failure. Run `python <collection-root>/html-to-pptx/convert.py` only after the delivery gate confirms its runtime can render a page.

Do not use direct shape-by-shape `python-pptx` or `pptxgenjs` authoring. Keep the task state, source facts, chosen tokens, and independent review next to the output so another session can resume without relying on chat memory.
