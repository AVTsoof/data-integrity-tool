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
    if not check_7z_installed():
        raise RuntimeError("7z is not installed or not in PATH.")

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
    hash_file = archive_path.with_suffix(archive_path.suffix + ".sha256")
    # If the file is .zip, it becomes .zip.sha256. 
    # Wait, the shell script does: "$ARCHIVE.sha256". So test.zip -> test.zip.sha256
    # pathlib with_suffix replaces the suffix if one exists, or appends?
    # with_suffix replaces. So test.zip -> test.sha256. This is WRONG based on shell script.
    # Shell script: test.zip -> test.zip.sha256
    hash_file = Path(str(archive_path) + ".sha256")
    
    with open(hash_file, "w") as f:
        f.write(f"{file_hash}  {archive_path.name}\n")

    # Layer 3: Content Hash
    content_hash = get_archive_content_hash(archive_path)
    content_hash_file = None
    if content_hash:
        content_hash_file = Path(str(archive_path) + ".content.sha256")
        with open(content_hash_file, "w") as f:
            f.write(f"{content_hash}\n")
            
    return hash_file, content_hash_file
