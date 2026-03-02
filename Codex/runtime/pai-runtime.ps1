param(
  [Parameter(ValueFromRemainingArguments = $true)]
  [string[]]$RuntimeArgs
)

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = Resolve-Path (Join-Path $scriptDir "..\..")
$runtime = Join-Path $repoRoot "Tools\pai_codex_runtime.py"

py $runtime @RuntimeArgs
exit $LASTEXITCODE
