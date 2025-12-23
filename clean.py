import os
import shutil
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def clean_workspace():
    """Cleans build artifacts and temporary files."""
    root_dir = Path(__file__).parent.absolute()
    
    # Folders to remove
    folders_to_remove = [
        "__pycache__",
        "build",
        "dist",
        ".venv",
        "src/data_integrity_tool.egg-info",
        "tests/__pycache__",
        "src/__pycache__",
        "src/data_integrity_tool/__pycache__",
    ]
    
    # Files to remove
    files_to_remove = [
        "version_info.txt",
        "src/data_integrity_tool/_build_info.py",
    ]
    
    # Wildcard patterns to remove
    wildcard_patterns = [
        "*.pyc",
        "*.pyo",
        "*.pyd",
        "*.spec",
    ]

    logger.info("Cleaning workspace...")

    # Remove specific folders
    for folder_name in folders_to_remove:
        folder_path = root_dir / folder_name
        if folder_path.exists() and folder_path.is_dir():
            logger.info(f"Removing folder: {folder_name}")
            shutil.rmtree(folder_path)

    # Remove specific files
    for file_name in files_to_remove:
        file_path = root_dir / file_name
        if file_path.exists() and file_path.is_file():
            logger.info(f"Removing file: {file_name}")
            file_path.unlink()

    # Remove patterns
    for pattern in wildcard_patterns:
        for file_path in root_dir.rglob(pattern):
            if file_path.is_file():
                logger.info(f"Removing file: {file_path.relative_to(root_dir)}")
                file_path.unlink()

    # Also look for any remaining __pycache__ folders recursively
    for pycache in root_dir.rglob("__pycache__"):
        if pycache.is_dir():
            logger.info(f"Removing recursive folder: {pycache.relative_to(root_dir)}")
            shutil.rmtree(pycache)

    logger.info("Cleanup complete.")

if __name__ == "__main__":
    clean_workspace()
