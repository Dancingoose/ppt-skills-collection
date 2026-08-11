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


HTML = """<!doctype html><html><head><script src='https://cdn.jsdelivr.net/npm/echarts@5'></script></head><body>
<section class='slide dark' data-pptx-slide data-slide-id='1' data-layout='B1' data-item-count='0' data-color-system='coastal-dark'></section>
<section class='slide' data-pptx-slide data-slide-id='2' data-layout='B6' data-item-count='1' data-color-system='coastal-light'></section>
</body></html>"""

PREVIEW_HTML = """<!doctype html><html><body>
<section class='slide' data-slide-id='1'></section>
<section class='slide' data-slide-id='2'></section>
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
    def write_task(self, state=None, html=HTML):
        directory = tempfile.TemporaryDirectory()
        task = Path(directory.name)
        if state is not None:
            (task / "workflow-state.json").write_text(json.dumps(state), encoding="utf-8")
        (task / "content-inventory.md").write_text(CONTENT_INVENTORY, encoding="utf-8")
        (task / "design.html").write_text(html, encoding="utf-8")
        (task / "preview.html").write_text(PREVIEW_HTML, encoding="utf-8")
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
                    "colorSystems": [
                        {"id": "coastal-dark", "mode": "dark", "slides": [1], "baseColor": "#10283C", "temperature": "cool", "dominantSurface": "ink with aqua details", "notes": "The cover uses the dark coastal system."},
                        {"id": "coastal-light", "mode": "light", "slides": [2], "baseColor": "#F2FBFA", "temperature": "cool", "dominantSurface": "foam with aqua details", "notes": "The content page uses the light coastal system."},
                    ],
                }), encoding="utf-8")
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

    def test_intent_gate_rejects_fewer_than_twelve_creator_answers(self):
        state = valid_state()
        state["decision"]["intentQuestionnaire"]["responses"].pop()
        result = self.check(self.write_task(state), "intent")
        self.assertEqual(result.returncode, 2)
        self.assertIn("exactly 12 responses", result.stdout)
        self.assertIn("includes every required question exactly once", result.stdout)

    def test_experimental_boldness_requires_live_html_delivery(self):
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
        self.assertIn("experimental design boldness requires a playable live HTML companion", result.stdout)

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
        self.assertIn("live composition requires a playable live HTML companion", result.stdout)

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


if __name__ == "__main__":
    unittest.main()
