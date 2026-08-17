import importlib.util
import tempfile
import unittest
import zipfile
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "template_embedding.py"
SPEC = importlib.util.spec_from_file_location("template_embedding", SCRIPT)
EMBEDDING = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(EMBEDDING)


def template_parts():
    return {
        "[Content_Types].xml": b"""<?xml version='1.0' encoding='UTF-8'?>
<Types xmlns='http://schemas.openxmlformats.org/package/2006/content-types'>
  <Default Extension='rels' ContentType='application/vnd.openxmlformats-package.relationships+xml'/>
  <Default Extension='xml' ContentType='application/xml'/>
  <Override PartName='/ppt/presentation.xml' ContentType='application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml'/>
  <Override PartName='/ppt/slides/slide1.xml' ContentType='application/vnd.openxmlformats-officedocument.presentationml.slide+xml'/>
</Types>""",
        "ppt/presentation.xml": b"""<?xml version='1.0' encoding='UTF-8'?>
<p:presentation xmlns:a='http://schemas.openxmlformats.org/drawingml/2006/main'
 xmlns:r='http://schemas.openxmlformats.org/officeDocument/2006/relationships'
 xmlns:p='http://schemas.openxmlformats.org/presentationml/2006/main'>
  <p:sldIdLst><p:sldId id='256' r:id='rId1'/></p:sldIdLst>
</p:presentation>""",
        "ppt/_rels/presentation.xml.rels": b"""<?xml version='1.0' encoding='UTF-8'?>
<Relationships xmlns='http://schemas.openxmlformats.org/package/2006/relationships'>
  <Relationship Id='rId1' Type='http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide' Target='slides/slide1.xml'/>
</Relationships>""",
        "ppt/slides/slide1.xml": b"""<?xml version='1.0' encoding='UTF-8'?>
<p:sld xmlns:a='http://schemas.openxmlformats.org/drawingml/2006/main'
 xmlns:r='http://schemas.openxmlformats.org/officeDocument/2006/relationships'
 xmlns:p='http://schemas.openxmlformats.org/presentationml/2006/main'>
  <p:cSld><p:spTree/></p:cSld>
</p:sld>""",
        "ppt/slides/_rels/slide1.xml.rels": b"""<?xml version='1.0' encoding='UTF-8'?>
<Relationships xmlns='http://schemas.openxmlformats.org/package/2006/relationships'>
  <Relationship Id='rId1' Type='http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout' Target='../slideLayouts/slideLayout1.xml'/>
</Relationships>""",
        "ppt/slideLayouts/slideLayout1.xml": b"<p:sldLayout xmlns:p='http://schemas.openxmlformats.org/presentationml/2006/main'/>",
        "ppt/slideMasters/slideMaster1.xml": b"<p:sldMaster xmlns:p='http://schemas.openxmlformats.org/presentationml/2006/main'/>",
        "ppt/theme/theme1.xml": b"<a:theme xmlns:a='http://schemas.openxmlformats.org/drawingml/2006/main'/>",
        "ppt/media/logo.png": b"original-logo-background",
    }


class TemplateEmbeddingTests(unittest.TestCase):
    def make_template(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        path = Path(directory.name) / "template.pptx"
        with zipfile.ZipFile(path, "w") as archive:
            for name, data in template_parts().items():
                archive.writestr(name, data)
        return path

    def replace_part(self, archive_path: Path, name: str, data: bytes):
        with zipfile.ZipFile(archive_path) as archive:
            parts = {info.filename: archive.read(info.filename) for info in archive.infolist()}
        parts[name] = data
        with zipfile.ZipFile(archive_path, "w") as archive:
            for part_name, part_data in parts.items():
                archive.writestr(part_name, part_data)

    def test_profile_records_immutable_template_parts(self):
        template = self.make_template()
        profile = EMBEDDING.profile_template(template)
        protected = {item["part"] for item in profile["protectedParts"]}

        self.assertEqual(profile["mode"], "append-only-template-embedding")
        self.assertEqual(profile["template"]["slideCount"], 1)
        self.assertIn("ppt/media/logo.png", protected)
        self.assertIn("ppt/slides/slide1.xml", protected)
        self.assertNotIn("ppt/presentation.xml", protected)

    def test_clone_appends_background_pages_without_changing_template_parts(self):
        template = self.make_template()
        output = template.with_name("embedded.pptx")

        created = EMBEDDING.clone_background_slide(template, output, source_slide=1, count=2)
        report = EMBEDDING.verify_template_integrity(template, output)

        self.assertEqual([item["newSlide"] for item in created], [2, 3])
        self.assertEqual(report["result"], "pass")
        self.assertEqual(report["newSlideParts"], ["ppt/slides/slide2.xml", "ppt/slides/slide3.xml"])
        with zipfile.ZipFile(template) as original, zipfile.ZipFile(output) as candidate:
            self.assertEqual(candidate.read("ppt/slides/slide2.xml"), original.read("ppt/slides/slide1.xml"))
            self.assertEqual(candidate.read("ppt/media/logo.png"), original.read("ppt/media/logo.png"))

    def test_integrity_rejects_a_changed_logo_background(self):
        template = self.make_template()
        output = template.with_name("embedded.pptx")
        EMBEDDING.clone_background_slide(template, output, source_slide=1, count=1)
        self.replace_part(output, "ppt/media/logo.png", b"changed-logo-background")

        report = EMBEDDING.verify_template_integrity(template, output)

        self.assertEqual(report["result"], "fail")
        self.assertEqual(report["changedProtectedParts"], ["ppt/media/logo.png"])

    def test_integrity_rejects_a_changed_original_slide(self):
        template = self.make_template()
        output = template.with_name("embedded.pptx")
        EMBEDDING.clone_background_slide(template, output, source_slide=1, count=1)
        self.replace_part(output, "ppt/slides/slide1.xml", b"changed-original-slide")

        report = EMBEDDING.verify_template_integrity(template, output)

        self.assertEqual(report["result"], "fail")
        self.assertEqual(report["changedProtectedParts"], ["ppt/slides/slide1.xml"])

    def test_integrity_rejects_a_changed_presentation_setting(self):
        template = self.make_template()
        output = template.with_name("embedded.pptx")
        EMBEDDING.clone_background_slide(template, output, source_slide=1, count=1)
        with zipfile.ZipFile(output) as archive:
            presentation = archive.read("ppt/presentation.xml")
        self.replace_part(
            output,
            "ppt/presentation.xml",
            presentation.replace(b"<p:sldIdLst>", b"<p:sldSz cx='1' cy='1'/><p:sldIdLst>"),
        )

        report = EMBEDDING.verify_template_integrity(template, output)

        self.assertEqual(report["result"], "fail")
        self.assertIn("Presentation structure changed", report["structuralErrors"][0])

    def test_clone_rejects_a_missing_base_slide(self):
        template = self.make_template()
        with self.assertRaisesRegex(ValueError, "source slide 2"):
            EMBEDDING.clone_background_slide(template, template.with_name("out.pptx"), source_slide=2, count=1)


if __name__ == "__main__":
    unittest.main()
