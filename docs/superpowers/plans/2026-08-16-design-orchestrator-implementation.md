# PPT 设计编排器实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**目标：** 将五个设计 skill 接入为固定的设计编排阶段，并以三套设计配方、五项专属产物和哈希交接作为失败关闭门禁。

**架构：** `ppt-workflow-studio` 在前 12 项意图确认后依次编排设计方向、研究、故事线、设计审查和样张渲染。`design-orchestration.json` 绑定这些产物，`workflow-state.json` 保存三套摘要配方；验证器在 decision 与 exec 层重复校验，阻止任何一个设计视角被跳过。

**技术栈：** Codex 插件 skill Markdown/YAML、Python 标准库验证器、JSON 任务契约、`unittest`。

---

### 任务 1：为设计编排门禁建立失败测试

**文件：**

- 修改：`ppt-workflow/tests/test_check_workflow_state.py:174-1285`
- 新建：`ppt-workflow/tests/test_plugin_design_orchestrator.py`

- [ ] **步骤 1：在 `valid_v3_state()` 中加入期望的设计编排摘要和工件生成辅助函数**

新增 `valid_design_orchestration()`，返回三套候选、五个产物记录和每个文件的
SHA-256；在 `write_task()` 中写入这些 Markdown、HTML 和 JSON 文件。每套候选
至少包含 `id`、`theme`、`narrativeStance`、`compositionGeometry`、
`visualTemperature`、`typographicLanguage`、`informationStructure`、
`signature`、`sourceLenses` 和 `sampleSlideIds`。

```python
DESIGN_ARTIFACTS = {
    "claude-design": "design-directions.md",
    "ui-ux-pro-max": "design-research.md",
    "mbb-decks": "ghost-deck.md",
    "frontend-design": "frontend-design-review.md",
    "axi-front-design": "visual-direction-preview.html",
}

def valid_design_orchestration():
    return {
        "schemaVersion": 1,
        "artifacts": [{"skill": skill, "file": filename, "sha256": ""}
                      for skill, filename in DESIGN_ARTIFACTS.items()],
        "recipes": [
            {"id": "evidence", "theme": "swiss-grid", "narrativeStance": "evidence",
             "compositionGeometry": "grid", "visualTemperature": "cool",
             "typographicLanguage": "grotesk", "informationStructure": "argument",
             "signature": "evidence rail", "sourceLenses": ["claude-design", "mbb-decks"],
             "sampleSlideIds": [1, 2]},
            {"id": "editorial", "theme": "editorial-serif", "narrativeStance": "opinion",
             "compositionGeometry": "asymmetric-columns", "visualTemperature": "warm",
             "typographicLanguage": "editorial-serif", "informationStructure": "feature-story",
             "signature": "pull quote", "sourceLenses": ["claude-design", "frontend-design"],
             "sampleSlideIds": [3, 4]},
            {"id": "momentum", "theme": "aurora", "narrativeStance": "future-state",
             "compositionGeometry": "full-bleed-sequence", "visualTemperature": "neutral",
             "typographicLanguage": "display-sans", "informationStructure": "journey",
             "signature": "motion horizon", "sourceLenses": ["ui-ux-pro-max", "axi-front-design"],
             "sampleSlideIds": [5, 6]},
        ],
    }
```

- [ ] **步骤 2：添加四个 decision 层失败测试并验证它们目前失败**

加入下列测试，均通过 `self.check(task, "decision")` 断言退出码为 `2` 并检查
清晰的失败文字：

