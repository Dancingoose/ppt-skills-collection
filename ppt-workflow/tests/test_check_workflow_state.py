import copy
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "check_workflow_state.py"


def valid_intent_questionnaire():
    questions = [
        ("audience", 1), ("intent", 1), ("coreClaim", 1), ("canvas", 1),
        ("language", 2), ("expectedOutcome", 2), ("useScene", 2), ("deliveryUse", 2),
        ("storyline", 3), ("contentFocus", 3), ("informationDensity", 3), ("referenceStyle", 3),
    ]
    answers = {
        "audience": "Leadership", "intent": "Decision", "coreClaim": "Invest", "canvas": "ppt169",
    }
    return {
        "schemaVersion": 1,
        "skill": "ppt-workflow-intake",
        "completed": True,
        "responses": [
            {
                "id": question_id,
                "batch": batch,
                "question": f"Question for {question_id}",
                "answer": answers.get(question_id, f"Creator answer for {question_id}"),
                "source": "creator-confirmed",
                "evidence": f"Creator reply after batch {batch}",
            }
            for question_id, batch in questions
        ],
        "batches": [
            {"batch": 1, "questionIds": ["audience", "intent", "coreClaim", "canvas"], "creatorConfirmation": "Creator reply after batch 1"},
            {"batch": 2, "questionIds": ["language", "expectedOutcome", "useScene", "deliveryUse"], "creatorConfirmation": "Creator reply after batch 2"},
            {"batch": 3, "questionIds": ["storyline", "contentFocus", "informationDensity", "referenceStyle"], "creatorConfirmation": "Creator reply after batch 3"},
        ],
    }

def valid_state():
    passport = {
        "theme": "swiss-grid", "accent": "#0057B8", "background": "#FFFFFF",
        "titleFont": "Helvetica", "bodyFont": "Noto Sans SC", "style": "Swiss editorial",
        "backgroundStrategy": "rhythmic", "primaryBackgroundMode": "dark",
    }
    return {
        "schemaVersion": 1,
        "task": {"name": "test", "deliveryFormat": "html"},
        "prep": {
            "sourceType": "report", "coreMessage": "Evidence supports a focused investment.",
            "pagePlan": {"count": 2, "chapters": ["Evidence"]},
            "dataPoints": [{"claim": "Adoption rose", "source": "Research", "url": "https://example.com"}],
        },
        "decision": {
            "phase1": {"audience": "Leadership", "intent": "Decision", "coreClaim": "Invest", "canvas": "ppt169"},
            "intentQuestionnaire": valid_intent_questionnaire(),
            "phase2": {
                "pageCount": 2, "theme": "swiss-grid", "contentHandling": "extend", "imageSource": "none",
                "imageSourcingPlan": {"artifact": "image-sourcing-plan.md"},
            },
            "passport": passport,
            "antiTemplateReview": {
                "reviewer": "ppt-workflow-review", "skill": "ppt-workflow-review",
                "artifact": "anti-template-review.json", "result": "pass", "notes": "Specific layout choices.",
            },
            "preview": {"html": "preview.html", "slideIds": [1, 2], "result": "approved", "notes": "Approved representative slides."},
        },
        "execution": {
            "html": "design.html", "lockedPassport": copy.deepcopy(passport),
            "slides": [
                {"id": 1, "layout": "B1", "contentType": "cover", "dark": True,
                 "layoutEvidence": {"itemCount": 0, "sourceRefs": ["content-inventory.md: Slide 1"]},
                 "visualEffect": {"status": "skipped", "reason": "Text-led cover."}},
                {"id": 2, "layout": "B6", "contentType": "data", "dark": False, "dataSources": ["Research"],
                 "layoutEvidence": {"itemCount": 1, "sourceRefs": ["Research"], "numericValues": [1]},
                 "visualEffect": {"status": "applied", "type": "echarts", "reason": "Trend chart."}},
            ],
            "effectScan": {
                "skill": "ppt-workflow-effects", "artifact": "effects-scan.json", "reviewedSlides": [1, 2],
            },
            "sourceVisualReview": {
                "result": "pass", "reviewedSlides": [1, 2],
                "htmlSha256": "", "notes": "Reviewed each source slide for overlap, clipping, and contrast.",
            },
            "colorContinuityReview": {
                "skill": "ppt-workflow-review", "artifact": "color-continuity-review.json", "result": "pass",
                "reviewedSlides": [1, 2], "htmlSha256": "",
                "notes": "Reviewed the dark and light systems for base color, temperature, and surface continuity.",
            },
            "independentReview": {"result": "pass", "notes": "No layout defects."},
        },
        "delivery": {"converterHealthChecked": True, "canvasRasterizationAcknowledged": True},
    }


def valid_v2_state(level=4, profile=None, motion_mode="pptx-static"):
    state = valid_state()
    profile = profile or {1: "conservative", 2: "measured", 3: "expressive", 4: "bold", 5: "experimental"}[level]
    intake = state["decision"]["intentQuestionnaire"]
    intake["schemaVersion"] = 2
    intake["responses"].insert(-1, {
        "id": "designBoldness", "batch": 3,
        "question": "How bold should the design be?", "answer": f"Level {level}", "level": level,
        "source": "creator-confirmed", "evidence": "Creator reply after batch 3",
    })
    intake["batches"][2]["questionIds"] = [
        "storyline", "contentFocus", "informationDensity", "designBoldness", "referenceStyle",
    ]
    state["decision"]["phase2"].update({
        "designBoldness": {"level": level, "profile": profile},
        "motionDelivery": {"mode": motion_mode, "creatorConfirmed": True, "evidence": "Creator selected the delivery mode."},
    })
    return state


V3_QUESTIONS = (
    ("audience", 1), ("intent", 1), ("coreClaim", 1), ("canvas", 1),
    ("language", 2), ("expectedOutcome", 2), ("useScene", 2), ("deliveryUse", 2),
    ("storyline", 3), ("contentFocus", 3), ("informationDensity", 3),
    ("designBoldness", 3), ("visualSampleConfirmation", 4),
)

DESIGN_ORCHESTRATION_SKILLS = (
    "claude-design", "ui-ux-pro-max", "mbb-decks",
    "frontend-design", "axi-front-design",
)
DESIGN_ORCHESTRATION_ARTIFACTS = {
    "claude-design": "design-directions.md",
    "ui-ux-pro-max": "design-research.md",
    "mbb-decks": "ghost-deck.md",
    "frontend-design": "frontend-design-review.md",
    "axi-front-design": "visual-direction-preview.html",
}


def valid_design_recipes():
    return [
        {
            "id": "signal-led", "theme": "swiss-grid", "narrativeStance": "evidence-first",
            "compositionGeometry": "modular-grid", "visualTemperature": "cool",
            "typographicLanguage": "compact-sans", "informationStructure": "evidence-matrix",
            "imageTreatment": "documentary-crop", "chartLanguage": "analytical",
            "motionStrategy": "static-reveal", "signature": "evidence rail",
            "sourceLenses": list(DESIGN_ORCHESTRATION_SKILLS), "sampleSlideIds": [1, 2],
            "adoptedConstraints": ["Use cool evidence surfaces with clear source hierarchy."],
        },
        {
            "id": "thesis-led", "theme": "editorial-serif", "narrativeStance": "thesis-first",
            "compositionGeometry": "asymmetric-columns", "visualTemperature": "warm",
            "typographicLanguage": "editorial-serif", "informationStructure": "argument-arc",
            "imageTreatment": "editorial-detail", "chartLanguage": "annotated-comparison",
            "motionStrategy": "paced-sequence", "signature": "thesis margin",
            "sourceLenses": list(DESIGN_ORCHESTRATION_SKILLS), "sampleSlideIds": [3, 4],
            "adoptedConstraints": ["Translate accessibility contrast research into the editorial palette."],
        },
        {
            "id": "momentum-led", "theme": "aurora", "narrativeStance": "future-state",
            "compositionGeometry": "full-bleed-sequence", "visualTemperature": "neutral",
            "typographicLanguage": "display-sans", "informationStructure": "decision-journey",
            "imageTreatment": "atmospheric-context", "chartLanguage": "trajectory",
            "motionStrategy": "progressive-horizon", "signature": "motion horizon",
            "sourceLenses": list(DESIGN_ORCHESTRATION_SKILLS), "sampleSlideIds": [5, 6],
            "adoptedConstraints": ["Use motion only where the delivery choice preserves playback."],
        },
    ]


def valid_design_orchestration():
    return {
        "schemaVersion": 1,
        "artifact": "design-orchestration.json",
        "sha256": "",
        "intentBindingsSha256": "",
        "previewSha256": "",
        "executionHtmlSha256": "",
        "selectedRecipeId": "thesis-led",
        "artifacts": [
            {"skill": skill, "file": filename, "inputSha256": "", "sha256": ""}
            for skill, filename in DESIGN_ORCHESTRATION_ARTIFACTS.items()
        ],
    }


