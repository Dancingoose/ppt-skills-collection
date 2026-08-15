#!/usr/bin/env python3
"""Fail-closed validation for PPT workflow evidence stored in workflow-state.json."""
import argparse
import hashlib
import importlib.util
import itertools
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
INTENT_QUESTIONS_V3 = (
    ("audience", 1), ("intent", 1), ("coreClaim", 1), ("canvas", 1),
    ("language", 2), ("expectedOutcome", 2), ("useScene", 2), ("deliveryUse", 2),
    ("storyline", 3), ("contentFocus", 3), ("informationDensity", 3),
    ("designBoldness", 3), ("visualSampleConfirmation", 4),
)
PAGE_ARCHETYPES = {
    "hero", "context", "evidence", "data", "comparison", "process", "transition",
    "recommendation", "action",
}
COMPOSITION_FAMILIES = {
    "modular-grid", "asymmetric-columns", "full-bleed-sequence", "editorial-stack",
    "process-flow", "matrix", "timeline", "single-axis", "comparison-split",
}
DESIGN_ORCHESTRATION_SKILLS = (
    "claude-design", "ui-ux-pro-max", "mbb-decks",
    "frontend-design", "axi-front-design",
)
DESIGN_ORCHESTRATION_FILES = {
    "claude-design": "design-directions.md",
    "ui-ux-pro-max": "design-research.md",
    "mbb-decks": "ghost-deck.md",
    "frontend-design": "frontend-design-review.md",
    "axi-front-design": "visual-direction-preview.html",
}
DESIGN_AXES = (
    "narrativeStance", "compositionGeometry", "visualTemperature",
    "typographicLanguage", "informationStructure", "imageTreatment",
    "chartLanguage", "motionStrategy",
)


def intent_questions_for_schema(schema_version):
    if schema_version == 3:
        return INTENT_QUESTIONS_V3
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


def canonical_sha256(value):
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


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
    v.require(schema_version in {1, 2, 3}, "intent questionnaire has a supported schema version")
    design_profile = decision.get("designProfile", {})
    pre_design_v3 = (
        schema_version == 3
        and not design_profile
        and "designOrchestration" not in decision
        and "designRecipes" not in decision
    )
    questions = INTENT_QUESTIONS_V3[:12] if pre_design_v3 else intent_questions_for_schema(schema_version)
    question_batch = dict(questions)
    expected_batch_order = list(dict.fromkeys(batch for _, batch in questions))
    expected_by_batch = {
        batch: [question_id for question_id, expected_batch in questions if expected_batch == batch]
        for batch in expected_batch_order
    }
    v.require(intake.get("skill") == "ppt-workflow-intake", "intent questionnaire uses the packaged intake skill")
    revision_requested = (
        schema_version == 3
        and isinstance(design_profile, dict)
        and design_profile.get("status") == "revision-requested"
    )
    if pre_design_v3:
        v.require(intake.get("completed") is False,
                  "pre-design intent questionnaire remains incomplete before visual samples")
    else:
        v.require(intake.get("completed") is True or revision_requested,
                  "intent questionnaire is marked complete")

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
                  "intent responses follow the required question order")
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
    v.require(isinstance(batches, list) and len(batches) == len(expected_batch_order),
              "intent questionnaire records all required question batches")
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
                          f"intent batch {batch} contains its required questions in order")
            v.value(batch_record, "creatorConfirmation",
                    f"intent batch {batch!r} records the creator's response evidence")
        v.require([batch_record.get("batch") if isinstance(batch_record, dict) else None for batch_record in batches] == expected_batch_order,
                  "intent batches are recorded in creator-response order")
    for batch in expected_batch_order:
        v.require(batch in seen_batches, f"intent batch {batch} is recorded")
    v.require(seen_batches == set(expected_batch_order),
              "intent questionnaire records every required batch exactly once")


