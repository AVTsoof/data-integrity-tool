# 🛡️ Data Integrity Tool

**Ensure your archives are intact, even if they've been re-packaged.**

A robust, cross-platform toolset designed to verify the integrity of archive files (ZIP, 7z, etc.) during transfer and storage. It uses a unique **Triple-Layer Verification** system to guarantee data safety.

---

## 🚀 Quick Start

### 1. Create Hashes
Generate verification files for your archive.
```bash
python -m data_integrity_tool.main create my_data.zip
```
This creates two files:
- `my_data.zip.sha256`: The standard file hash.
- `my_data.zip.content.sha256`: The stable content hash.

### 2. Verify Integrity
Check if the file is valid. The tool automatically looks for `.sha256` and `.content.sha256` files in the same folder.
```bash
python -m data_integrity_tool.main verify my_data.zip

# Advanced: Explicitly provide hash files
python -m data_integrity_tool.main verify my_data.zip --hash-file my_data.zip.sha256
python -m data_integrity_tool.main verify my_data.zip --hash-file my_data.zip.sha256 --content-hash-file my_data.zip.content.sha256
```

---

## ✨ Key Features

- **✅ Triple-Layer Verification**: 
    1. **Archive Hash**: Validates the file container itself.
    2. **7z CRC Check**: Uses 7-Zip's internal checksums to detect bit-rot.
    3. **Content Hash**: Validates the actual data bits (SHA256).
- **🔄 Resilient**: Detects if an archive was re-zipped but still contains the same data.
- **🌍 Cross-Platform**: Native support for Windows (Batch) and Linux/macOS (Bash).
- **📦 Format Agnostic**: Works with ZIP, 7z, TAR, and more.
- **📄 Simple Storage**: Uses clean `.sha256` files for easy management.

---

## 💡 The 3 Layers: Simple Explanation

Think of your archive as a **sealed box** of documents.

1.  **Layer 1: The Box (Archive Hash)**
    *   **Checks:** Is the box identical to the original?
    *   **Verdict:** If yes, 100% safe.

2.  **Layer 2: The Structure (Internal Check) — *The Standard***
    *   **Checks:** Is the box damaged or corrupted?
    *   **Verdict:** Catches download errors. **Valid even if re-packaged.**

3.  **Layer 3: The Contents (Content Hash) — *Extra Security***
    *   **Checks:** Are the documents inside 100% authentic?
    *   **Verdict:** **Advanced protection.** Protects against malicious tampering (e.g. fake files with matching CRC).

---

## 🛠️ Prerequisites

Ensure you have these installed and in your system PATH:

