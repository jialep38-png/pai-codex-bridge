import tempfile
import unittest
from pathlib import Path

from Tools.codex_bridge_generator import generate_bridge_file


class CodexBridgeIntegrationTests(unittest.TestCase):
    def test_generate_bridge_file_success(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            release = root / "Releases" / "v4.0.1" / ".claude"
            template = root / "template.md"
            output = root / "proj" / "AGENTS.md"

            (release / "skills" / "Agents").mkdir(parents=True)
            (release / "skills" / "Thinking").mkdir(parents=True)
            latest = release / "PAI" / "Algorithm" / "LATEST"
            latest.parent.mkdir(parents=True)
            latest.write_text("v3.5.0\n", encoding="utf-8")

            template.write_text(
                "root={{PAI_ROOT}}\nversion={{ALGO_VERSION}}\n{{SKILL_CATEGORIES}}",
                encoding="utf-8",
            )

            generate_bridge_file(
                template_path=template,
                release_dir=release,
                output_path=output,
                project_root=root,
                force=False,
            )

            self.assertTrue(output.exists())
            content = output.read_text(encoding="utf-8")
            self.assertIn("version=v3.5.0", content)
            self.assertIn("- `Agents`", content)
            self.assertIn("- `Thinking`", content)

    def test_generate_bridge_file_respects_force_flag(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            release = root / "Releases" / "v4.0.1" / ".claude"
            template = root / "template.md"
            output = root / "AGENTS.md"

            (release / "skills" / "Agents").mkdir(parents=True)
            latest = release / "PAI" / "Algorithm" / "LATEST"
            latest.parent.mkdir(parents=True)
            latest.write_text("v3.5.0\n", encoding="utf-8")

            template.write_text("{{ALGO_VERSION}}", encoding="utf-8")
            output.write_text("existing", encoding="utf-8")

            with self.assertRaises(FileExistsError):
                generate_bridge_file(
                    template_path=template,
                    release_dir=release,
                    output_path=output,
                    project_root=root,
                    force=False,
                )


if __name__ == "__main__":
    unittest.main()