def check_design_profile(decision, task_dir, v):
    """Validate V3 visual samples while allowing an unapproved revision record."""
    profile = decision.get("designProfile", {})
    v.require(isinstance(profile, dict), "decision design profile is recorded")
    profile = profile if isinstance(profile, dict) else {}
    v.require(profile.get("schemaVersion") == 1, "design profile has schema version 1")
    status = profile.get("status")
    v.require(status in {"confirmed", "revision-requested"},
              "design profile has a supported status")

    preview_name = v.value(profile, "previewArtifact", "design profile preview artifact is recorded")
    preview_path = task_artifact_path(task_dir, preview_name)
    v.require(preview_path is not None and preview_path.is_file(),
              "design profile preview artifact exists")
    preview_html = preview_path.read_text(encoding="utf-8", errors="ignore") if preview_path and preview_path.is_file() else ""

    candidates = profile.get("candidates")
    v.require(isinstance(candidates, list) and len(candidates) == 3,
              "design profile records exactly 3 candidates")
    candidates = candidates if isinstance(candidates, list) else []
    required_sources = [question_id for question_id, _ in INTENT_QUESTIONS_V3[:12]]
    contract_keys = (
        "narrativeStance", "compositionGeometry", "visualTemperature", "typographicLanguage",
        "backgroundStrategy", "primaryBackgroundMode", "compositionFamily",
    )
    candidate_ids = []
    contracts = {}
    for candidate in candidates:
        candidate = candidate if isinstance(candidate, dict) else {}
        candidate_id = v.value(candidate, "id", "visual candidate has an id")
        if isinstance(candidate_id, str):
            candidate_ids.append(candidate_id)
        v.value(candidate, "name", f"visual candidate {candidate_id!r} has a name")
        v.value(candidate, "rationale", f"visual candidate {candidate_id!r} has a rationale")
        v.require(candidate.get("sourceQuestionIds") == required_sources,
                  f"visual candidate {candidate_id} cites the first 12 V3 intake questions in order")
        contract = candidate.get("visualContract")
        v.require(isinstance(contract, dict), f"visual candidate {candidate_id} records a visual contract")
        contract = contract if isinstance(contract, dict) else {}
        for key in contract_keys:
            v.value(contract, key, f"visual candidate {candidate_id} visual contract has {key}")
        v.require(contract.get("backgroundStrategy") in {"uniform", "rhythmic"},
                  f"visual candidate {candidate_id} background strategy is supported")
        v.require(contract.get("primaryBackgroundMode") in {"dark", "light"},
                  f"visual candidate {candidate_id} primary background mode is supported")
        v.require(contract.get("compositionFamily") in COMPOSITION_FAMILIES,
                  f"visual candidate {candidate_id} composition family is supported")
        if isinstance(candidate_id, str):
            contracts[candidate_id] = contract
            marker = rf"data-design-profile=[\"']{re.escape(candidate_id)}[\"']"
            v.require(bool(re.search(marker, preview_html)),
                      f"visual direction preview embeds candidate {candidate_id}")
            family_marker = rf"data-composition-family=[\"']{re.escape(str(contract.get('compositionFamily')))}[\"']"
            v.require(bool(re.search(rf"<[^>]*{marker}[^>]*{family_marker}[^>]*>", preview_html)),
                      f"visual direction preview records candidate {candidate_id} composition family")
    v.require(len(candidate_ids) == len(set(candidate_ids)), "visual candidate ids are unique")
    for first_id, second_id in itertools.combinations(candidate_ids, 2):
        first_contract = contracts.get(first_id, {})
        second_contract = contracts.get(second_id, {})
        differences = sum(first_contract.get(key) != second_contract.get(key) for key in contract_keys)
        v.require(differences >= 3,
                  f"visual candidates {first_id} and {second_id} differ in at least 3 visual contract dimensions")
    composition_families = [contracts[item].get("compositionFamily") for item in candidate_ids if item in contracts]
    v.require(len(composition_families) == len(set(composition_families)),
              "visual candidates use distinct composition families")

    intake = decision.get("intentQuestionnaire", {})
    completed = intake.get("completed") if isinstance(intake, dict) else None
    responses = intake.get("responses") if isinstance(intake, dict) else []
    responses = responses if isinstance(responses, list) else []
    sample_answer = next((response.get("answer") for response in responses
                          if isinstance(response, dict) and response.get("id") == "visualSampleConfirmation"), None)
    if status == "confirmed":
        selected_profile_id = profile.get("selectedProfileId")
        v.require(selected_profile_id in candidate_ids,
                  "confirmed design profile selects one proposed candidate")
        v.value(profile, "creatorConfirmation", "confirmed design profile records creator confirmation")
        v.value(profile, "evidence", "confirmed design profile records confirmation evidence")
        v.require(completed is True, "confirmed design profile has a completed visual sample questionnaire")
        v.require(sample_answer == selected_profile_id,
                  "visual sample confirmation answer exactly matches the selected design profile")
    elif status == "revision-requested":
        v.value(profile, "revisionFeedback", "revision-requested design profile records revision feedback")
        v.require(completed is False,
                  "revision-requested design profile keeps the visual sample questionnaire incomplete")
    return status == "confirmed"


