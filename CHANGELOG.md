# Workflow Change Log

This log records every workflow change made after the copied collection was
baselined in `D:\GPTworkspace`. Each entry names the affected files, reason,
and verification so a change can be reverted with Git.

## 2026-08-11 - Multi-Source Inventory And Canvas Capture Isolation

- Extended the material inventory CLI to accept multiple local files and
  repeatable HTTP(S) URL inputs in one bounded run. It writes an auditable
  per-source record, preserves source boundaries in the extracted Markdown,
  and retains the existing single-source fields for compatibility.
- Added a Markdown-plus-CSV simulation that uses a Bauhaus decision brief,
  six distinct layouts, source-to-slide evidence, an ECharts data view, and a
  Canvas visual effect. It passed all workflow gates after a real PowerPoint
  render and six-page HTML/PPT visual review.
- Fixed Canvas media capture: Chromium element screenshots are composited and
  could include a transparent Canvas's visible sibling text. The converter now
  hides and restores those direct siblings during capture so text remains one
  editable PPT object rather than being baked into the Canvas PNG as well.
- Added regression coverage for multi-source boundaries and Canvas foreground
  isolation.
- Reason: a PPT workflow must preserve attribution when several materials are
  supplied and must not rely on preflight reports that miss an actual rendered
  duplication defect.
- Verification: 26 workflow tests, 6 converter tests, and all 139 checks of
  the mixed-material simulation pass. PowerPoint rendered all six output
  pages without remaining blank output, duplicate text, clipping, source loss,
  or material-layout divergence.

## 2026-08-11 - Workbook Evidence And Resolved Inventory Gate

- Added `.xlsx` material extraction through declared `openpyxl` support. It
  preserves each worksheet's text, headers, row count, numeric columns, and
  formula-cell count; only cached formula results are admitted as numerical
  evidence, and missing caches are an explicit warning.
- Made the preparation gate require a physical `content-inventory.md` with
  resolved core-message, data-point, and page-plan sections. The structured
  state can no longer pass while its cross-session material snapshot still
  contains placeholders.
- Added regression coverage for multi-sheet workbooks, uncalculated formulas,
  cached formula values, and unresolved inventory placeholders.
- Reason: common XLSX source material was rejected, and a simulation showed
  that an otherwise complete state manifest could coexist with a stale,
  placeholder-only inventory document.
- Verification: workflow suite has 25 passing tests and converter suite has 5
  passing tests. A real three-sheet XLSX (Budget, Milestones, Summary) produced
  an evidence-led five-page `corporate-clean` governance brief. It passed 23
  preparation, 27 decision, 73 execution, and 127 combined checks, converted
  through Edge and PowerPoint, and all final HTML/PPT comparisons were reviewed
  without clipping, overlap, blank chart, text loss, or material-layout
  divergence.

## 2026-08-11 - Bounded Web Material Fetch

- Added an HTTP(S)-only URL input path to the material inventory script. It
  enforces a response-size limit and timeout, saves raw HTML beside the task,
  extracts visible text without scripts/styles, and records the original URL.
- Added regression tests for successful HTML extraction and unsafe non-HTTP
  URL rejection.
- Reason: the workflow documented web-material handling but its executable
  inventory accepted only local paths.
- Verification: workflow suite has 22 passing tests. The live IANA Example
  Domains page was fetched, its raw HTML preserved, and its three source-backed
  rules were converted into a three-page `swiss-grid` technical brief. The
  task passed 16 preparation, 27 decision, 43 execution, and final delivery
  checks; all HTML/PPT comparisons were reviewed with no clipping, overlap,
  text loss, or material layout divergence.

## 2026-08-11 - Structured CSV Material Evidence

- Added CSV inventory metadata for table headers, data-row count, and fully
  numeric columns while preserving the supplied raw CSV text.
- Added regression coverage for BOM-safe, quoted CSV parsing and documented
  that data layouts must cite this table evidence.
- Reason: merely treating a CSV as a text file loses the table structure that
  determines whether a chart or data layout is appropriate.
- Verification: workflow suite has 20 passing tests. A distinct CSV-sourced
  four-page budget brief preserved seven rows and the complete numeric column,
  converted a two-page preview before approval, then passed 16 preparation,
  27 decision, 62 execution, and final delivery checks. All final HTML/PPT
  comparisons were reviewed without clipping, overlap, blank chart, text loss,
  or material layout divergence.

