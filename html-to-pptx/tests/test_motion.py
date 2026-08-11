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


if __name__ == "__main__":
    unittest.main()
