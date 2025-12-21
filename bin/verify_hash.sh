#!/bin/bash
ARCHIVE=$1
HASH_FILE=$2
EXPLICIT_CONTENT_HASH_FILE=$3

if [ -z "$ARCHIVE" ]; then echo "Usage: ./verify_hash.sh [archive] [optional_hashfile] [optional_contenthashfile]"; exit 1; fi

# Automatic Discovery: If HASH_FILE is not provided, look for [archive].sha256
if [ -z "$HASH_FILE" ]; then
    if [ -f "$ARCHIVE.sha256" ]; then
        HASH_FILE="$ARCHIVE.sha256"
        echo "[INFO] Automatically discovered hash file: $HASH_FILE"
    fi
fi

# Determine if the provided hashfile is a standard .sha256 or a .content.sha256
IS_CONTENT_FILE=0
if [[ "$HASH_FILE" == *".content.sha256"* ]]; then IS_CONTENT_FILE=1; fi

# Layer 1: Archive File Hash
if [ "$IS_CONTENT_FILE" -eq 0 ]; then
    if [ ! -f "$HASH_FILE" ]; then
        echo "[SKIP] Archive hash file not found: $HASH_FILE"
    else
        echo "[INFO] Layer 1: Checking Archive File Hash..."
        EXPECTED_HASH=$(head -n 1 "$HASH_FILE" | awk '{print $1}')
        ACTUAL_HASH=$(sha256sum "$ARCHIVE" | awk '{print $1}')
        
        if [ "$EXPECTED_HASH" != "$ACTUAL_HASH" ]; then
            echo "[WARN] Layer 1: Archive file hash mismatch."
            echo "Expected: $EXPECTED_HASH"
            echo "Actual:   $ACTUAL_HASH"
        else
            echo "[PASS] Layer 1: Archive file hash matches."
        fi
    fi
fi

# Layer 2: 7z Internal Integrity (CRC)
echo "[INFO] Layer 2: Checking 7z Internal Integrity (CRC)..."
7z t "$ARCHIVE" > /dev/null
if [ $? -ne 0 ]; then
    echo "[FAIL] Layer 2: 7z integrity test failed (CRC mismatch or corrupt archive)."
    exit 1
fi
echo "[PASS] Layer 2: 7z internal integrity is OK."

# Layer 3: Content Hash (Optional)
CONTENT_HASH_FILE=""
if [ ! -z "$EXPLICIT_CONTENT_HASH_FILE" ]; then
    CONTENT_HASH_FILE="$EXPLICIT_CONTENT_HASH_FILE"
elif [ "$IS_CONTENT_FILE" -eq 1 ]; then
    CONTENT_HASH_FILE="$HASH_FILE"
elif [ -f "$ARCHIVE.content.sha256" ]; then
    CONTENT_HASH_FILE="$ARCHIVE.content.sha256"
fi

if [ ! -z "$CONTENT_HASH_FILE" ]; then
    echo "[INFO] Layer 3: Checking Content Hash..."
    EXPECTED_CONTENT_HASH=$(cat "$CONTENT_HASH_FILE" | tr -d ' ')
    ACTUAL_CONTENT_HASH=$(7z t -scrcSHA256 "$ARCHIVE" | grep "SHA256 for data:" | cut -d':' -f2 | tr -d ' ' | cut -d'-' -f1)

    if [ "$EXPECTED_CONTENT_HASH" != "$ACTUAL_CONTENT_HASH" ]; then
        echo "[FAIL] Layer 3: Content hash mismatch!"
        echo "Expected: $EXPECTED_CONTENT_HASH"
        echo "Actual:   $ACTUAL_CONTENT_HASH"
        exit 1
    fi
    echo "[PASS] Layer 3: Content hash matches."
else
    echo "[SKIP] Layer 3: No content hash file found."
fi

echo ""
echo "[SUCCESS] All active integrity layers passed for \"$ARCHIVE\"."
exit 0
