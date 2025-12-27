# PowerShell script to start Neo4j, PostgreSQL, Redis, backend FastAPI, and Expo frontend for The Grey Tutor

Write-Host "=== The Grey Tutor Startup Script ===" -ForegroundColor Cyan

# 1. Start Docker containers (Neo4j + PostgreSQL + Redis)
Write-Host "`n[1/4] Starting Docker containers (Neo4j + PostgreSQL + Redis)..." -ForegroundColor Yellow
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
Write-Host "`n[2/4] Starting backend FastAPI app on http://localhost:8000..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD'; python -m uvicorn thegreytutor.backend.src.main:app --reload --host 0.0.0.0 --port 8000"

# Wait for backend to start
Start-Sleep -Seconds 5

# 3. Start Expo frontend (from root now since we moved src)
Write-Host "`n[3/4] Starting Expo frontend..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD'; npx expo start"

Write-Host "`n[4/4] All services started!" -ForegroundColor Green
Write-Host @"

=== Services Running ===
- Neo4j Browser:    http://localhost:7474
- Redis:            localhost:6379
- Backend API:      http://localhost:8000
- API Docs:         http://localhost:8000/docs
- Cache Stats:      http://localhost:8000/cache/stats
- Expo Dev Server:  Check the new terminal window

Press Ctrl+C to stop (then run: docker-compose down)
"@ -ForegroundColor Cyan

# Keep script running
Write-Host "`nPress Ctrl+C to stop all services..." -ForegroundColor Yellow
try {
    while ($true) { Start-Sleep -Seconds 1 }
} finally {
    Write-Host "`nStopping services..." -ForegroundColor Red
    docker-compose down
}
