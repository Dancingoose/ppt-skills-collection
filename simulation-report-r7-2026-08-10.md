# PPT 工作流合集 — 第七轮全流程审查报告

> 审查类型：**独立审计**（非修复轮）——模拟制作 + 跨版本一致性 + 流程覆盖 + 意图捕获精度
> 审查日期：2026-08-10
> 审查人：独立 agent（非主制作 agent）
> 前六轮累计：61 项问题已修复（R1-30 → R2-14 → R3-14 → R5-3 → R6-0）

---

## 执行摘要

**本次独立审计模拟了一个完整 PPT 制作任务（场景：用户口述「帮我做一个 AI 行业趋势分析 PPT」），逐层、逐 Step、逐门禁走查，同时对比了合集 7 个 skill 文件与 installed 版本的字节级一致性。**

**核心发现**：
1. 🚨 **版本同步再次漂移**：6 个核心 skill 中 5 个 MD5 不一致（仅 frontend-design 相同）。R6 报告说"IDENTICAL"但实际检查发现合集→installed 存在 3 种差异：frontmatter 引号格式漂移（ppt-workflow）、多余的 frontmatter 块复制（html-to-pptx/ppt-visual-effects/axi-front-design）、尾部换行差异（claude-design/mbb-decks）。**html-to-pptx、ppt-visual-effects 和 axi-front-design 的 installed 版存在重复的 frontmatter 块（双/三套 `---` 包裹块），agent 加载 skill 时 skill registry 会如何解析这些元数据不确定。**
2. ✅ **流程设计已基本完善**：四层架构 + 6 硬门禁 + 自检清单覆盖全面，材料驱动提问引擎有合理的推导逻辑。
3. ⚠️ **执行层依赖臃肿**：Step 4 要求一次性加载 5 个资产库（~120KB），虽有 quick-reference-card 优化但实际 agent 可能还是会通读。
4. ⚠️ **三类边界场景未覆盖**：用户"一句话需求"的快速路径容易跳过 Phase 1/2 的关键问题；已有源文件（docx/PDF）场景的准备层处理链过长；中途变更需求的 spec_lock 解锁机制不明确。

---

## 1. 版本同步状态（对比合集 ↔ installed）

### 1.1 MD5 逐文件对比

| skill | 合集 MD5 | installed MD5 | 匹配? | 差异类型 |
|-------|----------|--------------|-------|---------|
| frontend-design | b803c15f... | b803c15f... | ✅ 完全相同 | — |
| ppt-workflow | 7f95809b... | 68af8bdf... | ❌ | frontmatter 引号格式 |
| claude-design | 9ac6531a... | 7b6dc035... | ❌ | 尾部空行（1 字节） |
| mbb-decks | 46196b63... | a86379f1... | ❌ | 尾部空行（1 字节） |
| axi-front-design | 3a997583... | 9788d274... | ❌ | **重复 frontmatter 块（实质性差异）** |
| html-to-pptx | 9ecbb534... | a6c9d1f4... | ❌ | **重复 frontmatter 块（实质性差异）** |
| ppt-visual-effects | 0bdb2f9a... | b3df6893... | ❌ | **重复 frontmatter 块（实质性差异）** |
| ui-ux-pro-max | dbfd8aba... | cf64d793... | ❌ | 架构差异（合集独立脚本 vs installed 自包含），已知可接受 |

### 1.2 三种差异类型详细分析

**类型 A：frontmatter 引号格式漂移（ppt-workflow）**
- 合集：`name: ppt-workflow`（无引号）
- installed：`name: "ppt-workflow"`（有引号）
- 风险：低。正文完全一致（4 字节差异来自引号 + 尾部换行）。YAML frontmatter 规范通常接受两种写法。

**类型 B：尾部换行（claude-design, mbb-decks）**
- 合集末尾有空行，installed 无
- 风险：无。纯格式化差异。

