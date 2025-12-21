@echo off
set "archive=%~1"
if "%~1"=="" (echo Usage: create_hash.bat [archive.zip/7z] & exit /b 1)

:: Generate SHA256 of the archive file itself
powershell -Command "$hash = (Get-FileHash '%archive%' -Algorithm SHA256).Hash.ToLower(); \"$hash  $((Split-Path -Leaf '%archive%'))\"" > "%archive%.sha256"

:: Generate "Content Hash" based on internal file CRCs
:: We list files, extract Path and CRC, sort them to be deterministic, and hash the result.
powershell -Command ^
    "$contentInfo = 7z l -slt '%archive%' | Select-String '^Path = |^CRC = ' | ForEach-Object { $_.ToString() }; " ^
    "if ($contentInfo) { " ^
    "  $contentHash = [BitConverter]::ToString([System.Security.Cryptography.SHA256]::Create().ComputeHash([System.Text.Encoding]::UTF8.GetBytes(($contentInfo | Sort-Object | Out-String)))).Replace('-', '').ToLower(); " ^
    "  Add-Content -Path '%archive%.sha256' -Value \"content:$contentHash\" " ^
    "}"

echo [SUCCESS] Created %archive%.sha256
