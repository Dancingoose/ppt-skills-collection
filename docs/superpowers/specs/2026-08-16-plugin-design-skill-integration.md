# PPT 设计编排器与多样化样式库

## 目标

将 `claude-design`、`frontend-design`、`mbb-decks`、`ui-ux-pro-max` 和
`axi-front-design` 组合成 PPT Workflow Studio 的设计编排器。目标不是让每个
skill 机械执行或留下调用痕迹，而是让它们共同扩大设计库，使每个 PPT 默认
获得三套真正不同、可执行且与素材匹配的设计方案。

## 范围

本次只调整以上五个设计与创作 skill。`prep-assets/docx` 与
`prep-assets/pptx` 不在本次打包和门禁范围内。

## 核心架构

前 12 项创作者意图确认和素材盘点完成后，设计编排器按固定顺序吸收五类能
力，产出三份“设计配方”。第 13 项由创作者在可查看的三套样张中选择。选择后，
`axi-front-design` 以配方为唯一视觉依据制作预览与完整 HTML；现有 review、
effects 和 delivery 继续负责审查、视觉增强与交付。

```text
素材盘点 + V3 前 12 项意图确认
  -> 设计编排器
       claude-design：设计语言与美术方向
       ui-ux-pro-max：颜色、字体、图表、动效与可访问性材料
       mbb-decks：叙事、论点、信息结构与图表表达
       frontend-design：独特性与反模板审查
       本地资产库：41 主题、41 布局、15 构图模式
  -> 三套设计配方
  -> axi-front-design：visual-direction-preview.html
  -> 第 13 项视觉样张确认
  -> ppt-workflow-review：正式设计决策
  -> axi-front-design：preview.html、design.html
  -> ppt-workflow-effects -> ppt-workflow-delivery
```

## Skill 分工

### `claude-design`

为三个候选选择跨流派的设计语言，给出各自的设计叙事、字体气质、色彩逻辑、
布局态度与标志性动作。它将 10 种设计语言转译为本地主题和构图选择，而不是
仅在创作者毫无偏好时才触发。明确的创作者风格要求作为其中一个候选的锚点，
其余候选仍需提供有意义的相邻方向。

### `ui-ux-pro-max`

为每个候选补充可检索的颜色、字体、图表、动效和可访问性材料。它的丰富数
据库用于扩大候选的可组合元素，而非取代本地主题 token。每项采用的建议均
要转译为本地 token、图表语言或可访问性约束；不采用时保留理由，避免无根
据的拼贴。

### `mbb-decks`

为所有候选提供内容骨架选项：核心论点、叙事路径、行动标题、数据表达与图
表建议。它贡献结构而非固定的咨询视觉主题。候选可以分别采用编辑叙事、决
策结构或实验科技等不同结构侧重；仅当选中方案确有咨询视觉需求时，才使用
`mbb-consulting` 本地主题。

### `frontend-design`

担任三套候选的设计总监。它检查每套方案是否有与主题相关的独特签名，审查
排版、色彩、信息结构与动效是否服务内容，并拒绝仅换颜色或主题名的伪差异。
它不替代 `ppt-workflow-review`：前者确保方案有设计辨识度，后者验证选定方
案的意图、证据、版式与交付一致性。

### `axi-front-design`

读取完整配方并渲染三套可查看的视觉样张，之后将选定配方落地为
`preview.html` 和 `design.html`。它不重复询问 V3 intake 已完成的项目；前
12 项回答映射为沟通契约，第 13 项样张选择映射为设计方案确认。

## 设计配方

每个候选写入 `design-recipes.json`，而摘要写入
`workflow-state.json` 的 `decision.designRecipes`。每套配方包含：

