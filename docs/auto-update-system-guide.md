# Auto-Update System Guide

## Overview

The auto-update system automatically checks Firebase for new app versions, downloads updates in the background, and notifies users when updates are available. The system only works for logged-in users and prevents installation during active fetch operations.

## Features

- ✅ Automatic background checking (every 1 hour)
- ✅ Auto-downloads updates when available
- ✅ SHA256 checksum verification for security
- ✅ Platform-specific support (Windows, macOS, Linux)
- ✅ Toast notifications with Ignore/Install buttons
- ✅ Prevents installation during fetch operations
- ✅ Tracks installations per user in database
- ✅ Only works for logged-in users

## Architecture

### Components

1. **Update Service** (`services/update_service.py`)
   - Background service that checks Firebase every hour
   - Downloads updates automatically
   - Verifies checksums
   - Handles platform-specific installation

2. **Update Manager** (`database/managers/update_manager.py`)
   - Tracks update installations in database
   - Records user email, version, and download path

3. **Version Utility** (`utils/version_utils.py`)
   - Semantic versioning comparison
   - Parses and compares version strings

4. **Update Toast** (`ui/components/update_toast.py`)
   - Custom toast notification with action buttons
   - Shows version and file size

5. **Firebase Integration** (`config/firebase_config.py`)
   - Fetches update info from Firestore
   - Reads from `app_updates/latest` document

## Setup Instructions

### 1. Firebase Configuration

Create a Firestore collection and document:

**Collection**: `app_updates`  
**Document**: `latest`

**Document Structure**:
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
  "checksum_windows": "abc123def456...",
  "checksum_macos": "def456ghi789...",
  "checksum_linux": "ghi789jkl012...",
  "release_notes": "Bug fixes and performance improvements",
  "min_version_required": "1.0.0"
}
```

### 2. Field Descriptions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `version` | string | Yes | Semantic version (e.g., "1.0.1") |
| `download_url_windows` | string | Yes | GitHub release URL for Windows .exe |
| `download_url_macos` | string | Yes | GitHub release URL for macOS .dmg/.app |
| `download_url_linux` | string | Yes | GitHub release URL for Linux binary |
| `release_date` | timestamp | No | When update was released |
| `is_available` | boolean | Yes | Whether update is currently available |
| `file_size_windows` | number | No | File size in bytes (Windows) |
| `file_size_macos` | number | No | File size in bytes (macOS) |
| `file_size_linux` | number | No | File size in bytes (Linux) |
| `checksum_windows` | string | Yes | SHA256 checksum (Windows) |
| `checksum_macos` | string | Yes | SHA256 checksum (macOS) |
| `checksum_linux` | string | Yes | SHA256 checksum (Linux) |
| `release_notes` | string | No | Optional release notes |
| `min_version_required` | string | No | Minimum version that can update |

### 3. Calculate Checksums

For each platform binary, calculate SHA256 checksum:

**Windows (PowerShell)**:
```powershell
Get-FileHash -Path "dist\TelegramUserTracking.exe" -Algorithm SHA256
```

**macOS/Linux**:
```bash
shasum -a 256 dist/TelegramUserTracking
# or
sha256sum dist/TelegramUserTracking
```

### 4. Create GitHub Release

1. Go to GitHub repository → Releases → Draft a new release
2. Tag version: `v1.0.1` (must match `version` in Firebase)
3. Release title: `Version 1.0.1` or descriptive title
4. Release notes: Add changelog/features
5. Upload binaries:
   - `TelegramUserTracking-v1.0.1-windows.exe`
   - `TelegramUserTracking-v1.0.1-macos.dmg`
   - `TelegramUserTracking-v1.0.1-linux`
6. Publish release (private release)

### 5. Get Download URLs

After publishing, get direct download URLs:
- Right-click on uploaded file → "Copy link address"
- Format: `https://github.com/OWNER/REPO/releases/download/v1.0.1/TelegramUserTracking-v1.0.1-windows.exe`