def check_design_orchestration(decision, task_dir, v, html_path=None):
    """Require the fixed design-skill chain and bind its output to the task."""
    orchestration = decision.get("designOrchestration", {})
    v.require(isinstance(orchestration, dict), "design orchestration is recorded")
    orchestration = orchestration if isinstance(orchestration, dict) else {}
    v.require(orchestration.get("schemaVersion") == 1, "design orchestration has schema version 1")
    artifact_name = v.value(orchestration, "artifact", "design orchestration artifact is recorded")
    artifact_path = task_artifact_path(task_dir, artifact_name)
    v.require(artifact_path is not None and artifact_path.is_file(), "design orchestration artifact exists")
    artifact_document = load_json_artifact(task_dir, artifact_name, "design orchestration", v)
    actual_orchestration_hash = hashlib.sha256(artifact_path.read_bytes()).hexdigest() if artifact_path and artifact_path.is_file() else ""
    recorded_orchestration_hash = v.value(orchestration, "sha256", "design orchestration artifact records its SHA-256")
    v.require(normalized_sha256(recorded_orchestration_hash) == actual_orchestration_hash,
              "design orchestration artifact hash matches the current file")
    v.require(artifact_document.get("schemaVersion") == 1, "design orchestration artifact has schema version 1")

    bindings = decision.get("intentBindings", {})
    bindings_hash = canonical_sha256(bindings) if isinstance(bindings, dict) else ""
    v.require(normalized_sha256(orchestration.get("intentBindingsSha256")) == bindings_hash,
              "design orchestration is bound to the current intent constraints")
    v.require(artifact_document.get("intentBindingsSha256") == orchestration.get("intentBindingsSha256"),
              "design orchestration artifact agrees with intent constraint binding")

    records = orchestration.get("artifacts")
    v.require(isinstance(records, list) and [item.get("skill") for item in records if isinstance(item, dict)]
              == list(DESIGN_ORCHESTRATION_SKILLS)
              and [item.get("file") for item in records if isinstance(item, dict)]
              == [DESIGN_ORCHESTRATION_FILES[skill] for skill in DESIGN_ORCHESTRATION_SKILLS],
              "design orchestration records every required skill artifact")
    v.require(artifact_document.get("artifacts") == records,
              "design orchestration artifact agrees with the manifest skill artifacts")
    records = records if isinstance(records, list) else []
    expected_input_hash = bindings_hash
    for record in records:
        record = record if isinstance(record, dict) else {}
        skill = record.get("skill")
        filename = record.get("file")
        path = task_artifact_path(task_dir, filename)
        v.require(path is not None and path.is_file(), f"design orchestration {skill} artifact exists")
        actual_hash = hashlib.sha256(path.read_bytes()).hexdigest() if path and path.is_file() else ""
        v.require(normalized_sha256(record.get("inputSha256")) == expected_input_hash,
                  "design orchestration artifact input hash chain is continuous")
        content = path.read_text(encoding="utf-8", errors="ignore") if path and path.is_file() else ""
        v.require(bool(re.search(rf"Input SHA-256:\s*{re.escape(expected_input_hash)}\b", content, re.I)),
                  f"design orchestration {skill} artifact records its reviewed input hash")
        v.require(normalized_sha256(record.get("sha256")) == actual_hash,
                  f"design orchestration {skill} artifact hash matches the current file")
        expected_input_hash = actual_hash

    recipes = decision.get("designRecipes")
    v.require(isinstance(recipes, list) and len(recipes) == 3,
              "design orchestration records exactly three design recipes")
    recipes = recipes if isinstance(recipes, list) else []
    v.require(artifact_document.get("recipes") == recipes,
              "design orchestration artifact and manifest agree on design recipes")
    recipe_ids = []
    for recipe in recipes:
        recipe = recipe if isinstance(recipe, dict) else {}
        recipe_id = v.value(recipe, "id", "design recipe has an id")
        if isinstance(recipe_id, str):
            recipe_ids.append(recipe_id)
        for key in ("theme", "signature", *DESIGN_AXES):
            v.value(recipe, key, f"design recipe {recipe_id!r} has {key}")
        lenses = recipe.get("sourceLenses")
        v.require(isinstance(lenses, list) and lenses == list(DESIGN_ORCHESTRATION_SKILLS),
                  "every design recipe uses every required design skill lens")
        sample_slide_ids = recipe.get("sampleSlideIds")
        v.require(isinstance(sample_slide_ids, list) and len(sample_slide_ids) >= 2
                  and all(isinstance(slide_id, int) for slide_id in sample_slide_ids),
                  f"design recipe {recipe_id!r} records sample slide ids")
        constraints = recipe.get("adoptedConstraints")
        v.require(isinstance(constraints, list) and bool(constraints)
                  and all(isinstance(item, str) and item.strip() for item in constraints),
                  "design recipe translates ui-ux-pro-max research")
    v.require(len(recipe_ids) == 3 and len(recipe_ids) == len(set(recipe_ids)),
              "design recipe ids are unique")
    for first, second in itertools.combinations(recipes, 2):
        first = first if isinstance(first, dict) else {}
        second = second if isinstance(second, dict) else {}
        differences = sum(first.get(axis) != second.get(axis) for axis in DESIGN_AXES)
        v.require(differences >= 3, "design recipes differ across at least three design axes")

    selected_recipe_id = orchestration.get("selectedRecipeId")
    profile = decision.get("designProfile", {})
    profile = profile if isinstance(profile, dict) else {}
    v.require(selected_recipe_id in recipe_ids and selected_recipe_id == profile.get("selectedProfileId"),
              "selected design recipe matches the confirmed design profile")
    v.require(artifact_document.get("selectedRecipeId") == selected_recipe_id,
              "design orchestration artifact locks the selected design recipe")

    preview_name = profile.get("previewArtifact")
    preview_path = task_artifact_path(task_dir, preview_name)
    preview_html = preview_path.read_text(encoding="utf-8", errors="ignore") if preview_path and preview_path.is_file() else ""
    preview_hash = hashlib.sha256(preview_path.read_bytes()).hexdigest() if preview_path and preview_path.is_file() else ""
    v.require(normalized_sha256(orchestration.get("previewSha256")) == preview_hash,
              "design orchestration preview hash matches the current file")
    v.require(artifact_document.get("previewSha256") == orchestration.get("previewSha256"),
              "design orchestration artifact agrees with preview hash")
    for recipe_id in recipe_ids:
        v.require(bool(re.search(rf"data-design-recipe=[\"']{re.escape(recipe_id)}[\"']", preview_html)),
                  f"design orchestration preview embeds recipe {recipe_id}")

    if html_path is not None:
        execution_hash = hashlib.sha256(html_path.read_bytes()).hexdigest() if html_path.is_file() else ""
        v.require(normalized_sha256(orchestration.get("executionHtmlSha256")) == execution_hash,
                  "design orchestration execution hash matches the current HTML")
    return orchestration


