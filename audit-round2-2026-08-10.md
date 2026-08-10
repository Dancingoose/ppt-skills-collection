# PPT 工作流合集第二轮审查：流程逻辑与 skill 参与度

> 审查方式：模拟"用户说'做个 PPT'"→遍历四层架构每一步，找逻辑矛盾和 skill 缺位
> 审查日期：2026-08-10（第一轮修复后）


## 问题 1 · 两阶段询问在三个地方各自定义了不同规则

**涉及文件**：`ppt-workflow/SKILL.md` Step 1（3 项强制问） vs `axi-front-design/SKILL.md` Step 1（Phase 1 九项 + Phase 2 十项）

ppt-workflow Step 1 说执行层第一步要问"语言/字号强度/风格版本数"三项。axi-front-design Step 1 有完整的 Phase 1（9 项沟通契约）+ Phase 2（10 项设计方案），共 19 项。这两套并存会导致 agent 困惑——是按 ppt-workflow 问 3 项，还是按 axi-front-design 问 19 项？

更重要的是：**axi-front-design Phase 1 问的"受众/意图/核心主张/画布"是设计决策层应该填充的字段**（数据护照分配表中明确写"设计决策层填充画布/受众/沟通意图"）。这意味着真实流程中，这些字段要到执行层才被问出来，而不是在进入执行层之前就已经填好——数据护照的"各层填充责任"表与实际执行顺序错位。

另外，claude-design 也有自己的提问流程（核心原则 1：先问后做，至少 4 个问题），但没有引用 axi-front-design 的两阶段框架。如果设计决策层加载 claude-design 先问了一轮，再进入执行层加载 axi-front-design 又用 Phase 1/2 问一轮——用户会被反复问同类问题（风格方向、页数、受众等）。

**建议**：把所有的"询问用户"集中到 axi-front-design 的 Phase 1/2 框架中，作为唯一的提问入口。ppt-workflow 只做一个引用（"执行层第一步 = axi-front-design Phase 1/2"），不自己定义问题清单。claude-design 在设计方向顾问模式下也可以引用这个框架，但不单独开一轮新提问。


## 问题 2 · 预览 HTML 的颜色/字体从哪来——Step 2 在 Step 2.5 之前，但没有 token 来源

**涉及文件**：`ppt-workflow/SKILL.md` L127-131 vs L133-143

ppt-workflow 的 Step 顺序是：Step 2 "出方案预览（封面+1-2内容页，三版tab切换）" → Step 2.5 "加载布局库+设计系统选版式". 但做 Step 2 的预览 HTML 时，每套方案已经需要颜色（`:root` CSS 变量）、字体、圆角/阴影——这些信息来自 Step 2.5 要加载的 `design-system.md` + `theme-tokens.md`。

逻辑矛盾：**Step 2 需要 Step 2.5 的输出才能执行，但 Step 2.5 定义在 Step 2 之后**. 实际做法是 agent 自己领会"先读 design-system 和 theme-tokens，选 3 个候选主题，再建预览 HTML"——但这个领会不在任何文件的书面步骤中。

**建议**：把"读取 design-system.md + theme-tokens.md，选定 3 个候选主题名"提升为 Step 2 的前置条件。或者把 Step 2.5 拆成两部分：2.5a（读设计系统选主题，在预览前做）和 2.5b（按布局库选版式，在预览后/展开前做）。


## 问题 3 · 准备层产出（源内容全文）在设计护照中没有承载字段

**涉及文件**：`ppt-workflow/SKILL.md` L43（准备层产出） + L51-65（设计护照模板）

准备层产出是"源内容全文 + 图片资源清单 + 核心信息一句话总结"。但设计护照模板只有 8 个字段（主题/受众/意愿/画布/页数/颜色/字体/风格/品牌词/源素材路径），不包含"源内容全文"的实际内容载体。

从 docx 提取的一大段文本、从 pdf 提取的结构化内容——这些是无法塞进护照模板的大块数据。它们去哪里了？目前依赖 agent 在内存中持有，但上下文窗口压缩后可能丢失。

这对 Step 3.5（内容核实）非常重要——你需要对比源内容与承诺页数。如果源内容已在之前的上下文压缩中丢失，Step 3.5 的核实就变成空的。

**建议**：在准备层产出时，写一个独立的 `content-inventory.md` 文件（如 `D:\CLAUDEworkspace\work\<任务名>\content-inventory.md`），包含：源内容全文（从 docx/pdf 提取）、图片清单（路径+描述）、每段落/章节的核心要点。设计护照中加一个字段 `content-inventory: [文件路径]`。执行层 Step 3.5 读这个文件做核实。


## 问题 4 · mbb-decks 作为独立 skill 被触发时，四层流水线不会启动

**涉及文件**：`mbb-decks/SKILL.md` → `ppt-workflow/SKILL.md`

场景：用户说"给我做个咨询级 market entry deck"。mbb-decks 触发（因为它匹配"咨询级 deck / 市场进入"关键词），但它自己的 SKILL.md 只负责产出 ghost deck，然后说"交接给标准流水线"。