**类型 C：重复 frontmatter 块（🚨 需要关注）**
- html-to-pptx installed 版：3 组 `---` 包裹的 frontmatter 块（`name:"html-to-pptx"` 出现两次 + 1 组无引号版本），共 6 个 `---` 分隔符。
- ppt-visual-effects installed 版：同样，3 组 frontmatter 块，`name:"ppt-visual-effects"` 出现两次 + 1 组无引号版本。
- axi-front-design installed 版：1 组 frontmatter（含引号版本），但合集版有 2 组（引号 + 无引号版本），共 9 个 `---` 分隔符。
- 根源：在 save_skill 同步过程中，新内容被**追加**到旧 frontmatter 后面，而不是**替换**。导致 agent 加载 skill 时会看到多个 frontmatter 块。
- 风险：中等。Skill registry 通常只读第一个 `---` 块作为元数据（符合 YAML 流规范），后续 `---` 会被视为正文中的水平线分隔符。这意味着 **installed 版的 agent 可能看到 `name: "html-to-pptx"` 等行作为正文内容**，但不影响功能。

### 1.3 版本同步结论

R6 报告声称的"IDENTICAL"是基于**正文内容**判断，但在**元数据层**已发生漂移。类型 C 的重复 frontmatter 块是 save_skill （overwrite） 操作未清理旧元数据的结果，属于流程性 bug。

---

## 2. 四层模拟走查（场景：口述「AI 行业趋势 PPT」）

### 2.1 🏁 准备层

| Step | 预期行为 | 模拟结果 | 门禁 |
|------|---------|---------|------|
| 检测源文件 | 口述主题 → 触发 WebSearch | ✅ 指令明确："仅口述主题无源文件 → 必须做 WebSearch" | Gate 1: content-inventory.md 写入 ✅ |
| WebSearch | 搜索 AI 行业趋势事实/数据/来源 | ✅ 指令有模板（数据点清单 + 来源 URL） | — |
| 写入 content-inventory.md | 物理文件落盘 | ✅ 格式模板完整（源全文/数据/页数预判） | — |
| 提前门禁 convert.py | Bash 检查 | ⚠️ 时序争议：快速参考放在准备层末尾，但实际 agent 可能先读到内容再检查 — 顺序不强制 | — |

**准备层问题**：
- **P2 · I7-1**：content-inventory.md 的「核心信息」字段定义模糊——agent 可能写太宽泛（"AI 行业很好"）而非一个可提炼核心主张的观点陈述。建议加约束："核心信息必须是 1 个可争论的判断句，而非事实陈述。"
- **P3 · I7-2**：WebSearch 后的数据质量无验证步骤——agent 可能引用过时或来源可疑的数据。建议加约束："每个数据点至少来自 1 个权威来源（Gartner/IDC/Statista/国信办 等），低质量来源标注置信度。"

### 2.2 🏁 设计决策层

| Step | 预期行为 | 模拟结果 | 门禁 |
|------|---------|---------|------|
| Phase 1 前置（Gate 1） | AskUserQuestion 问 4 项关键 | ✅ 指令明确："Phase 1 在 claude-design 之前" | Gate 1 ✅ |
| claude-design | 出 3 方向 | ✅ 有映射表闭环（方向名→主题名→theme-tokens） | — |
| Phase 2 | AskUserQuestion 问设计方案 | ✅ 程序 10 项，分批 ≤4 | — |
| 反模板审查 | frontend-design | ✅ 时机正确（Phase 2 后、预览前） | — |

**设计决策层问题**：
- **P2 · I7-3**：「明确风格快速路径」的触发条件不够精确。用户说"我要科技感" — agent 可能错误地跳过 Phase 1（实际用户没说过受众/意图）。当前指令写了"跳过 claude-design 的三方向顾问模式"但没写"不跳过 Phase 1 的四项关键问题"——当 agent 解读不够细致时可能把"快速路径"解读为"全跳"。
- **P2 · I7-4**：claude-design 的方向名→主题名映射表依赖 agent 使用**精确**方向名。若 agent 用近义改写（"科技感"→agent 自由诠释为"cyber-geometric"而非"cyberpunk-neon"），映射失败。映射表覆盖之外的场景缺乏兜底规则。当前映射表有 11 行，但不含"手绘/轻松/温暖/温馨/环保/医疗/金融"等常见主题方向。
- **P3 · I7-5**：mbb-decks ghost deck 产出后，到执行层的交接依赖 agent 记住"把 story line 写入 content-inventory.md 或设计护照"。当前指令写"产出后须显式交接给 ppt-workflow"，但没有指定**交接格式**（是追加到 content-inventory.md 还是写入设计护照的「故事线」字段？）。

