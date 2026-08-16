#!/usr/bin/env python3
"""Fail-closed validation for PPT workflow evidence stored in workflow-state.json."""
import argparse
import hashlib
import importlib.util
import json
import re
import sys
from pathlib import Path

DATA_LAYOUTS = {"A3", "B2", "B6", "B7", "B18", "B20", "B21", "B22"}
CARD_GRID_LAYOUTS = {"B4", "B16", "B19", "C8"}
LAYOUT_RE = re.compile(r"^[ABC](?:[1-9]|1[0-9]|2[0-2])$")
COMPOSITION_PATTERNS = {f"P{index:02d}" for index in range(1, 16)}
BOLD_COMPOSITION_PATTERNS = {"P10", "P11", "P12", "P13", "P14", "P15"}
BOLDNESS_PROFILES = {
    1: "conservative",
    2: "measured",
    3: "expressive",
    4: "bold",
    5: "experimental",
}
MAX_COMPOSITION_PATTERN_BY_BOLDNESS = {1: 2, 2: 5, 3: 9, 4: 13, 5: 15}
PHOTO_DEPENDENT_COMPOSITION_PATTERNS = {"P05"}

# These constraints come from references/layout-library.md.  The manifest and
# the rendered slide must both declare the repeated-item count, so a layout
# label cannot silently mask an incompatible amount of material.
LAYOUT_ITEM_LIMITS = {
    "A3": (4, 6),
    "B4": (6, 6),
    "B5": (3, 3),
    "B7": (5, 10),
    "B9": (3, 3),
    "B11": (3, 7),
    "B13": (3, 3),
    "B18": (3, 3),
    "B19": (4, 4),
    "B20": (4, 6),
    "B22": (3, 3),
}

# Material may inform recommendations, but it cannot substitute for the
# creator's explicit choices.
INTENT_QUESTIONS_V1 = (
    ("audience", 1), ("intent", 1), ("coreClaim", 1), ("canvas", 1),
    ("language", 2), ("expectedOutcome", 2), ("useScene", 2), ("deliveryUse", 2),
    ("storyline", 3), ("contentFocus", 3), ("informationDensity", 3), ("referenceStyle", 3),
)
INTENT_QUESTIONS_V2 = (
    ("audience", 1), ("intent", 1), ("coreClaim", 1), ("canvas", 1),
    ("language", 2), ("expectedOutcome", 2), ("useScene", 2), ("deliveryUse", 2),
    ("storyline", 3), ("contentFocus", 3), ("informationDensity", 3),
    ("designBoldness", 3), ("referenceStyle", 3),
)


def intent_questions_for_schema(schema_version):
    return INTENT_QUESTIONS_V2 if schema_version == 2 else INTENT_QUESTIONS_V1


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


def task_artifact_path(task_dir: Path, name):
    if not isinstance(name, str) or not name.strip():
        return None
    try:
        path = (task_dir / name).resolve()
        path.relative_to(task_dir.resolve())
        return path
    except (OSError, ValueError):
        return None


def normalized_sha256(value):
    """Accept standard SHA-256 output from Windows and Python consistently."""
    if not isinstance(value, str):
        return ""
    value = value.strip().lower()
    return value if re.fullmatch(r"[0-9a-f]{64}", value) else ""


def load_json_artifact(task_dir: Path, name, label, v: Validator):
    path = task_artifact_path(task_dir, name)
    v.require(path is not None and path.is_file(), f"{label} artifact exists")
    if path is None or not path.is_file():
        return {}
    try:
        artifact = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        v.require(False, f"{label} artifact is valid JSON ({exc})")
        return {}
    return artifact if isinstance(artifact, dict) else {}


