@echo off
setlocal enabledelayedexpansion
set "archive=%~1"
set "hashfile=%~2"
set "explicit_content_hashfile=%~3"

if "%~1"=="" (echo Usage: verify_hash.bat [archive] [optional_hashfile] [optional_contenthashfile] & exit /b 1)

:: Automatic Discovery: If hashfile is not provided, look for [archive].sha256
if "%hashfile%"=="" (
    if exist "%archive%.sha256" (
        set "hashfile=%archive%.sha256"
        echo [INFO] Automatically discovered hash file: !hashfile!
    )
)

:: Determine if the provided hashfile is a standard .sha256 or a .content.sha256
set "is_content_file=0"
echo "%hashfile%" | findstr /i ".content.sha256" >nul && set "is_content_file=1"

:: Layer 1: Archive File Hash
if "%is_content_file%"=="1" goto :layer2
if not exist "%hashfile%" (
    echo [SKIP] Layer 1: Archive hash file not found: %hashfile%
    goto :layer2
)

echo [INFO] Layer 1: Checking Archive File Hash...
for /f "usebackq tokens=1" %%a in ("%hashfile%") do set "expected_hash=%%a"
:: Get actual hash using a temp file to avoid for-loop parsing issues
powershell -command "(Get-FileHash '%archive%' -Algorithm SHA256).Hash.ToLower()" > "%temp%\actual_hash.txt"
set /p actual_hash=<"%temp%\actual_hash.txt"
del "%temp%\actual_hash.txt"

if /i not "%actual_hash%"=="%expected_hash%" (
    echo [WARN] Layer 1: Archive file hash mismatch.
    echo Expected: %expected_hash%
    echo Actual:   %actual_hash%
) else (
    echo [PASS] Layer 1: Archive file hash matches.
)

:layer2
:: Layer 2: 7z Internal CRC Check Default Validation
echo [INFO] Layer 2: Checking 7z Internal Integrity CRC...
7z t "%archive%" >nul 2>&1
if %errorlevel% neq 0 (
    echo [FAIL] Layer 2: 7z integrity test failed - CRC mismatch or corrupt archive.
    exit /b 1
)
echo [PASS] Layer 2: 7z internal integrity is OK.

:layer3
:: Layer 3: Content Hash Optional
set "content_hash_file="
if not "%explicit_content_hashfile%"=="" (
    set "content_hash_file=%explicit_content_hashfile%"
) else if "%is_content_file%"=="1" (
    set "content_hash_file=%hashfile%"
) else (
    if exist "%archive%.content.sha256" set "content_hash_file=%archive%.content.sha256"
)

if "%content_hash_file%"=="" (
    echo [SKIP] Layer 3: No content hash file found.
    goto :success
)

echo [INFO] Layer 3: Checking Content Hash...
set /p expected_content_hash=<"%content_hash_file%"
:: Trim spaces from expected_content_hash
set "expected_content_hash=%expected_content_hash: =%"

:: Get actual content hash using a temp file
7z t -scrcSHA256 "%archive%" > "%temp%\7z_output.txt" 2>&1
for /f "tokens=2 delims=:" %%a in ('findstr /C:"SHA256 for data:" "%temp%\7z_output.txt"') do set "actual_content_hash=%%a"
del "%temp%\7z_output.txt"

set "actual_content_hash=%actual_content_hash: =%"
for /f "tokens=1 delims=-" %%g in ("%actual_content_hash%") do set "actual_content_hash=%%g"

if /i not "%actual_content_hash%"=="%expected_content_hash%" (
    echo [FAIL] Layer 3: Content hash mismatch!
    echo Expected: %expected_content_hash%
    echo Actual:   %actual_content_hash%
    exit /b 1
)
echo [PASS] Layer 3: Content hash matches.

:success
echo.
echo [SUCCESS] All active integrity layers passed for "%archive%".
exit /b 0
