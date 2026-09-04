import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BOOTSTRAP = ROOT / "ppt-workflow" / "scripts" / "bootstrap.ps1"
RUN_TESTS = ROOT / "scripts" / "run-tests.ps1"
WORKFLOW = ROOT / ".github" / "workflows" / "quality.yml"


def powershell_executable():
    return shutil.which("pwsh") or shutil.which("powershell")


def run_script(script, *arguments, environment=None):
    executable = powershell_executable()
    if executable is None:
        raise unittest.SkipTest("PowerShell is required for tooling script tests")
    child_environment = os.environ.copy()
    if environment:
        child_environment.update(environment)
    result = subprocess.run(
        [
            executable,
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(script),
            *map(str, arguments),
        ],
        cwd=ROOT,
        capture_output=True,
        env=child_environment,
        text=False,
        check=False,
    )
    result.stdout = result.stdout.decode("utf-8-sig", errors="replace")
    result.stderr = result.stderr.decode("utf-8-sig", errors="replace")
    return result


class ToolingScriptTests(unittest.TestCase):
    def test_bootstrap_reports_missing_distribution_and_install_command(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            fake_python = Path(temp_dir) / "missing-python.cmd"
            fake_python.write_text("@echo off\r\nexit /b 1\r\n", encoding="ascii")
            result = run_script(BOOTSTRAP, "-Python", fake_python)

        output = result.stdout + result.stderr
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("pypdf", output)
        self.assertIn("-m pip install -r ppt-workflow/requirements.txt -r html-to-pptx/requirements.txt", output)

    def test_run_tests_fails_before_discovery_when_dependency_is_missing(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            fake_python = Path(temp_dir) / "missing-python.cmd"
            fake_python.write_text("@echo off\r\nexit /b 1\r\n", encoding="ascii")
            result = run_script(RUN_TESTS, "-Python", fake_python)

        output = result.stdout + result.stderr
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("pypdf", output)
        self.assertIn("tests were not started", output)

    def test_quality_workflow_uses_windows_python_and_shared_scripts(self):
        workflow = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("runs-on: windows-latest", workflow)
        self.assertIn("python-version: ['3.12']", workflow)
        self.assertIn("ppt-workflow\\scripts\\bootstrap.ps1 -Install", workflow)
        self.assertIn(".\\scripts\\run-tests.ps1", workflow)

    def test_bootstrap_checks_render_and_com_dependencies(self):
        bootstrap = (ROOT / "ppt-workflow" / "scripts" / "bootstrap.ps1").read_text(encoding="utf-8")
        self.assertIn("pdf2image", bootstrap)
        self.assertIn("win32com.client", bootstrap)
        self.assertIn("PPT_FFMPEG_EXECUTABLE", bootstrap)
        self.assertIn("playwright install chromium", bootstrap)

    def test_bootstrap_rejects_an_invalid_configured_ffmpeg_path(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            missing_ffmpeg = Path(temp_dir) / "missing-ffmpeg.exe"
            result = run_script(
                BOOTSTRAP,
                "-Python",
                sys.executable,
                environment={"PPT_FFMPEG_EXECUTABLE": str(missing_ffmpeg)},
            )

        output = result.stdout + result.stderr
        self.assertEqual(result.returncode, 0, output)
        self.assertIn("PPT_FFMPEG_EXECUTABLE does not point to a file", output)
        self.assertNotIn(f"[PASS] ffmpeg with libx264 ({missing_ffmpeg}", output)


if __name__ == "__main__":
    unittest.main()
