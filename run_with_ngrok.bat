@echo off
echo ====================================
echo FinAlert Backend + Ngrok Tunnel
echo ====================================
echo.

REM Check if ngrok is installed
where ngrok >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: ngrok not found!
    echo Please install ngrok first:
    echo 1. Go to https://ngrok.com/download
    echo 2. Extract and add to PATH
    echo 3. Run: ngrok config add-authtoken YOUR_AUTHTOKEN
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
echo Starting ngrok tunnel...
echo Copy the forwarding URL shown below and update App.tsx
echo.
ngrok http 8000 --inspect=false

pause