import argparse
import sys
from pathlib import Path
from colorama import init, Fore, Style
from .core import create_hashes, verify_archive_integrity, get_archive_content_hash, calculate_file_hash, find_hash_files

# Initialize colorama
init()

# Colors
RED = Fore.RED
GREEN = Fore.GREEN
YELLOW = Fore.YELLOW
BLUE = Fore.BLUE
CYAN = Fore.CYAN
NC = Style.RESET_ALL

def print_color(text: str, color: str = NC):
    # colorama handles stripping colors if not a tty or on Windows
    print(f"{color}{text}{NC}")

def cmd_create(args):
    archive_path = Path(args.archive)
    
    # Verify valid archive
    try:
        if not verify_archive_integrity(archive_path):
             print_color(f"[ERROR] '{archive_path}' is not a valid archive file.", RED)
             sys.exit(1)
    except Exception as e:
        print_color(f"[ERROR] Failed to check archive: {e}", RED)
        sys.exit(1)

    print_color("Layer 1: Generating Archive File Hash...", CYAN)
    try:
        hash_file, content_hash_file = create_hashes(archive_path)
        print_color(f"[SUCCESS] Created {hash_file.name}", GREEN)
        
        print_color("Layer 3: Generating Content Hash (Internal 7z data)...", CYAN)
        if content_hash_file:
            print_color(f"[SUCCESS] Created {content_hash_file.name}", GREEN)
        else:
            print_color("[WARN] Could not generate content hash (maybe not supported for this format).", YELLOW)

    except Exception as e:
        print_color(f"[ERROR] Failed to create hashes: {e}", RED)
        sys.exit(1)

def cmd_verify(args):
    archive_path = Path(args.archive)
    hash_file = Path(args.hash_file) if args.hash_file else None
    content_hash_file = Path(args.content_hash_file) if args.content_hash_file else None

    # Auto discovery
    found_hashes = find_hash_files(archive_path)
    
    if not hash_file and found_hashes['archive_hash']:
        hash_file = found_hashes['archive_hash']
        print_color(f"[INFO] Automatically discovered archive hash file: {hash_file.name}", CYAN)
    elif hash_file:
        print_color(f"[INFO] Using provided archive hash file: {hash_file.name}", CYAN)
    else:
        print_color("[INFO] No archive hash file found.", YELLOW)

    if not content_hash_file and found_hashes['content_hash']:
        content_hash_file = found_hashes['content_hash']
        print_color(f"[INFO] Automatically discovered content hash file: {content_hash_file.name}", CYAN)
    elif content_hash_file:
        print_color(f"[INFO] Using provided content hash file: {content_hash_file.name}", CYAN)
    else:
        print_color("[INFO] No content hash file found.", YELLOW)
    
    print("-" * 40)

    layer1_status = f"{YELLOW}SKIPPED (No hash file){NC}"
    layer2_status = f"{YELLOW}PENDING{NC}"
    layer3_status = f"{YELLOW}SKIPPED (No hash file){NC}"

    # Layer 1
    if hash_file:
        if not hash_file.exists():
             print_color(f"[SKIP] Layer 1: Archive hash file not found: {hash_file}", YELLOW)
             layer1_status = f"{YELLOW}SKIPPED (File not found){NC}"
        else:
            print_color(f"Layer 1: Checking Archive File Hash ({hash_file})...", CYAN)
            try:
                with open(hash_file, "r") as f:
                    expected_hash = f.read().split()[0].strip().lower()
                
                actual_hash = calculate_file_hash(archive_path)
                
                if expected_hash != actual_hash:
                    print_color("[WARN] Layer 1: Archive file hash mismatch.", YELLOW)
                    print(f"        Expected: {RED}{expected_hash}{NC}")
                    print(f"        Actual:   {RED}{actual_hash}{NC}")
                    layer1_status = f"{RED}WARNING (Hash mismatch){NC}"
                else:
                    print_color("[PASS] Layer 1: Archive file hash matches.", GREEN)
                    layer1_status = f"{GREEN}PASSED{NC}"
            except Exception as e:
                print_color(f"[ERROR] Layer 1 check failed: {e}", RED)
                layer1_status = f"{RED}ERROR{NC}"

    # Layer 2
    print_color("Layer 2: Checking 7z Internal Integrity (CRC)...", CYAN)
    try:
        if verify_archive_integrity(archive_path):
            print_color("[PASS] Layer 2: 7z internal integrity is OK.", GREEN)
            layer2_status = f"{GREEN}PASSED{NC}"
        else:
            print_color("[FAIL] Layer 2: 7z integrity test failed.", RED)
            layer2_status = f"{RED}FAILED{NC}"
            # Fail immediately on Layer 2? Shell script does.
            # But let's print summary first.
    except Exception as e:
        print_color(f"[FAIL] Layer 2: 7z integrity test failed with error: {e}", RED)
        layer2_status = f"{RED}FAILED{NC}"

    # Layer 3
    # Determine content hash file
    target_content_file = content_hash_file
    
    if target_content_file:
        print_color(f"Layer 3: Checking Content Hash ({target_content_file})...", CYAN)
        try:
            with open(target_content_file, "r") as f:
                expected_content = f.read().strip().lower()
            
            actual_content = get_archive_content_hash(archive_path)
            if actual_content:
                actual_content = actual_content.lower()
            
            if expected_content != actual_content:
                print_color("[FAIL] Layer 3: Content hash mismatch!", RED)
                print(f"        Expected: {RED}{expected_content}{NC}")
                print(f"        Actual:   {RED}{actual_content}{NC}")
                layer3_status = f"{RED}FAILED (Hash mismatch){NC}"
            else:
                print_color("[PASS] Layer 3: Content hash matches.", GREEN)
                layer3_status = f"{GREEN}PASSED{NC}"
        except Exception as e:
            print_color(f"[ERROR] Layer 3 check failed: {e}", RED)
            layer3_status = f"{RED}ERROR{NC}"
    else:
        print_color("[SKIP] Layer 3: No content hash file found.", YELLOW)
        layer3_status = f"{YELLOW}SKIPPED (File not found){NC}"

    print("\n" + BLUE + f"Verification Summary for \"{archive_path.name}\":" + NC)
    print(f"  Layer 1 (Archive Hash): {layer1_status}")
    print(f"  Layer 2 (7z CRC):      {layer2_status}")
    print(f"  Layer 3 (Content Hash): {layer3_status}\n")

    if "FAILED" in layer2_status or "FAILED" in layer3_status:
        sys.exit(1)
    
    if "WARNING" in layer1_status:
        print_color("[WARN] Verification passed, but with warnings.", YELLOW)
    elif "SKIPPED" in layer1_status or "SKIPPED" in layer2_status or "SKIPPED" in layer3_status:
        print_color("[WARN] Verification passed, but some layers were skipped.", YELLOW)
    else:
        print_color("[SUCCESS] All integrity layers passed.", GREEN)

def main():
    parser = argparse.ArgumentParser(description="Data Integrity Tool")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Create command
    create_parser = subparsers.add_parser("create", help="Create hashes for an archive")
    create_parser.add_argument("archive", help="Path to the archive file")

    # Verify command
    verify_parser = subparsers.add_parser("verify", help="Verify hashes for an archive")
    verify_parser.add_argument("archive", help="Path to the archive file")
    verify_parser.add_argument("--hash-file", help="Explicit path to archive hash file")
    verify_parser.add_argument("--content-hash-file", help="Explicit path to content hash file")

    args = parser.parse_args()

    if args.command == "create":
        cmd_create(args)
    elif args.command == "verify":
        cmd_verify(args)

if __name__ == "__main__":
    main()
