# PPT Skills Collection

一套完整的 Claude 幻灯片制作 skill 合集——从素材读取到 PPTX 交付，四层架构流水线。

## 快速安装

将整个 `ppt-skills-collection/` 文件夹复制到你的 skills 目录：

- **Claude Desktop**: `%USERPROFILE%\.claude\skills\` (Win) / `~/.claude/skills/` (Mac)
- **Claude Code**: `~/.claude/skills/`

在 `.claude/settings.json` 中注册（Claude Code）：

```json
{
  "skills": [
    { "name": "ppt-workflow", "path": "skills/ppt-skills-collection/ppt-workflow/SKILL.md" },
    { "name": "axi-front-design", "path": "skills/ppt-skills-collection/axi-front-design/SKILL.md" },
    { "name": "html-to-pptx", "path": "skills/ppt-skills-collection/html-to-pptx/SKILL.md" },
    { "name": "ppt-visual-effects", "path": "skills/ppt-skills-collection/ppt-visual-effects/SKILL.md" },
    { "name": "claude-design", "path": "skills/ppt-skills-collection/design-assets/claude-design/SKILL.md" },
    { "name": "frontend-design", "path": "skills/ppt-skills-collection/design-assets/frontend-design/SKILL.md" },
    { "name": "ui-ux-pro-max", "path": "skills/ppt-skills-collection/design-assets/ui-ux-pro-max/SKILL.md" },
    { "name": "mbb-decks", "path": "skills/ppt-skills-collection/design-assets/mbb-decks/SKILL.md" },
    { "name": "docx", "path": "skills/ppt-skills-collection/prep-assets/docx/SKILL.md" },
    { "name": "pptx", "path": "skills/ppt-skills-collection/prep-assets/pptx/SKILL.md" }
  ]
}
```

也可以通过 `/skill` 命令或 Claude Desktop 插件面板逐个安装。

> **references/ 资产库**（5 个文件：`layout-library.md` / `design-system.md` / `theme-tokens.md` / `canvas-formats.md` / `image-generation.md`）不是 skill，无需在 settings.json 注册——它们随合集复制，由 `ppt-workflow` 在执行层通过 `Read` 加载。**确保整个 `ppt-skills-collection/` 文件夹连同 `references/` 一起复制**，否则执行层读不到资产库。
> 
> **⚠️ 完整性检查**：ppt-workflow 执行层启动时会用 Bash `test -f` 检查 `references/theme-tokens.md` 是否存在（该文件是所有主题 token 的单一事实来源）。若缺失，报错并告知用户合集复制不完整。

## 四层架构

```
准备层（一次性）          设计决策层           执行层            交付层
  docx         →    claude-design     axi-front-design    html-to-pptx
                                ppt-visual-effects
                                (逐页视觉增强)
  pptx              frontend-design   (HTML 设计稿)       (导出 pptx)
  (读取素材)         ui-ux-pro-max     → 方案预览
                    mbb-decks          → 用户选定
                    (可选)             → 展开全量
```

### 准备层 — 读素材
- **docx** / **pptx**: 从源文件提取文字和图片（合集内置）
- **vision-qwen**: 图片/音频/视频分析（外部 skill，需单独安装）
- **pdf-reading**: PDF 内容提取（外部 skill，需单独安装）

### 设计决策层 — 定方向
- **claude-design**: 10 种设计语言，出 3 个差异化方向
- **ui-ux-pro-max**: 84+ 风格、190+ 配色、74 字体配对的数据库搜索引擎
- **mbb-decks**: 咨询级 ghost deck + MECE + 行动标题（故事线顾问，不渲染 PPTX）
- **frontend-design**: 全程质量把关，反 AI 模板化

### 执行层 — HTML 设计稿（核心）
- **axi-front-design**: 先弹窗问偏好（两阶段确认：沟通契约 + 设计方案）→ 出方案预览 → 用户选定 → 展开全部页面。**Phase 1 采用材料驱动选择题**——有 content-inventory.md 时，选项由 agent 读材料现场生成（详见 `references/material-driven-questioning.md`）
- **ppt-visual-effects**: 展开每页时自动判断是否需要嵌入 ECharts 图表 / Shadertoy 背景 / Three.js 3D / Matter.js 物理，直接生成可运行代码
- **画布格式**（`references/canvas-formats.md`）: 8 种画布规格（16:9 / 4:3 / 小红书 3:4 / 朋友圈 1:1 / 故事 9:16 / 公众号头图 / 横幅 / A4），正文字号基准随画布缩放
- **设计系统**（`references/design-system.md`）: 语义化 token 基线 + **41 套主题目录**（html-ppt 36 套 + codex-ppt 中国场景 4 套：党政红/科研答辩/教学课件/手绘技术解释 + mbb-consulting 咨询 1 套），token-driven 换肤，禁止硬编码颜色
- **布局库**（`references/layout-library.md`）: 41 个页面布局素材（A1–A10 叙事风 + B1–B22 事实风 + C1–C9 Bento 网格），axi-front-design 执行时按内容形状选版式，附选版式决策表、主题节奏硬规则、反 AI 俗套清单
- **配图流程**（`references/image-generation.md`）: AI 配图指南（何时生成、后端检测、硬规则），按需启用——需外部生图后端

### 交付层 — 导出
- **html-to-pptx**: HTML → 原生可编辑 PPTX（文本框是文本框、形状是形状）

## 使用方式

直接说"做个 PPT"或"把这篇文章做成 slide"，`ppt-workflow` 会自动调度全套流程。

## 核心原则

- PPTX 是 HTML 设计稿的导出格式，不是创作媒介
- 禁止直接用 python-pptx/pptxgenjs 手工拼形状
- 必须先出方案预览再展开全量
- 必须先两阶段询问确认（沟通契约 + 设计方案），禁止跳过 AskUserQuestion 直接假设
- 禁止 AI 俗套：渐变背景、emoji、accent stripe、圆角卡片 + 左边框

## 依赖

### html-to-pptx 渲染脚本（已内置 ✅）

**2026-08-10 已从上游仓库拉取完整脚本到 `html-to-pptx/`**（convert.py + scripts/ 14 个模块 + references/ 文档 + requirements.txt），无需再手动获取。已验证端到端转换成功。

如需更新到上游最新版：

```bash
# 上游仓库（已更名为 html-to-editable-pptx）
git clone https://github.com/Hasasasa/html-to-editable-pptx.git /tmp/html-to-pptx-upstream

