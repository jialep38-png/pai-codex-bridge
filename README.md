# pai-codex-bridge

> Language: **English (Primary)** | [中文文档](README.zh-CN.md)

A Codex-compatible bridge built on top of Personal AI Infrastructure (PAI), focused on daily usability in Codex with runtime hook orchestration.

## What This Repository Is

`pai-codex-bridge` is a derivative project that adapts PAI assets for Codex workflows.

Key goals:

1. Make PAI methods usable in Codex.
2. Preserve high-equivalence runtime behavior where possible.
3. Provide practical daily-use commands and auto mode.

## Core Features

1. Codex bridge generator (`Tools/codex_bridge_generator.py`)
2. Runtime lifecycle orchestration (`Tools/pai_codex_runtime.py`)
3. One-command launcher (`Codex/runtime/pai-codex.ps1`, `Codex/runtime/pai-codex.sh`)
4. Environment diagnostics (`doctor`)
5. PowerShell auto mode (`codex` wrapper + `codex-raw` fallback)

## Quick Start

Run from repository root:

```powershell
# 1) Environment health check
py Tools/pai_codex_runtime.py doctor --json

# 2) Refresh AGENTS context (recommended)
py Tools/codex_bridge_generator.py --project-root . --output AGENTS.md --force

# 3) Launch Codex with PAI runtime lifecycle
.\Codex\runtime\pai-codex.ps1
```

## Daily Auto Mode

If your PowerShell profile includes the `PAI CODEX MODE` block, running:

```powershell
codex
```

will automatically:

1. Enter PAI runtime mode
2. Inject `--dangerously-bypass-approvals-and-sandbox`

Use native Codex directly when needed:

```powershell
codex-raw
```

## Project Docs

1. [Codex Bridge Overview](Codex/README.md)
2. [Runtime Details](Codex/runtime/README.md)
3. [Open Source Package Guide](OPEN_SOURCE_GITHUB_PACKAGE_GUIDE.md)
4. [Full Work Summary (CN)](OPEN_SOURCE_WORK_SUMMARY_20260302.md)
5. [Contributing](CONTRIBUTING.md)
6. [Code of Conduct](CODE_OF_CONDUCT.md)
7. [Support](SUPPORT.md)
8. [Changelog](CHANGELOG.md)

## Attribution and License

This repository is based on:

- Upstream project: [danielmiessler/Personal_AI_Infrastructure](https://github.com/danielmiessler/Personal_AI_Infrastructure)
- Upstream license: MIT

License compliance actions in this repo:

1. Original MIT license text is retained in [LICENSE](LICENSE).
2. Derivative attribution is documented in [NOTICE](NOTICE).
3. Modifications for Codex compatibility are provided under MIT terms.

## Compatibility Boundary

This implementation simulates Claude lifecycle hooks externally. It is not a Codex kernel-native hook system.

Most core flows are supported, while some transcript-dependent stop/session-end hooks may emit non-blocking warnings.
