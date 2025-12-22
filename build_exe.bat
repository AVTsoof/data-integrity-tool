@echo off
echo Checking for PyInstaller...
python -m PyInstaller --version >nul 2>&1
if %errorlevel% neq 0 (
    echo PyInstaller is not installed. Please install it using:
    echo pip install pyinstaller
    exit /b 1
)

echo Building Data Integrity Tool...
echo Building Data Integrity Tool...
python build_release.py

if %errorlevel% equ 0 (
    echo.
    echo Build successful!
    echo Executable is located in the 'dist' folder.
) else (
    echo.
    echo Build failed.
)