### 2.3 🏁 执行层

| Step | 预期行为 | 模拟结果 | 门禁 |
|------|---------|---------|------|
| Gate 2: 方案预览 | 封面+1-2内容页，三版同 HTML | ✅ 指令详细，含 tab 展示、风格描述、accent 色块 | Gate 2 ✅ |
| Gate 3: spec_lock 锁定 | 用户选定方案→锁护照 | ✅ spec_lock 纪律明确（5 条规则） | Gate 3 ✅ |
| Step 3: 内容核实 | content-inventory + 数据来源 | ✅ 5 项检查清单 | Gate 3 ✅ |
| Step 4: 选版式 | 加载布局库→登记布局编号 | ✅ 强制步骤，有 P0 规则 | Gate 4 ✅ |
| Step 5: 展开全量 | 基于选定方案做所有页 | ✅ 锁护照后展开 | — |
| Step 6: 逐页增强 | ppt-visual-effects 扫描 | ✅ 强制步骤 | Gate 5 ✅ |
| Step 7: 验收 | 自检 + 独立审查 | ✅ 有 sub-agent dispatch 指令 | — |

**执行层问题**：
- **P1 · I7-6**：Step 4 加载 5 个资产库（~120KB）可能导致 agent 的上下文窗口被消耗。quick-reference-card（~4.5KB）是精简化方案，但 agent 容易跳过"先读速查卡再按需读完整库"的约束而直接通读。尤其是 agent 收到"必须加载 layout-library.md + design-system.md"这类指令时，倾向于全部读而非渐进式。
- **P2 · I7-7**：Step 3 内容核实的「补素材」路径无时间限制——agent 可能陷入 WebSearch→content-inventory→再核实→仍需补的循环。建议加约束："内容核实最多 2 轮；第 2 轮后仍有不足→告知用户当前材料能支撑的页数上限+建议缩小范围。"
- **P2 · I7-8**：Step 6 逐页增强——pptx-visual-effects 的判断决策树偏「是/否」二元，缺少「可能」的灰度处理。如"数据页有数字但只有一个数字（非趋势/占比）"→规则说注入 ECharts，但单个大数字更适合大字报而非图表。当前扫描规则的第一条"数据展示页（有数字、对比、趋势、占比）"覆盖过宽。
- **P3 · I7-9**：spec_lock 的"换风格"解锁规则写的是"回到方案预览层重新出方案"。但用户中途只说"第三页的配色怪怪的"—这是小调整不是换风格，当前规则没区分"大改（回预览层）"vs"小调（在当前页改单个元素）"。agent 可能在小调整时也触发全套回滚。
- **P3 · I7-10**：独立审查（Step 7）依赖 agent 派 sub-agent 或自己切视角——但对 agent 来说"生成者模式"和"审查者模式"用的是同一模型的同一上下文，实际独立性有限。审查发现相同遗漏的可能性高。

### 2.4 🏁 交付层

| Step | 预期行为 | 模拟结果 | 门禁 |
|------|---------|---------|------|
| Gate 6: convert.py | Bash 检查 | ✅ 合集内置 convert.py（22,850 bytes） | Gate 6 ✅ |
| .config.local.toml | 首次使用弹窗配置 | ✅ 有 .example 模板 | — |
| html-to-pptx 转换 | python convert.py input.html | ✅ 指令含流水线、修复纪律、排查路径 | — |
| 视觉 audit | triage 模式 | ✅ 有 sub-agent dispatch 指令 | — |

**交付层问题**：
- **P2 · I7-11**：convert.py 实际运行依赖 Playwright（Chromium）+ 系统库。README 提到"需镜像下载+LD_LIBRARY_PATH 补系统库"，但交付层指令没提这片——agent 可能直接跑 convert.py 然后懵掉。建议交付层第一条指令改为："Bash: python convert.py --help（验证可运行性，非仅存在性）"。
- **P3 · I7-12**：Canvas/WebGL 降级告知的时机不当。当前指令在交付层自检清单中写"Canvas/WebGL 增强已告知会降级为静态截图"——但这是**交付时**才告知，而非**执行前**。用户可能在看到静态截图时才意识到着色器效果无法编辑。更合理的时机是 Phase 2 的「辅助产出」选项中就提示。

