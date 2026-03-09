# Kill any process on port 8000, then start backend
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

$conns = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue
$pids = $conns | ForEach-Object { $_.OwningProcess } | Where-Object { $_ -and $_ -ne 0 } | Sort-Object -Unique
foreach ($procId in $pids) {
    Write-Host "Stopping process $procId on port 8000..."
    Stop-Process -Id $procId -Force -ErrorAction SilentlyContinue
}
# Also kill child processes (uvicorn reloader spawns workers)
Start-Sleep -Seconds 2
$conns2 = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue
foreach ($c in $conns2) {
    $procId = $c.OwningProcess
    if ($procId -and $procId -ne 0) {
        Stop-Process -Id $procId -Force -ErrorAction SilentlyContinue
    }
}
Start-Sleep -Seconds 2

Write-Host "Starting backend..."
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 --reload-exclude ".venv"
