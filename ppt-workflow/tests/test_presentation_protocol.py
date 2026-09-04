import copy
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from presentation_protocol import ProtocolError, build_protocol, protocol_errors, sync_protocol


def state_with_execution():
    return {
        "task": {"deliveryFormat": "pptx"},
        "decision": {
            "phase1": {"canvas": "ppt169"},
            "designProfile": {"selectedProfileId": "thesis-led"},
            "designOrchestration": {"selectedRecipeId": "thesis-led"},
        },
        "execution": {
            "html": "design.html",
            "slides": [
                {
                    "id": 1,
                    "layout": "B1",
                    "contentType": "cover",
                    "dark": False,
                    "archetype": "hero",
                    "compositionFamily": "editorial-stack",
                    "layoutEvidence": {"itemCount": 0, "sourceRefs": ["content-inventory.md: Slide 1"]},
                    "visualEffect": {"status": "skipped", "reason": "Text-led cover."},
                }
            ],
        },
    }


class PresentationProtocolTests(unittest.TestCase):
    def write_task(self, state):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        task = Path(directory.name)
        (task / "design.html").write_text("<main>deck</main>", encoding="utf-8")
        return task

    def test_build_captures_the_current_html_and_slide_contract(self):
        state = state_with_execution()
        task = self.write_task(state)

        protocol = build_protocol(task, state)

        self.assertEqual(protocol["kind"], "ppt-workflow-presentation-protocol")
        self.assertEqual(protocol["source"]["html"], "design.html")
        self.assertEqual(protocol["source"]["sha256"], hashlib.sha256((task / "design.html").read_bytes()).hexdigest())
        self.assertEqual(protocol["deck"]["slideIds"], [1])
        self.assertEqual(protocol["slides"][0]["compositionFamily"], "editorial-stack")
        self.assertEqual(protocol_errors(task, state, protocol), [])

    def test_validation_rejects_html_and_manifest_drift(self):
        state = state_with_execution()
        task = self.write_task(state)
        protocol = build_protocol(task, state)

        (task / "design.html").write_text("<main>changed</main>", encoding="utf-8")
        self.assertIn("protocol source does not match the current execution HTML", protocol_errors(task, state, protocol))

        changed_state = copy.deepcopy(state)
        changed_state["execution"]["slides"][0]["layout"] = "B2"
        self.assertIn("protocol slides do not match the current execution manifest", protocol_errors(task, changed_state, protocol))

    def test_sync_refuses_to_overwrite_workflow_state_or_execution_html(self):
        state = state_with_execution()
        task = self.write_task(state)
        (task / "workflow-state.json").write_text(json.dumps(state), encoding="utf-8")

        for artifact in ("workflow-state.json", "design.html"):
            with self.subTest(artifact=artifact):
                with self.assertRaisesRegex(ProtocolError, "cannot overwrite"):
                    sync_protocol(task, artifact)


if __name__ == "__main__":
    unittest.main()
