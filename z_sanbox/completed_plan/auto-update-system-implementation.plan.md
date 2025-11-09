<!-- 4ba434b7-a3b3-4128-8ebb-50a97ef4f9fe 282fea38-8cd3-4af5-a82e-612d27f4c524 -->
# Auto Update System Implementation

## Overview

Implement automatic app update system that checks Firebase for new versions, auto-downloads updates, shows toast notifications, and tracks installations. Only works for logged-in users.

## Architecture

### 1. Firebase Structure

- **Collection**: `app_updates`
- **Document**: `latest`
- **Fields**:
  - `version` (string): Semantic version (e.g., "1.0.1")
  - `download_url_windows` (string): GitHub release URL for Windows .exe
  - `download_url_macos` (string): GitHub release URL for macOS .app/.dmg
  - `download_url_linux` (string): GitHub release URL for Linux binary
  - `release_date` (timestamp): When update was released
  - `is_available` (boolean): Whether update is currently available
  - `file_size` (number): Size in bytes
  - `checksum` (string): SHA256 checksum for verification
  - `release_notes` (string): Optional release notes
  - `min_version_required` (string): Minimum version that can update (optional)

### 2. Database Schema

Add new table `app_update_history`:

```sql
CREATE TABLE IF NOT EXISTS app_update_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_email TEXT NOT NULL,
    version TEXT NOT NULL,
    installed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    download_path TEXT,
    UNIQUE(user_email, version)
);
CREATE INDEX IF NOT EXISTS idx_app_update_history_email ON app_update_history(user_email);
CREATE INDEX IF NOT EXISTS idx_app_update_history_version ON app_update_history(version);
```

### 3. Update Service

**File**: `services/update_service.py` (new)

Service responsibilities:

- Check Firebase for updates every 1 hour (only if logged in)
- Compare current version with latest version using semantic versioning
- Auto-download update if available
- Verify download checksum
- Show toast notification when download completes
- Track installations in database
- Handle platform-specific download URLs
- Check if fetch operation is running before allowing install

Key methods:

- `start()`: Start background update checker
- `stop()`: Stop background update checker
- `check_for_updates()`: Check Firebase for new version
- `download_update(url, version)`: Download update file
- `verify_checksum(file_path, expected_checksum)`: Verify download integrity
- `is_fetch_running()`: Check if fetch operation is active
- `install_update(file_path)`: Launch installer (platform-specific)
- `record_installation(version)`: Save installation record to database

### 4. Firebase Config Updates

**File**: `config/firebase_config.py`

Add method:

- `get_app_update_info()`: Fetch latest update info from Firestore `app_updates/latest`

### 5. Database Manager Updates

**File**: `database/managers/update_manager.py` (new)

Manager for update history:

- `record_update_installation(user_email, version, download_path)`: Record installation
- `get_user_installed_versions(user_email)`: Get list of versions user installed
- `has_user_installed_version(user_email, version)`: Check if user installed specific version

### 6. Version Comparison Utility

**File**: `utils/version_utils.py` (new)

Semantic versioning comparison:

- `compare_versions(current, latest)`: Compare two semantic versions
- `is_newer_version(latest, current)`: Check if latest is newer
- `parse_version(version_string)`: Parse version string to tuple

### 7. Update Toast Component

**File**: `ui/components/update_toast.py` (new)

Custom toast for update notifications:

- Shows update icon, version info, and two buttons: [Ignore, Install]
- Install button checks if fetch is running
- Handles installation launch
- Auto-dismisses after user action

### 8. Integration Points

**File**: `ui/app.py`

- Initialize update service after login
- Start update service when user logs in
- Stop update service when user logs out
- Pass page reference to update service for toast notifications

**File**: `services/auth_service.py`

- No changes needed (update service checks login status)

**File**: `ui/pages/fetch_data/handlers.py` or `ui/pages/fetch_data_page.py`

- Expose `is_fetching` state to update service (via view model or service)

### 9. Platform-Specific Installation

**Windows**:

- Download .exe to `USER_DATA_DIR / "updates" / "TelegramUserTracking-v{version}.exe"`
- Launch installer: `subprocess.Popen([exe_path])`
- Installer should handle replacing current executable

**macOS**:

- Download .app or .dmg to `USER_DATA_DIR / "updates" / "TelegramUserTracking-v{version}.dmg"`
- For .dmg: Mount and copy .app to Applications
- For .app: Copy to Applications folder

**Linux**:

- Download binary or .AppImage to `USER_DATA_DIR / "updates" / "TelegramUserTracking-v{version}"`
- Make executable: `chmod +x`
- Replace current binary or update symlink

### 10. Background Task Pattern

Follow existing pattern from `AccountStatusService`:

