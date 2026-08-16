import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image

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

    def test_portrait_reference_and_canvas_screenshots_use_native_canvas(self):
        try:
            from playwright.sync_api import sync_playwright
        except ImportError as exc:
            self.skipTest(f"Playwright unavailable: {exc}")

        with sync_playwright() as playwright:
            try:
                browser, _ = MEASURE.launch_browser(playwright)
            except RuntimeError as exc:
                self.skipTest(str(exc))
            else:
                browser.close()

        html = """<!doctype html><style>
        body { margin: 0; overflow: hidden; }
        .stage { width: 1080px; height: 1920px; transform-origin: 0 0; }
        .slide { position: relative; width: 1080px; height: 1920px; overflow: hidden; }
        .slide:not(.active) { display: none !important; }
        canvas { position: absolute; inset: 0; width: 100%; height: 100%; }
        h1 { position: relative; z-index: 1; margin: 80px; color: white; }
        </style><div id='stage' class='stage'>
        <section class='slide active' data-pptx-slide>
          <canvas data-pptx-canvas-id='portrait-canvas'></canvas><h1>Editable title</h1>
        </section><section class='slide' data-pptx-slide><h1>Second slide</h1></section>
        </div><script>
        const canvas = document.querySelector('canvas');
        canvas.width = 1080; canvas.height = 1920;
        const context = canvas.getContext('2d');
        context.fillStyle = '#123456'; context.fillRect(0, 0, 1080, 1920);
        addEventListener('resize', () => stage.style.transform = 'scale(.5)');
        </script>"""

        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            source = directory / "portrait.html"
            measurements = directory / "measurements.json"
            source.write_text(html, encoding="utf-8")

            result = MEASURE.measure(source, measurements,
                                     no_screenshots=False, verbose=False)
            first_slide = result["slides"][0]
            canvas_record = next(record for record in first_slide["records"]
                                 if record.get("kind") == "canvas")

            self.assertEqual((first_slide["slide"]["width"],
                              first_slide["slide"]["height"]), (1080, 1920))
            with Image.open(directory / "measurements_screenshots" / "slide_01.png") as image:
                self.assertEqual(image.size, (1080, 1920))
            with Image.open(canvas_record["screenshot"]) as image:
                self.assertEqual(image.size, (1080, 1920))


if __name__ == "__main__":
    unittest.main()