| Tool | Windows | Linux | macOS |
| :--- | :--- | :--- | :--- |
| **7-Zip** | [Download](https://www.7-zip.org/) | `sudo apt install p7zip-full` | `brew install p7zip` |
| **Python** | [Download](https://www.python.org/) | `sudo apt install python3` | `brew install python` |
| **Shell** | PowerShell (Built-in) | Bash (Standard) | Bash (Standard) |
| **Hash** | PowerShell (Built-in) | `sha256sum` | `sha256sum` |

---

## 🔍 Technical Deep Dive

### The Triple-Layer System

Standard hashing tools only check the file itself. This tool adds two more layers of protection:

1.  **Layer 1: Archive Hash (SHA256)**
    - Checks the `.sha256` file. If it matches, the archive is bit-for-bit identical to the original.
2.  **Layer 2: 7z Internal Integrity (CRC32)**
    - Runs `7z t`. This uses the archive's internal checksums to ensure no "bit-rot" has occurred during storage.
3.  **Layer 3: Content Hash (SHA256)**
    - Checks the `.content.sha256` file. This is a stable hash of the *uncompressed data*. If you re-zip the same files, Layer 1 will fail, but Layer 3 will pass, confirming your data is safe.

### Flexible Verification
You can verify against either file:
- Providing the `.sha256` file will trigger all 3 layers (if the content hash file exists).
- Providing the `.content.sha256` file will skip the archive hash check but still perform the CRC and Content Hash checks.
- **Advanced**: You can explicitly provide both files: `python -m data_integrity_tool.main verify archive.zip --hash-file archive.sha256 --content-hash-file archive.content.sha256`.

### Running Tests

We include a comprehensive test suite to verify the logic across different scenarios:
- **Windows**: `tests\run_tests.bat`
- **Linux/macOS**: `./tests/run_tests.sh`

---


## 🐍 Python Application

We now offer a robust, cross-platform Python application that includes both a CLI and a GUI.

### Installation

1.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
2.  **Install the Tool**:
    ```bash
    pip install .
    ```

### Usage

#### Command Line Interface (CLI)

The CLI mirrors the functionality of the shell scripts.

**Create Hashes:**
```bash
python -m data_integrity_tool.main create my_data.zip
```

**Verify Integrity:**
```bash
python -m data_integrity_tool.main verify my_data.zip
```

#### Graphical User Interface (GUI)

Simply run the tool without arguments to launch the GUI:
```bash
python -m data_integrity_tool.main
# 🛡️ Data Integrity Tool

**Ensure your archives are intact, even if they've been re-packaged.**

A robust, cross-platform toolset designed to verify the integrity of archive files (ZIP, 7z, etc.) during transfer and storage. It uses a unique **Triple-Layer Verification** system to guarantee data safety.

---

## 🚀 Quick Start

### 1. Create Hashes
Generate verification files for your archive.
```bash
# Windows
bin\create_hash.bat my_data.zip

# Linux/macOS
./bin/create_hash.sh my_data.zip
```
This creates two files:
- `my_data.zip.sha256`: The standard file hash.
- `my_data.zip.content.sha256`: The stable content hash.

### 2. Verify Integrity
Check if the file is valid. The tool automatically looks for `.sha256` and `.content.sha256` files in the same folder.
```bash
# Windows
bin\verify_hash.bat my_data.zip

# Linux/macOS
./bin/verify_hash.sh my_data.zip

# Advanced: Explicitly provide hash files
bin\verify_hash.bat my_data.zip my_data.zip.sha256
bin\verify_hash.bat my_data.zip my_data.zip.sha256 my_data.zip.content.sha256
```

---

## ✨ Key Features

- **✅ Triple-Layer Verification**: 
    1. **Archive Hash**: Validates the file container itself.
    2. **7z CRC Check**: Uses 7-Zip's internal checksums to detect bit-rot.
    3. **Content Hash**: Validates the actual data bits (SHA256).
- **🔄 Resilient**: Detects if an archive was re-zipped but still contains the same data.
- **🌍 Cross-Platform**: Native support for Windows (Batch) and Linux/macOS (Bash).
- **📦 Format Agnostic**: Works with ZIP, 7z, TAR, and more.
- **📄 Simple Storage**: Uses clean `.sha256` files for easy management.

---

## 💡 The 3 Layers: Simple Explanation

Think of your archive as a **sealed box** of documents.

1.  **Layer 1: The Box (Archive Hash)**
    *   **Checks:** Is the box identical to the original?
    *   **Verdict:** If yes, 100% safe.

2.  **Layer 2: The Structure (Internal Check) — *The Standard***
    *   **Checks:** Is the box damaged or corrupted?
    *   **Verdict:** Catches download errors. **Valid even if re-packaged.**

3.  **Layer 3: The Contents (Content Hash) — *Extra Security***
    *   **Checks:** Are the documents inside 100% authentic?
    *   **Verdict:** **Advanced protection.** Protects against malicious tampering (e.g. fake files with matching CRC).

---

## 🛠️ Prerequisites

Ensure you have these installed and in your system PATH:

| Tool | Windows | Linux | macOS |
| :--- | :--- | :--- | :--- |
| **7-Zip** | [Download](https://www.7-zip.org/) | `sudo apt install p7zip-full` | `brew install p7zip` |
| **Python** | [Download](https://www.python.org/) | `sudo apt install python3` | `brew install python` |
| **Shell** | PowerShell (Built-in) | Bash (Standard) | Bash (Standard) |
| **Hash** | PowerShell (Built-in) | `sha256sum` | `sha256sum` |

---

## 🔍 Technical Deep Dive

### The Triple-Layer System

Standard hashing tools only check the file itself. This tool adds two more layers of protection:

1.  **Layer 1: Archive Hash (SHA256)**
    - Checks the `.sha256` file. If it matches, the archive is bit-for-bit identical to the original.
2.  **Layer 2: 7z Internal Integrity (CRC32)**
    - Runs `7z t`. This uses the archive's internal checksums to ensure no "bit-rot" has occurred during storage.
3.  **Layer 3: Content Hash (SHA256)**
    - Checks the `.content.sha256` file. This is a stable hash of the *uncompressed data*. If you re-zip the same files, Layer 1 will fail, but Layer 3 will pass, confirming your data is safe.

### Flexible Verification
You can verify against either file:
- Providing the `.sha256` file will trigger all 3 layers (if the content hash file exists).
- Providing the `.content.sha256` file will skip the archive hash check but still perform the CRC and Content Hash checks.
- **Advanced**: You can explicitly provide both files: `bin\verify_hash.bat archive.zip archive.sha256 archive.content.sha256`.

### Running Tests

We include a comprehensive test suite to verify the logic across different scenarios:
- **Windows**: `tests\run_tests.bat`
- **Linux/macOS**: `./tests/run_tests.sh`

---


#### Graphical User Interface (GUI)

Simply run the tool without arguments to launch the GUI:
```bash
python -m data_integrity_tool.main
```
- **Create Tab**: Select an archive to generate hashes.
- **Verify Tab**: Select an archive to verify its integrity.

---

## Building from Source

To create a standalone Windows executable:

1.  Ensure you have Python and `pip` installed.
2.  Install the dependencies:
    ```bash
    pip install -r requirements.txt
    ```
3.  Run the build script:
    ```cmd
    build_exe.bat
    ```
4.  The executable will be created in the `dist` folder as `data-integrity-tool.exe`.

> [!NOTE]
> The generated executable still requires `7z` to be installed and available in your system PATH.

## License

This project is licensed under the [MIT License](LICENSE).
