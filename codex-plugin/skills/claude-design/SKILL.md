---
name: claude-design
description: Develop distinct visual directions for a PPT Workflow Studio task when the creator has not specified a clear visual style. Use in the canonical design-decision layer before selecting a theme; skip only for the documented explicit-style fast path.
---

# Claude Design For PPT

Use the collection root named by `PPT_WORKFLOW_ROOT`; when it is unset, derive it from this installed package. Follow the design-decision routing in `ppt-workflow/SKILL.md` and read `design-assets/claude-design/SKILL.md` as the authority.

1. Use this bridge when the creator needs visual exploration, not when an explicit-style fast path already supplies the direction.
2. Produce three divergent directions from the available design languages and map them to the collection theme library.
3. Keep the result inside the existing design decision and `designProfile` workflow. Do not add a parallel state model or bypass the existing decision gate.
