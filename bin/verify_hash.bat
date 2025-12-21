@echo off
setlocal enabledelayedexpansion
set "archive=%~1"
set "hashfile=%~2"
set "explicit_content_hashfile=%~3"

:: Define colors via ESC code
for /F %%a in ('echo prompt $E ^| cmd') do set "ESC=%%a"
set "RED=!ESC![31m"
set "GREEN=!ESC![32m"
set "YELLOW=!ESC![33m"
set "BLUE=!ESC![34m"
set "CYAN=!ESC![36m"
set "NC=!ESC![0m"

if "%~1"=="" (
    echo Usage: verify_hash.bat [archive] [optional_hashfile] [optional_contenthashfile]
    exit /b 1
)

REM Automatic Discovery: If hashfile is not provided, look for [archive].sha256
if not "%hashfile%"=="" goto :skip_discovery
if exist "%archive%.sha256" (
    set "hashfile=%archive%.sha256"
    echo !CYAN![INFO]!NC!  Automatically discovered archive hash file: !BLUE!!hashfile!!NC!
)
:skip_discovery

REM Determine if the provided hashfile is a standard .sha256 or a .content.sha256
set "is_content_file=0"
echo "%hashfile%" | findstr /i ".content.sha256" >nul && set "is_content_file=1"

set "layer1_status=!YELLOW!SKIPPED (No hash file)!NC!"
set "layer2_status=!YELLOW!PENDING!NC!"
set "layer3_status=!YELLOW!SKIPPED (No hash file)!NC!"

REM Layer 1: Archive File Hash
if "%is_content_file%"=="1" (
    set "layer1_status=!YELLOW!SKIPPED (Content hash file provided instead)!NC!"
    goto :layer2
)

if not exist "%hashfile%" (
    echo !YELLOW![SKIP]!NC!  Layer 1: Archive hash file not found: %hashfile%
    set "layer1_status=!YELLOW!SKIPPED (File not found: %hashfile%)!NC!"
    goto :layer2
)

echo !CYAN![INFO]!NC!  Layer 1: Checking Archive File Hash (%hashfile%)...
for /f "usebackq tokens=1" %%a in ("%hashfile%") do set "expected_hash=%%a"
REM Get actual hash using a temp file to avoid for-loop parsing issues
powershell -command "(Get-FileHash '%archive%' -Algorithm SHA256).Hash.ToLower()" > "%temp%\actual_hash.txt"
set /p actual_hash=<"%temp%\actual_hash.txt"
del "%temp%\actual_hash.txt"

if /i not "!actual_hash!"=="!expected_hash!" (
    echo !YELLOW![WARN]!NC!  Layer 1: Archive file hash mismatch.
    echo         Expected: !RED!!expected_hash!!NC!
    echo         Actual:   !RED!!actual_hash!!NC!
    set "layer1_status=!RED!WARNING (Hash mismatch)!NC!"
) else (
    echo !GREEN![PASS]!NC!  Layer 1: Archive file hash matches.
    set "layer1_status=!GREEN!PASSED!NC!"
)

:layer2
REM Layer 2: 7z Internal CRC Check Default Validation
echo !CYAN![INFO]!NC!  Layer 2: Checking 7z Internal Integrity CRC...
7z t "%archive%" >nul 2>&1
if errorlevel 1 goto :layer2_fail
echo !GREEN![PASS]!NC!  Layer 2: 7z internal integrity is OK.
set "layer2_status=!GREEN!PASSED!NC!"
goto :layer3_start

:layer2_fail
echo !RED![FAIL]!NC!  Layer 2: 7z integrity test failed - CRC mismatch or corrupt archive.
set "layer2_status=!RED!FAILED!NC!"
echo.
echo !BLUE!Verification Summary for "!archive!":!NC!
echo   Layer 1 (Archive Hash): !layer1_status!
echo   Layer 2 (7z CRC):      !layer2_status!
exit /b 1

:layer3_start

REM Layer 3: Content Hash Optional
set "content_hash_file="
if not "%explicit_content_hashfile%"=="" set "content_hash_file=%explicit_content_hashfile%"
if not "%content_hash_file%"=="" goto :check_content_file
if "%is_content_file%"=="1" set "content_hash_file=%hashfile%"
if not "%content_hash_file%"=="" goto :check_content_file
if exist "%archive%.content.sha256" set "content_hash_file=%archive%.content.sha256"

:check_content_file
if not "%content_hash_file%"=="" goto :run_layer3
echo !YELLOW![SKIP]!NC!  Layer 3: No content hash file found.
set "layer3_status=!YELLOW!SKIPPED (File not found)!NC!"
goto :success

:run_layer3
echo !CYAN![INFO]!NC!  Layer 3: Checking Content Hash (%content_hash_file%)...
set /p expected_content_hash=<"%content_hash_file%"
REM Trim spaces from expected_content_hash
set "expected_content_hash=!expected_content_hash: =!"

REM Get actual content hash using a temp file
7z t -scrcSHA256 "%archive%" > "%temp%\7z_output.txt" 2>&1
set "actual_content_hash="
for /f "tokens=2 delims=:" %%a in ('findstr /C:"SHA256 for data:" "%temp%\7z_output.txt"') do set "actual_content_hash=%%a"
del "%temp%\7z_output.txt"

if not "!actual_content_hash!"=="" goto :layer3_check_match
echo !RED![FAIL]!NC!  Layer 3: Could not extract content hash from 7z output.
set "layer3_status=!RED!FAILED (Extraction error)!NC!"
echo.
echo !BLUE!Verification Summary for "!archive!":!NC!
echo   Layer 1 (Archive Hash): !layer1_status!
echo   Layer 2 (7z CRC):      !layer2_status!
echo   Layer 3 (Content Hash): !layer3_status!
exit /b 1

:layer3_check_match
set "actual_content_hash=!actual_content_hash: =!"
for /f "tokens=1 delims=-" %%g in ("!actual_content_hash!") do set "actual_content_hash=%%g"

if /i "!actual_content_hash!"=="!expected_content_hash!" goto :layer3_pass
echo !RED![FAIL]!NC!  Layer 3: Content hash mismatch!
echo         Expected: !RED!!expected_content_hash!!NC!
echo         Actual:   !RED!!actual_content_hash!!NC!
set "layer3_status=!RED!FAILED (Hash mismatch)!NC!"
echo.
echo !BLUE!Verification Summary for "!archive!":!NC!
echo   Layer 1 (Archive Hash): !layer1_status!
echo   Layer 2 (7z CRC):      !layer2_status!
echo   Layer 3 (Content Hash): !layer3_status!
exit /b 1

:layer3_pass
echo !GREEN![PASS]!NC!  Layer 3: Content hash matches.
set "layer3_status=!GREEN!PASSED!NC!"

:success
REM Check for skips
set "any_skipped=0"
echo "!layer1_status!" | findstr "SKIPPED" >nul && set "any_skipped=1"
echo "!layer2_status!" | findstr "SKIPPED" >nul && set "any_skipped=1"
echo "!layer3_status!" | findstr "SKIPPED" >nul && set "any_skipped=1"

echo.
echo !BLUE!Verification Summary for "%archive%":!NC!
echo   Layer 1 (Archive Hash): !layer1_status!
echo   Layer 2 (7z CRC):      !layer2_status!
echo   Layer 3 (Content Hash): !layer3_status!
echo.

if "!any_skipped!"=="1" (
    echo !YELLOW![WARN]!NC! Verification passed, but some layers were skipped.
) else (
    echo !GREEN![SUCCESS]!NC! All integrity layers passed.
)
exit /b 0
