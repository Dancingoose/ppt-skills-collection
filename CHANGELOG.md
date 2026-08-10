# Workflow Change Log

This log records every workflow change made after the copied collection was
baselined in `D:\GPTworkspace`. Each entry names the affected files, reason,
and verification so a change can be reverted with Git.

## 2026-08-10 - Material Inventory Regression Coverage

- Added standard-library tests for Markdown preservation, paragraph-order
  extraction from DOCX OOXML, and explicit unsupported-file reporting in
  `inventory_material.py`.
- Reason: a workflow that cannot reliably preserve supplied source material
  cannot safely infer the creator's intent or choose a presentation layout.
- Verification: full workflow suite passes 12 tests. A contrasting 9-page
  DOCX-driven campus-event simulation passes 16 preparation, 19 decision, and
  120 execution checks; it uses `handdrawn-explainer`, a real Canvas cover
  effect, and a sourced seven-line ECharts budget chart.

## 2026-08-10 - Layout-to-Material Evidence Gate

- Added per-slide `layoutEvidence` validation to the structured gate and its
  sample manifest. It records the repeated-item count, source references, and
  numeric values where a data layout requires them; the rendered slide must
  expose the same item count through `data-item-count`.
- Added explicit limits for A3, B4, B5, B7, B11, B13, B18, B19, and B20 from
  the layout library, and corrected the data-layout registry to include A3,
  B2, and B18.
- Reason: a simulated EV deck passed while assigning three agenda entries to
  six-cell B4 and unsourced three-metric evidence to five-to-ten-value B7.
- Verification: the regression suite now has nine passing tests, including
  incompatible count, mismatched numerical evidence, and missing-evidence
  failures. The corrected 10-page EV simulation passes preparation, decision,
  and execution checks (162 passes before delivery-only checks). Visual
  browser inspection could not run because the in-app browser blocks local
  file URLs; delivery remains separately blocked by the missing Playwright
  Chromium binary.

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

## 2026-08-10 - Material Inventory

- Added `ppt-workflow/scripts/inventory_material.py` for TXT, Markdown, HTML,
  DOCX, and PPTX source extraction.
- The script writes both human-readable `content-inventory.md` and structured
  `material-inventory.json`, including source path, extraction warnings, and
  per-slide embedded-picture references where present.
- The Codex entry now treats source material as untrusted data rather than
  executable instructions.
- Verification: extracted the 10-slide EV market sample PPTX; recovered its
  titles, claims, sources, and correctly reported no embedded pictures.

## 2026-08-10 - Existing Deck Reframe Simulation

- Simulated a 10-page executive market-entry reframe from the extracted EV
  sample material. The simulation used `mbb-consulting`, varied B1/B3/B4/A2/
  B7/B13/B11/B9 layouts, preserved source evidence for quantitative claims,
  and recorded a per-slide effect decision.
- Verification: structured preparation, decision, and execution gates passed
  16, 19, and 85 checks respectively. Delivery remains blocked until a
  Playwright Chromium executable is available, as intended.

## 2026-08-10 - Runtime Bootstrap

- Added `html-to-pptx/scripts/bootstrap-runtime.ps1` to create the workspace
  virtual environment, install conversion dependencies, install Chromium, and
  launch a real page before declaring the converter ready.
- The Codex entry now points new machines to this explicit runtime setup.
- Verification: PowerShell parsing and deployed plugin validation passed. In
  this environment Chromium download timed out twice without transfer, so the
  delivery gate remains intentionally failing.
