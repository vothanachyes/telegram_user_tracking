# Current Directory Structure (With Custom .env Configuration)

Based on your `.env` file configuration:

```env
APP_DATA_DIR=./xvothana
DEFAULT_DOWNLOAD_DIR=./xvothana/downloads
DATABASE_PATH=./xvothana/data/app.db
```

## Actual Directory Structure

```
telegram_user_tracking/              # BASE_DIR (project root)
├── .env                             # Your environment variables
├── main.py
├── requirements.txt
├── README.md
│
└── xvothana/                        # APP_DATA_DIR (custom, from .env)
    ├── logs/                        # Category-based logs
    │   ├── database/
    │   │   └── YYYY-MM-DD.log
    │   ├── firebase/
    │   │   └── YYYY-MM-DD.log
    │   ├── telegram/
    │   │   └── YYYY-MM-DD.log
    │   ├── flet/
    │   │   └── YYYY-MM-DD.log
    │   └── general/
    │       └── YYYY-MM-DD.log
    │
    ├── sessions/                    # Telegram session files
    │   ├── session_85512345678.session
    │   └── session_85598765432.session
    │
    ├── data/                        # Database directory (from DATABASE_PATH)
    │   └── app.db                   # Your database file
    │
    ├── downloads/                   # Download directory (from DEFAULT_DOWNLOAD_DIR)
    │   └── {group_id}/
    │       └── {username}/
    │           └── {date}/
    │               └── {message_id}_{time}/
    │                   ├── photo_123.jpg
    │                   ├── video_456.mp4
    │                   └── document_789.pdf
    │
    └── sample_db/                   # Sample database (if used)
        └── app.db

# Per-user databases (if Firebase authenticated)
%APPDATA%\Telegram User Tracking\databases\
└── app_{firebase_uid}.db            # USER_DATA_DIR/databases/
```

## Key Points

### 1. **xvothana/** (APP_DATA_DIR)
- **Location**: Project root (`./xvothana`)
- **Contains**:
  - `logs/` - All application logs (category-based)
  - `sessions/` - Telegram session files
  - `sample_db/` - Sample database (if used)
- **Created**: Automatically when app runs

### 2. **xvothana/data/** (Database Directory)
- **Location**: Inside xvothana (`./xvothana/data`)
- **Contains**:
  - `app.db` - Your database file
- **Created**: Automatically (with auto-fix if file conflict exists)
- **Source**: `DATABASE_PATH=./xvothana/data/app.db` in `.env`

### 3. **xvothana/downloads/** (Download Directory)
- **Location**: Inside xvothana (`./xvothana/downloads`)
- **Contains**: Media files organized by group/user/date
- **Created**: Automatically when first download starts
- **Source**: `DEFAULT_DOWNLOAD_DIR=./xvothana/downloads` in `.env`

## Path Relationships

| Setting | Value | Actual Path | Purpose |
|---------|-------|-------------|---------|
| `APP_DATA_DIR` | `./xvothana` | `telegram_user_tracking/xvothana/` | Logs, sessions, sample_db |
| `DATABASE_PATH` | `./xvothana/data/app.db` | `telegram_user_tracking/xvothana/data/app.db` | Main database |
| `DEFAULT_DOWNLOAD_DIR` | `./xvothana/downloads` | `telegram_user_tracking/xvothana/downloads/` | Media downloads |

## Important Notes

1. **All paths are relative** - They're relative to the project root (`BASE_DIR`)
2. **Auto-creation** - All directories are created automatically when needed
3. **Database auto-fix** - If a file named `data` exists, it will be automatically moved to `data/app.db`
4. **Per-user databases** - Still stored in `USER_DATA_DIR/databases/` (not affected by `.env`)

## When Directories Are Created

- **xvothana/**: Created when first log is written or first session is saved
- **xvothana/data/**: Created when database is initialized (with auto-fix for conflicts)
- **xvothana/downloads/**: Created when first download starts

## Customization

You can change these paths in your `.env` file:

```env
# Change app data directory (logs, sessions)
APP_DATA_DIR=./my_custom_dir

# Change database location (keep inside APP_DATA_DIR for organization)
DATABASE_PATH=./my_custom_dir/data/app.db

# Change download directory (keep inside APP_DATA_DIR for organization)
DEFAULT_DOWNLOAD_DIR=./my_custom_dir/downloads
```

**Note**: After changing `.env`, restart the application for changes to take effect.

