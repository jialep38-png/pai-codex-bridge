param(
  [Parameter(ValueFromRemainingArguments = $true)]
  [string[]]$CodexArgs
)

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = Resolve-Path (Join-Path $scriptDir "..\..")
$runtime = Join-Path $repoRoot "Tools\pai_codex_runtime.py"

# 直接启动 Codex，并自动触发 SessionStart/Stop/SessionEnd
py $runtime --project-root (Get-Location).Path launch-codex -- $CodexArgs
exit $LASTEXITCODE
