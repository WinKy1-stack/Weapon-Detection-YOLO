# Docker Quick Start

Write-Host "🐳 Starting Weapon Detection Web App with Docker" -ForegroundColor Cyan
Write-Host "==============================================`n" -ForegroundColor Cyan

# Check Docker
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Docker not found. Please install Docker Desktop" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Docker found" -ForegroundColor Green

# Create .env if not exists
if (-not (Test-Path backend/.env)) {
    Write-Host "Creating backend/.env file..." -ForegroundColor Cyan
    Copy-Item backend/.env.example backend/.env
    Write-Host "⚠️  Please edit backend/.env and set your SECRET_KEY" -ForegroundColor Yellow
}

# Start services
Write-Host "`n🚀 Starting all services..." -ForegroundColor Yellow
docker-compose up -d

# Wait for services
Write-Host "`n⏳ Waiting for services to be ready..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# Check status
Write-Host "`n📊 Service Status:" -ForegroundColor Cyan
docker-compose ps

Write-Host "`n✅ All services started!" -ForegroundColor Green
Write-Host "`n📝 Access the application:" -ForegroundColor Cyan
Write-Host "  Frontend:  http://localhost:3000" -ForegroundColor White
Write-Host "  Backend:   http://localhost:8000" -ForegroundColor White
Write-Host "  API Docs:  http://localhost:8000/api/v1/docs" -ForegroundColor White

Write-Host "`n📋 Useful commands:" -ForegroundColor Cyan
Write-Host "  View logs:      docker-compose logs -f" -ForegroundColor White
Write-Host "  Stop services:  docker-compose down" -ForegroundColor White
Write-Host "  Restart:        docker-compose restart" -ForegroundColor White

# Open browser
Write-Host "`nPress any key to open browser..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
Start-Process "http://localhost:3000"

Write-Host "`n✨ Happy detecting!" -ForegroundColor Green