def check_anti_template_artifact(review, task_dir, v):
    v.require(review.get("skill") == "ppt-workflow-review", "anti-template review uses the packaged review skill")
    artifact_name = v.value(review, "artifact", "anti-template review artifact is recorded")
    artifact = load_json_artifact(task_dir, artifact_name, "anti-template review", v)
    v.require(artifact.get("schemaVersion") == 1, "anti-template review artifact has schema version")
    v.require(artifact.get("skill") == "ppt-workflow-review", "anti-template review artifact identifies the review skill")
    v.require(artifact.get("result") == review.get("result"), "anti-template review artifact agrees with the manifest result")
    areas = artifact.get("reviewedAreas")
    v.require(isinstance(areas, list) and {"intent", "evidence", "theme", "typography", "layouts"}.issubset(set(areas)),
              "anti-template review artifact covers intent, evidence, theme, typography, and layouts")
    v.value(artifact, "notes", "anti-template review artifact has notes")


def check_image_sourcing_plan(phase2, task_dir, page_count, v):
    plan = phase2.get("imageSourcingPlan", {})
    v.require(isinstance(plan, dict), "decision image sourcing plan is recorded")
    plan = plan if isinstance(plan, dict) else {}
    artifact_name = v.value(plan, "artifact", "image sourcing plan artifact is recorded")
    artifact_path = task_artifact_path(task_dir, artifact_name)
    v.require(artifact_path is not None and artifact_path.is_file(), "image sourcing plan artifact exists")
    if artifact_path is None or not artifact_path.is_file():
        return {}
    content = artifact_path.read_text(encoding="utf-8", errors="replace")
    entries = re.findall(
        r"(?m)^\|\s*(\d+)\s*\|\s*(supplied-image|web-search|no-image)\s*\|", content,
    )
    page_decisions = {}
    for raw_page, decision in entries:
        page = int(raw_page)
        v.require(page not in page_decisions, f"image sourcing plan records slide {page} once")
        page_decisions[page] = decision
    expected_pages = set(range(1, page_count + 1)) if isinstance(page_count, int) and page_count > 0 else set()
    v.require(set(page_decisions) == expected_pages,
              "image sourcing plan covers every approved slide exactly once")
    v.require(all(decision in {"supplied-image", "web-search", "no-image"} for decision in page_decisions.values()),
              "image sourcing plan uses supported per-slide decisions")
    image_records = {
        page: {"decision": decision, "asset": None}
        for page, decision in page_decisions.items()
    }
    for page, decision in page_decisions.items():
        detail = re.search(rf"(?ms)^###\s*(?:Slide|Page)\s+{page}\b(.*?)(?=^###\s*(?:Slide|Page)\s+\d+\b|\Z)", content)
        detail_text = detail.group(1) if detail else ""
        if decision == "web-search":
            v.require(bool(re.search(r"(?im)^\s*-\s*Candidate URL:\s*https?://\S+", detail_text)),
                      f"image sourcing plan slide {page} records a web candidate URL")
            v.require(bool(re.search(r"(?im)^\s*-\s*License:\s*\S+", detail_text)),
                      f"image sourcing plan slide {page} records a web image license")
            v.require(bool(re.search(r"(?im)^\s*-\s*Attribution:\s*\S+", detail_text)),
                      f"image sourcing plan slide {page} records web image attribution")
            local_file = re.search(r"(?im)^\s*-\s*Local file:\s*(\S+)", detail_text)
            v.require(local_file is not None,
                      f"image sourcing plan slide {page} records a downloaded local file")
            if local_file:
                local_path = task_artifact_path(task_dir, local_file.group(1))
                v.require(local_path is not None and local_path.is_file(),
                          f"image sourcing plan slide {page} downloaded web image exists in the task directory")
                image_records[page]["asset"] = local_file.group(1)
            v.require(bool(re.search(r"(?im)^\s*-\s*Approval:\s*creator-approved\s*$", detail_text)),
                      f"image sourcing plan slide {page} has creator approval for its web image")
        elif decision == "supplied-image":
            supplied_file = re.search(r"(?im)^\s*-\s*(?:Supplied file|Local file|File path):\s*(\S+)", detail_text)
            v.require(supplied_file is not None,
                      f"image sourcing plan slide {page} records its supplied image path")
            if supplied_file:
                supplied_path = task_artifact_path(task_dir, supplied_file.group(1))
                v.require(supplied_path is not None and supplied_path.is_file(),
                          f"image sourcing plan slide {page} supplied image exists in the task directory")
                image_records[page]["asset"] = supplied_file.group(1)
    return image_records


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


