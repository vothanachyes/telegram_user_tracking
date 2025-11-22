<!-- 0c1f7a77-2cf9-4c00-a3dc-6245a6d475d1 0983e21c-a189-4e4d-8cbd-5dfcf9a97628 -->
# Per-User Database Implementation Plan

## Overview

Replace the shared `app.db` with per-user database files named `app_{firebase_uid}.db`. Each Firebase user will have their own isolated database stored in `USER_DATA_DIR/databases/`. Sample database mode remains unchanged.

## Implementation Steps

### 1. Create Database Path Utility (`utils/database_path.py`)

- Create new file with `get_user_database_path(firebase_uid: Optional[str]) -> str`
- If `firebase_uid` provided: return `USER_DATA_DIR/databases/app_{firebase_uid}.db`
- If `firebase_uid` is None: return `USER_DATA_DIR/app.db` (fallback for non-authenticated)
- Ensure `databases/` directory exists
- Handle path normalization and expansion

### 2. Update AuthService (`services/auth_service.py`)

- Add method `get_user_database_path() -> Optional[str]`
- Extract `uid` from `self.current_user` if logged in
- Return user-specific database path using utility function
- Return `None` if not logged in

### 3. Update App Initialization (`ui/app.py`)

- Modify `__init__` to NOT create default database if Firebase is configured
- Only create database when user logs in (in `_on_login_success`)
- Keep sample database mode logic unchanged (lines 28-30)
- If Firebase not configured, use fallback database path

### 4. Update Login Flow (`ui/app.py` - `_on_login_success`)

- After successful authentication, get user's database path from `auth_service.get_user_database_path()`
- Create new `DatabaseManager` with user-specific path
- Reinitialize `ServiceInitializer` with new database manager
- Reinitialize `TelegramService` with new database manager
- Update `PageFactory` with new `db_manager` and `telegram_service`
- Update `update_service` with new `db_manager`
- Log database switch for debugging

### 5. Update Logout Flow (`ui/app.py` - `_on_logout`)

- Call `auth_service.logout()` to clear current user
- Stop update service
- Set `is_logged_in = False`
- Show login page (database reference will be cleared when new user logs in)
- No need to explicitly close database connections (SQLite handles this)

### 6. Update Constants (`utils/constants.py`)

- Keep `DATABASE_PATH` for backward compatibility (fallback)
- Add comment explaining per-user database structure
- Keep `SAMPLE_DATABASE_PATH` unchanged

### 7. Update Settings Manager (`config/settings.py`)

- Ensure `db_manager` property handles user-specific paths correctly
- When reloading database manager, check if user is logged in and use their database path

### 8. Handle Edge Cases

- **Firebase not configured**: Use fallback database path (existing behavior)
- **Sample database mode**: Continue using `SAMPLE_DATABASE_PATH` (no changes)
- **Auto-login with saved credentials**: Database switch happens in `_on_login_success` which is called after auto-login
- **PIN dialog after login**: Database switch happens before PIN dialog, so PIN is checked against user's database

### 9. Database File Structure

- Location: `USER_DATA_DIR/databases/app_{firebase_uid}.db`
- Each user gets isolated database with all tables (app_settings, telegram_groups, messages, etc.)
- Database initialization happens automatically when `DatabaseManager` is created with new path

### 10. Testing Considerations

- Verify each user sees only their own data
- Verify sample database mode still works
- Verify logout clears user session
- Verify login switches to correct database
- Verify database files are created in correct location

## Files to Create

- `utils/database_path.py` - Database path generation utility

## Files to Modify

- `services/auth_service.py` - Add `get_user_database_path()` method
- `ui/app.py` - Update initialization, login, and logout flows
- `utils/constants.py` - Add comments about per-user databases
- `config/settings.py` - Ensure compatibility with per-user paths

## Key Implementation Details

### Database Path Generation

```python
# utils/database_path.py
def get_user_database_path(firebase_uid: Optional[str] = None) -> str:
    if firebase_uid:
        db_dir = USER_DATA_DIR / "databases"
        db_dir.mkdir(parents=True, exist_ok=True)
        return str(db_dir / f"app_{firebase_uid}.db")
    return str(USER_DATA_DIR / "app.db")  # Fallback
```

### Login Flow Database Switch

```python
# ui/app.py - _on_login_success
user_db_path = auth_service.get_user_database_path()
if user_db_path:
    new_db_manager = DatabaseManager(user_db_path)
    # Reinitialize all services with new database
```

### Sample Database Mode

- No changes needed - continues using `SAMPLE_DATABASE_PATH`
- Checked before any user-specific database logic

## Migration Notes

- Existing `app.db` will not be used for new logins
- Each user's first login creates their own database file
- No data migration needed (users start fresh with their own database)
- Old `app.db` can remain but won't be accessed by authenticated users

### To-dos

- [ ] Create utils/database_path.py with get_user_database_path() function that generates user-specific database paths
- [ ] Add get_user_database_path() method to AuthService that returns user-specific database path when logged in
- [ ] Modify ui/app.py __init__ to not create default database when Firebase is configured, only create on login
- [ ] Update _on_login_success() in ui/app.py to switch to user-specific database and reinitialize all services
- [ ] Ensure _on_logout() in ui/app.py properly clears user session (already implemented, verify compatibility)
- [ ] Add comments to utils/constants.py explaining per-user database structure
- [ ] Verify config/settings.py db_manager property works correctly with per-user paths
- [ ] Test login/logout flows, verify database isolation, and ensure sample database mode still works