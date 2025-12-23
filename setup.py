from setuptools import setup, find_packages
import os
from metadata import AUTHOR, URL, VERSION

setup(
    name="data-integrity-tool",
    version=VERSION,
    author=AUTHOR,
    url=URL,
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
