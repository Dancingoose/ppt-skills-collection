---
name: "ppt-workflow"
description: "PPT 制作完整分层流程。当用户要求做 PPT、slide、deck、演示文稿、presentation 时触发。四层架构：准备层(读素材)→设计决策层(定方向)→执行层(HTML设计稿+视觉增强)→交付层(导出PPTX)。杜绝直接用 python-pptx 手工拼形状。"
---

## V3 动态视觉方案规则（优先于旧的固定风格提问）

前 12 项意图问题按 `4+4+4` 三批完成后，基于回答与素材盘点动态提出三个互有明显差异的视觉方案；不预设固定的风格类别。每个方案要给出名称、适配理由、四维视觉契约（叙事姿态、构图几何、视觉温度、字体语言）和可查看的独立样张。三方案任意两者至少有三个维度不同。

第 13 项是样张确认：制作者查看 `visual-direction-preview.html` 后选定一个方案，或选择“都不符合”。后者必须记录修改意见、重新生成三张样张，并保持问卷未完成；未确认方案时不得进入正式设计。选中方案必须写入 `decision.designProfile`，并把同一视觉契约锁入 `decision.passport.designProfile`。

执行层的每页必须登记并在 HTML `.slide` 上标记页面原型：`hero`、`context`、`evidence`、`data`、`comparison`、`process`、`transition`、`recommendation` 或 `action`。十页及以上的文稿必须包含开场、数据或证据、转场和行动页，且不得连续三页同原型。完成后输出 `deck-rhythm-review.json` 与 `design-profile-review.json`，检查整套节奏以及字体、留白、图片处理、图表语言、构图是否持续遵守所选方案。

# PPT 制作分层流程

## 核心原则

**PPTX 是 HTML 设计稿的导出格式，不是创作媒介。** 禁止直接用 python-pptx/pptxgenjs 手工拼形状——那是之前反复翻车的根因。

## 四层架构

```
准备层（一次性）          设计决策层           执行层                   交付层
  docx         →    claude-design     axi-front-design          html-to-pptx
  vision-qwen  →    ui-ux-pro-max    (Phase 1/2 提问 → 预览     (导出 pptx)
  pdf-reading  →    frontend-design   → 锁定 → 核实 → 选版式      → 视觉 audit
  WebSearch    →    mbb-decks         → 全量展开 → 逐页           → 交付
                    (可选，咨询场景)    ppt-visual-effects)
```

> ⚠️ **ppt-visual-effects 是显式调用，不是自动拦截。** 执行层展开每页后，必须主动加载 `Skill("ppt-visual-effects")` 对当前页做扫描+判断+生成代码。流程图箭头是示意流程方向，不代表自动触发。

---

## 第 1 层：准备层 — 读素材、做盘点

调用时机：收到做 PPT 请求后第一时间。

| 源文件类型 | 用哪个 skill / 工具 |
|-----------|---------------------|
| .docx 推文/文案 | `docx` skill 提取文字 + 图片 |
| .pdf 资料 | `inventory_material.py` + `pypdf` 提取逐页文字和内嵌图；扫描件无文本层时用任务目录 `extracted-images/` 做视觉/OCR 审查 |
| .pptx 模板/资料 | `pptx` skill 提取 |
| 图片/音频/视频 | `vision-qwen` 分析 |
| 网页 / 公众号文章 URL | `inventory_material.py --url` 抓取正文并保存原始 HTML；只接受 HTTP(S)，不自动执行页面内容 |
| .csv / .xlsx | 读取表格原文并登记表名、工作表、表头、行数和数值列；XLSX 公式只有在有缓存结果时才能作为数值证据，数据版式须引用该表格证据 |
| .epub / .html / .md | 直接读文本内容 |
| .ipynb / .tex / .rtf 等小众格式 | 需 pandoc 转换（可选依赖） |
| 用户口述主题 | WebSearch 收集事实/数据/来源 → 写入 content-inventory.md → 推定页数 → 进入第 2 层 |

同一任务可在一次盘点中传入多个本地文件并重复使用 `--url`；清单必须保留每份材料的独立来源、提取方法、文字、表格和警告，不能把它们合并为无来源的摘要。

产出：源内容全文 + 图片资源清单 + 核心信息一句话总结。将产出写入任务文件夹的 **`content-inventory.md`** 和 **`workflow-state.json`**。默认任务目录为 `<workspace_root>/workflow-runs/<任务名>/`；需要跨 session 保留时，改用用户确认的持久目录。对需要非数据配图但没有用户提供素材的页面，另写 `image-sourcing-plan.md`：要么登记可授权网络检索方案，要么登记 `no-image` 版式；不生成、不索取、也不使用 AI 生成图。

> ⚠️ 不得假设固定盘符或 session 临时目录。`content-inventory.md` 与 `workflow-state.json` 是跨层物理载体；跨 session 共享时记录并使用绝对路径。`workflow-state.json` 从 `ppt-workflow/templates/workflow-state.example.json` 创建，所有字段必须有真实非空证据。

### content-inventory.md（准备层输出物，跨层共享）