def check_v3_intent_bindings(decision, v):
    """Require V3 answers to become explicit content, composition, and delivery constraints."""
    bindings = decision.get("intentBindings", {})
    v.require(isinstance(bindings, dict), "V3 intent bindings are recorded")
    bindings = bindings if isinstance(bindings, dict) else {}
    v.require(bindings.get("creatorConfirmed") is True,
              "V3 intent bindings are creator-confirmed")
    v.value(bindings, "evidence", "V3 intent bindings record creator evidence")

    responses = decision.get("intentQuestionnaire", {}).get("responses", [])
    responses = responses if isinstance(responses, list) else []
    answers = {
        item.get("id"): item.get("answer", "").strip()
        for item in responses if isinstance(item, dict) and isinstance(item.get("answer"), str)
    }
    design_boldness = next((item.get("level") for item in responses
                            if isinstance(item, dict) and item.get("id") == "designBoldness"), None)

    content = bindings.get("content", {})
    v.require(isinstance(content, dict), "V3 content intent bindings are recorded")
    content = content if isinstance(content, dict) else {}
    for key, question_id in (("storyline", "storyline"), ("focus", "contentFocus"), ("density", "informationDensity")):
        v.require(content.get(key) == answers.get(question_id),
                  f"V3 content binding {key} exactly matches the creator answer")
    for key, label in (("mustInclude", "content must-include boundaries"), ("mustAvoid", "content must-avoid boundaries")):
        value = content.get(key)
        v.require(isinstance(value, list) and bool(value) and all(isinstance(item, str) and item.strip() for item in value), label)

    composition = bindings.get("composition", {})
    v.require(isinstance(composition, dict), "V3 composition intent bindings are recorded")
    composition = composition if isinstance(composition, dict) else {}
    v.require(composition.get("boldnessLevel") == design_boldness,
              "V3 composition boldness binding exactly matches the creator answer")
    v.value(composition, "densityRule", "V3 composition binding records an information-density rule")
    visual_avoid = composition.get("visualMustAvoid")
    v.require(isinstance(visual_avoid, list) and bool(visual_avoid)
              and all(isinstance(item, str) and item.strip() for item in visual_avoid),
              "visual composition must-avoid boundaries")

    delivery = bindings.get("delivery", {})
    v.require(isinstance(delivery, dict), "V3 delivery intent bindings are recorded")
    delivery = delivery if isinstance(delivery, dict) else {}
    for key, question_id in (("expectedOutcome", "expectedOutcome"), ("useScene", "useScene"), ("deliveryUse", "deliveryUse")):
        v.require(delivery.get(key) == answers.get(question_id),
                  f"V3 delivery binding {key} exactly matches the creator answer")
    delivery_constraints = delivery.get("mustSupport")
    v.require(isinstance(delivery_constraints, list) and bool(delivery_constraints)
              and all(isinstance(item, str) and item.strip() for item in delivery_constraints),
              "delivery must-support boundaries")


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
    design_profile_confirmed = True
    if isinstance(intake, dict) and intake.get("schemaVersion") == 3:
        design_profile_confirmed = check_design_profile(decision, task_dir, v)
        check_v3_intent_bindings(decision, v)
        check_design_orchestration(decision, task_dir, v)
        v.require(design_profile_confirmed, "design profile is confirmed before formal decision")
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
    if intake.get("schemaVersion") == 3:
        profile = decision.get("designProfile", {})
        selected_id = profile.get("selectedProfileId")
        selected = next((candidate for candidate in profile.get("candidates", [])
                         if isinstance(candidate, dict) and candidate.get("id") == selected_id), {})
        passport_profile = passport.get("designProfile", {})
        v.require(passport_profile.get("id") == selected_id,
                  "passport locks the selected design profile id")
        v.require(passport_profile.get("visualContract") == selected.get("visualContract"),
                  "passport locks the selected design profile visual contract")
        selected_contract = selected.get("visualContract", {}) if isinstance(selected, dict) else {}
        v.require(passport.get("backgroundStrategy") == selected_contract.get("backgroundStrategy"),
                  "passport background strategy matches the selected visual contract")
        v.require(passport.get("primaryBackgroundMode") == selected_contract.get("primaryBackgroundMode"),
                  "passport primary background mode matches the selected visual contract")
        v.require(passport_profile.get("visualContract", {}).get("compositionFamily") == selected_contract.get("compositionFamily"),
                  "passport composition family matches the selected visual contract")
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


