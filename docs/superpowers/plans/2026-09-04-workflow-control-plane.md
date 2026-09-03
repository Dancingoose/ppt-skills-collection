# PPT Workflow Control Plane Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task with verification checkpoints.

**Goal:** Add a command-driven, hash-checked workflow controller around the existing PPT gates without changing the existing gate or converter contracts.

**Architecture:** `workflow_ctl.py` is the CLI boundary and `workflow_control.py` owns pure state, hash, event-chain, and transition logic. The CLI invokes `check_workflow_state.py` as a subprocess and records every command as an append-only JSONL event. PowerShell bootstrap/test scripts close the local dependency and test-entry gap; existing scripts remain directly usable.

**Tech Stack:** Python 3.10+, standard library (`argparse`, `hashlib`, `json`, `subprocess`, `uuid`, `datetime`, `pathlib`), PowerShell, Python `unittest`, GitHub Actions on Windows.

**Spec:** `docs/superpowers/specs/2026-09-04-workflow-control-plane-design.md`

## Global Constraints

- Preserve `workflow-state.json.schemaVersion == 1` and all existing validator behavior.
- Never write outside the resolved task directory from controller commands.
- Never silently install dependencies, fonts, or assets; installation requires `-Install`.
- `advance` is sequential and fail-closed; `seal` requires a successful `deliver` gate.
- Event records are append-only and chained by SHA-256.
- Use UTF-8 JSON, sorted keys, and compact separators for canonical hashes.

---

### Task 1: Add Dependency Bootstrap and Test Entry

**Files:**
- Create: `ppt-workflow/scripts/bootstrap.ps1`
- Create: `scripts/run-tests.ps1`
- Create: `.github/workflows/quality.yml`
- Test: `ppt-workflow/tests/test_tooling_scripts.py`

**Interfaces:**
- `bootstrap.ps1 [-Install] [-Python <path>]` checks imports for `pypdf`, `openpyxl`, `defusedxml`, `pptx`, `lxml`, `fontTools`, `playwright`, and `PIL`; with `-Install` it runs `python -m pip install -r ppt-workflow/requirements.txt -r html-to-pptx/requirements.txt`.
- `run-tests.ps1 [-Python <path>]` runs both test trees with `python -m unittest discover`, exits non-zero before tests if a required import is missing, and prints the missing package names and install command.
- GitHub Actions invokes `bootstrap.ps1`, then `run-tests.ps1` on `windows-latest` with Python 3.12.

- [ ] **Step 1: Write failing script behavior tests**

Add subprocess tests that create a temporary fake Python executable or call the scripts with an environment flag, then assert missing dependency output contains the package name and the exit code is non-zero.

- [ ] **Step 2: Run the tooling tests**

Run: `& .\\venv\\Scripts\\python.exe -m unittest ppt-workflow.tests.test_tooling_scripts -v`

Expected: FAIL because the scripts do not exist.

- [ ] **Step 3: Implement bootstrap and test runner**

Keep dependency mapping in one PowerShell hashtable. Use `Get-Command`/`& $Python -c` for import checks. Do not use `pip` directly; use the selected interpreter's `-m pip`.

- [ ] **Step 4: Add CI workflow**

Install requirements through `bootstrap.ps1 -Install`, run `run-tests.ps1`, and publish the command output as the job log. Do not add a second test framework.

- [ ] **Step 5: Run the tooling tests and syntax checks**

Run: `& .\\venv\\Scripts\\python.exe -m unittest ppt-workflow.tests.test_tooling_scripts -v`

Expected: PASS for script contract tests. Run `Get-Content .github/workflows/quality.yml` to confirm the workflow uses the same scripts.

### Task 2: Implement Pure Workflow State and Event Logic

**Files:**
- Create: `ppt-workflow/scripts/workflow_control.py`
- Test: `ppt-workflow/tests/test_workflow_control.py`

**Interfaces:**
- `LAYERS = ("prep", "intent", "design", "decision", "exec", "deliver")`
- `canonical_json(value: object, exclude_paths: set[tuple[str, ...]] = set()) -> bytes`
- `sha256_bytes(data: bytes) -> str`
- `state_digest(state: dict) -> str`
- `event_digest(event: dict) -> str`
- `read_event_chain(path: Path) -> tuple[list[dict], str]`
- `append_event(path: Path, event: dict) -> str`
- `next_layer(current_layer: str, target_layer: str) -> bool`
- `artifact_hashes(task_dir: Path, state: dict) -> dict[str, str]`
- `control_status(task_dir: Path, state: dict) -> str`

- [ ] **Step 1: Write failing unit tests**

Cover sorted canonical JSON, exclusion of `control.stateSha256` and `control.eventHeadSha256`, deterministic event hashes, valid chain construction, tamper detection, truncation detection, legal adjacent transitions, and rejection of jumps/backward transitions.

- [ ] **Step 2: Run the focused tests**

Run: `& .\\venv\\Scripts\\python.exe -m unittest ppt-workflow.tests.test_workflow_control -v`

Expected: FAIL with missing module or missing functions.

- [ ] **Step 3: Implement canonical hashing and event-chain validation**

Validate every JSONL line is an object with `schemaVersion == 1`, a 64-character `eventSha256`, and a `previousEventSha256` matching the previous line. Recompute each event hash after removing only `eventSha256`.

