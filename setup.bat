@echo off
echo Setting up GCO Office Management System...
cd /d "%~dp0"

REM Use py launcher (works when python/pip not in PATH)
py -3 -m venv venv
if errorlevel 1 (
    echo Trying python instead...
    python -m venv venv
)
if errorlevel 1 (
    echo ERROR: Python not found. Install from https://www.python.org/downloads/
    echo Be sure to check "Add Python to PATH" during install.
    pause
    exit /b 1
)

echo Installing packages...
venv\Scripts\python.exe -m pip install --upgrade pip
venv\Scripts\python.exe -m pip install -r requirements.txt

echo.
echo Setup complete! Run start.bat to start the app.
pause
