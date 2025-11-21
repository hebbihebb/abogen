@echo off
REM Abogen Web UI Launcher Script for Windows
REM Starts both backend and frontend in development mode

echo Starting Abogen Web UI...
echo.

REM Get script directory
set SCRIPT_DIR=%~dp0

REM Check if frontend dependencies are installed
if not exist "%SCRIPT_DIR%frontend\node_modules" (
    echo Installing frontend dependencies...
    cd "%SCRIPT_DIR%frontend"
    call npm install
    cd "%SCRIPT_DIR%"
)

REM Start backend in new window
echo Starting backend server...
start "Abogen Backend" cmd /k "cd /d %SCRIPT_DIR%backend && python main.py"

REM Wait a bit for backend to start
timeout /t 3 /nobreak >nul

REM Start frontend in new window
echo Starting frontend server...
start "Abogen Frontend" cmd /k "cd /d %SCRIPT_DIR%frontend && npm run dev"

echo.
echo Abogen Web UI is starting!
echo.
echo Backend API:  http://localhost:8000
echo Frontend UI:  http://localhost:5173
echo API Docs:     http://localhost:8000/docs
echo.
echo Close the command windows to stop the servers
echo.

pause
