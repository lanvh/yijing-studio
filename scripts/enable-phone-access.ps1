# Run once as administrator when phone connections are blocked by Windows Firewall.
$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot -Parent
$nodePath = Join-Path $root '.tools/node/node_modules/node/bin/node.exe'
if (-not (Test-Path -LiteralPath $nodePath)) { throw 'Project Node runtime not found.' }
$ruleName = 'AISeedStudio-Phone-5173'
if (-not (Get-NetFirewallRule -Name $ruleName -ErrorAction SilentlyContinue)) {
  New-NetFirewallRule -Name $ruleName -DisplayName 'AI Seed Studio phone access (local subnet only)' -Direction Inbound -Action Allow -Protocol TCP -LocalPort 5173 -Program $nodePath -RemoteAddress LocalSubnet -Profile Any | Out-Null
}
Write-Output 'Phone access enabled for this project on TCP 5173 from the local subnet.'
