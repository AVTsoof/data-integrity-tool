@echo off
set "archive=%~1"
set "hashfile=%~2"
if "%~2"=="" (echo Usage: verify_hash.bat [archive] [hashfile] & exit /b 1)

:: Extract the expected hash (first token) from the hash file
for /f "tokens=1" %%a in (%hashfile%) do set expected_hash=%%a

:: Calculate the actual hash of the provided archive
for /f "tokens=1" %%a in ('powershell -command "Get-FileHash '%archive%' -Algorithm SHA256 | Select-Object -ExpandProperty Hash"') do set actual_hash=%%a

if /i "%actual_hash%"=="%expected_hash%" (
    echo [PASS] %archive% is valid.
) else (
    echo [FAIL] %archive% IS CORRUPT!
    echo Expected: %expected_hash%
    echo Actual:   %actual_hash%
    exit /b 1
)