**Note**: For private repos, you may need to use GitHub API with authentication or use a different hosting method.

## How It Works

### Update Check Flow

1. **User logs in** → Update service starts
2. **Every 1 hour** → Service checks Firebase for updates
3. **If update available**:
   - Compares current version with latest version
   - Downloads update file to `USER_DATA_DIR/updates/`
   - Verifies SHA256 checksum
   - Shows toast notification with [Ignore, Install] buttons
4. **User clicks Install**:
   - Checks if fetch is running (blocks if running)
   - Launches platform-specific installer
   - Records installation in database
5. **User logs out** → Update service stops

### Update Service Lifecycle

```
App Start → Initialize Service → User Login → Start Service → Check Every Hour
                                                                    ↓
                                                              Update Available?
                                                                    ↓
                                                              Download & Verify
                                                                    ↓
                                                              Show Toast
                                                                    ↓
                                                              User Clicks Install
                                                                    ↓
                                                              Check Fetch State
                                                                    ↓
                                                              Launch Installer
                                                                    ↓
                                                              Record Installation
```

## Testing

### Test Scenario 1: Normal Update Flow

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

### Test Scenario 2: Update During Fetch

1. **Start fetch operation**
2. **Trigger update check** (or wait for auto-check)
3. **Download completes**, toast shows
4. **Click Install**:
   - Should show error: "Cannot install update while fetch is in progress"
   - Install button disabled or shows error message
5. **Stop fetch**
6. **Click Install again**:
   - Should work now

### Test Scenario 3: Checksum Verification

1. **Manually corrupt download file** in `USER_DATA_DIR/updates/`
2. **Trigger install**:
   - Should detect checksum mismatch
   - Delete corrupted file
   - Re-download automatically
   - Verify checksum again

### Test Scenario 4: Multiple Users

1. **User A installs update** → Recorded in database
2. **User B installs same update** → Separate record in database
3. **Verify** both users have records in `app_update_history`

### Manual Testing

To manually trigger an update check (for testing):

```python
# In Python console or test script
from services.update_service import UpdateService
from database.db_manager import DatabaseManager

db_manager = DatabaseManager()
update_service = UpdateService(db_manager, page=page)

# Start service
await update_service.start()

# Manually check for updates
update_info = await update_service.check_for_updates()
```

## Database Schema

### app_update_history Table

```sql
CREATE TABLE app_update_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_email TEXT NOT NULL,
    version TEXT NOT NULL,
    installed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    download_path TEXT,
    UNIQUE(user_email, version)
);
```

### Query Examples

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

## Configuration

### Constants

Located in `utils/constants.py`:

```python
UPDATE_CHECK_INTERVAL_SECONDS = 3600  # 1 hour
UPDATES_DIR_NAME = "updates"
FIREBASE_APP_UPDATES_COLLECTION = "app_updates"
FIREBASE_APP_UPDATES_DOCUMENT = "latest"
```

### Update Directory

