# Quick Start Scripts for Weapon Detection Web App

Write-Host "🚀 Weapon Detection Web App - Quick Start" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# Function to check if a command exists
function Test-Command($cmdname) {
    return [bool](Get-Command -Name $cmdname -ErrorAction SilentlyContinue)
}

Write-Host "📋 Checking prerequisites..." -ForegroundColor Yellow

# Check Python
if (Test-Command python) {
    $pythonVersion = python --version
    Write-Host "✅ $pythonVersion" -ForegroundColor Green
} else {
    Write-Host "❌ Python not found. Please install Python 3.10+" -ForegroundColor Red
    exit 1
}

# Check Node.js
if (Test-Command node) {
    $nodeVersion = node --version
    Write-Host "✅ Node.js $nodeVersion" -ForegroundColor Green
} else {
    Write-Host "❌ Node.js not found. Please install Node.js 18+" -ForegroundColor Red
    exit 1
}

# Check MongoDB
Write-Host "`n📦 Checking MongoDB..." -ForegroundColor Yellow
$mongoRunning = Get-Process -Name mongod -ErrorAction SilentlyContinue
if ($mongoRunning) {
    Write-Host "✅ MongoDB is running" -ForegroundColor Green
} else {
    Write-Host "⚠️  MongoDB not running. Starting with Docker..." -ForegroundColor Yellow
    if (Test-Command docker) {
        docker run -d --name weapon-detection-mongo -p 27017:27017 mongo:7.0
        Write-Host "✅ MongoDB started in Docker" -ForegroundColor Green
    } else {
        Write-Host "❌ MongoDB not running and Docker not found." -ForegroundColor Red
        Write-Host "Please install MongoDB or Docker" -ForegroundColor Red
        exit 1
    }
}

Write-Host "`n🔧 Setting up Backend..." -ForegroundColor Yellow

# Setup backend
cd backend

# Create .env if not exists
if (-not (Test-Path .env)) {
    Write-Host "Creating .env file..." -ForegroundColor Cyan
    Copy-Item .env.example .env
    Write-Host "⚠️  Please edit backend/.env and set your SECRET_KEY" -ForegroundColor Yellow
}

# Create virtual environment if not exists
if (-not (Test-Path venv)) {
    Write-Host "Creating virtual environment..." -ForegroundColor Cyan
    python -m venv venv
}

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Cyan
& .\venv\Scripts\Activate.ps1

# Install requirements
Write-Host "Installing Python dependencies..." -ForegroundColor Cyan
pip install -q -r requirements.txt

# Start backend in background
Write-Host "Starting FastAPI backend on port 8000..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD'; .\venv\Scripts\Activate.ps1; python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000" -WindowStyle Normal

cd ..

Write-Host "`n🎨 Setting up Frontend..." -ForegroundColor Yellow

# Setup frontend
cd frontend

# Install npm packages if not exists
if (-not (Test-Path node_modules)) {
    Write-Host "Installing npm packages..." -ForegroundColor Cyan
    npm install
}

# Start frontend in background
Write-Host "Starting React frontend on port 3000..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD'; npm run dev" -WindowStyle Normal

cd ..

Write-Host "`n✅ All services started!" -ForegroundColor Green
Write-Host "`n📝 Access the application:" -ForegroundColor Cyan
Write-Host "  Frontend:  http://localhost:3000" -ForegroundColor White
Write-Host "  Backend:   http://localhost:8000" -ForegroundColor White
Write-Host "  API Docs:  http://localhost:8000/api/v1/docs" -ForegroundColor White
Write-Host "`n⏳ Please wait 10-20 seconds for services to start..." -ForegroundColor Yellow
Write-Host "`n💡 Tip: Register a new account to get started!" -ForegroundColor Cyan

# Wait for user
Write-Host "`nPress any key to open browser..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

# Open browser
Start-Process "http://localhost:3000"

Write-Host "`n✨ Happy detecting! Press Ctrl+C in backend/frontend windows to stop." -ForegroundColor Green
