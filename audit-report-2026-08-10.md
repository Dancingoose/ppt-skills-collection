# PPT 工作流合集审查报告

> 审查范围：`D:\CLAUDEworkspace\work\ppt-skills-collection\` 全部 16 个文件
> 审查日期：2026-08-10
> 四层架构：准备层 → 设计决策层 → 执行层 → 交付层

---

## P0 · 阻断级（不改会导致功能失效或明显错误）

### 1. ppt-visual-effects 引用的 CSS 变量在设计系统中不存在

**文件**：`ppt-visual-effects/SKILL.md` L67, L248

效果模块要求颜色"必须使用设计系统的 CSS 变量（--navy, --coral 等）"，但 `references/design-system.md` 实际定义的 token 名是 `--accent`、`--accent-2`、`--accent-3`、`--bg`、`--text-1` 等，从未定义 `--navy`、`--coral`。这两个名字可能是 Shadertoy 着色器模板示例里的硬编码，跟设计系统完全对不上——穿着色器颜色一致的效果无法实现。

**建议**：把 ppt-visual-effects 里 `--navy, --coral` 改成 `--accent, --accent-2`，并在效果生成指令里明确"从当前主题的 :root CSS 变量读取颜色"。

### 2. html-ppt 的 36 套主题只有目录名，没有实际 token 值

**文件**：`references/design-system.md` L115-176

中国场景 4 套（party-gov-red / academic-defense / courseware-blue / handdrawn-explainer）有完整的 token 定义表（bg/bg-soft/surface/border/text-1/2/3/accent-1/2/3/radius/shadow/font-sans）。但 html-ppt 的 36 套主题只列了分类+名字+一句话气质描述，没有任何 token 值。

这意味着设计决策层选定 `swiss-grid` 或 `corporate-clean` 主题后，执行层 axi-front-design **无法直接用**——它不知道 `swiss-grid` 的 `--accent` 是什么 hex，全靠自己猜。整个 token-driven 换肤机制的根基缺了一半。

**建议**：要么补齐 36 套主题的 token 值（从上游 html-ppt-skill 的 references/themes.md 提取），要么把所有 40 套变成可实际落地的 CSS；否则仅 4 套中国场景能直接用。

### 3. convert.py 缺失且无兜底

**文件**：`html-to-pptx/SKILL.md` L21，`README.md` L88-94

html-to-pptx 的核心功能依赖 `convert.py` 脚本，但合集只含 SKILL.md，脚本需用户手动 git clone 上游仓库到本地。README 里有说明，但三条路径都没有兜底：

- ppt-workflow 第 4 层只说"用户要 .pptx → 用 html-to-pptx 转换"，不提配置
- 如果用户跟完完整四层后才发现无法导出 PPTX，浪费整个执行流程

**建议**：在 ppt-workflow 第 4 层加入门禁检查——"html-to-pptx/convert.py 是否存在？不在则告知用户先下载"——不等到最后一刻才发现。

---

## P1 · 配合级（两层之间衔接断档，执行层会走偏）

### 4. claude-design 10 种设计语言 → design-system 40 主题没有映射

**文件**：`claude-design/SKILL.md` L237，`references/design-system.md`

claude-design 产出"3 个差异化方向"，用的是 10 种设计语言的词汇（"瑞士编辑式""包豪斯几何""Kenya Hara 留白"）。这些方向写进数据护照后，执行层需要从 design-system 的 40 主题中选一套落地。但两者之间没有任何对照表。"瑞士编辑式"对应 swiss-grid 还是 corporate-clean？"杂志编辑式"对应 magazine-bold 还是 editorial-serif？全凭执行层自己猜。

**建议**：建一个对照表（不到 20 行），如：

| 设计语言 | 推荐主题 |
|---------|---------|
| 瑞士编辑式 | swiss-grid / corporate-clean |
| 包豪斯几何 | bauhaus / neo-brutalism |
| Kenya Hara 留白 | japanese-minimal / minimal-white |
| ... | ... |

放在 design-system.md 或 claude-design 末尾。

### 5. mbb-decks 的视觉系统没有接入 design-system token

**文件**：`mbb-decks/SKILL.md` L62-74，`references/design-system.md`

mbb-decks 定义了完整的视觉规范（`#051C2C` 海军蓝、`#2251FF` 电光蓝、Georgia、Calibri、`#FFFFFF` 白底），但 `#2251FF` 不在 design-system 任何主题的 accent 色里。当 mbb-decks 产出 ghost deck 后交给 axi-front-design 渲染时，执行层需要把这些硬编码的颜色转成 design-system token，没有现成的对照。

