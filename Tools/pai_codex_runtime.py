#!/usr/bin/env python3
"""PAI Codex Runtime。

目标：在 Codex 中模拟 Claude Hook 生命周期，尽可能复用 PAI 既有 hooks。
"""

from __future__ import annotations

import argparse
import fnmatch
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import time
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


ENV_PATTERN = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}")


@dataclass
class HookCommand:
    event: str
    matcher: Optional[str]
    command: str
    timeout: int
    hook_type: str


@dataclass
class HookExecutionResult:
    event: str
    command: str
    command_resolved: str
    matched: bool
    success: bool
    skipped: bool
    timed_out: bool
    exit_code: Optional[int]
    duration_ms: int
    stdout: str
    stderr: str
    decision: Optional[str]
    reason: Optional[str]


@dataclass
class RuntimeEventResult:
    event: str
    session_id: str
    hook_count: int
    executed_count: int
    blocked: bool
    block_reason: Optional[str]
    results: List[HookExecutionResult]


class RuntimeConfigError(RuntimeError):
    """运行时配置错误。"""


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _configure_stdio() -> None:
    for stream_name in ("stdout", "stderr"):
        stream = getattr(sys, stream_name, None)
        if stream is None:
            continue
        reconfig = getattr(stream, "reconfigure", None)
        if callable(reconfig):
            try:
                reconfig(encoding="utf-8", errors="replace")
            except Exception:
                pass


def _repo_root(script_file: Path) -> Path:
    return script_file.resolve().parents[1]


def _default_settings_path() -> Path:
    root = _repo_root(Path(__file__))
    return root / "Releases" / "v4.0.1" / ".claude" / "settings.json"


