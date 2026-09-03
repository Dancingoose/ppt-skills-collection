import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from workflow_control import (
    append_event, artifact_hashes, canonical_json, control_status, event_digest,
    next_layer, read_event_chain, state_digest,
)


class WorkflowControlTests(unittest.TestCase):
    def test_canonical_and_state_hash_exclusions(self):
        self.assertEqual(canonical_json({"b": 1, "a": 2}), b'{"a":2,"b":1}')
        state = {"schemaVersion": 1, "control": {"stateSha256": "x", "eventHeadSha256": "y"}, "x": 1}
        state["control"]["stateSha256"] = state_digest(state)
        first = state_digest(state)
        state["control"]["eventHeadSha256"] = "changed"
        self.assertEqual(first, state_digest(state))

    def test_event_chain_and_tamper_detection(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "workflow-events.jsonl"
            first = append_event(path, {"eventId": "1", "command": "init"})
            append_event(path, {"eventId": "2", "command": "verify"})
            events, head = read_event_chain(path)
            self.assertEqual(len(events), 2)
            self.assertEqual(head, events[-1]["eventSha256"])
            raw = path.read_text(encoding="utf-8").replace(first, "0" * 64)
            path.write_text(raw, encoding="utf-8")
            with self.assertRaises(ValueError):
                read_event_chain(path)

    def test_layers_artifacts_and_status(self):
        self.assertTrue(next_layer("prep", "intent"))
        self.assertFalse(next_layer("prep", "design"))
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            state = {"schemaVersion": 1, "control": {"status": "active", "stateSha256": "", "eventHeadSha256": ""}}
            append_event(root / "workflow-events.jsonl", {"eventId": "1", "command": "init"})
            _, head = read_event_chain(root / "workflow-events.jsonl")
            state["control"]["eventHeadSha256"] = head
            state["control"]["stateSha256"] = state_digest(state)
            (root / "artifact.txt").write_text("x", encoding="utf-8")
            self.assertEqual(control_status(root, state), "active")
            self.assertIn("artifact.txt", artifact_hashes(root, state))
            state["x"] = 1
            self.assertEqual(control_status(root, state), "drifted")


if __name__ == "__main__":
    unittest.main()
