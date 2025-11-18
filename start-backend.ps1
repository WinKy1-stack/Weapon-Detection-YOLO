# Start Backend Server
Write-Host "Starting Weapon Detection Backend..." -ForegroundColor Green

# Activate virtual environment
& ".\backend\venv\Scripts\Activate.ps1"

# Start uvicorn server
python -m uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
