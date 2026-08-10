import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "check_ppt_execution.py"


class CheckPptExecutionConsoleTests(unittest.TestCase):
    def test_legacy_checker_handles_gbk_console_output(self):
        with tempfile.TemporaryDirectory() as directory:
            environment = os.environ.copy()
            environment["PYTHONIOENCODING"] = "gbk"
            result = subprocess.run(
                [sys.executable, str(SCRIPT), "--layer", "prep", "--task", directory],
                capture_output=True,
                encoding="utf-8",
                env=environment,
                check=False,
            )

        self.assertEqual(result.returncode, 2)
        self.assertIn("FAIL", result.stdout)
        self.assertNotIn("UnicodeEncodeError", result.stderr)


if __name__ == "__main__":
    unittest.main()
