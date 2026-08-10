# 设计系统（Design System）

> **axi-front-design 执行层的 token 基线**。吸收自 html-ppt-skill（lewislulu，MIT License）的 token-driven 设计理念 + codex-ppt-skill（ningzimu，MIT License）的中国场景风格，改写成合集自己的画布规格（1920×1080）与布局库字号体系。
> 核心哲学：**一切颜色、间距、圆角、阴影都走语义化 CSS 变量，切换主题只换一组 token，禁止硬编码颜色值。**
> 主题总数：**41 套**（html-ppt 36 套 + codex 中国场景 4 套 + mbb-consulting 1 套）

## 主题 token 完整值

**本文件第一节只放 token 基线定义和语义类。全部 41 套主题的完整 CSS `:root` token 值见 `references/theme-tokens.md`**——每套主题的 `--bg` / `--accent` / `--font-sans` / `--radius` / `--shadow` 等全部 20+ token 的精确值都在那里。执行层按数据护照的「主题方案」字段 → 查 theme-tokens.md → 把对应 CSS 变量写入 HTML `:root`。

## 与布局库的关系

- `layout-library.md` 定**每页怎么排**（线框、结构、内容-版式匹配）
- 本文档定**整个 deck 用什么颜色/字体/圆角/阴影**（全局 token + 主题）
- 两者独立：布局库的 41 个布局可以配任意一套主题

## 一、语义化 token 基线（默认）

所有组件**只引用 token**，不写死颜色。主题文件通过覆盖 `:root` 变量换肤。

| 类别 | token | 默认值 | 说明 |
|---|---|---|---|
| 背景 | `--bg` | `#ffffff` | 页面主背景 |
| | `--bg-soft` | `#f7f7f8` | 柔和底色（章节区分） |
| | `--surface` | `#ffffff` | 卡片/面板表面 |
| | `--surface-2` | `#f2f2f4` | 次级表面（可点区域） |
| 边框 | `--border` | `rgba(0,0,0,.08)` | 常规描边 |
| | `--border-strong` | `rgba(0,0,0,.16)` | 强调描边 |
| 文字 | `--text-1` | `#111216` | 主文字（标题/正文） |
| | `--text-2` | `#55596a` | 次级文字（说明） |
| | `--text-3` | `#8a8f9e` | 辅助文字（meta/页码） |
| 强调 | `--accent` | `#3b6cff` | 主强调色（唯一视觉锚点） |
| | `--accent-2` | `#7a5cff` | 次强调 |
| | `--accent-3` | `#ff5c8a` | 第三强调 |
| 语义 | `--good` | `#1aaf6c` | 正向 |
| | `--warn` | `#f5a524` | 警示 |
| | `--bad` | `#e0445a` | 负向 |
| 圆角 | `--radius` | `18px` | 卡片 |
| | `--radius-sm` | `12px` | 小组件 |
| | `--radius-lg` | `26px` | 大容器 |
| 阴影 | `--shadow` | `0 10px 30px rgba(18,24,40,.08)` | 常规 |
| | `--shadow-lg` | `0 24px 60px rgba(18,24,40,.14)` | 悬浮 |
| 字体 | `--font-sans` | `'Noto Sans SC','Microsoft YaHei',sans-serif` | 正文（默认无衬线，不含 Inter/Roboto） |
| | `--font-serif` | `'Noto Serif SC','Playfair Display',serif` | 衬线标题/引用 |
| | `--font-mono` | `'JetBrains Mono','IBM Plex Mono',monospace` | 代码/数据 |
| | `--font-display` | `var(--font-sans)` | 标题字体（主题可换） |
| 字距 | `--letter-tight` | `-.03em` | 大标题收紧 |
| | `--letter-normal` | `-.01em` | 常规 |
| 缓动 | `--ease` | `cubic-bezier(.4,0,.2,1)` | 全局过渡 |

> ⚠️ 默认 token 仅作 fallback——**实际字体必须来自数据护照指定的主题**。选择主题后，从 `references/theme-tokens.md` 读取该主题的 `--font-sans` / `--font-display` 并覆盖默认值。合集反俗套规则：标题禁 Inter/Roboto/Arial 默认无衬线——多数主题已内置有性格的字体（如 Space Grotesk / Archivo Black / Playfair Display 等），执行层按主题已有的字体族直接用即可。