def valid_design_profile():
    source_question_ids = [question_id for question_id, _ in V3_QUESTIONS[:12]]
    candidates = [
        {
            "id": "signal-led", "name": "Signal-led evidence", "rationale": "Prioritizes decision evidence.",
            "sourceQuestionIds": list(source_question_ids),
            "visualContract": {
                "narrativeStance": "evidence-first", "compositionGeometry": "modular-grid",
                "visualTemperature": "cool", "typographicLanguage": "compact-sans",
                "backgroundStrategy": "uniform", "primaryBackgroundMode": "light",
                "compositionFamily": "modular-grid",
            },
        },
        {
            "id": "thesis-led", "name": "Thesis-led narrative", "rationale": "Prioritizes an executive point of view.",
            "sourceQuestionIds": list(source_question_ids),
            "visualContract": {
                "narrativeStance": "thesis-first", "compositionGeometry": "asymmetric-columns",
                "visualTemperature": "warm", "typographicLanguage": "editorial-serif",
                "backgroundStrategy": "uniform", "primaryBackgroundMode": "light",
                "compositionFamily": "asymmetric-columns",
            },
        },
        {
            "id": "momentum-led", "name": "Momentum-led projection", "rationale": "Prioritizes the future-state decision.",
            "sourceQuestionIds": list(source_question_ids),
            "visualContract": {
                "narrativeStance": "future-state", "compositionGeometry": "full-bleed-sequence",
                "visualTemperature": "neutral", "typographicLanguage": "display-sans",
                "backgroundStrategy": "uniform", "primaryBackgroundMode": "light",
                "compositionFamily": "full-bleed-sequence",
            },
        },
    ]
    return {
        "schemaVersion": 1,
        "status": "confirmed",
        "previewArtifact": "visual-direction-preview.html",
        "candidates": candidates,
        "selectedProfileId": "thesis-led",
        "creatorConfirmation": "Creator selected the thesis-led visual sample.",
        "evidence": "Creator response after visual sample review.",
    }


def valid_v3_state():
    state = valid_state()
    intake = state["decision"]["intentQuestionnaire"]
    intake["schemaVersion"] = 3
    answers = {
        "audience": "Leadership", "intent": "Decision", "coreClaim": "Invest", "canvas": "ppt169",
    }
    intake["responses"] = [
        {
            "id": question_id,
            "batch": batch,
            "question": (
                "Which visual sample do you confirm?"
                if question_id == "visualSampleConfirmation"
                else f"Question for {question_id}"
            ),
            "answer": answers.get(
                question_id,
                "thesis-led" if question_id == "visualSampleConfirmation"
                else f"Creator answer for {question_id}",
            ),
            "source": "creator-confirmed",
            "evidence": f"Creator reply after batch {batch}",
            **({"level": 4} if question_id == "designBoldness" else {}),
        }
        for question_id, batch in V3_QUESTIONS
    ]
    intake["batches"] = [
        {
            "batch": batch,
            "questionIds": [question_id for question_id, question_batch in V3_QUESTIONS if question_batch == batch],
            "creatorConfirmation": f"Creator reply after batch {batch}",
        }
        for batch in (1, 2, 3, 4)
    ]
    state["decision"]["designProfile"] = valid_design_profile()
    state["decision"]["designRecipes"] = valid_design_recipes()
    state["decision"]["designOrchestration"] = valid_design_orchestration()
    state["decision"]["intentBindings"] = {
        "creatorConfirmed": True,
        "evidence": "Creator confirmed the content, composition, and delivery boundaries.",
        "content": {
            "storyline": "Creator answer for storyline",
            "focus": "Creator answer for contentFocus",
            "density": "Creator answer for informationDensity",
            "mustInclude": ["cited evidence", "decision implication"],
            "mustAvoid": ["unsupported exact forecasts"],
        },
        "composition": {
            "boldnessLevel": 4,
            "densityRule": "Use layered evidence blocks with readable hierarchy.",
            "visualMustAvoid": ["repeated equal card grids", "low contrast small text"],
        },
        "delivery": {
            "expectedOutcome": "Creator answer for expectedOutcome",
            "useScene": "Creator answer for useScene",
            "deliveryUse": "Creator answer for deliveryUse",
            "mustSupport": ["readable at distance", "usable as a speaking outline"],
        },
    }
    state["decision"]["passport"]["backgroundStrategy"] = "uniform"
    state["decision"]["passport"]["primaryBackgroundMode"] = "light"
    selected = state["decision"]["designProfile"]["candidates"][1]
    state["decision"]["passport"]["designProfile"] = {
        "id": selected["id"], "visualContract": dict(selected["visualContract"]),
    }
    state["execution"]["lockedPassport"] = copy.deepcopy(state["decision"]["passport"])
    state["execution"]["slides"][0]["archetype"] = "hero"
    state["execution"]["slides"][1]["archetype"] = "data"
    state["execution"]["slides"][0]["dark"] = False
    state["execution"]["slides"][1]["dark"] = False
    state["execution"]["slides"][0]["compositionFamily"] = "full-bleed-sequence"
    state["execution"]["slides"][1]["compositionFamily"] = "single-axis"
    state["execution"].update({
        "deckRhythmReview": {"skill": "ppt-workflow-review", "artifact": "deck-rhythm-review.json", "result": "pass"},
        "designProfileReview": {
            "skill": "ppt-workflow-review", "artifact": "design-profile-review.json", "result": "pass",
            "selectedProfileId": selected["id"], "reviewedSlides": [1, 2], "htmlSha256": "",
            "notes": "Typography, spacing, image treatment, chart language, and composition match the selected profile.",
        },
        "intentContinuityReview": {
            "skill": "ppt-workflow-review", "artifact": "intent-continuity-review.json", "result": "pass",
            "previewSha256": "", "executionHtmlSha256": "", "notes": "Intent, preview, execution, and delivery remain aligned.",
        },
    })
    return state


HTML = """<!doctype html><html><head><script src='https://cdn.jsdelivr.net/npm/echarts@5'></script></head><body>
<section class='slide dark' data-pptx-slide data-slide-id='1' data-layout='B1' data-item-count='0' data-color-system='coastal-dark' data-background-mode='dark' data-composition-family='full-bleed-sequence' data-archetype='hero'></section>
<section class='slide' data-pptx-slide data-slide-id='2' data-layout='B6' data-item-count='1' data-color-system='coastal-light' data-background-mode='light' data-composition-family='single-axis' data-archetype='data'></section>
</body></html>"""

V3_HTML = HTML.replace(
    "class='slide dark' data-pptx-slide data-slide-id='1' data-layout='B1' data-item-count='0' data-color-system='coastal-dark' data-background-mode='dark'",
    "class='slide' data-pptx-slide data-slide-id='1' data-layout='B1' data-item-count='0' data-color-system='coastal-light' data-background-mode='light'",
).replace("data-color-system='coastal-light' data-background-mode='light'", "data-color-system='coastal-light' data-background-mode='light' data-design-recipe='thesis-led'")

PREVIEW_HTML = """<!doctype html><html><body>
<section class='slide' data-slide-id='1'></section>
<section class='slide' data-slide-id='2'></section>
</body></html>"""

VISUAL_DIRECTION_HTML = """<!doctype html><html><body>
<section data-design-profile='signal-led' data-design-recipe='signal-led' data-composition-family='modular-grid'>Signal-led evidence</section>
<section data-design-profile='thesis-led' data-design-recipe='thesis-led' data-composition-family='asymmetric-columns'>Thesis-led narrative</section>
<section data-design-profile='momentum-led' data-design-recipe='momentum-led' data-composition-family='full-bleed-sequence'>Momentum-led projection</section>
</body></html>"""

CONTENT_INVENTORY = """# Content Inventory

## Core Message
Evidence supports a focused investment.

## Data Points
- Adoption rose, with a cited source.

## Page and Chapter Plan
- Two pages: evidence and decision.
"""


