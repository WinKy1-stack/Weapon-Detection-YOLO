# Start Frontend Development Server
Write-Host "Starting Weapon Detection Frontend..." -ForegroundColor Green

# Navigate to frontend directory
Set-Location -Path ".\frontend"

# Install dependencies if not installed
if (-not (Test-Path "node_modules")) {
    Write-Host "Installing dependencies..." -ForegroundColor Yellow
    npm install
}

# Start Vite dev server
npm run dev
