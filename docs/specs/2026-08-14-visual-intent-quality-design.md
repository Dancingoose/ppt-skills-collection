# 视觉意图与整套 PPT 质量规格

## 目标

让 PPT 工作流能够准确捕捉制作者的视觉意图，并稳定产出更有辨识度的
演示文稿，而不是将全部任务固定为同一种风格。工作流必须保留三种可选方向：

- `consulting`：面向管理层，证据优先、克制、结论锋利。
- `editorial`：叙事驱动、有记忆点、以章节节奏推进。
- `impact`：大尺度、高对比、适合现场演讲。

制作者通过可见的视觉样张选择方向，而不是回答含义模糊的文字风格问题。
选择结果成为任务契约中可验证的一部分；最终审查既评估单页正确性，也评估
整套文稿的阅读节奏。

## 范围

本次变更只更新可复用 PPT 工作流封包，不向仓库加入示例报告、成品 PPT 或
任务输出。保留 HTML-first 制作方式、证据溯源、现有 PPTX 转换路径，以及
已有的源页面、色彩连续性和交付审查。

## 意图采集

规范的意图采集包含 13 个由制作者确认的答案，分为四批；每次交互最多四问。

| 批次 | 问题 | 目的 |
|---|---|---|
| 1 | 受众、沟通意图、核心主张、画布 | 建立沟通契约。 |
| 2 | 语言、希望听众会后采取的行动、使用场景、交付方式 | 建立演示的使用与阅读条件。 |
| 3 | 故事线、内容重心、信息密度、设计大胆程度 | 建立叙事和构图约束。 |
| 4 | 视觉方向样张确认 | 锁定可见的视觉方向。 |

现有 `referenceStyle` 由“视觉方向样张确认”取代。`expectedOutcome` 的文案
改为询问听众会后需要做出的行动或决策，避免与“沟通意图”重复。`deliveryUse`
重命名或明确为交付方式，用于区分现场演讲、邮件阅读和混合交付。

意图问卷模式从版本 2 升级到版本 3。版本 1 和 2 仅为已有任务记录保留读取
兼容；新任务必须使用版本 3。

## 视觉方向预览

完成前三批后，工作流生成轻量的 `visual-direction-preview.html`，其中包含三张
独立的视觉样张。样张使用中性占位内容，不为同一份完整 PPT 做三套渲染。

每个候选方向必须清晰体现其视觉契约：

| 方向 | 视觉契约 |
|---|---|
| consulting | 结论先行标题、直接证据区、克制配色、分析型图表、精确标注 |
| editorial | 有立场的标题、章节节奏、受控的图片或色块、编辑式字体、记忆点转场页 |
| impact | 大尺度对比、稀疏信息、强构图动作、舞台感色块、现场演讲可读性 |

制作者选择写入 `decision.visualDirection`：

```json
{
  "schemaVersion": 1,
  "selected": "editorial",
  "previewArtifact": "visual-direction-preview.html",
  "candidates": ["consulting", "editorial", "impact"],
  "creatorConfirmation": "制作者在查看全部三种样张后选择 editorial。",
  "evidence": "制作者回复的引用位置"
}
```

决策门禁必须校验全部候选方向、合法的选择值、可读取的预览文件和制作者确认。
禁止根据主题、组织或旧文件自动推断视觉方向。

## 视觉方向到设计约束的映射

`decision.visualDirection` 复制到已锁定的设计护照。执行层据此映射允许的主题
家族、字体尺度、图片用法、构图模式、图表表达与预期页面原型。任何例外都必须
记录原因。

每个执行页新增必填 `archetype`，取值范围为：

`hero`、`context`、`evidence`、`data`、`comparison`、`process`、`transition`、
`recommendation`、`action`。

页面原型不同于布局 ID：布局描述几何结构，页面原型描述读者在本页应完成的理解
任务。二者结合后，工作流才能审查整套 PPT 的叙事节奏，而不只是统计布局编号。

## 质量门禁

保留现有视觉检查。在全部 HTML 页面完成后、转换前新增两份文件化审查。

### 整套节奏审查

`deck-rhythm-review.json` 记录阅读顺序、每页原型、章节边界和审查结果。以下
情况必须失败：

- 连续三页使用同一种页面原型；
- 10 页及以上的 PPT 缺少有目的的 `hero`、数据或证据页、行动或建议页；
- 长篇 PPT 没有明确的章节或转场停顿；
- 重复卡片网格页违反既有的“最多 20%、间隔至少三页”规则。

### 视觉方向审查

`visual-direction-review.json` 记录已选方向、审查页面、结果、例外和说明。它
核验实际字体、留白、图片处理、图表语言和构图行为是否匹配已选方向，并明确拒绝
“封面精美、内容页退化为通用模板”的断裂。

### 独立质量审查

现有 `execution.independentReview` 扩展为五个维度：

- 层级：三秒内能读出主结论；
- 节奏：阅读姿态按设计发生变化；
- 重复：布局和页面原型不公式化；
- 证据：数据图包含结论性标注和来源；
- 方向：页面持续符合已选视觉契约。

每个维度记录 `pass`、`revised` 或具有理由的 `exception`。存在未解决失败项时，
执行门禁不得通过。

## 需要修改的文件

- `ppt-workflow/SKILL.md`：规范 13 项、四批提问和样张预览时机。
- `codex-plugin/skills/ppt-workflow-intake/SKILL.md`：新批次规则和视觉确认产物。
- `codex-plugin/skills/ppt-workflow-authoring/SKILL.md`：方向映射与逐页原型要求。
- `codex-plugin/skills/ppt-workflow-review/SKILL.md`：整套节奏和视觉方向审查。
- `ppt-workflow/templates/workflow-state.example.json`：模式版本 3 与全部新字段/产物。
- `ppt-workflow/scripts/check_workflow_state.py`：模式、决策、执行、审查的 fail-closed
  校验。
- `ppt-workflow/tests/test_check_workflow_state.py`：聚焦的正向与负向回归测试。
- `references/quick-reference-card.md` 与
  `references/material-driven-questioning.md`：简洁的执行说明。

## 验证标准

实施完成必须同时满足：

1. 新模式准确接受 `4 + 4 + 4 + 1` 批次中的 13 个答案；
2. 缺少视觉预览或缺少制作者确认时，决策门禁失败；
3. 视觉方向与锁定护照不一致时，执行门禁失败；
4. 缺少、重复或缺乏连贯性的页面原型触发新的质量门禁失败；
5. 合规的长篇 PPT 通过准备、意图、决策、执行和交付全部检查；
6. 既有工作流与转换器测试继续全部通过。