- [ ] **Step 4: Implement state drift detection**

Load `workflow-state.json`, compute the digest with the two self-reference fields excluded, compare it with `control.stateSha256`, and compare the log head with `control.eventHeadSha256`. Return `legacy-unmanaged` when control metadata or the log is absent.

- [ ] **Step 5: Run focused tests**

Expected: PASS for all pure logic tests.

### Task 3: Implement the Workflow Controller CLI

**Files:**
- Create: `ppt-workflow/scripts/workflow_ctl.py`
- Modify: `ppt-workflow/templates/workflow-state.example.json`
- Test: `ppt-workflow/tests/test_workflow_ctl.py`

**Interfaces:**
- `main(argv: list[str] | None = None) -> int`
- Commands: `init`, `status`, `verify`, `advance`, `seal`, `log`.
- `run_gate(task_dir: Path, layer: str) -> GateResult` invokes `check_workflow_state.py --task <task_dir> --layer <layer>` and parses `[PASS]`, `[FAIL]`, and `Summary:` lines.

- [ ] **Step 1: Write failing CLI tests**

Use temporary task directories and a fake gate executable injected through a `--gate-script` test-only option or a patched subprocess call. Assert `init` copies the template without overwriting, `status` reports `legacy-unmanaged` for old tasks, `advance` rejects jumps and failed gates, and `seal` rejects non-deliver states.

- [ ] **Step 2: Run focused CLI tests**

Run: `& .\\venv\\Scripts\\python.exe -m unittest ppt-workflow.tests.test_workflow_ctl -v`

Expected: FAIL because the controller does not exist.

- [ ] **Step 3: Implement safe task/path handling**

Resolve the task path, reject a file as a task directory, and use `task_artifact_path`-style containment checks for every state/template/log path. `init` creates the directory only when absent, copies the example template, adds the `control` object, and creates an empty event log.

- [ ] **Step 4: Implement `verify` and event recording**

Run the existing validator, leave `currentLayer` unchanged, set `status` to `active` or `blocked`, update state and event hashes, and append a `verify` event even when the gate fails.

- [ ] **Step 5: Implement `advance`**

Require the target to be exactly the next layer. Run the previous layer gate first; on success update `currentLayer` to the target, set `status` to `active`, recompute state hash, and append an `advance` event. On failure leave the layer unchanged and return the gate's non-zero result.

- [ ] **Step 6: Implement `status`, `log`, and `seal`**

`status` validates the state and event chain and prints `active`, `blocked`, `sealed`, `drifted`, or `legacy-unmanaged`. `log` prints parsed events in order. `seal` requires `currentLayer == deliver` and a passing deliver gate, writes `sealedAt`, sets `status` to `sealed`, and records a `seal` event.

- [ ] **Step 7: Run focused CLI tests**

Expected: PASS, including no mutation after failed `advance` and drift detection after changing a tracked artifact.

### Task 4: Add End-to-End Regression Coverage and Documentation

**Files:**
- Modify: `README.md`
- Modify: `ppt-workflow/SKILL.md`
- Create: `ppt-workflow/tests/test_workflow_ctl_integration.py`

- [ ] **Step 1: Write integration tests**

Create a minimal task from the example template, stub the gate subprocess to return pass/fail for each layer, execute `init -> verify prep -> advance intent`, then assert the state, log head, and event chain. Modify `workflow-state.json` and assert `status` returns non-zero with `drifted`.

- [ ] **Step 2: Run the integration tests**

Run: `& .\\venv\\Scripts\\python.exe -m unittest ppt-workflow.tests.test_workflow_ctl_integration -v`

Expected: FAIL until the controller and template contract are fully connected.

- [ ] **Step 3: Document the managed workflow**

Add a concise command sequence to `README.md`. In `ppt-workflow/SKILL.md`, state that new tasks should use `workflow_ctl.py`, while direct gate scripts remain supported for legacy tasks and diagnostics.

- [ ] **Step 4: Run the complete test entry**

Run: `powershell -ExecutionPolicy Bypass -File scripts/run-tests.ps1`

Expected: With requirements installed, both test trees complete successfully; without requirements, the script exits before test discovery and names each missing import.

### Task 5: Final Verification and Commit

**Files:**
- Modify only files listed in Tasks 1-4.

- [ ] **Step 1: Run static checks**

Run: `& .\\venv\\Scripts\\python.exe -m compileall ppt-workflow\\scripts`

Expected: exit code 0.

- [ ] **Step 2: Run all unit and integration tests**

Run: `powershell -ExecutionPolicy Bypass -File scripts/run-tests.ps1`

Expected: all available tests pass; conditional FFmpeg tests may be skipped only with an explicit skip report.

- [ ] **Step 3: Exercise the CLI manually in a temporary task**

Run: `& .\\venv\\Scripts\\python.exe ppt-workflow\\scripts\\workflow_ctl.py init --task $env:TEMP\\ppt-workflow-control-smoke --name smoke --format html`

Then run `status`, `log`, and an expected-blocking `advance --to intent`; confirm no source repository files are modified.

- [ ] **Step 4: Review the diff and commit**

Run: `git diff --check; git status --short`

Commit only the controller, scripts, template/docs, CI, and tests introduced by this plan with message: `feat: add workflow control plane`.