## 二、排版体系（语义类，字号由布局库定义）

以下保留 html-ppt 的语义类名（`.kicker`、`.eyebrow`、`.lede`、`.dim` 等），**但字号以布局库为准**（`layout-library.md` 开头 token 基线）。本文档不定义字号——只负责语义类名的用途说明。

| 类 | 字号 | 字重 | 用途 |
|---|---|---|---|
| `.kicker` | 14px | 600 | 页眉引导句，uppercase，accent 色 |
| `.eyebrow` | 13px | 500 | 上方小标签，uppercase，text-3 |
| `h1.title` | 72px | 800 | 主标题 |
| `h2.title` | 54px | 700 | 页内标题 |
| `h3` | 32px | 600 | 栏目标题 |
| `h4` | 22px | 600 | 卡片标题 |
| `.lede` | 22px | 300 | 引子段落，text-2，max-width 62ch |
| `.dim` | — | — | text-2 |
| `.dim2` | — | — | text-3 |

### 字号权威来源：`references/layout-library.md`

**本文档不定义字号。** 字号体系以 `layout-library.md` 开头「设计 token 基线」中的 H1 88–120px / H2 64–80px / H3 32–44px / 正文 22–28px 为准。layout-library 还包含中文标题字号分档规则（1行≤8字 / 2行 / 3行+）和「字号越大越细」原则。

以下语义类名的**用途说明**保留，但 `font-size` 值由布局库决定，执行层不得硬套：

## 三、布局原语（间距 / 网格 / 卡片）

| 类 | 值 | 用途 |
|---|---|---|
| `.stack > * + *` | `margin-top:14px` | 垂直间距 |
| `.row` | `flex; gap:24px` | 水平排布 |
| `.grid` | `display:grid; gap:24px` | 网格 |
| `.g2/.g3/.g4` | 2/3/4 等分列 | 均分 |
| `.center` | 居中 | 居中容器 |
| `.fill` | `flex:1` | 撑满 |
| `.sp-t/.sp-b` | 24px | 内边距 |
| `.mt-s/.mt-m/.mt-l` | 8/18/32px | 上边距 |
| `.mb-s/.mb-m/.mb-l` | 8/18/32px | 下边距 |
| `.card` | surface + border + radius + shadow | 标准卡片 |
| `.card-soft` | surface-2 | 柔和卡片 |
| `.card-outline` | 描边卡 | 锚点框 |
| `.card-accent` | 顶部 3px accent 线 | 强调卡 |
| `.card-hover` | 悬浮上移 + 大阴影 | 交互卡 |
| `.pill` | 圆角胶囊 | 标签 |
| `.pill-accent` | accent 色胶囊 | 强调标签 |
| `.divider` | 1px border | 分隔线 |
| `.divider-accent` | 3px × 72px accent | 强调分隔 |

> ⚠️ 反俗套规则冲突：`--radius:18px` 默认圆角卡 + 阴影，与布局库事实风的"直角无阴影"冲突。**叙事风（A 系列）可用圆角/阴影；事实风（B 系列）必须直角无阴影**——主题通过覆盖 `--radius:0; --shadow:none` 实现。

## 四、页面骨架（chrome 系统）

```
┌────────────────────────────────────────────┐
│ .deck-header  左上栏目  ·  右上页码 12px     │  ← 绝对定位 top
│                                            │
│        .slide 内容区（flex column 垂直居中）  │
│        padding:72px 96px                   │
│                                            │
│ .deck-footer  左下说明  ·  右下进度 12px     │  ← 绝对定位 bottom
│ .progress-bar  底部 3px accent 进度条       │
└────────────────────────────────────────────┘
```

- `.deck`：100vw×100vh，overflow hidden
- `.slide`：绝对定位 inset 0，`display:flex; flex-direction:column; justify-content:center; padding:72px 96px`
- `.slide.is-active`：opacity 1 + translateX 0 + z-index 2；`.is-prev` 左移
- 翻页过渡：`opacity .5s + transform .5s var(--ease)`
- `.notes`：演讲备注默认 `display:none!important`（不显示给观众）
- `@media print`：每页分页，隐藏 header/footer/progress

