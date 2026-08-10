---
name: ppt-workflow-authoring
description: Build source-backed HTML slides for PPT Workflow Studio using the collection's themes, layout library, and native canvas rules. Use after the design decision is approved and before PPTX conversion or when repairing a source-layout defect.
---

# PPT Workflow Authoring

Use the collection named by `PPT_WORKFLOW_ROOT`, or `D:\GPTworkspace\ppt-skills-collection`.

1. Read `references/quick-reference-card.md`, then only the selected theme block from `references/theme-tokens.md`, the chosen layouts in `references/layout-library.md`, and the native-size rule for the selected canvas in `references/canvas-formats.md`.
2. Build `preview.html` with the cover and a representative content slide before expansion. Bind approval to `decision.preview`; do not expand a rejected or unrecorded preview.
3. Build `design.html` at the native canvas. Each `.slide` must carry `data-pptx-slide`, `data-slide-id`, `data-layout`, and `data-item-count` matching `workflow-state.json`. The explicit marker is required because a small or ultra-wide native canvas can fall below the converter's geometric discovery threshold. Keep facts traceable to the inventory and preserve supplied images when they are evidence rather than decoration.
4. Maintain deliberate page rhythm, layout variation, readable CJK/Latin typography, and a source review at native size. Repair clipping, overflow, overlap, blank render, untraceable data, or a layout/material mismatch before conversion. After the final source review, write the SHA-256 of `design.html` to `execution.sourceVisualReview.htmlSha256`; any HTML change invalidates that review.
5. Use the HTML-first converter only. Do not author the deliverable shape-by-shape with `python-pptx` or `pptxgenjs`.