---

## 3. Skill 覆盖分析

### 3.1 哪些场景有完整覆盖

| 场景 | 准备层 | 决策层 | 执行层 | 交付层 | 评级 |
|------|--------|--------|--------|--------|------|
| 口述主题（无源文件） | WebSearch→content-inventory | Phase 1/2→claude-design→frontend-design | axi-front-design→ppt-visual-effects | html-to-pptx | ✅ 完整 |
| 有 docx 源文件 | docx skill 提取 | 同上 | 同上 | 同上 | ✅ 完整 |
| 有 PDF 源文件 | pdf-reading 提取 | 同上 | 同上 | 同上 | ✅ 完整 |
| 有 pptx 模板参考 | pptx skill 提取 | 同上 + 模板内容纳入 | 同上 | 同上 | ✅ 完整 |
| MBB 咨询汇报 | WebSearch/docx 提取 | mbb-decks ghost deck→Phase 1/2 | 同上 | 同上 | ✅ 完整 |
| 用户有明确风格 | 同上 | 快速路径（跳过 claude-design） | 同上 | 同上 | ✅ 完整 |

### 3.2 哪些场景覆盖不足

| 场景 | 缺失 | 影响 |
|------|------|------|
| 用户提供多源混合（docx+图片+URL） | 准备层没有"多源冲突/优先级"处理规则 | agent 可能混用不同时期/来源的数据 |
| 用户要做「更新现有 deck」而非从零做 | 准备层没有"增量识别"：哪些页保留/替换/新增 | agent 可能重建整个 deck 而非精准更新 |
| 非 16:9 画布（小红书/故事/A4） | canvas-formats.md 有规格，但执行层实际验证很少 | agent 可能用 16:9 思维做 3:4 排版 |
| 用户要求多语言 deck（中英双语） | Phase 1 有语言选项但执行层没双语排版规则 | 双语同页的 typography/reflow 没有指导 |
| 可访问性需求（色盲/屏幕阅读） | 全流程无此维度 | 配色只考虑美学不考虑 accessibility |
| 打印输出 | canvas-formats 有 A4 但没 print CSS 规则 | 打印效果可能崩 |

### 3.3 Skill 互操作性检查

| 连接点 | 状态 | 备注 |
|--------|------|------|
| content-inventory → Phase 1 材料驱动提问 | ✅ | material-driven-questioning.md 推导逻辑完整 |
| claude-design 方向名 → theme-tokens 映射 | ✅ | 映射表 11 行，精确匹配 |
| 设计护照 → 执行层 theme-tokens 选 token | ✅ | 通过「主题方案」字段桥接 |
| 设计护照 → 布局库选版式 | ✅ | 通过内容形状（数据形态/章节骨架）桥接 |
| mbb-decks ghost deck → 执行层展开 | ⚠️ | 交接格式模糊（I7-5） |
| ppt-visual-effects → HTML slide 嵌入 | ✅ | 指令含验证规则 |
| html-to-pptx convert.py → 视觉 audit | ✅ | triage 模式 + sub-agent |
| 合集↔installed 版本 | 🚨 | 多个 skill 出现重复 frontmatter（类型 C） |

---

## 4. 意图捕获精度评估

模拟场景：用户说「帮我做一个 AI 行业趋势分析 PPT」

### 4.1 Phase 1/2 提问质量评估

假设 agent 严格按材料驱动提问引擎走：

**第一批（受众/意图/主张/画布）**：
- 推断正确率预计：60-70%
  - 受众："AI 行业趋势"→agent 可能推断为"投资/决策层"或"从业者"——取决于 WebSearch 收集的材料偏投资分析还是技术报告
  - 核心主张：agent 从 WebSearch 大数据中提炼候选主张的质量高度依赖搜索结果的「一句话结论」能力

