#!/bin/bash
ARCHIVE=$1
if [ -z "$ARCHIVE" ]; then echo "Usage: ./create_hash.sh [archive.zip/7z]"; exit 1; fi

# Standard sha256sum works for any file type
sha256sum "$ARCHIVE" > "$ARCHIVE.sha256"

# Generate "Content Hash" based on internal file CRCs
# We list files, extract Path and CRC, sort them to be deterministic, and hash the result.
CONTENT_INFO=$(7z l -slt "$ARCHIVE" | grep -E "^Path = |^CRC = ")
if [ ! -z "$CONTENT_INFO" ]; then
    CONTENT_HASH=$(echo "$CONTENT_INFO" | sort | sha256sum | awk '{print $1}')
    echo "content:$CONTENT_HASH" >> "$ARCHIVE.sha256"
fi

echo "[SUCCESS] Created $ARCHIVE.sha256"
