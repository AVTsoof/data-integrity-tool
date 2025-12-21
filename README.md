# 🛡️ Data Integrity Tool

**Ensure your archives are intact, even if they've been re-packaged.**

A robust, cross-platform toolset designed to verify the integrity of archive files (ZIP, 7z, etc.) during transfer and storage. It uses a unique dual-layer system to distinguish between actual data corruption and harmless re-compression.

---

## 🚀 Quick Start

### 1. Create a Hash
Generate a verification file for your archive.
```bash
# Windows
bin\create_hash.bat my_data.zip

# Linux/macOS
./bin/create_hash.sh my_data.zip
```

### 2. Verify Integrity
Check if the file is valid or if the internal data is still intact.
```bash
# Windows
bin\verify_hash.bat my_data.zip my_data.zip.sha256

# Linux/macOS
./bin/verify_hash.sh my_data.zip my_data.zip.sha256
```

---

## ✨ Key Features

- **✅ Dual-Layer Verification**: Checks both the file container and the uncompressed data.
- **🔄 Resilient**: Detects if an archive was re-zipped but still contains the same data.
- **🌍 Cross-Platform**: Native support for Windows (Batch) and Linux/macOS (Bash).
- **📦 Format Agnostic**: Works with ZIP, 7z, TAR, and more.
- **📄 Standard Compliant**: Uses `.sha256` files that remain compatible with standard tools.

---

## 🛠️ Prerequisites

Ensure you have these installed and in your system PATH:

| Tool | Windows | Linux | macOS |
| :--- | :--- | :--- | :--- |
| **7-Zip** | [Download](https://www.7-zip.org/) | `sudo apt install p7zip-full` | `brew install p7zip` |
| **Shell** | PowerShell (Built-in) | Bash (Standard) | Bash (Standard) |
| **Hash** | PowerShell (Built-in) | `sha256sum` | `sha256sum` |

---

## 🔍 Technical Deep Dive

### How the Dual-Layer System Works

Standard hashing tools only check the file itself. If you re-zip a folder, the hash changes, even if the files inside are identical. This tool solves that by generating two hashes:

1.  **File Hash**: A standard SHA256 of the archive file.
2.  **Content Hash**: A stable SHA256 of the *uncompressed data* extracted via 7-Zip (`7z t -scrcSHA256`).

**Storage:**
Both hashes are stored in a single `.sha256` file:
- **Line 1**: Standard SHA256 hash (compatible with `sha256sum`).
- **Line 2**: The content hash, prefixed with `content:`.

**The Verification Logic:**
1.  **Check File Hash**: If it matches, the file is 100% identical. **[PASS]**
2.  **Check Content Hash**: If the file hash fails (e.g., re-zipped), the tool calculates the hash of the internal data.
3.  **Result**: If the data matches, the tool confirms the integrity is intact but notes the file container has changed. **[PASS]**
4.  **Failure**: If both hashes mismatch, the file is corrupt. **[FAIL]**

### Running Tests

We include a comprehensive test suite to verify the logic across different scenarios:
- **Windows**: `tests\run_tests.bat`
- **Linux/macOS**: `./tests/run_tests.sh`

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).
