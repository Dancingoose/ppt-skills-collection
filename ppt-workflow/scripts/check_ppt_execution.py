#!/usr/bin/env python3
"""check_ppt_execution.py — PPT 工作流执行合规检查器

把「靠 agent 自觉打勾」的自检清单，变成「跑脚本拿结果」的强制校验。
在四层各关键节点由 agent 主动调用：`python <合集>/ppt-workflow/scripts/check_ppt_execution.py --layer <layer> --task <任务目录>`。

Layer 参数：
  prep      准备层  — content-inventory.md 存在性/完整性、convert.py 门禁
  decision  决策层  — Phase 1 记录、设计护照字段、反模板审查标记
  exec      执行层  — 布局编号登记、token 一致性、字体、节奏、增强扫描、spec_lock
  deliver   交付层  — convert.py 存在、.config.local.toml、形态确认、audit

用法示例：
  python check_ppt_execution.py --layer prep   --task D:/CLAUDEworkspace/work/AI行业趋势分析
  python check_ppt_execution.py --layer exec   --task D:/CLAUDEworkspace/work/AI行业趋势分析 --html design.html
  python check_ppt_execution.py --layer deliver --task D:/CLAUDEworkspace/work/AI行业趋势分析

退出码：0 = 全部通过；2 = 有 FAIL（agent 必须修正后重跑）；1 = 有 WARN（建议核对）。
"""
import argparse
import os
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# 配色（仅终端友好，不改变功能）
# ---------------------------------------------------------------------------
GREEN = "\033[32m"
YELLOW = "\033[33m"
RED = "\033[31m"
BOLD = "\033[1m"
RESET = "\033[0m"

RESULTS = []  # (layer, check_name, status, msg)  status in {PASS, WARN, FAIL}


def record(layer, name, status, msg=""):
    RESULTS.append((layer, name, status, msg))


def p(name, msg="", layer=None):
    record(layer or "?", name, "PASS", msg)


def w(name, msg="", layer=None):
    record(layer or "?", name, "WARN", msg)


def f(name, msg="", layer=None):
    record(layer or "?", name, "FAIL", msg)


def status_icon(s):
    return {"PASS": f"{GREEN}✅ PASS{RESET}", "WARN": f"{YELLOW}⚠️  WARN{RESET}", "FAIL": f"{RED}❌ FAIL{RESET}"}[s]


# ---------------------------------------------------------------------------
# 检查项实现
# ---------------------------------------------------------------------------

def find_html_files(task_dir: Path):
    """任务目录里所有 .html 文件（含子目录）"""
    return sorted([p for p in task_dir.rglob("*.html") if "audited" not in p.name and "._" not in p.name])


def check_content_inventory(task_dir: Path, layer):
    """准备层 G1：content-inventory.md 存在且含必要字段"""
    ci = task_dir / "content-inventory.md"
    if not ci.exists():
        f("content-inventory.md 落盘", "未找到 content-inventory.md，准备层产出缺失", layer)
        return
    text = ci.read_text(encoding="utf-8", errors="ignore")
    p("content-inventory.md 落盘", str(ci), layer)
    for field, pat in [
        ("源文件/提取方式", r"##\s*源文件|提取方式"),
        ("核心信息", r"##\s*核心信息"),
        ("数据点清单", r"##\s*数据点清单|数据点"),
        ("页数与章节预判", r"##\s*页数与章节预判|页数"),
    ]:
        if re.search(pat, text):
            p(f"content-inventory 含「{field}」", "", layer)
        else:
            f(f"content-inventory 缺「{field}」", "准备层模板要求该节", layer)


def check_convert_py_gate(task_dir: Path, layer, collection_root: Path):
    """准备层/交付层：convert.py 存在"""
    conv = collection_root / "html-to-pptx" / "convert.py"
    if conv.exists():
        p("convert.py 存在", str(conv), layer)
    else:
        f("convert.py 存在", "缺失！需从上游获取或先交付 HTML", layer)