- 候选名称、适配理由和目标受众；
- 设计语言、叙事姿态与内容结构；
- 本地主题、字体角色、色彩与可访问性约束；
- 布局节奏、构图模式、图片处理与图表语言；
- 一项与主题相关的视觉签名；
- 动效策略及其 HTML/PPTX 交付取舍；
- 各项决定所借鉴的 skill 与来源材料；
- 三套样张的页面 ID 与 HTML 哈希。

配方必须把 `ui-ux-pro-max` 的建议转译到本地设计系统，把 `mbb-decks` 的论
点链映射到页面计划，并把 `claude-design` 的设计语言映射到本地主题和构图。
`axi-front-design` 不得在制作时擅自改变这些锁定决策。

## 多样性与质量门禁

门禁采用失败关闭策略。它要求五个设计视角均有实际落盘产物，不能以
`used/skipped` 声明、自由文本说明或模型自我陈述代替。任何一个环节缺失时，
第 13 项确认、`preview.html`、`design.html` 和 PPTX 交付均不得继续。

在第 13 项确认前，`design-orchestration.json` 必须记录并哈希绑定以下五项
产物：

- `claude-design` 的 `design-directions.md`，其中恰有三条候选方向和主题
  映射；
- `ui-ux-pro-max` 的 `design-research.md`，其中每套候选至少一条被转译为本
  地约束的颜色、字体、图表、动效或可访问性建议；
- `mbb-decks` 的 `ghost-deck.md`，其中每套候选均有页面计划、论点或叙事路
  径；这不要求采用咨询视觉主题；
- `frontend-design` 的 `frontend-design-review.md`，其中审查三套候选的差异
  与模板化风险；
- `axi-front-design` 的 `visual-direction-preview.html`，其中每套候选均有可
  查看样张。

所有桥接 skill 均为固定流程步骤，不再按任务类型被静默跳过。遇到信息不足、
本地数据库未初始化或候选不适用时，必须补齐输入、初始化依赖或产出明确的
替代设计结论；不得绕过该 skill 继续制作。

除上述编排证据外，三套完整配方还必须满足：

- 任意两套候选至少在三个设计轴不同：叙事姿态、构图几何、视觉温度、字体
  语言、信息结构、图片处理、图表语言、动效策略；
- 每套均有本地主题、布局/构图、叙事结构和视觉签名，不能仅替换色彩；
- 每套均能追溯到创作者意图、素材和至少两个设计视角；
- 候选样张必须按配方渲染，并在创作者确认后以哈希绑定；
- 选定配方必须与 `preview.html`、`design.html`、独立审查和交付审计的哈希
  链保持一致。

现有 intent、decision、execution 和 delivery 门禁继续保留。新增的设计编排
门禁在决策层和执行层重复验证五项产物、三套配方、候选差异与哈希连续性。
它不把 skill 名称本身当作质量证明，而是要求每项 skill 的专属产物实际进入
后续配方与样张。

## 插件结构

在 `codex-plugin/skills/` 中为五项能力创建可发现的轻量桥接 skill。桥接
skill 指向 `<collection_root>` 中的权威源文件，要求读取后才能生成相应配方
部分或样张。权威内容保留在现有 `design-assets/` 和 `axi-front-design/` 路径，
避免复制长指令造成漂移。

`ppt-workflow-studio` 负责调度桥接 skill；`ppt-workflow-review`、
`ppt-workflow-effects` 与 `ppt-workflow-delivery` 保持原有职责边界。

## 一致性修复

插件根 skill 的 V3 意图采集说明统一为：前 12 个问题分三批、每批四题完成；
第 13 个视觉样张确认问题在第 4 批完成。现有 intake skill 和验证器仍是权
威定义。

## 测试

新增回归测试，验证决策与执行门禁会拒绝：五项专属产物任一缺失、候选数量
不是三套、候选差异少于三个设计轴、配方缺少主题/结构/签名、采用的外部建
议没有转译、样张或正式 HTML 在审查后变更。新增插件结构测试，验证五个桥
接 skill 存在，且根工作流按既定固定阶段引用它们。
