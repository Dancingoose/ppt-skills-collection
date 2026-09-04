# PPT Workflow Studio

一个可下载、可复用的 PPT 制作工作流封包。它采用 HTML-first 设计与可编辑 PPTX 导出，并通过结构化任务状态、素材溯源和交付审查保证质量。

## 包含内容

- `codex-plugin/`：Codex 插件入口与分阶段技能。
- `ppt-workflow/`：任务状态模板、素材盘点和分层验证脚本。
- `html-to-pptx/`：HTML 转原生可编辑 PPTX 的转换器与测试。
- `axi-front-design/`、`ppt-visual-effects/`：页面设计和逐页视觉增强规则。
- `design-assets/`、`prep-assets/`、`references/`：设计、素材读取和版式参考资产。

封包不包含任何示例报告、演示 PPT、任务输出、本地配置或历史审计记录。

## 在 Codex 中使用

1. 下载整个 `ppt-skills-collection/` 文件夹。
2. 将 `PPT_WORKFLOW_ROOT` 指向该文件夹；未设置时，插件按自身安装位置解析集合根目录。
3. 将 `codex-plugin/` 作为 Codex 本地插件安装，或使用 `codex-plugin/scripts/deploy-plugin.ps1` 部署到本地插件目录。
4. 首次使用前，在封包根目录运行 Python 与浏览器依赖初始化：

```powershell
.\ppt-workflow\scripts\bootstrap.ps1 -Install
```

该命令会安装两个子项目的 Python 依赖和 Playwright Chromium，并检查 Python 导入及可选的 FFmpeg 配置。它不安装或探测 PowerPoint、LibreOffice、Poppler；视觉审计需 Windows PowerPoint，或 LibreOffice 加 Poppler。需要视频动效或视频嵌入时，Windows 还需安装带 `libx264` 的 FFmpeg；可使用 `winget install --id Gyan.FFmpeg.Essentials --exact`，或设置 `PPT_FFMPEG_EXECUTABLE` 指向已有的 `ffmpeg.exe`。

只初始化 HTML 转换器运行时时，也可运行：

```powershell
.\html-to-pptx\scripts\bootstrap-runtime.ps1
```

5. 使用 `ppt-workflow-studio` 创建或修订演示文稿。工作流会在素材盘点、意图确认、设计审查、执行和交付阶段运行验证。

## 工作流原则

- 先盘点证据和意图，再设计与导出；不编造数据。
- 先制作 HTML 设计稿，再转换为可编辑 PPTX；不直接用 `python-pptx` 或 `pptxgenjs` 拼装页面。
- 每页选择与信息形状匹配的版式并记录依据。
- 10 页及以上的演示文稿中，等宽卡片网格页最多占 20%，且两页之间至少间隔 3 页非网格页面，避免模板化重复。
- 交付前验证 HTML/PPT 渲染、字体、裁切、来源和审计记录。
- 用户要求保留既有模板时，使用追加式模板嵌入：原模板页面、Logo 背景、母版、布局、主题和媒体保持不变，仅从批准的背景页克隆并填充新增内容页；交付前必须生成模板完整性审计。

## 验证

新任务建议使用可审计控制器逐层推进：

```powershell
python .\ppt-workflow\scripts\workflow_ctl.py init --task .\tasks\demo --name demo --format pptx
python .\ppt-workflow\scripts\workflow_ctl.py verify --task .\tasks\demo --layer prep
python .\ppt-workflow\scripts\workflow_ctl.py advance --task .\tasks\demo --to intent
python .\ppt-workflow\scripts\workflow_ctl.py status --task .\tasks\demo
python .\ppt-workflow\scripts\workflow_ctl.py log --task .\tasks\demo
```

完成 `deliver` 门禁后执行 `seal` 锁定交付状态。控制器会记录状态哈希、产物哈希和追加式事件链；旧任务仍可直接运行下方门禁脚本。

```powershell
python .\ppt-workflow\scripts\check_workflow_state.py --layer prep --task <task-dir>
python .\ppt-workflow\scripts\check_workflow_state.py --layer decision --task <task-dir>
python .\ppt-workflow\scripts\check_workflow_state.py --layer exec --task <task-dir>
python .\ppt-workflow\scripts\check_workflow_state.py --layer deliver --task <task-dir>
```

完成最终 HTML 和执行清单后，在执行门禁前同步增量演示协议；之后任一 HTML 或清单变更都需要重新同步：

```powershell
python .\ppt-workflow\scripts\presentation_protocol.py sync --task <task-dir>
```

模板保真嵌入还需要执行：

```powershell
python .\ppt-workflow\scripts\template_embedding.py inspect --template <template.pptx> --out <task-dir>\template-embedding-plan.json
python .\ppt-workflow\scripts\template_embedding.py clone --template <template.pptx> --out <task-dir>\working-template.pptx --source-slide <approved-slide> --count <new-page-count>
python .\ppt-workflow\scripts\template_embedding.py verify --template <template.pptx> --output <task-dir>\final.pptx --report <task-dir>\template-integrity-audit.json
```

## 依赖与来源

运行时需要 Python 3.10+、Playwright Chromium、PPTX/PDF 处理依赖，以及 Windows PowerPoint（用于 COM 渲染和视频嵌入）。LibreOffice 加 Poppler 可作为跨平台视觉审计渲染器。视频动效额外需要带 `libx264` 的 FFmpeg；bootstrap 会验证其可执行性和编码器支持，并在缺失时给出配置提示。各组成部分的上游来源与许可证说明保留在对应技能文件中。
