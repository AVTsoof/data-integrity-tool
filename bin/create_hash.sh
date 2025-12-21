#!/bin/bash
ARCHIVE=$1
if [ -z "$ARCHIVE" ]; then echo "Usage: ./create_hash.sh [archive.zip/7z]"; exit 1; fi

# Standard sha256sum works for any file type
sha256sum "$ARCHIVE" > "$ARCHIVE.sha256"
echo "[SUCCESS] Created $ARCHIVE.sha256"
