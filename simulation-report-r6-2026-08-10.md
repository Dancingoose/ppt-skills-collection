# PPT Skill Collection — 第六轮全流程模拟审查

> 模拟场景：用户说"帮我做一个 AI 行业趋势分析 PPT"（口述，无源文件）
> 审查日期：2026-08-10
> 审查方式：逐层逐 Step 逐文件交叉验证 + 环境实物检查（convert.py 存在性、文件行数、grep 命中数）
> 前五轮累计：58 + 3 = 61 项问题已修复

---

## 0. 环境实物检查

| 检查项 | 结果 | 证据 |
|--------|------|------|
| convert.py 存在 | ✅ | 22850 bytes，html-to-pptx/convert.py |
| theme-tokens.md 主题数 | ✅ 41 | `grep -c "^### "` = 41 |
| :root 块完整性 | ✅ | `grep -c "^:root {"` = 41，`grep -c "^}"` = 41 |
| 布局库三部分 | ✅ | Part 1 L41 (叙事风 A1-10)，Part 2 L293 (事实风 B1-22)，Part 3 L853 (Bento C1-9) |
| 选版式决策表位置 | ✅ | L777 (# 选版式决策表) |
| 节奏模板位置 | ✅ | L836 (# 8 页节奏模板) |
| 反俗套清单位置 | ✅ | L1049 (# 反 AI 俗套清单) |
| 设计语言→主题映射 | ✅ | theme-tokens.md 末尾，11 条（含 MBB） |
| prep-assets docx/pptx | ✅ | Anthropic built-in skill 指针（合集内置，正确策略） |
| ui-ux-pro-max 数据 | ⚠️ | 首次使用需 `--fetch-data`，尚未初始化 |
| python-pptx 可用 | ✅ | Python 3.10.12 + python-pptx OK |
| Inter 字体风险 | 🟡 | 10/41 主题的 --font-display 含 Inter（已知，执行层 Step 4 修补） |

---

## 1. 已安装 vs 合集版本同步验证

| skill | installed 行数 | collection 行数 | 关键内容 grep | 结论 |
|-------|---------------|-----------------|--------------|------|
| ppt-workflow | 360 | 355 | Phase1/2 + content-inventory + spec_lock + WebSearch + quick-reference-card + convert.py门禁 各命中相同 | ✅ 同步 |
| axi-front-design | installed 存在 | 241 | Phase1/2 + layout-library + 选版式 + spec_lock + 内容核实 各 10 命中 | ✅ 同步 |
| ppt-visual-effects | 286 | 281 | --navy 只在"禁止使用"警告中出现 | ✅ 同步 |
| html-to-pptx | 86 | 81 | convert.py 前置警告存在 | ✅ 同步 |

**结论：R5 报告的核心风险（installed 版落后）已消除。** 第五轮修复（save_skill overwrite）已生效，四个核心 skill 正文一致。

---

## 2. 准备层模拟

**模拟动作**：用户口述"AI 行业趋势分析"，无源文件。

**期望执行路径**：
1. ppt-workflow 触发 → 检测无源文件 → WebSearch 收集 AI 行业事实+数据
2. 写入 `D:\CLAUDEworkspace\work\AI行业趋势分析\content-inventory.md`
3. 设计护照填充：主题、源素材路径、页数估算、research-done=true

| 步骤 | 预期 | 实际检查 | 结论 |
|------|------|---------|------|
| WebSearch 入口 | ppt-workflow L37 明确写 | grep 命中 | ✅ |
| content-inventory.md 模板 | L46-77 完整模板 | 包含源文件/源内容全文/数据点/页数预判 | ✅ |
| 回退路径 | L44 D:盘优先 + outputs/ 回退 | 逻辑清楚 | ✅ |
| research-done 标记 | 设计护照有该字段 | L100 | ✅ |
| cross-session 访问 | content-inventory.md 存物理文件 | 不会丢失（除非 outputs/ 回退目录被清理） | 🟡 边缘风险 |

### 发现

**P2 · R6-1：outputs/ 回退路径下 content-inventory.md 跨 session 丢失风险**
当 D:盘未挂载时，回退到 session 临时 outputs/ 目录——该目录跨 session 可能不存在。虽然 D:盘是用户主要环境，但如果没有挂载，Step 3 内容核实时会导致"找不到 content-inventory.md"。
**建议**：回退时先在当前 session 确认路径持久性，或主动告知用户"D盘未连接"。

---

## 3. 设计决策层模拟

**模拟动作**：content-inventory.md 已有内容 → 进入设计决策。

**期望执行路径**：
1. Phase 1 AskUserQuestion（受众/意图/核心主张/画布）← claude-design 前置门禁
2. Skill("claude-design") → 出 3 方向 → 映射表 → 3 候选主题名
3. Phase 2 AskUserQuestion（页数/主题方案/风格版本数等）
4. Skill("frontend-design") → 反模板审查（已填设计护照字段）

| 步骤 | 预期 | 实际检查 | 结论 |
|------|------|---------|------|
| Phase 1 前置门禁 | L128 "Phase 1 是 claude-design 的前置门禁" | 正文+快速参考均明确标注 | ✅ |
| claude-design 搜索复用 | 读 content-inventory.md，research-done=true 跳过 WebSearch | claude-design SKILL.md L52 写明 | ✅ |
| 主题映射 | 10 设计语言 + MBB → 41 主题 | theme-tokens.md 末尾 11 条 | ✅ |
| Phase 2 候选主题分叉 | Phase 2 选 1 主题 → Step 1 展 3 变体；Phase 2 选"你来定" → Step 1 展 3 不同主题 | L179 分叉逻辑清晰 | ✅ |
| 反模板审查时机 | Phase 1/2 之后，Step 1 之前 | ppt-workflow L141 明确 | ✅ |
| spec_lock 锁定 | 选定方案后 design passport 升级为锁定稿 | L112-123 完整纪律 | ✅ |

### 发现

**P3 · R6-2：claude-design 方向顾问模式输出格式未标准化**
claude-design 出 3 方向后，映射到主题名。但 claude-design 本身的输出格式（方向名称 + pitch + 关键词 + 标志性旗舰 + vibe）是靠该 skill 自行组织的——如果 agent 没有正确提取"方向名称"，映射表可能会误匹配。
**建议**：在 ppt-workflow 或 claude-design 中加一句"输出方向时必须用 10 种设计语言的**精确名称**（如『瑞士编辑式』而非『瑞士风格』），以便映射表匹配"。

---

## 4. 执行层模拟

**模拟动作**：锁定版设计护照 → 执行层 7 步。

**期望执行路径**：
Step 1: 加载 design-system + theme-tokens → 出预览 HTML（封面+1-2页，三版）
Step 2: 用户选定 → 锁设计护照
Step 3: 读 content-inventory.md → 核实内容（选版式之前）
Step 4: 读 quick-reference-card → 按需跳读 4 资产库 → 按内容形状选版式 → 登记布局编号
Step 5: 展开全部页面（严格按登记编号实现）
Step 6: Skill("ppt-visual-effects") → 逐页扫描增强
Step 7: 验收

| 步骤 | 预期 | 实际检查 | 结论 |
|------|------|---------|------|
| Step 4 速查卡优先 | "先读 quick-reference-card.md 速览，再按需跳读" | ppt-workflow L206 已加 | ✅ |
| 选版式 P0：数据-版式匹配 | layout-library L809-824 明确规则 | 有数据用 B6/B7/B20/B21，无数据禁 B6/B7 | ✅ |
| token 一致性：叙事 vs 事实 | 叙事风(A)可圆角/阴影，事实风(B)直角无阴影 | design-system + ppt-workflow L212 明确 | ✅ |
| 反俗套字体修补 | 复制 :root 时同步检查 --font-display | ppt-workflow L213 "同步检查" | ✅ |
| 8 页+节奏表 | 先画表再动手 | L215 + layout-library L836-848 模板 | ✅ |
| spec_lock | 展开过程中不漂移 | L221 ⛔门禁标记醒目 | ✅ |
| Step 6 逐页增强 | 显式加载一次 Skill 后逐页扫描 | L227-234 流程明确 | ✅ |
| 验收自检清单 | 7 项自检 | L252-257 | ✅ |

### 发现

**P3 · R6-3：quick-reference-card 版式 P0 表中跨文件引用格式不一致**
quick-reference-card L14 写 `（→ layout-library.md L777-825）`——但布局库 L777 是"选版式决策表"的**开头**，L825 是"内容类型必须匹配版式"部分之后——两者之间的内容不完全是"P0 决策"。更精确的引用应为 L777-802（决策表本体）或 L809-824（P0 匹配规则）。
**建议**：修正为 `（→ layout-library.md L777-824）`——L825 的"---"之后是下一节，824 是 P0 匹配规则的最后一条。

---

## 5. 交付层模拟

**模拟动作**：HTML 设计稿完成 → 导出 PPTX。

**期望执行路径**：
1. 前置门禁：convert.py 检查（准备层后已做一次 + 交付层二次检查）
2. 首次配置 AskUserQuestion（fonts.auto_install + audit.mode）
3. 运行 `python convert.py input.html`
4. Canvas/WebGL → 静态截图降级
5. 视觉 audit（triage 模式）
6. 交付

| 步骤 | 预期 | 实际检查 | 结论 |
|------|------|---------|------|
| convert.py 双重门禁 | 准备层后 + 交付层前各检查一次 | ppt-workflow L319 + L262 | ✅ |
| Canvas/WebGL 降级细节 | L281-290 完整说明 | 包含截图分辨率/着色器延迟/CSV 备选 | ✅ |
| 首次配置 | 2 条偏好确认 | html-to-pptx L43-48 | ✅ |
| audit triage 模式 | 主 agent 看缩略图分流 + sub-agent 审入围页 | ppt-workflow L281 | ✅ |

### 发现

**P3 · R6-4：首次配置 AskUserQuestion 可能被漏掉**
html-to-pptx 的首次配置（fonts.auto_install + audit.mode）需要 agent 先检查 `.config.local.toml` 是否存在。如果 agent 已经做过一次 PPT 任务，配置已写入——但如果这是 agent 第一次在这个 session 做交付，很可能忘记检查。
**建议**：在 ppt-workflow 交付层步骤前加一句"先检查 html-to-pptx/.config.local.toml 是否存在：不存在则弹 AskUserQuestion 首次配置；存在则跳过"。

---

## 6. 跨层衔接验证

### 6.1 数据护照字段流

| 字段 | 准备层填 | Phase 1/2 填 | 决策层填 | 执行层读取 | 验证 |
|------|---------|-------------|---------|-----------|------|
| 主题 | ✅ | — | — | ✅ | ✅ |
| 源素材路径 | ✅ | — | — | ✅ (Step 3) | ✅ |
| 页数/章节 | ✅ (估算) | ✅ (确认) | — | ✅ | ✅ |
| research-done | ✅ | — | ✅ (读) | — | ✅ |
| 受众 | — | ✅ (Phase 1) | — | ✅ | ✅ |
| 核心主张 | — | ✅ (Phase 1) | — | ✅ | ✅ |
| 画布 | — | ✅ (Phase 1) | — | ✅ | ✅ |
| 主题方案 | — | ✅ (Phase 2) | — | ✅ | ✅ |
| 配色/字体 | — | — | ✅ (从 theme-tokens 读) | ✅ | ✅ |

### 6.2 文件间引用完整性

| 引用关系 | 验证方式 | 结论 |
|---------|---------|------|
| ppt-workflow → layout-library.md | L205 引用 | ✅ |
| ppt-workflow → design-system.md | L207 引用 | ✅ |
| ppt-workflow → theme-tokens.md | L208 引用 | ✅ |
| ppt-workflow → canvas-formats.md | L207 (快速参考) | ✅ |
| ppt-workflow → image-generation.md | L207 (快速参考) | ✅ |
| ppt-workflow → quick-reference-card.md | L206 引用 | ✅ |
| design-system → theme-tokens.md | L9, L51, L125, L240 多处引用 | ✅ |
| axiom-front-design → layout-library.md | L181 引用 | ✅ |
| axiom-front-design → design-system.md | L212-213 引用 | ✅ |
| axiom-front-design → theme-tokens.md | L212 引用 | ✅ |
| README → 所有文件 | 完整映射表 | ✅ |

### 6.3 Skill 调用链完整性

| 场景 | 调用链 | 验证 |
|------|--------|------|
| 用户无想法 | Phase 1 → claude-design(3方向) → 映射表 → Phase 2(含候选主题) | ✅ |
| MBB 咨询 | Phase 1 → mbb-decks(ghost deck) → 确认 → Phase 2(mbb-consulting+2备选) | ✅ |
| 用户有明确风格 | Phase 1 → Phase 2(直接选主题) → 跳过 claude-design | 🟡 |
| 口述无源文件 | WebSearch → content-inventory → Phase 1 → ... | ✅ |
| HTML 交付（非 PPTX） | 跳过交付层 → 直接给 HTML | ✅ |
| 纯 PPTX 不要 HTML | 走内置 pptx skill | ✅ |

### 发现

**P3 · R6-5：用户有明确风格时的快速路径未明确**
快速参考和 ppt-workflow 的第 2 层"按场景判断"表（L132-136）列出四种场景：用户没想法 / 需要 token / MBB 咨询 / 所有场景。但没有"用户说『我要极简白风格』"的直接路径——此时 claude-design 的三方向顾问模式是多余的。
虽然 ppt-workflow L168 有 Phase 2 快速路径（跳过 5-7 项），但设计决策层的 skill 选择没有快速路径。
**建议**：在 L132 表加一行：`用户有明确风格要求 | 跳过 claude-design | 直接进入 Phase 2，主题方案选项只含用户指定的 + 2 替代`。

---

## 7. 边缘场景验证

| 场景 | 处理方式 | 结论 |
|------|---------|------|
| 非 16:9 画布（小红书 3:4） | canvas-formats.md 有完整 8 种画布 + 非 16:9 布局适配规则（L92-113） | ✅ |
| AI 配图无后端 | image-generation.md L74 "回退到占位符" | ✅ |
| ECharts + 配图冲突 | image-generation.md L62-64 "优先 ppt-visual-effects，不同时用于同一页" | ✅ |
| 着色器 + 中文字幕页 | ppt-visual-effects L28 "文字占比 > 80% 跳过着色器" | ✅ |
| A4 打印画布 | canvas-formats L112-113 "禁 ECharts/Three.js 等交互增强，改用静态 SVG" | ✅ |
| 10 个主题含 Inter 字体 | ppt-workflow L213 "复制 :root 时同步检查替换" | 🟡 需要 agent 执行纪律 |
| MBB → Phase 2 交接 | ppt-workflow L177 "候选 = mbb-consulting + 2 备选" | ✅ |
| 用户中途换风格 | ppt-workflow L120 "回到方案预览层重新出方案" | ✅ |

---

## 8. 本轮新发现问题汇总

| 编号 | 严重度 | 问题 | 涉及文件 |
|------|--------|------|---------|
| R6-1 | 🟢 P2 | outputs/ 回退路径下 content-inventory.md 跨 session 丢失风险 | ppt-workflow |
| R6-2 | 🟢 P3 | claude-design 方向名称未强制标准化，映射表可能误匹配 | claude-design / ppt-workflow |
| R6-3 | 🟢 P3 | quick-reference-card 版式 P0 引用行号范围过宽 | quick-reference-card |
| R6-4 | 🟢 P3 | html-to-pptx 首次配置检查可能被漏掉 | ppt-workflow |
| R6-5 | 🟢 P3 | 用户有明确风格要求时缺少跳过 claude-design 的快速路径 | ppt-workflow |

---

## 9. 总评

### 工作流自洽性：✅ 通过

四层架构逻辑完整自洽：
- 准备层 → content-inventory.md 物理文件承载
- Phase 1 前置门禁 → claude-design 有受众/意图上下文
- Phase 2 + 主题映射 → 方案预览有据可依
- Step 3 内容核实 → Step 4 选版式（顺序正确）
- Step 6 逐页增强 → 显式调用而非自动拦截
- spec_lock 纪律 → 防止展开漂移
- convert.py 双重门禁 → 交付前可兜底

### 技能覆盖：✅ 完整

11 个 skill 全部在四层架构中有明确定位：
- 准备层 3 个：docx / pptx / vision-qwen (external)
- 决策层 4 个：claude-design / frontend-design / ui-ux-pro-max / mbb-decks
- 执行层 2 个：axi-front-design / ppt-visual-effects
- 交付层 1 个：html-to-pptx
- 配套 5 个资产库：layout-library / design-system / theme-tokens / canvas-formats / image-generation

### 当前风险排名

| 风险 | 等级 |
|------|------|
| Inter 字体在 10 个主题中需要执行层修补（依赖 agent 纪律） | 🟡 |
| ui-ux-pro-max 首次使用需 --fetch-data（文档已说明，但可能首次使用时被遗忘） | 🟡 |
| 5 个 P3 问题（本报告 R6-1 至 R6-5） | 🟢 |
| convert.py 已存在且 python-pptx 可用 | ✅ 无风险 |

### 与前五轮对比

前五轮累计修复 61 项问题。本轮（第六轮）仅发现 5 个 P2/P3 级问题，无 P0/P1 阻塞性问题。工作流成熟度已达到可生产使用水平。

---

## 10. 建议修复顺序

1. **R6-1 (P2)**：在 ppt-workflow 准备层回退路径处加提示"若回退到 outputs/，告知用户：content-inventory.md 可能跨 session 丢失，建议保存到持久位置"
2. **R6-5 (P3)**：在设计决策层"按场景判断"表加一行快速路径
3. **R6-3 (P3)**：修正 quick-reference-card 行号引用
4. **R6-4 (P3)**：在交付层步骤前加 toml 检查提示
5. **R6-2 (P3)**：在 claude-design 或 ppt-workflow 中要求输出标准方向名称