**建议**：要么在 design-system 里新增 `mbb-consulting` 主题（把 mbb 的颜色写入 token），要么在 mbb-decks SKILL.md 末尾加一段"交付时告诉执行层：用 corporate-clean 主题，覆盖 --accent 为 #2251FF"。

### 6. axi-front-design 独立加载会漏掉 Step 2.5（选版式+读设计系统）

**文件**：`ppt-workflow/SKILL.md` L133-143，`axi-front-design/SKILL.md`

Step 2.5（"按布局库选版式，登记布局编号"）是 ppt-workflow 的执行层强制步骤，但在 axi-front-design 自身的 SKILL.md 中，对应的工作流是 Step 1→2→3→4→5→6，没有任何"Step 2.5"的存在。axi-front-design 的幻灯片专项部分提到"布局必须来自合集布局库"，但用的措辞是"推荐"而非 ppt-workflow 里的"强制"。

如果某个场景下 axi-front-design 被单独加载（不走 ppt-workflow），Step 2.5 就不会执行。

**建议**：在 axi-front-design 的幻灯片专项里加一个明确的强制性步骤节点，和 ppt-workflow 的 Step 2.5 保持一致，措辞对齐为"生成任何内容页之前，必须加载 references/layout-library.md + references/design-system.md"。

### 7. frontend-design 的位置和责任模糊

**文件**：`ppt-workflow/SKILL.md` L91-112

ppt-workflow 给 frontend-design 分配了两个角色：
- 设计决策层"所有场景"列出它，"全程辅助，确保每个选择有原因"（L98，全程顾问）
- 设计决策层末尾单独有一节"反模板审查检查点"（L102-112，一次性门禁）

但 frontend-design 的 SKILL.md 是面向通用 web 设计的英文文档，没有任何 PPT 工作流的意识。它不知道设计护照、不知道 10 种设计语言、不知道布局库。当加载它做"反模板审查"时，它要审查什么？审查的依据是什么？审查后的替代方案给谁？这些都是空白。

**建议**：要么为 frontend-design 写一个面向 PPT 场景的补充指令（小段追加在 ppt-workflow 里，说明审查点），要么把这个角色合并进 claude-design（它已有 slop 防护），删掉重复的一道门禁。

---

## P2 · 数据/配置级（不影响功能但会出错）

### 8. font 禁用列表分散，默认值有冲突

三个地方对字体说了不同的话：
- `design-system.md` L39-47：默认 token 用 `Inter` / `Playfair Display`，但附注"合集反俗套规则要求标题禁用 Inter/Roboto"
- `axi-front-design/SKILL.md` L49：反俗套清单包含"老掉牙的字体：Inter、Roboto、Arial、Fraunces、系统字体"
- `ppt-workflow/SKILL.md` L217：禁止项包含"标题字体用 Inter/Roboto 默认"

默认 token 值（Inter）本身就在反俗套清单里——相当于设计系统自己违规。新手只套默认 template 时会直接踩中。且 mbb-decks 推荐 Georgia+Calibri、中国场景用 Source Han Sans SC——整整 4 套不同的字体体系没有统一管理。

**建议**：把默认 `--font-sans` 从 `'Inter','Noto Sans SC',sans-serif` 改成至少不带 Inter/Roboto 的安全字体（如 `'Noto Sans SC','Microsoft YaHei',sans-serif`）。同时在 design-system.md 开篇加一张"可用字体白名单"。

### 9. 数据护照的颜色字段与 design-system token 不是同一套模型

**文件**：`ppt-workflow/SKILL.md` L51-65

数据护照定义了三个颜色字段：主色 `#XXXXXX`、强调色 `#XXXXXX`、底色 `#XXXXXX`。但 design-system 走了语义 token 模型：`--accent`、`--accent-2`、`--accent-3`、`--text-1/2/3`。

