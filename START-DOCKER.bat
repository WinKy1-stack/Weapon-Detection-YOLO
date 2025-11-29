@echo off
title Weapon Detection - Docker
color 0B
cls

echo ================================================
echo    WEAPON DETECTION SYSTEM - DOCKER
echo ================================================
echo.

REM Check if Docker is running
echo [Checking] Docker status...
docker info >nul 2>&1
if errorlevel 1 (
    echo.
    echo [ERROR] Docker is not running!
    echo Please start Docker Desktop first.
    echo.
    pause
    exit /b 1
)
echo [OK] Docker is running
echo.

echo [1/3] Stopping old containers...
docker-compose down 2>nul
echo.

echo [2/3] Building images (first time may take 5-10 minutes)...
docker-compose build
echo.

echo [3/3] Starting containers...
docker-compose up -d
echo.

echo ================================================
echo    SYSTEM STARTED!
echo ================================================
echo.
echo Frontend: http://localhost:3000
echo Backend:  http://localhost:8000
echo API Docs: http://localhost:8000/api/v1/docs
echo.
echo Login: son@gmail.com / 123456
echo.
echo [Tip] To view logs:
echo   docker-compose logs -f
echo.
echo [Tip] To stop:
echo   docker-compose down
echo.
echo ================================================
echo.
pause