## 五、主题系统（41 套：36 html-ppt + 4 中国场景 + 1 MBB）

**机制**：每套主题 = 一段覆盖 `:root` 变量的 CSS 块。切换主题只换 `<link>` 的 href 或按 T 键循环。**所有页面组件自动适配，无需改组件代码。**

**完整 token 值**：全部 41 套主题的 `:root` CSS 变量（bg / surface / text-1/2/3 / accent / accent-2/3 / good/warn/bad / grad / radius/shadow / font-sans/font-display/font-serif / letter-tight 全部 20+ token）见 **`references/theme-tokens.md`**。该文件也包含「设计语言 → 主题映射表」。

以下是主题目录（分类 + 一句话气质），方便设计决策层快速浏览——选中主题名后去 theme-tokens.md 取完整 token 值：

### Light & calm（浅色冷静）
| 主题 | 气质 | 适合 |
|---|---|---|
| `minimal-white` | 极简白，克制的文字层级 | 内部汇报、技术评审 |
| `editorial-serif` | Playfair 衬线 + 奶油底 | 品牌故事、长文演讲 |
| `soft-pastel` | 马卡龙渐变 | 产品发布、消费向 |
| `xiaohongshu-white` | 小红书白 + 暖红 accent | 小红书图文、生活美学 |
| `solarized-light` | 低眩光 | 工作坊、教学 |
| `catppuccin-latte` | catppuccin 浅 | 技术分享 |

### Bold & statement（大胆宣言）
| 主题 | 气质 | 适合 |
|---|---|---|
| `sharp-mono` | 纯黑白 + Archivo Black + 硬阴影 | 宣言、冲击视觉 |
| `neo-brutalism` | 厚描边 + 硬阴影 + 明黄 | 创业路演、敢说敢做 |
| `bauhaus` | 几何 + 红黄蓝原色 | 设计 talk、艺术史 |
| `swiss-grid` | 瑞士网格 + Helvetica + 12 栏底纹 | 严肃排版、设计行业 |
| `memphis-pop` | 孟菲斯波普点 + 大字标题 | 年轻、潮流、品牌 |

### Cool & dark（深色冷静）
| 主题 | 气质 | 适合 |
|---|---|---|
| `catppuccin-mocha` | catppuccin 深 | 开发者内部分享 |
| `dracula` | Dracula 紫红 | 代码密集技术分享 |
| `tokyo-night` | 蓝夜 | 冷技术、基础设施 |
| `nord` | 北欧清冷蓝白 | 基础设施、云 |
| `gruvbox-dark` | 温暖复古深 | Terminal 社群 |
| `rose-pine` | 玫瑰松柔和暗 | 设计+开发交界 |
| `arctic-cool` | 蓝/青/石板灰浅 | 商业分析、金融 |

### Warm & vibrant（暖色活力）
| 主题 | 气质 | 适合 |
|---|---|---|
| `sunset-warm` | 橘/珊瑚/琥珀渐变 | 生活方式、奖项 |

### Effect-heavy（特效）
| 主题 | 气质 | 适合 |
|---|---|---|
| `glassmorphism` | 毛玻璃 + 光斑 | Apple 式发布会 |
| `aurora` | 极光渐变 blur | 封面/CTA/结语 |
| `rainbow-gradient` | 彩虹流动渐变 accent | 欢乐、节日 |
| `blueprint` | 蓝图工程网格底纹 | 系统架构、工程 |
| `terminal-green` | 绿屏终端 + 发光字 | CLI、复古朋克 |

