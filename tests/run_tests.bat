@echo off
setlocal enabledelayedexpansion

echo [TEST] Starting Data Integrity Tool Tests...
set "TEMP_DIR=test_temp"
if exist "%TEMP_DIR%" rd /s /q "%TEMP_DIR%"
mkdir "%TEMP_DIR%"
cd "%TEMP_DIR%"

:: Create dummy files
echo content 1 > f1.txt
echo content 2 > f2.txt

:: Test 1: Basic Hash Creation and Verification
echo [TEST 1] Basic Hash Creation and Verification...
call ..\bin\create_hash.bat f1.txt > nul 2>&1
if not exist f1.txt.sha256 (echo [FAIL] Hash file not created & exit /b 1)
call ..\bin\verify_hash.bat f1.txt f1.txt.sha256 > nul 2>&1
if %errorlevel% neq 0 (echo [FAIL] Verification failed & exit /b 1)
echo [PASS] Basic test successful.

:: Test 2: Content Hash Stability (Re-zipped)
echo [TEST 2] Content Hash Stability (Re-zipped)...
7z a test_v1.zip f1.txt f2.txt > nul
call ..\bin\create_hash.bat test_v1.zip > nul
:: Re-zip with different settings (store only)
7z a -mx=0 test_v2.zip f1.txt f2.txt > nul
call ..\bin\verify_hash.bat test_v2.zip test_v1.zip.sha256 > nul
if %errorlevel% neq 0 (echo [FAIL] Content hash mismatch for re-zipped file & exit /b 1)
echo [PASS] Content hash stable across re-zipping.

:: Test 3: Content Hash Stability (Cross-Format)
echo [TEST 3] Content Hash Stability (Cross-Format)...
7z a test_v3.7z f1.txt f2.txt > nul
call ..\bin\verify_hash.bat test_v3.7z test_v1.zip.sha256 > nul
if %errorlevel% neq 0 (echo [FAIL] Content hash mismatch for cross-format & exit /b 1)
echo [PASS] Content hash stable across formats (ZIP -> 7z).

:: Test 4: Corruption Detection
echo [TEST 4] Corruption Detection...
echo corrupted > f1.txt
7z a test_corrupt.zip f1.txt f2.txt > nul
call ..\bin\verify_hash.bat test_corrupt.zip test_v1.zip.sha256 > nul
if %errorlevel% equ 0 (echo [FAIL] Failed to detect corruption & exit /b 1)
echo [PASS] Corruption correctly detected.

cd ..
rd /s /q "%TEMP_DIR%"
echo [SUCCESS] All tests passed!
exit /b 0
