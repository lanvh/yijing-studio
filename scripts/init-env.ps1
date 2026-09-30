$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot -Parent
$target = Join-Path $root '.env'
if (Test-Path -LiteralPath $target) { Write-Output '.env already exists; preserved.'; exit 0 }
$bytes = New-Object byte[] 32
$rng = [System.Security.Cryptography.RandomNumberGenerator]::Create()
$rng.GetBytes($bytes)
$rng.Dispose()
$password = -join ($bytes | ForEach-Object { $_.ToString('x2') })
$content = Get-Content -LiteralPath (Join-Path $root '.env.example') -Raw
$content = $content.Replace('POSTGRES_PASSWORD=', 'POSTGRES_PASSWORD=' + $password)
$content = $content.Replace('DATABASE_URL=', 'DATABASE_URL=postgresql+psycopg://seed:' + $password + '@localhost:5432/ai_seed_studio')
[IO.File]::WriteAllText($target, $content, [Text.UTF8Encoding]::new($false))
Write-Output 'Created .env with a random database password.'
