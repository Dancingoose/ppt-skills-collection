import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile

from lxml import etree
from PIL import Image


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))


def load_module(name):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


ASSEMBLE = load_module("assemble")
SELF_CHECK = load_module("self_check")
VISUAL_AUDIT = load_module("visual_audit")


class CanvasDimensionTests(unittest.TestCase):
    def _slide(self, width=1440, height=1080):
        return {
            "slide": {
                "width": width,
                "height": height,
                "background": "rgb(255,255,255)",
                "theme": "test",
            },
            "records": [],
        }

    def test_assemble_uses_measured_four_by_three_ppt_size(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "four-three.pptx"
            ASSEMBLE.assemble({"slides": [self._slide()]}, output)
            with ZipFile(output) as archive:
                root = etree.fromstring(archive.read("ppt/presentation.xml"))
            ns = {"p": "http://schemas.openxmlformats.org/presentationml/2006/main"}
            size = root.find("p:sldSz", namespaces=ns)

            self.assertEqual((size.get("cx"), size.get("cy")), ("9144000", "6858000"))
            self.assertEqual(SELF_CHECK._pptx_render_size(output), (1440, 1080))

    def test_assemble_rejects_mixed_canvas_dimensions(self):
        with self.assertRaisesRegex(ValueError, "mixed slide dimensions"):
            ASSEMBLE.configure_slide_dimensions([
                self._slide(1440, 1080),
                self._slide(1920, 1080),
            ])

    def test_compare_image_keeps_original_panel_dimensions(self):
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            html = directory / "html.png"
            ppt = directory / "ppt.png"
            output = directory / "compare.png"
            Image.new("RGB", (144, 108), (20, 30, 40)).save(html)
            Image.new("RGB", (192, 108), (40, 50, 60)).save(ppt)

            VISUAL_AUDIT.build_compare_image(html, ppt, output, 1)

            with Image.open(output) as composite:
                self.assertEqual(composite.size, (344, 168))


if __name__ == "__main__":
    unittest.main()
