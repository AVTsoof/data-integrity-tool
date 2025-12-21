#!/bin/bash
ARCHIVE=$1
HASH_FILE=$2
if [ -z "$HASH_FILE" ]; then echo "Usage: ./verify_hash.sh [archive] [hashfile]"; exit 1; fi

# Extract expected archive hash (first column of first line)
EXPECTED_HASH=$(head -n 1 "$HASH_FILE" | awk '{print $1}')

# Extract expected content hash (line starting with content:)
EXPECTED_CONTENT_HASH=$(grep "^content:" "$HASH_FILE" | cut -d':' -f2)

# Calculate actual hash
ACTUAL_HASH=$(sha256sum "$ARCHIVE" | awk '{print $1}')

if [ "$EXPECTED_HASH" == "$ACTUAL_HASH" ]; then
    echo "[PASS] $ARCHIVE is valid (File hash matches)."
    exit 0
fi

# If archive hash fails, check content hash
if [ -z "$EXPECTED_CONTENT_HASH" ]; then
    echo "[FAIL] $ARCHIVE IS CORRUPT! (File hash mismatch and no content hash found)"
    echo "Expected: $EXPECTED_HASH"
    echo "Actual:   $ACTUAL_HASH"
    exit 1
fi

echo "[INFO] File hash mismatch. Checking internal data integrity..."

ACTUAL_CONTENT_HASH=$(7z l -slt "$ARCHIVE" | grep -E "^Path = |^CRC = " | sort | sha256sum | awk '{print $1}')

if [ "$EXPECTED_CONTENT_HASH" == "$ACTUAL_CONTENT_HASH" ]; then
    echo "[PASS] $ARCHIVE data is intact (Content hash matches)."
    echo "[NOTE] The archive file itself has changed (e.g. re-zipped), but the internal data is identical."
    exit 0
else
    echo "[FAIL] $ARCHIVE IS CORRUPT! (Both file and content hashes mismatch)"
    echo "Expected Content Hash: $EXPECTED_CONTENT_HASH"
    echo "Actual Content Hash:   $ACTUAL_CONTENT_HASH"
    exit 1
fi
