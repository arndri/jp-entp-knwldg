$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$backend = Join-Path $root "backend"
$frontend = Join-Path $root "frontend"
$python = Join-Path $backend ".venv\Scripts\python.exe"

function Assert-LastExitCode([string]$step) {
  if ($LASTEXITCODE -ne 0) {
    throw "$step failed with exit code $LASTEXITCODE"
  }
}

if (-not (Test-Path $python)) {
  throw "Virtual environment Python not found at $python"
}

Write-Output "== Backend compile check =="
Push-Location $backend
try {
  & $python -m compileall app
  Assert-LastExitCode "Backend compile check"
  Write-Output ""
  Write-Output "== Backend pytest =="
  & $python -m pytest
  Assert-LastExitCode "Backend pytest"
}
finally {
  Pop-Location
}

Write-Output ""
Write-Output "== Frontend production build =="
Push-Location $frontend
try {
  npm.cmd run build
  Assert-LastExitCode "Frontend production build"
  Write-Output ""
  Write-Output "== Frontend E2E smoke test =="
  npm.cmd run test:e2e
  Assert-LastExitCode "Frontend E2E smoke test"
}
finally {
  Pop-Location
}

Write-Output ""
Write-Output "All project checks passed."
