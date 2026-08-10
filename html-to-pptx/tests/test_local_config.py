import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "local_config.py"
SPEC = importlib.util.spec_from_file_location("local_config", SCRIPT)
CONFIG = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CONFIG)


class LocalConfigTests(unittest.TestCase):
    def test_missing_config_uses_executable_triage_audit(self):
        with tempfile.TemporaryDirectory() as directory:
            missing = Path(directory) / "missing.toml"
            with patch.object(CONFIG, "CONFIG_PATH", missing):
                self.assertEqual(CONFIG.audit_mode(), "triage")

    def test_invalid_audit_mode_falls_back_to_triage(self):
        with patch.object(CONFIG, "load", return_value={"audit": {"mode": "invalid"}}):
            self.assertEqual(CONFIG.audit_mode(), "triage")


if __name__ == "__main__":
    unittest.main()
