# Standalone payments stack: Postgres (Docker) + FastAPI :8888 + Vite :5174
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

Write-Host "Starting Postgres (docker compose)..." -ForegroundColor Cyan
docker compose up -d

Set-Location backend
if (-not (Test-Path .\.venv\Scripts\python.exe)) {
  Write-Host "Creating Python venv..." -ForegroundColor Cyan
  python -m venv .venv
  .\.venv\Scripts\pip install -r requirements.txt
}

Write-Host "Running migrations..." -ForegroundColor Cyan
.\.venv\Scripts\alembic upgrade head

$apiPort = if ($env:PAYMENTS_API_PORT) { $env:PAYMENTS_API_PORT } else { "8888" }
Write-Host "Starting API on port $apiPort (stop with Ctrl+C)..." -ForegroundColor Green
.\.venv\Scripts\uvicorn app.main:app --reload --host 127.0.0.1 --port $apiPort