```python
def test_v3_decision_requires_all_design_orchestration_artifacts(self):
    state = valid_v3_state()
    state["decision"]["designOrchestration"]["artifacts"].pop()
    result = self.check(self.write_task(state), "decision")
    self.assertEqual(result.returncode, 2)
    self.assertIn("design orchestration records every required skill artifact", result.stdout)

def test_v3_decision_rejects_recipe_pair_with_fewer_than_three_distinct_axes(self):
    state = valid_v3_state()
    state["decision"]["designRecipes"][1].update(state["decision"]["designRecipes"][0])
    result = self.check(self.write_task(state), "decision")
    self.assertEqual(result.returncode, 2)
    self.assertIn("design recipes differ across at least three design axes", result.stdout)

def test_v3_decision_rejects_untranslated_uiux_research(self):
    state = valid_v3_state()
    state["decision"]["designRecipes"][0]["adoptedConstraints"] = []
    result = self.check(self.write_task(state), "decision")
    self.assertEqual(result.returncode, 2)
    self.assertIn("design recipe translates ui-ux-pro-max research", result.stdout)

def test_v3_decision_rejects_stale_visual_direction_preview_hash(self):
    task = self.write_task(valid_v3_state())
    (task / "visual-direction-preview.html").write_text("changed", encoding="utf-8")
    result = self.check(task, "decision")
    self.assertEqual(result.returncode, 2)
    self.assertIn("design orchestration preview hash matches the current file", result.stdout)
```

运行：

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
python -m unittest discover -s ppt-workflow/tests -p test_check_workflow_state.py -v
```

预期：测试因尚未实现 `design-orchestration` 验证而失败，且失败原因是门禁未拒绝无效状态。

- [ ] **步骤 3：添加 exec 层持续性失败测试并验证它当前失败**

加入两项测试，先通过 decision，再在执行前替换 `design.html` 或
`visual-direction-preview.html`，断言 exec 层拒绝旧的编排哈希：

```python
def test_v3_execution_rejects_design_html_changed_after_orchestration(self):
    task = self.write_task(valid_v3_state())
    (task / "design.html").write_text("<div class='slide'>changed</div>", encoding="utf-8")
    result = self.check(task, "exec")
    self.assertEqual(result.returncode, 2)
    self.assertIn("design orchestration execution hash matches the current HTML", result.stdout)

def test_v3_execution_rejects_preview_changed_after_orchestration(self):
    task = self.write_task(valid_v3_state())
    (task / "visual-direction-preview.html").write_text("changed", encoding="utf-8")
    result = self.check(task, "exec")
    self.assertEqual(result.returncode, 2)
    self.assertIn("design orchestration preview hash matches the current file", result.stdout)
```

运行：

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
python -m unittest discover -s ppt-workflow/tests -p test_check_workflow_state.py -v
```

预期：测试失败，因为执行门禁尚未验证设计编排哈希。

- [ ] **步骤 4：建立插件结构失败测试并验证它当前失败**

新测试只读取仓库文件，不依赖临时任务目录。它要求五个 bridge 目录均存在、
具有 `SKILL.md` 与 `agents/openai.yaml`，且根 skill 按固定顺序出现五个名称。

```python
class PluginDesignOrchestratorTests(unittest.TestCase):
    expected = ("claude-design", "ui-ux-pro-max", "mbb-decks",
                "frontend-design", "axi-front-design")

    def test_plugin_exposes_all_design_bridges(self):
        for skill in self.expected:
            self.assertTrue((SKILLS / skill / "SKILL.md").is_file())
            self.assertTrue((SKILLS / skill / "agents" / "openai.yaml").is_file())

    def test_studio_orders_every_design_bridge_before_samples(self):
        text = STUDIO.read_text(encoding="utf-8")
        positions = [text.index(name) for name in self.expected]
        self.assertEqual(positions, sorted(positions))
        self.assertLess(positions[-1], text.index("visual-direction-preview.html"))
```

