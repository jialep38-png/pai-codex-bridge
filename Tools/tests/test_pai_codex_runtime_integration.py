import json
import tempfile
import unittest
from pathlib import Path

from Tools.pai_codex_runtime import PaiCodexRuntime, main


class PaiCodexRuntimeIntegrationTests(unittest.TestCase):
    def _write_hook(self, path: Path, code: str) -> None:
        path.write_text(code, encoding="utf-8")

    def test_session_start_executes_python_hook(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            hooks_dir = root / "hooks"
            hooks_dir.mkdir(parents=True)

            marker = root / "session_start_marker.txt"
            hook = hooks_dir / "session_start_hook.py"
            self._write_hook(
                hook,
                (
                    "import json\n"
                    "import sys\n"
                    f"open(r'{marker.as_posix()}', 'w', encoding='utf-8').write(sys.stdin.read())\n"
                    "print('{\"decision\":\"allow\"}')\n"
                ),
            )

            settings = root / "settings.json"
            settings.write_text(
                json.dumps(
                    {
                        "hooks": {
                            "SessionStart": [
                                {
                                    "hooks": [
                                        {
                                            "type": "command",
                                            "command": str(hook),
                                            "timeout": 10,
                                        }
                                    ]
                                }
                            ]
                        }
                    }
                ),
                encoding="utf-8",
            )

            runtime = PaiCodexRuntime(settings_path=settings, pai_dir=root)
            payload = {"session_id": "s1", "hook_event_name": "SessionStart"}
            result = runtime.run_event("SessionStart", payload, project_root=root)

            self.assertFalse(result.blocked)
            self.assertEqual(result.executed_count, 1)
            self.assertTrue(marker.exists())
            saved = marker.read_text(encoding="utf-8")
            self.assertIn('"session_id": "s1"', saved)

    def test_pre_tool_deny_decision_blocks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            hooks_dir = root / "hooks"
            hooks_dir.mkdir(parents=True)

            deny_hook = hooks_dir / "deny_hook.py"
            self._write_hook(
                deny_hook,
                "print('{\"decision\":\"deny\",\"reason\":\"security policy\"}')\n",
            )

            settings = root / "settings.json"
            settings.write_text(
                json.dumps(
                    {
                        "hooks": {
                            "PreToolUse": [
                                {
                                    "matcher": "Bash",
                                    "hooks": [
                                        {
                                            "type": "command",
                                            "command": str(deny_hook),
                                            "timeout": 10,
                                        }
                                    ],
                                }
                            ]
                        }
                    }
                ),
                encoding="utf-8",
            )

            runtime = PaiCodexRuntime(settings_path=settings, pai_dir=root)
            payload = {
                "session_id": "s2",
                "hook_event_name": "PreToolUse",
                "tool_name": "Bash",
                "tool_input": {"command": "rm -rf /"},
            }
            result = runtime.run_event("PreToolUse", payload, project_root=root)

            self.assertTrue(result.blocked)
            self.assertIn("security policy", result.block_reason or "")
            self.assertEqual(result.executed_count, 1)

    def test_pre_tool_matcher_skips_non_matching_hook(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            hooks_dir = root / "hooks"
            hooks_dir.mkdir(parents=True)

            hook = hooks_dir / "hook.py"
            self._write_hook(hook, "print('ok')\n")

            settings = root / "settings.json"
            settings.write_text(
                json.dumps(
                    {
                        "hooks": {
                            "PreToolUse": [
                                {
                                    "matcher": "Read",
                                    "hooks": [
                                        {
                                            "type": "command",
                                            "command": str(hook),
                                            "timeout": 10,
                                        }
                                    ],
                                }
                            ]
                        }
                    }
                ),
                encoding="utf-8",
            )

            runtime = PaiCodexRuntime(settings_path=settings, pai_dir=root)
            payload = {
                "session_id": "s3",
                "hook_event_name": "PreToolUse",
                "tool_name": "Bash",
                "tool_input": {"command": "echo hi"},
            }
            result = runtime.run_event("PreToolUse", payload, project_root=root)

            self.assertFalse(result.blocked)
            self.assertEqual(result.executed_count, 0)
            self.assertEqual(result.hook_count, 0)

    def test_run_bash_triggers_pre_and_post_tool(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            hooks_dir = root / "hooks"
            hooks_dir.mkdir(parents=True)

            pre_marker = root / "pre.txt"
            post_marker = root / "post.txt"

            pre_hook = hooks_dir / "pre.py"
            post_hook = hooks_dir / "post.py"
            self._write_hook(
                pre_hook,
                (
                    "import sys\n"
                    f"open(r'{pre_marker.as_posix()}', 'w', encoding='utf-8').write(sys.stdin.read())\n"
                    "print('{\"decision\":\"allow\"}')\n"
                ),
            )
            self._write_hook(
                post_hook,
                (
                    "import sys\n"
                    f"open(r'{post_marker.as_posix()}', 'w', encoding='utf-8').write(sys.stdin.read())\n"
                    "print('{\"decision\":\"allow\"}')\n"
                ),
            )

            settings = root / "settings.json"
            settings.write_text(
                json.dumps(
                    {
                        "hooks": {
                            "PreToolUse": [
                                {
                                    "matcher": "Bash",
                                    "hooks": [{"type": "command", "command": str(pre_hook), "timeout": 10}],
                                }
                            ],
                            "PostToolUse": [
                                {
                                    "matcher": "Bash",
                                    "hooks": [{"type": "command", "command": str(post_hook), "timeout": 10}],
                                }
                            ],
                        }
                    }
                ),
                encoding="utf-8",
            )

            code = main(
                [
                    "--settings",
                    str(settings),
                    "--pai-dir",
                    str(root),
                    "--project-root",
                    str(root),
                    "run-bash",
                    "--command-text",
                    'py -c "print(42)"',
                ]
            )

            self.assertEqual(code, 0)
            self.assertTrue(pre_marker.exists())
            self.assertTrue(post_marker.exists())

    def test_launch_codex_triggers_session_start_and_end(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            hooks_dir = root / "hooks"
            hooks_dir.mkdir(parents=True)

            start_marker = root / "start.txt"
            end_marker = root / "end.txt"

            start_hook = hooks_dir / "start.py"
            end_hook = hooks_dir / "end.py"
            self._write_hook(
                start_hook,
                (
                    "import sys\n"
                    f"open(r'{start_marker.as_posix()}', 'w', encoding='utf-8').write(sys.stdin.read())\n"
                    "print('{\"decision\":\"allow\"}')\n"
                ),
            )
            self._write_hook(
                end_hook,
                (
                    "import sys\n"
                    f"open(r'{end_marker.as_posix()}', 'w', encoding='utf-8').write(sys.stdin.read())\n"
                    "print('{\"decision\":\"allow\"}')\n"
                ),
            )

            settings = root / "settings.json"
            settings.write_text(
                json.dumps(
                    {
                        "hooks": {
                            "SessionStart": [{"hooks": [{"type": "command", "command": str(start_hook), "timeout": 10}]}],
                            "SessionEnd": [{"hooks": [{"type": "command", "command": str(end_hook), "timeout": 10}]}],
                        }
                    }
                ),
                encoding="utf-8",
            )

            code = main(
                [
                    "--settings",
                    str(settings),
                    "--pai-dir",
                    str(root),
                    "--project-root",
                    str(root),
                    "launch-codex",
                    "--skip-ensure-agents",
                    "--codex-bin",
                    "py",
                    "--",
                    "-c",
                    "print('codex-mock')",
                ]
            )

            self.assertEqual(code, 0)
            self.assertTrue(start_marker.exists())
            self.assertTrue(end_marker.exists())

    def test_doctor_with_python_only_requirement(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            hooks_dir = root / "hooks"
            hooks_dir.mkdir(parents=True)
            hook = hooks_dir / "h.py"
            self._write_hook(hook, "print('ok')\n")

            settings = root / "settings.json"
            settings.write_text(
                json.dumps(
                    {
                        "hooks": {
                            "SessionStart": [{"hooks": [{"type": "command", "command": str(hook), "timeout": 10}]}]
                        }
                    }
                ),
                encoding="utf-8",
            )

            code = main(
                [
                    "--settings",
                    str(settings),
                    "--pai-dir",
                    str(root),
                    "doctor",
                    "--codex-bin",
                    "py",
                ]
            )
            self.assertEqual(code, 0)


if __name__ == "__main__":
    unittest.main()