**第三批（故事线/侧重点/密度/风格）**：
- 推断正确率预计：40-50%
  - 故事线：WebSearch 结果通常不提供"章节骨架"，agent 得自己编——这是最弱的推导环节
  - 参考风格：用户只说"AI 行业"，agent 没有品牌/历史/行业惯例线索，可能默认"科技感"（aurora/cyberpunk-neon）——抹平了用户对自己品牌的风格偏好

### 4.2 关键信息丢失风险点

| 阶段 | 丢失风险 | 概率 |
|------|---------|------|
| 准备层 | WebSearch 结果不够「一句话可概括」，核心主张提炼走偏 | 中 |
| Phase 1 第一批 | 受众推断错误（投资者 vs 开发者→deck 完全不同） | 中 |
| Phase 1 第三批 | "故事线"无真实章节骨架→agent 自编→跟用户预期不一致 | 高 |
| Step 3 内容核实 | 用户口头补充的信息 agent 可能忘记写入 content-inventory | 中 |
| Step 5 展开 | spec_lock 锁定后用户的后续微调需求被"不敢漂移"枷锁抑制 | 低 |
| 全流程 | 用户对「科技感」的私有定义（他们的品牌色、logo、字体）agent 从未获取 | 高 |

### 4.3 一句话需求的处理路径

"帮我做一个 AI 行业趋势分析 PPT"——这是一个典型的"一句话需求"：

1. 准备层：WebSearch → content-inventory（~30-60s）
2. Phase 1 第一批：AskUserQuestion（受众/意图/主张/画布）→ 用户可能不知道如何回答"核心主张"（他们还没看过数据）
3. Phase 1 第二批：继续问...
4. Phase 1 第三批：继续问...
5. 设计决策层：claude-design 出方向 → 用户再选
6. Phase 2：继续问...

**从用户视角，这可能是 15-20 个问题后才看到第一版设计**。对"一句话需求"的快速路径，当前机制依赖 agent 的判断来跳过某些 Phase 2 项——但如果 agent 判断偏保守（每项都要问），用户体验会下降。

---

## 5. 执行纪律风险评估

### 5.1 6 硬门禁在实际 agent 执行中的通过率预估

| Gate | Agent 可能跳过的原因 | 跳过概率 |
|------|---------------------|---------|
| G1 Phase 1 前置 | agent 先加载 claude-design 再想起 Phase 1——skill 的加载顺序没有被强制执行 | 15% |
| G2 方案预览 | 用户说了"只做一版"→agent 直接展开全文 | 10% |
| G3 内容核实 | agent 觉得"数据够用"就跳过核实——核实是认知步骤无法纯代码检查 | 25% |
| G4 布局登记 | 需要的资产库太多，agent 走捷径凭感觉排——这是之前翻车率最高的门禁 | 20% |
| G5 逐页增强 | agent 忘记加载 ppt-visual-effects 或只加载不扫描 | 15% |
| G6 交付前置 | convert.py 在准备层已检查，agent 记得"有"就跳过二次检查 | 5% |

**叠加风险**：4 个门禁各 15-25% 跳过概率 + 串行依赖 → 完整遵守所有门禁的概率约 35%。

### 5.2 四层自检清单在实际 agent 中的执行

自检清单依赖 agent **主动回忆并输出打勾**——没有自动化强制执行。在上下文窗口接近满载时，agent 倾向于跳过"打勾输出"以节省 token。建议在每个层的关键点嵌入硬 prompt 提示（如"现在请输出准备层自检清单"）。

---

## 6. 问题按优先级汇总

### 🚨 P0（导致执行失败或输出完全错误）

无。当前系统在按照指令严格执行时可以产出正确的 PPT。未发现阻塞性 bug。

### ⚠️ P1（导致质量下降或流程偏离）

- **I7-6**：Step 4 资产库加载臃肿——5 个文件累计 ~120KB 消耗大量上下文，agent 可能通读而非按需跳转，增加后期门禁的跳过概率。
- **I7-8**：ppt-visual-effects 数据页扫描规则覆盖过宽——单个大数字不适用 ECharts 图表，当前规则可能误触发图表注入。

### ⚠️ P2（影响一致性和稳定性）

