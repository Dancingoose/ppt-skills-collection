import importlib.util
import os
import sys
import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile

from lxml import etree
from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))


def load_module(name):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


MOTION = load_module("motion")
MEASURE = load_module("measure")
ASSEMBLE = load_module("assemble")


class MotionTests(unittest.TestCase):
    def test_emits_composable_motion_plan_and_triggers(self):
        presentation = Presentation()
        slide = presentation.slides.add_slide(presentation.slide_layouts[6])
        shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, 0, 0, 1000000, 1000000)
        plan = [
            {"effect": "fade", "duration": 300, "trigger": "click"},
            {"effect": "motion", "path": "M 0 0 L 0.18 -0.08 E", "duration": 650, "trigger": "with"},
            {"effect": "scale", "from": [80, 80], "to": [115, 115], "duration": 650, "trigger": "with"},
            {"effect": "rotate", "by": 360, "duration": 650, "trigger": "with"},
            {"effect": "fade", "duration": 250, "trigger": "after"},
        ]
        result = MOTION.apply_native_animations(
            slide, [{"id": "hero", "plan": plan}], {"hero": shape}
        )
        self.assertEqual(result["emitted"], ["hero"])
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "complex-motion.pptx"
            presentation.save(output)
            with ZipFile(output) as archive:
                root = etree.fromstring(archive.read("ppt/slides/slide1.xml"))
        ns = {"p": "http://schemas.openxmlformats.org/presentationml/2006/main"}
        self.assertEqual(root.xpath("count(.//p:animMotion[@path='M 0 0 L 0.18 -0.08 E'])", namespaces=ns), 1.0)
        self.assertEqual(root.xpath("count(.//p:animScale/p:from[@x='800' and @y='800'])", namespaces=ns), 1.0)
        self.assertEqual(root.xpath("count(.//p:animRot[@by='21600000'])", namespaces=ns), 1.0)
        self.assertEqual(root.xpath("count(.//p:cTn[@nodeType='withEffect'])", namespaces=ns), 3.0)
        self.assertEqual(root.xpath("count(.//p:cTn[@nodeType='afterEffect'])", namespaces=ns), 1.0)

    def test_emits_native_timing_for_fade_and_spin(self):
        presentation = Presentation()
        slide = presentation.slides.add_slide(presentation.slide_layouts[6])
        fade_shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, 1000000, 1000000)
        spin_shape = slide.shapes.add_shape(MSO_SHAPE.OVAL, 1000000, 0, 1000000, 1000000)

        result = MOTION.apply_native_animations(slide, [
            {"id": "fade", "kind": "fade", "duration": 600, "delay": 0},
            {"id": "spin", "kind": "spin", "duration": 800, "delay": 120},
        ], {"fade": fade_shape, "spin": spin_shape})

        self.assertEqual(result["emitted"], ["fade", "spin"])
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "motion.pptx"
            presentation.save(output)
            with ZipFile(output) as archive:
                root = etree.fromstring(archive.read("ppt/slides/slide1.xml"))
        ns = {"p": "http://schemas.openxmlformats.org/presentationml/2006/main"}
        self.assertEqual(len(root.xpath("./p:timing", namespaces=ns)), 1)
        self.assertEqual(root.xpath("count(.//p:animEffect[@filter='fade'])", namespaces=ns), 1.0)
        self.assertEqual(root.xpath("count(.//p:animRot[@by='21600000'])", namespaces=ns), 1.0)
        self.assertEqual({int(v) for v in root.xpath(".//p:bldP/@spid", namespaces=ns)},
                         {fade_shape.shape_id, spin_shape.shape_id})

    def test_measure_captures_css_motion_before_static_freeze(self):
        try:
            from playwright.sync_api import sync_playwright  # noqa: F401
        except ImportError as exc:
            self.skipTest(f"Playwright unavailable: {exc}")
        html = """<!doctype html><style>
        .slide { width: 1920px; height: 1080px; position: relative; }
        @keyframes rise { from { opacity: 0; transform: translateY(40px); } to { opacity: 1; transform: none; } }
        h1 { animation: rise 700ms 150ms both; }
        </style><section class='slide' data-pptx-slide><h1>Animated title</h1></section>"""
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "motion.html"
            output = Path(directory) / "motion.pptx"
            source.write_text(html, encoding="utf-8")
            data = MEASURE.measure(source, no_screenshots=True, verbose=False)
            ASSEMBLE.assemble(data, output)
            with ZipFile(output) as archive:
                root = etree.fromstring(archive.read("ppt/slides/slide1.xml"))
        slide = data["slides"][0]
        self.assertEqual(slide["motions"][0]["kind"], "fade")
        self.assertEqual(slide["motions"][0]["delay"], 150)
        self.assertTrue(any(record.get("motionId") == slide["motions"][0]["id"]
                            for record in slide["records"]))
        ns = {"p": "http://schemas.openxmlformats.org/presentationml/2006/main"}
        self.assertEqual(root.xpath("count(.//p:animEffect[@filter='fade'])", namespaces=ns), 1.0)

    def test_measure_captures_explicit_motion_plan(self):
        try:
            from playwright.sync_api import sync_playwright  # noqa: F401
        except ImportError as exc:
            self.skipTest(f"Playwright unavailable: {exc}")
        html = """<!doctype html><style>
        .slide { width: 1920px; height: 1080px; position: relative; }
        </style><section class='slide' data-pptx-slide>
        <div data-pptx-motion-plan='[{"effect":"fade","duration":300,"trigger":"click"},{"effect":"motion","path":"M 0 0 L 0.2 0 E","duration":500,"trigger":"with"}]'>Complex</div>
        </section>"""
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "plan.html"
            source.write_text(html, encoding="utf-8")
            data = MEASURE.measure(source, no_screenshots=True, verbose=False)
        plan = data["slides"][0]["motions"][0]["plan"]
        self.assertEqual([item["effect"] for item in plan], ["fade", "motion"])
        self.assertEqual(plan[1]["trigger"], "with")

    def test_measure_decomposes_parallel_css_transforms(self):
        try:
            from playwright.sync_api import sync_playwright  # noqa: F401
        except ImportError as exc:
            self.skipTest(f"Playwright unavailable: {exc}")
        html = """<!doctype html><style>
        .slide { width: 1920px; height: 1080px; position: relative; }
        @keyframes reveal {
          from { opacity: 0; transform: translate(40px, 20px) scale(.8) rotate(-20deg); }
          to { opacity: 1; transform: none; }
        }
        .hero { position: absolute; left: 100px; top: 100px; animation: reveal 600ms both; }
        </style><section class='slide' data-pptx-slide><div class='hero'>Hero</div></section>"""
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "parallel.html"
            source.write_text(html, encoding="utf-8")
            data = MEASURE.measure(source, no_screenshots=True, verbose=False)
        plan = data["slides"][0]["motions"][0]["plan"]
        self.assertEqual([item["effect"] for item in plan], ["fade", "motion", "scale", "rotate"])
        self.assertEqual([item["trigger"] for item in plan], ["click", "with", "with", "with"])
        self.assertEqual(plan[1]["path"], "M 0.020833 0.018519 L 0 0 E")
        self.assertAlmostEqual(plan[2]["from"][0], 80.0, places=4)
        self.assertAlmostEqual(plan[2]["from"][1], 80.0, places=4)
        self.assertEqual(plan[3]["from"], -20)

    @unittest.skipUnless(os.name == "nt", "PowerPoint COM validation is Windows-only")
    def test_powerpoint_recognizes_emitted_fade(self):
        try:
            import win32com.client
        except ImportError as exc:
            self.skipTest(f"pywin32 unavailable: {exc}")
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "powerpoint-motion.pptx"
            presentation = Presentation()
            slide = presentation.slides.add_slide(presentation.slide_layouts[6])
            fade_shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, 1000000, 1000000)
            spin_shape = slide.shapes.add_shape(MSO_SHAPE.OVAL, 1000000, 0, 1000000, 1000000)
            MOTION.apply_native_animations(
                slide,
                [
                    {"id": "fade", "kind": "fade", "duration": 600, "delay": 0},
                    {"id": "spin", "kind": "spin", "duration": 800, "delay": 0},
                ],
                {"fade": fade_shape, "spin": spin_shape},
            )
            presentation.save(output)
            app = win32com.client.Dispatch("PowerPoint.Application")
            try:
                document = app.Presentations.Open(str(output), False, True, False)
                try:
                    sequence = document.Slides.Item(1).TimeLine.MainSequence
                    self.assertEqual(sequence.Count, 2)
                    self.assertEqual(sequence.Item(1).EffectType, 10)
                    self.assertEqual(sequence.Item(2).EffectType, 61)
                finally:
                    document.Close()
            finally:
                app.Quit()

    @unittest.skipUnless(os.name == "nt", "PowerPoint COM validation is Windows-only")
    def test_powerpoint_recognizes_composable_motion_plan(self):
        try:
            import win32com.client
        except ImportError as exc:
            self.skipTest(f"pywin32 unavailable: {exc}")
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "powerpoint-complex-motion.pptx"
            presentation = Presentation()
            slide = presentation.slides.add_slide(presentation.slide_layouts[6])
            shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, 1000000, 1000000)
            MOTION.apply_native_animations(slide, [{
                "id": "hero",
                "plan": [
                    {"effect": "fade", "duration": 300, "trigger": "click"},
                    {"effect": "motion", "path": "M 0 0 L 0.18 -0.08 E", "duration": 650, "trigger": "with"},
                    {"effect": "scale", "from": [80, 80], "to": [115, 115], "duration": 650, "trigger": "with"},
                    {"effect": "rotate", "by": 360, "duration": 650, "trigger": "with"},
                    {"effect": "fade", "duration": 250, "trigger": "after"},
                ],
            }], {"hero": shape})
            presentation.save(output)
            app = win32com.client.Dispatch("PowerPoint.Application")
            try:
                document = app.Presentations.Open(str(output), False, True, False)
                try:
                    sequence = document.Slides.Item(1).TimeLine.MainSequence
                    self.assertEqual(sequence.Count, 5)
                    self.assertEqual([sequence.Item(i).Timing.TriggerType for i in range(1, 6)], [1, 2, 2, 2, 3])
                    self.assertEqual(sequence.Item(2).EffectType, 0)
                    self.assertEqual(sequence.Item(3).EffectType, 0)
                    self.assertEqual(sequence.Item(4).EffectType, 61)
                finally:
                    document.Close()
            finally:
                app.Quit()


if __name__ == "__main__":
    unittest.main()
