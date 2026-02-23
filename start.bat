@echo off
cd /d "%~dp0"

if not exist venv\Scripts\python.exe (
    echo Run setup.bat first! Double-click setup.bat to install.
    pause
    exit /b 1
)

venv\Scripts\python.exe run.py

pause
