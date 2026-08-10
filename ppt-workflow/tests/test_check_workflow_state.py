import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "check_workflow_state.py"


def valid_state():
    passport = {
        "theme": "swiss-grid", "accent": "#0057B8", "background": "#FFFFFF",
        "titleFont": "Helvetica", "bodyFont": "Noto Sans SC", "style": "Swiss editorial",
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
            "phase2": {"pageCount": 2, "theme": "swiss-grid", "contentHandling": "extend", "imageSource": "none"},
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
                "notes": "Reviewed each source slide for overlap, clipping, and contrast.",
            },
            "independentReview": {"result": "pass", "notes": "No layout defects."},
        },
        "delivery": {"converterHealthChecked": True, "canvasRasterizationAcknowledged": True},
    }


HTML = """<!doctype html><html><head><script src='https://cdn.jsdelivr.net/npm/echarts@5'></script></head><body>
<section class='slide dark' data-pptx-slide data-slide-id='1' data-layout='B1' data-item-count='0'></section>
<section class='slide' data-pptx-slide data-slide-id='2' data-layout='B6' data-item-count='1'></section>
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
        if state is not None:
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
        self.addCleanup(directory.cleanup)
        return task

    def check(self, task, layer):
        return subprocess.run(
            [sys.executable, str(SCRIPT), "--task", str(task), "--layer", layer],
            capture_output=True, text=True, check=False,
        )

    def test_valid_prep_decision_and_execution_pass(self):
        task = self.write_task(valid_state())
        for layer in ("prep", "decision", "exec"):
            result = self.check(task, layer)
            self.assertEqual(result.returncode, 0, result.stdout)

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


if __name__ == "__main__":
    unittest.main()