运行：

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
python -m unittest discover -s ppt-workflow/tests -p test_plugin_design_orchestrator.py -v
```

预期：五个 bridge 尚不存在，测试失败。

### 任务 2：实现设计配方契约与失败关闭验证器

**文件：**

- 修改：`ppt-workflow/scripts/check_workflow_state.py:136-730`
- 修改：`ppt-workflow/templates/workflow-state.example.json`
- 修改：`ppt-workflow/tests/test_check_workflow_state.py`

- [ ] **步骤 1：实现 `check_design_orchestration()`**

在 `check_design_profile()` 之后新增函数，接收 `state`、`task_dir`、
`html_path` 和 `Validator`。只对 V3 intake 执行。它应：

1. 读取 `decision.designOrchestration` 与 `design-orchestration.json`；
2. 要求恰有五条 `{skill, file, sha256}` 记录，skill 集合与
   `DESIGN_ORCHESTRATION_SKILLS` 完全一致；
3. 要求每个文件存在，重新计算 SHA-256，并与 JSON 和 manifest 摘要一致；
4. 要求三套 recipe 在 JSON 与 `decision.designRecipes` 完全一致；
5. 验证 recipe 的必填字段、至少两个 `sourceLenses`、主题/结构/签名；
6. 对三对 recipe 计算八个设计轴的不同项，要求每对至少三个；
7. 验证 `design-directions.md`、`design-research.md`、`ghost-deck.md`、
   `frontend-design-review.md` 和样张 HTML 均包含三个 recipe ID；
8. 验证样张 HTML 带三条 `data-design-recipe` 标记，并记录其哈希。

```python
DESIGN_ORCHESTRATION_SKILLS = (
    "claude-design", "ui-ux-pro-max", "mbb-decks",
    "frontend-design", "axi-front-design",
)
DESIGN_AXES = (
    "narrativeStance", "compositionGeometry", "visualTemperature",
    "typographicLanguage", "informationStructure", "imageTreatment",
    "chartLanguage", "motionStrategy",
)

def distinct_axis_count(left, right):
    return sum(left.get(axis) != right.get(axis) for axis in DESIGN_AXES)
```

- [ ] **步骤 2：把验证器接入 decision 与 exec 层**

在 `check_decision()` 中，在 `check_design_profile()` 成功后调用新函数，阻止
未完成三方案编排的第 13 项确认。在 `check_execution()` 中重用其结果，并新增
检查：`design.html` SHA-256、样张 SHA-256、选中 recipe ID 必须与
`execution.intentContinuityReview` 和 `designProfileReview` 一致。

```python
orchestration = check_design_orchestration(state, task_dir, v)
if orchestration:
    v.require(orchestration["selectedRecipeId"] == selected_profile_id,
              "selected design recipe matches the confirmed design profile")
```

- [ ] **步骤 3：扩展状态模板为有效 V3 示例**

在 `decision` 下新增 `designOrchestration` 和 `designRecipes`。用完整、非占
位的三套配方示例展示五个产物、哈希字段、八个设计轴、`sourceLenses`、样张
页面与选定配方。模板中将 `visual-direction-preview.html` 标为样张产物，避免
把它误作 `preview.html`。

- [ ] **步骤 4：运行新增测试并验证变绿**

运行：

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
python -m unittest discover -s ppt-workflow/tests -p test_check_workflow_state.py -v
```

预期：新增无效状态被拒绝，新增有效 V3 状态通过；如果环境允许临时目录和
`openpyxl`，整套 workflow state 单测通过。

### 任务 3：添加五个桥接 skill 并将它们编排到插件工作流

**文件：**

- 新建：`codex-plugin/skills/claude-design/SKILL.md`
- 新建：`codex-plugin/skills/claude-design/agents/openai.yaml`
- 新建：`codex-plugin/skills/ui-ux-pro-max/SKILL.md`
- 新建：`codex-plugin/skills/ui-ux-pro-max/agents/openai.yaml`
- 新建：`codex-plugin/skills/mbb-decks/SKILL.md`
- 新建：`codex-plugin/skills/mbb-decks/agents/openai.yaml`
- 新建：`codex-plugin/skills/frontend-design/SKILL.md`
- 新建：`codex-plugin/skills/frontend-design/agents/openai.yaml`
- 新建：`codex-plugin/skills/axi-front-design/SKILL.md`
- 新建：`codex-plugin/skills/axi-front-design/agents/openai.yaml`
- 修改：`codex-plugin/skills/ppt-workflow-studio/SKILL.md`
- 修改：`codex-plugin/skills/ppt-workflow-intake/SKILL.md`
- 修改：`codex-plugin/skills/ppt-workflow-review/SKILL.md`
- 修改：`codex-plugin/skills/ppt-workflow-authoring/SKILL.md`

