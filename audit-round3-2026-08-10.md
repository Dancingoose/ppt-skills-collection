# PPT 工作流合集第三轮审查 — 全流程模拟排查

> 模拟场景："帮我做一个 AI 行业趋势分析 PPT"（用户纯口述，无任何源文件）
> 审查方式：从准备层到交付层，逐步骤追踪 agent 应该执行的操作，比较每个步骤的输入/输出是否与实际文件内容匹配
> 审查日期：2026-08-10

---

## 模拟: 全流程 walkthrough

### 触发

用户说"帮我做一个 AI 行业趋势分析 PPT" → `ppt-workflow` 触发。

无源文件 → 走「用户口述主题」分支。

---

### 准备层

**workflow 规定**：WebSearch 收集事实/数据/来源 → 写入 content-inventory.md → 推定页数 → 进入第 2 层

**模拟执行**：
1. WebSearch "AI 行业趋势 2026" — ✅ 可行
2. 写 `content-inventory.md` — ✅ 模板清晰

#### ⚠️ #NEW-1：任务文件夹路径未定义 (P2)

ppt-workflow L43 说 content-inventory.md 放在"任务文件夹内"，但整个流程从未定义任务文件夹路径。用户 auto-memory 说所有文件放 `D:\CLAUDEworkspace\work\任务名\`，但 workflow **不引用这个约定**。不同 session 可能把 content-inventory.md 放在不同位置。

**建议**：在工作流开篇定义任务文件夹默认路径，或从用户 memory 中读取偏好。

---

### 设计决策层

**workflow 规定**：加载 claude-design → 出 3 方向 → 加载 frontend-design 做反模板审查 → (可选) ui-ux-pro-max

**快速参考中的加载顺序**：
```
Skill("claude-design")    # 决策层
Skill("frontend-design")  # 决策层
# Phase 1/2 用户提问      # 执行层
```

#### ⚠️ #NEW-2：claude-design 反搜索冗余 (P3)

claude-design SKILL.md 开篇说"Priority #0 — 先验证事实，WebSearch"。但准备层已经做过 WebSearch 并写入 content-inventory.md。claude-design 不知道这件事，会重复搜索。

**建议**：准备层做完 WebSearch 后，在数据护照中标记 `research-done: true`，决策层 skill 读到此标记后跳过搜索。

#### 🔴 #NEW-3：claude-design 缺少受众/意图上下文即出方向 (P1)

claude-design 在三方向顾问模式中生成 3 个差异化设计方向。但此时 Phase 1（受众/沟通意图/核心主张）还没有执行——Phase 1 被安排在"执行层"才处理。

claude-design 产出的方向是基于 10 种设计语言的纯风格分类（瑞士编辑式/包豪斯/留白...），不依赖业务上下文——所以功能上可运行。但如果知道受众是"投资人 vs 内部团队 vs 公开观众"，方向建议明显可以更精准。

**现象**：claude-design 出方向 → 映射到 3 个主题 → Phase 2 "主题方案"选项包含这 3 个主题 → 用户选 → 但 Phase 1 的受众/意图到这之后才被确认。

**这不是阻断性 bug，但存在优化空间**：Phase 1 的核心三问（受众/意图/核心主张）如果提前到设计决策层之前，能让 claude-design 的方向建议更贴切，也能让数据护照更早锁定关键字段。

**建议**：把 Phase 1 拆为两部分——"方向级"（受众/意图/核心主张/画布）提前到设计决策层之前；"细节级"（语言/期望结果/场景/交付用途/故事线）留在执行层之前。

---

#### 反模板审查检查点

ppt-workflow 说"设计决策层产出后，在进入执行层之前做一次反模板审查"。审查对象：设计护照中的风格方向、主题方案、配色 hex、字体选择。

但在当前流程中，设计护照的配色/字体字段是"从 Phase 1/2 结果写入"——Phase 1/2 发生在执行层。所以反模板审查发生时，设计护照只有：
- ✅ 主题（准备层）
- ✅ 源素材路径（准备层）
- ✅ 页数估算（准备层）
- ✅ 3 个设计方向（claude-design）
- ❌ 受众、意图、核心主张、画布 — Phase 1 还没跑
- ❌ 最终配色 hex、字体 — 来自 Phase 1/2 结果

#### ⚠️ #NEW-4：反模板审查时护照数据不完整 (P2)

审查发生在决策层末尾，但被审查字段（配色 hex、字体、主题方案最终确认值）要到执行层 Phase 2 之后才填入。审查的"对象"大部分是空的。

实际效果：审查只能审 claude-design 出的 3 个方向是否踩了反俗套。这个价值有限。

**建议**：把反模板审查移到 Phase 1/2 之后、Step 1 预览之前（此时护照已完成，但还没建 HTML）。

---

### 执行层

#### 正确的 Step 顺序（第二轮审查后已修正）

Step 1: 预览 → Step 2: 锁定 → Step 3: 内容核实 → Step 4: 选版式 → Step 5: 展开 → Step 6: 逐页增强 → Step 7: 验收

#### Phase 1/2 提问

Phase 1 (9 项) + Phase 2 (10 项) = 19 项。AskUserQuestion 每次 ≤ 4 问。理论最少 5 轮。

#### ⚠️ #NEW-5：19 问的摩擦度 (P2)

对于"口述主题无文件"场景（最常见的 PPT 需求），几乎所有 19 项都需要用户确认。5+ 轮 AskUserQuestion 弹窗会让用户感到"我在填问卷"而非"我在做 deck"。

在实践中有优化空间：agent 可以智能跳过（比如"没有源文件 = 没有模板 → 自由设计"，"没提品牌色 → 按主题默认"），但 workflow 当前文档没有给出"可跳过场景"的指引——每个问题都标为强制。

**建议**：在 Phase 1/2 询问规则中加一段「快速路径」——口述主题无源文件场景下，可基于默认假设跳过 5-7 项，只确认"受众/核心主张/画布/页数/主题方向"5 项。

---

#### Step 1: 方案预览

**前置条件**："从 Phase 1/2 用户回答中确定 3 个候选主题名，从 theme-tokens.md 读取每个候选主题的完整 token"

#### ⚠️ #NEW-6："从 Phase 1/2 回答确定候选主题"表述不准确 (P2)

实际上 3 个候选主题名的来源是：claude-design 出 3 个设计方向 → 通过 theme-tokens.md 末尾映射表找到对应主题名。Phase 1/2 的"主题方案"问题是把这三个映射后的主题名作为选项呈现给用户。

当前表述"从 Phase 1/2 用户回答中确定"容易让人误解为"用户先回答了才确定"，实际上是"映射先确定，再让用户选"。建议改为："从 claude-design 的方向建议 + 映射表确定 3 个候选主题名（Phase 2 的「主题方案」选项即为这三者）"。

---

#### Step 3: 内容核实

模拟：读 content-inventory.md → 对比承诺页数 → 数据点是否有来源 → 不够则补。

如果 content-inventory.md 来自 WebSearch（口述主题场景），数据点清单应该包含来源 URL —— ✅ 模板中有"来源/引用"字段。

#### Step 4: 选版式

**workflow 规定**："使用布局库的「选版式决策表」"

#### ⚠️ #NEW-7：layout-library.md 中没有统一的「选版式决策表」(P2)

layout-library.md 有 41 个布局各自的"适用内容"字段，但没有一个集中的决策表。最接近的东西是 axi-front-design SKILL.md 里的快速索引表（L192-208），但那不是 layout-library.md 的内容。

ppt-workflow 说"读 layout-library.md 的「选版式决策表」"，但 layout-library.md 不包含这个名字的章节。agent 在 layout-library.md 里找不到这个名字的表。

**建议**：在 layout-library.md 末尾（反俗套清单之前）增加一个「选版式决策表」章节，把所有布局编号、内容类型、适用场景放进一张统一表。

---

#### Step 6: 逐页 ppt-visual-effects

ppt-workflow 规定："对每一页，在完成 HTML 结构后，必须加载 Skill('ppt-visual-effects')"

对于一个 12 页的 deck，这意味着 12 次 Skill() 调用。每次 Skill 调用会加载整个 ppt-visual-effects SKILL.md（~280 行）到上下文。

#### ⚠️ #NEW-8：逐页 Skill() 调用开销 (P3)

对于 12+ 页的 deck，12 次 Skill("ppt-visual-effects") 会产生大量重复的上下文加载。实际效果上 agent 可能会一次加载后批量处理所有页面（绕过了"每页"的要求），或者严格遵守但浪费大量 token。

**建议**：改为"加载一次 Skill，然后逐页扫描并生成代码"，不要求每页重新加载。

---

### 交付层

#### 前置门禁：convert.py 检查

ppt-workflow L252-257 规定进入交付层前检查 convert.py。同时说"不要等到执行层全跑完才通知"。

#### ⚠️ #NEW-9：门禁位置与"不要等到最后"矛盾 (P3)

门禁指令写在交付层章节。agent 如果按章节顺序阅读，会等到执行层全跑完才看到这条指令。虽然指令说"不要等到最后"，但指令自身的位置就在最后。

**建议**：在准备层之后加一条"提前门禁：立刻检查 convert.py，不存在则警告用户"，再配合交付层的二次检查。

---

### 交付层 — html-to-pptx 首次配置

ppt-workflow 规定首次使用前弹窗问 fonts.auto_install + audit.mode。

这个步骤只有首次需要，后续 session 可以跳过（配置已写入 `.config.local.toml`）。但 workflow 没有"检查是否已配置"的指令。

---

## 🔴 P0 阻断级发现

### #NEW-10：中国场景 4 套主题 token 值形成循环引用——既不在 design-system.md 也不在 theme-tokens.md

**这是这次模拟排查发现的最严重问题。**

涉及的 4 套主题：`party-gov-red`、`academic-defense`、`courseware-blue`、`handdrawn-explainer`

两个文件各自的说法：

**theme-tokens.md**（L715-724）：
```
## 中国场景 4 套（codex-ppt，MIT）
> 上卷 auth 已有完整 token。此处仅索引主题名+accent hex，详细 token 见 design-system.md 第五部分。
```
只给了一个简单索引表（主题名 / accent hex / 气质），**没有 CSS `:root` token 值**。

**design-system.md**（L201-203）：
```
### 中国场景 4 套（来自 codex-ppt-skill）
> 这 4 套的**完整 CSS `:root` token 值**见 `references/theme-tokens.md`，格式与其他 37 套一致。
以下仅保留视觉规则和特殊约束说明，token 表不在此重复。
```
说 token 在 theme-tokens.md。**但 theme-tokens.md 里没有。**

**两边的 CSS `:root` 值是空的。** 当用户选党政红/科研答辩/教学课件/手绘解释主题时，执行层无法获取 `--bg` / `--accent` / `--font-sans` / `--radius` 等 token——整个主题无法落地。

**第二轮审查问题 #10 说"已修复"，但修复只做了一半**：design-system.md 删了 token 表（正确），theme-tokens.md 加了索引（不够），但 CSS `:root` 值没有实际写入。

**修复**：为这 4 套主题补全 CSS `:root` 变量块（格式与其他 37 套一致），写入 theme-tokens.md 中国场景章节，替换当前的简单索引表。

---

## 🟡 P1 配合/逻辑问题

### #NEW-11：claude-design 运行时缺少 Phase 1 核心信息 (P1)

Phase 1 的核心三问（受众/意图/核心主张）安排在"执行层"，但 claude-design 在"设计决策层"。
claude-design 出方向时不知道受众是谁、沟通意图是什么。

影响：方向建议不够精准（但功能可运行，因为 10 种设计语言本身不依赖受众）。

---

### #NEW-12：Phase 2 "主题方案"和 Step 1 "方案预览"都涉及主题选择 (P1)

Phase 2 的第十问是"主题方案：倾向哪套主题？"，而 Step 1 是"出 3 个主题的方案预览"。
这两步都是让用户选主题——如果 Phase 2 通过弹窗选了"瑞士网格"，Step 1 还要再展示"瑞士网格 + 杂志 + 极简白"三版预览吗？还是 Phase 2 只是缩小范围（比如 41→3），Step 1 才是最终选择？

当前文档对此没有明确分工，agent 可能两种做法都合理。

**建议**：明确：Phase 2 "主题方案"= 从 claude-design 映射来的 3 个主题名 + "你来定"；Step 1 方案预览 = 把 Phase 2 选中的 1 个（或尚未选的 3 个）做成视觉预览。如果 Phase 2 已选 1 个，Step 1 展示该主题的 3 个风格变体而非 3 个不同主题。

---

## 🟢 P2 体验/摩擦问题

### #NEW-13：optional skill 的首次初始化未纳入流程 (P2)

ui-ux-pro-max 首次使用需要 `--fetch-data` 下载 BM25 索引数据。workflow 加载它时，如果数据不存在，搜素引擎返回空结果——不会报错但结果无效。workflow 没有"检查数据是否存在、不存在则初始化"的步骤。

---

### #NEW-14：字体反俗套修补规则分散在两处，执行层可能重复修补 (P2)

theme-tokens.md 开头说"保留上游原始 token 不做修改"、执行层修补。ppt-workflow Step 4 第 7 条说"检查 --font-display 含 Inter 则替换"。但 axi-front-design 的反俗套清单也有一条关于字体的。三处都在说同一件事，但修补发生的精确位置不明确——是在读 theme-tokens 时、写 HTML `:root` 时、还是做完预览之后？

**建议**：在 Step 4 第 7 条中明确："修补时机：从 theme-tokens.md 复制 CSS `:root` 变量到 HTML 时同步替换"，避免"读了不改、后面再改"的两段式修补。

---

## 📊 汇总：本轮新发现问题

| 优先级 | 编号 | 问题 | 影响 |
|-------|------|------|------|
| 🔴 P0 | #NEW-10 | 中国场景 4 套主题 token CSS 值缺失（循环引用） | 这 4 套主题完全无法使用 |
| 🟡 P1 | #NEW-11 | claude-design 缺少受众/意图上下文 | 方向建议不够精准 |
| 🟡 P1 | #NEW-12 | Phase 2 主题选择 vs Step 1 预览分工不清 | agent 可能重复或遗漏 |
| 🟢 P2 | #NEW-1 | 任务文件夹路径未定义 | 文件散落 |
| 🟢 P2 | #NEW-4 | 反模板审查时护照字段未填 | 审查价值打折扣 |
| 🟢 P2 | #NEW-5 | 19 问摩擦度 | 用户填问卷感 |
| 🟢 P2 | #NEW-6 | "从 Phase 1/2 回答确定候选主题"表述不准 | agent 理解偏差 |
| 🟢 P2 | #NEW-7 | layout-library 中缺少「选版式决策表」章节 | agent 找不到对应名称 |
| 🟢 P2 | #NEW-13 | ui-ux-pro-max 首次初始化未纳入流程 | 搜索引擎返回空结果 |
| 🟢 P2 | #NEW-14 | 字体修补三处各自描述 | 修补时机不精确 |
| 🟢 P3 | #NEW-2 | claude-design 与准备层 WebSearch 重复 | 浪费一次搜索 |
| 🟢 P3 | #NEW-3 | 同 #NEW-11 的轻微形式 | — |
| 🟢 P3 | #NEW-8 | 逐页 Skill() 调用开销 | 12 页 deck = 12 次加载 |
| 🟢 P3 | #NEW-9 | convert.py 门禁指令位置偏后 | agent 可能读到晚了 |

**总计**：14 个新问题（1 个 P0 / 2 个 P1 / 8 个 P2 / 3 个 P3）

---

## 🔍 两轮审查修复完成度复核

模拟流程中还交叉验证了前两轮修复的状态：

| 前两轮修复 | 状态 | 备注 |
|-----------|------|------|
| #1 CSS 变量名 | ✅ 已修复 | `var(--accent)` 正确 |
| #2 36 主题 token | ✅ 已修复 | theme-tokens.md 存在且完整 |
| #3 convert.py 门禁 | ✅ 已修复 | ppt-workflow L250-257 |
| #4 设计语言→主题映射 | ✅ 已修复 | theme-tokens.md 末尾映射表 |
| #5 mbb 视觉接入 token | ✅ 已修复 | mbb-consulting 主题完整 |
| #6 Step 2.5 强制标注 | ✅ 已修复 | axi-front-design 已改 |
| #7 frontend-design 角色 | ✅ 已修复 | 审查规则明确 |
| #8 字体默认违规 | ✅ 已修复 | 默认改为 Noto Sans SC |
| #9 护照颜色 vs token | ✅ 已修复 | 覆盖规则已写 |
| #10 字号双来源 | ✅ 已修复 | design-system 不再定义字号 |
| R2#10 token 单源 | ⚠️ 半修复 | **中国 4 套的 CSS :root 丢失（即 #NEW-10）** |
| R2#5 Step 顺序 | ✅ 已修复 | Step 1-7 顺序正确 |
| R2#9 口述搜索路径 | ✅ 已修复 | 准备层表格有分支 |

---

## 修复记录（2026-08-10，本轮 14 项）

| 编号 | 优先级 | 问题 | 修复方式 | 涉及文件 |
|------|-------|------|---------|---------|
| #NEW-10 | 🔴 P0 | 中国 4 套主题 CSS :root 缺失 | 在 theme-tokens.md 补全 4 套完整 `:root` CSS 变量（party-gov-red / academic-defense / courseware-blue / handdrawn-explainer），格式与其他 37 套一致；更新 design-system.md 指向注释 | theme-tokens.md, design-system.md |
| #NEW-11 | 🟡 P1 | claude-design 缺受众/意图上下文 | ppt-workflow 第 2 层加"Phase 1 前置门禁"——进入 design decision layer 前先做完 Phase 1；claude-design 加"前置检查"从数据护照读受众/意图 | ppt-workflow/SKILL.md, claude-design/SKILL.md |
| #NEW-12 | 🟡 P1 | Phase 2 vs Step 1 主题选择分工不清 | ppt-workflow Step 1 前置中明确：Phase 2 用户选 1 个主题 → Step 1 出该主题 3 个变体；Phase 2 选"你来定" → Step 1 出 3 个不同主题 | ppt-workflow/SKILL.md |
| #NEW-1 | 🟢 P2 | 任务文件夹路径未定义 | ppt-workflow 准备层加默认路径 + 回退逻辑 | ppt-workflow/SKILL.md |
| #NEW-4 | 🟢 P2 | 反模板审查时护照字段为空 | 审查时机从"决策层末尾"移到"Phase 1/2 完成后→Step 1 预览前" | ppt-workflow/SKILL.md |
| #NEW-5 | 🟢 P2 | 19 问摩擦度 | 加"快速路径"段落：口述无文件场景下 Phase 2 可跳过 5-7 项 | ppt-workflow/SKILL.md |
| #NEW-6 | 🟢 P2 | 候选主题来源表述不准 | Step 1 前置改写为"claude-design 方向 → 映射表 → Phase 2 选项"，明确链条 | ppt-workflow/SKILL.md |
| #NEW-7 | 🟢 P2 | layout-library 缺选版式决策表 | 新建「选版式决策表」章节（按类型选系列 + 按形状选布局 + 决策流程图） | layout-library.md |
| #NEW-13 | 🟢 P2 | 快速参考加载顺序与实际不一致 | 重写快速参考：Phase 1 前置、convert.py 提前门禁、反模板审查位置后移 | ppt-workflow/SKILL.md |
| #NEW-14 | 🟢 P2 | 字体修补时机不精确 | Step 4 第 7 条加"修补时机：复制 CSS :root 到 HTML 时同步替换" | ppt-workflow/SKILL.md |
| #NEW-2 | 🟢 P3 | claude-design 与准备层搜索重复 | claude-design 加"搜索复用"段：读 data 护照或 content-inventory.md，已存在则跳过 | claude-design/SKILL.md |
| #NEW-8 | 🟢 P3 | 逐页 Skill() 重复加载 | ppt-workflow Step 6 改为"加载一次 Skill，逐页扫描"；ppt-visual-effects 触发时机同步描述为"加载一次后逐页应用" | ppt-workflow/SKILL.md, ppt-visual-effects/SKILL.md |
| #NEW-9 | 🟢 P3 | convert.py 门禁位置偏后 | 快速参考中在准备层后立即插入 Bash 门禁检查 | ppt-workflow/SKILL.md |

### 本次修复涉及文件

| 文件 | 操作 |
|------|------|
| `references/theme-tokens.md` | 替换中国 4 套索引表为完整 CSS :root（≈100 行新增） |
| `references/design-system.md` | 更新中国场景指向注释 |
| `references/layout-library.md` | 新建「选版式决策表」章节（≈55 行） |
| `ppt-workflow/SKILL.md` | 8 处编辑（Phase 1 前置/Step 1 分工/反模板时机/快速参考/任务路径/字体修补/快速路径/Step 6 措辞） |
| `design-assets/claude-design/SKILL.md` | 2 处编辑（前置检查/搜索复用） |

**总计**：5 个文件，14 项修复全部完成。

---

# 第四轮模拟（2026-08-10 修复后回归排查）

> 方式：在第三轮修复完成后重新走完整流程，重点验证修复是否引入新矛盾、是否有遗漏断点。

## 发现的问题（14 项，含 2 项上轮修复引入的回归）

| 编号 | 优先级 | 问题 | 修复方式 | 涉及文件 |
|------|-------|------|---------|---------|
| R4-1 | 🔴 P0 | **快速参考区块残留旧代码**——上轮重写时旧行未删干净，导致代码围栏提前关闭、"来源"行散落代码块外 | 删除残留的旧快速参考片段，围栏闭合 | ppt-workflow/SKILL.md |
| R4-2 | 🟡 P1 | **快速参考时序矛盾**——frontend-design 反模板审查标记在"设计决策层"块内（Phase 2 之前），但正文要求 Phase 1/2 完成后才审查 | 快速参考重组为「方案预览前（Phase 2 + 反模板审查）」块，Phase 2 先行 | ppt-workflow/SKILL.md |
| R4-3 | 🟡 P1 | **mbb 场景候选主题来源断掉**——Step 1 只说候选主题来自 claude-design 映射表，咨询场景无此来源 | Step 1 前置拆分为标准/咨询两条路径（咨询 = mbb-consulting + 映射表备选） | ppt-workflow/SKILL.md |
| R4-4 | 🟢 P2 | **反模板审查"审查通过后锁定"与 spec_lock 冲突**——spec_lock 规定用户选定（Step 2）才锁定，审查环节却提前锁定 | 改为"审查发现问题则替换，锁定发生在 Step 2" | ppt-workflow/SKILL.md |
| R4-5 | 🟢 P2 | **数据护照模板缺 research-done 字段**——claude-design 引用了该标记但模板中没有，agent 找不到 | 数据护照模板 + 各层填充责任表补 `research-done` 字段 | ppt-workflow/SKILL.md |
| R4-6 | 🟢 P2 | **layout-library 决策表重复（回归）**——上轮误判"决策表不存在"而新增重复表，实际原生就有完整表 | 删除新增的「选版式决策表（统一入口）」，保留原生表 | layout-library.md |
| R4-7 | 🟢 P2 | **决策表位置描述不准**——ppt-workflow 写"末尾章节"但原生表在 B 系列后 | 改为"位于 B 系列布局之后" | ppt-workflow/SKILL.md |
| R4-8 | 🟢 P2 | **ui-ux-pro-max 路径三处说法不一**——bootstrap 命令仍用旧绝对路径 D:/CLAUDEworkspace/work/ui_ux_pro_max | 统一为合集内相对路径 `<skill_dir>/scripts/uupm.py`，加首次初始化提示 | ui-ux-pro-max/SKILL.md |
| R4-9 | 🟢 P2 | **ui-ux-pro-max 首次初始化仍未入流程**（上轮 #NEW-13 只改了报告未改 SKILL） | ppt-workflow 设计决策层条目补"首次使用先跑 --fetch-data" | ppt-workflow/SKILL.md |
| R4-10 | 🟢 P2 | **theme-tokens 映射表注释"40 主题"过时**（实为 41） | 改为 41 套 | theme-tokens.md |
| R4-11 | 🟢 P2 | **README 两处"40 主题"过时** | 改为 41 主题（含 mbb-consulting） | README.md |
| R4-12 | 🟢 P3 | **axi-front-design "Step 2.5" 过时引用**（实为 Step 4） | 改为"ppt-workflow 执行层 Step 4（按布局库选版式）" | axi-front-design/SKILL.md |
| R4-13 | 🟢 P3 | **ppt-visual-effects "Step 4" 过时引用**（视觉增强实为 Step 6） | 触发时机改为 Step 6；"加载一次后逐页应用"语义对齐 | ppt-visual-effects/SKILL.md |
| R4-14 | 🟢 P3 | **ppt-visual-effects 触发语义与"加载一次"不一致**——内部写"每次被加载扫描当前页" | 顶部说明改为"加载一次后对每页逐一扫描" | ppt-visual-effects/SKILL.md |

## 修复涉及文件

| 文件 | 操作 |
|------|------|
| `ppt-workflow/SKILL.md` | 7 处编辑（快速参考清理/时序重组/mbb 路径/审查锁定语义/research-done/决策表位置/ui-ux-pro-max 初始化） |
| `references/layout-library.md` | 删除新增的重复决策表（回归修复） |
| `references/theme-tokens.md` | 1 处数字修正（40→41） |
| `README.md` | 2 处数字修正（40→41） |
| `axi-front-design/SKILL.md` | 1 处 Step 编号修正 |
| `ppt-visual-effects/SKILL.md` | 2 处触发时机语义修正 |
| `design-assets/ui-ux-pro-max/SKILL.md` | bootstrap 路径统一 + 首次初始化提示 |
| `design-assets/claude-design/SKILL.md` | 无修改（引用已成立） |

**总计**：8 个文件，14 项修复全部完成。第四轮模拟后工作流自洽。
