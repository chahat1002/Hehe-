@echo off
title SafeRoute Server
cd /d "%~dp0"

echo ========================================================
echo   Starting SafeRoute Map Backend Server...
echo ========================================================

if exist ".venv\Scripts\python.exe" (
    set "PYTHON_EXE=.venv\Scripts\python.exe"
) else (
    set "PYTHON_EXE=python"
)

echo Opening map at http://127.0.0.1:5000 in your default browser...
start "" http://127.0.0.1:5000

"%PYTHON_EXE%" app.py
pause