# 覆盖合集目录下的 convert.py 与 scripts/
cp /tmp/html-to-pptx-upstream/convert.py "D:\CLAUDEworkspace\work\ppt-skills-collection\html-to-pptx\convert.py"
cp -r /tmp/html-to-pptx-upstream/scripts "D:\CLAUDEworkspace\work\ppt-skills-collection\html-to-pptx\"
```

- **Python**: 3.10+, Playwright, pptx
- **外部 skill（准备层用，需单独安装）**:
  - `vision-qwen` — 图片/音频/视频分析（来源见下方表格）
  - `pdf-reading` — PDF 内容提取（Anthropic 内置）
- **AI 配图**（可选，`references/image-generation.md`）: 需要外部生图后端——Codex/Cursor 原生生图工具、`baoyu-image-gen` skill（需单独安装）、Gemini `generate_image`、或 OpenAI 兼容生图 API（如 gpt-image-2）。无可用后端时回退到占位符
- **执行合规检查**（`ppt-workflow/scripts/check_ppt_execution.py`）: 纯标准库（re/pathlib/argparse），无额外依赖。各层自检由 agent 运行此脚本（见 ppt-workflow SKILL.md 各层自检清单），替代纯记忆打勾。
- **其他 skill**: 无额外依赖，纯指令

### references/ 资产库清单（共 7 个，随合集整体复制）

| 文件 | 内容 | 用途 |
|------|------|------|
| `references/layout-library.md` | 41 布局（A+B+C）+ 选版式决策表 + 反俗套清单 | 执行层每页选版式 |
| `references/design-system.md` | 语义化 token 基线 + 41 主题目录 + 数据护照覆盖规则 | 执行层全局 token 体系 |
| `references/theme-tokens.md` | **41 套主题完整 CSS `:root` 值** + 设计语言→主题映射表 | 执行层直接复制粘贴用的唯一颜色/字体来源 |
| `references/canvas-formats.md` | 8 种画布规格 + 非 16:9 布局适配规则 | 执行层画布选择 |
| `references/image-generation.md` | AI 配图流程 + 数据页图表决策规则 | 执行层可选配图 |
| `references/quick-reference-card.md` | 执行前速查卡（~60行） | 执行层 Step 4 快速参考，替代通读全部5个资产库 |
| `references/material-driven-questioning.md` | **Phase 1 材料驱动提问推导引擎**（12 项 + 6 类材料特征 + 示例） | 执行层 Phase 1 现场生成选择题选项 |
| `audit-report-2026-08-10.md` | 本合集审查报告（20 个配合问题） | 合集维护参考 |

> **`references/theme-tokens.md` 是新文件（2026-08-10 审查后新增）**——补齐了原合集"36 主题只有名字没有 CSS 值"的断档，同时加入了 MBB 咨询主题和设计语言映射表。执行层必须读此文件取 token 值。

## 来源与许可

| Skill | 来源 | 许可 |
|-------|------|------|
| axi-front-design | [Diddysister/axi-front-design](https://github.com/Diddysister/axi-front-design) | MIT |
| html-to-pptx | [Hasasasa/claude-skill-html-to-pptx](https://github.com/Hasasasa/claude-skill-html-to-pptx) | MIT |
| ppt-workflow | 基于多次迭代试错总结 | MIT |
| ppt-visual-effects | 基于 ECharts/Three.js/Spline/Shadertoy/Matter.js 社区实践总结 | MIT |
| claude-design | [jiji262/claude-design-skill](https://github.com/jiji262/claude-design-skill) | MIT |
| frontend-design | Anthropic 内置 skill | MIT |
| ui-ux-pro-max | [nextlevelbuilder/ui-ux-pro-max-skill](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill) | MIT |
| mbb-decks | [floflo11/mbb-decks](https://github.com/floflo11/mbb-decks) | MIT |
| docx / pptx | Anthropic 内置 skill | MIT |
| vision-qwen | [223nobody/Deepseek-Vision-Skill](https://github.com/223nobody/Deepseek-Vision-Skill) 改编 | MIT |
| pdf-reading | Anthropic 内置 skill | MIT |

**references/ 资产库来源**：

| 资产 | 内容 | 来源 | 许可 |
|------|------|------|------|
| layout-library | 41 布局（A 叙事 + B 事实 + C Bento） | guizang-ppt-skill + ppt-agent | AGPL / 无 LICENSE → **仅吸收结构** |
| design-system | 41 主题（36 通用 + 4 中国场景 + 1 MBB） | html-ppt-skill + codex-ppt-skill + mbb-decks | MIT |
| canvas-formats | 8 种画布 | ppt-master | MIT |
| image-generation | AI 配图流程 | baoyu-design | MIT |
