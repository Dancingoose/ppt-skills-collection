#!/usr/bin/env python3
"""Fail-closed validation for PPT workflow evidence stored in workflow-state.json."""
import argparse
import importlib.util
import json
import re
import sys
from pathlib import Path

DATA_LAYOUTS = {"A3", "B2", "B6", "B7", "B18", "B20", "B21", "B22"}
LAYOUT_RE = re.compile(r"^[ABC](?:[1-9]|1[0-9]|2[0-2])$")

# These constraints come from references/layout-library.md.  The manifest and
# the rendered slide must both declare the repeated-item count, so a layout
# label cannot silently mask an incompatible amount of material.
LAYOUT_ITEM_LIMITS = {
    "A3": (4, 6),
    "B4": (6, 6),
    "B5": (3, 3),
    "B7": (5, 10),
    "B9": (3, 3),
    "B11": (4, 7),
    "B13": (3, 3),
    "B18": (3, 3),
    "B19": (4, 4),
    "B20": (4, 6),
    "B22": (3, 3),
}


class Validator:
    def __init__(self):
        self.failures = []
        self.passes = []

    def require(self, condition, message):
        (self.passes if condition else self.failures).append(message)

    def value(self, obj, key, label):
        value = obj.get(key) if isinstance(obj, dict) else None
        self.require(isinstance(value, str) and value.strip() and value.strip() not in {"[TBD]", "TODO", "N/A"}, label)
        return value


def load_state(task_dir: Path, v: Validator):
    path = task_dir / "workflow-state.json"
    v.require(path.is_file(), "workflow-state.json exists")
    if not path.is_file():
        return {}
    try:
        state = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        v.require(False, f"workflow-state.json is valid JSON ({exc})")
        return {}
    v.require(state.get("schemaVersion") == 1, "schemaVersion is 1")
    return state


def inventory_section(content, heading):
    match = re.search(rf"(?ms)^## {re.escape(heading)}\s*\n(.*?)(?=^## |\Z)", content)
    return match.group(1).strip() if match else ""


def check_prep(state, task_dir, v):
    inventory_path = task_dir / "content-inventory.md"
    v.require(inventory_path.is_file(), "content-inventory.md exists")
    inventory = inventory_path.read_text(encoding="utf-8", errors="replace") if inventory_path.is_file() else ""
    for heading in ("Core Message", "Data Points", "Page and Chapter Plan"):
        section = inventory_section(inventory, heading)
        unresolved = not section or section.startswith("[") or "[TBD]" in section or "TODO" in section
        v.require(not unresolved, f"content inventory {heading.lower()} is resolved")
    prep = state.get("prep", {})
    v.value(prep, "sourceType", "prep.sourceType is recorded")
    v.value(prep, "coreMessage", "prep.coreMessage is non-empty")
    plan = prep.get("pagePlan", {})
    v.require(isinstance(plan.get("count"), int) and plan["count"] > 0, "prep.pagePlan.count is positive")
    v.require(isinstance(plan.get("chapters"), list) and bool(plan["chapters"]), "prep.pagePlan.chapters is non-empty")
    points = prep.get("dataPoints", [])
    v.require(isinstance(points, list) and bool(points), "prep.dataPoints contains evidence")
    for index, point in enumerate(points, 1):
        v.value(point, "claim", f"data point {index} has a claim")
        v.value(point, "source", f"data point {index} has a source")
        v.require(bool(point.get("url")) or bool(point.get("citation")), f"data point {index} has a URL or citation")


def check_decision(state, task_dir, v):
    decision = state.get("decision", {})
    phase1 = decision.get("phase1", {})
    for key in ("audience", "intent", "coreClaim", "canvas"):
        v.value(phase1, key, f"decision.phase1.{key} is non-empty")
    phase2 = decision.get("phase2", {})
    v.require(isinstance(phase2.get("pageCount"), int) and phase2["pageCount"] > 0, "decision.phase2.pageCount is positive")
    for key in ("theme", "contentHandling", "imageSource"):
        v.value(phase2, key, f"decision.phase2.{key} is non-empty")
    passport = decision.get("passport", {})
    for key in ("theme", "accent", "background", "titleFont", "bodyFont", "style"):
        v.value(passport, key, f"decision.passport.{key} is non-empty")
    review = decision.get("antiTemplateReview", {})
    v.value(review, "reviewer", "anti-template reviewer is named")
    v.require(review.get("result") in {"pass", "revised"}, "anti-template review has a result")
    v.value(review, "notes", "anti-template review has notes")
    preview = decision.get("preview", {})
    preview_name = v.value(preview, "html", "decision preview HTML is recorded")
    preview_path = task_dir / preview_name if isinstance(preview_name, str) else None
    v.require(preview_path is not None and preview_path.is_file(), "decision preview HTML exists")
    preview_html = preview_path.read_text(encoding="utf-8", errors="ignore") if preview_path and preview_path.is_file() else ""
    v.require(slide_count(preview_html) >= 2, "decision preview contains a cover and representative content slide")
    preview_ids = preview.get("slideIds")
    v.require(isinstance(preview_ids, list) and len(preview_ids) >= 2 and all(isinstance(item, int) for item in preview_ids), "decision preview records at least two slide ids")
    if isinstance(preview_ids, list):
        for slide_id in preview_ids:
            v.require(f'data-slide-id="{slide_id}"' in preview_html or f"data-slide-id='{slide_id}'" in preview_html, f"decision preview includes slide {slide_id}")
    v.require(preview.get("result") == "approved", "decision preview is approved before expansion")
    v.value(preview, "notes", "decision preview has approval notes")


