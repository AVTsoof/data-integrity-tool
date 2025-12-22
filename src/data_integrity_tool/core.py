import hashlib
import subprocess
import sys
import shutil
from pathlib import Path
from typing import Optional, Tuple

class IntegrityError(Exception):
    """Base exception for integrity tool errors."""
    pass

class ArchiveError(IntegrityError):
    """Raised when archive operations fail."""
    pass

class DependencyError(IntegrityError):
    """Raised when a required external dependency is missing."""
    pass

def calculate_file_hash(file_path: Path, algorithm: str = "sha256") -> str:
    """Calculates the hash of a file."""
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    hash_func = getattr(hashlib, algorithm)()
    with open(file_path, "rb") as f:
        # Read in chunks to handle large files
        for chunk in iter(lambda: f.read(4096), b""):
            hash_func.update(chunk)
    return hash_func.hexdigest()

def check_7z_installed() -> bool:
    """Checks if 7z is available in the PATH."""
    return shutil.which("7z") is not None

def ensure_7z_installed():
    """
    Checks if 7z is installed. Raises DependencyError if not.
    """
    if not check_7z_installed():
        raise DependencyError(
            "7-Zip (7z) is not installed or not found in your PATH.\n"
            "Please install it from https://www.7-zip.org/ and ensure it is added to your system PATH."
        )

def verify_archive_integrity(archive_path: Path) -> bool:
    """Verifies the internal integrity of the archive using '7z t'."""
    if not check_7z_installed():
        raise RuntimeError("7z is not installed or not in PATH.")
    
    try:
        # 7z t <archive>
        result = subprocess.run(
            ["7z", "t", str(archive_path)],
            capture_output=True,
            text=True,
            check=False
        )
        return result.returncode == 0
    except Exception as e:
        raise ArchiveError(f"Failed to run 7z: {e}")

def get_archive_content_hash(archive_path: Path) -> Optional[str]:
    """
    Gets the content hash of the archive using '7z t -scrcSHA256'.
    Parses the output for 'SHA256 for data:'.
    """
    ensure_7z_installed()

    try:
        # 7z t -scrcSHA256 <archive>
        result = subprocess.run(
            ["7z", "t", "-scrcSHA256", str(archive_path)],
            capture_output=True,
            text=True,
            check=False
        )
        
        if result.returncode != 0:
            raise ArchiveError(f"7z command failed: {result.stderr}")

        # Parse output
        # Look for "SHA256 for data: <hash>"
        for line in result.stdout.splitlines():
            if "SHA256 for data:" in line:
                # Line format: "SHA256 for data: <hash>"
                parts = line.split(":")
                if len(parts) >= 2:
                    return parts[1].strip().split()[0] # Take first part if there are extra spaces
        
        return None

    except Exception as e:
        raise ArchiveError(f"Failed to get content hash: {e}")

def create_hashes(archive_path: Path) -> Tuple[Path, Optional[Path]]:
    """
    Creates .sha256 and .content.sha256 files for the given archive.
    Returns paths to the created files.
    """
    if not archive_path.exists():
        raise FileNotFoundError(f"Archive not found: {archive_path}")

    # Layer 1: File Hash
    file_hash = calculate_file_hash(archive_path)
    # Standard: Append .sha256 to the full filename (e.g., test.zip -> test.zip.sha256)
    hash_file = archive_path.with_name(archive_path.name + ".sha256")
    
    with open(hash_file, "w") as f:
        f.write(f"{file_hash}  {archive_path.name}\n")

    # Layer 3: Content Hash
    content_hash = get_archive_content_hash(archive_path)
    content_hash_file = None
    if content_hash:
        content_hash_file = archive_path.with_name(archive_path.name + ".content.sha256")
        with open(content_hash_file, "w") as f:
            f.write(f"{content_hash}\n")
            
    return hash_file, content_hash_file

def find_hash_files(archive_path: Path) -> dict:
    """
    Finds existing hash files for the given archive.
    Returns a dictionary with paths or None.
    """
    result = {
        'archive_hash': None,
        'content_hash': None
    }
    
    # Layer 1: Archive Hash
    # Check for .sha256 extension
    potential_hash = archive_path.with_name(archive_path.name + ".sha256")
    if potential_hash.exists():
        result['archive_hash'] = potential_hash
        
    # Layer 3: Content Hash
    potential_content = archive_path.with_name(archive_path.name + ".content.sha256")
    if potential_content.exists():
        result['content_hash'] = potential_content
        
    return result

def verify_layers(archive_path: Path, hash_file: Optional[Path] = None, content_hash_file: Optional[Path] = None) -> dict:
    """
    Performs the 3-layer verification.
    
    Args:
        archive_path: Path to the archive.
        hash_file: Optional explicit path to the layer 1 hash file.
        content_hash_file: Optional explicit path to the layer 3 content hash file.
        
    Returns:
        A dictionary containing the status and details of each layer.
    """
    results = {
        "layer1": {"status": "SKIPPED", "message": "No hash file", "details": None},
        "layer2": {"status": "PENDING", "message": "", "details": None},
        "layer3": {"status": "SKIPPED", "message": "No content hash file", "details": None}
    }

    # Auto-discovery if not provided
    found_hashes = find_hash_files(archive_path)
    if not hash_file and found_hashes['archive_hash']:
        hash_file = found_hashes['archive_hash']
    if not content_hash_file and found_hashes['content_hash']:
        content_hash_file = found_hashes['content_hash']

    # Layer 1: Archive Hash
    if hash_file:
        if not hash_file.exists():
             results["layer1"] = {"status": "SKIPPED", "message": "File not found", "details": str(hash_file)}
        else:
            try:
                with open(hash_file, "r") as f:
                    expected = f.read().split()[0].strip().lower()
                actual = calculate_file_hash(archive_path)
                
                if expected != actual:
                    results["layer1"] = {
                        "status": "WARNING", 
                        "message": "Hash mismatch", 
                        "details": {"expected": expected, "actual": actual}
                    }
                else:
                    results["layer1"] = {"status": "PASSED", "message": "Match", "details": None}
            except Exception as e:
                results["layer1"] = {"status": "ERROR", "message": str(e), "details": None}

    # Layer 2: 7z Internal Integrity
    try:
        if verify_archive_integrity(archive_path):
            results["layer2"] = {"status": "PASSED", "message": "Integrity OK", "details": None}
        else:
            results["layer2"] = {"status": "FAILED", "message": "Integrity Check Failed", "details": None}
    except Exception as e:
        results["layer2"] = {"status": "FAILED", "message": f"Error: {e}", "details": None}

    # Layer 3: Content Hash
    if content_hash_file:
        if not content_hash_file.exists():
             results["layer3"] = {"status": "SKIPPED", "message": "File not found", "details": str(content_hash_file)}
        else:
            try:
                with open(content_hash_file, "r") as f:
                    expected_content = f.read().strip().lower()
                
                actual_content = get_archive_content_hash(archive_path)
                if actual_content:
                    actual_content = actual_content.lower()
                
                if expected_content != actual_content:
                     results["layer3"] = {
                        "status": "FAILED", 
                        "message": "Hash mismatch", 
                        "details": {"expected": expected_content, "actual": actual_content}
                    }
                else:
                    results["layer3"] = {"status": "PASSED", "message": "Match", "details": None}
            except Exception as e:
                results["layer3"] = {"status": "ERROR", "message": str(e), "details": None}

    return results