### v2 补充
| 主题 | 气质 | 适合 |
|---|---|---|
| `corporate-clean` | 白 + 海军蓝 + Inter | 董事会、B2B、金融保险 |
| `pitch-deck-vc` | YC 白 + 蓝紫渐变 + 大留白 | 融资路演、VC |
| `academic-paper` | 论文白 + 衬线 + 黑墨 | 学术报告、研究分享 |
| `japanese-minimal` | 象牙白 + 朱红 + 极大留白 | 品牌升级、匠人故事 |
| `engineering-whiteprint` | 坐标纸网格 + 海军墨线 + 等宽 | 系统设计、API 文档 |
| `magazine-bold` | 奶油 + 超大 Playfair + 橙 spot | 专栏文章、品牌月刊 |
| `news-broadcast` | 白 + 红竖条 + Oswald 大写 | 新闻、发布通稿 |
| `midcentury` | 奶油 + 芥末/青/焦橙 + 锐利几何 | 设计史、家居美学 |
| `retro-tv` | 暖奶油 + CRT 扫描线 + 琥珀橙 | 怀旧、八零九零 |
| `cyberpunk-neon` | 黑 + 霓虹粉青黄 + 发光 + mono | 黑客、地下文化 |
| `vaporwave` | 深紫 + 粉红青蓝渐变 | 音乐、潮流艺术 |
| `y2k-chrome` | 银铬渐变 + 彩虹 accent + 大圆角 | 千禧怀旧、Gen-Z |

### 中国场景补充（4 套，来自 codex-ppt-skill）+ MBB 咨询（1 套）

> 这 5 套补齐了 36 主题里没有的中国场景和咨询场景。完整 token 值见 `references/theme-tokens.md`。

| 主题 | 核心色 | 气质 | 适合 |
|---|---|---|---|
| `party-gov-red` | 中国红 `#C41E3A` + 暖象牙 `#FFF9F2` + 哑金 `#D6A84B` | 庄严、权威、庄重 | 党政机关汇报、党建学习、国企年度总结、政策宣讲 |
| `academic-defense` | 学术深蓝 `#003F8F` + 研究蓝 `#0B5CAD` + 警示红 `#B5121B` | 正式、学术、证据驱动 | 科研申报答辩、基金申请、论文答辩、课题验收 |
| `courseware-blue` | 学术海军蓝 `#0B2E6D` + 清晰蓝 `#1769AA` + 淡蓝 `#EAF3FB` | 清晰、可信、结构教学 | 高校课程、技术培训、知识科普、专题讲座 |
| `handdrawn-explainer` | 纸白 `#FCFBF7` + 石墨 `#2F3437` + 粉彩蓝/绿/桃/薰衣草 | 亲和、轻压、教学 | 中文技术文章配图、复杂概念解释、知识卡片 |
| `mbb-consulting` | 海军蓝 `#051C2C` + 电光蓝 `#2251FF` + 白 `#FFFFFF` + Georgia + Calibri | MBB 咨询 | 董事会汇报、高管预读、战略咨询报告 |

### 中国场景 4 套（来自 codex-ppt-skill）

> 这 4 套的**完整 CSS `:root` token 值**见 `references/theme-tokens.md`（与其他 37 套一样的 CSS `:root` 格式，可直接复制使用）。以下仅保留视觉规则和特殊约束说明。

#### party-gov-red · 党政红

**HTML 视觉规则**：
- 中文黑体大标题，端庄醒目；红色用于标题/结构强调，金色做克制点缀
- **禁**发光渐变、喜庆红金装饰、卡通化、厚阴影、3D 字
- **禁**编造官方标志/党徽国徽/机构名；只用用户提供素材
- 封面/章节/内容页允许版式差异，不强制每页同构
- 图片用纪实/景观/建筑等相关素材，不做装饰性背景

#### academic-defense · 科研答辩

**HTML 视觉规则**：
- **蓝色管结构，红色管结论**：蓝色用于标题/结构/箭头标签，红色只用于关键结论、风险、突破——不过度高亮
- 学术表格、技术路线图、证据卡片、图注是主力版式；**禁**营销 hero 版式、卡通插画、装饰渐变、无关图标
- 数据/证据优先，信息密度可高，但保持对齐可读
- **禁**编造机构 logo；只用用户提供标识

#### courseware-blue · 教学课件

**HTML 视觉规则**：
- 蓝色系统建立教学结构；辅助色只在需要语义区分时用，且一致应用
- 每页必须图文并茂——图/表/公式/证据/注释选合适组合，**禁**纯文字页、重复卡片网格、默认三列
- 避免过空和长段落；把密集说明转成图解/分组标签/要点
- **禁** AI 感：图内编造文字、发光科技效果、随机装饰物、重复模板感

