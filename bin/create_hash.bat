@echo off
setlocal enabledelayedexpansion
set "archive=%~1"

:: Define colors via ESC code
for /F %%a in ('echo prompt $E ^| cmd') do set "ESC=%%a"
set "RED=!ESC![31m"
set "GREEN=!ESC![32m"
set "YELLOW=!ESC![33m"
set "BLUE=!ESC![34m"
set "CYAN=!ESC![36m"
set "NC=!ESC![0m"

if "%~1"=="" (echo Usage: create_hash.bat [archive.zip/7z] & exit /b 1)

REM Verify that the input is a valid archive
7z l "%archive%" >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo !RED![ERROR]!NC! "%archive%" is not a valid archive file.
    exit /b 1
)

REM Generate SHA256 of the archive file itself
echo !CYAN![INFO]!NC!  Layer 1: Generating Archive File Hash...
powershell -Command "$hash = (Get-FileHash '%archive%' -Algorithm SHA256).Hash.ToLower(); \"$hash  $((Split-Path -Leaf '%archive%'))\"" > "%archive%.sha256"

REM Generate "Content Hash" based on internal file data
REM We use 7z test command with -scrcSHA256 to get a stable hash of the contents.
echo !CYAN![INFO]!NC!  Layer 3: Generating Content Hash (Internal 7z data)...
for /f "tokens=2 delims=:" %%a in ('7z t -scrcSHA256 "%archive%" ^| findstr /C:"SHA256 for data:"') do (
    set "contentHash=%%a"
)
REM Trim leading/trailing spaces and remove potential dash suffix (e.g. -00000000)
set "contentHash=%contentHash: =%"
for /f "tokens=1 delims=-" %%g in ("%contentHash%") do set "contentHash=%%g"

if not "%contentHash%"=="" (
    echo %contentHash% > "%archive%.content.sha256"
)

echo !GREEN![SUCCESS]!NC! Created %archive%.sha256
if exist "%archive%.content.sha256" echo !GREEN![SUCCESS]!NC! Created %archive%.content.sha256
