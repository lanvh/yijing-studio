$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot -Parent
$envPath = Join-Path $root '.env'
if (-not (Test-Path -LiteralPath $envPath)) { & "$PSScriptRoot/init-env.ps1" }
$content = Get-Content -LiteralPath $envPath -Raw
if ($content -notmatch '(?m)^ADMIN_EMAIL=') {
  $bytes = New-Object byte[] 24
  $rng = [System.Security.Cryptography.RandomNumberGenerator]::Create()
  $rng.GetBytes($bytes)
  $rng.Dispose()
  $password = [Convert]::ToBase64String($bytes)
  [IO.File]::AppendAllText($envPath, "`nADMIN_EMAIL=creator@example.com`nADMIN_PASSWORD=$password`n", [Text.UTF8Encoding]::new($false))
}
Push-Location (Join-Path $root 'backend')
try {
  & ./.venv/Scripts/python.exe -m app.cli create-user --from-env --display-name '创作者' --role admin
  if ($LASTEXITCODE -ne 0) { throw 'Account creation did not complete. Existing accounts are never overwritten.' }
} finally { Pop-Location }
Write-Output 'Credentials are stored only in root .env (ADMIN_EMAIL / ADMIN_PASSWORD).'
