import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import workflow_ctl


class WorkflowCtlIntegrationTests(unittest.TestCase):
    @patch.object(workflow_ctl, "run_gate")
    def test_init_verify_advance_log_and_drift(self, run_gate):
        with tempfile.TemporaryDirectory() as directory:
            task = Path(directory) / "demo"
            run_gate.return_value = workflow_ctl.GateResult(0, 2, 0, "Summary: 2 pass, 0 fail", "[PASS] ok\nSummary: 2 pass, 0 fail\n")
            self.assertEqual(workflow_ctl.main(["init", "--task", str(task), "--name", "demo", "--format", "html"]), 0)
            self.assertEqual(workflow_ctl.main(["verify", "--task", str(task), "--layer", "prep"]), 0)
            self.assertEqual(workflow_ctl.main(["advance", "--task", str(task), "--to", "intent"]), 0)
            events = (task / "workflow-events.jsonl").read_text(encoding="utf-8").splitlines()
            self.assertEqual(len(events), 3)
            state = json.loads((task / "workflow-state.json").read_text(encoding="utf-8"))
            self.assertEqual(state["control"]["currentLayer"], "intent")
            (task / "changed.txt").write_text("drift", encoding="utf-8")
            self.assertEqual(workflow_ctl.main(["status", "--task", str(task)]), 1)
            self.assertEqual(workflow_ctl.main(["advance", "--task", str(task), "--to", "design"]), 1)


if __name__ == "__main__":
    unittest.main()