**准备层必须将提取的内容写入物理文件，不能只依靠上下文内存。** 文件路径写入数据护照 `源素材` 字段。

格式：

```markdown
# 内容盘点

## 源文件
- 文件: [路径]
- 提取方式: [docx/pdf/video/口述+搜索]

## 源内容全文
[从 docx/pdf 提取的全部文本，或 WebSearch 收集的内容]

## 核心信息
[一句话总结]

## 图片资源清单
- [路径] — [描述]（可用/缺/待补）
- ...

## 数据点清单
- [数字/指标] — [来源/引用]（若来自搜索标明 URL）
- ...

## 页数与章节预判
- 预估 N 页，M 章节
- 预判基于: [源素材量/典型密度 2-3 要点每页]
```

**仅口述主题无源文件 → 准备层必须做 WebSearch 收集事实/数据/来源 → 写入 content-inventory.md → 推定页数和内容形状 → 进入第 2 层。**

### 准备层强制自检清单（进入第 2 层前逐项打勾）

**⛔ 自检方式：运行检查脚本，不要纯靠记忆打勾。**

```bash
python <collection_root>/ppt-workflow/scripts/check_workflow_state.py --layer prep --task <task_dir>
```

脚本自动核对结构化素材证据、非空核心结论、可追溯数据点和页数/章节计划；`content-inventory.md` 中的核心信息、数据点和页数计划必须已替换占位文本。**任何 FAIL 项必须修正后重跑，全部 PASS 才进入第 2 层。**

```
[ ] check_workflow_state.py --layer prep 已运行且全部 PASS
[ ] content-inventory.md 和 workflow-state.json 已写入任务文件夹
[ ] 源素材类型已判定（docx/pdf/pptx/图片/口述）并用了对应提取路径；PDF 无文本层已做视觉/OCR 审查
[ ] 口述主题 → WebSearch 已做，数据点有来源 URL
[ ] 页数/章节预判已写入
[ ] convert.py 存在性已检查（提前门禁）
```

---

## 数据护照（层间信息载体）

每进入下一层时，必须携带当前层产出的"设计护照"——一个结构化 Markdown 信息块。确保关键 token（配色 hex、字体、风格方向）不丢失。

### 格式模板

```markdown
## 设计护照
- 主题: [一句话核心信息]
- 受众: [内部团队 / 管理层 / 客户 / 公开] | 沟通意图: [说服/汇报/教学/分享]
- 画布: [ppt169 16:9 / ppt43 4:3 / xiaohongshu 3:4 / story 9:16 / ...]（从 canvas-formats.md 选）
- 页数: N 页 | 章节: M 个
- 主色: #XXXXXX | 强调色: #XXXXXX | 底色: #XXXXXX
- 标题字体: FontName | 正文字体: FontName
- 风格方向: [瑞士编辑式 / 包豪斯 / ...]
- 主题方案: [minimal-white / editorial-serif / swiss-grid / party-gov-red / ...]（从 design-system.md 主题目录选）
- 品牌关键词: [词1, 词2, 词3]
- 源素材: [content-inventory.md 的文件路径]
- research-done: [true / false]（准备层已做事实调研则 true，决策层可跳过重复 WebSearch）
```

### 各层填充责任

| 层 | 填充字段 |
|----|---------|
| 准备层 | 主题、源素材路径（含 content-inventory.md）、页数/章节（估算）、research-done |
| Phase 1/2 询问 | 受众、沟通意图、核心主张、画布、页数确认、内容处理、风格版本数、主题方案、字号强度、图片来源等 |
| 设计决策层 | 从 Phase 1/2 结果写入：主色、强调色、底色、标题/正文字体、风格方向、品牌关键词 |
| 执行层 | 继承全部字段作为设计约束 — 不自行覆盖 |

### spec_lock 锁定纪律（吸收自 ppt-master）

**设计护照在用户选定方案后升级为"锁定稿"，执行层不得漂移。**

1. 方案预览阶段：设计护照是**草案**，用户选定方案时逐项确认
2. 选定后：把确认过的字段**锁定**（核心主张、受众、画布、配色、字体、主题方案、版式风格、背景策略与主背景模式）
3. 执行层展开全量页时：**必须严格按锁定字段实现**，不临时换风格、不改配色、不自行加布局；若背景策略是 `uniform`，不得为了节奏插入另一种深浅背景
4. 想改锁定的字段？**停下来问用户**，重新确认后再继续——不要在展开过程中悄悄漂移
5. 用户中途说"换一种风格"→ 回到方案预览层重新出方案，不基于漂移后的半成品修补

> 这是避免"做完整版时越做越偏"的关键纪律。锁定的意义不是僵化，而是让"确定的方向"和"正在做的东西"始终对齐。

---

## 第 2 层：设计决策层 — 定方向，不定稿

**⚠️ 进入本层前，必须完成 13 项意图采集的 3 轮创作者确认**。第一批是受众/意图/核心主张/画布；第二批是语言/期望结果/使用场景/交付用途；第三批是故事线/内容侧重点/信息密度/**设计大胆程度（1 保守至 5 实验性）**/参考风格。材料只可生成推荐选项，不能代替创作者作答；不得推断、假设或自动填充。将每项问题、回答、`creator-confirmed` 来源和创作者回复证据写入 `decision.intentQuestionnaire`，运行 `check_workflow_state.py --layer intent` 全部 PASS 后，才能加载设计 skill、生成预览或展开页面。