#### handdrawn-explainer · 手绘技术解释

**HTML 视觉规则**：
- **近白纸底 + 细手绘线 + 浅粉彩**，一页一个核心概念，低到中信息密度，大量留白
- 中央小图 + 3-4 个稀疏标签；手绘箭头、铅笔排线、粉彩强调块、括号注记
- 中文文字少而精，标题克制（中等偏大，不海报化）
- **禁**白板框、马克笔托盘、大卡通角色、密集手写、泛黄纸、贴纸、全页边框、数字 UI 卡

### 主题落地方式（合集内）

**方式一（推荐）：设计护照直接指定主题方向。** 设计决策层从上述主题目录中选定 1-2 套（叙事风/事实风各选），把主题名写进数据护照，axi-front-design 从 `references/theme-tokens.md` 读取该主题的完整 CSS token 值实现 `:root` 变量。

**方式二：HTML 内建主题切换。** 在 HTML 顶部 `:root` 写一套 token，如需多主题对比（方案预览阶段），用 `data-themes` + JS 切换，或直接并列三套独立 CSS。

### 如何新增主题
复制现有主题，改名，只覆盖想改的变量。每套主题保持简洁（覆盖 token 为主，不新增选择器）。**主题是 token 的皮肤，不是新组件。**

### 数据护照 → token 覆盖规则

当数据护照中「主题方案」字段和「主色/强调色/底色」hex 字段同时填写时：

1. **主题方案优先**：先按主题名从 `theme-tokens.md` 读取完整 `:root` 变量组
2. **用户指定品牌色覆盖**：如果用户特别指定了品牌色 hex，仅覆盖主题中的 `--accent` / `--accent-2` / `--accent-3`（三个 accent token），不覆盖 --bg / --text / --radius 等结构 token
3. **没有指定主题时**：从用户指定的主色/强调色/底色 hex 反向匹配最接近的主题（比 hex 距离），落选接近的主题

示例：数据护照写「主题方案: corporate-clean，强调色: #ff6600」→ 执行层用 corporate-clean 的全部 token，只把 `--accent` 从 `#0a2540` 覆盖为 `#ff6600`。

---

# 反 AI 俗套提醒（token 层的隐形约束）

> **完整的反 AI 俗套清单以 `layout-library.md` 末尾「反 AI 俗套清单」为权威来源（13 条，覆盖卡片/图标/透明度/间距/字号/底色/来源等全部维度）。** 以下仅列本文档 token 层独有的约束——与设计系统变量直接相关的红线：

- ❌ 默认 `--font-sans` 含 Inter/Roboto——默认已改为 Noto Sans SC，多数主题自带更丰富的字体族（Archivo Black / Space Grotesk / Playfair Display 等），执行层按主题字体直接用即可，**不要覆盖回 Inter**
- ❌ 无脑用 `--radius:18px` 圆角卡 + 阴影——**事实风必须 `--radius:0` + `--shadow:none`**（直角语言），主题 token 已预设
- ❌ `--grad` 渐变 token 滥用——**渐变只允许在 effect-heavy 主题（aurora/rainbow/vaporwave 等）刻意使用**，叙事风/事实风默认禁渐变
- ❌ 数据页无来源——每个数字主张都要归属
- ❌ 每个内容块都加卡片/边框——留白优先，卡片只承载真正需要分组的信息

---

# 来源与许可

- **token 基线、排版体系、主题目录** 吸收自 [html-ppt-skill](https://github.com/lewislulu/html-ppt-skill)（lewislulu，**MIT License**）
- **中国场景 4 套主题**（party-gov-red / academic-defense / courseware-blue / handdrawn-explainer）吸收自 [codex-ppt-skill](https://github.com/ningzimu/codex-ppt-skill)（ningzimu，**MIT License**）的 `references/*.md` 风格定义

本库只吸收**设计规格、配色值、视觉规则**（原格式为 GPT-Image-2 生图 prompt，已转译为 HTML token 主题），不复制其生图 prompt 原文或实现代码；合集内的实现由 axi-front-design 按 1920×1080 画布与布局库字号体系落地。MIT 许可允许自由使用，引用来源以示尊重。