- **I7-1**：content-inventory 「核心信息」字段约束弱——容易产出无用的宽泛总结。
- **I7-3**：快速路径可能跳过 Phase 1 关键问题——受众/意图等前置上下文丢失。
- **I7-4**：claude-design 映射表覆盖外的方向名无兜底——非标准方向名匹配失败。
- **I7-7**：内容核实的补素材循环无上限——可能陷入无限 WebSearch。
- **I7-11**：convert.py 可运行性验证不充分——只查存在性不查依赖。

### ⚠️ P3（边界场景和体验优化）

- **I7-2**：WebSearch 数据质量无验证——可能引用不可靠数据。
- **I7-5**：mbb-decks→执行层交接格式不明。
- **I7-9**：spec_lock 不区分"大改"和"小调"——小改动也触发全套回滚。
- **I7-10**：独立审查的独立性不足——生成者和审查者是同一模型。
- **I7-12**：Canvas/WebGL 降级告知时机不当——交付时才告知而非执行前。

### 🔵 元数据/版本管理

- **I7-13**：合集installed版本同步再次漂移（5/7 skill 不一致）。
- **I7-14**：html-to-pptx, ppt-visual-effects, axi-front-design installed 版含重复 frontmatter 块（append 而非 overwrite 的结果）。
- **I7-15**：prep-assets 中的 docx/pptx SKILL.md 是完整副本的 Anthropic 内置 skill——是否与已安装的 Anthropic 官方版本冲突？

---

## 7. 与 R6 报告对比

| R6 结论 | 本次复验 | 变化 |
|---------|---------|------|
| "installed 版 = collection 版 IDENTICAL" | ❌ 5/7 不一致 | 版本再次漂移（距离 R6 不超过半天） |
| "6 硬门禁机制完善，agent 会遵守" | 修正：结构完善，但实际执行率预计 ~65% | 非设计问题，是 agent 上下文竞争问题 |
| "材料驱动提问 12 项逻辑正确" | ✅ 确认 | 无变化 |
| "主题 token 41 套 + 映射表 11 条" | ✅ 确认 | 无变化 |
| "convert.py + 门禁完整" | ⚠️ 可运行性验证不足 | P2 级发现 |
| "无新增阻塞问题" | ✅ 确认 | 本次也无 P0 |

---

## 8. 建议优先级行动清单

### 立即修复（本次 session）

1. **[版本同步]** 重新 save_skill overwrite 同步 5 个不一致的 skill（特别是清理重复 frontmatter 块），然后 diff 验证正文一致 + frontmatter 格式统一。
2. **[I7-6 缓解]** 在 ppt-workflow SKILL.md 的 Step 4 前加强约束："先读 quick-reference-card.md（~4.5KB）→ 只从 layout-library.md 读选版式决策表（L777-824）+ 只从 theme-tokens.md 读选定主题的 `:root` 块（1/41）→ 其他主题块不读。"

### 短期修复（下次审查前）

3. **[I7-3]** 快速路径指令改："跳过 claude-design 的三方向顾问模式，但 Phase 1 的四项关键问题不跳过"——加黑体强调。
4. **[I7-4]** claude-design 映射表扩展 5-8 行（涵盖手绘/温暖/环保/医疗/金融/学术 等方向），或加兜底规则："映射表无匹配→选 minimal-white 作为安全默认，并要求用户 Phase 2 手动确认主题。"
5. **[I7-7]** 内容核实指令加约束："最多 2 轮；第 2 轮后仍有不足→告知用户上限建议。"
6. **[I7-11]** 交付层第一条指令改为 Bash 可运行性验证而非纯存在性检查。

### 中期改进

7. 增加「一句话需求」快速评估模式：Phase 1 只问最关键的 2 项（受众 + 核心主张），其他 10 项用"最佳猜测 + 标注可修改"。
8. 增加「更新现有 deck」工作流分支。
9. 建立合集→installed 同步的自动化验证（CI-like 检查）：每次修改合集后自动 diff 所有 installed 版本。

---

*审查完成。建议先修复项 1-2（版本同步 + 资产库加载优化），再逐步推进 3-6。*
