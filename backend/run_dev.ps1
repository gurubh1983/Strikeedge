# Run backend with reload; exclude .venv to prevent reload storms from package changes
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 --reload-exclude ".venv"