- [ ] **步骤 1：为每个桥接 skill 写最小可执行职责**

所有 bridge 在开始时解析 `PPT_WORKFLOW_ROOT`，读取对应权威文件，并只产出
其专属工件。不要复制原始 skill 的长正文。五个工件的责任必须如下：

```text
claude-design      -> design-directions.md（3 条方向 + 本地主题映射）
ui-ux-pro-max      -> design-research.md（每条候选的采用/转译记录）
mbb-decks          -> ghost-deck.md（每条候选的论点/叙事/页面计划）
frontend-design    -> frontend-design-review.md（三方案差异与修订）
axi-front-design   -> visual-direction-preview.html（3 个 data-design-recipe 样张）
```

每个 `agents/openai.yaml` 使用与现有 plugin skill 相同的 `interface` 结构，且
描述明确限制为 PPT 设计编排阶段，避免与通用环境内同名 skill 混淆。

- [ ] **步骤 2：重写 studio 根 skill 的阶段 3-5**

将现有“12 问、3 批”的错误表述改为“12 问分三批，随后用样张完成第 13 问”。
在 intent gate 之后以固定顺序调用五个 bridge，写入
`design-orchestration.json` 与 `decision.designRecipes`，运行 decision gate，
再向创作者展示样张。禁止在编排工件齐全前展示或确认样张。

```markdown
Apply packaged `claude-design`, `ui-ux-pro-max`, `mbb-decks`,
`frontend-design`, and `axi-front-design` in that order. Do not continue if
any required artifact or its SHA-256 binding is absent.
```

- [ ] **步骤 3：对 intake、review 与 authoring 写清交接边界**

`ppt-workflow-intake` 只负责问题与创作者确认；明确禁止在前三批完成前创建设
计配方。`ppt-workflow-review` 要读取选定配方并将其作为正式审查基准。
`ppt-workflow-authoring` 必须只使用选定 recipe，确认其哈希仍有效后生成
`preview.html` 和 `design.html`，并在源 HTML 中保留 `data-design-recipe`。

- [ ] **步骤 4：运行桥接结构测试并验证变绿**

运行：

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
python -m unittest discover -s ppt-workflow/tests -p test_plugin_design_orchestrator.py -v
```

预期：五个 bridge 均可发现，根 skill 在样张之前按固定顺序编排全部 skill。

### 任务 4：验证插件与完整回归并提交

**文件：**

- 修改：本计划涉及的全部文件

- [ ] **步骤 1：运行 skill 与插件静态验证**

运行：

```powershell
python C:/Users/duanz/.codex/skills/.system/skill-creator/scripts/quick_validate.py codex-plugin/skills/claude-design
python C:/Users/duanz/.codex/skills/.system/skill-creator/scripts/quick_validate.py codex-plugin/skills/ui-ux-pro-max
python C:/Users/duanz/.codex/skills/.system/skill-creator/scripts/quick_validate.py codex-plugin/skills/mbb-decks
python C:/Users/duanz/.codex/skills/.system/skill-creator/scripts/quick_validate.py codex-plugin/skills/frontend-design
python C:/Users/duanz/.codex/skills/.system/skill-creator/scripts/quick_validate.py codex-plugin/skills/axi-front-design
python C:/Users/duanz/.codex/skills/.system/plugin-creator/scripts/validate_plugin.py codex-plugin
```

预期：所有 skill frontmatter、目录和 plugin manifest 有效。

- [ ] **步骤 2：运行相关及完整测试**

运行：

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
python -m unittest discover -s ppt-workflow/tests -v
python -m unittest discover -s html-to-pptx/tests -v
```

预期：测试均通过；若 FFmpeg 依赖的媒体测试因环境缺失跳过，记录跳过原因。

- [ ] **步骤 3：复核变更并创建功能提交**

运行：

```powershell
git diff --check
git status --short
git add ppt-workflow codex-plugin docs/superpowers/specs docs/superpowers/plans
git commit -m "feat: orchestrate diverse PPT design skills"
```

预期：仅包含设计编排器、门禁、测试、技能说明及本次规格/计划的变更。
