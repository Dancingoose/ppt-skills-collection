import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))


def load_module(name):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


PREFLIGHT = load_module("preflight")


class PreflightTests(unittest.TestCase):
    def test_rotated_child_inside_clipped_decoration_is_blocking(self):
        try:
            from playwright.sync_api import sync_playwright
        except ImportError as exc:
            self.skipTest(f"Playwright unavailable: {exc}")

        html = """<!doctype html>
        <style>
          [data-pptx-slide] { width: 1920px; height: 1080px; position: relative; }
          .deco { position: absolute; inset: 0; overflow: hidden; }
          .rotated { width: 130%; height: 130%; transform: rotate(8deg); background: #dbeafe; }
          .copy { position: absolute; left: 100px; top: 100px; font: 48px sans-serif; }
        </style>
        <section data-pptx-slide>
          <div class="deco"><div class="rotated"></div></div>
          <div class="copy">AI market outlook</div>
        </section>"""

        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "rotated-decoration.html"
            source.write_text(html, encoding="utf-8")
            result = PREFLIGHT.preflight(source, verbose=False)

        self.assertEqual(result["summary"]["blocking_risks"], [{"page": 1, "code": "R001"}])
        risk = result["slides"][0]["risks"][0]
        self.assertTrue(risk["blocking"])
        self.assertIn("clip-with-transformed-children", risk["detail"])


if __name__ == "__main__":
    unittest.main()
