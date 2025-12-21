#!/bin/bash
ARCHIVE=$1
HASH_FILE=$2
EXPLICIT_CONTENT_HASH_FILE=$3

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

if [ -z "$ARCHIVE" ]; then echo "Usage: ./verify_hash.sh [archive] [optional_hashfile] [optional_contenthashfile]"; exit 1; fi

# Automatic Discovery: If HASH_FILE is not provided, look for [archive].sha256
if [ -z "$HASH_FILE" ]; then
    if [ -f "$ARCHIVE.sha256" ]; then
        HASH_FILE="$ARCHIVE.sha256"
        echo -e "${CYAN}[INFO]${NC}  Automatically discovered archive hash file: ${BLUE}$HASH_FILE${NC}"
    fi
fi

# Determine if the provided hashfile is a standard .sha256 or a .content.sha256
IS_CONTENT_FILE=0
if [[ "$HASH_FILE" == *".content.sha256"* ]]; then IS_CONTENT_FILE=1; fi

LAYER1_STATUS="${YELLOW}SKIPPED (No hash file)${NC}"
LAYER2_STATUS="${YELLOW}PENDING${NC}"
LAYER3_STATUS="${YELLOW}SKIPPED (No hash file)${NC}"

# Layer 1: Archive File Hash
if [ "$IS_CONTENT_FILE" -eq 0 ]; then
    if [ ! -f "$HASH_FILE" ]; then
        echo -e "${YELLOW}[SKIP]${NC}  Layer 1: Archive hash file not found: $HASH_FILE"
        LAYER1_STATUS="${YELLOW}SKIPPED (File not found: $HASH_FILE)${NC}"
    else
        echo -e "${CYAN}[INFO]${NC}  Layer 1: Checking Archive File Hash ($HASH_FILE)..."
        EXPECTED_HASH=$(head -n 1 "$HASH_FILE" | awk '{print $1}')
        ACTUAL_HASH=$(sha256sum "$ARCHIVE" | awk '{print $1}')
        
        if [ "$EXPECTED_HASH" != "$ACTUAL_HASH" ]; then
            echo -e "${YELLOW}[WARN]${NC}  Layer 1: Archive file hash mismatch."
            echo -e "        Expected: ${RED}$EXPECTED_HASH${NC}"
            echo -e "        Actual:   ${RED}$ACTUAL_HASH${NC}"
            LAYER1_STATUS="${RED}WARNING (Hash mismatch)${NC}"
        else
            echo -e "${GREEN}[PASS]${NC}  Layer 1: Archive file hash matches."
            LAYER1_STATUS="${GREEN}PASSED${NC}"
        fi
    fi
else
    LAYER1_STATUS="${YELLOW}SKIPPED (Content hash file provided instead)${NC}"
fi

# Layer 2: 7z Internal Integrity (CRC)
echo -e "${CYAN}[INFO]${NC}  Layer 2: Checking 7z Internal Integrity (CRC)..."
7z t "$ARCHIVE" > /dev/null
if [ $? -ne 0 ]; then
    echo -e "${RED}[FAIL]${NC}  Layer 2: 7z integrity test failed (CRC mismatch or corrupt archive)."
    LAYER2_STATUS="${RED}FAILED${NC}"
    # Even if Layer 2 fails, we might want to see the report, but usually we exit
    echo ""
    echo -e "${BLUE}Verification Summary for \"$ARCHIVE\":${NC}"
    echo -e "  Layer 1 (Archive Hash): $LAYER1_STATUS"
    echo -e "  Layer 2 (7z CRC):      $LAYER2_STATUS"
    exit 1
fi
echo -e "${GREEN}[PASS]${NC}  Layer 2: 7z internal integrity is OK."
LAYER2_STATUS="${GREEN}PASSED${NC}"

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
    echo -e "${CYAN}[INFO]${NC}  Layer 3: Checking Content Hash ($CONTENT_HASH_FILE)..."
    EXPECTED_CONTENT_HASH=$(cat "$CONTENT_HASH_FILE" | tr -d ' ')
    ACTUAL_CONTENT_HASH=$(7z t -scrcSHA256 "$ARCHIVE" | grep "SHA256 for data:" | cut -d':' -f2 | tr -d ' ' | cut -d'-' -f1)

    if [ "$EXPECTED_CONTENT_HASH" != "$ACTUAL_CONTENT_HASH" ]; then
        echo -e "${RED}[FAIL]${NC}  Layer 3: Content hash mismatch!"
        echo -e "        Expected: ${RED}$EXPECTED_CONTENT_HASH${NC}"
        echo -e "        Actual:   ${RED}$ACTUAL_CONTENT_HASH${NC}"
        LAYER3_STATUS="${RED}FAILED (Hash mismatch)${NC}"
        echo ""
        echo -e "${BLUE}Verification Summary for \"$ARCHIVE\":${NC}"
        echo -e "  Layer 1 (Archive Hash): $LAYER1_STATUS"
        echo -e "  Layer 2 (7z CRC):      $LAYER2_STATUS"
        echo -e "  Layer 3 (Content Hash): $LAYER3_STATUS"
        exit 1
    fi
    echo -e "${GREEN}[PASS]${NC}  Layer 3: Content hash matches."
    LAYER3_STATUS="${GREEN}PASSED${NC}"
else
    echo -e "${YELLOW}[SKIP]${NC}  Layer 3: No content hash file found."
    LAYER3_STATUS="${YELLOW}SKIPPED (File not found)${NC}"
fi

# Check for skips
ANY_SKIPPED=0
if [[ "$LAYER1_STATUS" == *"SKIPPED"* ]]; then ANY_SKIPPED=1; fi
if [[ "$LAYER2_STATUS" == *"SKIPPED"* ]]; then ANY_SKIPPED=1; fi
if [[ "$LAYER3_STATUS" == *"SKIPPED"* ]]; then ANY_SKIPPED=1; fi

echo ""
echo -e "${BLUE}Verification Summary for \"$ARCHIVE\":${NC}"
echo -e "  Layer 1 (Archive Hash): $LAYER1_STATUS"
echo -e "  Layer 2 (7z CRC):      $LAYER2_STATUS"
echo -e "  Layer 3 (Content Hash): $LAYER3_STATUS"
echo ""

if [ "$ANY_SKIPPED" -eq 1 ]; then
    echo -e "${YELLOW}[WARN]${NC} Verification passed, but some layers were skipped."
else
    echo -e "${GREEN}[SUCCESS]${NC} All integrity layers passed."
fi
exit 0