def slide_count(html: str):
    return len(re.findall(r"class=[\"'][^\"']*\bslide\b", html))


def check_execution(state, task_dir, v):
    execution = state.get("execution", {})
    passport = state.get("decision", {}).get("passport", {})
    v.require(execution.get("lockedPassport") == passport and bool(passport), "locked passport exactly matches decision passport")
    html_name = execution.get("html")
    html_path = task_dir / html_name if isinstance(html_name, str) else None
    v.require(html_path is not None and html_path.is_file(), "execution HTML exists")
    html = html_path.read_text(encoding="utf-8", errors="ignore") if html_path and html_path.is_file() else ""
    slides = execution.get("slides", [])
    v.require(isinstance(slides, list) and bool(slides), "execution.slides is non-empty")
    v.require(slide_count(html) == len(slides), "HTML slide count matches execution manifest")
    expected_count = state.get("decision", {}).get("phase2", {}).get("pageCount")
    v.require(len(slides) == expected_count, "execution slide count matches approved page count")
    planned_count = state.get("prep", {}).get("pagePlan", {}).get("count")
    v.require(len(slides) == planned_count, "execution slide count matches preparation plan")
    seen_ids = set()
    for item in slides:
        slide_id = item.get("id")
        layout = item.get("layout")
        v.require(isinstance(slide_id, int) and slide_id not in seen_ids, f"slide {slide_id} has a unique id")
        seen_ids.add(slide_id)
        v.require(isinstance(layout, str) and bool(LAYOUT_RE.fullmatch(layout)), f"slide {slide_id} has a valid layout")
        tags = re.findall(r"<[^>]+>", html)
        matching_tag = any(
            re.search(rf"data-slide-id=[\"']{slide_id}[\"']", tag)
            and re.search(rf"data-layout=[\"']{re.escape(layout)}[\"']", tag)
            and re.search(r"class=[\"'][^\"']*\bslide\b", tag)
            for tag in tags
        )
        v.require(matching_tag, f"slide {slide_id} layout is embedded in its HTML container")
        evidence = item.get("layoutEvidence", {})
        item_count = evidence.get("itemCount")
        v.require(isinstance(item_count, int) and item_count >= 0, f"slide {slide_id} records a layout item count")
        source_refs = evidence.get("sourceRefs")
        v.require(isinstance(source_refs, list) and bool(source_refs) and all(isinstance(ref, str) and ref.strip() for ref in source_refs), f"slide {slide_id} records source references for its layout")
        item_count_tag = any(
            re.search(rf"data-slide-id=[\"']{slide_id}[\"']", tag)
            and re.search(rf"data-item-count=[\"']{item_count}[\"']", tag)
            for tag in tags
        )
        v.require(item_count_tag, f"slide {slide_id} HTML agrees with the recorded layout item count")
        if layout in LAYOUT_ITEM_LIMITS and isinstance(item_count, int):
            minimum, maximum = LAYOUT_ITEM_LIMITS[layout]
            v.require(minimum <= item_count <= maximum, f"slide {slide_id} item count fits {layout} ({minimum}-{maximum})")
        content_type = item.get("contentType")
        v.require(content_type in {"cover", "narrative", "qualitative", "data", "process", "comparison", "close"}, f"slide {slide_id} has a valid content type")
        if content_type == "data":
            v.require(layout in DATA_LAYOUTS, f"slide {slide_id} data uses a data layout")
            v.require(bool(item.get("dataSources")), f"slide {slide_id} data has sources")
            if layout in {"A3", "B7", "B18", "B20", "B21", "B22"}:
                numeric_values = evidence.get("numericValues")
                v.require(isinstance(numeric_values, list) and len(numeric_values) == item_count, f"slide {slide_id} data count matches its numeric evidence")
                v.require(isinstance(numeric_values, list) and all(isinstance(value, (int, float)) and not isinstance(value, bool) for value in numeric_values), f"slide {slide_id} numeric evidence contains only numbers")
        else:
            v.require(layout not in DATA_LAYOUTS, f"slide {slide_id} does not misuse a data layout")
        effect = item.get("visualEffect", {})
        v.require(effect.get("status") in {"applied", "skipped"}, f"slide {slide_id} visual effect decision exists")
        v.value(effect, "reason", f"slide {slide_id} visual effect has a reason")
        if effect.get("status") == "applied":
            effect_type = v.value(effect, "type", f"slide {slide_id} applied effect has a type")
            signal = {
                "echarts": r"echarts",
                "three": r"three(?:@|\.module|\.js)",
                "shader": r"x-shader/x-fragment|shader-web-background",
                "matter": r"matter-js|Matter\.Engine",
                "spline": r"spline-viewer",
                "canvas": r"<canvas",
            }.get(effect_type)
            v.require(signal is not None and bool(re.search(signal, html, re.I)), f"slide {slide_id} applied effect is present in HTML")
    colors = [bool(item.get("dark")) for item in slides]
    v.require(not any(colors[i] == colors[i + 1] == colors[i + 2] for i in range(max(0, len(colors) - 2))), "no three consecutive slides share a background mode")
    if len(slides) >= 8:
        v.require(any(colors) and not all(colors), "long deck contains both light and dark rhythm pages")
    source_review = execution.get("sourceVisualReview", {})
    v.require(source_review.get("result") in {"pass", "revised"}, "source HTML visual review has a result")
    reviewed_slides = source_review.get("reviewedSlides")
    v.require(isinstance(reviewed_slides, list) and set(reviewed_slides) == seen_ids
              and len(reviewed_slides) == len(seen_ids),
              "source HTML visual review covers every slide exactly once")
    v.value(source_review, "notes", "source HTML visual review has notes")
    review = execution.get("independentReview", {})
    v.require(review.get("result") in {"pass", "revised"}, "independent execution review has a result")
    v.value(review, "notes", "independent execution review has notes")


