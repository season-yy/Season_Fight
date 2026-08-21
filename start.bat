@echo off
cd /d "%~dp0"

REM Check virtual environment
if not exist "venv\Scripts\python.exe" (
    echo [Setup] Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo [ERROR] Failed to create venv. Make sure Python 3.8+ is installed.
        pause
        exit /b 1
    )
    echo [Setup] Installing dependencies...
    venv\Scripts\python.exe -m pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
    if errorlevel 1 (
        echo [ERROR] Failed to install dependencies.
        pause
        exit /b 1
    )
)

REM Verify modules
echo [Verify] Checking modules...
venv\Scripts\python.exe -c "import flask, jieba, apscheduler" 2>nul
if errorlevel 1 (
    echo [ERROR] Missing modules. Reinstalling...
    venv\Scripts\python.exe -m pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
    if errorlevel 1 (
        echo [ERROR] Reinstall failed.
        pause
        exit /b 1
    )
)

REM Auto-open browser after 2 seconds (let Flask start first)
start "" cmd /c "timeout /t 2 /nobreak >nul && start http://localhost:1224"

echo.
echo ============================================================
echo   Season_Fight - Learning Tracker
echo ============================================================
echo   PC  access : http://localhost:1224
echo   Phone access: http://YOUR_LOCAL_IP:1224  (same WiFi)
echo.
echo   *** KEEP THIS WINDOW OPEN ***
echo   *** DO NOT close this window while using the app ***
echo   *** To stop: press Ctrl+C then Y, or close this window ***
echo ============================================================
echo.
echo   Starting server... browser will open automatically.
echo.

REM Launch with venv python directly
venv\Scripts\python.exe app.py

echo.
echo ============================================================
echo   Server stopped. Press any key to close.
echo ============================================================
pause