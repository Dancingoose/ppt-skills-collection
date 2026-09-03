# PPT Workflow Control Plane Design

**Date:** 2026-09-04  
**Status:** Proposed for implementation after creator review

## Goal

把现有 PPT 制作流程从“可验证的状态快照”升级为“可推进、可审计、可锁定的工作流控制平面”，同时保留现有门禁规则和旧脚本兼容性。

## Scope

本次改造包含四项互相依赖的能力：

1. 统一命令入口，负责任务初始化、状态查看、分层验证、合法推进和最终锁定。
2. 追加式执行日志，记录每次命令、门禁结果、状态哈希和产物哈希。
3. 状态与产物锁定，防止批准后静默修改；修改后必须重新验证并产生新事件。
4. 统一依赖检查和测试入口，让本地运行结果与 CI 运行结果一致。

本次不重写现有的内容盘点、设计编排、HTML 转 PPTX、视觉审查或模板嵌入逻辑；这些模块继续作为被调用的能力提供者。

## Architecture

新增一个薄编排层 `ppt-workflow/scripts/workflow_ctl.py`。它通过子进程调用现有 `check_workflow_state.py`，不复制门禁规则。控制器只负责状态机、证据摘要、哈希和日志。

工作流层级固定为：

```text
prep -> intent -> design -> decision -> exec -> deliver
```

允许从任一已通过层推进到下一层。`verify` 只执行检查，不改变状态；`advance` 必须先执行目标前一层的验证并在成功后更新状态；`seal` 只允许在 `deliver` 通过后执行。

## Command Interface

```text
python workflow_ctl.py init --task <dir> --name <name> --format <html|pptx>
python workflow_ctl.py status --task <dir>
python workflow_ctl.py verify --task <dir> --layer <prep|intent|design|decision|exec|deliver|all>
python workflow_ctl.py advance --task <dir> --to <intent|design|decision|exec|deliver>
python workflow_ctl.py seal --task <dir>
python workflow_ctl.py log --task <dir>
```

命令约定：

- 所有路径必须解析在任务目录内；禁止通过 `..` 写入任务目录之外。
- `init` 不覆盖已有 `workflow-state.json`，除非显式传入 `--force`；`--force` 只允许任务目录尚未存在控制日志时使用。
- `verify` 返回码沿用现有门禁：`0` 表示通过，非 `0` 表示阻塞，并始终把输出摘要写入日志。
- `advance` 不允许跳层、不允许回退、不允许绕过门禁。
- `seal` 写入最终状态哈希和事件链头哈希；之后任何受控文件变化都会使 `status` 显示 `drifted`，必须重新验证。

## State Contract

在现有 `workflow-state.json` 顶层增加 `control` 对象，不改变现有 `schemaVersion`：

```json
{
  "control": {
    "currentLayer": "prep",
    "status": "active",
    "toolVersion": "1",
    "stateSha256": "<64 hex chars>",
    "eventHeadSha256": "<64 hex chars or empty>",
    "sealedAt": null
  }
}
```

状态值只有 `active`、`blocked`、`sealed`、`drifted`。`currentLayer` 表示最后一个成功完成的层；初始化任务为 `prep`，但只有 `verify prep` 成功后才允许推进到 `intent`。

状态哈希计算使用稳定 JSON 序列化：UTF-8、按键排序、紧凑分隔符，并排除 `control.stateSha256` 与 `control.eventHeadSha256` 字段本身，避免自引用。

## Event Log Contract

任务目录新增 `workflow-events.jsonl`。每行一个 JSON 事件，事件不可修改，只能追加：

```json
{
  "schemaVersion": 1,
  "eventId": "uuid",
  "timestamp": "2026-09-04T00:00:00Z",
  "command": "verify",
  "fromLayer": "prep",
  "toLayer": "prep",
  "result": "pass",
  "stateSha256": "<64 hex chars>",
  "artifactHashes": {},
  "gateSummary": {"pass": 6, "fail": 0},
  "previousEventSha256": "<64 hex chars or empty>",
  "eventSha256": "<64 hex chars>"
}
```

`eventSha256` 对除自身外的规范化事件字段计算；`previousEventSha256` 形成单向事件链。日志损坏、重复事件哈希或链头不匹配时，`status` 返回 `drifted` 并以非零退出。

## Dependency and Test Entry

新增 `ppt-workflow/scripts/bootstrap.ps1`，默认只检查依赖；传入 `-Install` 才执行两个 requirements 文件的安装。新增 `scripts/run-tests.ps1`，使用 Python `unittest discover` 运行两个测试树，并在开始前验证 `openpyxl`、`defusedxml`、`pptx`、`lxml`、`fontTools`、`playwright` 和 `PIL`。

缺少依赖时，脚本必须列出缺失包和可复制的安装命令，不能报告“测试通过”。

## Error Handling and Compatibility

- 控制器遇到 JSON 损坏、非法层级、哈希漂移、门禁失败或日志链损坏时立即停止，不自动修复用户文件。
- 现有 `check_workflow_state.py`、`check_ppt_execution.py` 和 `convert.py` 的命令行行为保持不变。
- 旧任务没有 `control` 或事件日志时，`verify` 仍可直接运行；`status` 将其标记为 `legacy-unmanaged`，`advance` 要求先运行迁移式 `init --adopt`。
- 不自动安装字体、不自动下载素材、不自动覆盖用户产物。

## Testing Requirements

新增单元测试覆盖：

- 初始化不会覆盖现有状态。
- 只能按顺序推进，不能跳层或回退。
- 门禁失败时状态和层级不改变。
- 状态哈希排除自引用字段且能检测外部修改。
- 事件日志按链头校验，篡改和截断均失败闭合。
- `seal` 只接受交付层通过状态。
- 缺少依赖时测试入口返回非零并列出包名。

验收标准：

1. 新任务可以只通过 `workflow_ctl.py` 完成初始化、逐层验证、推进和锁定。
2. 任意受控产物在批准后被修改，`status` 和下一次 `advance` 都会阻止继续。
3. 旧门禁测试行为不回归，转换器测试继续通过；缺失依赖会被明确报告而不是静默跳过。
4. 文档包含从初始化到交付的可复制命令示例。