def check_delivery(state, task_dir, v):
    delivery = state.get("delivery", {})
    v.require(delivery.get("converterHealthChecked") is True, "converter health check is recorded")
    v.require(delivery.get("canvasRasterizationAcknowledged") is True, "rasterization tradeoff is acknowledged")
    missing = [name for name in ("playwright", "pptx", "lxml", "fontTools", "PIL") if importlib.util.find_spec(name) is None]
    v.require(not missing, "converter Python dependencies are importable" + (f": missing {', '.join(missing)}" if missing else ""))
    if not missing:
        try:
            from playwright.sync_api import sync_playwright
            runtime_script = Path(__file__).resolve().parents[2] / "html-to-pptx" / "scripts"
            sys.path.insert(0, str(runtime_script))
            from browser_runtime import launch_browser
            with sync_playwright() as playwright:
                browser, runtime_name = launch_browser(playwright)
                page = browser.new_page()
                page.set_content("<main>converter health</main>")
                healthy = page.locator("main").inner_text() == "converter health"
                browser.close()
            v.require(healthy, f"Playwright-compatible browser can render a page ({runtime_name})")
        except Exception as exc:
            v.require(False, f"Playwright-compatible browser can render a page ({exc})")
    output = delivery.get("output")
    requested_pptx = state.get("task", {}).get("deliveryFormat") == "pptx"
    if requested_pptx or output is not None:
        v.require(isinstance(output, str) and output.strip() and (task_dir / output).is_file(), "recorded PPTX output exists")
        audit = delivery.get("audit", {})
        expected_pages = state.get("execution", {}).get("slides", [])
        v.require(audit.get("result") in {"pass", "revised"}, "delivery audit has a result")
        v.require(isinstance(audit.get("reviewedPages"), int) and audit["reviewedPages"] == len(expected_pages), "delivery audit reviewed every slide")
        v.value(audit, "notes", "delivery audit has notes")


def main():
    parser = argparse.ArgumentParser(description="Validate structured PPT workflow evidence")
    parser.add_argument("--task", required=True, type=Path)
    parser.add_argument("--layer", required=True, choices=("prep", "decision", "exec", "deliver", "all"))
    args = parser.parse_args()
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    v = Validator()
    state = load_state(args.task, v)
    checks = {"prep": check_prep, "decision": check_decision, "exec": check_execution, "deliver": check_delivery}
    selected = checks if args.layer == "all" else {args.layer: checks[args.layer]}
    for name, check in selected.items():
        if name == "exec":
            check(state, args.task, v)
        elif name == "deliver":
            check(state, args.task, v)
        elif name in {"prep", "decision"}:
            check(state, args.task, v)
        else:
            check(state, v)
    for message in v.passes:
        print(f"[PASS] {message}")
    for message in v.failures:
        print(f"[FAIL] {message}")
    print(f"Summary: {len(v.passes)} pass, {len(v.failures)} fail")
    raise SystemExit(2 if v.failures else 0)


if __name__ == "__main__":
    main()
