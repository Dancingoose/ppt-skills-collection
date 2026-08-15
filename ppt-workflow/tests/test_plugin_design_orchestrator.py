import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SKILLS = ROOT / "codex-plugin" / "skills"
STUDIO = SKILLS / "ppt-workflow-studio" / "SKILL.md"


class PluginDesignOrchestratorTests(unittest.TestCase):
    expected = (
        "claude-design", "ui-ux-pro-max", "mbb-decks",
        "frontend-design", "axi-front-design",
    )

    def test_plugin_exposes_all_design_bridges(self):
        for skill in self.expected:
            self.assertTrue((SKILLS / skill / "SKILL.md").is_file())
            self.assertTrue((SKILLS / skill / "agents" / "openai.yaml").is_file())

    def test_studio_orders_every_design_bridge_before_samples(self):
        text = STUDIO.read_text(encoding="utf-8")
        positions = [text.index(name) for name in self.expected]
        self.assertEqual(positions, sorted(positions))
        self.assertLess(positions[-1], text.index("visual-direction-preview.html"))

    def test_studio_makes_missing_design_evidence_a_hard_stop(self):
        text = STUDIO.read_text(encoding="utf-8")
        self.assertIn("Do not continue if any required artifact or its SHA-256 binding is absent.", text)


if __name__ == "__main__":
    unittest.main()