def check_intent(state, task_dir, v):
    decision = state.get("decision", {})
    intake = decision.get("intentQuestionnaire", {})
    v.require("intentQuestionnaire" in decision and isinstance(intake, dict), "intent questionnaire is recorded")
    if not isinstance(intake, dict):
        return
    schema_version = intake.get("schemaVersion")
    v.require(schema_version in {1, 2}, "intent questionnaire has a supported schema version")
    questions = intent_questions_for_schema(schema_version)
    question_batch = dict(questions)
    v.require(intake.get("skill") == "ppt-workflow-intake", "intent questionnaire uses the packaged intake skill")
    v.require(intake.get("completed") is True, "intent questionnaire is marked complete")

    responses = intake.get("responses")
    v.require(isinstance(responses, list) and len(responses) == len(questions),
              f"intent questionnaire records exactly {len(questions)} responses")
    seen_ids = set()
    if isinstance(responses, list):
        for response in responses:
            response = response if isinstance(response, dict) else {}
            question_id = response.get("id")
            v.require(question_id in question_batch and question_id not in seen_ids,
                      f"intent response {question_id!r} has a unique required question id")
            if question_id in question_batch:
                seen_ids.add(question_id)
                v.require(response.get("batch") == question_batch[question_id],
                          f"intent response {question_id} is in its required batch")
            v.value(response, "question", f"intent response {question_id!r} records the question")
            v.value(response, "answer", f"intent response {question_id!r} has a creator-confirmed answer")
            v.require(response.get("source") == "creator-confirmed",
                      f"intent response {question_id!r} is creator-confirmed, not inferred")
            v.value(response, "evidence", f"intent response {question_id!r} records creator confirmation evidence")
            if question_id == "designBoldness":
                v.require(response.get("level") in {1, 2, 3, 4, 5},
                          "design boldness response records a level from 1 to 5")
        v.require([response.get("id") if isinstance(response, dict) else None for response in responses]
                  == [question_id for question_id, _ in questions],
                  "intent responses follow the required three-batch question order")
        answers_by_id = {
            response.get("id"): response.get("answer", "").strip()
            for response in responses if isinstance(response, dict) and isinstance(response.get("answer"), str)
        }
        phase1 = decision.get("phase1", {})
        phase1 = phase1 if isinstance(phase1, dict) else {}
        for question_id in ("audience", "intent", "coreClaim", "canvas"):
            v.require(phase1.get(question_id, "").strip() == answers_by_id.get(question_id),
                      f"decision.phase1.{question_id} exactly matches the creator-confirmed intake answer")
    v.require(seen_ids == set(question_batch), "intent questionnaire includes every required question exactly once")

    batches = intake.get("batches")
    v.require(isinstance(batches, list) and len(batches) == 3,
              "intent questionnaire records all three question batches")
    expected_by_batch = {
        batch: [question_id for question_id, expected_batch in questions if expected_batch == batch]
        for batch in (1, 2, 3)
    }
    seen_batches = set()
    if isinstance(batches, list):
        for batch_record in batches:
            batch_record = batch_record if isinstance(batch_record, dict) else {}
            batch = batch_record.get("batch")
            v.require(batch in expected_by_batch and batch not in seen_batches,
                      f"intent batch {batch!r} is uniquely recorded")
            if batch in expected_by_batch:
                seen_batches.add(batch)
                v.require(batch_record.get("questionIds") == expected_by_batch[batch],
                          f"intent batch {batch} contains its required four questions in order")
            v.value(batch_record, "creatorConfirmation",
                    f"intent batch {batch!r} records the creator's response evidence")
        v.require([batch_record.get("batch") if isinstance(batch_record, dict) else None for batch_record in batches] == [1, 2, 3],
                  "intent batches are recorded in creator-response order")
    v.require(seen_batches == {1, 2, 3}, "intent questionnaire records batches 1, 2, and 3")