按场景判断用哪个：

| 场景 | 用哪个 skill | 做什么 |
|------|-------------|--------|
| 用户没想法、不知道要什么风格 | `claude-design` | 从 10 种设计语言出 3 个差异方向，用户选 |
| **用户有明确风格要求**（如"我要极简白/瑞士网格/党政风"） | **跳过 claude-design** | 直接进入 Phase 2，主题方案选项只含用户指定的主题 + 2 个映射表替代（快速路径，见下） |
| 需要精确设计 token（配色/字体/间距具体数值） | `ui-ux-pro-max` | 搜索配色+字体+风格数据库（**首次使用先跑 `--fetch-data` 初始化数据目录**，见该 skill） |
| 用户要求 MECE/行动标题/咨询报告格式 | `mbb-decks` | 只出 ghost deck 定故事线，确认后走标准流水线渲染（不自行渲染 PPTX） |
| 所有场景 | `frontend-design` | 全程辅助，确保每个选择有"原因"而非模板惯性 |

> **明确风格快速路径**：用户已指定风格方向时，跳过 claude-design 的三方向顾问模式（省去一轮不必要探索）。把用户指定的风格名直接映射到 theme-tokens.md 末尾映射表对应主题；若用户给的是非标准说法（如"性冷淡风"），先到映射表/主题目录里找到最接近的主题名，再进 Phase 2 让用户确认。

产出：确定的设计方向声明。从 Phase 1/2 用户回答中提取颜色/字体/风格/品牌关键词，写入设计护照的数据决策字段。**主题方案通过 claude-design 映射表 + 用户 Phase 2 选择确定**。执行层继承全部字段。

### 反模板审查检查点

**时机：Phase 1/2 完成后、Step 1 方案预览之前**（此时设计护照的配色/字体/主题方案字段已填入）。审查时注意：

- **审查对象**：设计护照中的风格方向、主题方案、配色 hex、字体选择
- **审查依据**：对照 `layout-library.md` 末尾「反 AI 俗套清单」（13 条，合集唯一权威版本）+ `design-system.md` token 层反俗套约束
- **标记并替代**：标记可能滑向 AI 俗套的选型（cream 底色 F4F1EA、Inter/Roboto 默认字体、emojis 图标、纯卡片堆叠、无数据页用数据版式），给出 1-2 个替代方案
- **执行与证据**：运行 `ppt-workflow-review` 的审查程序；审查的具体规则以合集两条反俗套清单为准。将结论写入 `anti-template-review.json`（包含 `schemaVersion: 1`、`skill: "ppt-workflow-review"`、`result`、`notes` 和覆盖 `intent/evidence/theme/typography/layouts` 的 `reviewedAreas`），再将同一结论和文件名登记到 `decision.antiTemplateReview`。

**一次即可，不需要每页重复。** 审查发现问题则替换有问题的选型，无问题则带着审查结论进入 Step 1 方案预览。**锁定发生在 Step 2（用户选定方案后），不是审查环节**——审查只是给方案预览前的护照把关。

### 设计决策层强制自检清单（方案预览前逐项打勾）

**⛔ 自检方式：运行检查脚本，不要纯靠记忆打勾。**

```bash
python <collection_root>/ppt-workflow/scripts/check_workflow_state.py --layer decision --task <task_dir>
```

脚本自动核对 Phase 1/2 的非空答案、完整设计护照和有结论的反模板审查。**任何 FAIL 项必须修正后重跑，全部 PASS 才进入方案预览。**

```
[ ] check_workflow_state.py --layer decision 已运行且全部 PASS
[ ] Phase 1 完成（受众/意图/核心主张/画布）
[ ] 按场景选了 skill（claude-design / ui-ux-pro-max / mbb-decks / 跳过快速路径）
[ ] 方向名称用了 10 种设计语言的精确名称（映射表可匹配）
[ ] Phase 2 完成（页数/主题方案/风格版本数等）
[ ] 反模板审查已做，并有 `anti-template-review.json` 作为证据（一致登记到 manifest）
[ ] 设计护照 4 个关键字段已填：配色 hex / 字体 / 风格方向 / 主题方案
[ ] `preview.html` 已包含封面和代表性内容页；用户确认记录已写入 `workflow-state.json` 的 `decision.preview`
```

---

## 第 3 层：执行层 — `axi-front-design` 为主力，`ppt-visual-effects` 做增强

**必须严格按 axi-front-design 规定的幻灯片工作流。**

### 用户提问：统一用 axi-front-design Phase 1/2 框架

**合并所有用户提问到一个入口。** 设计中层（claude-design/ux-pro-max/mbb）和 ppt-workflow 本身不再单独定义提问清单——所有"问用户"走 `axi-front-design` 的两阶段确认：