def check_v3_execution_reviews(execution, task_dir, html_path, slides, seen_ids, selected_profile_id, v):
    rhythm = execution.get("deckRhythmReview", {})
    v.require(rhythm.get("skill") == "ppt-workflow-review", "deck rhythm review uses the packaged review skill")
    artifact_name = v.value(rhythm, "artifact", "deck rhythm review artifact is recorded")
    artifact = load_json_artifact(task_dir, artifact_name, "deck rhythm review", v)
    v.require(artifact.get("schemaVersion") == 1, "deck rhythm review artifact has schema version")
    v.require(artifact.get("skill") == "ppt-workflow-review", "deck rhythm review artifact identifies the review skill")
    v.require(artifact.get("result") == rhythm.get("result") and rhythm.get("result") in {"pass", "revised"},
              "deck rhythm review artifact has an approved result")
    sequence = [{"id": item.get("id"), "archetype": item.get("archetype"),
                 "compositionFamily": item.get("compositionFamily")} for item in slides]
    v.require(artifact.get("archetypeSequence") == sequence, "deck rhythm review matches the execution archetype sequence")
    archetypes = [item.get("archetype") for item in slides]
    v.require(not any(archetypes[index:index + 3] == [archetypes[index]] * 3
                      for index in range(max(0, len(archetypes) - 2))),
              "deck rhythm has no three consecutive matching archetypes")
    if len(slides) >= 10:
        available = set(archetypes)
        v.require({"hero", "action"}.issubset(available) and bool({"data", "evidence"} & available),
                  "long deck includes hero, evidence or data, and action archetypes")
        v.require("transition" in available, "long deck includes an intentional transition archetype")

    review = execution.get("designProfileReview", {})
    v.require(review.get("skill") == "ppt-workflow-review", "design profile review uses the packaged review skill")
    review_name = v.value(review, "artifact", "design profile review artifact is recorded")
    profile_artifact = load_json_artifact(task_dir, review_name, "design profile review", v)
    v.require(profile_artifact.get("schemaVersion") == 1, "design profile review artifact has schema version")
    v.require(profile_artifact.get("skill") == "ppt-workflow-review", "design profile review artifact identifies the review skill")
    v.require(profile_artifact.get("result") == review.get("result") and review.get("result") in {"pass", "revised"},
              "design profile review artifact has an approved result")
    expected_hash = hashlib.sha256(html_path.read_bytes()).hexdigest() if html_path and html_path.is_file() else ""
    for source in (review, profile_artifact):
        v.require(source.get("selectedProfileId") == selected_profile_id,
                  "design profile review locks the selected profile")
        reviewed = source.get("reviewedSlides")
        v.require(isinstance(reviewed, list) and set(reviewed) == seen_ids and len(reviewed) == len(seen_ids),
                  "design profile review covers every slide exactly once")
        v.require(normalized_sha256(source.get("htmlSha256")) == expected_hash,
                  "design profile review applies to the current execution HTML")
    dimensions = profile_artifact.get("reviewedDimensions")
    v.require(isinstance(dimensions, list) and {"typography", "spacing", "imageTreatment", "chartLanguage", "composition"}.issubset(dimensions),
              "design profile review covers typography, spacing, image treatment, chart language, and composition")
    v.require(isinstance(profile_artifact.get("exceptions"), list), "design profile review records exceptions as a list")
    v.value(review, "notes", "design profile review has notes")
    v.value(profile_artifact, "notes", "design profile review artifact has notes")


