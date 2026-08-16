# 动态视觉方案与整套质量门禁实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 以前 12 项意图回答和素材为依据生成三种差异化视觉样张，由第 13 项循环确认一个方案，并把所选方案、页面原型和整套质量审查纳入 fail-closed 工作流。

**Architecture:** 在既有 `workflow-state.json` 中引入嵌套模式版本 3 与 `decision.designProfile`。验证器使用文件化样张、文件化节奏审查和文件化方案审查作为证据；HTML 仍是唯一设计源，状态文件只记录可审计的设计约束和审查结果。版本 1、2 的历史状态保持可读，新建任务必须使用版本 3。

**Tech Stack:** Python 3 标准库（`json`、`hashlib`、`re`、`unittest`）、HTML、Markdown、PowerShell。

---

## 文件结构

| 路径 | 职责 |
|---|---|
| `ppt-workflow/scripts/check_workflow_state.py` | 模式版本、意图批次、方案契约、页面原型和审查产物的唯一 fail-closed 验证器。 |
| `ppt-workflow/templates/workflow-state.example.json` | 新任务应复制的版本 3 状态示例。 |
| `ppt-workflow/tests/test_check_workflow_state.py` | 验证器的状态夹具、文件化产物夹具与正负向回归测试。 |
| `codex-plugin/skills/ppt-workflow-intake/SKILL.md` | 前 12 项提问、候选样张生成、修改意见循环和第 13 项确认的操作顺序。 |
| `codex-plugin/skills/ppt-workflow-authoring/SKILL.md` | 将选中的设计方案映射到护照、页面原型和 HTML 属性。 |
| `codex-plugin/skills/ppt-workflow-review/SKILL.md` | 整套节奏审查、方案一致性审查和独立质量评分。 |
| `codex-plugin/skills/ppt-workflow-studio/SKILL.md` | 编排顺序与每个新门禁的调用时机。 |
| `ppt-workflow/SKILL.md` | 面向使用者的四层工作流说明与第 13 项确认时机。 |
| `references/material-driven-questioning.md` | 由素材和前 12 项回答推导三种候选方案的规则。 |
| `references/quick-reference-card.md` | 执行层可快速查阅的方案、原型和质量门禁。 |

## Task 1: 建立版本 3 的意图与设计方案契约

**Files:**
- Modify: `ppt-workflow/scripts/check_workflow_state.py:2-61`
- Modify: `ppt-workflow/scripts/check_workflow_state.py:221-294`
- Modify: `ppt-workflow/tests/test_check_workflow_state.py:14-143`
- Test: `ppt-workflow/tests/test_check_workflow_state.py`

- [ ] **Step 1: 写入版本 3 的失败测试夹具与四批意图测试**

在测试文件新增常量和 `valid_v3_state()`；它保留既有 `valid_state()` 与 `valid_v2_state()`，以覆盖向后兼容。夹具必须生成 `4 + 4 + 4 + 1` 的 13 个回答，其中最后一题 ID 为 `designProfileSelection`。

```python
V3_QUESTIONS = (
    ("audience", 1), ("intent", 1), ("coreClaim", 1), ("canvas", 1),
    ("language", 2), ("expectedOutcome", 2), ("useScene", 2), ("deliveryUse", 2),
    ("storyline", 3), ("contentFocus", 3), ("informationDensity", 3),
    ("designBoldness", 3), ("designProfileSelection", 4),
)

def test_v3_intake_requires_four_batches_and_a_confirmed_design_profile(self):
    task = self.write_task(valid_v3_state())
    for layer in ("intent", "decision"):
        result = self.check(task, layer)
        self.assertEqual(result.returncode, 0, result.stdout)
```

- [ ] **Step 2: 运行新增测试，确认现有验证器会失败**

Run:

```powershell
.\.venv\Scripts\python.exe .\ppt-skills-collection\ppt-workflow\tests\test_check_workflow_state.py WorkflowStateTests.test_v3_intake_requires_four_batches_and_a_confirmed_design_profile -v
```

Expected: `FAIL`，原因是版本 3 尚不在支持的模式集合中。

- [ ] **Step 3: 在验证器中定义版本 3 问题与设计方案字段校验**

在文件顶部新增 `from itertools import combinations`，并在 `INTENT_QUESTIONS_V2` 后新增以下常量；更新 `intent_questions_for_schema()`，仅在 `schema_version == 3` 时返回 V3。将 `check_intent()` 中的模式集合改为 `{1, 2, 3}`，批次计数和顺序从问题元组动态推导，不再硬编码三批。

