# Backend Restart Required

If the Dashboard shows "+0.00%" everywhere and "Restart backend for live data", the backend dashboard route is not loaded.

## Steps

1. **Stop all backends** – Close any terminal running uvicorn (Ctrl+C). Multiple processes can bind to port 8000 on Windows, causing stale routes.

2. **Kill processes on port 8000** (PowerShell):
   ```powershell
   Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }
   Start-Sleep -Seconds 3
   ```

3. **Restart** from the backend directory:
   ```powershell
   cd backend
   .\restart.ps1
   ```
   Or manually:
   ```powershell
   uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 --reload-exclude ".venv"
   ```

4. **Verify** – Open http://localhost:8000/api/v1/dashboard/market-overview – you should get JSON (not 404).

5. Refresh the Dashboard in your browser.
