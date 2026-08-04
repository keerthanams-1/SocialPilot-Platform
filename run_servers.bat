@echo off
echo ===================================================
echo   SocialPilot - Starting Backend & Frontend Servers
echo ===================================================
echo.

:: Start FastAPI Backend
start "SocialPilot Backend (Port 8000)" cmd /k "cd /d %~dp0backend && .\venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload"

echo [1/2] FastAPI Backend starting at http://127.0.0.1:8000 ...

:: Start Vite Frontend
start "SocialPilot Frontend (Port 5173)" cmd /k "cd /d %~dp0frontend && npm run dev -- --host 127.0.0.1 --port 5173"

echo [2/2] React Frontend starting at http://127.0.0.1:5173 ...

echo.
echo ===================================================
echo   Both services launched in separate windows!
echo   - Frontend App:   http://localhost:5173
echo   - Backend API:    http://localhost:8000
echo   - Swagger Docs:   http://localhost:8000/docs
echo ===================================================
pause
