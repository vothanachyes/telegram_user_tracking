# Deployment Scripts

This directory contains utility scripts for building and deploying the application.

## Scripts

### `build.py`

Builds the application executable for the current platform using PyInstaller with **three layers of code protection**:

1. **PyArmor Obfuscation** - Obfuscates Python code to prevent reverse engineering
2. **Bytecode Encryption** - Encrypts Python bytecode using PyInstaller's `--key` option
3. **Source File Removal** - Removes `.py` source files from the final bundle

**Usage:**
```bash
python scripts/build.py
```

**Prerequisites:**
```bash
pip install pyarmor  # Required for obfuscation
```

**Windows Installer (Optional):**
For Windows builds, the script can automatically create a professional installer using Inno Setup:
1. Download and install [Inno Setup](https://jrsoftware.org/isinfo.php) (version 5 or 6) (Or winget install --id JRSoftware.InnoSetup -e -s winget -i #window)
2. The installer will be automatically created after the executable build completes
3. Installer includes: desktop shortcut, Start Menu entry, uninstaller, and user-selectable installation directory

**Output:**
- Windows: 
  - `dist/TelegramUserTracking.exe` (standalone executable)
  - `dist/TelegramUserTracking-Setup-v{version}.exe` (installer, if Inno Setup is installed)
- macOS: `dist/TelegramUserTracking.app`
- Linux: `dist/TelegramUserTracking`

**Configuration:**
Edit `scripts/build.py` to enable/disable protection layers and installer:
```python
USE_PYARMOR = True              # Enable/disable PyArmor obfuscation
USE_BYTECODE_ENCRYPTION = True  # Enable/disable bytecode encryption
REMOVE_SOURCE_FILES = True      # Enable/disable source file removal
USE_INSTALLER = True            # Enable/disable Inno Setup installer creation (Windows only)
```

**Important Notes:**
- 🔑 Encryption key is auto-generated and stored in `.build_key` (keep secure!)
- 📦 PyArmor is optional - build will continue without it if not installed
- 📦 Inno Setup is optional - build will continue without it if not installed (Windows only)
- ⚠️ See [Code Protection Guide](../docs/CODE_PROTECTION_GUIDE.md) for detailed documentation

**Installer Features:**
- User-selectable installation directory (defaults to Program Files or Local AppData)
- Desktop shortcut (optional, user can deselect)
- Start Menu entry (optional, user can deselect)
- Uninstaller for clean removal
- Application icon and version information
- Professional installation wizard

**Troubleshooting Installer:**
- **Inno Setup not found**: Install Inno Setup from https://jrsoftware.org/isinfo.php and ensure `iscc.exe` is in PATH or in default installation location
- **Installer creation skipped**: Check that `USE_INSTALLER = True` in `scripts/build.py`
- **Installer compilation fails**: Check Inno Setup installation and ensure executable was built successfully first

### `deploy_update.py`

Automated deployment script that handles building, checksum calculation, GitHub release creation, and Firebase update.

## Deployment Script (`deploy_update.py`)

### Overview

The deployment script automates the entire update deployment process:

1. Builds executables (optional)
2. Calculates SHA256 checksums
3. Creates GitHub release in public releases repository
4. Uploads binaries to GitHub release
5. Updates Firebase Firestore with version info

### Prerequisites

1. **Install Dependencies:**
   ```bash
   pip install requests firebase-admin
   ```

2. **Set Environment Variables:**
   
   **Recommended: Create `.env.deploy` file** (deployment-only variables):
   
   ```bash
   # Create deployment-specific environment file
   cp .env.deploy.example .env.deploy
   # Edit .env.deploy with your values
   ```
   
   **Or use `.env` file** (includes development variables):
   
   ```bash
   # GitHub (for deployment script)
   export GITHUB_TOKEN=ghp_xxxxxxxxxxxx
   export GITHUB_REPO_OWNER=your_username
   export GITHUB_REPO_NAME=telegram_user_tracking-releases
   
   # GitHub Private Repo (for CI/CD - Mac only, optional)
   export GITHUB_PRIVATE_REPO_OWNER=your_username
   export GITHUB_PRIVATE_REPO_NAME=telegram_user_tracking
   export GITHUB_WORKFLOW_NAME="Build Windows Executable"  # Optional
   
   # Firebase (for deployment script)
   export FIREBASE_CREDENTIALS_PATH=/path/to/firebase-credentials.json
   ```
   
   **Note:** The deployment script automatically loads `.env.deploy` if it exists, otherwise falls back to `.env`. Using `.env.deploy` is recommended to avoid including development-only variables.

   **Getting GitHub Token:**
   - Go to GitHub Settings → Developer settings → Personal access tokens → Tokens (classic)
   - Generate new token with `repo` scope
   - Copy token and set as `GITHUB_TOKEN`

### Deployment Workflow (Smart Auto-Detection)

The script automatically detects your platform and handles everything:

**From Mac:**
```bash
python scripts/deploy_update.py 1.0.1 --release-notes "Bug fixes"
```

**What happens automatically:**
1. Detects Mac platform
2. Creates and pushes git tag `v1.0.1` to private repo
3. GitHub Actions automatically triggers Windows build
4. Waits for Windows build to complete
5. Downloads Windows artifact automatically
6. Builds Mac executable locally
7. Builds Linux executable locally (optional)
8. Calculates checksums for all binaries
9. Creates GitHub release in public repo
10. Uploads all binaries to release
11. Updates Firebase with version info

**From Windows:**
```bash
python scripts/deploy_update.py 1.0.1 --release-notes "Bug fixes"
```

**What happens automatically:**
1. Detects Windows platform
2. Builds Windows executable locally
3. Calculates checksum
4. Creates GitHub release in public repo
5. Uploads Windows binary to release
6. Updates Firebase with version info
7. Skips Mac/Linux (not needed)

### Usage Examples

#### One-Command Deployment (Recommended)

**From Mac:**
```bash
python scripts/deploy_update.py 1.0.1 --release-notes "Bug fixes"
```
Automatically handles Windows CI/CD + Mac/Linux local builds + deployment

**From Windows:**
```bash
python scripts/deploy_update.py 1.0.1 --release-notes "Bug fixes"
```
Automatically builds Windows locally + deployment

#### Deploy with Pre-built Binaries

Use existing binaries from `dist/` directory:

```bash
python scripts/deploy_update.py 1.0.1 \
  --skip-build \
  --release-notes "Bug fixes"
```

#### Build Only (No Deployment)

Build executable without creating release:

```bash
python scripts/deploy_update.py 1.0.1 \
  --skip-github \
  --skip-firebase
```

#### Build for Current OS Only

Build executable for your current platform (Mac builds Mac, Windows builds Windows):

```bash
# Build for current OS only (no deployment)
python scripts/build.py
```

Or using the deployment script (builds for current OS only):

```bash
python scripts/deploy_update.py 1.0.1 \
  --skip-github \
  --skip-firebase \
  --skip-windows-ci
```

#### Deploy to GitHub Only

Create GitHub release but skip Firebase update:

```bash
python scripts/deploy_update.py 1.0.1 \
  --skip-firebase \
  --release-notes "Bug fixes"
```

#### Deploy to Firebase Only

Update Firebase without creating GitHub release:

```bash
python scripts/deploy_update.py 1.0.1 \
  --skip-github \
  --release-notes "Bug fixes"
```

#### Specify Minimum Version Required

Set minimum version that can update:

```bash
python scripts/deploy_update.py 1.0.1 \
  --min-version 1.0.0 \
  --release-notes "Requires version 1.0.0 or higher"
```

### Command-Line Options

```
positional arguments:
  version               Version string (e.g., 1.0.1)

optional arguments:
  --platform {windows,macos,linux}
                        Platform to build (default: current platform)
  --release-notes TEXT Release notes for the update
  --min-version TEXT    Minimum version required to update
  --skip-build          Skip building (use existing binaries in dist/)
  --skip-github         Skip GitHub release creation
  --skip-firebase       Skip Firebase update
  --skip-windows-ci     Skip Windows CI/CD build (Mac only)
  --github-token TEXT   GitHub personal access token (overrides env var)
  --repo-owner TEXT     GitHub repository owner (overrides env var)
  --repo-name TEXT      GitHub repository name (overrides env var)
  --private-repo-owner TEXT  Private repo owner (overrides env var)
  --private-repo-name TEXT   Private repo name (overrides env var)
  --workflow-name TEXT  Workflow name (overrides env var)
```

### What the Script Does

1. **Builds Executables** (if not `--skip-build`):
   - Runs `scripts/build.py` for current platform
   - Outputs to `dist/` directory
   - Supports Windows, macOS, and Linux

2. **Finds Existing Binaries** (if `--skip-build`):
   - Scans `dist/` directory for executables
   - Detects platform based on file extension:
     - `.exe` → Windows
     - No extension → macOS or Linux (detected by system)

3. **Calculates Checksums**:
   - SHA256 checksum for each binary
   - Displays checksum and file size
   - Used for download verification

4. **Creates GitHub Release** (if not `--skip-github`):
   - Creates release with tag `v{version}`
   - Uploads all binaries to release
   - Returns release URL

5. **Updates Firebase** (if not `--skip-firebase`):
   - Updates `app_updates/latest` document in Firestore
   - Sets download URLs, checksums, file sizes
   - Sets `is_available=true`
   - Sets `release_date` to current timestamp

### Binary Naming Convention

The script expects binaries to be named:

- **Windows**: `TelegramUserTracking.exe`
- **macOS**: `TelegramUserTracking`
- **Linux**: `TelegramUserTracking`

When uploading to GitHub, files are renamed to:
- `TelegramUserTracking-v{version}-windows.exe`
- `TelegramUserTracking-v{version}-macos.dmg`
- `TelegramUserTracking-v{version}-linux`

### Troubleshooting

#### GitHub Token Not Working

**Symptoms:**
- Error: "Failed to create release: 401 Unauthorized"
- Error: "Failed to upload: 403 Forbidden"

**Solutions:**
- Verify token has `repo` scope
- Check token hasn't expired
- Ensure repository name is correct
- Verify token has access to the repository

#### Firebase Update Fails

**Symptoms:**
- Error: "Firebase credentials not found"
- Error: "Firestore database not available"

**Solutions:**
- Verify `FIREBASE_CREDENTIALS_PATH` is correct
- Check Firebase credentials file exists and is valid
- Ensure Firestore is enabled in Firebase project
- Verify Firebase Admin SDK is installed: `pip install firebase-admin`

#### Binaries Not Found

**Symptoms:**
- Error: "No binaries found in dist/ directory"

**Solutions:**
- Check `dist/` directory exists
- Verify binaries are named correctly:
  - Windows: `TelegramUserTracking.exe`
  - Mac/Linux: `TelegramUserTracking`
- Build binaries first or remove `--skip-build` flag
- Check file permissions

#### Upload Fails

**Symptoms:**
- Error: "Failed to upload: 413 Payload Too Large"
- Error: "Failed to upload: Timeout"

**Solutions:**
- Check file size (GitHub has 2GB limit per file)
- Verify network connection
- Check GitHub API rate limits (5000 requests/hour)
- Try uploading one file at a time

#### Checksum Mismatch

**Symptoms:**
- Warning: "Checksum mismatch" during download verification

**Solutions:**
- Re-download the file
- Rebuild the binary
- Verify file wasn't corrupted during upload

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GITHUB_TOKEN` | Yes (for GitHub) | GitHub personal access token with `repo` scope |
| `GITHUB_REPO_OWNER` | Yes (for GitHub) | GitHub username or organization |
| `GITHUB_REPO_NAME` | Yes (for GitHub) | Repository name (e.g., `telegram_user_tracking-releases`) |
| `FIREBASE_CREDENTIALS_PATH` | Yes (for Firebase) | Path to Firebase service account credentials JSON |

### Security Notes

- **GitHub token** is only needed in deployment environment (not in production app)
- **Firebase credentials** should be stored securely and not committed to git
- **Public releases repo** contains only binaries (no source code)
- **Checksums** ensure download integrity
- Never commit tokens or credentials to version control

### `decrypt_database_for_support.py`

Support script to decrypt all encrypted fields in a user's database and create a new database with decrypted data. Used by support staff when troubleshooting user issues.

**Usage:**

```bash
# With device info as arguments:
python scripts/decrypt_database_for_support.py input.db output_decrypted.db \
  --hostname "DESKTOP-ABC" --machine "AMD64" --system "Windows"

# With device info from JSON file:
python scripts/decrypt_database_for_support.py input.db output_decrypted.db \
  --device-info device_info.json

# Interactive mode (will prompt for device info):
python scripts/decrypt_database_for_support.py input.db output_decrypted.db
```

**Prerequisites:**
```bash
pip install cryptography
```

**What it does:**
1. Reads `encryption_key_hash` from `app_settings` table in the database
2. Derives encryption key from device information (hostname, machine, system) + encryption key hash
3. Decrypts all encrypted fields in:
   - `telegram_credentials` (phone_number, session_string)
   - `telegram_users` (username, first_name, last_name, full_name, phone, bio)
   - `messages` (content, caption, message_link)
   - `reactions` (message_link)
   - `group_fetch_history` (account_phone_number, account_full_name, account_username)
   - `account_activity_log` (phone_number)
4. Creates a new database file with all decrypted data

**Device Info JSON format:**
```json
{
  "hostname": "DESKTOP-ABC",
  "machine": "AMD64",
  "system": "Windows"
}
```

**Getting Device Info:**
Users can find their device information in:
- Settings → Security tab (device info should be displayed there)
- Or by running Python:
  ```python
  import platform
  print(f"Hostname: {platform.node()}")
  print(f"Machine: {platform.machine()}")
  print(f"System: {platform.system()}")
  ```

**Important Notes:**
- ⚠️ The encryption key is device-specific - you MUST have the correct device information
- 📦 The `encryption_key_hash` is automatically read from the database
- 🔒 The output database contains unencrypted sensitive data - handle securely
- ✅ Original database is not modified - a new decrypted copy is created

### `decrypt_pin.py`

Script to decrypt a PIN from exported recovery data. See script header for usage.

### Related Documentation

- [Auto-Update System Guide](../docs/auto-update-system-guide.md) - Complete guide to the update system
- [Windows Build Workflow](../docs/WINDOWS_BUILD_WORKFLOW.md) - CI/CD build workflow

