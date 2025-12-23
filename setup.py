from setuptools import setup, find_packages
import os
import json

def load_metadata():
    """Loads project metadata from metadata.json."""
    metadata_path = os.path.join(os.path.dirname(__file__), 'metadata.json')
    try:
        with open(metadata_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        raise RuntimeError(f"metadata.json not found at {metadata_path}")
    except json.JSONDecodeError:
        raise RuntimeError(f"Error decoding metadata.json at {metadata_path}")

metadata = load_metadata()

setup(
    name="data-integrity-tool",
    version=metadata["version"],
    author=metadata["author"],
    url=metadata["url"],
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    install_requires=["colorama>=0.4.6"],
    entry_points={
        "console_scripts": [
            "data-integrity-tool=data_integrity_tool.main:main",
        ],
    },
    python_requires=">=3.6",
)