问题：如果 ppt-workflow 没有同时被触发（因为 mbb-decks 抢先匹配了用户意图），那么准备层、执行层、交付层都不会运行。ghost deck 产出后没有后续步骤跟进——它只是一个 markdown 文本，不会自动变成 HTML + PPTX。

**建议**：在 mbb-decks SKILL.md 末尾"交付给执行层的交接规则"中加一条：**产出 ghost deck 后，必须显式加载 `Skill("ppt-workflow")` 或告知用户"故事线已完成，接下来走标准流水线渲染为完整 deck"**。或者在 ppt-workflow 中加一个触发补丁：检测到 mbb-decks 产出 ghost deck 后自动介入。


## 问题 5 · Step 3.5（内容核实）在 Step 2.5（选版式）之后，但选版式需要核实后的内容形状

**涉及文件**：`ppt-workflow/SKILL.md` L135-143（Step 2.5） vs L154-163（Step 3.5）

Step 2.5 要求"每页先确定内容形状（数据 or 论断？几项对等？有无时间轴？有无图片？），为每页登记布局编号". 但 Step 3.5 才做"源素材是否足以支撑承诺的页数和要点？不够 → 补内容". 这意味着：**你在不知道内容是否足够的情况下，已经基于"假设的内容"选定了所有页面的版式编号**。如果 Step 3.5 发现内容不够，需要补内容、改页数、甚至拆页，之前登记的布局编号就全废了。

正确的顺序应该是：先核实内容是否够（3.5）→ 再根据核实后的内容形状选版式（2.5）→ 再展开页面（3）。

**建议**：交换 Step 2.5 和 Step 3.5 的位置。或者把 3.5 的内容核实作为 2.5 的前置条件明确写进 2.5 的开头："在执行本步骤前，必须先完成内容核实（见 Step 3.5）"。


## 问题 6 · 多套主题中 --font-display 含 Inter 违反合集反俗套规则

**涉及文件**：`references/theme-tokens.md`

约 8 套主题的 `--font-display` 显式包含 Inter（minimal-white、corporate-clean、pitch-deck-vc 等），另有 ~20 套主题的 `--font-display: var(--font-sans)` 且 `--font-sans` 包含 Inter。而合集反俗套规则明确禁"标题字体用 Inter/Roboto 默认"。

虽然 Inter 在这些主题中是 font-sans（body）的一部分，但当 font-display 回退到 font-sans 时（很多主题就是这样），**标题实际上会渲染成 Inter**——这直接违反了合集的禁止项。

**建议**：不要在 theme-tokens.md 中修改上游原始 token（那是数据来源，保持一致有利于未来更新）。但需要在两个地方加注释：
1. theme-tokens.md 开头加"⚠️ 反俗套注意"提醒：某些主题的 --font-display 可能回退到 Inter，执行层在写入 HTML 时应检查并替换字体栈
2. ppt-workflow Step 2.5 加一条检查："如果选定主题的 --font-display 含 Inter/Roboto，执行层替换为 'Noto Sans SC', 'Microsoft YaHei', sans-serif 或主题目录中列出的有性格字体"


## 问题 7 · html-to-pptx 的 CJK 自动种子 Noto 与 MBB 主题的 Georgia+Calibri 冲突

**涉及文件**：`html-to-pptx/SKILL.md` vs `references/theme-tokens.md` 「mbb-consulting」

html-to-pptx 的逻辑是"HTML 含 CJK 字符自动种子 Noto Sans SC + Noto Serif SC". 但 mbb-consulting 主题的 font-sans 是 Calibri，font-display 是 Georgia。在导出 PPTX 时，如果 convert.py 自动嵌入 Noto 字体，中文字符会用 Noto 渲染而非 Calibri 的 CJK fallback，可能导致字体风格不一致。

**建议**：在 mbb-decks 的交接规则中追加一条："导出 PPTX 时，如果有 CJK 内容，执行层显式指定中文字体为 Microsoft YaHei（与 Calibri/Georgia 风格较匹配的无衬线中文字体），并告知 html-to-pptx 跳过自动种子（或手动指定字体映射）"。


## 问题 8 · Shadertoy 封面着色器和"纯文字排版页不加"冲突

**涉及文件**：`ppt-visual-effects/SKILL.md` 决策树 + 约束规则表

Shadertoy 触发条件："封面/过渡页/CTA 页（深色背景）". 约束规则："明确不触发：白底纯文字页、已经有复杂排版的对比页、附录/引用页".

冲突场景：一个 dark hero 封面（A1/B1），内容是主标题 + 副标 + 作者信息——**它是深色封面（触发 Shadertoy），同时又是纯文字排版页（应该不加）**. 目前的规则没有优先级，agent 会随机选择其中一条。

**建议**：在 Shadertoy 触发条件中加细化：深色封面若有全幅背景图/品牌底色则注入着色器做增强，若只有大号文字+留白则跳过。或者将"纯文字排版页"重新定义为"主内容区域文字占比 > 80% 且无其他视觉元素".


## 问题 9 · 四层架构缺少"用户只给了口头主题，没有任何文件"的标准路径