class WorkflowStateTests(unittest.TestCase):
    def write_task(self, state=None, html=None):
        directory = tempfile.TemporaryDirectory()
        task = Path(directory.name)
        if state is not None:
            (task / "workflow-state.json").write_text(json.dumps(state), encoding="utf-8")
        (task / "content-inventory.md").write_text(CONTENT_INVENTORY, encoding="utf-8")
        if html is None:
            html = V3_HTML if isinstance(state, dict) and state.get("decision", {}).get("intentQuestionnaire", {}).get("schemaVersion") == 3 else HTML
        (task / "design.html").write_text(html, encoding="utf-8")
        (task / "preview.html").write_text(PREVIEW_HTML, encoding="utf-8")
        design_profile = (state or {}).get("decision", {}).get("designProfile", {})
        if isinstance(design_profile, dict) and isinstance(design_profile.get("previewArtifact"), str):
            (task / design_profile["previewArtifact"]).write_text(VISUAL_DIRECTION_HTML, encoding="utf-8")
        orchestration = (state or {}).get("decision", {}).get("designOrchestration", {})
        if isinstance(orchestration, dict):
            recipe_ids = [
                recipe["id"] for recipe in (state or {}).get("decision", {}).get("designRecipes", [])
                if isinstance(recipe, dict)
            ]
            for artifact in orchestration.get("artifacts", []):
                if not isinstance(artifact, dict):
                    continue
                filename = artifact.get("file")
                if filename == "visual-direction-preview.html":
                    continue
                if isinstance(filename, str):
                    (task / filename).write_text(
                        "# Design orchestration artifact\n\n" + "\n".join(recipe_ids), encoding="utf-8",
                    )
        (task / "image-sourcing-plan.md").write_text(
            "# Image Sourcing Plan\n\n| Slide | Decision | Reason | Substitute |\n"
            "|---|---|---|---|\n| 1 | no-image | Text-led cover | Typography |\n"
            "| 2 | no-image | Data page | Chart |\n",
            encoding="utf-8",
        )
        if state is not None:
            source_review = state["execution"].get("sourceVisualReview")
            if isinstance(source_review, dict):
                source_review["htmlSha256"] = hashlib.sha256((task / "design.html").read_bytes()).hexdigest()
            color_review = state["execution"].get("colorContinuityReview")
            if isinstance(color_review, dict):
                color_review["htmlSha256"] = hashlib.sha256((task / "design.html").read_bytes()).hexdigest()
            (task / "workflow-state.json").write_text(json.dumps(state), encoding="utf-8")
            review = state["decision"]["antiTemplateReview"]
            (task / review["artifact"]).write_text(json.dumps({
                "schemaVersion": 1,
                "skill": review["skill"],
                "result": review["result"],
                "reviewedAreas": ["intent", "evidence", "theme", "typography", "layouts"],
                "notes": review["notes"],
            }), encoding="utf-8")
            scan = state["execution"]["effectScan"]
            (task / scan["artifact"]).write_text(json.dumps({
                "schemaVersion": 1,
                "skill": scan["skill"],
                "slides": [
                    {key: effect[key] for key in ("id", "status", "reason", "type") if key in effect}
                    for effect in [dict({"id": slide["id"]}, **slide["visualEffect"]) for slide in state["execution"]["slides"]]
                ],
            }), encoding="utf-8")
            if isinstance(color_review, dict):
                (task / color_review["artifact"]).write_text(json.dumps({
                    "schemaVersion": 1,
                    "skill": color_review["skill"],
                    "result": color_review["result"],
                    "reviewedSlides": color_review["reviewedSlides"],
                    "htmlSha256": color_review["htmlSha256"],
                    "notes": color_review["notes"],
                    "colorSystems": ([
                        {"id": "coastal-light", "mode": "light", "slides": [1, 2], "baseColor": "#F2FBFA", "temperature": "cool", "dominantSurface": "foam with aqua details", "notes": "The V3 deck uses one uniform light system."},
                    ] if state.get("decision", {}).get("intentQuestionnaire", {}).get("schemaVersion") == 3 else [
                        {"id": "coastal-dark", "mode": "dark", "slides": [1], "baseColor": "#10283C", "temperature": "cool", "dominantSurface": "ink with aqua details", "notes": "The cover uses the dark coastal system."},
                        {"id": "coastal-light", "mode": "light", "slides": [2], "baseColor": "#F2FBFA", "temperature": "cool", "dominantSurface": "foam with aqua details", "notes": "The content page uses the light coastal system."},
                    ]),
                }), encoding="utf-8")
            rhythm_review = state["execution"].get("deckRhythmReview")
            if isinstance(rhythm_review, dict):
                (task / rhythm_review["artifact"]).write_text(json.dumps({
                    "schemaVersion": 1, "skill": rhythm_review["skill"], "result": rhythm_review["result"],
                    "archetypeSequence": [
                        {"id": slide["id"], "archetype": slide.get("archetype"), "compositionFamily": slide.get("compositionFamily")}
                        for slide in state["execution"]["slides"]
                    ],
                }), encoding="utf-8")
            profile_review = state["execution"].get("designProfileReview")
            if isinstance(profile_review, dict):
                profile_review["htmlSha256"] = hashlib.sha256((task / "design.html").read_bytes()).hexdigest()
                (task / profile_review["artifact"]).write_text(json.dumps({
                    "schemaVersion": 1, "skill": profile_review["skill"], "result": profile_review["result"],
                    "selectedProfileId": profile_review["selectedProfileId"],
                    "reviewedSlides": profile_review["reviewedSlides"], "htmlSha256": profile_review["htmlSha256"],
                    "reviewedDimensions": ["typography", "spacing", "imageTreatment", "chartLanguage", "composition"],
                    "exceptions": [], "notes": profile_review["notes"],
                }), encoding="utf-8")
            continuity_review = state["execution"].get("intentContinuityReview")
            if isinstance(continuity_review, dict):
                preview_path = task / state["decision"]["preview"]["html"]
                continuity_review["previewSha256"] = hashlib.sha256(preview_path.read_bytes()).hexdigest()
                continuity_review["executionHtmlSha256"] = hashlib.sha256((task / "design.html").read_bytes()).hexdigest()
                bindings = state["decision"].get("intentBindings", {})
                bindings_hash = hashlib.sha256(json.dumps(bindings, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
                responses = state["decision"]["intentQuestionnaire"].get("responses", [])
                responses = responses if isinstance(responses, list) else []
                (task / continuity_review["artifact"]).write_text(json.dumps({
                    "schemaVersion": 1, "skill": continuity_review["skill"], "result": continuity_review["result"],
                    "previewSha256": continuity_review["previewSha256"],
                    "executionHtmlSha256": continuity_review["executionHtmlSha256"],
                    "intentQuestionIds": [item.get("id") for item in responses if isinstance(item, dict)],
                    "previewSlideIds": state["decision"]["preview"]["slideIds"],
                    "executionSlideIds": [slide["id"] for slide in state["execution"]["slides"]],
                    "selectedProfileId": state["decision"]["designProfile"]["selectedProfileId"],
                    "intentBindingsSha256": bindings_hash,
                    "checks": {"intentToPreview": "pass", "previewToExecution": "pass", "executionToDelivery": "pass"},
                    "revisionRound": 1, "exceptions": [], "notes": continuity_review["notes"],
                }), encoding="utf-8")
            if isinstance(orchestration, dict) and orchestration:
                bindings = state["decision"].get("intentBindings")
                orchestration["intentBindingsSha256"] = (
                    hashlib.sha256(json.dumps(bindings, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
                    if isinstance(bindings, dict) else ""
                )
                previous_hash = orchestration["intentBindingsSha256"]
                for artifact in orchestration["artifacts"]:
                    filename = artifact["file"]
                    if filename == "visual-direction-preview.html":
                        content = VISUAL_DIRECTION_HTML + f"\n<!-- Input SHA-256: {previous_hash} -->\n"
                    else:
                        content = "# Design orchestration artifact\n\n" + f"Input SHA-256: {previous_hash}\n\n" + "\n".join(recipe_ids)
                    (task / filename).write_text(content, encoding="utf-8")
                    artifact["inputSha256"] = previous_hash
                    artifact["sha256"] = hashlib.sha256((task / filename).read_bytes()).hexdigest()
                    previous_hash = artifact["sha256"]
                orchestration["previewSha256"] = orchestration["artifacts"][-1]["sha256"]
                orchestration["executionHtmlSha256"] = hashlib.sha256((task / "design.html").read_bytes()).hexdigest()
                orchestration_payload = {
                    key: value for key, value in orchestration.items()
                    if key not in {"artifact", "sha256", "executionHtmlSha256"}
                }
                orchestration_payload["recipes"] = state["decision"]["designRecipes"]
                orchestration_path = task / orchestration["artifact"]
                orchestration_path.write_text(json.dumps(orchestration_payload), encoding="utf-8")
                orchestration["sha256"] = hashlib.sha256(orchestration_path.read_bytes()).hexdigest()
            # Persist hashes populated while the file-backed review artifacts are built.
            (task / "workflow-state.json").write_text(json.dumps(state), encoding="utf-8")
        self.addCleanup(directory.cleanup)
        return task

    def check(self, task, layer):
        return subprocess.run(
            [sys.executable, str(SCRIPT), "--task", str(task), "--layer", layer],
            capture_output=True, text=True, check=False,
        )

    def test_valid_prep_decision_and_execution_pass(self):
        task = self.write_task(valid_state())
        for layer in ("prep", "intent", "decision", "exec"):
            result = self.check(task, layer)
            self.assertEqual(result.returncode, 0, result.stdout)

    def test_intent_gate_rejects_a_missing_questionnaire(self):
        state = valid_state()
        del state["decision"]["intentQuestionnaire"]
        result = self.check(self.write_task(state), "intent")
        self.assertEqual(result.returncode, 2)
        self.assertIn("intent questionnaire has a supported schema version", result.stdout)

    def test_v3_intake_accepts_visual_sample_confirmation_in_four_batches(self):
        state = valid_v3_state()
        confirmation = state["decision"]["intentQuestionnaire"]["responses"][-1]
        self.assertEqual(confirmation["id"], "visualSampleConfirmation")
        self.assertEqual(confirmation["question"], "Which visual sample do you confirm?")
        self.assertEqual(confirmation["batch"], 4)
        task = self.write_task(state)
        for layer in ("intent", "decision"):
            result = self.check(task, layer)
            self.assertEqual(result.returncode, 0, result.stdout)

    def test_v3_pre_design_intent_gate_accepts_only_the_first_three_batches(self):
        state = valid_v3_state()
        intake = state["decision"]["intentQuestionnaire"]
        intake["responses"] = intake["responses"][:12]
        intake["batches"] = intake["batches"][:3]
        intake["completed"] = False
        state["decision"].pop("designProfile")
        state["decision"].pop("designRecipes")
        state["decision"].pop("designOrchestration")
        state["execution"].pop("designProfileReview")
        state["execution"].pop("intentContinuityReview")
        result = self.check(self.write_task(state), "intent")
        self.assertEqual(result.returncode, 0, result.stdout)

    def test_v3_decision_accepts_a_confirmed_dynamic_visual_profile(self):
        result = self.check(self.write_task(valid_v3_state()), "decision")
        self.assertEqual(result.returncode, 0, result.stdout)

    def test_v3_decision_requires_every_design_orchestration_artifact(self):
        state = valid_v3_state()
        state["decision"]["designOrchestration"]["artifacts"].pop()
        result = self.check(self.write_task(state), "decision")
        self.assertEqual(result.returncode, 2)
        self.assertIn("design orchestration records every required skill artifact", result.stdout)

    def test_v3_decision_rejects_recipes_without_three_distinct_axes(self):
        state = valid_v3_state()
        state["decision"]["designRecipes"][1].update(state["decision"]["designRecipes"][0])
        result = self.check(self.write_task(state), "decision")
        self.assertEqual(result.returncode, 2)
        self.assertIn("design recipes differ across at least three design axes", result.stdout)

    def test_v3_decision_rejects_untranslated_uiux_research(self):
        state = valid_v3_state()
        state["decision"]["designRecipes"][0]["adoptedConstraints"] = []
        result = self.check(self.write_task(state), "decision")
        self.assertEqual(result.returncode, 2)
        self.assertIn("design recipe translates ui-ux-pro-max research", result.stdout)

    def test_v3_decision_rejects_stale_visual_direction_preview_hash(self):
        task = self.write_task(valid_v3_state())
        (task / "visual-direction-preview.html").write_text("changed", encoding="utf-8")
        result = self.check(task, "decision")
        self.assertEqual(result.returncode, 2)
        self.assertIn("design orchestration preview hash matches the current file", result.stdout)

    def test_v3_decision_rejects_a_broken_design_artifact_hash_chain(self):
        task = self.write_task(valid_v3_state())
        path = task / "workflow-state.json"
        state = json.loads(path.read_text(encoding="utf-8"))
        state["decision"]["designOrchestration"]["artifacts"][2]["inputSha256"] = "0" * 64
        path.write_text(json.dumps(state), encoding="utf-8")
        result = self.check(task, "decision")
        self.assertEqual(result.returncode, 2)
        self.assertIn("design orchestration artifact input hash chain is continuous", result.stdout)

    def test_v3_execution_rejects_design_html_changed_after_orchestration(self):
        task = self.write_task(valid_v3_state())
        (task / "design.html").write_text("<div class='slide'>changed</div>", encoding="utf-8")
        result = self.check(task, "exec")
        self.assertEqual(result.returncode, 2)
        self.assertIn("design orchestration execution hash matches the current HTML", result.stdout)

    def test_v3_execution_rejects_preview_changed_after_orchestration(self):
        task = self.write_task(valid_v3_state())
        (task / "visual-direction-preview.html").write_text("changed", encoding="utf-8")
        result = self.check(task, "exec")
        self.assertEqual(result.returncode, 2)
        self.assertIn("design orchestration preview hash matches the current file", result.stdout)

    def test_v3_execution_requires_the_confirmed_design_recipe_in_every_slide(self):
        html = V3_HTML.replace("data-design-recipe='thesis-led'", "")
        result = self.check(self.write_task(valid_v3_state(), html), "exec")
        self.assertEqual(result.returncode, 2)
        self.assertIn("embeds the confirmed design recipe", result.stdout)

    def test_v3_decision_requires_explicit_intent_bindings(self):
        state = valid_v3_state()
        del state["decision"]["intentBindings"]
        result = self.check(self.write_task(state), "decision")
        self.assertEqual(result.returncode, 2)
        self.assertIn("V3 intent bindings are recorded", result.stdout)

    def test_v3_decision_rejects_intent_binding_drift(self):
        state = valid_v3_state()
        state["decision"]["intentBindings"]["delivery"]["useScene"] = "self-read document"
        result = self.check(self.write_task(state), "decision")
        self.assertEqual(result.returncode, 2)
        self.assertIn("V3 delivery binding useScene exactly matches the creator answer", result.stdout)

    def test_v3_decision_rejects_empty_intent_boundaries(self):
        state = valid_v3_state()
        state["decision"]["intentBindings"]["content"]["mustAvoid"] = []
        result = self.check(self.write_task(state), "decision")
        self.assertEqual(result.returncode, 2)
        self.assertIn("content must-avoid boundaries", result.stdout)

    def test_v3_execution_requires_page_archetypes_and_file_backed_reviews(self):
        state = valid_v3_state()
        del state["execution"]["slides"][0]["archetype"]
        result = self.check(self.write_task(state), "exec")
        self.assertEqual(result.returncode, 2)
        self.assertIn("slide 1 has a supported page archetype", result.stdout)

        state = valid_v3_state()
        del state["execution"]["deckRhythmReview"]
        result = self.check(self.write_task(state), "exec")
        self.assertEqual(result.returncode, 2)
        self.assertIn("deck rhythm review artifact is recorded", result.stdout)

    def test_v3_execution_requires_intent_continuity_review(self):
        state = valid_v3_state()
        del state["execution"]["intentContinuityReview"]
        result = self.check(self.write_task(state), "exec")
        self.assertEqual(result.returncode, 2)
        self.assertIn("intent continuity review artifact is recorded", result.stdout)

    def test_v3_execution_rejects_preview_changed_after_continuity_review(self):
        task = self.write_task(valid_v3_state())
        (task / "preview.html").write_text(PREVIEW_HTML + "<!-- changed after continuity review -->", encoding="utf-8")
        result = self.check(task, "exec")
        self.assertEqual(result.returncode, 2)
        self.assertIn("intent continuity review applies to the current approved preview", result.stdout)

    def test_v3_execution_rejects_manifest_background_mode_drift(self):
        state = valid_v3_state()
        state["execution"]["slides"][0]["dark"] = True
        result = self.check(self.write_task(state), "exec")
        self.assertEqual(result.returncode, 2)
        self.assertIn("uniform background strategy keeps every slide", result.stdout)

    def test_v3_decision_rejects_fewer_than_three_visual_candidates(self):
        state = valid_v3_state()
        state["decision"]["designProfile"]["candidates"].pop()
        result = self.check(self.write_task(state), "decision")
        self.assertEqual(result.returncode, 2)
        self.assertIn("design profile records exactly 3 candidates", result.stdout)

    def test_v3_decision_rejects_candidates_without_three_distinct_visual_dimensions(self):
        state = valid_v3_state()
        candidates = state["decision"]["designProfile"]["candidates"]
        candidates[1]["visualContract"] = dict(candidates[0]["visualContract"])
        candidates[1]["visualContract"]["narrativeStance"] = "thesis-first"
        result = self.check(self.write_task(state), "decision")
        self.assertEqual(result.returncode, 2)
        self.assertIn("visual candidates signal-led and thesis-led differ in at least 3 visual contract dimensions", result.stdout)

    def test_v3_decision_rejects_duplicate_candidate_composition_families(self):
        state = valid_v3_state()
        state["decision"]["designProfile"]["candidates"][2]["visualContract"]["compositionFamily"] = "modular-grid"
        result = self.check(self.write_task(state), "decision")
        self.assertEqual(result.returncode, 2)
        self.assertIn("visual candidates use distinct composition families", result.stdout)

    def test_v3_decision_rejects_background_contract_drift(self):
        state = valid_v3_state()
        state["decision"]["passport"]["primaryBackgroundMode"] = "dark"
        result = self.check(self.write_task(state), "decision")
        self.assertEqual(result.returncode, 2)
        self.assertIn("passport primary background mode matches the selected visual contract", result.stdout)

    def test_v3_decision_rejects_candidate_with_wrong_question_sources(self):
        state = valid_v3_state()
        state["decision"]["designProfile"]["candidates"][0]["sourceQuestionIds"].pop()
        result = self.check(self.write_task(state), "decision")
        self.assertEqual(result.returncode, 2)
        self.assertIn("visual candidate signal-led cites the first 12 V3 intake questions in order", result.stdout)

    def test_v3_decision_rejects_missing_visual_direction_preview(self):
        state = valid_v3_state()
        task = self.write_task(state)
        (task / state["decision"]["designProfile"]["previewArtifact"]).unlink()
        result = self.check(task, "decision")
        self.assertEqual(result.returncode, 2)
        self.assertIn("design profile preview artifact exists", result.stdout)

    def test_v3_decision_rejects_preview_missing_a_candidate_marker(self):
        state = valid_v3_state()
        task = self.write_task(state)
        (task / "visual-direction-preview.html").write_text(
            "<section data-design-profile='signal-led'></section><section data-design-profile='thesis-led'></section>",
            encoding="utf-8",
        )
        result = self.check(task, "decision")
        self.assertEqual(result.returncode, 2)
        self.assertIn("visual direction preview embeds candidate momentum-led", result.stdout)

    def test_v3_decision_rejects_confirmed_profile_without_a_selected_candidate(self):
        state = valid_v3_state()
        state["decision"]["designProfile"]["selectedProfileId"] = "missing-profile"
        state["decision"]["intentQuestionnaire"]["responses"][-1]["answer"] = "missing-profile"
        result = self.check(self.write_task(state), "decision")
        self.assertEqual(result.returncode, 2)
        self.assertIn("confirmed design profile selects one proposed candidate", result.stdout)

    def test_v3_decision_fails_closed_for_malformed_intake_responses(self):
        state = valid_v3_state()
        state["decision"]["intentQuestionnaire"]["responses"] = None
        result = self.check(self.write_task(state), "decision")
        self.assertEqual(result.returncode, 2)
        self.assertNotIn("Traceback", result.stderr)

    def test_v3_decision_rejects_revision_request_without_feedback(self):
        state = valid_v3_state()
        profile = state["decision"]["designProfile"]
        profile["status"] = "revision-requested"
        profile.pop("revisionFeedback", None)
        state["decision"]["intentQuestionnaire"]["completed"] = False
        result = self.check(self.write_task(state), "decision")
        self.assertEqual(result.returncode, 2)
        self.assertIn("revision-requested design profile records revision feedback", result.stdout)

    def test_v3_decision_blocks_revision_request_even_with_feedback(self):
        state = valid_v3_state()
        profile = state["decision"]["designProfile"]
        profile["status"] = "revision-requested"
        profile["revisionFeedback"] = "Make the visual system less restrained."
        state["decision"]["intentQuestionnaire"]["completed"] = False
        result = self.check(self.write_task(state), "decision")
        self.assertEqual(result.returncode, 2)
        self.assertIn("design profile is confirmed before formal decision", result.stdout)

    def test_v3_intake_rejects_an_incomplete_answer_set(self):
        state = valid_v3_state()
        state["decision"]["intentQuestionnaire"]["responses"].pop()
        result = self.check(self.write_task(state), "intent")
        self.assertEqual(result.returncode, 2)
        self.assertIn("intent questionnaire records exactly 13 responses", result.stdout)

    def test_v3_intake_rejects_a_missing_fourth_batch(self):
        state = valid_v3_state()
        state["decision"]["intentQuestionnaire"]["batches"].pop()
        result = self.check(self.write_task(state), "intent")
        self.assertEqual(result.returncode, 2)
        self.assertIn("intent batch 4 is recorded", result.stdout)

    def test_v3_intake_rejects_a_non_sample_confirmation_final_question(self):
        state = valid_v3_state()
        state["decision"]["intentQuestionnaire"]["responses"][-1]["id"] = "designProfileSelection"
        result = self.check(self.write_task(state), "intent")
        self.assertEqual(result.returncode, 2)
        self.assertIn("intent response 'designProfileSelection' has a unique required question id", result.stdout)

    def test_v2_intake_binds_boldness_to_composition_choices(self):
        state = valid_state()
        intake = state["decision"]["intentQuestionnaire"]
        intake["schemaVersion"] = 2
        intake["responses"].insert(-1, {
            "id": "designBoldness", "batch": 3,
            "question": "How bold should the design be?",
            "answer": "Bold", "level": 4,
            "source": "creator-confirmed", "evidence": "Creator reply after batch 3",
        })
        intake["batches"][2]["questionIds"] = [
            "storyline", "contentFocus", "informationDensity", "designBoldness", "referenceStyle",
        ]
        state["decision"]["phase2"]["designBoldness"] = {"level": 4, "profile": "bold"}
        state["decision"]["phase2"]["motionDelivery"] = {
            "mode": "pptx-static", "creatorConfirmed": True, "evidence": "Creator selected static PPTX.",
        }
        state["execution"]["slides"][0]["compositionPattern"] = "P10"
        state["execution"]["slides"][1]["compositionPattern"] = "P03"
        task = self.write_task(state)
        for layer in ("intent", "decision", "exec"):
            result = self.check(task, layer)
            self.assertEqual(result.returncode, 0, result.stdout)

    def test_v2_rejects_a_boldness_profile_that_does_not_match_the_level(self):
        state = valid_v2_state(level=2, profile="bold")
        state["execution"]["slides"][0]["compositionPattern"] = "P02"
        state["execution"]["slides"][1]["compositionPattern"] = "P03"
        result = self.check(self.write_task(state), "decision")
        self.assertEqual(result.returncode, 2)
        self.assertIn("profile exactly matches its selected level", result.stdout)

    def test_v2_rejects_a_composition_above_the_selected_boldness_level(self):
        state = valid_v2_state(level=2)
        state["execution"]["slides"][0]["compositionPattern"] = "P02"
        state["execution"]["slides"][1]["compositionPattern"] = "P06"
        result = self.check(self.write_task(state), "exec")
        self.assertEqual(result.returncode, 2)
        self.assertIn("composition stays within the selected design boldness level", result.stdout)

    def test_v2_rejects_a_photo_dependent_composition_without_an_approved_image(self):
        state = valid_v2_state(level=2)
        state["execution"]["slides"][0]["compositionPattern"] = "P05"
        state["execution"]["slides"][1]["compositionPattern"] = "P03"
        result = self.check(self.write_task(state), "exec")
        self.assertEqual(result.returncode, 2)
        self.assertIn("photo-dependent composition has an approved image decision", result.stdout)

    def test_intent_gate_rejects_fewer_than_twelve_creator_answers(self):
        state = valid_state()
        state["decision"]["intentQuestionnaire"]["responses"].pop()
        result = self.check(self.write_task(state), "intent")
        self.assertEqual(result.returncode, 2)
        self.assertIn("exactly 12 responses", result.stdout)
        self.assertIn("includes every required question exactly once", result.stdout)

    def test_experimental_boldness_requires_playable_motion_delivery(self):
        state = valid_state()
        intake = state["decision"]["intentQuestionnaire"]
        intake["schemaVersion"] = 2
        intake["responses"].insert(-1, {
            "id": "designBoldness", "batch": 3,
            "question": "How bold should the design be?", "answer": "Experimental", "level": 5,
            "source": "creator-confirmed", "evidence": "Creator reply after batch 3",
        })
        intake["batches"][2]["questionIds"] = [
            "storyline", "contentFocus", "informationDensity", "designBoldness", "referenceStyle",
        ]
        state["decision"]["phase2"].update({
            "designBoldness": {"level": 5, "profile": "experimental"},
            "motionDelivery": {"mode": "pptx-static", "creatorConfirmed": True, "evidence": "Creator selected static PPTX."},
        })
        state["execution"]["slides"][0]["compositionPattern"] = "P10"
        state["execution"]["slides"][1]["compositionPattern"] = "P03"
        result = self.check(self.write_task(state), "decision")
        self.assertEqual(result.returncode, 2)
        self.assertIn("experimental design boldness requires playable video or live HTML delivery", result.stdout)

    def test_live_composition_rejects_a_static_only_delivery_choice(self):
        state = valid_state()
        intake = state["decision"]["intentQuestionnaire"]
        intake["schemaVersion"] = 2
        intake["responses"].insert(-1, {
            "id": "designBoldness", "batch": 3,
            "question": "How bold should the design be?", "answer": "Bold", "level": 4,
            "source": "creator-confirmed", "evidence": "Creator reply after batch 3",
        })
        intake["batches"][2]["questionIds"] = [
            "storyline", "contentFocus", "informationDensity", "designBoldness", "referenceStyle",
        ]
        state["decision"]["phase2"].update({
            "designBoldness": {"level": 4, "profile": "bold"},
            "motionDelivery": {"mode": "pptx-static", "creatorConfirmed": True, "evidence": "Creator selected static PPTX."},
        })
        state["execution"]["slides"][0]["compositionPattern"] = "P14"
        state["execution"]["slides"][1]["compositionPattern"] = "P03"
        result = self.check(self.write_task(state), "exec")
        self.assertEqual(result.returncode, 2)
        self.assertIn("live composition requires playable video or live HTML delivery", result.stdout)

    def test_intent_gate_rejects_duplicate_or_missing_question_ids(self):
        state = valid_state()
        state["decision"]["intentQuestionnaire"]["responses"][-1]["id"] = "audience"
        result = self.check(self.write_task(state), "intent")
        self.assertEqual(result.returncode, 2)
        self.assertIn("unique required question id", result.stdout)
        self.assertIn("includes every required question exactly once", result.stdout)

    def test_intent_gate_rejects_question_in_the_wrong_batch(self):
        state = valid_state()
        state["decision"]["intentQuestionnaire"]["responses"][0]["batch"] = 2
        result = self.check(self.write_task(state), "intent")
        self.assertEqual(result.returncode, 2)
        self.assertIn("audience is in its required batch", result.stdout)

    def test_intent_gate_rejects_inferred_creator_intent(self):
        state = valid_state()
        state["decision"]["intentQuestionnaire"]["responses"][0]["source"] = "inferred"
        result = self.check(self.write_task(state), "intent")
        self.assertEqual(result.returncode, 2)
        self.assertIn("creator-confirmed, not inferred", result.stdout)

    def test_intent_gate_rejects_phase1_drift_from_creator_answers(self):
        state = valid_state()
        state["decision"]["phase1"]["audience"] = "Model-inferred audience"
        result = self.check(self.write_task(state), "intent")
        self.assertEqual(result.returncode, 2)
        self.assertIn("decision.phase1.audience exactly matches", result.stdout)

    def test_decision_execution_and_delivery_repeat_the_intent_gate(self):
        state = valid_state()
        state["decision"]["intentQuestionnaire"]["completed"] = False
        task = self.write_task(state)
        for layer in ("decision", "exec", "deliver"):
            result = self.check(task, layer)
            self.assertEqual(result.returncode, 2)
            self.assertIn("intent questionnaire is marked complete", result.stdout)

    def test_missing_manifest_fails_closed(self):
        result = self.check(self.write_task(), "prep")
        self.assertEqual(result.returncode, 2)
        self.assertIn("workflow-state.json exists", result.stdout)

    def test_empty_core_message_fails(self):
        state = valid_state()
        state["prep"]["coreMessage"] = ""
        result = self.check(self.write_task(state), "prep")
        self.assertEqual(result.returncode, 2)
        self.assertIn("prep.coreMessage", result.stdout)

    def test_prep_rejects_unresolved_content_inventory(self):
        task = self.write_task(valid_state())
        (task / "content-inventory.md").write_text(
            "# Content Inventory\n\n## Core Message\n[To be confirmed]\n\n## Data Points\n[TBD]\n\n## Page and Chapter Plan\nTODO\n",
            encoding="utf-8",
        )
        result = self.check(task, "prep")
        self.assertEqual(result.returncode, 2)
        self.assertIn("content inventory core message is resolved", result.stdout)
        self.assertIn("content inventory data points is resolved", result.stdout)
        self.assertIn("content inventory page and chapter plan is resolved", result.stdout)

    def test_decision_requires_approved_preview_file(self):
        state = valid_state()
        state["decision"]["preview"]["result"] = "draft"
        task = self.write_task(state)
        (task / "preview.html").unlink()
        result = self.check(task, "decision")
        self.assertEqual(result.returncode, 2)
        self.assertIn("decision preview HTML exists", result.stdout)
        self.assertIn("decision preview is approved", result.stdout)

    def test_single_page_delivery_accepts_a_single_page_preview(self):
        state = valid_state()
        state["prep"]["pagePlan"]["count"] = 1
        state["decision"]["phase2"]["pageCount"] = 1
        state["decision"]["preview"]["slideIds"] = [1]
        state["execution"]["slides"] = state["execution"]["slides"][:1]
        state["execution"]["effectScan"]["reviewedSlides"] = [1]
        task = self.write_task(state)
        (task / "image-sourcing-plan.md").write_text(
            "# Image Sourcing Plan\n\n| Slide | Decision | Reason | Substitute |\n"
            "|---|---|---|---|\n| 1 | no-image | Text-led cover | Typography |\n",
            encoding="utf-8",
        )
        (task / "preview.html").write_text(
            "<!doctype html><html><body><section class='slide' data-slide-id='1'></section></body></html>",
            encoding="utf-8",
        )
        result = self.check(task, "decision")
        self.assertEqual(result.returncode, 0, result.stdout)

    def test_decision_requires_file_backed_anti_template_review(self):
        state = valid_state()
        task = self.write_task(state)
        (task / state["decision"]["antiTemplateReview"]["artifact"]).unlink()
        result = self.check(task, "decision")
        self.assertEqual(result.returncode, 2)
        self.assertIn("anti-template review artifact exists", result.stdout)

    def test_decision_rejects_page_count_that_drifts_from_preparation(self):
        state = valid_state()
        state["decision"]["phase2"]["pageCount"] = 3
        result = self.check(self.write_task(state), "decision")
        self.assertEqual(result.returncode, 2)
        self.assertIn("matches the preparation page plan", result.stdout)

    def test_decision_requires_a_complete_image_sourcing_plan(self):
        state = valid_state()
        task = self.write_task(state)
        (task / "image-sourcing-plan.md").write_text(
            "# Image Sourcing Plan\n\n| Slide | Decision |\n|---|---|\n| 1 | no-image |\n",
            encoding="utf-8",
        )
        result = self.check(task, "decision")
        self.assertEqual(result.returncode, 2)
        self.assertIn("covers every approved slide exactly once", result.stdout)

    def test_decision_rejects_web_image_without_a_complete_approved_record(self):
        state = valid_state()
        task = self.write_task(state)
        (task / "image-sourcing-plan.md").write_text(
            "# Image Sourcing Plan\n\n| Slide | Decision |\n|---|---|\n"
            "| 1 | no-image |\n| 2 | web-search |\n\n"
            "### Slide 2\n- Candidate URL: https://images.example.com/route.jpg\n"
            "- License: CC BY 4.0\n- Attribution: Example Photographer\n",
            encoding="utf-8",
        )
        result = self.check(task, "decision")
        self.assertEqual(result.returncode, 2)
        self.assertIn("records a downloaded local file", result.stdout)
        self.assertIn("has creator approval", result.stdout)

    def test_decision_accepts_an_approved_web_image_with_task_local_file(self):
        state = valid_state()
        task = self.write_task(state)
        asset = task / "assets" / "route.jpg"
        asset.parent.mkdir()
        asset.write_bytes(b"licensed image")
        (task / "image-sourcing-plan.md").write_text(
            "# Image Sourcing Plan\n\n| Slide | Decision |\n|---|---|\n"
            "| 1 | no-image |\n| 2 | web-search |\n\n"
            "### Slide 2\n- Candidate URL: https://images.example.com/route.jpg\n"
            "- License: CC BY 4.0\n- Attribution: Example Photographer\n"
            "- Local file: assets/route.jpg\n- Approval: creator-approved\n",
            encoding="utf-8",
        )
        result = self.check(task, "decision")
        self.assertEqual(result.returncode, 0, result.stdout)

    def test_decision_rejects_supplied_image_missing_from_task_directory(self):
        state = valid_state()
        task = self.write_task(state)
        (task / "image-sourcing-plan.md").write_text(
            "# Image Sourcing Plan\n\n| Slide | Decision |\n|---|---|\n"
            "| 1 | supplied-image |\n| 2 | no-image |\n\n"
            "### Slide 1\n- Supplied file: assets/missing.jpg\n",
            encoding="utf-8",
        )
        result = self.check(task, "decision")
        self.assertEqual(result.returncode, 2)
        self.assertIn("supplied image exists in the task directory", result.stdout)

    def test_execution_requires_an_approved_image_file_in_layout_evidence(self):
        state = valid_state()
        task = self.write_task(state)
        asset = task / "assets" / "route.jpg"
        asset.parent.mkdir()
        asset.write_bytes(b"licensed image")
        (task / "image-sourcing-plan.md").write_text(
            "# Image Sourcing Plan\n\n| Slide | Decision |\n|---|---|\n"
            "| 1 | no-image |\n| 2 | web-search |\n\n"
            "### Slide 2\n- Candidate URL: https://images.example.com/route.jpg\n"
            "- License: CC BY 4.0\n- Attribution: Example Photographer\n"
            "- Local file: assets/route.jpg\n- Approval: creator-approved\n",
            encoding="utf-8",
        )
        result = self.check(task, "exec")
        self.assertEqual(result.returncode, 2)
        self.assertIn("layout evidence cites its approved image file", result.stdout)

    def test_qualitative_slide_cannot_claim_data_layout(self):
        state = valid_state()
        state["execution"]["slides"][1]["contentType"] = "qualitative"
        result = self.check(self.write_task(state), "exec")
        self.assertEqual(result.returncode, 2)
        self.assertIn("does not misuse a data layout", result.stdout)

    def test_applied_effect_must_appear_in_html(self):
        result = self.check(self.write_task(valid_state(), HTML.replace("echarts", "chart-library")), "exec")
        self.assertEqual(result.returncode, 2)
        self.assertIn("applied effect is present", result.stdout)

    def test_execution_accepts_native_motion_with_html_signal(self):
        state = valid_state()
        state["execution"]["slides"][1]["visualEffect"] = {
            "status": "applied", "type": "native-motion",
            "reason": "The metric reveal benefits from a native entrance.",
        }
        html = HTML.replace(
            "data-slide-id='2'", "data-pptx-motion='fade' data-slide-id='2'",
        )
        result = self.check(self.write_task(state, html), "exec")
        self.assertEqual(result.returncode, 0, result.stdout)

    def test_execution_accepts_embedded_video_with_html_signal(self):
        state = valid_state()
        state["execution"]["slides"][1]["visualEffect"] = {
            "status": "applied", "type": "embedded-video",
            "reason": "The WebGL scene is delivered as an embedded movie.",
        }
        html = HTML.replace(
            "data-slide-id='2'", "data-pptx-video data-slide-id='2'",
        )
        result = self.check(self.write_task(state, html), "exec")
        self.assertEqual(result.returncode, 0, result.stdout)

    def test_execution_page_count_must_match_decision(self):
        state = valid_state()
        state["decision"]["phase2"]["pageCount"] = 3
        result = self.check(self.write_task(state), "exec")
        self.assertEqual(result.returncode, 2)
        self.assertIn("approved page count", result.stdout)

    def test_uniform_background_strategy_rejects_a_mixed_mode_deck(self):
        state = valid_state()
        state["decision"]["passport"]["backgroundStrategy"] = "uniform"
        state["execution"]["lockedPassport"] = copy.deepcopy(state["decision"]["passport"])
        result = self.check(self.write_task(state), "exec")
        self.assertEqual(result.returncode, 2)
        self.assertIn("uniform background strategy keeps every slide", result.stdout)

    def test_uniform_background_strategy_accepts_an_all_dark_deck(self):
        state = valid_state()
        state["decision"]["passport"]["backgroundStrategy"] = "uniform"
        state["execution"]["lockedPassport"] = copy.deepcopy(state["decision"]["passport"])
        state["execution"]["slides"][1]["dark"] = True
        html = HTML.replace("data-color-system='coastal-light'", "data-color-system='coastal-dark'")
        task = self.write_task(state, html)
        artifact_path = task / state["execution"]["colorContinuityReview"]["artifact"]
        artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
        artifact["colorSystems"] = [
            {"id": "coastal-dark", "mode": "dark", "slides": [1, 2], "baseColor": "#10283C", "temperature": "cool", "dominantSurface": "ink with aqua details", "notes": "The deck uses one dark system."},
        ]
        artifact_path.write_text(json.dumps(artifact), encoding="utf-8")
        result = self.check(task, "exec")
        self.assertEqual(result.returncode, 0, result.stdout)

    def test_execution_requires_an_explicit_converter_slide_marker(self):
        result = self.check(self.write_task(valid_state(), HTML.replace("data-pptx-slide", "")), "exec")
        self.assertEqual(result.returncode, 2)
        self.assertIn("explicitly discoverable by the converter", result.stdout)

    def test_execution_requires_a_full_source_visual_review(self):
        state = valid_state()
        del state["execution"]["sourceVisualReview"]
        result = self.check(self.write_task(state), "exec")
        self.assertEqual(result.returncode, 2)
        self.assertIn("source HTML visual review has a result", result.stdout)
        self.assertIn("source HTML visual review covers every slide", result.stdout)

    def test_execution_requires_file_backed_color_continuity_review(self):
        state = valid_state()
        task = self.write_task(state)
        (task / state["execution"]["colorContinuityReview"]["artifact"]).unlink()
        result = self.check(task, "exec")
        self.assertEqual(result.returncode, 2)
        self.assertIn("color continuity review artifact exists", result.stdout)

    def test_execution_rejects_color_system_not_embedded_in_html(self):
        html = HTML.replace("data-color-system='coastal-light'", "data-color-system='wrong-light'")
        result = self.check(self.write_task(valid_state(), html), "exec")
        self.assertEqual(result.returncode, 2)
        self.assertIn("embeds its reviewed light color system", result.stdout)

    def test_execution_rejects_color_review_for_changed_html(self):
        task = self.write_task(valid_state())
        (task / "design.html").write_text(HTML + "<!-- changed after color review -->", encoding="utf-8")
        result = self.check(task, "exec")
        self.assertEqual(result.returncode, 2)
        self.assertIn("color continuity review applies to the current execution HTML", result.stdout)

    def test_execution_rejects_html_changed_after_source_review(self):
        task = self.write_task(valid_state())
        (task / "design.html").write_text(HTML + "<!-- changed after review -->", encoding="utf-8")
        result = self.check(task, "exec")
        self.assertEqual(result.returncode, 2)
        self.assertIn("source HTML has not changed since visual review", result.stdout)

    def test_execution_requires_a_file_backed_effect_scan(self):
        state = valid_state()
        task = self.write_task(state)
        (task / state["execution"]["effectScan"]["artifact"]).unlink()
        result = self.check(task, "exec")
        self.assertEqual(result.returncode, 2)
        self.assertIn("effect scan artifact exists", result.stdout)

    def test_execution_rejects_effect_scan_manifest_drift(self):
        state = valid_state()
        task = self.write_task(state)
        scan_path = task / state["execution"]["effectScan"]["artifact"]
        scan = json.loads(scan_path.read_text(encoding="utf-8"))
        scan["slides"][1]["reason"] = "Different reason."
        scan_path.write_text(json.dumps(scan), encoding="utf-8")
        result = self.check(task, "exec")
        self.assertEqual(result.returncode, 2)
        self.assertIn("effect scan agrees with manifest reason", result.stdout)

    def test_execution_rejects_duplicate_effect_scan_entries(self):
        state = valid_state()
        task = self.write_task(state)
        scan_path = task / state["execution"]["effectScan"]["artifact"]
        scan = json.loads(scan_path.read_text(encoding="utf-8"))
        scan["slides"].append(copy.deepcopy(scan["slides"][0]))
        scan_path.write_text(json.dumps(scan), encoding="utf-8")
        result = self.check(task, "exec")
        self.assertEqual(result.returncode, 2)
        self.assertIn("effect scan artifact covers every slide exactly once", result.stdout)

    def test_layout_item_count_must_fit_selected_layout(self):
        state = valid_state()
        state["execution"]["slides"][1]["layout"] = "B7"
        state["execution"]["slides"][1]["layoutEvidence"] = {
            "itemCount": 3, "sourceRefs": ["Research"], "numericValues": [1, 2, 3],
        }
        html = HTML.replace("data-layout='B6' data-item-count='1'", "data-layout='B7' data-item-count='3'")
        result = self.check(self.write_task(state, html), "exec")
        self.assertEqual(result.returncode, 2)
        self.assertIn("item count fits B7", result.stdout)

    def test_data_layout_requires_matching_numeric_evidence(self):
        state = valid_state()
        state["execution"]["slides"][1]["layout"] = "B18"
        state["execution"]["slides"][1]["layoutEvidence"] = {
            "itemCount": 3, "sourceRefs": ["Research"], "numericValues": [1, 2],
        }
        html = HTML.replace("data-layout='B6' data-item-count='1'", "data-layout='B18' data-item-count='3'")
        result = self.check(self.write_task(state, html), "exec")
        self.assertEqual(result.returncode, 2)
        self.assertIn("data count matches its numeric evidence", result.stdout)

    def test_missing_layout_evidence_fails_without_crashing(self):
        state = valid_state()
        del state["execution"]["slides"][1]["layoutEvidence"]
        result = self.check(self.write_task(state), "exec")
        self.assertEqual(result.returncode, 2)
        self.assertIn("records a layout item count", result.stdout)

    def test_delivery_gate_mentions_compatible_browser_runtime(self):
        result = self.check(self.write_task(valid_state()), "deliver")
        self.assertIn("Playwright-compatible browser", result.stdout)

    def test_recorded_pptx_requires_full_audit_evidence(self):
        state = valid_state()
        state["delivery"]["output"] = "deck.pptx"
        task = self.write_task(state)
        (task / "deck.pptx").write_bytes(b"placeholder")
        result = self.check(task, "deliver")
        self.assertEqual(result.returncode, 2)
        self.assertIn("delivery audit reviewed every slide", result.stdout)

    def test_delivery_rejects_pptx_changed_after_audit(self):
        state = valid_state()
        state["delivery"].update({
            "output": "deck.pptx",
            "audit": {"result": "pass", "reviewedPages": 2, "pptxSha256": "", "notes": "Audited output."},
        })
        task = self.write_task(state)
        pptx_path = task / "deck.pptx"
        pptx_path.write_bytes(b"audited output")
        persisted = json.loads((task / "workflow-state.json").read_text(encoding="utf-8"))
        persisted["delivery"]["audit"]["pptxSha256"] = hashlib.sha256(pptx_path.read_bytes()).hexdigest()
        (task / "workflow-state.json").write_text(json.dumps(persisted), encoding="utf-8")
        pptx_path.write_bytes(b"changed after audit")
        result = self.check(task, "deliver")
        self.assertEqual(result.returncode, 2)
        self.assertIn("PPTX has not changed since delivery audit", result.stdout)

    def test_delivery_accepts_a_file_backed_pptx_audit(self):
        state = valid_state()
        state["task"]["deliveryFormat"] = "pptx"
        state["delivery"].update({
            "output": "deck.pptx",
            "audit": {"result": "pass", "reviewedPages": 2, "pptxSha256": "", "artifact": "pptx-audit.json", "notes": "PowerPoint comparison reviewed."},
        })
        task = self.write_task(state)
        pptx_path = task / "deck.pptx"
        pptx_path.write_bytes(b"audited output")
        digest = hashlib.sha256(pptx_path.read_bytes()).hexdigest()
        persisted = json.loads((task / "workflow-state.json").read_text(encoding="utf-8"))
        persisted["delivery"]["audit"]["pptxSha256"] = digest
        (task / "workflow-state.json").write_text(json.dumps(persisted), encoding="utf-8")
        (task / "pptx-audit.json").write_text(json.dumps({
            "schemaVersion": 1, "result": "pass", "reviewedPages": 2, "pptxSha256": digest,
            "renderer": "PowerPoint", "notes": "Compared both rendered slides against HTML references.",
        }), encoding="utf-8")
        result = self.check(task, "deliver")
        self.assertEqual(result.returncode, 0, result.stdout)

    def test_v3_delivery_requires_zero_preflight_and_structural_findings(self):
        state = valid_v3_state()
        state["task"]["deliveryFormat"] = "pptx"
        state["delivery"].update({
            "output": "deck.pptx",
            "audit": {
                "result": "pass", "reviewedPages": 2, "pptxSha256": "",
                "artifact": "pptx-audit.json", "unresolvedHighRiskPages": [],
                "structuralWarnings": 0, "notes": "PowerPoint comparison reviewed.",
            },
        })
        task = self.write_task(state)
        pptx_path = task / "deck.pptx"
        pptx_path.write_bytes(b"audited V3 output")
        digest = hashlib.sha256(pptx_path.read_bytes()).hexdigest()
        persisted = json.loads((task / "workflow-state.json").read_text(encoding="utf-8"))
        persisted["delivery"]["audit"]["pptxSha256"] = digest
        (task / "workflow-state.json").write_text(json.dumps(persisted), encoding="utf-8")

        artifact = {
            "schemaVersion": 1, "result": "pass", "reviewedPages": 2,
            "pptxSha256": digest, "renderer": "PowerPoint",
            "notes": "Compared both rendered slides against HTML references.",
            "checks": {
                "preflight": {"status": "pass", "highRiskPages": []},
                "structuralSelfCheck": {"status": "pass", "warningCount": 0},
            },
        }
        audit_path = task / "pptx-audit.json"
        audit_path.write_text(json.dumps(artifact), encoding="utf-8")
        result = self.check(task, "deliver")
        self.assertEqual(result.returncode, 0, result.stdout)

        artifact["checks"]["preflight"] = {"status": "failed", "highRiskPages": [1]}
        artifact["checks"]["structuralSelfCheck"] = {"status": "failed", "warningCount": 1}
        audit_path.write_text(json.dumps(artifact), encoding="utf-8")
        result = self.check(task, "deliver")
        self.assertEqual(result.returncode, 2)
        self.assertIn("V3 delivery preflight evidence agrees with unresolved high-risk pages", result.stdout)
        self.assertIn("V3 delivery structural self-check evidence agrees with warning count", result.stdout)

    def test_delivery_rejects_an_unbacked_pptx_audit_manifest(self):
        state = valid_state()
        state["task"]["deliveryFormat"] = "pptx"
        state["delivery"].update({
            "output": "deck.pptx",
            "audit": {"result": "pass", "reviewedPages": 2, "pptxSha256": "", "notes": "PowerPoint comparison reviewed."},
        })
        task = self.write_task(state)
        pptx_path = task / "deck.pptx"
        pptx_path.write_bytes(b"audited output")
        persisted = json.loads((task / "workflow-state.json").read_text(encoding="utf-8"))
        persisted["delivery"]["audit"]["pptxSha256"] = hashlib.sha256(pptx_path.read_bytes()).hexdigest()
        (task / "workflow-state.json").write_text(json.dumps(persisted), encoding="utf-8")
        result = self.check(task, "deliver")
        self.assertEqual(result.returncode, 2)
        self.assertIn("delivery audit artifact is recorded", result.stdout)

    def test_native_motion_delivery_requires_playback_and_text_build_evidence(self):
        state = valid_state()
        state["task"]["deliveryFormat"] = "pptx"
        state["execution"]["slides"][1]["visualEffect"] = {
            "status": "applied", "type": "native-motion", "reason": "Reveal the point on click.",
        }
        state["delivery"].update({
            "output": "deck.pptx",
            "audit": {
                "result": "pass", "reviewedPages": 2, "pptxSha256": "",
                "artifact": "pptx-audit.json", "notes": "PowerPoint comparison reviewed.",
            },
        })
        task = self.write_task(state)
        pptx_path = task / "deck.pptx"
        pptx_path.write_bytes(b"native motion output")
        digest = hashlib.sha256(pptx_path.read_bytes()).hexdigest()
        persisted = json.loads((task / "workflow-state.json").read_text(encoding="utf-8"))
        persisted["delivery"]["audit"]["pptxSha256"] = digest
        (task / "workflow-state.json").write_text(json.dumps(persisted), encoding="utf-8")
        (task / "pptx-audit.json").write_text(json.dumps({
            "schemaVersion": 1, "result": "pass", "reviewedPages": 2, "pptxSha256": digest,
            "renderer": "PowerPoint", "notes": "Compared both rendered slides against HTML references.",
        }), encoding="utf-8")

        result = self.check(task, "deliver")
        self.assertEqual(result.returncode, 2)
        self.assertIn("native motion audit is recorded", result.stdout)

        motion_artifact = {
            "schemaVersion": 1, "kind": "native-motion-audit", "result": "pass", "pptxSha256": digest,
            "slides": [
                {"index": 1, "backgroundTargetCount": 0, "textBackgroundOnlyBuilds": 0},
                {"index": 2, "backgroundTargetCount": 0, "textBackgroundOnlyBuilds": 0},
            ],
            "powerPointCom": {"status": "unavailable", "reason": "Test environment", "slides": []},
            "slideshowPlayback": {"observed": True, "observer": "creator", "evidence": "Observed in Slide Show view."},
        }
        persisted = json.loads((task / "workflow-state.json").read_text(encoding="utf-8"))
        persisted["delivery"]["motionAudit"] = {
            "result": "pass", "reviewedSlides": [2], "pptxSha256": digest,
            "artifact": "motion-audit.json", "slideshowObserved": True,
            "evidence": "Observed in Slide Show view.", "notes": "COM is unavailable in this test environment.",
        }
        (task / "workflow-state.json").write_text(json.dumps(persisted), encoding="utf-8")
        motion_path = task / "motion-audit.json"
        motion_path.write_text(json.dumps(motion_artifact), encoding="utf-8")
        result = self.check(task, "deliver")
        self.assertEqual(result.returncode, 0, result.stdout)

        motion_artifact["slides"][1]["textBackgroundOnlyBuilds"] = 1
        motion_path.write_text(json.dumps(motion_artifact), encoding="utf-8")
        result = self.check(task, "deliver")
        self.assertEqual(result.returncode, 2)
        self.assertIn("does not animate only a text box background", result.stdout)

    def test_live_html_delivery_requires_playback_proof_and_current_file_hash(self):
        state = valid_state()
        intake = state["decision"]["intentQuestionnaire"]
        intake["schemaVersion"] = 2
        intake["responses"].insert(-1, {
            "id": "designBoldness", "batch": 3,
            "question": "How bold should the design be?", "answer": "Experimental", "level": 5,
            "source": "creator-confirmed", "evidence": "Creator reply after batch 3",
        })
        intake["batches"][2]["questionIds"] = [
            "storyline", "contentFocus", "informationDensity", "designBoldness", "referenceStyle",
        ]
        state["decision"]["phase2"].update({
            "designBoldness": {"level": 5, "profile": "experimental"},
            "motionDelivery": {"mode": "pptx-plus-live-html", "creatorConfirmed": True, "evidence": "Creator approved live HTML."},
        })
        state["execution"]["slides"][0]["compositionPattern"] = "P14"
        state["execution"]["slides"][1]["compositionPattern"] = "P03"
        state["delivery"]["liveHtml"] = {
            "output": "live-presentation.html",
            "playbackAudit": {"result": "pass", "motionObserved": False, "htmlSha256": "", "notes": "Playback reviewed."},
        }
        task = self.write_task(state)
        live_html = task / "live-presentation.html"
        live_html.write_text("<canvas></canvas>", encoding="utf-8")
        persisted = json.loads((task / "workflow-state.json").read_text(encoding="utf-8"))
        persisted["delivery"]["liveHtml"]["playbackAudit"]["htmlSha256"] = hashlib.sha256(live_html.read_bytes()).hexdigest()
        (task / "workflow-state.json").write_text(json.dumps(persisted), encoding="utf-8")
        result = self.check(task, "deliver")
        self.assertEqual(result.returncode, 2)
        self.assertIn("observed motion", result.stdout)
        live_html.write_text("<canvas>changed</canvas>", encoding="utf-8")
        persisted["delivery"]["liveHtml"]["playbackAudit"]["motionObserved"] = True
        (task / "workflow-state.json").write_text(json.dumps(persisted), encoding="utf-8")
        result = self.check(task, "deliver")
        self.assertEqual(result.returncode, 2)
        self.assertIn("live HTML has not changed since playback audit", result.stdout)

    def test_live_html_delivery_requires_a_static_pptx_fallback(self):
        state = valid_state()
        intake = state["decision"]["intentQuestionnaire"]
        intake["schemaVersion"] = 2
        intake["responses"].insert(-1, {
            "id": "designBoldness", "batch": 3,
            "question": "How bold should the design be?", "answer": "Bold", "level": 4,
            "source": "creator-confirmed", "evidence": "Creator reply after batch 3",
        })
        intake["batches"][2]["questionIds"] = [
            "storyline", "contentFocus", "informationDensity", "designBoldness", "referenceStyle",
        ]
        state["decision"]["phase2"].update({
            "designBoldness": {"level": 4, "profile": "bold"},
            "motionDelivery": {"mode": "pptx-plus-live-html", "creatorConfirmed": True, "evidence": "Creator approved live HTML."},
        })
        state["execution"]["slides"][0]["compositionPattern"] = "P10"
        state["execution"]["slides"][1]["compositionPattern"] = "P03"
        state["delivery"]["liveHtml"] = {
            "output": "live-presentation.html",
            "playbackAudit": {"result": "pass", "motionObserved": True, "htmlSha256": "", "notes": "Playback reviewed."},
        }
        task = self.write_task(state)
        live_html = task / "live-presentation.html"
        live_html.write_text("<canvas></canvas>", encoding="utf-8")
        persisted = json.loads((task / "workflow-state.json").read_text(encoding="utf-8"))
        persisted["delivery"]["liveHtml"]["playbackAudit"]["htmlSha256"] = hashlib.sha256(live_html.read_bytes()).hexdigest()
        (task / "workflow-state.json").write_text(json.dumps(persisted), encoding="utf-8")
        result = self.check(task, "deliver")
        self.assertEqual(result.returncode, 2)
        self.assertIn("live HTML delivery includes a static PPTX fallback output", result.stdout)


if __name__ == "__main__":
    unittest.main()
