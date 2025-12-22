from setuptools import setup, find_packages

setup(
    name="data-integrity-tool",
    version="0.1.0",
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
