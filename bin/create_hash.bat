@echo off
set "archive=%~1"
if "%~1"=="" (echo Usage: create_hash.bat [archive.zip/7z] & exit /b 1)

:: Generate SHA256 and output: [hash] [filename]
:: Split-Path -Leaf ensures only the filename is stored, not the full path.
powershell -Command "$hash = (Get-FileHash '%archive%' -Algorithm SHA256).Hash.ToLower(); \"$hash  $((Split-Path -Leaf '%archive%'))\"" > "%archive%.sha256"

echo [SUCCESS] Created %archive%.sha256