设计决策层填写数据护照时用的是离散 hex 值，执行层实现时走的是语义 token。两者之间没有翻译规则——是执行层把 hex 覆盖进 token，还是从 hex 挑主题？这条链路是从"设计意图"到"CSS 实现"的关键桥，目前靠默认。

**建议**：在数据护照模板里增加一个字段"主题方案"（已在模板里有了），并明确规则：**主题方案的 token 值优先于主色/强调色/底色的 hex 值**；如果用户特别指定了品牌色 hex，则执行层覆盖主题的三个 accent token。

### 10. layout-library.md 和 design-system.md 的字号体系不一致

layout-library.md 开头自带一套设计 token 基线（H1 88-120px、H2 64-80px、H3 32-44px、正文 22-28px），强调"用布局库的字号体系"。design-system.md 也有一套排版体系（h1.title 72px、h2.title 54px 等），但附注"合集 1920×1080 幻灯片必须用布局库的字号体系"。

两份文档各自声明了自己的字号定义——新手不知道该听谁的，两份都读容易混淆。

**建议**：把 design-system.md 排版体系里的字号值删掉（只保留语义类名如 `.kicker`、`.lede`），字号完全由 layout-library 定义。design-system 只负责 token（颜色/圆角/阴影/字体族），不负责字号。

---

## P3 · 体验级（不影响正确性但增加摩擦）

### 11. canvas-formats.md 说"非 16:9 画布时须按本文件的布局原则调整"，但没给出具体调整规则

canvas-formats.md L7 说布局库的 41 布局默认 16:9，非 16:9 时需调整。但实际只给了一张"字号基准随画布缩放"的表——没有 layout 级别的调整指导。比如小红书 3:4 画布用 A4 左文右图，左右比例怎么调？B1 封面在故事 9:16 上怎么变形？这些都是空白。

### 12. ppt-visual-effects 的 shader-web-background@latest 是脆弱 CDN 引用

使用 `@latest` 意味着上游发布 breaking change 时，所有已生成的 HTML 文件都可能坏掉。建议锁版本号。

### 13. ui-ux-pro-max 脚注路径与合集存放位置不一致

SKILL.md 提到数据目录 `<skill_dir>/data/`，但实际上 `design-assets/ui-ux-pro-max/` 下面只有 `scripts/uupm.py` 和 `SKILL.md`，没有 data 目录（数据靠 `--fetch-data` 下载）。且 SKILL.md 提到的多个路径（`D:/CLAUDEworkspace/work/ui_ux_pro_max/`、`<skill_dir>/scripts/uupm.py`）与实际合集位置（`ppt-skills-collection/design-assets/ui-ux-pro-max/`）不一致，新手会迷惑。

### 14. image-generation.md 与 ppt-visual-effects 的数据页图表边界未定义

image-generation 产出"真正信息图"，ppt-visual-effects 产出 ECharts 交互图表。但数据页面既可以用静态信息图（image-generation 管线），也可以用交互式 ECharts（ppt-visual-effects 管线）。什么情况下走哪条路？目前只有一句"两者互补"，没有决策规则。

### 15. ppt-workflow 流程图与文字描述有歧义

流程图第 3 层把 ppt-visual-effects 画在 axi-front-design 下面，箭头是"↓"，暗示自动介入。但正文 Step 4 说是"显式调用——必须对每一页加载 Skill 再做判断"。流程图和文字给执行层的指令不一致：是自动介入还是手工逐页调用？

### 16. html-to-pptx 的首次配置步骤 ppt-workflow 未提及

html-to-pptx SKILL.md 要求"第一次 convert 前需确认两条偏好（fonts.auto_install + audit.mode）"，但 ppt-workflow 第 4 层没有转发这个要求。用户首次导出时会遇到意料之外的询问弹窗。

### 17. mbb-decks 图表族与 ppt-visual-effects 的 ECharts 选择逻辑不统一

mbb-decks 给出了"行动标题动词 → 图表族"对照表，ppt-visual-effects 给出了"数据展示页 → ECharts 图表类型"对照表。两套选图逻辑可以互相覆盖同一页——如果 ghost deck 标注了 waterfall，ppt-visual-effects 判断该用玫瑰图，谁说了算？