- Use `asyncio.create_task()` for background loop
- Check every 3600 seconds (1 hour)
- Only run if user is logged in
- Handle errors gracefully (don't crash app)

### 11. Constants

**File**: `utils/constants.py`

Add:

```python
UPDATE_CHECK_INTERVAL_SECONDS = 3600  # 1 hour
UPDATES_DIR_NAME = "updates"
FIREBASE_APP_UPDATES_COLLECTION = "app_updates"
FIREBASE_APP_UPDATES_DOCUMENT = "latest"
```

## Implementation Steps

1. **Create database migration** for `app_update_history` table
2. **Create version utility** (`utils/version_utils.py`) with semantic versioning comparison
3. **Create update manager** (`database/managers/update_manager.py`) for database operations
4. **Update Firebase config** to add `get_app_update_info()` method
5. **Create update service** (`services/update_service.py`) with background checking and download logic
6. **Create update toast component** (`ui/components/update_toast.py`) for user notifications
7. **Integrate in app.py** to start/stop service based on login status
8. **Add fetch state checking** to prevent install during fetch operations
9. **Test on all platforms** (Windows, macOS, Linux)

## Error Handling

- Network failures: Log error, retry on next check cycle
- Download failures: Log error, show error toast, retry on next check
- Checksum verification failure: Delete corrupted file, retry download
- Installation failure: Log error, show error toast
- Firebase errors: Log error, continue with cached data if available
- Fetch running: Show message "Cannot install update while fetch is in progress"

## Security Considerations

- Verify checksums before installation
- Only download from trusted GitHub release URLs
- Validate version strings before comparison
- Only allow updates for logged-in users
- Store downloads in secure user data directory

## Update Workflow Guide

### Prerequisites

1. GitHub repository with private releases enabled
2. GitHub Personal Access Token with `repo` scope
3. Firebase project with Firestore enabled
4. Build environment for each target platform (Windows, macOS, Linux)

### Step 1: Update Version Number

**File**: `.env` or `utils/constants.py`

Update `APP_VERSION`:

```bash
APP_VERSION=1.0.1  # Increment version (semantic versioning: MAJOR.MINOR.PATCH)
```

**File**: `build.py` (for Windows version info)

Update version in `create_version_info()`:

```python
filevers=(1, 0, 1, 0),
prodvers=(1, 0, 1, 0),
StringStruct(u'FileVersion', u'1.0.1.0'),
StringStruct(u'ProductVersion', u'1.0.1.0')
```

### Step 2: Build Executables for All Platforms

#### Windows Build

```bash
# On Windows machine or Windows VM
python build.py
# Output: dist/TelegramUserTracking.exe
```

#### macOS Build

```bash
# On macOS machine
python build.py
# Output: dist/TelegramUserTracking (or .app bundle if configured)
# Or create .dmg:
# hdiutil create -volname "Telegram User Tracking" -srcfolder dist/TelegramUserTracking.app -ov -format UDZO TelegramUserTracking-v1.0.1.dmg
```

#### Linux Build

```bash
# On Linux machine
python build.py
# Output: dist/TelegramUserTracking
# Make executable:
# chmod +x dist/TelegramUserTracking
```

### Step 3: Calculate Checksums

For each platform binary, calculate SHA256 checksum:

**Windows**:

```powershell
Get-FileHash -Path "dist\TelegramUserTracking.exe" -Algorithm SHA256
```

**macOS/Linux**:

```bash
shasum -a 256 dist/TelegramUserTracking
# or
sha256sum dist/TelegramUserTracking
```

### Step 4: Create GitHub Release

1. **Go to GitHub repository** → Releases → Draft a new release
2. **Tag version**: `v1.0.1` (must match APP_VERSION)
3. **Release title**: `Version 1.0.1` or descriptive title
4. **Release notes**: Add changelog/features
5. **Upload binaries**:

   - `TelegramUserTracking-v1.0.1-windows.exe`
   - `TelegramUserTracking-v1.0.1-macos.dmg` (or .app)
   - `TelegramUserTracking-v1.0.1-linux` (or .AppImage)

6. **Publish release** (private release)

### Step 5: Get Download URLs

After publishing, get direct download URLs:

- Right-click on uploaded file → "Copy link address"
- Format: `https://github.com/OWNER/REPO/releases/download/v1.0.1/TelegramUserTracking-v1.0.1-windows.exe`

**Note**: For private repos, you may need to use GitHub API with authentication or use a different hosting method.

### Step 6: Update Firebase Firestore

**Collection**: `app_updates`

**Document**: `latest`

Update document with:

```json
{
  "version": "1.0.1",
  "download_url_windows": "https://github.com/OWNER/REPO/releases/download/v1.0.1/TelegramUserTracking-v1.0.1-windows.exe",
  "download_url_macos": "https://github.com/OWNER/REPO/releases/download/v1.0.1/TelegramUserTracking-v1.0.1-macos.dmg",
  "download_url_linux": "https://github.com/OWNER/REPO/releases/download/v1.0.1/TelegramUserTracking-v1.0.1-linux",
  "release_date": "2025-01-15T10:00:00Z",
  "is_available": true,
  "file_size_windows": 52428800,
  "file_size_macos": 52838400,
  "file_size_linux": 51200000,
  "checksum_windows": "abc123...",
  "checksum_macos": "def456...",
  "checksum_linux": "ghi789...",
  "release_notes": "Bug fixes and performance improvements",
  "min_version_required": "1.0.0"
}
```

**Firebase Console Steps**:

1. Go to Firebase Console → Firestore Database
2. Create collection `app_updates` if not exists
3. Create/update document `latest`
4. Add all fields above
5. Set `is_available` to `true` when ready to release

### Step 7: Testing the Update Flow

#### Test Scenario 1: Normal Update Flow

1. **Install old version** (e.g., 1.0.0)
2. **Login to app**
3. **Wait 1 hour** (or manually trigger check)
4. **Verify**:

   - App checks Firebase
   - Downloads new version automatically
   - Shows toast notification with [Ignore, Install] buttons
   - Download is saved to `USER_DATA_DIR/updates/`

5. **Click Install**:

   - Verify fetch is not running (should show error if running)
   - Installer launches
   - App closes
   - New version installs

6. **Verify installation**:

   - Check `app_update_history` table has record
   - New version runs correctly

#### Test Scenario 2: Update During Fetch

1. **Start fetch operation**
2. **Trigger update check** (or wait for auto-check)
3. **Download completes**, toast shows
4. **Click Install**:

   - Should show error: "Cannot install update while fetch is in progress"
   - Install button disabled or shows error message

5. **Stop fetch**
6. **Click Install again**:

   - Should work now

#### Test Scenario 3: Checksum Verification

1. **Manually corrupt download file** in `USER_DATA_DIR/updates/`
2. **Trigger install**:

   - Should detect checksum mismatch
   - Delete corrupted file
   - Re-download automatically
   - Verify checksum again

#### Test Scenario 4: Multiple Users

1. **User A installs update** → Recorded in database
2. **User B installs same update** → Separate record in database
3. **Verify** both users have records in `app_update_history`

### Step 8: Rollback Procedure

If update has issues:

1. **Set `is_available` to `false`** in Firebase:
   ```json
   {
     "is_available": false
   }
   ```

2. **Or update to previous version** in Firebase document
3. **Users won't get update** until `is_available` is `true` again

### Step 9: Monitoring

**Check update installations**:

```sql
SELECT * FROM app_update_history 
WHERE version = '1.0.1' 
ORDER BY installed_at DESC;
```

**Check user update history**:

```sql
SELECT * FROM app_update_history 
WHERE user_email = 'user@example.com' 
ORDER BY installed_at DESC;
```

### Step 10: Cleanup Old Downloads

Periodically clean up old update files from `USER_DATA_DIR/updates/`:

- Keep only current version download
- Delete versions older than 30 days
- Or implement auto-cleanup in update service

## Build Script Enhancement (Optional)

Create `scripts/release.py` to automate:

1. Version bump
2. Build all platforms
3. Calculate checksums
4. Create GitHub release draft
5. Upload binaries
6. Generate Firebase update document JSON

## Troubleshooting

### Issue: Update not detected

- Check Firebase document `app_updates/latest` exists and `is_available = true`
- Verify version comparison logic (semantic versioning)
- Check app logs for update service errors
- Verify user is logged in

### Issue: Download fails

- Check internet connectivity
- Verify GitHub release URL is accessible
- Check file size matches Firebase `file_size`
- Verify GitHub token/permissions for private repos

### Issue: Checksum verification fails

- Recalculate checksum of uploaded file
- Verify checksum in Firebase matches actual file
- Check for file corruption during download

### Issue: Installation fails

- Verify platform-specific installation logic
- Check file permissions (Linux/macOS)
- Verify installer has proper permissions
- Check app logs for installation errors

## Best Practices

1. **Version Naming**: Always use semantic versioning (MAJOR.MINOR.PATCH)
2. **Testing**: Test update flow on each platform before releasing
3. **Staged Rollout**: Consider adding `rollout_percentage` field for gradual releases
4. **Release Notes**: Always provide clear release notes in Firebase
5. **Backward Compatibility**: Consider `min_version_required` for breaking changes
6. **Monitoring**: Track update adoption rate via database queries
7. **Security**: Always verify checksums before installation
8. **User Communication**: Provide clear toast messages about updates