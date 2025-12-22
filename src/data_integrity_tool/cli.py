import argparse
import sys
from pathlib import Path
from colorama import init, Fore, Style
from .core import (
    create_hashes, 
    verify_archive_integrity, 
    get_archive_content_hash, 
    calculate_file_hash, 
    find_hash_files,
    verify_layers,
    ArchiveError,
    DependencyError
)

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
    except (ArchiveError, DependencyError) as e:
        print_color(f"[ERROR] Failed to check archive: {e}", RED)
        sys.exit(1)
    except Exception as e:
        print_color(f"[ERROR] Unexpected error checking archive: {e}", RED)
        sys.exit(1)

    print_color("Generating Archive File Hash...", CYAN)
    try:
        hash_file, content_hash_file = create_hashes(archive_path)
        print_color(f"[SUCCESS] Created {hash_file.name}", GREEN)
        
        print_color("Generating Content Hash (Internal 7z data)...", CYAN)
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

    # Perform verification using core logic
    results = verify_layers(archive_path, hash_file, content_hash_file)

    # Output results
    
    # --- 1. Data Structure (Layer 2) ---
    l2 = results["layer2"]
    if l2["status"] == "PASSED":
        print_color("[PASS] 1. Data Structure: 7z internal integrity is OK.", GREEN)
        layer2_status = f"{GREEN}PASSED (Valid Structure){NC}"
    elif l2["status"] == "FAILED":
         print_color(f"[FAIL] 1. Data Structure: {l2['message']}", RED)
         layer2_status = f"{RED}FAILED (Corrupted Structure){NC}"
    else:
         print_color(f"[ERROR] 1. Data Structure: {l2['message']}", RED)
         layer2_status = f"{RED}ERROR{NC}"

    # --- 2. Content Authenticity (Layer 3) ---
    l3 = results["layer3"]
    if l3["status"] == "PASSED":
        print_color("[PASS] 2. Content Authenticity: Content hash matches.", GREEN)
        layer3_status = f"{GREEN}PASSED (Matches Original){NC}"
    elif l3["status"] == "FAILED":
        print_color("[FAIL] 2. Content Authenticity: Content hash mismatch!", RED)
        if l3["details"]:
            print(f"        Expected: {RED}{l3['details']['expected']}{NC}")
            print(f"        Actual:   {RED}{l3['details']['actual']}{NC}")
        layer3_status = f"{RED}FAILED (Content Mismatch / Tampered){NC}"
    elif l3["status"] == "ERROR":
        print_color(f"[ERROR] 2. Content Authenticity: Check failed: {l3['message']}", RED)
        layer3_status = f"{RED}ERROR{NC}"
    else: # SKIPPED
        print_color(f"[SKIP] 2. Content Authenticity: {l3['message']}", YELLOW)
        layer3_status = f"{YELLOW}SKIPPED ({l3['message']}){NC}"

    # --- 3. Archive File (Layer 1) ---
    l1 = results["layer1"]
    if l1["status"] == "PASSED":
        print_color("[PASS] 3. Archive File: Hash matches.", GREEN)
        layer1_status = f"{GREEN}PASSED (Original File){NC}"
    elif l1["status"] == "WARNING":
        print_color("[WARN] 3. Archive File: Hash mismatch.", YELLOW)
        if l1["details"]:
            print(f"        Expected: {RED}{l1['details']['expected']}{NC}")
            print(f"        Actual:   {RED}{l1['details']['actual']}{NC}")
        layer1_status = f"{RED}WARNING (Re-archived / Modified){NC}"
    elif l1["status"] == "ERROR":
         print_color(f"[ERROR] 3. Archive File: Check failed: {l1['message']}", RED)
         layer1_status = f"{RED}ERROR{NC}"
    else: # SKIPPED
        print_color(f"[SKIP] 3. Archive File: {l1['message']}", YELLOW)
        layer1_status = f"{YELLOW}SKIPPED ({l1['message']}){NC}"

    print("-" * 40)
    print("\n" + BLUE + f"Verification Summary for \"{archive_path.name}\":" + NC)
    print(f"  1. Data Structure:      {layer2_status}")
    print(f"  2. Content Authenticity:{layer3_status}")
    print(f"  3. Archive File:        {layer1_status}\n")

    if "FAILED" in layer2_status or "FAILED" in layer3_status or "ERROR" in layer2_status:
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
