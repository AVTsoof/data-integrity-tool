#!/bin/bash
ARCHIVE=$1
if [ -z "$ARCHIVE" ]; then echo "Usage: ./create_hash.sh [archive.zip/7z]"; exit 1; fi

# Standard sha256sum works for any file type
sha256sum "$ARCHIVE" > "$ARCHIVE.sha256"

# Generate "Content Hash" based on internal file data
# We use 7z test command with -scrcSHA256 to get a stable hash of the contents.
CONTENT_HASH=$(7z t -scrcSHA256 "$ARCHIVE" | grep "SHA256 for data:" | cut -d':' -f2 | tr -d ' ' | cut -d'-' -f1)
if [ ! -z "$CONTENT_HASH" ]; then
    echo "content:$CONTENT_HASH" >> "$ARCHIVE.sha256"
fi

echo "[SUCCESS] Created $ARCHIVE.sha256"
