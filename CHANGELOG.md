# Workflow Change Log

## 2026-08-15 - Intent Continuity Quality Loop

- Added V3 `intent-continuity-review.json` to bind confirmed intent, approved
  preview, final HTML, and delivery evidence in one file-backed review.
- The execution and delivery gates now reject stale preview/HTML hashes,
  missing page coverage, or an unapproved intent-to-preview-to-execution chain.

## 2026-08-15 - Precision Intent Bindings

- Added V3 `decision.intentBindings` so creator answers explicitly constrain
  content, composition, and delivery instead of remaining as free-form notes.
- Added required must-include, must-avoid, visual-avoid, and delivery-support
  boundaries, with fail-closed checks for answer drift and malformed intake data.
- Updated the intake skill, material-driven questioning reference, quick card,
  and workflow template with executable boundary examples.

## 2026-08-15 - V3 Delivery Evidence Gate

- Completed the V3 regression-hardening contract by requiring file-backed
  proof of zero unresolved high-risk preflight pages and zero structural
  self-check warnings before PPTX delivery.
- Kept V1/V2 delivery records backward compatible; the stricter evidence is
  required only for V3 tasks.
- Verification: 86 workflow tests and 23 converter tests pass; the two
  FFmpeg-dependent media integration tests are skipped when FFmpeg is absent.

## 2026-08-11 - Explicit Background Strategy

- Replaced the unconditional “no three consecutive slides share a background mode” rule with a locked passport choice: `uniform` or `rhythmic`, plus `primaryBackgroundMode`.
- A `uniform` deck now fails execution if any page switches from the approved deep/light background mode. The old alternation checks run only for `rhythmic` decks.
- Reason: forcing background variation introduced shallow pages into a dark-led recruitment deck and made visual consistency worse.

## 2026-08-11 - Perceived Color Continuity Gate

- Added a post-build `ppt-workflow-review` color-continuity review. It requires native-size sequence inspection of each light/dark color system, including base color, visual temperature, and dominant surface treatment.
- Added `execution.colorContinuityReview`, a file-backed `color-continuity-review.json` artifact, `data-color-system` bindings, and execution-gate validation tied to the exact reviewed HTML hash.
- Reason: a deck can use the same literal CSS background on two slides yet feel inconsistent when warm images or large callouts overpower one page's surface system.

## 2026-08-11 - Fail-Closed Creator Intent Intake

- Added the `ppt-workflow-intake` Codex skill. It collects all 12 intent questions in three batches and waits for the creator's response after each batch.
- Added file-backed `decision.intentQuestionnaire` validation. Every required answer must be unique, in its prescribed batch, non-empty, explicitly `creator-confirmed`, and linked to creator-response evidence; each of the three batches requires its own confirmation record.
- Added the `intent` validation layer and made the decision, execution, and delivery gates repeat it. A preview, deck expansion, or conversion cannot pass based on model-inferred intent.
- Replaced the historical skip rule with confirmation-only handling: even a value already stated by the creator or suggested by material is asked and recorded in its assigned batch.
- Reason: an earlier document-driven run skipped the documented intake and allowed the model to infer creator choices from supplied material.

## 2026-08-11 - Installed Plugin Forward Test And Legacy Console Compatibility

- Ran a fresh, ephemeral Codex session against the installed
  `ppt-workflow-studio@personal` plugin. It discovered and used the root
  workflow plus all four packaged companion skills (`review`, `authoring`,
  `effects`, and `delivery`) to produce a three-slide municipal rain-garden
  decision deck from supplied inline material only.
- Independently reran the authoritative workflow-state gate against the
  produced artifacts: 131 checks passed, with the source HTML and audited PPTX
  hashes matching the manifest. The actual 16:9 PPTX contains three slides and
  50 native text runs; HTML/PPT render comparisons showed no clipping, blank
  content, or material layout drift.
- Fixed the historical diagnostic checker for Windows GBK consoles. Its Unicode
  status glyphs previously raised `UnicodeEncodeError`, even though it is not an
  authoritative delivery gate. It now configures standard streams as UTF-8 and
  has a subprocess regression test that forces `PYTHONIOENCODING=gbk`.

## 2026-08-11 - Review Hash Binding And A4 Print Evidence

- Bound source and delivery review to the actual artifacts. A source review now
  records SHA-256 for the reviewed HTML and a delivery audit records SHA-256
  for the audited PPTX; the workflow gate recomputes both hashes and fails if
  either artifact changes after its review.
- Added regressions for HTML changed after source review and PPTX changed after
  delivery audit. This closes the prior gap where a manifest could retain a
  passing review while its reviewed artifact had been replaced.
- Independently exercised an A4 (1240x1754) two-page, print-first field guide.
  It used B22 for a source-poster-plus-three-qualified-figures page and B11 for
  the participation route. The gate caught the original three-node B11 misuse;
  the revised four-node, source-backed route passed after a fresh source review.
