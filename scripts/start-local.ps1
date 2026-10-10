$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot -Parent
Set-Location $root
& "$PSScriptRoot/init-env.ps1"
$phoneConfigured = Get-Content -LiteralPath (Join-Path $root '.env') | Where-Object { $_ -match '^MOBILE_PUBLIC_URL=' } | Select-Object -First 1
if (-not $env:MOBILE_PUBLIC_URL -and $phoneConfigured) {
  $phoneConfiguredValue = ($phoneConfigured -split '=', 2)[1].Trim().Trim('"').Trim("'")
  if ($phoneConfiguredValue) { $env:MOBILE_PUBLIC_URL = $phoneConfiguredValue }
}
# Keep the API on loopback; only Vite exposes the authenticated app and scoped phone links.
$phoneAddress = Get-NetIPConfiguration -ErrorAction SilentlyContinue |
  Where-Object { $_.IPv4DefaultGateway -and $_.NetAdapter.Status -eq 'Up' } |
  ForEach-Object { $_.IPv4Address.IPAddress } | Select-Object -First 1
if (-not $env:MOBILE_PUBLIC_URL -and $phoneAddress) {
  $env:MOBILE_PUBLIC_URL = "http://${phoneAddress}:5173"
}
docker compose up -d --wait db
if ($LASTEXITCODE -ne 0) { throw 'Database startup failed.' }
$python = Join-Path $root 'backend/.venv/Scripts/python.exe'
$node = Join-Path $root '.tools/node/node_modules/node/bin/node.exe'
if (-not (Test-Path $python)) { throw 'Create backend/.venv with Python 3.12+ first; see README.' }
if (-not (Test-Path $node)) { $node = (Get-Command node).Source }
Push-Location (Join-Path $root 'backend')
try {
  & $python -m alembic upgrade head
  if ($LASTEXITCODE -ne 0) { throw 'Migration failed.' }
} finally { Pop-Location }
if (-not (Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue)) {
  $backend = Start-Process -FilePath $python -ArgumentList '-m','uvicorn','app.main:app','--host','127.0.0.1','--port','8000' -WorkingDirectory (Join-Path $root 'backend') -WindowStyle Hidden -RedirectStandardOutput (Join-Path $root 'storage/backend.log') -RedirectStandardError (Join-Path $root 'storage/backend-error.log') -PassThru
  $backend.Id | Set-Content (Join-Path $root 'storage/backend.pid')
}
if (-not (Get-NetTCPConnection -LocalPort 5173 -State Listen -ErrorAction SilentlyContinue)) {
  $frontend = Start-Process -FilePath $node -ArgumentList 'node_modules/vite/bin/vite.js','--host','0.0.0.0' -WorkingDirectory (Join-Path $root 'frontend') -WindowStyle Hidden -RedirectStandardOutput (Join-Path $root 'storage/frontend.log') -RedirectStandardError (Join-Path $root 'storage/frontend-error.log') -PassThru
  $frontend.Id | Set-Content (Join-Path $root 'storage/frontend.pid')
}
Write-Output 'Frontend: http://localhost:5173'
Write-Output 'API docs: http://localhost:8000/docs'

if ($phoneAddress) { Write-Output "Phone (same Wi-Fi): http://${phoneAddress}:5173" }
