# Production vs Development Path Behavior

## Overview

The application behaves differently in **development** vs **production** environments, especially regarding file paths and Windows Store Python virtualization.

---

## Development Mode

### Detection
- `sys.frozen = False` (running from Python source)
- Uses Windows Store Python (if installed from Microsoft Store)

### Path Behavior

#### Windows Store Python Virtualization
When using **Windows Store Python**, `%APPDATA%` is virtualized:

**Expected Path:**
```
C:\Users\{Username}\AppData\Roaming\Telegram User Tracking\databases\app_{uid}.db
```

**Actual Physical Location:**
```
C:\Users\{Username}\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.13_qbz5n2kfra8p0\LocalCache\Roaming\Telegram User Tracking\databases\app_{uid}.db
```

**Why?**
- Windows Store Python uses file system virtualization for security/isolation
- Files written to `%APPDATA%` are redirected to `LocalCache\Roaming`
- `Path.resolve()` follows this redirection and shows the actual physical location
- **This is normal behavior** - the database works correctly, just in a virtualized location

### Development Paths

| Directory | Location |
|-----------|----------|
| **Database** (per-user) | `USER_DATA_DIR/databases/app_{uid}.db` → Resolves to LocalCache |
| **Database** (fallback) | `USER_DATA_DIR/app.db` → Resolves to LocalCache |
| **Sessions** | `APP_DATA_DIR/sessions/` (project root or custom) |
| **Logs** | `APP_DATA_DIR/logs/` (project root or custom) |
| **Downloads** | `DEFAULT_DOWNLOAD_DIR` (from .env or USER_DATA_DIR) |

---

## Production Mode

### Detection
- `sys.frozen = True` (running from PyInstaller executable)
- Uses standard Windows environment (no virtualization)

### Path Behavior

#### Standard Windows Paths
In production, the executable is **NOT** using Windows Store Python:

**Database Path:**
```
C:\Users\{Username}\AppData\Roaming\Telegram User Tracking\databases\app_{uid}.db
```

**No Virtualization:**
- `%APPDATA%` resolves directly to `C:\Users\{Username}\AppData\Roaming`
- No LocalCache redirection
- `Path.resolve()` shows the same path as the original
- Files are stored in the standard Windows location

### Production Paths

| Directory | Location |
|-----------|----------|
| **Database** (per-user) | `USER_DATA_DIR/databases/app_{uid}.db` → Standard AppData\Roaming |
| **Database** (fallback) | `USER_DATA_DIR/app.db` → Standard AppData\Roaming |
| **Sessions** | `USER_DATA_DIR/sessions/` (same as USER_DATA_DIR) |
| **Logs** | `USER_DATA_DIR/logs/` (same as USER_DATA_DIR) |
| **Downloads** | `USER_DATA_DIR/downloads` (or custom from settings) |

**Note:** In production, `APP_DATA_DIR = USER_DATA_DIR`, so all data is in one location.

---

## Comparison

| Aspect | Development | Production |
|--------|-------------|------------|
| **Python** | Windows Store Python | Standard Python (bundled) |
| **Virtualization** | ✅ Yes (LocalCache) | ❌ No (standard paths) |
| **APPDATA Resolution** | Redirects to LocalCache | Direct to AppData\Roaming |
| **Path.resolve()** | Shows LocalCache path | Shows same as original |
| **Database Location** | `LocalCache\Roaming\...` | `AppData\Roaming\...` |
| **Works Correctly?** | ✅ Yes | ✅ Yes |

---

## Why This Matters

### Development
- Files are in a virtualized location (LocalCache)
- This is **normal** and **expected** with Windows Store Python
- The database works correctly
- Logs show both original and resolved paths for clarity

### Production
- Files are in standard Windows locations
- No virtualization issues
- Easier to find and backup user data
- Standard Windows application behavior

---

## Verification

### Check Current Mode
```python
import sys
is_production = getattr(sys, 'frozen', False)
print(f"Mode: {'PRODUCTION' if is_production else 'DEVELOPMENT'}")
```

### Check Database Path
```python
from utils.database_path import get_user_database_path
from pathlib import Path

path = get_user_database_path("test_uid")
print(f"Original: {path}")
print(f"Resolved: {Path(path).resolve()}")
print(f"Same? {path == str(Path(path).resolve())}")
```

**Development Output:**
```
Original: C:\Users\...\AppData\Roaming\Telegram User Tracking\databases\app_test_uid.db
Resolved: C:\Users\...\LocalCache\Roaming\Telegram User Tracking\databases\app_test_uid.db
Same? False
```

**Production Output:**
```
Original: C:\Users\...\AppData\Roaming\Telegram User Tracking\databases\app_test_uid.db
Resolved: C:\Users\...\AppData\Roaming\Telegram User Tracking\databases\app_test_uid.db
Same? True
```

---

## Summary

✅ **Production works fine** - No virtualization, standard Windows paths  
✅ **Development works fine** - Virtualization is normal for Windows Store Python  
✅ **Both modes are correct** - The difference is just where files are physically stored

The application handles both scenarios correctly. In production, you'll see the standard `AppData\Roaming` location without any LocalCache redirection.

