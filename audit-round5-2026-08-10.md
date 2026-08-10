# PPT 工作流合集第五轮审查报告

> 审查方式：基于更新后状态（第三/四轮修复已落地 + installed 版已同步）重新模拟完整四层流程
> 审查日期：2026-08-10
> 模拟场景：用户说"帮我做一个 AI 行业趋势分析 PPT"（口述，无源文件）
> 前四轮累计：30 + 14 + 14 = 58 项问题已修复

---

## 0. 版本一致性验证（本轮回溯确认）

### 0.1 installed vs collection 三个核心 skill 已同步 ✅

| skill | installed | collection | 正文 diff |
|-------|-----------|------------|-----------|
| ppt-workflow | 359行 | 354行 | **IDENTICAL**（从 `# PPT 制作分层流程` 起） |
| axi-front-design | 246行 | 241行 | **IDENTICAL**（从 `# Axi Front Design` 起） |
| ppt-visual-effects | 286行 | 281行 | **IDENTICAL**（从 `# PPT Visual Effects` 起） |

> 行数差异仅为 frontmatter（skill registry 元数据 vs 合集原文），正文完全一致。

### 0.2 关键修复点在 installed 版已生效 ✅

- `research-done` 字段：installed 版命中 2 处
- Canvas/WebGL 降级细节：installed 版命中 1 处
- quick-reference-card 引用：installed 版命中 1 处

### 0.3 前四轮修复落地复核 ✅

| 关键修复 | 状态 | 验证方式 |
|---------|------|---------|
| 中国场景4套token CSS值 | ✅ 完整 | party-gov-red 等 4 套完整 `:root` 块（~30行/套）在 theme-tokens.md L715-795 |
| 选版式决策表唯一性 | ✅ | layout-library L777 仅一处，无重复表（R4-6 回归已修复） |
| 设计语言→主题映射表 | ✅ | theme-tokens.md L832+，11 条含 MBB |
| 主题总数 41 | ✅ | theme-tokens `###` = 41；design-system/README 均写 41 |
| Step 编号 | ✅ | axi-front-design 无 Step 2.5 残留；ppt-visual-effects 触发时机=Step 6 |
| ui-ux-pro-max 路径 | ✅ | `scripts/uupm.py` 存在，相对路径统一 |
| 快速参考时序 | ✅ | Phase 1 → claude-design → Phase 2 → frontend-design → 执行层 |
| 反模板审查时机 | ✅ | 正文 L141 反模板审查；快速参考在 Phase 2 后 |
| convert.py 门禁 | ✅ | 准备层后立即 Bash 检查 + 交付层二次检查 |
| 速查卡行号引用 | ✅ | L777/L836/L1049 全部准确 |

---

## 1. 本轮新发现问题

### 🟢 P2 · R5-1：html-to-pptx installed 版缺 convert.py 前置警告

**现象**：collection 版 html-to-pptx/SKILL.md 在"调用"节前有一行警告：

```
> ⚠️ **首次使用前**：本 skill 需要 `convert.py` 渲染脚本。请从 [上游仓库](https://github.com/Hasasasa/claude-skill-html-to-pptx) 获取完整脚本文件放入本目录。
```

但 installed 版**没有这行**（行数 81 vs 79，差 2 行正是这个警告块）。

**影响**：agent 直接调 installed 版 html-to-pptx 时，不会在第一次接触就意识到 convert.py 缺失——虽然 ppt-workflow 有门禁兜底，但单独加载 html-to-pptx 时缺提示。

**修复**：同步 html-to-pptx installed 版到 collection 版。

### 🟢 P2 · R5-2：collection 与 installed 的 frontmatter 存在格式差异

**现象**：collection 版 ppt-workflow/axi-front-design/ppt-visual-effects 是**双 frontmatter**（第 1 块带引号的简版 + 第 2 块完整版），installed 版同样是双 frontmatter 但内容不完全一致（description 措辞不同）。

**影响**：功能无害（skill 引擎取第 1 块），但造成 diff 噪音，后续审计容易误判"不同步"。

**修复**：统一 frontmatter 格式——collection 与 installed 都保留第 1 块简版即可，正文单源。

### 🟢 P3 · R5-3：quick-reference-card 的引用是"可选"非"必读"

**现象**：ppt-workflow 快速参考把 `Read references/quick-reference-card.md` 列在执行层第 1 位，但正文 Step 4 第 1 条仍写"读 layout-library + design-system"。速查卡是"精简替代"，正文没有明确"先读速查卡，再按需跳读"的强制语义。

**影响**：agent 可能跳过速查卡直接读 120KB 资产库，失去优化意义。

**修复**：正文 Step 4 开头加一句"先读 quick-reference-card.md 速览，再按需跳读对应资产库"。

---

## 2. 全流程 walkthrough 结果（第五轮）

### 准备层
- 口述主题 → WebSearch → content-inventory.md → research-done: true ✅
- 任务文件夹路径：ppt-workflow 已加默认路径 + 回退逻辑 ✅

### 设计决策层
- Phase 1 前置门禁：已在 claude-design 之前 ✅
- claude-design 前置检查：读数据护照，无则先完成 Phase 1 ✅
- 搜索复用：claude-design 读 content-inventory.md，research-done 则跳过 ✅
- 映射表：10 设计语言 + MBB → 41 主题 ✅

### 执行层
- Phase 2（含候选主题）→ 反模板审查 → Step 1 预览 ✅
- Step 1-7 顺序正确，spec_lock 纪律完整 ✅
- 每页登记布局编号，P0 数据-版式匹配 ✅
- Step 6 加载一次 ppt-visual-effects 逐页扫描 ✅

### 交付层
- convert.py 门禁：准备层后 + 交付层双重检查 ✅
- Canvas/WebGL → PPTX 降级细节完整 ✅

---

## 3. 结论

**工作流已自洽。** 前四轮 58 项修复全部落地且经回归验证无复发。第五轮仅发现 3 个低优先级问题：

1. **R5-1 (P2)** html-to-pptx installed 版缺 convert.py 前置警告 → 需同步
2. **R5-2 (P2)** frontmatter 格式双源差异 → 需统一
3. **R5-3 (P3)** 速查卡引用语义不强 → 建议加强制语义

**当前最大的实质风险仍是外部依赖**：convert.py 未实际存在（需手动获取）。这不是 skill 逻辑问题，而是安装完整性问题——合集文档已充分说明，但实际环境缺失。

---

## 修复记录

| 编号 | 优先级 | 问题 | 修复方式 | 涉及文件 |
|------|-------|------|---------|---------|
| R5-1 | 🟢 P2 | html-to-pptx installed 缺 convert.py 警告 | save_skill 同步 collection 版 | html-to-pptx |
| R5-2 | 🟢 P2 | frontmatter 双源差异 | collection 统一为简版 frontmatter | ppt-workflow / axi-front-design / ppt-visual-effects |
| R5-3 | 🟢 P3 | 速查卡引用不强 | Step 4 开头加"先读速查卡再按需跳读" | ppt-workflow/SKILL.md |