```python
INTENT_QUESTIONS_V3 = (
    ("audience", 1), ("intent", 1), ("coreClaim", 1), ("canvas", 1),
    ("language", 2), ("expectedOutcome", 2), ("useScene", 2), ("deliveryUse", 2),
    ("storyline", 3), ("contentFocus", 3), ("informationDensity", 3),
    ("designBoldness", 3), ("designProfileSelection", 4),
)
DESIGN_PROFILE_DIMENSIONS = (
    "narrativeStance", "compositionGeometry", "visualTemperature", "typographicLanguage",
)
PAGE_ARCHETYPES = {
    "hero", "context", "evidence", "data", "comparison", "process", "transition",
    "recommendation", "action",
}

def intent_questions_for_schema(schema_version):
    if schema_version == 3:
        return INTENT_QUESTIONS_V3
    return INTENT_QUESTIONS_V2 if schema_version == 2 else INTENT_QUESTIONS_V1
```

把 `expected_by_batch` 改为从 `sorted(set(question_batch.values()))` 生成；错误消息使用
“its required questions in order”，避免把第四批的一题称为“四个问题”。

- [ ] **Step 4: 运行意图测试，确认版本 1、2、3 同时通过**

Run:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s .\ppt-skills-collection\ppt-workflow\tests -p test_check_workflow_state.py -v
```

Expected: 新增 V3 测试通过，既有 V1/V2 意图测试仍通过。

- [ ] **Step 5: 提交模式版本与四批问卷支持**

```powershell
git add ppt-skills-collection/ppt-workflow/scripts/check_workflow_state.py ppt-skills-collection/ppt-workflow/tests/test_check_workflow_state.py
git commit -m "add v3 visual proposal intake schema"
```

## Task 2: 实现动态三方案样张与“都不符合”循环门禁

**Files:**
- Modify: `ppt-workflow/scripts/check_workflow_state.py:294-362`
- Modify: `ppt-workflow/tests/test_check_workflow_state.py:145-205`
- Modify: `ppt-workflow/templates/workflow-state.example.json`
- Test: `ppt-workflow/tests/test_check_workflow_state.py`

- [ ] **Step 1: 为三种候选方案、差异性和修改意见写失败测试**

新增以下测试。测试夹具中的每个 candidate 都包含 `id`、`name`、`rationale`、
`sourceQuestionIds` 与四个 `visualContract` 维度；`write_task()` 要写入
`visual-direction-preview.html`，每个候选对应一个 `data-design-profile` 属性。

```python
def test_v3_rejects_candidates_without_three_distinct_contract_dimensions(self):
    state = valid_v3_state()
    state["decision"]["designProfile"]["candidates"][1]["visualContract"] = \
        copy.deepcopy(state["decision"]["designProfile"]["candidates"][0]["visualContract"])
    result = self.check(self.write_task(state), "decision")
    self.assertEqual(result.returncode, 2)
    self.assertIn("candidate profiles differ in at least three visual dimensions", result.stdout)

def test_v3_revision_request_requires_feedback_and_cannot_pass_decision(self):
    state = valid_v3_state()
    profile = state["decision"]["designProfile"]
    profile.update({"status": "revision-requested", "selectedProfileId": "", "revisionFeedback": ""})
    result = self.check(self.write_task(state), "decision")
    self.assertEqual(result.returncode, 2)
    self.assertIn("revision-requested design profile records creator feedback", result.stdout)
```

- [ ] **Step 2: 运行两个测试，确认现有验证器会失败**

Run:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s .\ppt-skills-collection\ppt-workflow\tests -p test_check_workflow_state.py -v
```

Expected: 两个新增测试失败，因为当前决策层不识别 `designProfile`。

- [ ] **Step 3: 编写 `check_design_profile()` 并绑定到决策门禁**

在 `check_decision()` 前添加函数。它只在版本 3 调用，并使用既有
`task_artifact_path()` 限制预览文件必须位于任务目录。