**涉及文件**：`ppt-workflow/SKILL.md` 准备层

准备层表格覆盖了 docx / pdf / pptx / 图片 / 网页 / epub 等各种源格式，最后一项是"用户口述主题 → 直接记录，进入第 2 层". 这是最常见的场景（"帮我做个 AI 行业趋势 PPT"），但处理过于草率。

"直接记录"意味着：没有源内容全文（问题 3）、没有数据来源、没有图片。这样的 deck 在 Step 3.5 内容核实时会发现"素材不足以支撑页数和要点"，然后需要 agent 自己去做事实调研（web search）或补素材——但这步在四层中完全没有定义位置。搜索调研应该在哪层？准备层？设计决策层？执行层？

**建议**：准备层"用户口述主题"分支展开为：① 记录主题 ② WebSearch 收集事实/数据/来源 ③ 写入 content-inventory.md ④ 推定页数和内容形状 ⑤ 进入第 2 层。把"调研搜索"正式纳入准备层。


## 问题 10 · design-system.md 和 theme-tokens.md 的内容重叠，两个文件都声称自己是"主题 token 的来源"

**涉及文件**：`design-system.md` vs `theme-tokens.md`

design-system.md 有 4 套中国场景的完整 token 表（party-gov-red 等），theme-tokens.md 也有这些 token（但以注释方式引用 design-system）。两份文件各自维护部分主题 token——未来修改时需要同步改两个地方。

**建议**：把 design-system.md 中 4 套中国场景的详细 token 表移到 theme-tokens.md（与其他 37 套主题同样的 CSS `:root` 格式），design-system.md 只保留目录 + 一句话描述 + 指向 theme-tokens.md 的链接。统一主题 token 的单一事实来源。


## 优先级排序

| 优先级 | 问题 | 核心矛盾 |
|-------|------|---------|
| 🔴 P0 | #1 三处询问定义冲突 | agent 不知道该问 3 项还是 19 项，用户被重复提问 |
| 🔴 P0 | #3 无内容承载机制 | 源内容跨上下文可能丢失，Step 3.5 成空 |
| 🔴 P0 | #5 Step 顺序逻辑错误 | 选版式在内容核实之前——登记了废的布局编号 |
| 🟡 P1 | #2 预览 token 来源缺失 | Step 2 需要 token 但加载 token 在 Step 2.5 |
| 🟡 P1 | #4 mbb-decks 独立触发无后续 | ghost deck 产出后无人接管 |
| 🟡 P1 | #9 口述主题无调研路径 | 最常见的场景反而是最不完整的 |
| 🟢 P2 | #6 font-display含Inter | 约28套主题违规，但可在执行层修补 |
| 🟢 P2 | #7 CJK字体与MBB主题冲突 | 影响面窄（仅mbb+中文场景） |
| 🟢 P2 | #8 着色器vs纯文字冲突 | 边缘场景，影响不超过2页/deck |
| 🟢 P2 | #10 两份文件维护重叠tok | 维护性问题，不影响运行 → **已修复** |

## 修复记录（2026-08-10，全部 10 项已完成）

| 编号 | 修复方式 | 涉及文件 |
|------|---------|---------|
| #1 三处提问冲突 | ppt-workflow Step 1 改为"统一用 axi-front-design Phase 1/2 框架"；claude-design 加"PPT 场景不单独提问，通过映射表并入 Phase 2" | ppt-workflow/SKILL.md, claude-design/SKILL.md, axi-front-design/SKILL.md |
| #2 预览 token 来源缺失 | ppt-workflow Step 1 加前置："先加载 design-system.md + theme-tokens.md，确定 3 个候选主题名" | ppt-workflow/SKILL.md |
| #3 无内容承载机制 | 新建 content-inventory.md 模板；准备层产出写入该文件；口述主题时准备层先做 WebSearch | ppt-workflow/SKILL.md |
| #4 mbb 独立触发无后续 | mbb-decks 末尾加「触发后续步骤」：显式告知用户 + 加载 ppt-workflow | mbb-decks/SKILL.md |
| #5 Step 顺序错误 | 重排：Step1 预览 → Step2 锁定 → Step3 内容核实 → Step4 选版式 → Step5 展开 → Step6 增强 → Step7 验收 | ppt-workflow/SKILL.md |
| #6 font-display 含 Inter | theme-tokens.md 开头加反俗套注意；ppt-workflow Step4 加字体检查规则 | theme-tokens.md, ppt-workflow/SKILL.md |
| #7 CJK+MBB 冲突 | mbb-decks 交接规则加第 7 条"CJK 字体映射" | mbb-decks/SKILL.md |
| #8 着色器 vs 纯文字 | Shadertoy 触发条件加例外："主内容区文字占比 > 80% 时跳过" | ppt-visual-effects/SKILL.md |
| #9 口述无调研路径 | 准备层"用户口述"分支展开为 WebSearch→content-inventory→推定页数 | ppt-workflow/SKILL.md |
| #10 两份文件重叠 token | 4 套中国场景 token 表从 design-system.md 删除，只保留视觉规则，标注"完整值见 theme-tokens.md" | design-system.md |
