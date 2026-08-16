import importlib.util
import os
import unittest
from pathlib import Path
from unittest.mock import patch


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "browser_runtime.py"
SPEC = importlib.util.spec_from_file_location("browser_runtime", SCRIPT)
RUNTIME = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(RUNTIME)


class BrowserRuntimeTests(unittest.TestCase):
    def test_explicit_existing_browser_path_is_selected(self):
        path = Path(r"C:\\tools\\browser.exe")
        with patch.dict(os.environ, {"PPT_PLAYWRIGHT_EXECUTABLE": str(path)}, clear=False), patch.object(Path, "is_file", return_value=True):
            self.assertEqual(RUNTIME.candidate_executables()[0], path)

    def test_falls_back_after_bundled_chromium_failure(self):
        class Chromium:
            def __init__(self): self.calls = []
            def launch(self, **kwargs):
                self.calls.append(kwargs)
                if "executable_path" not in kwargs: raise RuntimeError("missing bundled browser")
                return "edge-browser"
        class Playwright: chromium = Chromium()
        executable = Path(r"C:\\tools\\edge.exe")
        with patch.object(RUNTIME, "candidate_executables", return_value=[executable]):
            browser, name = RUNTIME.launch_browser(Playwright())
        self.assertEqual(browser, "edge-browser")
        self.assertEqual(name, str(executable))
        self.assertEqual(Playwright.chromium.calls[1]["executable_path"], str(executable))


if __name__ == "__main__":
    unittest.main()
