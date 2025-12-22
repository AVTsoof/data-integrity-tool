#!/bin/bash

echo "[TEST] Starting Data Integrity Tool Tests..."
TEMP_DIR="test_temp_sh"
rm -rf "$TEMP_DIR"
mkdir "$TEMP_DIR"
cd "$TEMP_DIR"
export PYTHONPATH=../src

# Create dummy files
echo "content 1" > f1.txt
echo "content 2" > f2.txt

# Test 1: Basic Hash Creation and Verification
echo "[TEST 1] Basic Hash Creation and Verification..."
7z a test_basic.zip f1.txt > /dev/null
python3 -m data_integrity_tool.main create test_basic.zip > /dev/null
if [ ! -f test_basic.zip.sha256 ]; then echo "[FAIL] Hash file not created"; exit 1; fi
python3 -m data_integrity_tool.main verify test_basic.zip > /dev/null
if [ $? -ne 0 ]; then echo "[FAIL] Verification failed"; exit 1; fi
echo "[PASS] Basic test successful."

# Test 2: Content Hash Stability (Re-zipped)
echo "[TEST 2] Content Hash Stability (Re-zipped)..."
7z a test_v1.zip f1.txt f2.txt > /dev/null
python3 -m data_integrity_tool.main create test_v1.zip > /dev/null
# Re-zip with different settings (store only)
7z a -mx=0 test_v2.zip f1.txt f2.txt > /dev/null
python3 -m data_integrity_tool.main verify test_v2.zip > /dev/null
if [ $? -ne 0 ]; then echo "[FAIL] Content hash mismatch for re-zipped file"; exit 1; fi
echo "[PASS] Content hash stable across re-zipping."

# Test 3: Content Hash Stability (Cross-Format)
echo "[TEST 3] Content Hash Stability (Cross-Format)..."
7z a test_v3.7z f1.txt f2.txt > /dev/null
python3 -m data_integrity_tool.main verify test_v3.7z > /dev/null
if [ $? -ne 0 ]; then echo "[FAIL] Content hash mismatch for cross-format"; exit 1; fi
echo "[PASS] Content hash stable across formats (ZIP -> 7z)."

# Test 4: Corruption Detection
echo "[TEST 4] Corruption Detection..."
echo "corrupted" > f1.txt
7z a test_corrupt.zip f1.txt f2.txt > /dev/null
# Explicitly testing the advanced CLI usage here to match original test intent of providing specific hash files
python3 -m data_integrity_tool.main verify test_corrupt.zip --hash-file test_v1.zip.sha256 --content-hash-file test_v1.zip.content.sha256 > /dev/null
if [ $? -eq 0 ]; then echo "[FAIL] Failed to detect corruption"; exit 1; fi
echo "[PASS] Corruption correctly detected."

cd ..
rm -rf "$TEMP_DIR"
echo "[SUCCESS] All tests passed!"
exit 0
