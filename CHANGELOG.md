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

## 2026-08-10 - Portable Runtime Gate

- Replaced hard-coded `D:\CLAUDEworkspace` checker commands in the workflow
  and quick-reference card with `<collection_root>` and `<task_dir>`.
- Made the structured delivery gate launch Chromium and render a page, rather
  than treating an importable `playwright` package as proof of conversion
  readiness.
- Verification: Python compilation passed. The gate correctly fails while the
  Playwright Chromium executable is absent, while confirming that the Python
  conversion dependencies are present in the workspace virtual environment.

## 2026-08-10 - Execution Evidence Regression

- Added cross-layer page-count checks and a required `data-slide-id` plus
  `data-layout` binding for every manifest slide.
- Added verification that a declared ECharts, Three.js, shader, Matter,
  Spline, or Canvas effect has a corresponding HTML signal.
- Verification: a two-page AI adoption simulation passed 28 execution checks,
  including layout/data compatibility, source evidence, theme lock, and effect
  presence.

## 2026-08-10 - Codex Plugin Entry

- Added a versioned `codex-plugin/` containing a `ppt-workflow-studio` skill
  and a PowerShell deployment script.
- Created and validated the personal-marketplace plugin at
  `C:\Users\duanz\plugins\ppt-workflow-studio`.
- Reason: the original collection used Claude-only `Skill(...)` references and
  was not discoverable by Codex. The new entry treats the collection, task
  manifest, and structured validator as the authoritative workflow.
- Verification: both the versioned source plugin and deployed plugin passed
  `validate_plugin.py`.

## 2026-08-10 - Workflow Gate Test Suite

- Added standard-library regression tests for the structured workflow gate.
- The suite covers valid preparation/decision/execution evidence, missing
  manifests, empty intent evidence, qualitative slides using data layouts,
  absent declared effects, and page-count drift.
- Verification: `python -m unittest discover -s ppt-workflow/tests -v` passed
  all six tests in the workspace virtual environment.
