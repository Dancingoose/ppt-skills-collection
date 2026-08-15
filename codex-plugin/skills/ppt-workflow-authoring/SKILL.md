---
name: ppt-workflow-authoring
description: Build source-backed HTML slides for PPT Workflow Studio using the collection's themes, layout library, and native canvas rules. Use after the design decision is approved and before PPTX conversion or when repairing a source-layout defect.
---

# PPT Workflow Authoring

## V3 方案映射

只使用已确认的 `decision.designProfile`。将其完整 `visualContract` 复制到设计护照；每页登记一个页面原型并在 HTML `.slide` 写入 `data-archetype`。用不同原型组织信息，不得把连续内容退化为重复卡片网格。

Use the collection root named by `PPT_WORKFLOW_ROOT`; when it is unset, derive it from this installed package.

1. Run `check_workflow_state.py --layer intent` and resolve every failure before authoring a preview or full deck. Read `references/quick-reference-card.md`, then only the selected theme block from `references/theme-tokens.md`, the chosen layouts in `references/layout-library.md`, and the native-size rule for the selected canvas in `references/canvas-formats.md`.
2. Build `preview.html` with the cover and a representative content slide before expansion. Bind approval to `decision.preview`; do not expand a rejected or unrecorded preview.
3. Read `references/web-image-sourcing.md` before placing a non-data image. Build `design.html` at the native canvas. Each `.slide` must carry `data-pptx-slide`, `data-slide-id`, `data-layout`, `data-item-count`, and `data-color-system` matching `workflow-state.json` and the post-build color review. The explicit marker is required because a small or ultra-wide native canvas can fall below the converter's geometric discovery threshold. Keep facts traceable to the inventory and preserve supplied images when they are evidence rather than decoration. For missing imagery, use only a licence-verified image recorded in `image-sourcing-plan.md`, or the page's recorded no-image layout; never generate, request, or use AI-generated imagery. ECharts data charts are outside this image rule.
4. Follow the locked `passport.backgroundStrategy`: for `uniform`, every slide uses `primaryBackgroundMode`; for `rhythmic`, use intentional alternation only. Maintain layout variation, readable CJK/Latin typography, a source review, and a color-continuity review at native size. Inspect the rendered sequence by light/dark system; repair a page whose warm or cool surface weight makes its background appear inconsistent even when its literal CSS background matches. Repair clipping, overflow, overlap, blank render, untraceable data, or a layout/material mismatch before conversion. After the final reviews, record the SHA-256 of `design.html` in both `execution.sourceVisualReview.htmlSha256` and `execution.colorContinuityReview.htmlSha256`; any HTML change invalidates both reviews.
5. Use the HTML-first converter only. Do not author the deliverable shape-by-shape with `python-pptx` or `pptxgenjs`.

### V3 regression guards

- Copy `backgroundStrategy`, `primaryBackgroundMode`, and `compositionFamily`
  from the selected visual contract into the locked passport.
- Every execution slide must declare `data-composition-family` and
  `data-background-mode` alongside `data-archetype`.
- Prefer non-transformed decorations. Do not place rotated children inside a
  clipped `.slide` root; the converter treats that pattern as blocking.
- For a uniform light passport, all slides must use the light background mode.
