# PowerShell script to start Neo4j, PostgreSQL, Redis, backend FastAPI, and Expo frontend for The Grey Tutor
# Usage:
#   .\start_all.ps1          # Start with cache cleared (recommended during development)
#   .\start_all.ps1 -fast    # Start without clearing cache (faster, but may not pick up all changes)

param(
    [switch]$fast = $false
)

Write-Host "=== The Grey Tutor Startup Script ===" -ForegroundColor Cyan

# 1. Start Docker containers (Neo4j + PostgreSQL + Redis)
Write-Host "`n[1/5] Starting Docker containers (Neo4j + PostgreSQL + Redis)..." -ForegroundColor Yellow
docker-compose up -d

# Wait for Neo4j to be ready
Write-Host "Waiting for Neo4j to be ready..." -ForegroundColor Gray
Start-Sleep -Seconds 10

# Wait for PostgreSQL to be ready
Write-Host "Waiting for PostgreSQL to be ready..." -ForegroundColor Gray
Start-Sleep -Seconds 3

# Wait for Redis to be ready
Write-Host "Waiting for Redis to be ready..." -ForegroundColor Gray
Start-Sleep -Seconds 2

# 2. Start backend FastAPI app
Write-Host "`n[2/5] Starting backend FastAPI app on http://localhost:8000..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD'; `$env:PYTHONPATH='$PWD'; python -m uvicorn thegreytutor.backend.src.main:app --reload --host 0.0.0.0 --port 8000"

# Wait for backend to start
Start-Sleep -Seconds 5

# 3. Clear Metro bundler cache (unless -fast flag is used)
if (-not $fast) {
    Write-Host "`n[3/5] Clearing Metro bundler cache..." -ForegroundColor Yellow

    # Clear root cache directories (if they exist)
    if (Test-Path "node_modules\.cache") {
        Remove-Item -Recurse -Force "node_modules\.cache" -ErrorAction SilentlyContinue
        Write-Host "  Cleared root node_modules/.cache" -ForegroundColor Gray
    }
    if (Test-Path ".expo") {
        Remove-Item -Recurse -Force ".expo" -ErrorAction SilentlyContinue
        Write-Host "  Cleared root .expo" -ForegroundColor Gray
    }

    # Clear frontend cache directories
    if (Test-Path "thegreytutor\frontend\node_modules\.cache") {
        Remove-Item -Recurse -Force "thegreytutor\frontend\node_modules\.cache" -ErrorAction SilentlyContinue
        Write-Host "  Cleared frontend node_modules/.cache" -ForegroundColor Gray
    }
    if (Test-Path "thegreytutor\frontend\.expo") {
        Remove-Item -Recurse -Force "thegreytutor\frontend\.expo" -ErrorAction SilentlyContinue
        Write-Host "  Cleared frontend .expo" -ForegroundColor Gray
    }

    Write-Host "  Cache cleared! Starting with fresh build..." -ForegroundColor Green
} else {
    Write-Host "`n[3/5] Skipping cache clear (fast mode)..." -ForegroundColor Yellow
    Write-Host "  Note: Use '.\start_all.ps1' without -fast to clear cache if changes do not appear" -ForegroundColor Gray
}

# 4. Start Expo frontend from the correct directory
Write-Host "`n[4/5] Starting Expo frontend from thegreytutor/frontend/..." -ForegroundColor Yellow

if (-not $fast) {
    # Start with --clear flag to ensure Metro cache is cleared
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD\thegreytutor\frontend'; npx expo start --clear"
} else {
    # Start normally for faster startup
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD\thegreytutor\frontend'; npx expo start"
}

Write-Host "`n[5/5] All services started!" -ForegroundColor Green
Write-Host ""
Write-Host "=== Services Running ===" -ForegroundColor Cyan
Write-Host "- Neo4j Browser:    http://localhost:7474" -ForegroundColor Cyan
Write-Host "- Redis:            localhost:6379" -ForegroundColor Cyan
Write-Host "- Backend API:      http://localhost:8000" -ForegroundColor Cyan
Write-Host "- API Docs:         http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host "- Cache Stats:      http://localhost:8000/cache/stats" -ForegroundColor Cyan
Write-Host "- Expo Dev Server:  Check the new terminal window (running from thegreytutor/frontend/)" -ForegroundColor Cyan
Write-Host ""
Write-Host "=== Development Mode ===" -ForegroundColor Cyan

if (-not $fast) {
    Write-Host "  Cache cleared - all changes will be loaded" -ForegroundColor Green
    Write-Host "  To start faster next time: .\start_all.ps1 -fast" -ForegroundColor Gray
} else {
    Write-Host "  Fast mode - skipped cache clear" -ForegroundColor Yellow
    Write-Host "  If changes do not appear, restart with: .\start_all.ps1" -ForegroundColor Gray
}

Write-Host ""
Write-Host "=== Quick Commands ===" -ForegroundColor Cyan
Write-Host "In Expo terminal window:" -ForegroundColor Cyan
Write-Host "  r  - Reload app" -ForegroundColor Cyan
Write-Host "  Shift+r - Reload and clear app cache" -ForegroundColor Cyan
Write-Host "  m  - Toggle menu" -ForegroundColor Cyan
Write-Host "  c  - Clear Metro bundler cache" -ForegroundColor Cyan
Write-Host ""
Write-Host "Press Ctrl+C to stop (then run: docker-compose down)" -ForegroundColor Cyan
Write-Host ""

# Keep script running
Write-Host "Press Ctrl+C to stop all services..." -ForegroundColor Yellow
try {
    while ($true) { Start-Sleep -Seconds 1 }
} finally {
    Write-Host "`nStopping services..." -ForegroundColor Red
    docker-compose down
}