- **Phase 1 沟通契约**（13 项：语言/受众/沟通意图/期望结果/核心主张/场景/交付用途/故事线/**内容侧重点/信息密度/设计大胆程度/参考风格**）
- **Phase 2 设计方案**（10 项：页数/模板/内容处理/风格版本数/主题/配色/图标/图片来源/字号强度/辅助产出）

分批规则：每次 `AskUserQuestion` ≤ 4 问；第一批优先（受众/意图/核心主张/画布是最重要的四个）；其余两批在预览前问。设计大胆程度必须记录为 1-5 的创作者确认值，不能由模型代填。

**Phase 1 材料驱动选项**：有 content-inventory.md 时，Phase 1 的**选项由 agent 读材料后现场生成**（从数据形态/章节骨架/语气立场/图表暗示/受众线索/内容密度 6 类特征推导），每个选项必须能在材料里找到出处；核心主张从材料「核心信息」字段提炼 2-3 个候选 + Other 兜底。无材料（纯口述）时回退到通用骨架。详细推导规则见 `<collection_root>/references/material-driven-questioning.md`。

**Phase 1 尽早问，Phase 2 不浪费**：Phase 1 在 claude-design 出方向**之前**问（让方向建议有受众/意图上下文）；Phase 2 在步骤 1 方案预览**之前**问。两者不合并到一轮里——批次分开才能让中间产物受益。

**快速路径**：口述主题无源文件的场景，Phase 2 可基于默认假设自动跳过约 5-7 项——只确认「页数/主题方案/风格版本数/图片来源/字号强度」5 项，"模板"（自由设计）、"内容处理"（扩展补充）、"辅助产出"（只要 PPT）按默认值自动填，不弹窗。

这里也负责填充数据护照的"设计决策层"字段（受众、画布、页数、风格方向、主题方案等），因为用户在这一步做出选择。

### Step 1: 出方案预览（封面 + 1-2 张内容页）

**前置**：先加载 `<collection_root>/references/design-system.md` + `<collection_root>/references/theme-tokens.md`；3 个候选主题名的来源取决于场景：
- **标准场景**（claude-design 出方向）：claude-design 方向 → theme-tokens.md 映射表 → 3 个候选主题名。**⚠️ claude-design 输出方向时，方向名称必须使用 10 种设计语言的精确名称（如「瑞士编辑式」「包豪斯几何」，见 theme-tokens.md 映射表左列）——不要用近义改写（如"瑞士风格""几何感"），否则映射表无法匹配。**
- **咨询场景**（mbb-decks）：候选 = `mbb-consulting` + 映射表推荐的 2 个备选（如 corporate-clean）→ 3 个候选

候选主题在 Phase 2「主题方案」选项中呈现给用户确认。若 Phase 2 用户已选 1 个主题，Step 1 展示该主题的 3 个风格变体（如字号强度差异／叙事 vs 事实 mode）；若 Phase 2 用户未选（选了"你来定"），Step 1 展示 3 个不同主题的方案预览。从 theme-tokens.md 读取对应主题的完整 token。

- 多页 deck：至少在同一个 HTML 文件中展示封面 + 1 张典型内容页（tab 或并列皆可）；**单页交付物**（如公众号头图、单页 A4 海报）则展示该唯一成品页并记录用户确认，不要为了通过门禁虚构第二页
- `ppt169` 使用 1920×1080 canvas，正文 ≥ 24px；非 16:9 画布按
  `<collection_root>/references/canvas-formats.md` 的原生尺寸和字号规则实现
- 多页 deck 的每版展示：封面 + 1 张典型内容页（如部门总述）；单页交付物沿用其唯一成品页
- 每版附风格描述 + 该主题的 accent hex 色块

### Step 2: 用户选定方案 → 锁定设计护照
- **⛔ 门禁：选定方案后先锁设计护照（见 spec_lock 纪律）。展开过程中不漂移。**
- 锁定后进入 Step 3 前做内容核实

### Step 3: 内容核实（⚠️ 在选版式之前，不是之后）

**先确认内容够不够，再选版式——因为内容量变会导致版式重选。** 读取 `content-inventory.md`（准备层产出）：

1. 源素材是否足以支撑承诺的页数和要点？不够 → 停下来问用户补素材，或先做事实调研/补资料
2. 数据页的数字有没有来源？每个数字主张都要能归属（引用来源）
3. 用户选了「扩展补充」内容处理方式 → 确认扩展的方向和边界，不凭空编造事实
4. 有缺失的非数据图/截图/Logo → 在选版式前写入 `image-sourcing-plan.md`，从 `ppt-workflow/templates/image-sourcing-plan.example.md` 开始：每一页恰好一个 `supplied-image`、`web-search` 或 `no-image` 决策。`web-search` 必须先向创作者展示候选，核验原始资源页许可与署名要求；只有获得 `creator-approved` 后，才可下载并嵌入。记录候选 URL、许可、署名、本地文件与审批；缺一项即不能交付。已批准的本地文件还必须写入该页 `layoutEvidence.sourceRefs`，以证明计划中的素材实际进入了该页。若无法取得许可明确且匹配的网络素材，明确登记 `no-image` 并选择无图版式。不得用 AI 生成图或无来源占位图代替。ECharts 数据图表不属于此流程。
5. **仅口述主题无源文件 → 先做 WebSearch 收集事实/数据/来源，写入 content-inventory.md**

> 素材不够硬撑 = 返工。先核实再选版式，比选完版式发现缺东西回来改快得多。

### Step 4: 按布局库选版式（强制）

**生成任何内容页之前，必须加载四个资产库，按核实后的内容形状选版式、按主题方案选 token：**

0. **先读 `<collection_root>/references/quick-reference-card.md` 速览**（~50 行精简卡：画布/字号/token/版式P0/节奏/反俗套/增强/交付门禁），再按需跳读下面列出的完整资产库——避免一次性通读全部 5 个资产库（~120KB）的 token 开销
1. 读 `<collection_root>/references/layout-library.md` 的「选版式决策表」（位于 B 系列布局之后）+ `<collection_root>/references/design-system.md`
2. 从数据护照的「主题方案」字段 → 查 `<collection_root>/references/theme-tokens.md`，读取完整 `:root` CSS 变量
3. 每页先确定内容形状（数据 or 论断？几项对等？有无时间轴？有无图片？）
4. 为每页登记一个布局编号（叙事风 A1–A10 / 事实风 B1–B22 / Bento C1–C9），并在 `workflow-state.json` 的 `layoutEvidence` 中记录重复内容数 `itemCount`、对应素材 `sourceRefs`；量化版式还要记录 `numericValues`
4.1. 读取 `<collection_root>/references/composition-patterns.md`，再为每页登记一个 `compositionPattern`（P01–P15），让布局标签变成有层级、有焦点的构图。大胆程度必须严格对应 profile：1=conservative、2=measured、3=expressive、4=bold、5=experimental；只可使用本档及以下的构图组（P01–P02 / P01–P05 / P01–P09 / P01–P13 / P01–P15）。P05 是照片叙事构图，必须关联已批准的 `supplied-image` 或 `web-search`，没有图片则改用其余无图构图。大胆程度为 4 或 5 时，至少 20% 页面使用 P10–P15，且不得连续三页重复同一构图；不允许以增加小线条、小标签或卡片数量冒充大胆设计。
5. 在对应 `.slide` 容器写入相同的 `data-item-count`，并写入 `data-pptx-slide`；后者是转换器唯一可靠的 slide 发现标记，尤其对 900×383 等小尺寸或超宽画布不可省略
5. **P0 规则：内容数据类型必须匹配版式**——有真实数据用数据版式（B6/B7/B20/B21），无数据禁编造数字硬塞（⚠️ 禁 B6/B7 于纯概念列举）
6. **P0 规则：token 一致性**——所有颜色/圆角/阴影走 CSS 变量；叙事风（A）可用圆角/阴影，事实风（B）必须直角无阴影（`--radius:0; --shadow:none`）
7. **反俗套字体检查（修补时机）**：从 theme-tokens.md 复制 CSS `:root` 变量到 HTML 时**同步**检查 `--font-display`——如果回退链含 Inter/Roboto，在复制的同时替换为 `'Noto Sans SC','Microsoft YaHei',sans-serif`。避免"先复制不改、后面再改"的两段式修补。上游原始 token 值在 theme-tokens.md 中保持不变（数据溯源）。

在 Phase 2 明确记录 `motionDelivery`：`pptx-static` 代表只有静态 PPTX 定格；`pptx-plus-video` 将无法原生映射的 HTML 动效录制为 H.264 MP4 并内嵌进 PPTX，离线播放时不弹出浏览器；`pptx-plus-live-html` 才保留实时交互。必须由创作者确认该取舍并记录证据。第五档“实验性”以及 P14/P15 构图必须选择可播放的 `pptx-plus-video` 或 `pptx-plus-live-html`。视频模式须在交付前实际验证 PowerPoint 媒体对象和播放设置；Canvas/ECharts 的单帧截图不得称为 PPTX 动效。
8. 按布局的线框 + 结构 + 尺寸规则实现，遵守「主题节奏硬规则」（禁 3 页连同样式）和「反 AI 俗套」
9. **8 页+ deck 先画节奏表再动手**（布局库「8 页节奏模板」）

> 布局库只提供结构模式，设计系统只提供 token 规格；类名由 axi-front-design 自建，不依赖任何外部模板文件。

### Step 5: 展开全部页面
- 基于选定样式做剩余所有页
- **⛔ 门禁：选定方案后先锁设计护照（见 spec_lock 纪律），再开始展开。展开过程中不漂移。**
- 每页布局策略必须不同——**严格按 Step 4 登记的布局编号实现**（禁止 4 页全是"左图右文"）
- 字号、网格、色彩严格来自第 2 层设计决策（设计护照锁定字段）
- 布局来源：`<collection_root>/references/layout-library.md`（41 个布局：A1–A10 叙事风 + B1–B22 事实风 + C1–C9 Bento 网格）

### Step 6: 逐页注入视觉增强 — `ppt-visual-effects` 强制步骤

**运行一次 `ppt-workflow-effects`，然后对每一页在完成 HTML 结构后执行扫描：**

1. 按 ppt-visual-effects 的扫描规则判断该页是否需要增强
2. 如需增强，将生成的代码嵌入该页 `.slide` 容器内
3. 验证：增强代码在浏览器可直接运行，颜色走设计系统 CSS 变量

**不可跳过。** 即使判断"该页不需要增强"，也必须执行逐页扫描（同一次即可）。将结果写入 `effects-scan.json`：根对象必须包含 `schemaVersion: 1`、`skill: "ppt-workflow-effects"` 和 `slides`；每页记录 `id`、`status`、`reason`，应用效果时还要记录 `type`。在 `execution.effectScan` 登记该文件和所有 slide ID；检查器会逐项比对它与 `visualEffect`。

**审查绑定：** 源页逐张目检完成后，对最终的 `execution.html` 计算 SHA-256 并写入 `execution.sourceVisualReview.htmlSha256`。再按深浅色系统检查感知底色、视觉温度和主导色块，排除“CSS 底色相同但暖/冷大色块使页面看起来换了背景”的假漂移；将同一哈希写入 `execution.colorContinuityReview.htmlSha256`。交付 PPTX 对比审计完成后，对该 PPTX 计算 SHA-256 并写入 `delivery.audit.pptxSha256`。任一文件在审查后被改动，门禁必须重新失败，直到重新审查并更新对应哈希。

| 页面内容信号 | 自动注入 | 库 |
|-------------|---------|-----|
| 深色封面/过渡/CTA 页 | 动态着色器背景（ocean/aurora/particle） | Shadertoy |
| 有数字/趋势/占比的数据页 | 完整图表配置（环形+KPI/主题河流/玫瑰图） | ECharts |
| "元气/活力/能量"类表达 | 手写 Canvas 粒子系统（~60行） | Canvas 2D |
| 3D 空间感/产品/地形隐喻 | 几何体旋转或波浪曲面场景 | Three.js |
| 快速交互式 3D（有现成场景） | `<spline-viewer>` 组件 | Spline |
| "碰撞/堆积/传递/弹跳"隐喻 | 物理场景（Ball Pool/牛顿摆/堆叠） | Matter.js |

增强约束：
- Canvas/WebGL 设 `pointer-events: none`，不挡翻页
- 颜色走设计系统 CSS 变量，不硬编码
- `.slide:not(.active)` 时暂停动画循环
- 纯文字排版页不加——留白美学优先
- 单页增强 ≤ 200 行，超出则降级为装饰背景

### Step 7: 验收
- `.slide:not(.active) { display: none !important }` 防多页同显
- 所有 flex 列 slide 的内容区有 `flex: 1` 撑满高度
- 标题字号不超过 88px（H2）/ 120px（H1）
- 每个注入的增强代码在浏览器可直接运行
- **独立审查**（吸收自 ppt-agent 的跨模型审查理念）：主 agent 自己检查完排版后，用**独立审查视角**再扫一遍——看缩略图找重叠/溢出/低对比，或派 sub-agent 当"第二双眼睛"。生成者容易"看到自己想看的"，独立审查者能看到真实渲染。

### 源页面视觉审查

在运行执行层检查前，逐页以**原生画布尺寸**查看 HTML，排除重叠、裁切、溢出和对比度问题。将结果写入 `workflow-state.json` 的 `execution.sourceVisualReview`：`result` 为 `pass` 或 `revised`，`reviewedSlides` 必须完整且不重复，`notes` 记录实际审查结论。再以阅读顺序按 `data-color-system` 分组检查每个深浅系统的感知底色、视觉温度、主导色块与图片/提示块的色彩权重；每个 `.slide` 必须有 `data-color-system`，并把全量结果、HTML 哈希和各系统覆盖页写入 `color-continuity-review.json` 与 `execution.colorContinuityReview`。相同 CSS 底色不是通过条件。HTML/PPT 对比图只验证转换忠实度，不能替代这一步。

### 执行层强制自检清单（Step 4-7 完成后逐项打勾）

**⛔ 自检方式：运行检查脚本，不要纯靠记忆打勾。**

```bash
python <collection_root>/ppt-workflow/scripts/check_workflow_state.py --layer exec --task <task_dir>
```

脚本自动核对 HTML 页数与清单一致性、每页内嵌布局、布局的内容数量/数值证据、内容类型与数据版式匹配、锁定护照、逐页视觉增强决策和页面节奏。**任何 FAIL 项必须修正后重跑，全部 PASS 才进入交付层。**

```
[ ] check_workflow_state.py --layer exec 已运行且全部 PASS
[ ] quick-reference-card 已读
[ ] 每页已登记布局编号、`layoutEvidence` 和 HTML `data-item-count`
[ ] 数据-版式 P0 匹配（有数据用 A3/B2/B6/B7/B18/B20/B21/B22，无数据禁这些量化版式）
[ ] 事实风(B) 直角无阴影，叙事风(A)/Bento(C) 用圆角
[ ] --font-display 含 Inter/Roboto 已替换为 Noto Sans SC / Microsoft YaHei
[ ] 8页+ deck 已画节奏表（先画表再动手）
[ ] 无 3 页连续同主题（light/dark 交替）
[ ] 展开时未漂移（配色/字体/风格与锁定护照一致）
[ ] ppt-visual-effects 已加载，每页扫过（含判断"不需要"的页）
[ ] Canvas/WebGL pointer-events: none
[ ] 增强代码颜色走 CSS 变量，无硬编码 hex
[ ] 已逐页审查原生 HTML，并将完整结果写入 execution.sourceVisualReview
[ ] 已按 color system 检查感知底色、色温和主导色块，并写入 execution.colorContinuityReview
[ ] 独立审查已做（缩略图/溢出/对比）
```

---

## 第 4 层：交付层 — HTML → PPTX

### 前置门禁：convert.py 检查（⚠️ 强制）

**进入交付层前，先检查 `html-to-pptx/convert.py` 是否存在。** 如果不存在：

1. 告知用户：html-to-pptx 需要转换脚本，尚未安装
2. 给出安装命令（见 README → 依赖 → html-to-pptx 渲染脚本）
3. 提供替代：先交付 HTML 版本（可在浏览器演示），等脚本就绪后再导出 PPTX
4. **不要**等到执行层全跑完才通知——提前确认避免浪费前面所有工作

### 首次配置提醒

html-to-pptx 首次使用需要确认两条偏好（fonts.auto_install + audit.mode），详见 `html-to-pptx/SKILL.md`。在执行层完成 HTML 设计稿后、转换前弹出 `AskUserQuestion`。

**⚠️ 检查时机**：转换前先 `Bash: test -f html-to-pptx/.config.local.toml`——**不存在**则弹 AskUserQuestion 首次配置；**已存在**则跳过（说明此前已配置过，不要再弹窗打扰）。这是交付层的前置检查，不要遗漏。

### 交付步骤

- 用户要 `.pptx` → 用 `html-to-pptx` 转换（文本是原生文本框，形状是原生 OOXML 对象）
- 用户只要 HTML → 直接交付 HTML 文件
- 用户明确说"纯 PPTX 不要 HTML" → 走内置 `pptx` skill（编辑模板用）
- 转换后跑视觉 audit（triage 模式：主 agent 看缩略图分流 + sub-agent 看入围页）
- **注意**：Canvas/WebGL 增强（Three.js/Shadertoy/Matter.js）导出 PPTX 时会降级为静态截图；若用户要求可编辑 PPTX，需在交付前说明这一点，或保留 HTML 版本做演示

### Canvas/WebGL → PPTX 降级细节

- **Three.js / Shadertoy / Matter.js / Canvas 粒子**：html-to-pptx 的 deco_snapshot 档自动截图（Playwright 截取激活 slide 的原生画布尺寸），嵌入为 PNG 位图。**不是可编辑的矢量对象，截图后不可在 PowerPoint 内修改着色器参数/3D 视角/粒子行为。**
- **ECharts 图表**：优先走 deco_snapshot 截图保留完整视觉（含动画终态）；如需在 PPTX 中编辑图表数据，可另附原始数据 CSV 或告知用户手动在 PowerPoint 中重建图表对象。
- **Shadertoy 着色器截图注意事项**：着色器依赖 `requestAnimationFrame` 持续渲染；截图前需等 2-3 帧确保着色器完成初始化。若着色器有 `iTime` 时间累积效果，截图保留的是截图时刻的静态帧。
- **用户若需要可编辑 PPTX 且含图表**：建议在 Phase 2 阶段（设计方案→辅助产出）提前确认，执行层可对数据页额外预留原生 PPT 图表数据表（CSV），交付时一并提供。

### 交付层强制自检清单（转换前逐项打勾）

**⛔ 自检方式：运行检查脚本，不要纯靠记忆打勾。**

```bash
python <collection_root>/ppt-workflow/scripts/check_workflow_state.py --layer deliver --task <task_dir>
```

脚本自动核对转换依赖导入、Playwright 兼容浏览器实际渲染、交付形态及导出产物。若登记 PPTX 输出，还会核对输出文件和覆盖全页的交付审计记录；审计必须另存为 JSON artifact，记录结果、全页计数、PPTX SHA-256、实际渲染器和结论，并与 manifest 完全一致。**任何 FAIL 项必须修正后重跑，全部 PASS 才交付。**

```
[ ] check_workflow_state.py --layer deliver 已运行且全部 PASS
[ ] convert.py 存在
[ ] 已审阅 HTML/PPT 对比图并把 result、reviewedPages、notes 写入 delivery.audit
[ ] .config.local.toml 已配置（无则弹首次配置）
[ ] 用户已确认交付形态（HTML / PPTX / 纯PPTX）
[ ] Canvas/WebGL 增强已告知会降级为静态截图
[ ] 转换后视觉 audit 已跑（triage 模式）
```

---

## 禁止项（检查清单）

> **合集唯一权威反俗套清单**。以下条款覆盖设计决策层+执行层，与 `layout-library.md` 末尾「反 AI 俗套清单」（13 条补充规则）互补——两份加起来是全集合禁止项。

- ❌ 直接用 python-pptx / pptxgenjs 手工拼矩形和椭圆堆砌页面
- ❌ 跳过方案预览直接做完整版（除非用户明确说"只要一版"）
- ❌ 跳过 AskUserQuestion 弹窗直接假设偏好
- ❌ 用 emoji 当图标（除非品牌本身用）
- ❌ 渐变背景、accent stripe、圆角卡片 + 左侧彩色 border 组合
- ❌ 多页内容页用同一种布局策略（左图右文 × 4）
- ❌ 每页都是白底——用 1-2 种背景色制造节奏
- ❌ 跳过布局库选版式直接凭感觉排（必须按 `<collection_root>/references/layout-library.md` 登记布局编号）
- ❌ 数据页编造数字硬塞进无数据版式（B6/B7 禁用于纯概念列举）
- ❌ 给纯文字排版页硬塞动画/粒子（破坏留白）
- ❌ 让 Canvas/WebGL 拦截鼠标事件导致无法翻页
- ❌ 在没确认最终交付形态（HTML vs PPTX）前做大量动画增强
- ❌ 选定方案后展开时偷偷改配色/字体/风格（违反 spec_lock——要改先问用户）
- ❌ 源素材不足硬撑页数（先补素材或做事实调研，再展开）
- ❌ 标题字体用 Inter/Roboto/Arial 默认无衬线——必须从主题 token 读取，多数主题已配有不含 Inter 的字体族
- ❌ 卡片填充类型混用（ink/accent/灰底/描边四选一）
- ❌ 用 9px 圆形装饰点替代文字标记
- ❌ 数据页不加来源——每个数字主张都要归属
- ❌ 装饰元素超出页面边距或贴 slide 边界
- ❌ 全 deck 只用 light 页没有 dark 页——节奏靠背景色交替

> 补充规则见 `layout-library.md` 末尾「反 AI 俗套清单」——两者互补，含负向清单的例子不重复列举。

---

## 快速参考：首次做 PPT 时的加载顺序

```
# === 准备层 ===
Skill("docx") 或 Skill("vision-qwen") 或 WebSearch(facts+data)  # 读素材或调研
Write content-inventory.md                                      # 写内容盘点（含源全文/数据/页数预判）
Bash: test -f html-to-pptx/convert.py                           # ⚠️ 提前门禁：检查convert.py是否存在

# === Phase 1 前置（⚠️ 在 claude-design 之前）===
AskUserQuestion Phase 1                                         # 受众/意图/核心主张/画布（claude-design 的前置上下文）

# === 设计决策层 ===
Skill("claude-design")                          # 出 3 方向（→ 映射表 → 候选主题名）
Skill("ui-ux-pro-max")                          # 搜索配色/字体/风格数据库（按需）

# === 方案预览前（Phase 2 + 反模板审查）===
AskUserQuestion Phase 2                                         # 页数/主题方案/风格版本数等（含 claude-design 映射的候选主题）
Skill("frontend-design")                        # 反模板审查（需 Phase 1/2 结果已填，审查设计护照）

# === 执行层 ===
Read <collection_root>/references/quick-reference-card.md  # 执行前速查卡（精简替代通读全部资产库）
Read <collection_root>/references/canvas-formats.md        # 画布规格 + 非16:9适配规则（非16:9时必读）
Read <collection_root>/references/design-system.md         # token 基线和主题目录
Read <collection_root>/references/theme-tokens.md          # 选定主题的完整 :root CSS token
Read <collection_root>/references/layout-library.md        # 41 布局选版式（含选版式决策表，选版式时按需跳读）
Read <collection_root>/references/composition-patterns.md  # 大胆程度到复杂构图的映射
Read <collection_root>/references/web-image-sourcing.md    # 网络配图或无图的决策与许可记录
Skill("axi-front-design")                       # 预览→展开
Skill("ppt-visual-effects")                     # 逐页增强（逐页扫描，加载一次即可）

# === 交付层 ===
Skill("html-to-pptx")                           # 导出 PPTX（convert.py 已在准备层之后检查过）
```

**四层自检全部用代码化检查**（各层完成时运行；脚本在合集内，不含于 installed 缓存）：

```bash
# 准备层完成时
python <collection_root>/ppt-workflow/scripts/check_workflow_state.py --layer prep --task <task_dir>
# 决策层完成时（方案预览前）
python <collection_root>/ppt-workflow/scripts/check_workflow_state.py --layer decision --task <task_dir>
# 执行层完成时（展开全量后、交付前）
python <collection_root>/ppt-workflow/scripts/check_workflow_state.py --layer exec --task <task_dir>
# 交付层完成时（转换后）
python <collection_root>/ppt-workflow/scripts/check_workflow_state.py --layer deliver --task <task_dir>
```

脚本输出 PASS/FAIL。**FAIL 必须修正后重跑直到全 PASS。** 它使用任务的 `workflow-state.json` 作为证据；示例见 `ppt-workflow/templates/workflow-state.example.json`。

来源：基于多次迭代试错总结，MIT License
