import json
import os
import tempfile
import unittest
from pathlib import Path

from Tools.pai_codex_runtime import (
    HookExecutionResult,
    _collect_runtime_requirements,
    _execute_user_shell_command,
    _extract_hook_commands,
    _interpolate_env,
    _matcher_matches,
    _normalize_command,
    _should_block,
)


class PaiCodexRuntimeUnitTests(unittest.TestCase):
    def test_interpolate_env(self) -> None:
        text = "${PAI_DIR}/hooks/${EVENT}.ts"
        env = {"PAI_DIR": "/tmp/pai", "EVENT": "LoadContext"}
        self.assertEqual(_interpolate_env(text, env), "/tmp/pai/hooks/LoadContext.ts")

    def test_matcher_exact_glob_case_insensitive(self) -> None:
        self.assertTrue(_matcher_matches("Bash", {"tool_name": "Bash"}))
        self.assertTrue(_matcher_matches("BaSh", {"tool_name": "bash"}))
        self.assertTrue(_matcher_matches("B*", {"tool_name": "Bash"}))
        self.assertFalse(_matcher_matches("Read", {"tool_name": "Bash"}))

    def test_extract_hook_commands_with_matcher_filter(self) -> None:
        settings = {
            "hooks": {
                "PreToolUse": [
                    {
                        "matcher": "Bash",
                        "hooks": [{"type": "command", "command": "a.py", "timeout": 9}],
                    },
                    {
                        "matcher": "Read",
                        "hooks": [{"type": "command", "command": "b.py", "timeout": 9}],
                    },
                ]
            }
        }
        commands = _extract_hook_commands(settings, "PreToolUse", {"tool_name": "Bash"})
        self.assertEqual(len(commands), 1)
        self.assertEqual(commands[0].command, "a.py")

    def test_normalize_command_py_script_prefers_py_runner(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            script = Path(tmp) / "hook.py"
            script.write_text("print('ok')\n", encoding="utf-8")
            resolved = _normalize_command(str(script), {})
            self.assertTrue(resolved.lower().startswith("py "))

    def test_pretool_critical_failure_blocks(self) -> None:
        result = HookExecutionResult(
            event="PreToolUse",
            command="x",
            command_resolved="C:/x/SecurityValidator.hook.ts",
            matched=True,
            success=False,
            skipped=True,
            timed_out=False,
            exit_code=None,
            duration_ms=0,
            stdout="",
            stderr="missing runtime",
            decision=None,
            reason="bun-not-found",
        )
        reason = _should_block("PreToolUse", result)
        self.assertIn("bun-not-found", reason or "")

    def test_execute_user_shell_command(self) -> None:
        result = _execute_user_shell_command(
            command_text='py -c "print(123)"',
            cwd=Path(".").resolve(),
            env=dict(os.environ),
        )
        self.assertEqual(result["exit_code"], 0)
        self.assertIn("123", result["stdout"])

    def test_collect_runtime_requirements(self) -> None:
        settings = {
            "hooks": {
                "SessionStart": [
                    {
                        "hooks": [
                            {"type": "command", "command": "bun a.ts"},
                            {"type": "command", "command": "py b.py"},
                            {"type": "command", "command": "powershell.exe -c echo hi"},
                        ]
                    }
                ]
            }
        }
        req = _collect_runtime_requirements(settings)
        self.assertIn("bun", req)
        self.assertIn("py", req)
        self.assertIn("powershell", req)


if __name__ == "__main__":
    unittest.main()