def check_decision(state, task_dir, v):
    check_intent(state, task_dir, v)
    decision = state.get("decision", {})
    phase1 = decision.get("phase1", {})
    for key in ("audience", "intent", "coreClaim", "canvas"):
        v.value(phase1, key, f"decision.phase1.{key} is non-empty")
    phase2 = decision.get("phase2", {})
    v.require(isinstance(phase2.get("pageCount"), int) and phase2["pageCount"] > 0, "decision.phase2.pageCount is positive")
    v.require(phase2.get("pageCount") == state.get("prep", {}).get("pagePlan", {}).get("count"),
              "decision.phase2.pageCount matches the preparation page plan")
    for key in ("theme", "contentHandling", "imageSource"):
        v.value(phase2, key, f"decision.phase2.{key} is non-empty")
    check_image_sourcing_plan(phase2, task_dir, phase2.get("pageCount"), v)
    intake = decision.get("intentQuestionnaire", {})
    if isinstance(intake, dict) and intake.get("schemaVersion") == 2:
        boldness = phase2.get("designBoldness", {})
        v.require(isinstance(boldness, dict), "decision design boldness is recorded")
        boldness = boldness if isinstance(boldness, dict) else {}
        v.require(boldness.get("level") in {1, 2, 3, 4, 5}, "decision design boldness has a level from 1 to 5")
        v.require(boldness.get("profile") in {"conservative", "measured", "expressive", "bold", "experimental"},
                  "decision design boldness has a supported profile")
        v.require(boldness.get("profile") == BOLDNESS_PROFILES.get(boldness.get("level")),
                  "decision design boldness profile exactly matches its selected level")
        intake_level = next((item.get("level") for item in intake.get("responses", [])
                             if isinstance(item, dict) and item.get("id") == "designBoldness"), None)
        v.require(boldness.get("level") == intake_level,
                  "decision design boldness exactly matches the creator-confirmed intake level")
        motion = phase2.get("motionDelivery", {})
        v.require(isinstance(motion, dict), "decision motion delivery choice is recorded")
        motion = motion if isinstance(motion, dict) else {}
        v.require(motion.get("mode") in {"pptx-static", "pptx-plus-video", "pptx-plus-live-html"},
                  "decision motion delivery mode is supported")
        v.require(motion.get("creatorConfirmed") is True,
                  "decision motion delivery tradeoff is creator-confirmed")
        v.value(motion, "evidence", "decision motion delivery records creator confirmation evidence")
        v.require(boldness.get("level") != 5 or motion.get("mode") in {"pptx-plus-video", "pptx-plus-live-html"},
                  "experimental design boldness requires playable video or live HTML delivery")
    passport = decision.get("passport", {})
    for key in ("theme", "accent", "background", "titleFont", "bodyFont", "style"):
        v.value(passport, key, f"decision.passport.{key} is non-empty")
    v.require(passport.get("backgroundStrategy") in {"uniform", "rhythmic"},
              "decision.passport.backgroundStrategy is uniform or rhythmic")
    v.require(passport.get("primaryBackgroundMode") in {"dark", "light"},
              "decision.passport.primaryBackgroundMode is dark or light")
    review = decision.get("antiTemplateReview", {})
    v.value(review, "reviewer", "anti-template reviewer is named")
    v.require(review.get("result") in {"pass", "revised"}, "anti-template review has a result")
    v.value(review, "notes", "anti-template review has notes")
    check_anti_template_artifact(review, task_dir, v)
    preview = decision.get("preview", {})
    preview_name = v.value(preview, "html", "decision preview HTML is recorded")
    preview_path = task_dir / preview_name if isinstance(preview_name, str) else None
    v.require(preview_path is not None and preview_path.is_file(), "decision preview HTML exists")
    preview_html = preview_path.read_text(encoding="utf-8", errors="ignore") if preview_path and preview_path.is_file() else ""
    page_count = phase2.get("pageCount")
    required_preview_slides = min(2, page_count) if isinstance(page_count, int) and page_count > 0 else 2
    v.require(slide_count(preview_html) >= required_preview_slides,
              f"decision preview contains {required_preview_slides} planned preview slide(s)")
    preview_ids = preview.get("slideIds")
    v.require(isinstance(preview_ids, list) and len(preview_ids) >= required_preview_slides
              and all(isinstance(item, int) for item in preview_ids),
              f"decision preview records at least {required_preview_slides} slide id(s)")
    if isinstance(preview_ids, list):
        for slide_id in preview_ids:
            v.require(f'data-slide-id="{slide_id}"' in preview_html or f"data-slide-id='{slide_id}'" in preview_html, f"decision preview includes slide {slide_id}")
    v.require(preview.get("result") == "approved", "decision preview is approved before expansion")
    v.value(preview, "notes", "decision preview has approval notes")


