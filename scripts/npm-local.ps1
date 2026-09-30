param([Parameter(ValueFromRemainingArguments=$true)][string[]]$NpmArgs)
$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot -Parent
$node = Join-Path $root '.tools/node/node_modules/node/bin/node.exe'
if (-not (Test-Path -LiteralPath $node)) { $node = (Get-Command node).Source }
$npmCli = Join-Path (Split-Path (Get-Command npm.cmd).Source -Parent) 'node_modules/npm/bin/npm-cli.js'
$env:PATH = (Split-Path $node -Parent) + ';' + $env:PATH
Push-Location (Join-Path $root 'frontend')
try { & $node $npmCli @NpmArgs; $result = $LASTEXITCODE } finally { Pop-Location }
exit $result
