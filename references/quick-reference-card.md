# 执行前速查卡（Quick Reference Card）

> 给 axi-front-design 执行层 Step 4 用。读此卡代替通读全部 5 个资产库（~120KB），需要具体线框/规则时再按需跳转对应文件。

## Phase 1 材料驱动提问（12 项 · 3 批 · → material-driven-questioning.md）
> 有 content-inventory.md 时，选项由 agent 读材料现场生成（每个选项须能在材料找到出处）；无材料回退通用骨架。
- **第一批**：受众 · 沟通意图 · 核心主张（提炼候选+Other） · 画布（标注材料适配理由）
- **第二批**：语言 · 期望结果（与意图联动） · 场景 · 交付用途
- **第三批**：故事线（从章节骨架推导） · 内容侧重点★ · 信息密度★ · 参考风格★（映射到主题）
- 单批 ≤4 问；材料能确定的维度只给推荐项 + 1-2 备选

## 画布与字号（→ canvas-formats.md）
- 默认 1920×1080，正文 ≥ 24px，标题 64–80px
- 非 16:9 画布：竖屏列数减半/转堆叠，方图中心辐射，横幅仅单行，A4 禁交互

## Token 速查（→ theme-tokens.md）
- 数据护照「主题方案」→ theme-tokens.md → 复制完整 `:root`块到HTML
- 复制时同步检查 `--font-display`：含 Inter/Roboto → 替换为 `'Noto Sans SC','Microsoft YaHei',sans-serif`
- 全部颜色走 `var(--accent)` / `var(--bg)` / `var(--text-1/2/3)` / `var(--surface)` 等 CSS 变量

## 版式 P0 决策（→ layout-library.md L777-824：选版式决策表 + 内容类型匹配规则）
| 内容类型 | 必须用 | 严禁用 |
|---------|--------|--------|
| 有真实数据 | A3/B2/B6/B7/B18/B20/B21/B22（按数据形状选） | B3/B4/B10/B13 |
| 无数据纯定性 | B3/B10/B12/B13/B19 | B6/B7 |
| 封面 | A1/B1 | — |
| 章节/幕 | A2/B3/B10 | — |
| Before/After | A9/B8(恰好2项) | — |
| 流程 | A6/B11(线性)/B14(闭环) | B11≠闭环 |
| 收尾 | A7/A8/B9/B12 | B9每deck仅1次 |

## 节奏硬规则
- 禁连续3页同主题(light/dark)
- 8页+ deck 至少1个 hero dark + 1个 hero light
- 每3-4页插1个 hero（封面/幕封/问题/大引用）
- 先画节奏表（layout-library L836-848 模板），再动手

## 反俗套红线（layout-library L1049-1065 + ppt-workflow 禁止项）
- 事实风(B)直角无阴影(`--radius:0;--shadow:none`)，叙事风(A)/Bento(C)可用圆角
- 卡片填充类型四选一互斥（ink/accent/灰底/描边）
- 禁9px圆形装饰点、禁emoji图标、禁渐变背景、禁accent stripe
- 数据页加来源，标题字体禁Inter/Roboto

## 增强触发（→ ppt-visual-effects）
- 深色封面→Shadertoy（文字>80%则跳过）| 数据页→ECharts | 活力→Canvas粒子 | 3D→Three.js | 物理→Matter.js
- Canvas/WebGL设 `pointer-events:none`，slide隐藏时暂停动画
- 纯文字排版页不加

## 交付门禁
- convert.py 存在？不存在→先告知用户+先交HTML
- Canvas/WebGL→PPTX降级为静态截图（deco_snapshot档，使用已激活 slide 的原生画布尺寸 PNG）
- ECharts 走截图保留视觉；着色器等2-3帧初始化后再截

## 执行门禁速查（6 个 Gate，不可跳过）
| Gate | 位置 | 检查 | 不过的处理 |
|------|------|------|-----------|
| G1 意图采集 | 决策层入口 | 12 项问题按 3 批完成；每项均有创作者确认来源；`check --layer intent` PASS | 停止，不做设计方向、预览或扩展 |
| G2 方案预览 | Step2 展开前 | 设计护照已锁定 + 已有预览HTML | 回到 Step 1 出预览 |
| G3 内容核实 | Step3 选版式前 | content-inventory.md 存在且支撑页数、数据有来源 | 停下列清单问用户补素材/做调研 |
| G4 布局登记 | Step4 生成页面前 | 每页登记布局编号（HTML 注释 `LAYOUT: X`）+ P0 数据匹配 | 没登记=违规，回 Step 4 |
| G5 逐页增强 | Step6 每页后 | ppt-visual-effects 已加载、每页扫过 | 没加载=违规 |
| G6 源页面审查 | Step4 展开完成后 | 逐页查看原生 HTML，排除重叠、裁切、溢出和对比度问题；结果写入 `execution.sourceVisualReview` | 修正 HTML 后重新审查 |
| G7 交付前置 | 交付层入口 | convert.py 存在 + .config.local.toml 已配置 | 缺 convert.py 先交HTML；缺 toml 弹首次配置 |

> **代码化自检（替代纯记忆打勾）**：每层自检读取任务的 `workflow-state.json`，验证非空素材证据、设计护照、逐页布局与增强决策，而非匹配关键词。每页 `layoutEvidence` 必须含 `itemCount` 与 `sourceRefs`，量化版式还须有 `numericValues`；HTML 容器同步写入 `data-item-count`。执行层还必须记录覆盖全部页面的 `sourceVisualReview`，因为 HTML/PPT 对比图只能发现转换差异，不能发现两侧共有的源设计问题。脚本位置为 `<collection_root>/ppt-workflow/scripts/check_workflow_state.py`；从 `ppt-workflow/templates/workflow-state.example.json` 创建任务状态文件。
> ```bash
> python <collection_root>/ppt-workflow/scripts/check_workflow_state.py --layer prep|intent|decision|exec|deliver \
>   --task <task_dir>
> ```

## 四层自检清单速查（完成每层时运行脚本 + 输出打勾结果）
- **准备层**：`check --layer prep` → content-inventory.md 写入 | 素材类型判定 | WebSearch有来源 | 页数预判 | convert.py提前查
- **意图采集层**：`check --layer intent` → 12 项、3 批、每项 `creator-confirmed`、每批创作者回复证据
- **决策层**：`check --layer decision` → 意图采集已通过 | 按场景选skill | 方向名精确 | Phase2完成 | 反模板审查 | 护照4字段填
- **执行层**：`check --layer exec` → 速查卡已读 | 每页布局编号 | 数据版式P0 | B系列直角 | 字体已替换 | 节奏表 | 无3页同主题 | 未漂移 | 逐页扫过 | pointer-events:none | 颜色走变量 | 独立审查
- **交付层**：`check --layer deliver` → convert.py存在 | toml已配置 | 形态确认 | 降级已告知 | audit已跑