def check_v3_intent_continuity_review(state, task_dir, html_path, slides, seen_ids, v):
    """Verify that intent, approved preview, source HTML, and delivery review remain one chain."""
    execution = state.get("execution", {})
    decision = state.get("decision", {})
    review = execution.get("intentContinuityReview", {})
    v.require(review.get("skill") == "ppt-workflow-review",
              "intent continuity review uses the packaged review skill")
    artifact_name = v.value(review, "artifact", "intent continuity review artifact is recorded")
    artifact = load_json_artifact(task_dir, artifact_name, "intent continuity review", v)
    v.require(artifact.get("schemaVersion") == 1, "intent continuity review artifact has schema version")
    v.require(artifact.get("skill") == "ppt-workflow-review",
              "intent continuity review artifact identifies the review skill")
    v.require(review.get("result") in {"pass", "revised"}, "intent continuity review has an approved result")
    v.require(artifact.get("result") == review.get("result"),
              "intent continuity review artifact agrees with the manifest result")

    preview = decision.get("preview", {})
    preview = preview if isinstance(preview, dict) else {}
    preview_name = preview.get("html") if isinstance(preview, dict) else None
    preview_path = task_artifact_path(task_dir, preview_name)
    preview_hash = hashlib.sha256(preview_path.read_bytes()).hexdigest() if preview_path and preview_path.is_file() else ""
    execution_hash = hashlib.sha256(html_path.read_bytes()).hexdigest() if html_path and html_path.is_file() else ""
    for source in (review, artifact):
        v.require(normalized_sha256(source.get("previewSha256")) == preview_hash,
                  "intent continuity review applies to the current approved preview")
        v.require(normalized_sha256(source.get("executionHtmlSha256")) == execution_hash,
                  "intent continuity review applies to the current execution HTML")

    intent_responses = decision.get("intentQuestionnaire", {}).get("responses", [])
    intent_responses = intent_responses if isinstance(intent_responses, list) else []
    expected_intent_ids = [item.get("id") for item in intent_responses if isinstance(item, dict)]
    expected_slide_ids = [item.get("id") for item in slides]
    v.require(artifact.get("intentQuestionIds") == expected_intent_ids,
              "intent continuity review covers every confirmed intent answer in order")
    v.require(artifact.get("previewSlideIds") == preview.get("slideIds"),
              "intent continuity review covers the approved preview slides")
    v.require(artifact.get("executionSlideIds") == expected_slide_ids,
              "intent continuity review covers every execution slide")
    selected_id = decision.get("designProfile", {}).get("selectedProfileId")
    v.require(artifact.get("selectedProfileId") == selected_id,
              "intent continuity review locks the selected visual profile")
    bindings = decision.get("intentBindings", {})
    v.require(artifact.get("intentBindingsSha256") == canonical_sha256(bindings),
              "intent continuity review locks the current intent bindings")

    checks = artifact.get("checks")
    v.require(isinstance(checks, dict), "intent continuity review records its quality-loop checks")
    checks = checks if isinstance(checks, dict) else {}
    for key in ("intentToPreview", "previewToExecution", "executionToDelivery"):
        v.require(checks.get(key) == "pass", f"intent continuity check {key} passes")
    v.require(isinstance(artifact.get("revisionRound"), int) and artifact["revisionRound"] >= 1,
              "intent continuity review records a revision round")
    v.require(isinstance(artifact.get("exceptions"), list),
              "intent continuity review records exceptions as a list")
    v.value(review, "notes", "intent continuity review has notes")
    v.value(artifact, "notes", "intent continuity review artifact has notes")


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
    selected_recipe_id = state.get("decision", {}).get("designOrchestration", {}).get("selectedRecipeId")
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
        if intake_schema == 3:
            v.require(any(
                re.search(rf"data-slide-id=[\"']{slide_id}[\"']", tag)
                and re.search(rf"data-design-recipe=[\"']{re.escape(selected_recipe_id) if isinstance(selected_recipe_id, str) else '(?!)'}[\"']", tag)
                for tag in tags
            ), f"slide {slide_id} embeds the confirmed design recipe")
            archetype = item.get("archetype")
            v.require(archetype in PAGE_ARCHETYPES, f"slide {slide_id} has a supported page archetype")
            v.require(any(
                re.search(rf"data-slide-id=[\"']{slide_id}[\"']", tag)
                and re.search(rf"data-archetype=[\"']{re.escape(archetype) if isinstance(archetype, str) else '(?!)'}[\"']", tag)
                for tag in tags
            ), f"slide {slide_id} archetype is embedded in its HTML container")
            composition_family = item.get("compositionFamily")
            v.require(composition_family in COMPOSITION_FAMILIES,
                      f"slide {slide_id} has a supported composition family")
            v.require(any(
                re.search(rf"data-slide-id=[\"']{slide_id}[\"']", tag)
                and re.search(rf"data-composition-family=[\"']{re.escape(composition_family) if isinstance(composition_family, str) else '(?!)'}[\"']", tag)
                for tag in tags
            ), f"slide {slide_id} composition family is embedded in its HTML container")
            background_mode = "dark" if bool(item.get("dark")) else "light"
            v.require(any(
                re.search(rf"data-slide-id=[\"']{slide_id}[\"']", tag)
                and re.search(rf"data-background-mode=[\"']{background_mode}[\"']", tag)
                for tag in tags
            ), f"slide {slide_id} background mode is embedded in its HTML container")
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
    if intake_schema == 3:
        families = [item.get("compositionFamily") for item in slides]
        v.require(not any(families[index:index + 3] == [families[index]] * 3
                          for index in range(max(0, len(families) - 2))),
                  "composition families do not repeat three times consecutively")
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
    if intake_schema == 3:
        check_design_orchestration(state.get("decision", {}), task_dir, v, html_path)
        check_v3_execution_reviews(
            execution, task_dir, html_path, slides, seen_ids,
            state.get("decision", {}).get("designProfile", {}).get("selectedProfileId"), v,
        )
        check_v3_intent_continuity_review(state, task_dir, html_path, slides, seen_ids, v)
    review = execution.get("independentReview", {})
    v.require(review.get("result") in {"pass", "revised"}, "independent execution review has a result")
    v.value(review, "notes", "independent execution review has notes")


