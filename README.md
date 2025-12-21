# Data Integrity Tool

A cross-platform toolset to ensure the integrity of archives (ZIP, 7z, etc.) during transfer.

## Features
- **Format Agnostic**: Works with any file type.
- **Standard Compliant**: Uses standard SHA256 hash format.
- **Cross-Platform**: Scripts for Windows (Batch) and Linux/macOS (Bash).
- **Robust**: Handles renamed files and relative paths correctly.

## Prerequisites

To use these scripts, ensure you have the following installed:

- **7-Zip (7z)**: Required for content-based hashing.
  - **Windows**: Install 7-Zip and ensure `7z` is in your PATH.
  - **Linux**: Install `p7zip-full` (e.g., `sudo apt install p7zip-full`).
- **PowerShell**: Required for Windows scripts (`.bat`).
- **sha256sum**: Required for Linux/macOS scripts (`.sh`).

## Usage

### Windows
```batch
:: Create hash
bin\create_hash.bat my_data.zip

:: Verify hash
bin\verify_hash.bat my_data.zip my_data.zip.sha256
```

### Linux/macOS
```bash
# Create hash
./bin/create_hash.sh my_data.zip

# Verify hash
./bin/verify_hash.sh my_data.zip my_data.zip.sha256
```