- Verification: 35 workflow tests and 12 converter tests pass. The A4 task
  passed 113 structured checks, rendered at native 1240x1754 in HTML and
  PowerPoint, produced a 7874000x11137900 EMU PPTX, and passed both native
  visual comparisons without structural warnings or interactive effects.

## 2026-08-11 - Codex Companion Skills And File-Backed Execution Evidence

- Packaged four independently discoverable Codex companion skills:
  `ppt-workflow-review`, `ppt-workflow-authoring`, `ppt-workflow-effects`,
  and `ppt-workflow-delivery`. The root studio skill now directs each critical
  stage to an explicit procedure instead of relying on legacy, unregistered
  `Skill(...)` names.
- Replaced self-attested anti-template and visual-effect decisions with
  fail-closed JSON evidence. `anti-template-review.json` must record review of
  intent, evidence, theme, typography, and layout; `effects-scan.json` must
  cover each slide exactly once and agree with the manifest's effect status,
  reason, and type.
- Made one-page deliveries legitimate: preview requirements now use the
  smaller of two pages and the planned deck length, retaining explicit creator
  approval without inventing a second page for a WeChat header or single A4
  poster.
- Required `data-pptx-slide` on every slide container. This replaces fragile
  geometric discovery for small or ultra-wide canvases, which otherwise can
  silently measure zero pages.
- Verification: 33 workflow tests and 12 converter tests pass. A fresh,
  single-page `wechat` (900x383) image-led header passed all 87 workflow gates,
  measured and rendered at native size, produced a 5715000x2432050 EMU PPTX,
  and passed manual HTML/PowerPoint visual comparison with zero structural
  warnings.

## 2026-08-11 - 3:4 Xiaohongshu Image-Led Delivery Evidence

- Independently exercised the previously untested 1242x1660 Xiaohongshu
  canvas with a three-card, Chinese-language, image-led creator brief. The
  run used the `xiaohongshu-white` theme and B22/C4/C9 layouts, including an
  intentional dark process card.
- Preserved the supplied poster as visible source evidence and retained the
  qualified `60+` / `30+` claims without turning them into exact attendance,
  registration, ticketing, or sponsor assertions.
- Verification: every HTML reference screenshot and PowerPoint render measured
  1242x1660; the PPTX page size was 7886700x10541000 EMU; PowerPoint
  self-check reported zero structural warnings; all three side-by-side native
  comparisons passed visual review. The task passed all 102 structured
  workflow-state checks after recording source and delivery review evidence.

## 2026-08-11 - Native Portrait Audit Evidence And Source-Review Gate

- Fixed portrait HTML audit screenshots being clipped to the initial 1920x1080 browser viewport even when the generated PPTX canvas was correct. `measure.py` now sizes the viewport to each activated slide's natural dimensions before capturing reference screenshots and raster media, then reasserts the adapter position after resize listeners run.
- Added a Playwright regression test for a responsive 1080x1920 deck with a full-slide Canvas. It verifies measured dimensions, reference screenshots, and Canvas screenshots are all native portrait size.
- Added a fail-closed `execution.sourceVisualReview` requirement to the workflow-state gate. It must include a pass/revised result, every slide exactly once, and notes, because HTML/PPT comparison validates conversion fidelity but cannot detect a source layout problem shared by both sides.
- Clarified root-relative reference-library paths in `ppt-workflow/SKILL.md` and corrected the quick-reference Canvas guidance to use the activated slide's native dimensions.
- Evidence: the four-page Story/9:16 Library Night simulation renders all HTML and PowerPoint pages at 1080x1920 with a 6858000x12192000 EMU PPTX canvas; the full-screen Canvas and ECharts cases were visually reviewed after source-layout revision.

This log records every workflow change made after the copied collection was
baselined in `D:\GPTworkspace`. Each entry names the affected files, reason,
and verification so a change can be reverted with Git.

## 2026-08-11 - Native Non-16:9 Canvas Delivery

- Fixed the converter's 16:9-only assumptions. The adapter now preserves a
  target slide's natural dimensions; resize listeners cannot reapply a parent
  transform before measurement. The assembler derives PowerPoint page size
  from measured CSS pixels and fails closed when one deck mixes canvases.
- PowerPoint and LibreOffice rendering now derive output PNG dimensions from
  `ppt/presentation.xml`, full-slide picture detection uses the actual page
  dimensions, and visual comparison images preserve each input's native size
  instead of stretching both sides to 1920x1080.
- Added regressions for an explicit 4:3 page, a responsive resize handler,
  4:3 PPTX `sldSz`, mixed-canvas rejection, and non-stretched audit panels.
- Reason: a full HTML-first 4:3 classroom-brief simulation initially rendered
  as a 16:9 PPTX, while the old audit compositor concealed the specification
  violation by stretching its comparison images.
- Verification: the repaired simulation measured four 1440x1080 pages,
  created a 9144000x6858000 EMU PPTX, rendered all four pages through
  PowerPoint at 1440x1080, passed all three structured workflow layers, and
  completed a page-by-page visual audit without clipping, overlap, blank
  output, text loss, or remaining ratio distortion.

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
