@echo off
set "archive=%~1"
if "%~1"=="" (echo Usage: create_hash.bat [archive.zip/7z] & exit /b 1)

:: Generate SHA256 of the archive file itself
powershell -Command "$hash = (Get-FileHash '%archive%' -Algorithm SHA256).Hash.ToLower(); \"$hash  $((Split-Path -Leaf '%archive%'))\"" > "%archive%.sha256"

:: Generate "Content Hash" based on internal file data
:: We use 7z test command with -scrcSHA256 to get a stable hash of the contents.
for /f "tokens=2 delims=:" %%a in ('7z t -scrcSHA256 "%archive%" ^| findstr /C:"SHA256 for data:"') do (
    set "contentHash=%%a"
)
:: Trim leading/trailing spaces and remove potential dash suffix (e.g. -00000000)
set "contentHash=%contentHash: =%"
for /f "tokens=1 delims=-" %%g in ("%contentHash%") do set "contentHash=%%g"

if not "%contentHash%"=="" (
    echo content:%contentHash%>>"%archive%.sha256"
)

echo [SUCCESS] Created %archive%.sha256