```python
def check_design_profile(profile, task_dir, v):
    v.require(profile.get("schemaVersion") == 1, "design profile has schema version")
    v.require(profile.get("status") in {"confirmed", "revision-requested"},
              "design profile has a supported status")
    preview_name = v.value(profile, "previewArtifact", "design profile preview artifact is recorded")
    preview_path = task_artifact_path(task_dir, preview_name)
    v.require(preview_path is not None and preview_path.is_file(), "design profile preview artifact exists")
    candidates = profile.get("candidates")
    v.require(isinstance(candidates, list) and len(candidates) == 3,
              "design profile has exactly three candidates")
    ids, contracts = [], []
    for candidate in candidates if isinstance(candidates, list) else []:
        candidate = candidate if isinstance(candidate, dict) else {}
        candidate_id = v.value(candidate, "id", "design profile candidate has an id")
        ids.append(candidate_id)
        v.value(candidate, "name", f"design profile candidate {candidate_id!r} has a name")
        v.value(candidate, "rationale", f"design profile candidate {candidate_id!r} has a rationale")
        v.require(candidate.get("sourceQuestionIds") == [item[0] for item in INTENT_QUESTIONS_V3[:12]],
                  f"design profile candidate {candidate_id!r} cites all first twelve answers")
        contract = candidate.get("visualContract", {})
        contracts.append(contract)
        for dimension in DESIGN_PROFILE_DIMENSIONS:
            v.value(contract, dimension, f"design profile candidate {candidate_id!r} records {dimension}")
    v.require(len(set(ids)) == 3, "design profile candidate ids are unique")
    for left, right in combinations(contracts, 2):
        differences = sum(left.get(key) != right.get(key) for key in DESIGN_PROFILE_DIMENSIONS)
        v.require(differences >= 3, "candidate profiles differ in at least three visual dimensions")
    if profile.get("status") == "revision-requested":
        v.value(profile, "revisionFeedback", "revision-requested design profile records creator feedback")
        return
    v.require(profile.get("selectedProfileId") in set(ids), "confirmed design profile selects a proposed candidate")
    v.value(profile, "creatorConfirmation", "confirmed design profile records creator confirmation")
    v.value(profile, "evidence", "confirmed design profile records creator confirmation evidence")
```

在 `check_decision()` 的 Phase 2 校验之后加入：

```python
if intake.get("schemaVersion") == 3:
    check_design_profile(decision.get("designProfile", {}), task_dir, v)
```

预览 HTML 还必须包含全部三个候选对象 ID 对应的 `data-design-profile` 标记；
`check_design_profile()` 应在 `preview_path` 存在时逐一校验这些标记。

- [ ] **Step 4: 将模板升级为可复制的版本 3 示例**

把 `intentQuestionnaire.schemaVersion` 改为 3，替换为四批 `4 + 4 + 4 + 1` 记录。
新增 `decision.designProfile`，使用三个完整候选对象，且将所选候选的
`id`、`name` 和 `visualContract` 复制到 `decision.passport.designProfile`。示例的
未完成字段只能出现在 `completed: false` 的问卷状态中。

- [ ] **Step 5: 运行全部工作流测试，确认方案门禁通过**

Run:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s .\ppt-skills-collection\ppt-workflow\tests -v
```

Expected: 所有测试通过；候选不够差异、缺样张、未确认选择、以及“都不符合”无意见都返回验证失败。

- [ ] **Step 6: 提交动态方案门禁与模板**

```powershell
git add ppt-skills-collection/ppt-workflow/scripts/check_workflow_state.py ppt-skills-collection/ppt-workflow/tests/test_check_workflow_state.py ppt-skills-collection/ppt-workflow/templates/workflow-state.example.json
git commit -m "validate dynamic visual proposal selection"
```

## Task 3: 增加页面原型、整套节奏与方案一致性审查

**Files:**
- Modify: `ppt-workflow/scripts/check_workflow_state.py:430-602`
- Modify: `ppt-workflow/tests/test_check_workflow_state.py:145-205`
- Test: `ppt-workflow/tests/test_check_workflow_state.py`

- [ ] **Step 1: 添加执行层失败测试与文件化审查夹具**

扩展 `valid_v3_state()` 的 `execution.slides`：每页都有 `archetype` 和 `chapter`；
扩展 HTML，使每个 `.slide` 同时有 `data-archetype`。在 `write_task()` 中写入
`deck-rhythm-review.json` 与 `design-profile-review.json`。

```python
def test_v3_execution_rejects_missing_or_repeated_archetypes(self):
    state = valid_v3_state(page_count=10)
    state["execution"]["slides"][3]["archetype"] = "evidence"
    state["execution"]["slides"][4]["archetype"] = "evidence"
    state["execution"]["slides"][5]["archetype"] = "evidence"
    result = self.check(self.write_task(state), "exec")
    self.assertEqual(result.returncode, 2)
    self.assertIn("deck rhythm has no three consecutive matching archetypes", result.stdout)

