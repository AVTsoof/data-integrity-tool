@echo off
echo Checking for PyInstaller...
set "PYTHON_CMD=python"
if exist ".venv\Scripts\python.exe" (
    set "PYTHON_CMD=.venv\Scripts\python.exe"
    echo Using virtual environment: .venv
)

echo Checking for PyInstaller...
"%PYTHON_CMD%" -m PyInstaller --version >nul 2>&1
if %errorlevel% neq 0 (
    echo PyInstaller is not installed.
    echo Please run setup_env.bat first to install dependencies.
    pause
    exit /b 1
)

echo Building Data Integrity Tool...
"%PYTHON_CMD%" build_release.py

if %errorlevel% equ 0 (
    echo.
    echo Build successful!
    echo Executable is located in the 'dist' folder.
) else (
    echo.
    echo Build failed.
)
pause
