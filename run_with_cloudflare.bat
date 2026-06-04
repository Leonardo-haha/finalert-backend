@echo off
chcp 65001 >nul
echo ====================================
echo FinAlert Backend + Cloudflare Tunnel
echo ====================================
echo.

REM Check if cloudflared is installed
where cloudflared >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: cloudflared not found!
    echo.
    echo Please install Cloudflare Tunnel first:
    echo Option A: Run: winget install Cloudflare.cloudflared
    echo Option B: Download from:
    echo   https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/
    echo.
    pause
    exit /b 1
)

REM Check if virtual environment exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
    echo Activating and installing dependencies...
    venv\Scripts\pip install -r requirements.txt
)

echo.
echo Starting backend server...
start "FinAlert Backend" cmd /k "venv\Scripts\activate && python -m uvicorn app.main:app --reload --port 8000"

echo Waiting for backend to start (5 seconds)...
timeout /t 5 /nobreak > nul

echo.
echo Starting Cloudflare Tunnel...
echo.
echo IMPORTANT: Copy the URL shown below (e.g., https://xxxx.trycloudflare.com)
echo Then update api.config.ts in the frontend project.
echo.
cloudflared tunnel --url http://localhost:8000

pause