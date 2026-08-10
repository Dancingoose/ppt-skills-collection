---
name: ppt-workflow-effects
description: Evaluate every completed PPT HTML slide for an appropriate visual effect and produce auditable effect-scan evidence. Use after HTML slides exist in a PPT Workflow Studio task, including when the correct decision is to use no visual effect.
---

# PPT Workflow Effects

Use the collection named by `PPT_WORKFLOW_ROOT`, or `D:\GPTworkspace\ppt-skills-collection`. Read `ppt-visual-effects/SKILL.md` and the affected HTML slides before making any decision.

1. Scan every slide exactly once after its HTML structure is complete. Consider effects only when they improve the meaning: sourced charts for real data, Canvas for a suitable expressive motif, or a restrained motion/3D treatment for genuinely spatial or energetic content.
2. Skip effects for text-led, source-image-led, dense, or static information slides when an effect would weaken inspection, readability, or delivery reliability. Do not inject an effect merely to satisfy the scan.
3. For an applied effect, embed working code inside the relevant `.slide`, preserve editable foreground text, use the selected theme's CSS variables, and verify that the effect is visible in the source HTML. Keep chart data traceable to supplied evidence.
4. Write `<task>/effects-scan.json` with one entry for every slide:

```json
{
  "schemaVersion": 1,
  "skill": "ppt-workflow-effects",
  "slides": [
    {"id": 1, "status": "skipped", "reason": "Source-image-led card; an effect would reduce inspectability."},
    {"id": 2, "status": "applied", "type": "echarts", "reason": "Sourced trend needs a chart."}
  ]
}
```

5. Copy each record exactly into the matching slide's `visualEffect` and record `execution.effectScan` with `skill: "ppt-workflow-effects"`, artifact filename, and every slide ID. Resolve validator failures rather than editing the manifest independently of the scan.