### 18. anti-slop 规则在四个文件中重复但不完全一致

四份文件各自维护了反俗套清单：
- ppt-workflow 禁止项 (L212-226)
- axi-front-design 第 4 条 (L45-52)
- claude-design 硬性工艺规则 (L205-206)
- layout-library 反 AI 俗套清单 (L1049-1061)

每条清单的条目不完全相同。layout-library 最完整（13 条），ppt-workflow 次之（14 条），axi-front-design 偏短（8 条）。如果有新规则要加，可能需要改 4 个地方。

### 19. 中国场景 4 套主题禁"编造官方标志/机构名"，但 mbb-decks 的引用格式可能触发

party-gov-red 视觉规则明确禁编造机构名。但 mbb-decks 的引用格式要求"来源用权威机构"。如果用户做党政汇报用 mbb 的故事线方法论，轴会出现"引用某官方机构数据"——这虽然不违规，但两个规则放在一起容易让执行层困惑：数据引用和机构标志是两个不同层面的东西，但规则措辞有交集。

### 20. references 文件夹的相对路径假设依赖合集整体复制

ppt-workflow 用 `Read references/layout-library.md` 这样的相对路径。如果合集被拆开安装（skill 文件在 Claude Desktop skills 目录，references 在别处），这些 Read 就会失效。README 有提醒"确保 references/ 一起复制"，但没有机制在运行时校验文件是否存在。

---

## 优先级排序建议

| 优先级 | 编号 | 问题 | 影响 |
|-------|------|------|------|
| 🔴 立即修 | #1 | CSS 变量名不匹配 | 色器/图表颜色无法匹配设计系统 |
| 🔴 立即修 | #2 | 36 主题无 token 值 | 大部分主题无法实际使用 |
| 🔴 立即修 | #3 | convert.py 缺失无兜底 | 交付链断裂 |
| 🟡 尽快修 | #4 | 设计语言→主题无映射 | 决策到执行衔接断层 |
| 🟡 尽快修 | #5 | mbb 视觉未接入 token | mbb 产出无法无缝渲染 |
| 🟡 尽快修 | #6 | Split 2.5 强制步骤不完整 | 独立加载漏步骤 |
| 🟡 尽快修 | #7 | frontend-design 角色模糊 | 重复审查无实际效果 |
| 🟢 有空修 | #8-20 | 其余 13 项 | 摩擦和潜在错误 |

---

*审查基于 2026-08-10 的合集 snapshot，文件总数 16 个，四层架构覆盖完整。*

## 修复记录（2026-08-10，全部 20 项已完成）