def slide_count(html: str):
    return len(re.findall(r"class=[\"'][^\"']*\bslide\b", html))


def check_color_continuity_review(review, task_dir, html, html_path, slides, seen_ids, v):
    v.require(review.get("skill") == "ppt-workflow-review", "color continuity review uses the packaged review skill")
    v.require(review.get("result") in {"pass", "revised"}, "color continuity review has a result")
    artifact_name = v.value(review, "artifact", "color continuity review artifact is recorded")
    artifact = load_json_artifact(task_dir, artifact_name, "color continuity review", v)
    v.require(artifact.get("schemaVersion") == 1, "color continuity review artifact has schema version")
    v.require(artifact.get("skill") == "ppt-workflow-review", "color continuity review artifact identifies the review skill")
    v.require(artifact.get("result") == review.get("result"), "color continuity review artifact agrees with the manifest result")

    reviewed_slides = review.get("reviewedSlides")
    artifact_slides = artifact.get("reviewedSlides")
    for label, values in (("manifest", reviewed_slides), ("artifact", artifact_slides)):
        v.require(isinstance(values, list) and set(values) == seen_ids and len(values) == len(seen_ids),
                  f"color continuity review {label} covers every slide exactly once")
    actual_html_hash = hashlib.sha256(html_path.read_bytes()).hexdigest() if html_path and html_path.is_file() else ""
    manifest_hash = v.value(review, "htmlSha256", "color continuity review records the reviewed HTML hash")
    artifact_hash = v.value(artifact, "htmlSha256", "color continuity artifact records the reviewed HTML hash")
    v.require(normalized_sha256(manifest_hash) == normalized_sha256(artifact_hash) == actual_html_hash,
              "color continuity review applies to the current execution HTML")
    v.value(review, "notes", "color continuity review has notes")
    v.value(artifact, "notes", "color continuity review artifact has notes")

    expected_by_mode = {
        "dark": [item.get("id") for item in slides if bool(item.get("dark"))],
        "light": [item.get("id") for item in slides if not bool(item.get("dark"))],
    }
    expected_by_mode = {mode: ids for mode, ids in expected_by_mode.items() if ids}
    systems = artifact.get("colorSystems")
    v.require(isinstance(systems, list) and bool(systems), "color continuity artifact has color system records")
    systems_by_mode = {}
    if isinstance(systems, list):
        for system in systems:
            system = system if isinstance(system, dict) else {}
            system_id = v.value(system, "id", "color system has an id")
            mode = system.get("mode")
            v.require(mode in expected_by_mode and mode not in systems_by_mode,
                      f"color system {system_id!r} has a unique represented mode")
            if mode in expected_by_mode and mode not in systems_by_mode:
                systems_by_mode[mode] = system
                v.require(system.get("slides") == expected_by_mode[mode],
                          f"{mode} color system covers its exact slide sequence")
            base_color = system.get("baseColor")
            v.require(isinstance(base_color, str) and bool(re.fullmatch(r"#[0-9A-Fa-f]{6}", base_color)),
                      f"color system {system_id!r} records a hex canvas base color")
            v.require(system.get("temperature") in {"cool", "neutral", "warm"},
                      f"color system {system_id!r} records its visual temperature")
            v.value(system, "dominantSurface", f"color system {system_id!r} records its dominant surface treatment")
            v.value(system, "notes", f"color system {system_id!r} records visual continuity findings")
    v.require(set(systems_by_mode) == set(expected_by_mode), "color continuity artifact covers every represented background mode")

    tags = re.findall(r"<[^>]+>", html)
    for mode, slide_ids in expected_by_mode.items():
        system = systems_by_mode.get(mode, {})
        system_id = system.get("id")
        system_pattern = re.escape(system_id) if isinstance(system_id, str) else r"(?!)"
        for slide_id in slide_ids:
            v.require(any(
                re.search(rf"data-slide-id=[\"']{slide_id}[\"']", tag)
                and re.search(rf"data-color-system=[\"']{system_pattern}[\"']", tag)
                for tag in tags
            ), f"slide {slide_id} embeds its reviewed {mode} color system")