def test_v3_execution_requires_current_rhythm_and_design_profile_reviews(self):
    state = valid_v3_state()
    del state["execution"]["deckRhythmReview"]
    result = self.check(self.write_task(state), "exec")
    self.assertEqual(result.returncode, 2)
    self.assertIn("deck rhythm review artifact is recorded", result.stdout)

def test_v3_full_workflow_passes_all_layers(self):
    result = self.check(self.write_task(valid_v3_state()), "all")
    self.assertEqual(result.returncode, 0, result.stdout)
```

- [ ] **Step 2: 运行新增测试，确认其先失败**

Run:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s .\ppt-skills-collection\ppt-workflow\tests -p test_check_workflow_state.py -v
```

Expected: 两项测试失败，因为版本 3 尚未检查页面原型和新审查产物。

- [ ] **Step 3: 增加原型和节奏验证器**

在 `check_execution()` 中的逐页循环内，仅对模式版本 3 强制 `archetype` 与 HTML
属性一致。循环后调用两个新函数；二者复用 `load_json_artifact()`、当前 HTML 的
SHA-256 和 `seen_ids`，不能接受仅写入状态文件、没有独立产物的审查。

```python
def check_deck_rhythm_review(review, task_dir, slides, seen_ids, v):
    v.require(review.get("skill") == "ppt-workflow-review", "deck rhythm review uses the packaged review skill")
    artifact_name = v.value(review, "artifact", "deck rhythm review artifact is recorded")
    artifact = load_json_artifact(task_dir, artifact_name, "deck rhythm review", v)
    v.require(artifact.get("schemaVersion") == 1, "deck rhythm review artifact has schema version")
    v.require(artifact.get("result") in {"pass", "revised"}, "deck rhythm review artifact has a result")
    sequence = artifact.get("archetypeSequence")
    expected = [{"id": item.get("id"), "archetype": item.get("archetype")} for item in slides]
    v.require(sequence == expected, "deck rhythm review matches the execution archetype sequence")
    v.require(all(sequence[index:index + 3] != [sequence[index]] * 3 for index in range(max(0, len(sequence) - 2))),
              "deck rhythm has no three consecutive matching archetypes")
    if len(slides) >= 10:
        archetypes = {item.get("archetype") for item in slides}
        v.require({"hero", "action"}.issubset(archetypes) and bool({"data", "evidence"} & archetypes),
                  "long deck includes hero, evidence or data, and action archetypes")
        v.require("transition" in archetypes, "long deck includes an intentional transition archetype")
```

`check_design_profile_review()` 必须校验：`selectedProfileId` 与
`decision.designProfile.selectedProfileId` 完全相同，`reviewedSlides` 覆盖全部页面，
`htmlSha256` 与当前 `design.html` 一致，`reviewedDimensions` 恰好包含
`typography`、`spacing`、`imageTreatment`、`chartLanguage`、`composition`，并且
`exceptions` 是列表、`notes` 非空。

- [ ] **Step 4: 将已选方案锁入护照并验证不漂移**

在 `check_decision()` 中，模式版本 3 还必须验证：

```python
selected = next(candidate for candidate in decision["designProfile"]["candidates"]
                if candidate["id"] == decision["designProfile"]["selectedProfileId"])
passport_profile = passport.get("designProfile", {})
v.require(passport_profile.get("id") == selected["id"],
          "passport locks the selected design profile id")
v.require(passport_profile.get("visualContract") == selected["visualContract"],
          "passport locks the selected design profile visual contract")
```

`execution.lockedPassport == decision.passport` 的既有规则将自动把这份合同传递到
执行层；无需引入第二个锁定字段。

- [ ] **Step 5: 运行工作流与转换器完整测试**