| 编号 | 问题 | 修复方式 | 涉及文件 |
|------|------|---------|---------|
| #1 | CSS 变量名不匹配 | 改成 `var(--accent)` / `var(--accent-2)` 等实际存在的 token；shader-web-background 版本锁 0.4.2 | ppt-visual-effects/SKILL.md |
| #2 | 36 主题无 token 值 | 新建 `references/theme-tokens.md`，从上游 36 个 CSS 文件提取全部 `:root` token（20+ 变量/主题），含 MBB 咨询主题共 41 套 | theme-tokens.md (新建) |
| #3 | convert.py 缺失无兜底 | ppt-workflow 第 4 层加「前置门禁」检查 convert.py 是否存在，不存在则提前告知用户 | ppt-workflow/SKILL.md |
| #4 | 设计语言→主题无映射 | theme-tokens.md 末尾加「设计语言→主题映射表」；claude-design 末尾注明路径 | theme-tokens.md, claude-design/SKILL.md |
| #5 | mbb 视觉未接入 token | 新建 `mbb-consulting` 主题（theme-tokens.md）+ mbb-decks 末尾加「交接规则」：主题/图标/图表/页脚/字号/密度 6 项 | theme-tokens.md, mbb-decks/SKILL.md |
| #6 | Step 2.5 强制步骤不完整 | axi-front-design 布局变体选择节改为「⛔ 强制步骤，非推荐」，步骤 1-5 对齐 ppt-workflow | axi-front-design/SKILL.md |
| #7 | frontend-design 角色模糊 | ppt-workflow 反模板审查节明确：审查对象是设计护照；审查规则以 layout-library 反俗套清单为准；frontend-design 作为通用判断力介入 | ppt-workflow/SKILL.md |
| #8 | 字体默认违规 | design-system 默认 `--font-sans` 从 Inter 改为 `'Noto Sans SC','Microsoft YaHei',sans-serif` | design-system.md |
| #9 | 数据护照颜色 vs token 模型断裂 | design-system 末尾加「数据护照→token 覆盖规则」：主题优先→品牌色覆盖 accent→无主题时反向匹配 | design-system.md |
| #10 | 两份文档字号冲突 | design-system 排版体系节明确「字号权威来源是 layout-library，本文档不定义字号」 | design-system.md |
| #11 | 非 16:9 布局无具体规则 | canvas-formats 加「非 16:9 画布布局适配规则」（竖屏/方图/横幅/A4 各一段） | canvas-formats.md |
| #12 | CDN `@latest` 脆弱 | shader-web-background 锁为 `@0.4.2` | ppt-visual-effects/SKILL.md |
| #13 | uupm.py 路径不一致 | ui-ux-pro-max SKILL.md 路径改为合集内相对路径 `design-assets/ui-ux-pro-max/scripts/uupm.py` | ui-ux-pro-max/SKILL.md |
| #14 | 数据页图表边界未定义 | image-generation 加「数据页图表决策规则」：优先 ECharts → 明确3种才用静态生图 → 两者不同时 | image-generation.md |
| #15 | 流程图与文字歧义 | ppt-workflow 四层架构 ASCII 图改写，加注释「显式调用，非自动拦截」 | ppt-workflow/SKILL.md |
| #16 | html-to-pptx 首次配置未提醒 | ppt-workflow 第 4 层加「首次配置提醒」+ 执行层完成后、转换前弹窗 | ppt-workflow/SKILL.md |
| #17 | mbb 图表族 vs ECharts 冲突 | ppt-visual-effects 加「与 mbb-decks 图表选择的职责划分」：ghost deck 优先→无标注用决策树→冲突以 ghost deck 为准 | ppt-visual-effects/SKILL.md, mbb-decks/SKILL.md |
| #18 | 反俗套规则分散不一致 | 三处对齐：layout-library 加 2 条（成为 13 条完整版）→ ppt-workflow 加 5 条且注明"以 layout-library 为权威"→ design-system token 层精简为 5 条独有规则 | layout-library.md, ppt-workflow/SKILL.md, design-system.md |
| #19 | 党政报规则与 mbb 引用交集 | 无需修改——审查确认：party-gov-red 禁的是"编造官方标志/党徽国徽"（视觉素材），mbb 的"数据来源引用"是文字引用（数据归属），层面不同不冲突 |
| #20 | references 相对路径无运行时校验 | README 加「完整性检查」说明：执行层启动用 Bash `test -f` 检查 theme-tokens.md 是否存在 | README.md |
| — | 新增 MBB 咨询主题 | `mbb-consulting` 主题完整 token 写入 theme-tokens.md | theme-tokens.md |
| — | 主题总数更新 | 40→41（html-ppt 36 + codex 中国 4 + mbb 1），design-system/README 全部更新 | design-system.md, README.md |

### 本次修复涉及文件

| 文件 | 操作 |
|------|------|
| `references/theme-tokens.md` | **新建**：41 套主题完整 CSS token + 设计语言映射表 |
| `ppt-visual-effects/SKILL.md` | 4 处编辑 |
| `references/design-system.md` | 7 处编辑 |
| `ppt-workflow/SKILL.md` | 5 处编辑 |
| `axi-front-design/SKILL.md` | 2 处编辑 |
| `design-assets/mbb-decks/SKILL.md` | 2 处编辑 |
| `design-assets/claude-design/SKILL.md` | 1 处编辑 |
| `references/canvas-formats.md` | 2 处编辑 |
| `references/image-generation.md` | 1 处编辑 |
| `references/layout-library.md` | 1 处编辑 |
| `design-assets/ui-ux-pro-max/SKILL.md` | 2 处编辑 |
| `README.md` | 2 处编辑 |
| `audit-report-2026-08-10.md` | 加修复记录 |
