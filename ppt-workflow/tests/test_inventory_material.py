import importlib.util
import tempfile
import unittest
import zipfile
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "inventory_material.py"
SPEC = importlib.util.spec_from_file_location("inventory_material", SCRIPT)
INVENTORY = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(INVENTORY)


class InventoryMaterialTests(unittest.TestCase):
    def temporary_file(self, name, content, binary=False):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        path = Path(directory.name) / name
        if binary:
            path.write_bytes(content)
        else:
            path.write_text(content, encoding="utf-8")
        return path

    def test_markdown_text_is_preserved(self):
        source = self.temporary_file("brief.md", "# Spring fair\n\n60+ clubs")
        text, warnings = INVENTORY.extract(source)
        self.assertEqual(text, "# Spring fair\n\n60+ clubs")
        self.assertEqual(warnings, [])

    def test_docx_paragraphs_are_extracted_in_order(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        source = Path(directory.name) / "plan.docx"
        document = """<?xml version='1.0' encoding='UTF-8'?>
        <w:document xmlns:w='http://schemas.openxmlformats.org/wordprocessingml/2006/main'>
          <w:body>
            <w:p><w:r><w:t>Spring fair</w:t></w:r></w:p>
            <w:p><w:r><w:t>60+ clubs</w:t></w:r></w:p>
          </w:body>
        </w:document>"""
        with zipfile.ZipFile(source, "w") as archive:
            archive.writestr("word/document.xml", document)
        text, warnings = INVENTORY.extract(source)
        self.assertEqual(text, "Spring fair\n\n60+ clubs")
        self.assertEqual(warnings, [])

    def test_unsupported_material_fails_explicitly(self):
        source = self.temporary_file("brief.xyz", "opaque")
        text, warnings = INVENTORY.extract(source)
        self.assertEqual(text, "")
        self.assertEqual(warnings, ["Unsupported source type: .xyz"])

    def test_standalone_image_is_registered_for_visual_review(self):
        source = self.temporary_file("poster.png", b"not-a-real-image", binary=True)
        refs = INVENTORY.standalone_image_refs(source)
        self.assertEqual(refs[0]["name"], "poster.png")
        self.assertEqual(refs[0]["source"], str(source.resolve()))
        self.assertIn("inspect visually", refs[0]["description"])


if __name__ == "__main__":
    unittest.main()
