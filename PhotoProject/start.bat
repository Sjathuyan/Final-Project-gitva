@echo off
echo === Photo Print Studio ===
cd /d "%~dp0"
start "Photo Print Studio" cmd /k "python -m uvicorn app.main:app --reload --port 8000"
timeout /t 4 /nobreak >nul
start "" "http://localhost:8000"
echo.
echo Server: http://localhost:8000
pause
