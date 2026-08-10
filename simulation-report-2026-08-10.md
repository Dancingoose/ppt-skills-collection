# PPT Skills Collection 工作流模拟审查报告

> 模拟场景：用户说"帮我做一个分析AI行业趋势的PPT"
> 模拟日期：2026-08-10
> 模拟方式：逐层逐Step逐文件交叉验证，不实际运行代码，只检查逻辑/衔接/数据流/文件存在性

---

## 0. 环境状态快照

| 检查项 | 状态 | 详情 |
|--------|------|------|
| 合集文件完整性 | ✅ | 19个文件全部可读 |
| references/ 5个资产库 | ✅ | 五个文件全部存在，总计 ~125KB |
| theme-tokens.md 主题数量 | ✅ | 41套，count确认 |
| 设计语言→主题映射表 | ✅ | 已存在于 theme-tokens.md 末尾（10+1=11条） |
| 内容-版式决策表 | ✅ | 存在于 layout-library.md L777-825，含P0匹配规则 |
| ppt-workflow installed vs collection 版本 | ⚠️ 不同步 | installed=122行(旧版)，collection=346行(审查修复后) |
| axi-front-design installed vs collection | ⚠️ 不同步 | installed=169行(上游原版)，collection=241行(含Phase1/2+选版式) |
| ppt-visual-effects installed vs collection | ⚠️ 不同步 | installed=273行(含`--navy,--coral`)，collection=281行(已修) |
| convert.py | ❌ 缺失 | html-to-pptx/convert.py 不存在 |

---

## 1. 准备层模拟

**模拟输入**：用户口述"分析AI行业趋势"，无源文件

**期望流程**：
1. ppt-workflow触发 → 检测无docx/pdf/图片 → 触发WebSearch收集AI行业事实+数据
2. 产出 content-inventory.md（写入 `D:\CLAUDEworkspace\work\AI行业趋势分析\content-inventory.md`）
3. 设计护照填充：主题、源素材路径、页数/章节估算、research-done=true

**发现的问题**：

### 问题1 · WebSearch 入口有但描述不一致
- collection版 ppt-workflow L37 明确写了 `WebSearch 收集事实/数据/来源 → 写入 content-inventory.md`
- 但 installed版（122行）的快速参考里完全没提 WebSearch，只写了 Skill("docx")/Skill("vision-qwen")
- **影响**：口述主题场景下，installed版可能导致agent跳过WebSearch直接进入决策层，content-inventory.md空洞

