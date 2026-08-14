---
name: "html-to-pptx"
description: "将 HTML 幻灯片转成可编辑 .pptx。文本→原生文本框、形状→原生 OOXML、复杂装饰→局部截图兜底。字体按需嵌入、CJK 自动适配、含视觉 audit 审查流程。触发：\"HTML转PPT\"\"给同事一份ppt副本\"等。"
---

# html-to-pptx

## 何时触发

用户说出下列任一意图：
- "把这个 HTML / 网页 deck 转成 PPT / pptx"
- "做了 HTML 幻灯片，要给同事一份 ppt"
- "汇报现场不方便放浏览器，想要 ppt 文件"
- 已有 HTML 文件路径 + 提到 ppt / pptx / 演示 / 幻灯片

> ⚠️ **首次使用前**：本 skill 需要 `convert.py` 渲染脚本。请从 [上游仓库](https://github.com/Hasasasa/claude-skill-html-to-pptx) 获取完整脚本文件放入本目录。

## 调用

```bash
python <skill_dir>/convert.py <input.html>
```

- 默认输出到与输入同目录的 `<input>.pptx`
- 字体完全按需：HTML 用到的字体从 Google Fonts 拉取并 subset 嵌入
- HTML 含 CJK 字符会自动种子 Noto Sans SC + Noto Serif SC
- 首次自动 cp 一份 `<input>.audited.html`，所有 audit 修复改副本不改源 HTML

| 选项 | 含义 |
|---|---|
| `--out <path>` | 自定义输出 .pptx 路径 |
| `--keep-screenshots` | 保留每页 HTML 参考截图 |
| `--no-embed-fonts` | 跳过字体嵌入，文件更小但换机会回退到系统字体 |
| `--no-visual-audit` | 关闭视觉 audit 物料产出。日常不要关 |
| `--only-slides N,N,N` | 增量重跑指定页 |
| `--cleanup` | 删除 audit 工作物，只保留 .pptx 和 audited.html |

## 首次使用配置

第一次 convert 前可确认两条偏好（通过 AskUserQuestion 弹窗）：
1. `fonts.auto_install` — 是否自动安装字体到系统（让 WPS/PowerPoint 正确渲染）
2. `audit.mode` — 视觉审查模式：`triage`（默认，主 agent 看缩略图分流）/ `page`（全量每页审查）/ `manual`（人工审查）

没有本机配置时，审计默认走 `triage`，保证转换后有可执行的审查路径；只在用户明确要逐页或人工审查时写入对应模式。`ask` 是显式选择，不是默认门禁。

## 覆盖策略

skill 内部把所有 CSS 翻译成四档输出：
1. **矢量文字** — 文本、颜色、字号、行距 → 可编辑文本框
2. **矢量形状** — bg-color、border、border-radius、线条 → 原生 OOXML 几何
3. **栅格装饰（deco_snapshot）** — gradient、box-shadow、filter、blend-mode → 局部截图底板，文字仍矢量叠加
4. **媒体直传** — SVG、图片、canvas → 嵌入

## 流水线

```
[1 预扫] → [2 测量] → [3 组装] → [4 字体嵌入] → [5a 自检] → [5b 视觉 audit]
```

## 修复纪律

- 收到 audit_findings.md 后，一轮里把所有 finding 都改完，再一次性重跑 convert + audit
- 每个 finding 只做最小局部 HTML 修改
- 同一个 finding 在连续两轮都出现 → sticky 命中，停下来告诉用户
- 本批改完一次性 `python convert.py <input>.audited.html --only-slides <被改页号>`

## 排查路径

80% 的 finding 是档位选错了。看 preflight.json 里元素走了哪条路径：
- 走 `deco_snapshot` 但视觉缺装饰 → 截图前的 hide JS 漏掉了什么
- 走 `text` 但样式没对上 → measure 抓 style 字段不全
- 走 `shape` 但圆角/border 不对 → border-radius 数值或阈值
- 视觉效果完全丢 → 该走 deco_snapshot 但没走，hasComplexDecoration 漏触发
- 文字消失 → 走了截图档但没发对应 text 记录

来源：https://github.com/Hasasasa/claude-skill-html-to-pptx MIT License

## Native Motion

Before browser animation is frozen for static measurement, the converter
captures supported CSS/WAAPI motion and writes native PowerPoint timing,
including composable motion paths, scale, rotation, and click/with/after
sequencing. Read `references/native-motion.md` before authoring or reviewing
an animated deck. Use `data-pptx-motion` for a single effect and
`data-pptx-motion-plan` for multi-stage choreography. For non-native WebGL,
Canvas, shader, or arbitrary JavaScript animation that must play inside the
PPTX, use `data-pptx-video` on the slide and convert with
`--embed-video-motion`; it embeds an offline MP4 rather than launching a
browser companion.
