@echo off
REM Start the Abogen Web UI backend using the project's virtual environment
REM This script ensures the backend has access to all installed dependencies

setlocal enabledelayedexpansion

REM Get the directory where this batch file is located
set SCRIPT_DIR=%~dp0
REM Remove trailing backslash
set SCRIPT_DIR=%SCRIPT_DIR:~0,-1%
set PROJECT_ROOT=%SCRIPT_DIR%\..

REM Check if .venv exists
if not exist "%PROJECT_ROOT%\.venv" (
    echo Error: Virtual environment not found at %PROJECT_ROOT%\.venv
    exit /b 1
)

REM Check if backend directory exists
if not exist "%SCRIPT_DIR%\backend" (
    echo Error: Backend directory not found at %SCRIPT_DIR%\backend
    exit /b 1
)

echo Starting Abogen Web UI Backend...
echo Using Python: %PROJECT_ROOT%\.venv\Scripts\python.exe
echo Backend directory: %SCRIPT_DIR%\backend
echo.

REM Start the backend server
cd /d "%SCRIPT_DIR%\backend"
"%PROJECT_ROOT%\.venv\Scripts\python.exe" main.py

endlocal
