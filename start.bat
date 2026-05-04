@echo off
setlocal enabledelayedexpansion

:: NetGuard IDS — Windows Startup Script
echo 🚀 Starting NetGuard IDS for Windows...

:: 1. Check for Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python not found. Please install Python 3.11 from python.org.
    pause
    exit /b 1
)

:: 2. Set environment
set "PYTHONPATH=%PYTHONPATH%;%CD%"

:: 3. Inform about Npcap (Crucial for Windows)
echo 🔍 Checking for Npcap/WinPcap requirements...
echo 💡 Reminder: You MUST have Npcap installed in 'WinPcap API-compatible mode'.
echo    Download: https://npcap.com/#download

:: 4. Start Backend
echo 📡 Starting Backend (FastAPI)...
start "NetGuard Backend" /B python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000

:: 5. Start Frontend
echo 🎨 Starting Frontend (React/Vite)...
cd frontend
start "NetGuard Frontend" /B npm run dev
cd ..

echo.
echo ✨ NetGuard is now initializing!
echo --------------------------------------------------
echo Dashboard:   http://localhost:5173
echo Backend API: http://localhost:8000
echo --------------------------------------------------
echo ⚠️  IMPORTANT: Run this terminal as ADMINISTRATOR for packet capture.
echo.
echo Press Ctrl+C in the backend/frontend windows to stop, or close this window.
echo (Process IDs: Use Task Manager to kill 'python.exe' and 'node.exe' if they persist).
echo.

pause
