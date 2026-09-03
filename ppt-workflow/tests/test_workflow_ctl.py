import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import workflow_ctl


class WorkflowCtlTests(unittest.TestCase):
    def test_init_does_not_overwrite_and_status_legacy(self):
        with tempfile.TemporaryDirectory() as directory:
            task = Path(directory) / "task"
            self.assertEqual(workflow_ctl.main(["init", "--task", str(task), "--name", "x", "--format", "html"]), 0)
            state_path = task / "workflow-state.json"
            original = state_path.read_text(encoding="utf-8")
            self.assertEqual(workflow_ctl.main(["init", "--task", str(task), "--name", "y", "--format", "pptx"]), 2)
            self.assertEqual(state_path.read_text(encoding="utf-8"), original)

    @patch.object(workflow_ctl, "run_gate")
    def test_advance_rejects_jump_and_failed_gate(self, run_gate):
        with tempfile.TemporaryDirectory() as directory:
            task = Path(directory) / "task"
            workflow_ctl.main(["init", "--task", str(task), "--name", "x", "--format", "html"])
            self.assertEqual(workflow_ctl.main(["advance", "--task", str(task), "--to", "design"]), 2)
            run_gate.return_value = workflow_ctl.GateResult(2, 0, 1, "Summary: 0 pass, 1 fail", "[FAIL] bad\nSummary: 0 pass, 1 fail\n")
            self.assertNotEqual(workflow_ctl.main(["advance", "--task", str(task), "--to", "intent"]), 0)
            state = json.loads((task / "workflow-state.json").read_text(encoding="utf-8"))
            self.assertEqual(state["control"]["currentLayer"], "prep")

    @patch.object(workflow_ctl, "run_gate")
    def test_seal_requires_deliver_and_can_seal(self, run_gate):
        with tempfile.TemporaryDirectory() as directory:
            task = Path(directory) / "task"
            workflow_ctl.main(["init", "--task", str(task), "--name", "x", "--format", "html"])
            self.assertEqual(workflow_ctl.main(["seal", "--task", str(task)]), 2)
            state_path = task / "workflow-state.json"
            state = json.loads(state_path.read_text(encoding="utf-8")); state["control"]["currentLayer"] = "deliver"
            state["control"]["stateSha256"] = workflow_ctl.state_digest(state)
            state_path.write_text(json.dumps(state), encoding="utf-8")
            run_gate.return_value = workflow_ctl.GateResult(0, 1, 0, "Summary: 1 pass, 0 fail", "")
            self.assertEqual(workflow_ctl.main(["seal", "--task", str(task)]), 0)


if __name__ == "__main__":
    unittest.main()
