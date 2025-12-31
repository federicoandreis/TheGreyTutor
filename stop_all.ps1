# PowerShell script to stop all The Grey Tutor services

Write-Host "=== Stopping The Grey Tutor Services ===" -ForegroundColor Red

# Stop Docker containers
Write-Host "`nStopping Docker containers..." -ForegroundColor Yellow
docker-compose down

Write-Host "`n✓ All services stopped!" -ForegroundColor Green
Write-Host @"

To restart:
  .\start_all.ps1          # With cache clear (recommended)
  .\start_all.ps1 -fast    # Without cache clear (faster)

"@ -ForegroundColor Cyan
