#!/usr/bin/env python3
"""PAI Codex 桥接文件生成器。

用途：从指定 PAI 发布目录提取算法版本与技能分类，生成 Codex 可用的 AGENTS 指令文件。
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Dict, List


def detect_repo_root(script_file: Path) -> Path:
    """根据脚本位置推断仓库根目录。"""
    return script_file.resolve().parents[1]


def discover_skill_categories(release_dir: Path) -> List[str]:
    """读取 skills 目录下的一级分类。"""
    skills_dir = release_dir / "skills"
    if not skills_dir.exists():
        raise FileNotFoundError(f"未找到 skills 目录: {skills_dir}")

    categories = [d.name for d in skills_dir.iterdir() if d.is_dir()]
    categories.sort(key=str.lower)
    return categories


def load_algorithm_version(release_dir: Path) -> str:
    """读取 PAI 算法最新版本号。"""
    latest_file = release_dir / "PAI" / "Algorithm" / "LATEST"
    if not latest_file.exists():
        raise FileNotFoundError(f"未找到算法版本文件: {latest_file}")

    version = latest_file.read_text(encoding="utf-8").strip()
    if not version:
        raise ValueError(f"算法版本文件为空: {latest_file}")
    return version


def render_skill_categories(categories: List[str]) -> str:
    """渲染技能分类列表。"""
    if not categories:
        return "- （未检测到技能分类）"
    return "\n".join(f"- `{name}`" for name in categories)


def _to_posix_path(path: Path) -> str:
    """统一路径展示格式。"""
    return path.as_posix()


def _render_reference_path(project_root: Path, target: Path) -> str:
    """优先输出相对路径，无法相对化时退回绝对路径。"""
    project_root_resolved = project_root.resolve()
    target_resolved = target.resolve()

    try:
        relative = target_resolved.relative_to(project_root_resolved)
        return _to_posix_path(relative)
    except ValueError:
        return _to_posix_path(target_resolved)


def build_replacements(
    release_dir: Path,
    algorithm_version: str,
    categories: List[str],
    project_root: Path,
) -> Dict[str, str]:
    """构造模板替换字典。"""
    release_root = _render_reference_path(project_root, release_dir)
    return {
        "PAI_ROOT": release_root,
        "ALGO_VERSION": algorithm_version,
        "ALGO_FILE": f"{release_root}/PAI/Algorithm/{algorithm_version}.md",
        "CONTEXT_ROUTING": f"{release_root}/PAI/CONTEXT_ROUTING.md",
        "PAI_README": f"{release_root}/PAI/README.md",
        "SKILL_CATEGORIES": render_skill_categories(categories),
    }


def render_template(template_text: str, replacements: Dict[str, str]) -> str:
    """执行模板渲染。"""
    rendered = template_text
    for key, value in replacements.items():
        rendered = rendered.replace(f"{{{{{key}}}}}", value)
    return rendered


def generate_bridge_file(
    template_path: Path,
    release_dir: Path,
    output_path: Path,
    project_root: Path,
    force: bool = False,
) -> None:
    """生成 Codex 兼容 AGENTS 文件。"""
    if not template_path.exists():
        raise FileNotFoundError(f"模板文件不存在: {template_path}")

    if output_path.exists() and not force:
        raise FileExistsError(f"输出文件已存在（使用 --force 覆盖）: {output_path}")

    algorithm_version = load_algorithm_version(release_dir)
    categories = discover_skill_categories(release_dir)
    replacements = build_replacements(
        release_dir=release_dir,
        algorithm_version=algorithm_version,
        categories=categories,
        project_root=project_root,
    )

    template_text = template_path.read_text(encoding="utf-8")
    output_text = render_template(template_text, replacements)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(output_text, encoding="utf-8")


def parse_args(argv: List[str]) -> argparse.Namespace:
    """解析命令行参数。"""
    parser = argparse.ArgumentParser(description="生成 PAI 的 Codex 桥接 AGENTS 文件")

    script_file = Path(__file__).resolve()
    repo_root = detect_repo_root(script_file)

    parser.add_argument("--project-root", default=".", help="目标项目根目录（默认当前目录）")
    parser.add_argument("--output", default="AGENTS.md", help="输出文件名（默认 AGENTS.md）")
    parser.add_argument(
        "--release",
        default=str((repo_root / "Releases" / "v4.0.1" / ".claude").as_posix()),
        help="PAI 发布目录，默认 Releases/v4.0.1/.claude",
    )
    parser.add_argument(
        "--template",
        default=str((repo_root / "Codex" / "templates" / "AGENTS.pai-codex.template.md").as_posix()),
        help="模板文件路径",
    )
    parser.add_argument("--force", action="store_true", help="覆盖已存在输出文件")

    return parser.parse_args(argv)


def main(argv: List[str] | None = None) -> int:
    """命令行入口。"""
    args = parse_args(argv or sys.argv[1:])

    project_root = Path(args.project_root).resolve()
    output_path = project_root / args.output
    release_dir = Path(args.release).resolve()
    template_path = Path(args.template).resolve()

    try:
        generate_bridge_file(
            template_path=template_path,
            release_dir=release_dir,
            output_path=output_path,
            project_root=project_root,
            force=args.force,
        )
    except Exception as exc:  # noqa: BLE001
        print(f"[codex-bridge] 生成失败: {exc}", file=sys.stderr)
        return 1

    print(f"[codex-bridge] 生成完成: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