## 2026-08-11 - Enforced Design Preview Evidence

- Added a fail-closed decision gate for `preview.html`: it must contain at
  least a cover and representative content slide, identify the previewed slide
  IDs, and record approval notes before full deck expansion can pass.
- Added regression coverage for missing or unapproved preview evidence and
  updated the state template and Codex plugin instructions.
- Reason: the workflow documented a preview-and-approval discipline but its
  validator allowed a deck to skip that user-control point entirely.
- Verification: workflow suite has 19 passing tests. A new five-page,
  PDF-sourced simulation extracted the poster image, converted and reviewed a
  two-page preview before simulated approval, then passed 19 preparation, 27
  decision, 69 execution, and final delivery checks. All five HTML/PPT
  comparisons were reviewed without clipping, overlap, missing assets, or
  material layout divergence.

## 2026-08-11 - PDF Material Extraction And Authoritative Gate Clarification

- Added local, page-indexed PDF text extraction through `pypdf`, including
  extraction of embedded image assets into the task's `extracted-images/`
  directory. A scanned PDF without a text layer now has material available for
  visual review instead of becoming a silent empty source.
- Added PDF extraction regression tests and declared `pypdf` in the workflow
  dependency file.
- Corrected the README to name `check_workflow_state.py` as the authoritative
  gate. The older `check_ppt_execution.py` remains only as an advisory
  diagnostic and now says so in its module documentation.
- Reason: the Codex plugin promised PDF input, while the actual inventory
  rejected it; the README also pointed new users to a weaker historical gate.
- Verification: installed `pypdf 6.15.0`; the supplied one-page poster PDF
  correctly reports its missing text layer and extracts a 3508x4961 PNG to the
  task directory for visual review. The workflow suite has 18 passing tests
  and the converter suite has 5 passing tests.

## 2026-08-10 - Standalone Image Material And Image-Hero Evidence

- Added standalone raster-image registration to `inventory_material.py`, with
  optional dimensions and an explicit requirement for visual review.
- Registered B22 as a source-backed data layout: it requires a real image and
  three quantitative facts, matching the layout library instead of treating it
  as a qualitative page.
- Changed the unconfigured visual-audit default from `ask` to executable
  `triage`. The previous default produced the PPTX and only then reported that
  it should have asked for an audit preference before conversion.
- Reason: a supplied event poster was not represented in the task inventory,
  and therefore could have been ignored during composition.
- Verification: 15 workflow tests and 5 converter tests pass. A four-page
  poster-only simulation passes 19 preparation, 19 decision, and 58 execution
  checks; it converts with the local Edge fallback and all four HTML/PPT
  comparisons were manually reviewed with no clipping, overlap, missing image,
  or material layout divergence.

## 2026-08-10 - Browser Runtime Fallback

- Added a shared browser launcher for HTML measurement and delivery health
  checks. It tries Playwright Chromium first, then an explicitly configured
  `PPT_PLAYWRIGHT_EXECUTABLE`, Microsoft Edge, and Chrome.
- Reason: the workspace had a healthy local Edge but the workflow hard-coded a
  separately downloaded Playwright Chromium, leaving a working renderer unused.
- The converter now also uses bounded page readiness waits instead of
  unbounded `networkidle`, and skips external font resolution when the user
  explicitly requests `--no-embed-fonts`.
- Fixed a conversion audit finding where ECharts initialized inside a hidden
  slide remained blank after the measurement adapter activated it. The adapter
  now emits standard resize/activation signals and resizes registered ECharts
  instances for the active slide.
- Fixed the root layout cause behind that finding: the adapter had reused the
  cover page's `display:flex` for every hidden slide. It now detects and
  restores each slide's own natural display mode before measurement.
- Delivery validation now requires a registered PPTX to exist and its audit to
  cover every slide, rather than accepting a converter health flag alone.
- Verification: the fallback launcher, per-slide display handling, and
  recorded-delivery audit rules have 4 focused tests; the full workflow suite
  has 14 tests. Both the 10-page EV deck and 9-page DOCX event deck completed
  real HTML-to-PPTX conversion with the Edge fallback, PowerPoint rendering,
  and manual HTML/PPT contact-sheet review. The event simulation exposed and
  corrected both a blank hidden ECharts chart and a seven-item timeline wrap.

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
