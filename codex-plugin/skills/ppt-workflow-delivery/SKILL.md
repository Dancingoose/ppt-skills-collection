---
name: ppt-workflow-delivery
description: Convert validated PPT Workflow Studio HTML to PPTX and audit the real rendered output. Use for final presentation delivery, re-export after a repair, or when diagnosing conversion differences between HTML and PowerPoint.
---

# PPT Workflow Delivery

Use the collection named by `PPT_WORKFLOW_ROOT`, or `D:\GPTworkspace\ppt-skills-collection`.

1. Run `check_workflow_state.py` for preparation, decision, and execution. Resolve every failure, including review and effects-scan artifacts, before conversion.
2. Confirm the runtime can render a page. On a new machine run `html-to-pptx/scripts/bootstrap-runtime.ps1`; do not claim a healthy converter from import checks alone.
3. Convert the HTML using `html-to-pptx/convert.py`. Let the converter derive the PPTX page size from the measured active slide; do not assume 16:9.
4. Inspect the generated HTML/PPT comparison image for every page at native dimensions. Check source images, charts, text, CJK glyphs, layout, clipping, and blank content. Fix source HTML or converter defects, re-export, and repeat the audit when needed.
5. Record the final output filename, audit result, reviewed page count, and specific findings in `delivery.audit`. Delivery is incomplete until the delivery gate passes.