Run:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s .\ppt-skills-collection\ppt-workflow\tests -v
.\.venv\Scripts\python.exe -m unittest discover -s .\ppt-skills-collection\html-to-pptx\tests -v
```

Expected: 两套测试均通过；仅当 FFmpeg 未安装时，现有视频集成测试可按既有逻辑跳过。

- [ ] **Step 6: 提交整套质量门禁**

```powershell
git add ppt-skills-collection/ppt-workflow/scripts/check_workflow_state.py ppt-skills-collection/ppt-workflow/tests/test_check_workflow_state.py
git commit -m "add deck rhythm and design profile reviews"
```

## Task 4: 同步技能说明与参考资料

**Files:**
- Modify: `codex-plugin/skills/ppt-workflow-intake/SKILL.md`
- Modify: `codex-plugin/skills/ppt-workflow-authoring/SKILL.md`
- Modify: `codex-plugin/skills/ppt-workflow-review/SKILL.md`
- Modify: `codex-plugin/skills/ppt-workflow-studio/SKILL.md`
- Modify: `ppt-workflow/SKILL.md`
- Modify: `references/material-driven-questioning.md`
- Modify: `references/quick-reference-card.md`

- [ ] **Step 1: 更新 intake 与 studio 的编排说明**

明确写入以下不可跳过顺序：先完成前三批共 12 项；读取素材盘点和回答，生成三种
候选样张；让制作者在第 13 项选一个或选择“都不符合”；若选择“都不符合”，收集
修改意见并重生三种候选，保持 `intentQuestionnaire.completed: false`；只有确认后
才写 `decision.designProfile` 并运行意图门禁。

- [ ] **Step 2: 更新 authoring 与 review 的可执行约束**

authoring 说明必须要求将所选候选的完整 `visualContract` 写入护照、每页登记
`archetype` 和 HTML `data-archetype`。review 说明必须给出 `deck-rhythm-review.json`
与 `design-profile-review.json` 的最小 JSON 示例，并要求审查五个维度：字体、留白、
图片处理、图表语言、构图。

- [ ] **Step 3: 更新主工作流与两份参考资料**

主工作流不再列举固定视觉方向；材料驱动提问参考明确三种候选必须在四个设计维度
中的至少三项不同；速查卡新增“12 项后生成样张、第 13 项确认、未确认即停止”的
门禁和九种页面原型表。

- [ ] **Step 4: 用全文搜索验证没有保留过期规则**

Run:

```powershell
rg -n "12 项.*3 批|每批.*4 问|referenceStyle.*确认|consulting.*editorial.*impact" .\ppt-skills-collection
```

Expected: 搜索结果只允许出现在历史兼容说明或“禁止固定枚举”的文字中；不能出现在
新任务操作步骤、模板或速查卡的要求中。

- [ ] **Step 5: 提交文档与技能同步**

```powershell
git add ppt-skills-collection/codex-plugin/skills ppt-skills-collection/ppt-workflow/SKILL.md ppt-skills-collection/references
git commit -m "document dynamic visual proposal workflow"
```

## Task 5: 端到端验证与交付检查

**Files:**
- Modify: `ppt-workflow/tests/test_check_workflow_state.py`（仅在前四项测试暴露夹具遗漏时）
- Verify: `ppt-workflow/scripts/check_workflow_state.py`
- Verify: `html-to-pptx/tests/`

- [ ] **Step 1: 使用版本 3 完整夹具运行所有层级验证**

Run:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s .\ppt-skills-collection\ppt-workflow\tests -v
.\.venv\Scripts\python.exe -m unittest discover -s .\ppt-skills-collection\html-to-pptx\tests -v
```

Expected: 工作流测试全部通过；转换器测试全部通过，或仅保留明确标注为 FFmpeg 不可用的跳过项。

- [ ] **Step 2: 对版本 3 夹具执行命令行全门禁**

运行刚新增的端到端测试；它通过临时任务目录调用 `--layer all`，不依赖未跟踪的
工作区文件。

```powershell
.\.venv\Scripts\python.exe .\ppt-skills-collection\ppt-workflow\tests\test_check_workflow_state.py WorkflowStateTests.test_v3_full_workflow_passes_all_layers -v
```

Expected: 进程退出码 `0`，测试断言的验证器输出不含 `[FAIL]`，并覆盖 prep、intent、decision、exec、deliver。

- [ ] **Step 3: 审查提交范围与封包完整性**

Run:

```powershell
git diff --check HEAD~4..HEAD
git ls-files | Where-Object { $_ -notmatch '^ppt-skills-collection/' }
git status --short
```

Expected: 差异检查无空白错误；第二条没有输出；状态中不出现要提交的报告、PPT、运行目录或 `.config.local.toml`。

- [ ] **Step 4: 提交最终验证修复（仅在有修复时）**

```powershell
git add ppt-skills-collection
git commit -m "verify dynamic visual proposal workflow"
```

若本任务没有产生修复，不创建空提交。
