import importlib.util
import sys
import unittest
from pathlib import Path


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))


def load_module(name):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


MEASURE = load_module("measure")


class CanvasCaptureTests(unittest.TestCase):
    def test_canvas_capture_hides_and_restores_foreground_siblings(self):
        try:
            from playwright.sync_api import sync_playwright
        except ImportError as exc:
            self.skipTest(f"Playwright unavailable: {exc}")

        html = """<!doctype html><section>
        <canvas data-pptx-canvas-id='slide1-canvas1'></canvas>
        <h1 id='title'>Editable title</h1><p id='body'>Editable body</p>
        </section>"""
        with sync_playwright() as playwright:
            try:
                browser, _ = MEASURE.launch_browser(playwright)
            except RuntimeError as exc:
                self.skipTest(str(exc))
            try:
                page = browser.new_page(viewport={"width": 1920, "height": 1080})
                page.set_content(html)
                page.evaluate(MEASURE._CANVAS_HIDE_SIBLINGS_JS, "slide1-canvas1")
                hidden = page.evaluate("""() => ({
                    canvas: getComputedStyle(document.querySelector('canvas')).visibility,
                    title: getComputedStyle(document.querySelector('#title')).visibility,
                    body: getComputedStyle(document.querySelector('#body')).visibility
                })""")
                page.evaluate(MEASURE._CANVAS_RESTORE_SIBLINGS_JS)
                restored = page.evaluate("""() => ({
                    title: document.querySelector('#title').style.visibility,
                    body: document.querySelector('#body').style.visibility
                })""")
            finally:
                browser.close()

        self.assertEqual(hidden, {"canvas": "visible", "title": "hidden", "body": "hidden"})
        self.assertEqual(restored, {"title": "", "body": ""})
        self.assertIs(MEASURE._MARKER_SHOOT_SPECS["canvas"][2], MEASURE._CANVAS_HIDE_SIBLINGS_JS)
        self.assertIs(MEASURE._MARKER_SHOOT_SPECS["canvas"][3], MEASURE._CANVAS_RESTORE_SIBLINGS_JS)


if __name__ == "__main__":
    unittest.main()
