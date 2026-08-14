# V3 Trial Regression Hardening Implementation Plan

> **For agentic workers:** Execute the tasks inline with verification after each gate.

**Goal:** Prevent the V3 PPT workflow from producing visually repetitive decks,
unconfirmed dark pages, stale intake behavior, and unsafe transformed decorations.

**Architecture:** Keep V1/V2 validation unchanged. Extend the V3 contract from
the intake candidate through the passport and execution manifest, then validate
the HTML markers and audit artifacts at the existing decision, execution, and
delivery gates.

**Tech Stack:** Python `unittest`, JSON workflow manifests, Markdown skills,
HTML-first PPTX converter preflight.

---

### Task 1: Align V3 intake and candidate contracts

**Files:**
- Modify: `ppt-skills-collection/codex-plugin/skills/ppt-workflow-intake/SKILL.md`
- Modify: `ppt-skills-collection/ppt-workflow/templates/workflow-state.example.json`
- Modify: `ppt-skills-collection/ppt-workflow/scripts/check_workflow_state.py`
- Test: `ppt-skills-collection/ppt-workflow/tests/test_check_workflow_state.py`

- [ ] Replace stale V1/V2 intake instructions with the V3 `4+4+4+1` sequence.
- [ ] Require each V3 candidate to declare `backgroundStrategy`,
  `primaryBackgroundMode`, and `compositionFamily` in its visual contract.
- [ ] Require candidate composition families to be pairwise distinct and the
  selected passport to copy all three fields exactly.
- [ ] Add tests for stale-contract rejection and passport drift rejection.

### Task 2: Add composition-family and background execution gates

**Files:**
- Modify: `ppt-skills-collection/ppt-workflow/templates/workflow-state.example.json`
- Modify: `ppt-skills-collection/ppt-workflow/scripts/check_workflow_state.py`
- Modify: `ppt-skills-collection/codex-plugin/skills/ppt-workflow-authoring/SKILL.md`
- Modify: `ppt-skills-collection/codex-plugin/skills/ppt-workflow-review/SKILL.md`
- Test: `ppt-skills-collection/ppt-workflow/tests/test_check_workflow_state.py`

- [ ] Require each V3 execution slide to record and embed
  `compositionFamily`.
- [ ] Reject three consecutive matching composition families and retain the
  existing 20% equal-card-grid limit.
- [ ] Require `data-color-system` and `data-background-mode` to agree with the
  locked passport and color-continuity artifact.
- [ ] Document that a uniform light passport rejects any dark execution slide;
  rhythmic backgrounds require explicit selected-contract evidence.
- [ ] Add tests for repeated composition families and background-mode drift.

### Task 3: Harden conversion-risk guidance and delivery evidence

**Files:**
- Modify: `ppt-skills-collection/html-to-pptx/scripts/preflight.py`
- Modify: `ppt-skills-collection/codex-plugin/skills/ppt-workflow-delivery/SKILL.md`
- Modify: `ppt-skills-collection/ppt-workflow/tests/test_check_workflow_state.py`

- [ ] Treat clipped slide roots with transformed children as a blocking
  preflight risk instead of a warning.
- [ ] Add authoring guidance to use non-transformed decorations for PPTX.
- [ ] Require delivery evidence to report zero unresolved high-risk preflight
  pages and zero structural self-check warnings.
- [ ] Add a regression test for the transformed-decoration preflight case.

### Task 4: Verify and package

**Files:**
- Verify: `ppt-skills-collection/ppt-workflow/tests/`
- Verify: `ppt-skills-collection/html-to-pptx/tests/`

- [ ] Run all workflow-state tests and converter tests.
- [ ] Run `git diff --check` and inspect that only workflow-package files are
  changed.
- [ ] Commit the package-only changes on the existing `ppt正式版` branch.