Updates are downloaded to:
- **Windows**: `%APPDATA%\Telegram User Tracking\updates\`
- **macOS**: `~/Library/Application Support/Telegram User Tracking/updates/`
- **Linux**: `~/.config/Telegram User Tracking/updates/`

## Troubleshooting

### Issue: Update not detected

**Possible causes**:
- Firebase document `app_updates/latest` doesn't exist
- `is_available` is set to `false`
- Version comparison logic issue
- User is not logged in

**Solutions**:
1. Check Firebase document exists and `is_available = true`
2. Verify version comparison (semantic versioning)
3. Check app logs for update service errors
4. Verify user is logged in

### Issue: Download fails

**Possible causes**:
- Internet connectivity issues
- GitHub release URL is inaccessible
- File size mismatch
- GitHub token/permissions for private repos

**Solutions**:
1. Check internet connectivity
2. Verify GitHub release URL is accessible
3. Check file size matches Firebase `file_size`
4. Verify GitHub token/permissions for private repos

### Issue: Checksum verification fails

**Possible causes**:
- Checksum in Firebase doesn't match actual file
- File corruption during download

**Solutions**:
1. Recalculate checksum of uploaded file
2. Verify checksum in Firebase matches actual file
3. Check for file corruption during download
4. System will automatically re-download if checksum fails

### Issue: Installation fails

**Possible causes**:
- Platform-specific installation logic issue
- File permissions (Linux/macOS)
- Installer doesn't have proper permissions

**Solutions**:
1. Verify platform-specific installation logic
2. Check file permissions (Linux/macOS: `chmod +x`)
3. Verify installer has proper permissions
4. Check app logs for installation errors

### Issue: Toast not showing

**Possible causes**:
- Toast component not initialized
- Page reference not set
- Error in toast creation

**Solutions**:
1. Check toast component is initialized
2. Verify page reference is set
3. Check app logs for toast errors
4. Verify update service callback is working

## Rollback Procedure

If an update has issues:

1. **Set `is_available` to `false`** in Firebase:
   ```json
   {
     "is_available": false
   }
   ```

2. **Or update to previous version** in Firebase document

3. **Users won't get update** until `is_available` is `true` again

## Best Practices

1. **Version Naming**: Always use semantic versioning (MAJOR.MINOR.PATCH)
2. **Testing**: Test update flow on each platform before releasing
3. **Staged Rollout**: Consider adding `rollout_percentage` field for gradual releases
4. **Release Notes**: Always provide clear release notes in Firebase
5. **Backward Compatibility**: Consider `min_version_required` for breaking changes
6. **Monitoring**: Track update adoption rate via database queries
7. **Security**: Always verify checksums before installation
8. **User Communication**: Provide clear toast messages about updates

## Security Considerations

- ✅ Checksums are verified before installation
- ✅ Only downloads from trusted GitHub release URLs
- ✅ Version strings are validated before comparison
- ✅ Only allows updates for logged-in users
- ✅ Downloads stored in secure user data directory
- ✅ Prevents installation during critical operations (fetch)

## Platform-Specific Installation

### Windows
- Downloads `.exe` to `USER_DATA_DIR/updates/`
- Launches installer: `subprocess.Popen([exe_path])`
- Installer should handle replacing current executable

### macOS
- Downloads `.dmg` or `.app` to `USER_DATA_DIR/updates/`
- For `.dmg`: Mounts and copies `.app` to Applications
- For `.app`: Copies to Applications folder

### Linux
- Downloads binary or `.AppImage` to `USER_DATA_DIR/updates/`
- Makes executable: `chmod +x`
- Replaces current binary or updates symlink

## Monitoring

### Check Update Installations

```sql
SELECT 
    version,
    COUNT(*) as install_count,
    MIN(installed_at) as first_install,
    MAX(installed_at) as latest_install
FROM app_update_history
GROUP BY version
ORDER BY latest_install DESC;
```

### Check User Adoption

```sql
SELECT 
    user_email,
    COUNT(*) as total_updates,
    MAX(installed_at) as last_update
FROM app_update_history
GROUP BY user_email
ORDER BY last_update DESC;
```

## Cleanup

Periodically clean up old update files from `USER_DATA_DIR/updates/`:
- Keep only current version download
- Delete versions older than 30 days
- Or implement auto-cleanup in update service

## Support

For issues or questions:
1. Check app logs (`app.log`)
2. Verify Firebase configuration
3. Check database for installation records
4. Review update service logs

## Related Files

- `services/update_service.py` - Main update service
- `database/managers/update_manager.py` - Database operations
- `ui/components/update_toast.py` - Toast notifications
- `utils/version_utils.py` - Version comparison
- `config/firebase_config.py` - Firebase integration
- `ui/app.py` - Service initialization and lifecycle

