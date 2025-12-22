@echo off
setlocal

echo Setting up development environment...

REM Check if Python is available
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python is not found in PATH. Please install Python.
    pause
    exit /b 1
)

REM Create venv if it doesn't exist
if not exist ".venv" (
    echo Creating virtual environment (.venv)...
    python -m venv .venv
) else (
    echo Virtual environment (.venv) already exists.
)

REM Activate and install
echo Installing requirements...
call .venv\Scripts\activate.bat
pip install -U pip
pip install -r requirements.txt

echo.
echo Setup complete.
echo You can now use build_exe.bat to build the application.
pause
