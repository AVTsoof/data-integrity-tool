#!/bin/bash
ARCHIVE=$1
HASH_FILE=$2
if [ -z "$HASH_FILE" ]; then echo "Usage: ./verify_hash.sh [archive] [hashfile]"; exit 1; fi

# Extract hash from file (first column)
EXPECTED_HASH=$(awk '{print $1}' "$HASH_FILE")
# Calculate actual hash
ACTUAL_HASH=$(sha256sum "$ARCHIVE" | awk '{print $1}')

if [ "$EXPECTED_HASH" == "$ACTUAL_HASH" ]; then
    echo "[PASS] $ARCHIVE integrity verified."
else
    echo "[FAIL] Hash mismatch!"
    echo "Expected: $EXPECTED_HASH"
    echo "Actual:   $ACTUAL_HASH"
    exit 1
fi
