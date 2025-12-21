@echo off
set "archive=%~1"
set "hashfile=%~2"
if "%~2"=="" (echo Usage: verify_hash.bat [archive] [hashfile] & exit /b 1)

:: Extract the expected archive hash (first token of first line)
for /f "tokens=1" %%a in (%hashfile%) do (
    set expected_hash=%%a
    goto :got_expected
)
:got_expected

:: Extract the expected content hash (line starting with content:)
set expected_content_hash=
for /f "tokens=2 delims=:" %%a in ('findstr /b "content:" "%hashfile%"') do set expected_content_hash=%%a

:: Calculate the actual hash of the provided archive
for /f "tokens=1" %%a in ('powershell -command "Get-FileHash '%archive%' -Algorithm SHA256 | Select-Object -ExpandProperty Hash"') do set actual_hash=%%a

if /i "%actual_hash%"=="%expected_hash%" goto :pass_file

:: If archive hash fails, check content hash
if "%expected_content_hash%"=="" goto :fail_no_content

echo [INFO] File hash mismatch. Checking internal data integrity...

for /f "tokens=1" %%a in ('powershell -Command "$contentInfo = 7z l -slt '%archive%' | Select-String '^Path = |^CRC = ' | ForEach-Object { $_.ToString() }; if ($contentInfo) { [BitConverter]::ToString([System.Security.Cryptography.SHA256]::Create().ComputeHash([System.Text.Encoding]::UTF8.GetBytes(($contentInfo | Sort-Object | Out-String)))).Replace('-', '').ToLower() }"') do set actual_content_hash=%%a

if /i "%actual_content_hash%"=="%expected_content_hash%" goto :pass_content

:fail_both
echo [FAIL] "%archive%" IS CORRUPT! (Both file and content hashes mismatch)
echo Expected Content Hash: %expected_content_hash%
echo Actual Content Hash:   %actual_content_hash%
exit /b 1

:fail_no_content
echo [FAIL] "%archive%" IS CORRUPT! (File hash mismatch and no content hash found)
echo Expected: %expected_hash%
echo Actual:   %actual_hash%
exit /b 1

:pass_file
echo [PASS] "%archive%" is valid (File hash matches).
exit /b 0

:pass_content
echo [PASS] "%archive%" data is intact (Content hash matches).
echo [NOTE] The archive file itself has changed (e.g. re-zipped), but the internal data is identical.
exit /b 0
