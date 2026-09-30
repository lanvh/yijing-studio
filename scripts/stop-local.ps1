$root = Split-Path $PSScriptRoot -Parent
$escaped = [regex]::Escape($root)
Get-CimInstance Win32_Process | Where-Object {
  ($_.ExecutablePath -like "$root\*" -or $_.CommandLine -match $escaped) -and
  ($_.CommandLine -match 'uvicorn.*app.main:app|vite[/\\]bin[/\\]vite.js')
} | ForEach-Object { Stop-Process -Id $_.ProcessId -ErrorAction SilentlyContinue }
Write-Output 'Stopped this project local web processes. PostgreSQL remains running.'
