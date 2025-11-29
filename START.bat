@echo off
title Weapon Detection System
color 0A
cls

echo ========================================
echo    WEAPON DETECTION SYSTEM
echo    Auto Startup
echo ========================================
echo.

echo [1/3] Cleaning up old processes...
taskkill /F /IM python.exe >nul 2>&1
taskkill /F /IM node.exe >nul 2>&1
timeout /t 2 /nobreak >nul

echo [2/3] Starting Backend Server...
start "Backend - Port 8000" cmd /k "cd /d %~dp0 && backend\venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000"
timeout /t 5 /nobreak >nul

echo [3/3] Starting Frontend Server...
start "Frontend - Port 3000" cmd /k "cd /d %~dp0frontend && npm run dev"
timeout /t 3 /nobreak >nul

echo.
echo ========================================
echo    SYSTEM STARTED!
echo ========================================
echo.
echo Frontend: http://localhost:3000
echo API Docs: http://localhost:8000/api/v1/docs
echo.
echo Login: son@gmail.com / 123456
echo.
echo Press any key to exit...
pause >nul
