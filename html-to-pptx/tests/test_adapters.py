import importlib.util
import tempfile
import unittest
from pathlib import Path


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"


def load_module(name):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


ADAPTERS = load_module("adapters")
RUNTIME = load_module("browser_runtime")


class AdapterDisplayTests(unittest.TestCase):
    def test_activation_preserves_each_slide_display_mode(self):
        try:
            from playwright.sync_api import sync_playwright
        except ImportError as exc:
            self.skipTest(f"Playwright unavailable: {exc}")
        html = """<!doctype html><style>
        .slide { width: 1920px; height: 1080px; }
        .slide:not(.active) { display: none !important; }
        .cover { display: flex; }
        </style><section class='slide cover active'>cover</section>
        <section class='slide'><div id='chart'>body</div></section>"""
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "deck.html"
            source.write_text(html, encoding="utf-8")
            with sync_playwright() as playwright:
                try:
                    browser, _ = RUNTIME.launch_browser(playwright)
                except RuntimeError as exc:
                    self.skipTest(str(exc))
                try:
                    page = browser.new_page(viewport={"width": 1920, "height": 1080})
                    page.goto(source.resolve().as_uri(), wait_until="domcontentloaded")
                    page.evaluate(ADAPTERS.PREPARE_JS)
                    page.evaluate(ADAPTERS.ACTIVATE_JS, 1)
                    result = page.evaluate("""() => {
                        const target = document.querySelector('[data-pptx-target]');
                        return { display: getComputedStyle(target).display,
                                 width: target.getBoundingClientRect().width };
                    }""")
                finally:
                    browser.close()
        self.assertEqual(result["display"], "block")
        self.assertEqual(result["width"], 1920)

    def test_activation_preserves_explicit_four_by_three_canvas(self):
        try:
            from playwright.sync_api import sync_playwright
        except ImportError as exc:
            self.skipTest(f"Playwright unavailable: {exc}")
        html = """<!doctype html><style>
        .slide { width: 1440px; height: 1080px; }
        .slide:not(.active) { display: none !important; }
        </style><section class='slide active' data-pptx-slide>cover</section>
        <section class='slide' data-pptx-slide>body</section>"""
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "four-three.html"
            source.write_text(html, encoding="utf-8")
            with sync_playwright() as playwright:
                try:
                    browser, _ = RUNTIME.launch_browser(playwright)
                except RuntimeError as exc:
                    self.skipTest(str(exc))
                try:
                    page = browser.new_page(viewport={"width": 1920, "height": 1080})
                    page.goto(source.resolve().as_uri(), wait_until="domcontentloaded")
                    page.evaluate(ADAPTERS.PREPARE_JS)
                    page.evaluate(ADAPTERS.ACTIVATE_JS, 1)
                    result = page.evaluate("""() => {
                        const target = document.querySelector('[data-pptx-target]');
                        const rect = target.getBoundingClientRect();
                        return { width: rect.width, height: rect.height,
                                 cssWidth: getComputedStyle(target).width,
                                 cssHeight: getComputedStyle(target).height };
                    }""")
                finally:
                    browser.close()
        self.assertEqual(result["width"], 1440)
        self.assertEqual(result["height"], 1080)
        self.assertEqual(result["cssWidth"], "1440px")
        self.assertEqual(result["cssHeight"], "1080px")

    def test_reassertion_recovers_canvas_after_resize_handler_scales_parent(self):
        try:
            from playwright.sync_api import sync_playwright
        except ImportError as exc:
            self.skipTest(f"Playwright unavailable: {exc}")
        html = """<!doctype html><style>
        .slide { width: 1440px; height: 1080px; }
        .slide:not(.active) { display: none !important; }
        </style><div id='stage'><section class='slide active' data-pptx-slide>cover</section>
        <section class='slide' data-pptx-slide>body</section></div>
        <script>addEventListener('resize', () => stage.style.transform = 'scale(.75)')</script>"""
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "responsive-four-three.html"
            source.write_text(html, encoding="utf-8")
            with sync_playwright() as playwright:
                try:
                    browser, _ = RUNTIME.launch_browser(playwright)
                except RuntimeError as exc:
                    self.skipTest(str(exc))
                try:
                    page = browser.new_page(viewport={"width": 1920, "height": 1080})
                    page.goto(source.resolve().as_uri(), wait_until="domcontentloaded")
                    page.evaluate(ADAPTERS.PREPARE_JS)
                    page.evaluate(ADAPTERS.ACTIVATE_JS, 1)
                    page.evaluate("() => dispatchEvent(new Event('resize'))")
                    page.evaluate(ADAPTERS.REASSERT_TARGET_POSITION_JS)
                    result = page.evaluate("""() => {
                        const target = document.querySelector('[data-pptx-target]');
                        return target.getBoundingClientRect().toJSON();
                    }""")
                finally:
                    browser.close()
        self.assertEqual((result["width"], result["height"]), (1440, 1080))


if __name__ == "__main__":
    unittest.main()
