@echo off
setlocal enabledelayedexpansion

echo ============================================================
echo 🧪 ENHANCED DATA INTEGRITY TEST SUITE
echo ============================================================

:: Setup
if exist test_data rd /s /q test_data
mkdir test_data
echo "Hello World" > test_data\file1.txt
echo "Data Integrity" > test_data\file2.txt

:: 1. Create Archive and Hashes
echo [TEST 1] Creating Archive and Hashes...
7z a test_archive.zip .\test_data\* >nul
call bin\create_hash.bat test_archive.zip

if not exist test_archive.zip.sha256 (echo [FAIL] .sha256 missing & exit /b 1)
if not exist test_archive.zip.content.sha256 (echo [FAIL] .content.sha256 missing & exit /b 1)
echo [PASS] Hashes created successfully.

:: 2. Verify Valid Archive
echo [TEST 2] Verifying Valid Archive (All Layers)...
call bin\verify_hash.bat test_archive.zip test_archive.zip.sha256
if %errorlevel% neq 0 (echo [FAIL] Valid archive failed verification & exit /b 1)
echo [PASS] Valid archive passed.

:: 3. Verify with Content Hash File Only
echo [TEST 3] Verifying with Content Hash File Only...
call bin\verify_hash.bat test_archive.zip test_archive.zip.content.sha256
if %errorlevel% neq 0 (echo [FAIL] Content-only verification failed & exit /b 1)
echo [PASS] Content-only verification passed.

:: 3c. Verify with Automatic Hash Discovery
echo [TEST 3c] Verifying with Automatic Hash Discovery...
call bin\verify_hash.bat test_archive.zip
if %errorlevel% neq 0 (echo [FAIL] Automatic discovery verification failed & exit /b 1)
echo [PASS] Automatic discovery verification passed.

:: 4. Detect Re-zipped Archive (Layer 1 Fail, Layer 3 Pass)
echo [TEST 4] Detecting Re-zipped Archive...
:: Re-zip (changes file hash)
del test_archive.zip
7z a test_archive.zip .\test_data\* -mx=9 >nul

:: The original.sha256 still contains the OLD file hash.
:: But verify_hash.bat will look for test_archive.zip.content.sha256 automatically.
:: So we need to provide the OLD .sha256 file as the argument.
move original.sha256 test_archive.zip.sha256 >nul
move original.content.sha256 test_archive.zip.content.sha256 >nul

echo [INFO] Expecting Layer 1 FAIL, Layer 2 PASS, Layer 3 PASS...
call bin\verify_hash.bat test_archive.zip test_archive.zip.sha256
if %errorlevel% equ 0 (
    echo [PASS] Re-zipped archive correctly handled.
) else (
    echo [FAIL] Re-zipped archive should have passed Layer 3.
    exit /b 1
)

:: 5. Detect Corruption (Layer 2 Fail)
echo [TEST 5] Detecting Corruption (Layer 2 Fail)...
:: Corrupt the file by overwriting the first few bytes with zeros
powershell -command "$bytes = [System.IO.File]::ReadAllBytes('test_archive.zip'); for($i=0; $i -lt 10; $i++){ $bytes[$i] = 0 }; [System.IO.File]::WriteAllBytes('test_archive.zip', $bytes)"

echo [INFO] Expecting Layer 2 FAIL...
call bin\verify_hash.bat test_archive.zip test_archive.zip.sha256
if %errorlevel% neq 0 (
    echo [PASS] Corruption detected successfully.
) else (
    echo [FAIL] Corruption was NOT detected!
    exit /b 1
)

:: Cleanup
echo [INFO] Cleaning up...
if exist test_archive.zip del test_archive.zip
if exist test_archive.zip.sha256 del test_archive.zip.sha256
if exist test_archive.zip.content.sha256 del test_archive.zip.content.sha256
if exist original.sha256 del original.sha256
if exist original.content.sha256 del original.content.sha256
rd /s /q test_data

echo ============================================================
echo ✅ ALL TESTS PASSED SUCCESSFULLY!
echo ============================================================