def check_design_passport(task_dir: Path, layer):
    """决策层：设计护照关键字段已填"""
    candidates = ["design-passport.md", "passport.md", "设计护照.md", "content-inventory.md"]
    found = None
    for c in candidates:
        cand = task_dir / c
        if cand.exists():
            found = cand
            break
    if not found:
        w("设计护照存在", "未找到独立护照文件，尝试在 content-inventory.md 中查找字段", layer)
        check_target = task_dir / "content-inventory.md"
    else:
        p("设计护照存在", str(found), layer)
        check_target = found
    if not check_target or not check_target.exists():
        f("设计护照字段", "无法读取护照文件", layer)
        return
    text = check_target.read_text(encoding="utf-8", errors="ignore")
    for field in ["受众", "沟通意图", "核心主张", "画布", "页数", "配色", "字体", "风格方向", "主题方案"]:
        if field in text:
            p(f"设计护照含「{field}」", "", layer)
        else:
            w(f"设计护照缺「{field}」", f"建议补全 {field}（若为快速路径可说明原因）", layer)


def check_phase1_record(task_dir: Path, layer):
    """决策层：Phase 1 沟通契约记录（关键 4 项：受众/意图/主张/画布）"""
    ci = task_dir / "content-inventory.md"
    text = ci.read_text(encoding="utf-8", errors="ignore") if ci.exists() else ""
    for field in ["受众", "画布"]:
        if field in text:
            p(f"Phase 1 含「{field}」", "", layer)
        else:
            w(f"Phase 1 缺「{field}」", "Phase 1 未完整记录，可能导致方向建议无上下文", layer)


def check_anti_template_mark(task_dir: Path, layer):
    """决策层：反模板审查标记（frontend-design 介入痕迹）"""
    ci = task_dir / "content-inventory.md"
    text = ci.read_text(encoding="utf-8", errors="ignore") if ci.exists() else ""
    if re.search(r"反模板|反俗套|frontend-design|审查", text):
        p("反模板审查标记", "", layer)
    else:
        w("反模板审查标记", "未在产出中标记审查结果，建议追加一行（即使结论为无问题）", layer)


def check_layout_registration(html_path: Path, layer):
    """执行层 G4：每页登记布局编号（HTML 注释 LAYOUT: X）"""
    if not html_path.exists():
        f("HTML 存在", f"未找到 {html_path}", layer)
        return
    text = html_path.read_text(encoding="utf-8", errors="ignore")
    slides = re.findall(r'class="slide', text)
    layouts = re.findall(r"LAYOUT:\s*([A-C]\d+)", text)
    if not slides:
        f("slide 容器", "未找到 .slide 容器，可能不是 deck HTML", layer)
        return
    p(f"slide 容器数量 {len(slides)}", "", layer)
    if layouts:
        p(f"布局编号登记 {len(layouts)} 处", f"登记: {layouts[:12]}{'...' if len(layouts) > 12 else ''}", layer)
    else:
        f("布局编号登记", "HTML 中未找到 `LAYOUT: X` 注释，违反 Step 4 强制门禁", layer)
    if len(slides) >= 4:
        if len(layouts) < len(slides) * 0.8:
            w("布局覆盖度", f"仅 {len(layouts)}/{len(slides)} 页登记布局编号，建议全量登记", layer)


def check_token_consistency(html_path: Path, layer):
    """执行层：颜色走 CSS 变量，无硬编码 hex（背景/文字色）"""
    if not html_path.exists():
        return
    text = html_path.read_text(encoding="utf-8", errors="ignore")
    root_has_tokens = bool(re.search(r":root\s*\{[^}]*--(bg|accent|text-1|surface)", text))
    if root_has_tokens:
        p("CSS 变量 token 基线", "", layer)
    else:
        w("CSS 变量 token 基线", "未在 HTML 中找到 :root 语义 token 定义，可能未从 theme-tokens.md 读取", layer)
    # 硬编码 hex 检测（排除 :root 定义、白/黑、注释）
    stripped = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
    stripped = re.sub(r"^\s*--.*$", "", stripped, flags=re.M)
    hardcoded = re.findall(r"#[0-9A-Fa-f]{3,8}\b", stripped)
    root_blocks = re.findall(r":root\s*\{([^}]*)\}", text)
    root_hex = set()
    for block in root_blocks:
        root_hex.update(re.findall(r"#[0-9A-Fa-f]{3,8}\b", block))
    allowed_lower = {"#fff", "#ffffff", "#000", "#000000", "#ff0", "#f00", "#0f0", "#00f", "#0000ff", "#ff0000", "#00ff00"}
    leaks = [h for h in hardcoded if h.upper() not in {x.upper() for x in root_hex} and h.lower() not in allowed_lower]
    if leaks:
        w("硬编码 hex 泄漏", f"检测到 {len(leaks)} 处疑似硬编码色（不含 :root/白黑）: {leaks[:8]}", layer)
    else:
        p("无硬编码 hex 泄漏", "", layer)


