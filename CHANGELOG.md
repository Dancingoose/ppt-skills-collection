# Workflow Change Log

This log records every workflow change made after the copied collection was
baselined in `D:\GPTworkspace`. Each entry names the affected files, reason,
and verification so a change can be reverted with Git.

## 2026-08-10 - Baseline

- Recorded the copied PPT skills collection before reliability work begins.
- Known state: the collection is a Claude-oriented workflow; no local Python
  conversion dependencies or UI Pro Max data are installed yet.
- Evidence: `convert.py --help` starts, but a real conversion stops at the
  missing `playwright` module. The original execution checker can also pass
  deliberately incomplete task artifacts.

## 2026-08-10 - Structured Evidence Gate

- Added `ppt-workflow/scripts/check_workflow_state.py`.
- Added `ppt-workflow/templates/workflow-state.example.json`.
- Reason: the legacy checker accepted empty fields and unverified HTML
  comments. The new validator fails closed when structured task evidence is
  missing, checks non-empty preparation and decision evidence, binds every
  slide to an embedded layout, validates data-layout compatibility, records a
  per-slide visual-effect decision, and compares the locked passport with the
  approved passport.
- Verification: Python compilation passed; running the validator against a
  task without a state manifest fails with six explicit failures.
