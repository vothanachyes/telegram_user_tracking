# Directory Structure Guide

This document explains the directory structure for the Telegram User Tracking application in both **development** and **production** environments.

## Table of Contents

- [Overview](#overview)
- [Key Directory Types](#key-directory-types)
- [Development Environment](#development-environment)
- [Production Environment](#production-environment)
- [Directory Details](#directory-details)
- [Path Customization](#path-customization)
- [Platform-Specific Paths](#platform-specific-paths)

---

## Overview

The application uses different directory structures depending on the environment:

- **Development**: Uses project root directory for most data
- **Production**: Uses platform-specific user data directories for secure storage

### Key Concepts

- **`BASE_DIR`**: Project root directory (where the code is located)
- **`USER_DATA_DIR`**: Platform-specific secure directory for user data
- **`APP_DATA_DIR`**: Application data directory (logs, sessions, etc.)

---

## Key Directory Types

### 1. **USER_DATA_DIR** (Secure User Data)
Platform-specific directory for secure user data storage:
- **Windows**: `%APPDATA%\Telegram User Tracking`
- **macOS**: `~/Library/Application Support/Telegram User Tracking`
- **Linux**: `~/.config/Telegram User Tracking`

**Used for:**
- Per-user databases (Firebase authenticated users)
- Fallback databases (non-authenticated users)
- Default download directory

### 2. **APP_DATA_DIR** (Application Data)
Directory for application runtime data:
- **Development**: `BASE_DIR` (project root)
- **Production**: `USER_DATA_DIR` (same as secure user data)

**Used for:**
- Log files
- Telegram session files
- Sample database

### 3. **BASE_DIR** (Project Root)
The root directory of the project source code.

---

## Development Environment

### Directory Structure

```
telegram_user_tracking/          # BASE_DIR (project root)
├── .env                         # Environment variables
├── main.py                      # Application entry point
├── requirements.txt
├── README.md
│
├── data/                        # (Optional, if DATABASE_PATH set to ./data/app.db)
│   └── app.db                   # Fallback database (if not using Firebase)
│
├── sessions/                    # APP_DATA_DIR/sessions
│   ├── session_85512345678.session
│   └── session_85598765432.session
│
├── logs/                        # APP_DATA_DIR/logs
│   ├── database/
│   │   └── 2024-01-15.log
│   ├── firebase/
│   │   └── 2024-01-15.log
│   ├── telegram/
│   │   └── 2024-01-15.log
│   ├── flet/
│   │   └── 2024-01-15.log
│   └── general/
│       └── 2024-01-15.log
│
├── sample_db/                   # APP_DATA_DIR/sample_db
│   └── app.db                   # Sample database
│
└── downloads/                   # Default download directory (if not customized)
    └── {group_id}/
        └── {username}/
            └── {date}/
                └── {message_id}_{time}/
                    └── media_files...

# Per-user databases (if Firebase authenticated)
%APPDATA%\Telegram User Tracking\databases\
└── app_{firebase_uid}.db        # USER_DATA_DIR/databases/
```

### Path Resolution in Development

| Directory Type | Default Path | Customizable? |
|---------------|--------------|---------------|
| **Database** (per-user) | `USER_DATA_DIR/databases/app_{uid}.db` | ✅ Via Settings |
| **Database** (fallback) | `USER_DATA_DIR/app.db` | ✅ Via Settings |
| **Sample Database** | `BASE_DIR/sample_db/app.db` | ❌ No |
| **Sessions** | `BASE_DIR/sessions/` | ❌ No |
| **Logs** | `BASE_DIR/logs/` | ❌ No |
| **Downloads** | `USER_DATA_DIR/downloads` | ✅ Via Settings |

### Environment Variables (Development)

You can override paths using `.env` file:

```env
# Database path (for development convenience)
DATABASE_PATH=./data/app.db

# Download directory
DEFAULT_DOWNLOAD_DIR=./downloads

# Custom app data directory
APP_DATA_DIR=./custom_app_data
```

**Note**: In development, `DATABASE_PATH` from `.env` can be used to skip Firebase login for testing.

---

## Production Environment

### Directory Structure

#### Windows

```
C:\Users\{Username}\AppData\Roaming\Telegram User Tracking\  # USER_DATA_DIR
├── .env                        # (Optional) Environment variables for bundled app
│
├── databases\                  # Per-user databases
│   ├── app_abc123xyz.db        # Firebase user 1
│   └── app_def456uvw.db        # Firebase user 2
│
├── app.db                      # Fallback database (non-authenticated)
│
├── sessions\                   # APP_DATA_DIR/sessions (same as USER_DATA_DIR)
│   ├── session_85512345678.session
│   └── session_85598765432.session
│
├── logs\                       # APP_DATA_DIR/logs
│   ├── database\
│   │   └── 2024-01-15.log
│   ├── firebase\
│   │   └── 2024-01-15.log
│   ├── telegram\
│   │   └── 2024-01-15.log
│   ├── flet\
│   │   └── 2024-01-15.log
│   └── general\
│       └── 2024-01-15.log
│
├── downloads\                  # Default download directory
│   └── {group_id}/
│       └── {username}/
│           └── {date}/
│               └── {message_id}_{time}/
│                   └── media_files...
│
└── sample_db\                  # Sample database (if used)
    └── app.db
```

#### macOS

```
~/Library/Application Support/Telegram User Tracking/  # USER_DATA_DIR
├── databases/
│   └── app_{firebase_uid}.db
├── app.db
├── sessions/
├── logs/
├── downloads/
└── sample_db/
```

#### Linux

```
~/.config/Telegram User Tracking/  # USER_DATA_DIR
├── databases/
│   └── app_{firebase_uid}.db
├── app.db
├── sessions/
├── logs/
├── downloads/
└── sample_db/
```

### Path Resolution in Production

| Directory Type | Default Path | Customizable? |
|---------------|--------------|---------------|
| **Database** (per-user) | `USER_DATA_DIR/databases/app_{uid}.db` | ✅ Via Settings |
| **Database** (fallback) | `USER_DATA_DIR/app.db` | ✅ Via Settings |
| **Sample Database** | `USER_DATA_DIR/sample_db/app.db` | ❌ No |
| **Sessions** | `USER_DATA_DIR/sessions/` | ❌ No |
| **Logs** | `USER_DATA_DIR/logs/` | ❌ No |
| **Downloads** | `USER_DATA_DIR/downloads` | ✅ Via Settings |

**Note**: In production, `APP_DATA_DIR = USER_DATA_DIR`, so all application data is stored in the secure user directory.

---

## Directory Details

### 1. Database Directory

#### Per-User Databases (Firebase Authenticated)

**Path**: `USER_DATA_DIR/databases/app_{firebase_uid}.db`

- Created automatically when user logs in
- Each Firebase user gets their own isolated database
- Database path is generated dynamically based on Firebase UID
- Stored in `databases/` subdirectory

**Example**:
```
Windows: C:\Users\John\AppData\Roaming\Telegram User Tracking\databases\app_abc123xyz.db
macOS:   ~/Library/Application Support/Telegram User Tracking/databases/app_abc123xyz.db
Linux:   ~/.config/Telegram User Tracking/databases/app_abc123xyz.db
```

#### Fallback Database (Non-Authenticated)

**Path**: `USER_DATA_DIR/app.db`

- Used when Firebase is not configured
- Used when user is not logged in (if Firebase is configured but no login)
- Can be customized via Settings → Security → Database Path

#### Sample Database

**Path**: `APP_DATA_DIR/sample_db/app.db`

- Used in sample database mode
- Development: `BASE_DIR/sample_db/app.db`
- Production: `USER_DATA_DIR/sample_db/app.db`

### 2. Session Directory

**Path**: `APP_DATA_DIR/sessions/`

**Files**: `session_{phone_number}.session`

- Stores Telegram authentication sessions (Telethon format)
- One session file per Telegram account
- Session files are encrypted by Telethon internally
- **Not user-configurable**

**Example**:
```
sessions/
├── session_85512345678.session
├── session_85598765432.session
└── session_85555555555.session
```

### 3. Logs Directory

**Path**: `APP_DATA_DIR/logs/`

**Structure**:
```
logs/
├── database/
│   ├── 2024-01-15.log
│   ├── 2024-01-16.log
│   └── ...
├── firebase/
│   ├── 2024-01-15.log
│   └── ...
├── telegram/
│   ├── 2024-01-15.log
│   └── ...
├── flet/
│   └── 2024-01-15.log
└── general/
    └── 2024-01-15.log
```

- Logs are separated by category
- Daily rotation (new file each day)
- **Not user-configurable**

### 4. Downloads Directory

**Path**: `AppSettings.download_root_dir` (stored in database)

**Default**: `USER_DATA_DIR/downloads`

**Structure**:
```
downloads/
└── {group_id}/
    └── {username}/
        └── {date}/
            └── {message_id}_{time}/
                ├── photo_123.jpg
                ├── video_456.mp4
                └── document_789.pdf
```

- **User-configurable** via Settings → Configure → Download Directory
- Changes take effect immediately (no restart required)
- Existing downloads are not moved when path changes

---

## Path Customization

### Database Path Customization

**Location**: Settings → Security → Database Path

**Process**:
1. User selects new database path
2. System validates path
3. Database is migrated from old to new location
4. New path is saved to `AppSettings.db_path` in database
5. **Restart required** for changes to take effect

**Important Notes**:
- Database migration preserves all data
- If database is encrypted, encryption key is used during migration
- Old database file is not automatically deleted
- Per-user databases (Firebase authenticated) cannot be changed via settings (they use dynamic paths)

**Storage**: Custom path stored in `AppSettings.db_path` (database table)

### Download Directory Customization

**Location**: Settings → Configure → Download Directory

**Process**:
1. User enters new download directory path
2. System validates path
3. New path is saved to `AppSettings.download_root_dir` in database
4. **Takes effect immediately** (no restart required)
5. New downloads use new path
6. Existing downloads remain in old location

**Storage**: Custom path stored in `AppSettings.download_root_dir` (database table)

---

## Platform-Specific Paths

### Windows

```python
USER_DATA_DIR = %APPDATA%\Telegram User Tracking
# Example: C:\Users\John\AppData\Roaming\Telegram User Tracking
```

### macOS

```python
USER_DATA_DIR = ~/Library/Application Support/Telegram User Tracking
# Example: /Users/john/Library/Application Support/Telegram User Tracking
```

### Linux

```python
USER_DATA_DIR = ~/.config/Telegram User Tracking
# Example: /home/john/.config/Telegram User Tracking
```

---

## Path Resolution Priority

### Database Path Resolution

1. **Sample DB Mode**: `SAMPLE_DATABASE_PATH` (if enabled)
2. **Custom Path**: `AppSettings.db_path` (if set in settings)
3. **Per-User DB**: `USER_DATA_DIR/databases/app_{firebase_uid}.db` (if Firebase authenticated)
4. **Fallback**: `DATABASE_PATH` constant (from `.env` or default)

### Download Path Resolution

1. **Custom Path**: `AppSettings.download_root_dir` (if set in settings)
2. **Default**: `DEFAULT_DOWNLOAD_DIR` constant (from `.env` or `USER_DATA_DIR/downloads`)

### App Data Directory Resolution

1. **Production**: `USER_DATA_DIR` (if running from PyInstaller bundle)
2. **Custom**: `APP_DATA_DIR` env var (if set)
3. **Development**: `BASE_DIR` (project root)

---

## Environment Variables Reference

### Development (.env)

```env
# Database path (for development convenience)
DATABASE_PATH=./data/app.db

# Download directory
DEFAULT_DOWNLOAD_DIR=./downloads

# Custom app data directory
APP_DATA_DIR=./custom_app_data

# Application name (affects USER_DATA_DIR)
APP_NAME=Telegram User Tracking
```

### Production (.env in USER_DATA_DIR)

```env
# Database path (optional, usually not needed)
DATABASE_PATH=C:\Custom\Path\app.db

# Download directory (optional)
DEFAULT_DOWNLOAD_DIR=C:\Custom\Downloads

# Custom app data directory (optional)
APP_DATA_DIR=C:\Custom\AppData
```

---

## Best Practices

### Development

1. **Use default paths** for simplicity
2. **Set `DATABASE_PATH` in `.env`** to skip Firebase login during development
3. **Keep sessions in project directory** for easy access
4. **Use relative paths** in `.env` for portability

### Production

1. **Let app use default secure directories** (USER_DATA_DIR)
2. **Only customize if necessary** (e.g., network drive for downloads)
3. **Backup USER_DATA_DIR** regularly (contains all user data)
4. **Ensure write permissions** to USER_DATA_DIR

---

## Troubleshooting

### Database Not Found

**Issue**: Application cannot find database

**Solutions**:
- Check if `AppSettings.db_path` is set correctly
- Verify file permissions on database directory
- Check if database file exists at expected path
- For per-user databases, ensure user is logged in

### Session Files Not Found

**Issue**: Telegram sessions not loading

**Solutions**:
- Check `APP_DATA_DIR/sessions/` directory exists
- Verify session files have `.session` extension
- Check file permissions
- Ensure phone number format matches (no `+` in filename)

### Logs Not Writing

**Issue**: Log files not being created

**Solutions**:
- Check `APP_DATA_DIR/logs/` directory exists
- Verify write permissions
- Check disk space
- Review logging configuration

### Downloads Not Saving

**Issue**: Media files not downloading

**Solutions**:
- Check `AppSettings.download_root_dir` is valid
- Verify write permissions on download directory
- Ensure `download_media` setting is enabled
- Check media type settings (photos, videos, etc.)

---

## Summary

| Directory | Development | Production | Configurable |
|-----------|-------------|------------|--------------|
| **Database** (per-user) | `USER_DATA_DIR/databases/` | `USER_DATA_DIR/databases/` | ❌ No (dynamic) |
| **Database** (fallback) | `USER_DATA_DIR/app.db` | `USER_DATA_DIR/app.db` | ✅ Yes |
| **Sample Database** | `BASE_DIR/sample_db/` | `USER_DATA_DIR/sample_db/` | ❌ No |
| **Sessions** | `BASE_DIR/sessions/` | `USER_DATA_DIR/sessions/` | ❌ No |
| **Logs** | `BASE_DIR/logs/` | `USER_DATA_DIR/logs/` | ❌ No |
| **Downloads** | `USER_DATA_DIR/downloads` | `USER_DATA_DIR/downloads` | ✅ Yes |

---

## Related Documentation

- [QUICKSTART.md](QUICKSTART.md) - Quick start guide
- [Full_APP_Detail.md](Full_APP_Detail.md) - Complete application details
- [CODE_PROTECTION_GUIDE.md](CODE_PROTECTION_GUIDE.md) - Code protection guide

---

**Last Updated**: 2024-01-15
**Version**: 1.0.0

