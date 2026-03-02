#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
RUNTIME="$REPO_ROOT/Tools/pai_codex_runtime.py"

# 直接启动 Codex，并自动触发 SessionStart/Stop/SessionEnd
py "$RUNTIME" --project-root "$(pwd)" launch-codex -- "$@"
