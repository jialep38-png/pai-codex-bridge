#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
RUNTIME="$REPO_ROOT/Tools/pai_codex_runtime.py"

py "$RUNTIME" "$@"