def check_execution(state, task_dir, v):
    check_intent(state, task_dir, v)
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
    intake_schema = state.get("decision", {}).get("intentQuestionnaire", {}).get("schemaVersion")
    phase2 = state.get("decision", {}).get("phase2", {})
    image_records = check_image_sourcing_plan(phase2, task_dir, expected_count, v)
    boldness_level = phase2.get("designBoldness", {}).get("level")
    composition_patterns = []
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
        discoverable_tag = any(
            re.search(rf"data-slide-id=[\"']{slide_id}[\"']", tag)
            and re.search(r"\bdata-pptx-slide\b", tag)
            for tag in tags
        )
        v.require(discoverable_tag, f"slide {slide_id} is explicitly discoverable by the converter")
        evidence = item.get("layoutEvidence", {})
        item_count = evidence.get("itemCount")
        v.require(isinstance(item_count, int) and item_count >= 0, f"slide {slide_id} records a layout item count")
        source_refs = evidence.get("sourceRefs")
        v.require(isinstance(source_refs, list) and bool(source_refs) and all(isinstance(ref, str) and ref.strip() for ref in source_refs), f"slide {slide_id} records source references for its layout")
        image_record = image_records.get(slide_id, {})
        image_asset = image_record.get("asset") if isinstance(image_record, dict) else None
        if image_asset:
            v.require(isinstance(source_refs, list) and image_asset in source_refs,
                      f"slide {slide_id} layout evidence cites its approved image file")
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
        composition = item.get("compositionPattern")
        if intake_schema == 2:
            v.require(composition in COMPOSITION_PATTERNS,
                      f"slide {slide_id} records a supported composition pattern")
            composition_patterns.append(composition)
            pattern_number = int(composition[1:]) if isinstance(composition, str) and composition in COMPOSITION_PATTERNS else 99
            maximum_pattern = MAX_COMPOSITION_PATTERN_BY_BOLDNESS.get(boldness_level, 0)
            v.require(pattern_number <= maximum_pattern,
                      f"slide {slide_id} composition stays within the selected design boldness level")
            if composition in PHOTO_DEPENDENT_COMPOSITION_PATTERNS:
                v.require(image_record.get("decision") in {"supplied-image", "web-search"},
                          f"slide {slide_id} photo-dependent composition has an approved image decision")
            v.require(composition not in {"P14", "P15"}
                      or state.get("decision", {}).get("phase2", {}).get("motionDelivery", {}).get("mode")
                      in {"pptx-plus-video", "pptx-plus-live-html"},
                      f"slide {slide_id} live composition requires playable video or live HTML delivery")
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
                "native-motion": r"data-pptx-motion|@keyframes|\banimation\s*:|\.animate\s*\(",
                "embedded-video": r"data-pptx-video",
            }.get(effect_type)
            v.require(signal is not None and bool(re.search(signal, html, re.I)), f"slide {slide_id} applied effect is present in HTML")
    if intake_schema == 2 and composition_patterns:
        v.require(all(composition_patterns[index:index + 3] != [composition_patterns[index]] * 3
                      for index in range(max(0, len(composition_patterns) - 2))),
                  "composition patterns do not repeat three times consecutively")
        boldness = state.get("decision", {}).get("phase2", {}).get("designBoldness", {}).get("level", 0)
        if boldness in {4, 5}:
            minimum_bold = max(1, (len(slides) + 4) // 5)
            used_bold = sum(pattern in BOLD_COMPOSITION_PATTERNS for pattern in composition_patterns)
            v.require(used_bold >= minimum_bold,
                      "bold design uses bold or experimental compositions on at least 20 percent of slides")
    if len(slides) >= 10:
        grid_indices = [index for index, item in enumerate(slides) if item.get("layout") in CARD_GRID_LAYOUTS]
        maximum_grids = max(1, len(slides) // 5)
        v.require(len(grid_indices) <= maximum_grids,
                  "long deck limits equal-card grid layouts to 20 percent of pages")
        v.require(all(later - earlier >= 4 for earlier, later in zip(grid_indices, grid_indices[1:])),
                  "equal-card grid layouts are separated by at least three non-grid pages")
    colors = [bool(item.get("dark")) for item in slides]
    if passport.get("backgroundStrategy") == "uniform":
        expected_dark = passport.get("primaryBackgroundMode") == "dark"
        v.require(all(color == expected_dark for color in colors),
                  "uniform background strategy keeps every slide in the approved primary mode")
    elif passport.get("backgroundStrategy") == "rhythmic":
        v.require(not any(colors[i] == colors[i + 1] == colors[i + 2] for i in range(max(0, len(colors) - 2))),
                  "rhythmic background strategy has no three consecutive slides in one mode")
        if len(slides) >= 8:
            v.require(any(colors) and not all(colors), "long rhythmic deck contains both light and dark pages")
    effect_scan = execution.get("effectScan", {})
    v.require(effect_scan.get("skill") == "ppt-workflow-effects", "effect scan uses the packaged effects skill")
    scan_name = v.value(effect_scan, "artifact", "effect scan artifact is recorded")
    scan = load_json_artifact(task_dir, scan_name, "effect scan", v)
    v.require(scan.get("schemaVersion") == 1, "effect scan artifact has schema version")
    v.require(scan.get("skill") == "ppt-workflow-effects", "effect scan artifact identifies the effects skill")
    reviewed_slides = effect_scan.get("reviewedSlides")
    v.require(isinstance(reviewed_slides, list) and set(reviewed_slides) == seen_ids
              and len(reviewed_slides) == len(seen_ids),
              "effect scan manifest covers every slide exactly once")
    scan_slides = scan.get("slides")
    v.require(isinstance(scan_slides, list), "effect scan artifact has slide records")
    scan_by_id = {entry.get("id"): entry for entry in scan_slides if isinstance(entry, dict)} if isinstance(scan_slides, list) else {}
    v.require(set(scan_by_id) == seen_ids and len(scan_by_id) == len(seen_ids)
              and isinstance(scan_slides, list) and len(scan_slides) == len(seen_ids),
              "effect scan artifact covers every slide exactly once")
    for item in slides:
        scan_item = scan_by_id.get(item.get("id"), {})
        effect = item.get("visualEffect", {})
        v.require(scan_item.get("status") == effect.get("status"), f"slide {item.get('id')} effect scan agrees with manifest status")
        v.require(scan_item.get("reason") == effect.get("reason"), f"slide {item.get('id')} effect scan agrees with manifest reason")
        if effect.get("status") == "applied":
            v.require(scan_item.get("type") == effect.get("type"), f"slide {item.get('id')} effect scan agrees with manifest type")
    source_review = execution.get("sourceVisualReview", {})
    v.require(source_review.get("result") in {"pass", "revised"}, "source HTML visual review has a result")
    reviewed_slides = source_review.get("reviewedSlides")
    v.require(isinstance(reviewed_slides, list) and set(reviewed_slides) == seen_ids
              and len(reviewed_slides) == len(seen_ids),
              "source HTML visual review covers every slide exactly once")
    v.value(source_review, "notes", "source HTML visual review has notes")
    reviewed_html_hash = v.value(source_review, "htmlSha256", "source HTML visual review records the reviewed HTML hash")
    actual_html_hash = hashlib.sha256(html_path.read_bytes()).hexdigest() if html_path and html_path.is_file() else ""
    v.require(normalized_sha256(reviewed_html_hash) == actual_html_hash, "source HTML has not changed since visual review")
    check_color_continuity_review(execution.get("colorContinuityReview", {}), task_dir, html, html_path, slides, seen_ids, v)
    review = execution.get("independentReview", {})
    v.require(review.get("result") in {"pass", "revised"}, "independent execution review has a result")
    v.value(review, "notes", "independent execution review has notes")


def check_delivery(state, task_dir, v):
    check_intent(state, task_dir, v)
    delivery = state.get("delivery", {})
    phase2 = state.get("decision", {}).get("phase2", {})
    intake_schema = state.get("decision", {}).get("intentQuestionnaire", {}).get("schemaVersion")
    if intake_schema == 2 and phase2.get("motionDelivery", {}).get("mode") == "pptx-plus-live-html":
        v.require(isinstance(delivery.get("output"), str) and delivery.get("output", "").lower().endswith(".pptx"),
                  "live HTML delivery includes a static PPTX fallback output")
        live = delivery.get("liveHtml", {})
        v.require(isinstance(live, dict), "live HTML delivery is recorded")
        live = live if isinstance(live, dict) else {}
        live_name = v.value(live, "output", "live HTML output is recorded")
        live_path = task_artifact_path(task_dir, live_name)
        v.require(live_path is not None and live_path.is_file(), "live HTML output exists")
        playback = live.get("playbackAudit", {})
        v.require(playback.get("result") in {"pass", "revised"}, "live HTML playback audit has a result")
        v.require(playback.get("motionObserved") is True, "live HTML playback audit observed motion")
        v.value(playback, "notes", "live HTML playback audit has notes")
        reviewed_hash = v.value(playback, "htmlSha256", "live HTML playback audit records the reviewed hash")
        actual_hash = hashlib.sha256(live_path.read_bytes()).hexdigest() if live_path and live_path.is_file() else ""
        v.require(normalized_sha256(reviewed_hash) == actual_hash,
                  "live HTML has not changed since playback audit")
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
        audited_pptx_hash = v.value(audit, "pptxSha256", "delivery audit records the audited PPTX hash")
        actual_pptx_hash = hashlib.sha256((task_dir / output).read_bytes()).hexdigest() if isinstance(output, str) and (task_dir / output).is_file() else ""
        v.require(normalized_sha256(audited_pptx_hash) == actual_pptx_hash, "PPTX has not changed since delivery audit")
        audit_name = v.value(audit, "artifact", "delivery audit artifact is recorded")
        artifact = load_json_artifact(task_dir, audit_name, "delivery audit", v)
        v.require(artifact.get("schemaVersion") == 1, "delivery audit artifact has schema version")
        v.require(artifact.get("result") == audit.get("result"), "delivery audit artifact agrees with manifest result")
        v.require(artifact.get("reviewedPages") == audit.get("reviewedPages"), "delivery audit artifact agrees with reviewed page count")
        v.require(normalized_sha256(artifact.get("pptxSha256")) == normalized_sha256(audited_pptx_hash),
                  "delivery audit artifact agrees with PPTX hash")
        v.value(artifact, "renderer", "delivery audit artifact names the rendering engine")
        v.value(artifact, "notes", "delivery audit artifact has notes")


def main():
    parser = argparse.ArgumentParser(description="Validate structured PPT workflow evidence")
    parser.add_argument("--task", required=True, type=Path)
    parser.add_argument("--layer", required=True, choices=("prep", "intent", "decision", "exec", "deliver", "all"))
    args = parser.parse_args()
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    v = Validator()
    state = load_state(args.task, v)
    checks = {"prep": check_prep, "intent": check_intent, "decision": check_decision, "exec": check_execution, "deliver": check_delivery}
    selected = checks if args.layer == "all" else {args.layer: checks[args.layer]}
    for name, check in selected.items():
        if name == "exec":
            check(state, args.task, v)
        elif name == "deliver":
            check(state, args.task, v)
        elif name in {"prep", "decision", "intent"}:
            check(state, args.task, v)
        else:
            check(state, args.task, v)
    for message in v.passes:
        print(f"[PASS] {message}")
    for message in v.failures:
        print(f"[FAIL] {message}")
    print(f"Summary: {len(v.passes)} pass, {len(v.failures)} fail")
    raise SystemExit(2 if v.failures else 0)


if __name__ == "__main__":
    main()
