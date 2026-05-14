$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$backend = Join-Path $root "backend"
$python = Join-Path $backend ".venv\Scripts\python.exe"

if (-not (Test-Path $python)) {
  throw "Virtual environment Python not found at $python"
}

Set-Location $backend
$env:PYTHONIOENCODING = "utf-8"
& $python -m uvicorn app.main:app --host 127.0.0.1 --port 8000

