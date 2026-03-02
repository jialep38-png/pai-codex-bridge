import tempfile
import unittest
from pathlib import Path

from Tools.codex_bridge_generator import (
    build_replacements,
    discover_skill_categories,
    load_algorithm_version,
    render_skill_categories,
    render_template,
)


class CodexBridgeGeneratorUnitTests(unittest.TestCase):
    def test_discover_skill_categories_sorted(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            release = Path(tmp) / ".claude"
            skills = release / "skills"
            (skills / "Thinking").mkdir(parents=True)
            (skills / "agents").mkdir(parents=True)
            (skills / "Utilities").mkdir(parents=True)

            categories = discover_skill_categories(release)
            self.assertEqual(categories, ["agents", "Thinking", "Utilities"])

    def test_load_algorithm_version(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            release = Path(tmp) / ".claude"
            latest = release / "PAI" / "Algorithm" / "LATEST"
            latest.parent.mkdir(parents=True)
            latest.write_text("v3.6.0\n", encoding="utf-8")

            version = load_algorithm_version(release)
            self.assertEqual(version, "v3.6.0")

    def test_render_template_replaces_placeholders(self) -> None:
        template = "algo={{ALGO_VERSION}}\nskills=\n{{SKILL_CATEGORIES}}"
        rendered = render_template(
            template,
            {
                "ALGO_VERSION": "v3.5.0",
                "SKILL_CATEGORIES": render_skill_categories(["Agents", "Security"]),
            },
        )
        self.assertIn("algo=v3.5.0", rendered)
        self.assertIn("- `Agents`", rendered)
        self.assertIn("- `Security`", rendered)

    def test_build_replacements_contains_expected_keys(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            release = Path(tmp) / ".claude"
            data = build_replacements(
                release_dir=release,
                algorithm_version="v3.5.0",
                categories=["Agents"],
                project_root=Path(tmp),
            )
            self.assertIn("PAI_ROOT", data)
            self.assertIn("ALGO_FILE", data)
            self.assertIn("CONTEXT_ROUTING", data)
            self.assertEqual(data["ALGO_VERSION"], "v3.5.0")
            self.assertEqual(data["PAI_ROOT"], ".claude")


if __name__ == "__main__":
    unittest.main()
