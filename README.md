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
4. 首次导出前，在封包根目录运行：

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

## 验证

```powershell
python .\ppt-workflow\scripts\check_workflow_state.py --layer prep --task <task-dir>
python .\ppt-workflow\scripts\check_workflow_state.py --layer decision --task <task-dir>
python .\ppt-workflow\scripts\check_workflow_state.py --layer exec --task <task-dir>
python .\ppt-workflow\scripts\check_workflow_state.py --layer deliver --task <task-dir>
```

## 依赖与来源

运行时需要 Python 3.10+、Playwright 和 PowerPoint/PDF 处理依赖；`bootstrap-runtime.ps1` 会完成转换器的运行时初始化。各组成部分的上游来源与许可证说明保留在对应技能文件中。