def check_font_rule(html_path: Path, layer):
    """执行层：标题字体禁 Inter/Roboto 默认"""
    if not html_path.exists():
        return
    text = html_path.read_text(encoding="utf-8", errors="ignore")
    font_families = re.findall(r"font-family\s*:\s*([^;}]+)", text)
    risky = [ff.strip() for ff in font_families if re.search(r"\bInter\b|\bRoboto\b", ff, re.I)]
    if risky:
        f("字体反俗套", f"标题字体含 Inter/Roboto: {risky[:5]}", layer)
    else:
        p("字体反俗套", "", layer)


def check_rhythm(html_path: Path, layer):
    """执行层：节奏 — 3 页连同样式检查（light/dark 交替）"""
    if not html_path.exists():
        return
    text = html_path.read_text(encoding="utf-8", errors="ignore")
    slide_blocks = re.split(r'class="slide', text)[1:]
    dark_count = sum(1 for b in slide_blocks if "dark" in b[:300].lower())
    if slide_blocks and dark_count == 0 and len(slide_blocks) >= 4:
        w("节奏检查", f"{len(slide_blocks)} 页无 dark 页，建议至少 1 个 hero dark（8 页+ deck）", layer)
    else:
        p("节奏检查", f"{len(slide_blocks)} 页，含 {dark_count} 个 dark 标记", layer)


def check_pointer_events(html_path: Path, layer):
    """执行层：Canvas/WebGL 增强 pointer-events: none"""
    if not html_path.exists():
        return
    text = html_path.read_text(encoding="utf-8", errors="ignore")
    canvases = re.findall(r"<canvas", text)
    three_scripts = re.findall(r"three@|three\.module", text)
    shaders = re.findall(r"x-shader/x-fragment", text)
    if canvases or three_scripts or shaders:
        if canvases:
            pe_none = text.count("pointer-events:none") + text.count("pointer-events: none")
            if pe_none == 0:
                w("pointer-events", f"检测到 {len(canvases)} 个 canvas 但无 pointer-events:none", layer)
            else:
                p("pointer-events", f"{len(canvases)} canvas, {pe_none} 处 pointer-events:none", layer)
        else:
            p("pointer-events", "无 canvas（增强可能走 Three/Shadertoy，需人工确认）", layer)
    else:
        p("pointer-events", "无 Canvas/WebGL 增强", layer)


def check_enhancement_scan(task_dir: Path, layer):
    """执行层 G5：ppt-visual-effects 扫描痕迹"""
    htmls = find_html_files(task_dir)
    injected = 0
    for h in htmls:
        text = h.read_text(encoding="utf-8", errors="ignore")
        if re.search(r"echarts|three@|x-shader|matter-js|spline-viewer|<canvas", text, re.I):
            injected += 1
    if injected:
        p("视觉增强注入", f"{injected} 个 HTML 含增强库引用", layer)
    else:
        w("视觉增强注入", "未检测到增强代码，若为纯文字 deck 属正常，请确认已执行扫描", layer)


def check_spec_lock(html_path: Path, layer):
    """执行层：spec_lock — 主题名是否出现在 HTML"""
    if not html_path.exists():
        return
    text = html_path.read_text(encoding="utf-8", errors="ignore")
    theme_names = ["minimal-white", "swiss-grid", "editorial-serif", "mbb-consulting", "party-gov-red",
                   "aurora", "cyberpunk-neon", "corporate-clean", "academic-defense", "teaching-course",
                   "hand-drawn-tech"]
    hit = [t for t in theme_names if t in text]
    if hit:
        p("主题方案引用", f"HTML 中出现主题名: {hit}", layer)
    else:
        w("主题方案引用", "HTML 中未找到明确主题名标记，无法自动核对 spec_lock", layer)


def check_convert_toml(task_dir: Path, collection_root: Path, layer):
    """交付层：.config.local.toml 已配置"""
    toml = collection_root / "html-to-pptx" / ".config.local.toml"
    if toml.exists():
        p(".config.local.toml 已配置", str(toml), layer)
    else:
        f(".config.local.toml 未配置", "首次使用需弹 AskUserQuestion 配置 fonts.auto_install + audit.mode", layer)