def _load_settings(settings_path: Path) -> Dict[str, Any]:
    if not settings_path.exists():
        raise RuntimeConfigError(f"settings.json 不存在: {settings_path}")

    try:
        return json.loads(settings_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise RuntimeConfigError(f"settings.json JSON 解析失败: {exc}") from exc


def _interpolate_env(text: str, env: Dict[str, str]) -> str:
    def replace(match: re.Match[str]) -> str:
        key = match.group(1)
        return env.get(key, match.group(0))

    return ENV_PATTERN.sub(replace, text)


def _first_token(command: str) -> Optional[str]:
    try:
        tokens = shlex.split(command, posix=False)
    except ValueError:
        return None
    return tokens[0] if tokens else None


def _has_runtime(name: str, env: Dict[str, str]) -> bool:
    if shutil.which(name):
        return True
    if name == "bun" and _bun_bin_path() is not None:
        return True
    env_path = env.get("PATH", "")
    for base in env_path.split(os.pathsep):
        if not base:
            continue
        if os.name == "nt":
            candidate = Path(base) / f"{name}.exe"
            candidate_cmd = Path(base) / f"{name}.cmd"
            if candidate.exists() or candidate_cmd.exists():
                return True
        else:
            candidate = Path(base) / name
            if candidate.exists():
                return True
    return False


def _normalize_command(command: str, env: Dict[str, str]) -> str:
    resolved = _interpolate_env(command, env).strip()
    if not resolved:
        return resolved

    token = _first_token(resolved)
    if not token:
        return resolved

    lower_token = token.lower()
    has_runner = lower_token in {
        "bun",
        "node",
        "py",
        "python",
        "python3",
        "bash",
        "sh",
        "powershell",
        "powershell.exe",
        "pwsh",
        "cmd",
        "cmd.exe",
    }
    if has_runner:
        return resolved

    if lower_token.endswith((".ts", ".tsx", ".js", ".mjs", ".cjs")):
        if _has_runtime("bun", env):
            return f'bun "{token}"{resolved[len(token):]}'
        if _has_runtime("node", env) and lower_token.endswith((".js", ".mjs", ".cjs")):
            return f'node "{token}"{resolved[len(token):]}'
        return resolved

    if lower_token.endswith(".py"):
        return f'py "{token}"{resolved[len(token):]}'

    if lower_token.endswith(".sh") and _has_runtime("bash", env):
        return f'bash "{token}"{resolved[len(token):]}'

    return resolved


def _matcher_matches(matcher: Optional[str], payload: Dict[str, Any]) -> bool:
    if not matcher:
        return True

    tool_name = str(payload.get("tool_name", ""))
    if not tool_name:
        return False

    if matcher == tool_name:
        return True

    if fnmatch.fnmatchcase(tool_name, matcher):
        return True

    if matcher.lower() == tool_name.lower():
        return True

    return False


def _extract_hook_commands(settings: Dict[str, Any], event: str, payload: Dict[str, Any]) -> List[HookCommand]:
    hooks_root = settings.get("hooks", {})
    event_blocks = hooks_root.get(event, [])
    result: List[HookCommand] = []

    if not isinstance(event_blocks, list):
        return result

    for block in event_blocks:
        if not isinstance(block, dict):
            continue

        matcher = block.get("matcher")
        if not _matcher_matches(matcher, payload):
            continue

        hooks = block.get("hooks", [])
        if not isinstance(hooks, list):
            continue

        for hook in hooks:
            if not isinstance(hook, dict):
                continue
            if hook.get("type") != "command":
                continue

            command = str(hook.get("command", "")).strip()
            if not command:
                continue

            timeout = int(hook.get("timeout", 30))
            result.append(
                HookCommand(
                    event=event,
                    matcher=matcher,
                    command=command,
                    timeout=timeout,
                    hook_type="command",
                )
            )

    return result


def _parse_json_candidate(text: str) -> Optional[Dict[str, Any]]:
    stripped = text.strip()
    if not stripped:
        return None

    # 优先尝试整体 JSON
    try:
        data = json.loads(stripped)
        if isinstance(data, dict):
            return data
    except json.JSONDecodeError:
        pass

    # 再尝试按行从后往前解析 JSON 对象
    for line in reversed([ln.strip() for ln in stripped.splitlines() if ln.strip()]):
        if not (line.startswith("{") and line.endswith("}")):
            continue
        try:
            data = json.loads(line)
            if isinstance(data, dict):
                return data
        except json.JSONDecodeError:
            continue

    return None


def _is_critical_pretool_hook(command_text: str) -> bool:
    markers = ("SecurityValidator", "AgentExecutionGuard", "SkillGuard")
    return any(marker.lower() in command_text.lower() for marker in markers)


def _requires_missing_runtime(command_resolved: str, env: Dict[str, str]) -> Optional[str]:
    token = _first_token(command_resolved)
    if not token:
        return None

    lower = token.lower()
    if lower.endswith((".ts", ".tsx")) and not _has_runtime("bun", env):
        return "bun-not-found"
    if lower.endswith((".js", ".mjs", ".cjs")) and not (_has_runtime("bun", env) or _has_runtime("node", env)):
        return "node-or-bun-not-found"
    if lower.endswith(".sh") and not _has_runtime("bash", env):
        return "bash-not-found"
    return None


def _execute_hook_command(
    hook: HookCommand,
    payload: Dict[str, Any],
    env: Dict[str, str],
) -> HookExecutionResult:
    resolved_command = _normalize_command(hook.command, env)
    stdin_text = json.dumps(payload, ensure_ascii=False)

    if not resolved_command:
        return HookExecutionResult(
            event=hook.event,
            command=hook.command,
            command_resolved=resolved_command,
            matched=True,
            success=False,
            skipped=True,
            timed_out=False,
            exit_code=None,
            duration_ms=0,
            stdout="",
            stderr="空命令，已跳过。",
            decision=None,
            reason="empty-command",
        )

    missing_runtime = _requires_missing_runtime(resolved_command, env)
    if missing_runtime:
        return HookExecutionResult(
            event=hook.event,
            command=hook.command,
            command_resolved=resolved_command,
            matched=True,
            success=False,
            skipped=True,
            timed_out=False,
            exit_code=None,
            duration_ms=0,
            stdout="",
            stderr=f"缺少运行时依赖: {missing_runtime}",
            decision="deny" if (hook.event == "PreToolUse" and _is_critical_pretool_hook(resolved_command)) else None,
            reason=missing_runtime,
        )

    start = time.perf_counter()

    try:
        proc = subprocess.run(
            resolved_command,
            input=stdin_text,
            text=True,
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            timeout=hook.timeout,
            shell=True,
            env=env,
        )
        duration_ms = int((time.perf_counter() - start) * 1000)
        parsed = _parse_json_candidate(proc.stdout)
        decision = parsed.get("decision") if parsed else None
        reason = parsed.get("reason") if parsed else None
        success = proc.returncode == 0

        return HookExecutionResult(
            event=hook.event,
            command=hook.command,
            command_resolved=resolved_command,
            matched=True,
            success=success,
            skipped=False,
            timed_out=False,
            exit_code=proc.returncode,
            duration_ms=duration_ms,
            stdout=proc.stdout,
            stderr=proc.stderr,
            decision=str(decision) if decision is not None else None,
            reason=str(reason) if reason is not None else None,
        )
    except subprocess.TimeoutExpired as exc:
        duration_ms = int((time.perf_counter() - start) * 1000)
        return HookExecutionResult(
            event=hook.event,
            command=hook.command,
            command_resolved=resolved_command,
            matched=True,
            success=False,
            skipped=False,
            timed_out=True,
            exit_code=None,
            duration_ms=duration_ms,
            stdout=exc.stdout or "",
            stderr=exc.stderr or f"执行超时（>{hook.timeout}s）",
            decision="deny" if hook.event == "PreToolUse" else None,
            reason="timeout",
        )


def _should_block(event: str, result: HookExecutionResult) -> Optional[str]:
    if event != "PreToolUse":
        return None

    if result.timed_out:
        if _is_critical_pretool_hook(result.command_resolved):
            return f"关键 hook 超时: {result.command}"
        return None

    if result.exit_code == 2:
        return result.reason or f"hook 阻断（exit=2）: {result.command}"

    if result.decision and result.decision.lower() in {"deny", "block", "blocked"}:
        return result.reason or f"hook 决策阻断: {result.command}"

    if (not result.success) and _is_critical_pretool_hook(result.command_resolved):
        return result.reason or f"关键 hook 执行失败: {result.command}"

    return None


class PaiCodexRuntime:
    """PAI Codex 运行时。"""

    def __init__(self, settings_path: Path, pai_dir: Optional[Path] = None) -> None:
        self.settings_path = settings_path.resolve()
        self.settings = _load_settings(self.settings_path)
        self.pai_dir = pai_dir.resolve() if pai_dir else self.settings_path.parent.resolve()

    def _build_env(self, project_root: Optional[Path] = None) -> Dict[str, str]:
        env = dict(os.environ)
        env.setdefault("HOME", str(Path.home()))
        env["PAI_DIR"] = str(self.pai_dir)
        bun_bin = _bun_bin_path()
        if bun_bin:
            bun_dir = str(bun_bin.parent)
            current_path = env.get("PATH", "")
            path_items = current_path.split(os.pathsep) if current_path else []
            if bun_dir not in path_items:
                env["PATH"] = bun_dir + os.pathsep + current_path
        if project_root:
            env["PROJECT_ROOT"] = str(project_root.resolve())
        return env

    def run_event(
        self,
        event: str,
        payload: Dict[str, Any],
        project_root: Optional[Path] = None,
    ) -> RuntimeEventResult:
        commands = _extract_hook_commands(self.settings, event, payload)
        env = self._build_env(project_root)

        results: List[HookExecutionResult] = []
        blocked = False
        block_reason: Optional[str] = None

        for command in commands:
            result = _execute_hook_command(command, payload, env)
            results.append(result)

            reason = _should_block(event, result)
            if reason and not blocked:
                blocked = True
                block_reason = reason

        return RuntimeEventResult(
            event=event,
            session_id=str(payload.get("session_id", "")),
            hook_count=len(commands),
            executed_count=len(results),
            blocked=blocked,
            block_reason=block_reason,
            results=results,
        )


def _build_payload(args: argparse.Namespace, event: str) -> Dict[str, Any]:
    payload: Dict[str, Any] = {
        "session_id": args.session_id or str(uuid.uuid4()),
        "hook_event_name": event,
        "timestamp": _now_iso(),
    }

    if args.transcript_path:
        payload["transcript_path"] = args.transcript_path

    if event in {"PreToolUse", "PostToolUse"}:
        payload["tool_name"] = args.tool_name
        payload["tool_input"] = json.loads(args.tool_input_json or "{}")

    if event == "UserPromptSubmit":
        payload["prompt"] = args.prompt or ""

    if args.payload_json:
        payload.update(json.loads(args.payload_json))

    if args.payload_file:
        file_payload = json.loads(Path(args.payload_file).read_text(encoding="utf-8"))
        if isinstance(file_payload, dict):
            payload.update(file_payload)

    return payload


def _print_result(result: RuntimeEventResult, as_json: bool) -> int:
    if as_json:
        print(json.dumps(asdict(result), ensure_ascii=False, indent=2))
    else:
        print(f"[pai-codex-runtime] event={result.event} hooks={result.hook_count} executed={result.executed_count}")
        if result.blocked:
            print(f"[pai-codex-runtime] BLOCKED: {result.block_reason}")
        for item in result.results:
            status = "OK" if item.success else "FAIL"
            if item.skipped:
                status = "SKIP"
            if item.timed_out:
                status = "TIMEOUT"
            print(f"  - [{status}] {item.command_resolved} ({item.duration_ms}ms)")
            stderr_text = (item.stderr or "").strip()
            if stderr_text:
                print(f"    stderr: {stderr_text}")

    return 2 if result.blocked else 0


def _execute_user_shell_command(command_text: str, cwd: Path, env: Dict[str, str]) -> Dict[str, Any]:
    start = time.perf_counter()
    proc = subprocess.run(
        command_text,
        shell=True,
        text=True,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        cwd=str(cwd),
        env=env,
    )
    duration_ms = int((time.perf_counter() - start) * 1000)
    return {
        "command": command_text,
        "cwd": str(cwd),
        "exit_code": proc.returncode,
        "duration_ms": duration_ms,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
    }


def _sanitize_remainder_args(args: List[str]) -> List[str]:
    if args and args[0] == "--":
        return args[1:]
    return args


def _run_passthrough_process(command: List[str], cwd: Path, env: Dict[str, str]) -> int:
    proc = subprocess.run(
        command,
        cwd=str(cwd),
        env=env,
        check=False,
    )
    return int(proc.returncode)


def _bun_bin_path() -> Optional[Path]:
    home = Path.home()
    candidates = [
        home / ".bun" / "bin" / "bun.exe",
        home / ".bun" / "bin" / "bun",
    ]
    for item in candidates:
        if item.exists():
            return item
    return None


def _runtime_available(name: str) -> bool:
    if shutil.which(name):
        return True
    if name == "bun":
        return _bun_bin_path() is not None
    return False


def _resolve_executable(bin_name: str) -> Optional[str]:
    resolved = shutil.which(bin_name)
    if resolved:
        return resolved
    return None


def _ensure_project_agents(
    repo_root: Path,
    project_root: Path,
    output_name: str,
    release_dir: Path,
    force: bool,
) -> Optional[str]:
    template_path = repo_root / "Codex" / "templates" / "AGENTS.pai-codex.template.md"
    output_path = project_root / output_name

    if output_path.exists() and not force:
        return None

    try:
        from Tools.codex_bridge_generator import generate_bridge_file
    except Exception as exc:  # noqa: BLE001
        return f"无法加载桥接生成器: {exc}"

    try:
        generate_bridge_file(
            template_path=template_path,
            release_dir=release_dir,
            output_path=output_path,
            project_root=project_root,
            force=force,
        )
        return None
    except Exception as exc:  # noqa: BLE001
        return f"生成 AGENTS 失败: {exc}"


def _collect_runtime_requirements(settings: Dict[str, Any]) -> List[str]:
    required: set[str] = set()
    hooks_root = settings.get("hooks", {})
    if not isinstance(hooks_root, dict):
        return []

    for event_blocks in hooks_root.values():
        if not isinstance(event_blocks, list):
            continue
        for block in event_blocks:
            if not isinstance(block, dict):
                continue
            hooks = block.get("hooks", [])
            if not isinstance(hooks, list):
                continue
            for hook in hooks:
                if not isinstance(hook, dict):
                    continue
                cmd = str(hook.get("command", "")).strip()
                if not cmd:
                    continue
                token = _first_token(cmd) or ""
                lower = token.lower()
                if lower in {"bun"} or lower.endswith((".ts", ".tsx")):
                    required.add("bun")
                elif lower in {"node"} or lower.endswith((".js", ".mjs", ".cjs")):
                    required.add("node")
                elif lower in {"bash", "sh"} or lower.endswith(".sh"):
                    required.add("bash")
                elif lower in {"py", "python", "python3"} or lower.endswith(".py"):
                    required.add("py")
                elif lower.startswith("powershell"):
                    required.add("powershell")

    return sorted(required)


def _common_parser(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--session-id", help="会话 ID（默认自动生成）")
    parser.add_argument("--transcript-path", help="可选 transcript 路径")
    parser.add_argument("--payload-json", help="附加 payload JSON 字符串")
    parser.add_argument("--payload-file", help="附加 payload JSON 文件")
    parser.add_argument("--json", action="store_true", help="JSON 输出")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="PAI Codex Runtime")
    parser.add_argument(
        "--settings",
        default=str(_default_settings_path().as_posix()),
        help="settings.json 路径",
    )
    parser.add_argument("--pai-dir", help="PAI 根目录（默认 settings.json 所在目录）")
    parser.add_argument("--project-root", default=".", help="项目根目录（注入 PROJECT_ROOT 环境变量）")
    subparsers = parser.add_subparsers(dest="command", required=True)

    p_start = subparsers.add_parser("session-start", help="触发 SessionStart")
    _common_parser(p_start)

    p_end = subparsers.add_parser("session-end", help="触发 SessionEnd")
    _common_parser(p_end)

    p_stop = subparsers.add_parser("stop", help="触发 Stop")
    _common_parser(p_stop)

    p_prompt = subparsers.add_parser("user-prompt", help="触发 UserPromptSubmit")
    _common_parser(p_prompt)
    p_prompt.add_argument("--prompt", default="", help="用户输入")

    p_pre = subparsers.add_parser("pre-tool", help="触发 PreToolUse")
    _common_parser(p_pre)
    p_pre.add_argument("--tool-name", required=True, help="工具名")
    p_pre.add_argument("--tool-input-json", default="{}", help="工具输入 JSON")

    p_post = subparsers.add_parser("post-tool", help="触发 PostToolUse")
    _common_parser(p_post)
    p_post.add_argument("--tool-name", required=True, help="工具名")
    p_post.add_argument("--tool-input-json", default="{}", help="工具输入 JSON")

    p_run = subparsers.add_parser("run-bash", help="执行 Bash 命令并自动触发 pre/post-tool")
    _common_parser(p_run)
    p_run.add_argument("--command-text", required=True, help="要执行的命令文本")
    p_run.add_argument("--cwd", default=".", help="命令执行目录")

    p_launch = subparsers.add_parser("launch-codex", help="启动 Codex 并自动触发生命周期事件")
    _common_parser(p_launch)
    p_launch.add_argument("--codex-bin", default="codex", help="Codex 可执行程序名")
    p_launch.add_argument("--skip-ensure-agents", action="store_true", help="不自动生成项目 AGENTS.md")
    p_launch.add_argument("--agents-output", default="AGENTS.md", help="AGENTS 输出文件名")
    p_launch.add_argument("--force-agents", action="store_true", help="覆盖已有 AGENTS 文件")
    p_launch.add_argument("codex_args", nargs=argparse.REMAINDER, help="透传给 codex 的参数，建议以 -- 分隔")

    p_doctor = subparsers.add_parser("doctor", help="检查 Codex + PAI Runtime 依赖")
    _common_parser(p_doctor)
    p_doctor.add_argument("--codex-bin", default="codex", help="Codex 可执行程序名")

    return parser


def _command_to_event(command: str) -> str:
    mapping = {
        "session-start": "SessionStart",
        "session-end": "SessionEnd",
        "stop": "Stop",
        "user-prompt": "UserPromptSubmit",
        "pre-tool": "PreToolUse",
        "post-tool": "PostToolUse",
    }
    return mapping[command]


def main(argv: Optional[List[str]] = None) -> int:
    _configure_stdio()
    parser = build_parser()
    args = parser.parse_args(argv)

    settings_path = Path(args.settings).resolve()
    pai_dir = Path(args.pai_dir).resolve() if args.pai_dir else None
    project_root = Path(args.project_root).resolve()

    try:
        runtime = PaiCodexRuntime(settings_path=settings_path, pai_dir=pai_dir)

        if args.command == "run-bash":
            session_id = args.session_id or str(uuid.uuid4())
            pre_payload = {
                "session_id": session_id,
                "hook_event_name": "PreToolUse",
                "timestamp": _now_iso(),
                "tool_name": "Bash",
                "tool_input": {"command": args.command_text},
            }
            pre_result = runtime.run_event("PreToolUse", pre_payload, project_root=project_root)

            if pre_result.blocked:
                if args.json:
                    print(json.dumps({"pre_tool": asdict(pre_result), "blocked": True}, ensure_ascii=False, indent=2))
                else:
                    _print_result(pre_result, as_json=False)
                return 2

            env = runtime._build_env(project_root)  # noqa: SLF001
            command_result = _execute_user_shell_command(
                command_text=args.command_text,
                cwd=Path(args.cwd).resolve(),
                env=env,
            )

            post_payload = {
                "session_id": session_id,
                "hook_event_name": "PostToolUse",
                "timestamp": _now_iso(),
                "tool_name": "Bash",
                "tool_input": {
                    "command": args.command_text,
                    "exit_code": command_result["exit_code"],
                },
            }
            post_result = runtime.run_event("PostToolUse", post_payload, project_root=project_root)

            if args.json:
                print(
                    json.dumps(
                        {
                            "blocked": False,
                            "pre_tool": asdict(pre_result),
                            "command": command_result,
                            "post_tool": asdict(post_result),
                        },
                        ensure_ascii=False,
                        indent=2,
                    )
                )
            else:
                _print_result(pre_result, as_json=False)
                print(
                    f"[pai-codex-runtime] run-bash exit={command_result['exit_code']} "
                    f"duration={command_result['duration_ms']}ms"
                )
                if command_result["stdout"].strip():
                    print(command_result["stdout"].rstrip())
                if command_result["stderr"].strip():
                    print(command_result["stderr"].rstrip(), file=sys.stderr)
                _print_result(post_result, as_json=False)

            return int(command_result["exit_code"])

        if args.command == "launch-codex":
            repo_root = _repo_root(Path(__file__))
            session_id = args.session_id or str(uuid.uuid4())

            if not args.skip_ensure_agents:
                agents_error = _ensure_project_agents(
                    repo_root=repo_root,
                    project_root=project_root,
                    output_name=args.agents_output,
                    release_dir=runtime.pai_dir,
                    force=bool(args.force_agents),
                )
                if agents_error:
                    print(f"[pai-codex-runtime] {agents_error}", file=sys.stderr)

            start_payload = {
                "session_id": session_id,
                "hook_event_name": "SessionStart",
                "timestamp": _now_iso(),
            }
            start_result = runtime.run_event("SessionStart", start_payload, project_root=project_root)

            codex_args = _sanitize_remainder_args(list(args.codex_args or []))
            resolved_codex = _resolve_executable(args.codex_bin) or args.codex_bin
            launch_cmd = [resolved_codex, *codex_args]

            if not args.json:
                print(f"[pai-codex-runtime] launching: {' '.join(launch_cmd)}")

            env = runtime._build_env(project_root)  # noqa: SLF001
            try:
                codex_exit = _run_passthrough_process(launch_cmd, project_root, env)
            except FileNotFoundError:
                codex_exit = 127
                if not args.json:
                    print(f"[pai-codex-runtime] codex 可执行程序不存在: {args.codex_bin}", file=sys.stderr)

            stop_payload = {
                "session_id": session_id,
                "hook_event_name": "Stop",
                "timestamp": _now_iso(),
                "codex_exit_code": codex_exit,
            }
            stop_result = runtime.run_event("Stop", stop_payload, project_root=project_root)

            end_payload = {
                "session_id": session_id,
                "hook_event_name": "SessionEnd",
                "timestamp": _now_iso(),
                "codex_exit_code": codex_exit,
            }
            end_result = runtime.run_event("SessionEnd", end_payload, project_root=project_root)

            if args.json:
                print(
                    json.dumps(
                        {
                            "session_id": session_id,
                            "codex_exit_code": codex_exit,
                            "session_start": asdict(start_result),
                            "stop": asdict(stop_result),
                            "session_end": asdict(end_result),
                        },
                        ensure_ascii=False,
                        indent=2,
                    )
                )
            else:
                _print_result(start_result, as_json=False)
                _print_result(stop_result, as_json=False)
                _print_result(end_result, as_json=False)
                print(f"[pai-codex-runtime] codex exited with code {codex_exit}")

            return codex_exit

        if args.command == "doctor":
            requirements = _collect_runtime_requirements(runtime.settings)
            availability = {name: _runtime_available(name) for name in requirements}
            availability["codex"] = _runtime_available(args.codex_bin)

            missing = [k for k, v in availability.items() if not v]
            report = {
                "settings": str(runtime.settings_path),
                "pai_dir": str(runtime.pai_dir),
                "required_runtimes": requirements,
                "availability": availability,
                "missing": missing,
            }
            if args.json:
                print(json.dumps(report, ensure_ascii=False, indent=2))
            else:
                print(f"[pai-codex-runtime] settings={runtime.settings_path}")
                print(f"[pai-codex-runtime] pai_dir={runtime.pai_dir}")
                print(f"[pai-codex-runtime] required={', '.join(requirements) if requirements else 'none'}")
                for key, val in availability.items():
                    print(f"  - {key}: {'OK' if val else 'MISSING'}")
                if missing:
                    print(f"[pai-codex-runtime] 缺失依赖: {', '.join(missing)}", file=sys.stderr)
            return 0 if not missing else 1

        event = _command_to_event(args.command)
        payload = _build_payload(args, event)
        result = runtime.run_event(event=event, payload=payload, project_root=project_root)
        return _print_result(result, as_json=args.json)
    except Exception as exc:  # noqa: BLE001
        print(f"[pai-codex-runtime] 执行失败: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
