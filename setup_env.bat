@echo off
setlocal

echo Setting up development environment via Python...

REM Check if Python is available
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python is not found in PATH. Please install Python.
    pause
    exit /b 1
)

python setup_env.py

if %errorlevel% neq 0 (
    echo Setup failed.
    pause
    exit /b 1
)

echo.
echo Setup complete.
echo You can now use build_exe.bat to build the application.
pause
