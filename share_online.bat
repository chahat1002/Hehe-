@echo off
title SafeRoute Online Public Link
cd /d "%~dp0"

echo ========================================================
echo   SafeRoute Server + Public Online Sharing
echo ========================================================

REM Check if python venv exists
if exist ".venv\Scripts\python.exe" (
    set "PYTHON_EXE=.venv\Scripts\python.exe"
) else (
    set "PYTHON_EXE=python"
)

REM Start Flask server in background window
start "SafeRoute Server" /min "%PYTHON_EXE%" app.py

echo.
echo Generating public HTTPS link for your friends...
echo Copy the link ending in .trycloudflare.com below and send it to them!
echo.
cloudflared.exe tunnel --url http://127.0.0.1:5000
pause
