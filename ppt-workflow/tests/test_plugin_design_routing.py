import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SKILLS = ROOT / "codex-plugin" / "skills"
STUDIO = SKILLS / "ppt-workflow-studio" / "SKILL.md"


class PluginDesignRoutingTests(unittest.TestCase):
    bridges = {
        "claude-design": "design-assets/claude-design/SKILL.md",
        "ui-ux-pro-max": "design-assets/ui-ux-pro-max/SKILL.md",
        "mbb-decks": "design-assets/mbb-decks/SKILL.md",
        "frontend-design": "design-assets/frontend-design/SKILL.md",
        "axi-front-design": "axi-front-design/SKILL.md",
    }

    def test_plugin_exposes_the_canonical_design_bridges(self):
        for skill, authority in self.bridges.items():
            text = (SKILLS / skill / "SKILL.md").read_text(encoding="utf-8")
            self.assertTrue((SKILLS / skill / "agents" / "openai.yaml").is_file())
            self.assertIn(authority, text)

    def test_studio_delegates_to_the_aa6_canonical_architecture(self):
        text = STUDIO.read_text(encoding="utf-8")
        self.assertIn("Treat `ppt-workflow/SKILL.md` as the canonical four-layer architecture", text)
        self.assertIn("Do not replace this routing with a parallel `designOrchestration` or `designRecipes` state machine.", text)
        for skill in self.bridges:
            self.assertIn(skill, text)


if __name__ == "__main__":
    unittest.main()