def check_delivery_form(task_dir: Path, layer):
    """交付层：确认交付形态（HTML 或 PPTX）"""
    htmls = find_html_files(task_dir)
    pptx = sorted(task_dir.rglob("*.pptx"))
    if pptx:
        p("PPTX 产物存在", f"{len(pptx)} 个 .pptx", layer)
    elif htmls:
        p("HTML 产物存在", f"{len(htmls)} 个 .html（尚未导出 PPTX）", layer)
    else:
        f("交付产物", "任务目录无 .html 也无 .pptx", layer)
    audited = sorted(task_dir.rglob("*.audited.html"))
    if audited:
        p("视觉 audit 产物", f"{len(audited)} 个 audited.html", layer)
    else:
        w("视觉 audit 产物", "未找到 audited.html，可能未跑视觉 audit 或未生成物料", layer)


# ---------------------------------------------------------------------------
# 各 layer 调度
# ---------------------------------------------------------------------------

def run_layer(layer: str, task_dir: Path, collection_root: Path, html_path: Path | None):
    layer_l = layer.lower()
    if layer_l == "prep":
        check_content_inventory(task_dir, "prep")
        check_convert_py_gate(task_dir, "prep", collection_root)
    elif layer_l == "decision":
        check_phase1_record(task_dir, "decision")
        check_design_passport(task_dir, "decision")
        check_anti_template_mark(task_dir, "decision")
    elif layer_l == "exec":
        if html_path is None:
            htmls = find_html_files(task_dir)
            html_path = htmls[0] if htmls else task_dir / "design.html"
        if not html_path.exists() and html_path.name == "design.html":
            htmls = find_html_files(task_dir)
            if htmls:
                html_path = htmls[0]
        check_layout_registration(html_path, "exec")
        check_token_consistency(html_path, "exec")
        check_font_rule(html_path, "exec")
        check_rhythm(html_path, "exec")
        check_pointer_events(html_path, "exec")
        check_enhancement_scan(task_dir, "exec")
        check_spec_lock(html_path, "exec")
    elif layer_l == "deliver":
        check_convert_py_gate(task_dir, "deliver", collection_root)
        check_convert_toml(task_dir, collection_root, "deliver")
        check_delivery_form(task_dir, "deliver")
    else:
        print(f"未知 layer: {layer}", file=sys.stderr)
        sys.exit(2)


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description="PPT 工作流执行合规检查器")
    ap.add_argument("--layer", required=True, choices=["prep", "decision", "exec", "deliver"],
                    help="检查哪一层")
    ap.add_argument("--task", required=True, help="任务目录绝对路径")
    ap.add_argument("--html", default=None, help="执行层要检查的 HTML 文件（可选，默认取任务目录第一个 .html）")
    ap.add_argument("--collection", default=None, help="合集根目录（默认取本脚本的 ../../ 即合集根）")
    args = ap.parse_args()

    task_dir = Path(args.task)
    if not task_dir.exists():
        print(f"{RED}任务目录不存在: {task_dir}{RESET}", file=sys.stderr)
        sys.exit(2)

    # 合集根：本脚本位于 <合集>/ppt-workflow/scripts/check_ppt_execution.py
    collection_root = Path(args.collection) if args.collection else Path(__file__).resolve().parent.parent.parent

    html_path = Path(args.html) if args.html else None

    run_layer(args.layer, task_dir, collection_root, html_path)

    # 输出报告
    print(f"\n{BOLD}═══ PPT 执行合规检查 · {args.layer} 层 ═══{RESET}\n")
    n_pass = n_warn = n_fail = 0
    for layer, name, status, msg in RESULTS:
        n_pass += status == "PASS"
        n_warn += status == "WARN"
        n_fail += status == "FAIL"
        line = f"  {status_icon(status)} {name}"
        if msg:
            line += f"  {YELLOW}({msg}){RESET}" if status == "WARN" else f"  ({msg})"
        print(line)
    print(f"\n  合计: {GREEN}{n_pass} PASS{RESET} · {YELLOW}{n_warn} WARN{RESET} · {RED}{n_fail} FAIL{RESET}")

    if n_fail:
        print(f"\n{RED}❌ 存在 FAIL 项：修正后重新运行检查，全部 PASS 才进入下一步。{RESET}")
        sys.exit(2)
    if n_warn:
        print(f"\n{YELLOW}⚠️  存在 WARN 项：请核对，确认无碍后继续。{RESET}")
        sys.exit(1)
    print(f"\n{GREEN}✅ 全部通过，可进入下一步。{RESET}")
    sys.exit(0)


if __name__ == "__main__":
    main()