### 问题2 · content-inventory.md 跨session共享路径
- collection版 L44 写 `D:\CLAUDEworkspace\work\<任务名>\` 为优先路径
- 如果session中 D: 盘未挂载，回退到 `outputs/<任务名>/`
- 回退路径的 content-inventory.md 跨session可能丢失（outputs是临时目录）
- **影响**：多session协作时Step 3内容核实可能找不到文件

---

## 2. 设计决策层模拟

**模拟输入**：content-inventory.md（含AI行业10个关键趋势+数据）、设计护照（主题="AI行业趋势"）

**期望流程**：
1. Phase 1 AskUserQuestion（受众/意图/核心主张/画布）← claude-design前置门禁 ✅
2. Skill("claude-design") → 出3方向
3. 映射表 → 3个候选主题名
4. Phase 2 AskUserQuestion（页数/主题方案/风格版本数等）← 含候选主题确认
5. Skill("frontend-design") → 反模板审查

**发现的问题**：

### 问题3 · Phase 1 前置门禁在快速参考里没有
- collection版 ppt-workflow L128 写了"Phase 1 是设计决策层的前置门禁"
- 快速参考（L316-344）把 Phase 1 写成了"准备层之后"，但没有强调"必须在 claude-design 之前"
- installed版连这个前置门禁都没写
- **影响**：实际执行时，agent可能先加载claude-design出方向，再回头问用户受众/意图——方向缺少上下文，效率和相关性打折扣

### 问题4 · Phase 2 与方案预览的主题候选有逻辑分叉
- collection版 L167 写 Phase 2在 Step 1 方案预览**之前**问
- L179 写 Phase 2 呈现 claude-design 映射出的3个候选主题
- 但 Phase 2 问的是"主题方案"，如果用户在 Phase 2就选了1个 → Step 1只需展示该主题3个变体（字号/叙事vs事实mode）
- 如果用户Phase 2选"你来定" → Step 1展示3个不同主题的方案预览
- 这个分叉逻辑对，但**只有collection版有**，installed版既没有Phase 2框架也没有这个分叉

### 问题5 · installed版完全没有两阶段确认框架
- installed版 axi-front-design 只有原始的 Step 1-6 工作流（先问后做→找上下文→立系统→草稿→迭代→验收）
- 没有 Phase 1/2 的19项清单
- 没有与 claude-design 映射的联动
- 没有 spec_lock 纪律
- **结论：installed版的两个核心skill（ppt-workflow + axi-front-design）都没跟上审查修复**

---

## 3. 执行层模拟

**模拟输入**：锁定版设计护照（swiss-grid主题、16:9画布、管理层受众、N=10页）

**期望流程（按修复后顺序）**：
Step 1: 读 design-system.md + theme-tokens.md → 选3候选主题 → 出预览HTML
Step 2: 用户选定 → 锁设计护照
Step 3: 读 content-inventory.md → 核实内容（在选版式之前！）
Step 4: 读4个资产库 → 按核实后内容形状选版式 → 登记每页布局编号
Step 5: 展开全部页面（严格按登记编号实现）
Step 6: Skill("ppt-visual-effects") → 逐页扫描增强
Step 7: 验收自检

**发现的问题**：

### 问题6 · installed版 Step 顺序是旧版
- installed版 ppt-workflow：Step 1问 → Step 2预览 → Step 3展开 → Step 4验收（4步，没有核实和选版式步骤）
- collection版：Step 1-7（加了核实、选版式、增强三个关键步骤）
- **影响**：按installed版走会跳过内容核实和布局登记，可能做出内容和页面数量不匹配的PPT

### 问题7 · installed版 axi-front-design 的布局变体表过窄
- installed版（L144-151）只有5个推荐布局：三列、左文右图、步骤卡、对比两列
- collection版（241行）引用了完整的41个布局+选版式决策表
- **影响**：按installed版只会用少数几个通用布局，无法利用 A1-A10/B1-B22/C1-C9 的多样性

### 问题8 · ppt-visual-effects 颜色变量已修复但installed版未更新
- collection版：`--navy, --coral` → `var(--accent), var(--accent-2)` ✅
- installed版：仍写 `--navy, --coral` ❌
- **影响**：按installed版生成的着色器颜色和设计系统token对不上

### 问题9 · 8页+节奏表存在但有前提
- layout-library.md L836-848 有8页节奏模板
- 但 Step 4 第9条 "8页+ deck先画节奏表再动手" 只在collection版 ppt-workflow 里提了
- installed版没有任何节奏规划

### 问题10 · 执行层需要按顺序读4个资产库，但没有"单文件摘要"
- Step 4 要求读 layout-library（60KB）+ design-system（18KB）+ theme-tokens（35KB）+ canvas-formats（6KB）
- 每个文件都有"与其他资产库的关系"说明，但没有一个"执行前快速速查卡"
- agent需要通读 ~120KB 后才能动手
- **影响**：token消耗大，可能被截断导致信息不完整

---

## 4. 交付层模拟

**模拟输入**：完成版HTML设计稿（10页，含ECharts+Shadertoy增强）

**期望流程**：
1. 前置门禁：检查 convert.py 是否存在
2. 不存在 → 告知用户 + 给安装命令 + 先交付HTML
3. 存在 → AskUserQuestion首次配置(fonts.auto_install + audit.mode)
4. 运行 `python convert.py input.html`
5. 视觉audit（triage模式）
6. 交付

**发现的问题**：

### 问题11 · convert.py 缺失，前置门禁存在但手动
- collection版 ppt-workflow L262-269 有门禁流程（检查→告知→替代方案）
- 但"检查"需要agent手动用Bash `test -f`——这是人工纪律，不是自动阻断
- 快速参考 L319 也写了 `Bash: test -f html-to-pptx/convert.py`
- **影响**：门禁依赖agent自觉性，如果agent跳过了检查直接跑完4层 → 用户才发现无法导出 → 全部返工

### 问题12 · Canvas/WebGL 增强导出降级已说明但细节不足
- collection版 L281 写了"Canvas/WebGL增强导出PPTS时会降级为静态截图"
- 但没说明：
  - 静态截图是html-to-pptx自动处理还是需要额外配置？
  - Shadertoy着色器导出的截图质量如何？（着色器可能在截图时有渲染问题）
  - ECharts图表导出是截图还是转原生图表？
- **影响**：用户以为导出的PPTX里有可交互/可编辑的图表，实际只有截图

### 问题13 · 首次配置的 AskUserQuestion 与 Phase 1/2 可能冲突
- html-to-pptx 需要问 fonts.auto_install + audit.mode（2项）
- 如果执行层已经用了 Phase 1/2 的 AskUserQuestion（多轮），再加一轮"首次配置"弹窗
- collection版L273 说"在执行层完成HTML设计稿后、转换前弹出"
- **影响**：用户可能觉得被反复弹窗

---

## 5. Skill版本不同步 —— 这是最大的问题

| 文件 | installed版行数 | collection版行数 | 差距 | 关键缺失 |
|------|----------------|-----------------|------|---------|
| ppt-workflow/SKILL.md | 122 | 346 | +224 | Phase 1/2框架、content-inventory.md、数据护照、spec_lock、反模板审查、WebSearch、convert.py门禁、8页节奏模板、updated Step顺序 |
| axi-front-design/SKILL.md | 169 | 241 | +72 | Phase 1/2 19项清单、布局库引用、选版式强制步骤、Step 3/4增加的核实和版式登记 |
| ppt-visual-effects/SKILL.md | 273 | 281 | +8 | 颜色变量修复(--navy→--accent)、纯文字页着色器跳过例外 |
| html-to-pptx/SKILL.md | 79 | 81 | +2 | 基本一致 |

**根因**：installed skills 是 Anthropic Skill Registry 的原版上游版本，而 collection 里的版本是两轮审查修复（30项问题）后的改进版。但 installed版没有更新——因为 collection版虽然被 save_skill 到用户账户，但似乎 installed版读的是skill registry缓存。

---

## 6. 模拟结论汇总

### 工作流本身的逻辑 —— 通过 ✅
collection版 ppt-workflow 的四层架构逻辑自洽：
- 准备层 → content-inventory.md 物理文件承载（解决了审查问题3）
- Phase 1 前置门禁 → claude-design（解决了审查问题4）
- Phase 2 + 候选主题映射 → 方案预览（解决了审查问题1/2）
- Step 3 内容核实 → Step 4 选版式（顺序正确，解决了审查问题5）
- spec_lock 纪律（防止漂移）
- convert.py 门禁（解决了审查问题3）
- 每步都有前置条件说明

### 最大的实际风险 —— installed版本落后 🔴
如果用户实际触发"做个PPT"，agent加载的是 installed 版本（旧版122行）而不是 collection 版（346行）——那么审查修复的30项问题基本全部白费。agent会：
- 跳过 WebSearch（准备层断档）
- 跳过 content-inventory.md（内容无物理承载）
- 跳过 Phase 1/2 两阶段确认（用户体验差）
- 用旧版4步工作流代替新版7步（跳过核实和版式登记）
- ppt-visual-effects 颜色变量名对不上（`--navy` 不存在）
- convert.py 检查没有门禁流程

### 还有 3 个未在前两轮审查中覆盖的问题

| # | 问题 | 严重度 |
|---|------|--------|
| 1 | installed版 vs collection版版本不同步 → 修复不在生效 | 🔴 P0 |
| 2 | Canvas/WebGL→PPTX降级细节不足 | 🟡 P1 |
| 3 | 执行层需读~120KB资产库，无单文件速查卡 | 🟡 P2 |

---

## 7. 建议修复

### 立即 (P0)
更新 installed 版本的 skill 文件到 collection 版——`save_skill` 用 `overwrite: true` 将 ppt-workflow 和 axi-front-design 更新到审查修复后的版本。

### 短期 (P1)
1. 补充 html-to-pptx 文档：Canvas/WebGL→PPTX降级的具体机制和截图质量
2. 在 ppt-workflow 快速参考里标注 Phase 1 的时机（"在 claude-design 之前"）

### 中期 (P2)
1. 从上游仓库克隆 convert.py 到合集
2. 制作一个"执行前快速速查卡"精简版（~20行），减少agent读取全部资产库的token开销
