---
name: ppt-workflow-delivery
description: Convert validated PPT Workflow Studio HTML to PPTX and audit the real rendered output. Use for final presentation delivery, re-export after a repair, or when diagnosing conversion differences between HTML and PowerPoint.
---

# PPT Workflow Delivery

Use the collection root named by `PPT_WORKFLOW_ROOT`; when it is unset, derive it from this installed package.

1. Run `check_workflow_state.py` for intent, preparation, decision, and execution. Resolve every failure, including creator-confirmed intake, review, and effects-scan artifacts, before conversion.
2. Confirm the runtime can render a page. On a new machine run `html-to-pptx/scripts/bootstrap-runtime.ps1`; do not claim a healthy converter from import checks alone.
3. Convert the HTML using `html-to-pptx/convert.py`. Let the converter derive the PPTX page size from the measured active slide; do not assume 16:9.
4. Inspect the generated HTML/PPT comparison image for every page at native dimensions. Check source images, charts, text, CJK glyphs, layout, clipping, and blank content. Fix source HTML or converter defects, re-export, and repeat the audit when needed.
   Treat any blocking preflight risk, including clipped slide roots with transformed children, as a failed delivery. Do not ship until the risk is removed and preflight reports zero blocking risks.
5. Record the final output filename, audit result, reviewed page count, SHA-256 of the audited PPTX, and specific findings in `delivery.audit`. Delivery is incomplete until the delivery gate passes; any PPTX change after review invalidates the audit.
