import os
import subprocess
import sys
from pathlib import Path
import venv
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def setup_environment():
    """Sets up the development environment."""
    root_dir = Path(__file__).parent.absolute()
    venv_dir = root_dir / ".venv"
    
    logger.info("Setting up development environment...")

    # 1. Create virtual environment if it doesn't exist
    if not venv_dir.exists():
        logger.info(f"Creating virtual environment in {venv_dir}...")
        venv.create(venv_dir, with_pip=True)
    else:
        logger.info("Virtual environment already exists.")

    # 2. Determine path to the venv's python executable
    if os.name == "nt":
        python_exe = venv_dir / "Scripts" / "python.exe"
    else:
        python_exe = venv_dir / "bin" / "python"

    if not python_exe.exists():
        logger.error(f"Could not find Python executable at {python_exe}")
        sys.exit(1)

    # 3. Upgrade pip
    logger.info("Upgrading pip...")
    subprocess.check_call([str(python_exe), "-m", "pip", "install", "--upgrade", "pip"])

    # 4. Install requirements
    requirements_file = root_dir / "requirements.txt"
    if requirements_file.exists():
        logger.info("Installing requirements from requirements.txt...")
        subprocess.check_call([str(python_exe), "-m", "pip", "install", "-r", str(requirements_file)])
    else:
        logger.warning("requirements.txt not found. Skipping dependency installation.")

    # 5. Install the package in editable mode
    if (root_dir / "setup.py").exists():
        logger.info("Installing the package in editable mode...")
        subprocess.check_call([str(python_exe), "-m", "pip", "install", "-e", "."])

    logger.info("\nSetup complete!")
    if os.name == "nt":
        logger.info(f"To activate the environment, run: .venv\\Scripts\\activate.bat")
    else:
        logger.info(f"To activate the environment, run: source .venv/bin/activate")

if __name__ == "__main__":
    setup_environment()