def check_delivery(state, task_dir, v):
    check_intent(state, task_dir, v)
    delivery = state.get("delivery", {})
    phase2 = state.get("decision", {}).get("phase2", {})
    intake_schema = state.get("decision", {}).get("intentQuestionnaire", {}).get("schemaVersion")
    if intake_schema == 3:
        check_execution(state, task_dir, v)
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
        if intake_schema == 3:
            high_risk_pages = audit.get("unresolvedHighRiskPages")
            structural_warnings = audit.get("structuralWarnings")
            v.require(high_risk_pages == [], "V3 delivery has zero unresolved high-risk preflight pages")
            v.require(structural_warnings == 0, "V3 delivery has zero structural self-check warnings")

            checks = artifact.get("checks")
            v.require(isinstance(checks, dict), "V3 delivery audit artifact has converter checks")
            checks = checks if isinstance(checks, dict) else {}
            preflight = checks.get("preflight")
            v.require(isinstance(preflight, dict), "V3 delivery audit artifact has preflight evidence")
            preflight = preflight if isinstance(preflight, dict) else {}
            v.require(preflight.get("status") == "pass", "V3 delivery preflight evidence passes")
            v.require(preflight.get("highRiskPages") == high_risk_pages,
                      "V3 delivery preflight evidence agrees with unresolved high-risk pages")

            self_check = checks.get("structuralSelfCheck")
            v.require(isinstance(self_check, dict), "V3 delivery audit artifact has structural self-check evidence")
            self_check = self_check if isinstance(self_check, dict) else {}
            v.require(self_check.get("status") == "pass", "V3 delivery structural self-check evidence passes")
            warning_count = self_check.get("warningCount")
            if not isinstance(warning_count, int):
                known_counts = [self_check.get("layoutOverlaps"), self_check.get("fullSlidePictures")]
                warning_count = sum(known_counts) if all(isinstance(count, int) for count in known_counts) else None
            v.require(warning_count == structural_warnings,
                      "V3 delivery structural self-check evidence agrees with warning count")

        native_motion_slides = [
            slide.get("id") for slide in expected_pages
            if isinstance(slide, dict)
            and isinstance(slide.get("visualEffect"), dict)
            and slide["visualEffect"].get("status") == "applied"
            and slide["visualEffect"].get("type") == "native-motion"
        ]
        if native_motion_slides:
            motion_audit = delivery.get("motionAudit", {})
            v.require(isinstance(motion_audit, dict), "native motion audit is recorded")
            motion_audit = motion_audit if isinstance(motion_audit, dict) else {}
            v.require(motion_audit.get("result") == "pass", "native motion audit passes")
            reviewed = motion_audit.get("reviewedSlides")
            v.require(isinstance(reviewed, list) and set(native_motion_slides).issubset(set(reviewed)),
                      "native motion audit reviewed every animated slide")
            motion_hash = v.value(motion_audit, "pptxSha256", "native motion audit records the audited PPTX hash")
            v.require(normalized_sha256(motion_hash) == actual_pptx_hash,
                      "PPTX has not changed since native motion audit")
            motion_name = v.value(motion_audit, "artifact", "native motion audit artifact is recorded")
            motion_artifact = load_json_artifact(task_dir, motion_name, "native motion audit", v)
            v.require(motion_artifact.get("schemaVersion") == 1,
                      "native motion audit artifact has schema version")
            v.require(motion_artifact.get("kind") == "native-motion-audit",
                      "native motion audit artifact has native-motion kind")
            v.require(motion_artifact.get("result") == "pass",
                      "native motion audit artifact passes")
            v.require(normalized_sha256(motion_artifact.get("pptxSha256")) == actual_pptx_hash,
                      "native motion audit artifact agrees with PPTX hash")
            audited_slides = {
                slide.get("index"): slide for slide in motion_artifact.get("slides", [])
                if isinstance(slide, dict) and isinstance(slide.get("index"), int)
            }
            for slide_id in native_motion_slides:
                slide_audit = audited_slides.get(slide_id, {})
                v.require(isinstance(slide_audit, dict),
                          f"native motion audit includes slide {slide_id}")
                v.require(slide_audit.get("textBackgroundOnlyBuilds") == 0,
                          f"native motion slide {slide_id} does not animate only a text box background")
                v.require(slide_audit.get("backgroundTargetCount") == 0,
                          f"native motion slide {slide_id} does not use unsupported background targets")
            com = motion_artifact.get("powerPointCom", {})
            v.require(isinstance(com, dict) and com.get("status") in {"pass", "unavailable"},
                      "native motion audit has PowerPoint COM recognition evidence")
            if isinstance(com, dict) and com.get("status") == "unavailable":
                v.value(motion_audit, "notes", "native motion audit explains unavailable PowerPoint COM")
            v.require(motion_audit.get("slideshowObserved") is True,
                      "native motion slideshow playback was observed")
            v.value(motion_audit, "evidence", "native motion slideshow observation has evidence")
            playback = motion_artifact.get("slideshowPlayback", {})
            v.require(isinstance(playback, dict) and playback.get("observed") is True,
                      "native motion audit artifact records slideshow observation")
            if isinstance(playback, dict):
                v.value(playback, "evidence", "native motion artifact has slideshow observation evidence")


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
