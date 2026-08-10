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
            "antiTemplateReview": {"reviewer": "frontend-design", "result": "pass", "notes": "Specific layout choices."},
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
            "independentReview": {"result": "pass", "notes": "No layout defects."},
        },
        "delivery": {"converterHealthChecked": True, "canvasRasterizationAcknowledged": True},
    }


HTML = """<!doctype html><html><head><script src='https://cdn.jsdelivr.net/npm/echarts@5'></script></head><body>
<section class='slide dark' data-slide-id='1' data-layout='B1' data-item-count='0'></section>
<section class='slide' data-slide-id='2' data-layout='B6' data-item-count='1'></section>
</body></html>"""


class WorkflowStateTests(unittest.TestCase):
    def write_task(self, state=None, html=HTML):
        directory = tempfile.TemporaryDirectory()
        task = Path(directory.name)
        if state is not None:
            (task / "workflow-state.json").write_text(json.dumps(state), encoding="utf-8")
        (task / "design.html").write_text(html, encoding="utf-8")
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
