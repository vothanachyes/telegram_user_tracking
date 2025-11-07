<!-- a6182a1a-50b9-404a-be45-a1c9ddc48e0e c1cfe134-59c4-4d19-a0e3-d939bfad93b9 -->
# Database Refactoring Plan

## Overview

Refactor `database/db_manager.py` (1164 lines) and `database/models.py` (338 lines) into smaller, domain-organized modules for better maintainability and developer experience.

## Structure

### New Directory Structure

```
database/
├── __init__.py              # Re-exports for backward compatibility
├── models/
│   ├── __init__.py          # Re-exports all models
│   ├── app_settings.py      # AppSettings model
│   ├── telegram.py          # TelegramCredential, TelegramGroup, TelegramUser
│   ├── message.py           # Message, Reaction models
│   ├── media.py             # MediaFile model
│   ├── auth.py              # LoginCredential, UserLicenseCache models
│   ├── deleted.py           # DeletedMessage, DeletedUser models
│   └── schema.py            # CREATE_TABLES_SQL constant
├── managers/
│   ├── __init__.py          # Re-exports DatabaseManager
│   ├── base.py              # BaseDatabaseManager with connection, migrations, helpers
│   ├── settings_manager.py  # App settings operations
│   ├── telegram_credential_manager.py  # Telegram credentials
│   ├── group_manager.py     # Telegram groups
│   ├── user_manager.py      # Telegram users
│   ├── message_manager.py   # Messages
│   ├── media_manager.py     # Media files
│   ├── reaction_manager.py  # Reactions
│   ├── stats_manager.py     # Statistics and user activity
│   ├── auth_manager.py      # Login credentials
│   ├── license_manager.py   # License cache
│   └── db_manager.py        # Main DatabaseManager (composes all managers)
└── migrations/              # (existing)
```

## Implementation Steps

### Phase 1: Models Refactoring

1. **Create `database/models/` directory structure**

   - Create `__init__.py` that re-exports all models
   - Split models into domain files:
     - `app_settings.py`: AppSettings
     - `telegram.py`: TelegramCredential, TelegramGroup, TelegramUser
     - `message.py`: Message, Reaction
     - `media.py`: MediaFile
     - `auth.py`: LoginCredential, UserLicenseCache
     - `deleted.py`: DeletedMessage, DeletedUser
     - `schema.py`: CREATE_TABLES_SQL constant

2. **Update `database/models/__init__.py`**

   - Import all models from their respective files
   - Export CREATE_TABLES_SQL
   - Maintain same public API as current `models.py`

### Phase 2: Database Managers Refactoring

3. **Create `database/managers/base.py`**

   - Extract helper functions: `_safe_get_row_value`, `_parse_datetime`
   - Create `BaseDatabaseManager` class with:
     - `__init__` (db_path, connection setup)
     - `_ensure_db_directory`
     - `_init_database`
     - `_run_migrations`
     - `get_connection`

4. **Create domain manager files**

Each manager inherits from `BaseDatabaseManager` and contains methods for its domain:

   - `settings_manager.py`: `get_settings`, `update_settings`
   - `telegram_credential_manager.py`: `save_telegram_credential`, `get_telegram_credentials`, `get_default_credential`
   - `group_manager.py`: `save_group`, `get_all_groups`, `get_group_by_id`
   - `user_manager.py`: `save_user`, `get_all_users`, `get_user_by_id`, `get_users_by_group`, `search_users`, `soft_delete_user`
   - `message_manager.py`: `save_message`, `get_messages`, `get_message_count`, `soft_delete_message`, `is_message_deleted`
   - `media_manager.py`: `save_media_file`, `get_media_for_message`, `get_total_media_size`
   - `reaction_manager.py`: `save_reaction`, `get_reactions_by_message`, `get_reactions_by_user`, `delete_reaction`
   - `stats_manager.py`: `get_dashboard_stats`, `get_user_activity_stats`, `get_message_type_breakdown`
   - `auth_manager.py`: `save_login_credential`, `get_login_credential`, `delete_login_credential`
   - `license_manager.py`: `save_license_cache`, `get_license_cache`, `delete_license_cache`

5. **Create `database/managers/db_manager.py`**

   - Main `DatabaseManager` class that inherits from `BaseDatabaseManager`
   - Composes all domain managers as mixins or delegates to them
   - Maintains same public API as current `DatabaseManager`

6. **Update `database/managers/__init__.py`**

   - Export `DatabaseManager` for backward compatibility

### Phase 3: Backward Compatibility

7. **Update `database/__init__.py`**

   - Import from new locations
   - Maintain same exports as before

8. **Update `database/models.py` (deprecated)**

   - Add deprecation warning
   - Re-export from `models/__init__.py` for transition period

9. **Update `database/db_manager.py` (deprecated)**

   - Add deprecation warning
   - Re-export from `managers/db_manager.py` for transition period

### Phase 4: Testing & Cleanup

10. **Verify all imports work**

    - Test that existing code still works without changes
    - Verify `database/__init__.py` exports are correct

11. **Update documentation**

    - Update any inline comments referencing file structure
    - Ensure migration notes are clear

## Key Design Decisions

1. **Backward Compatibility**: All existing imports continue to work via `database/__init__.py` and `database/models/__init__.py`

2. **Composition Pattern**: Main `DatabaseManager` composes domain managers rather than using inheritance to avoid diamond problem

3. **Shared Utilities**: Helper functions and base class in `managers/base.py` to avoid duplication

4. **File Size Target**: Each file should be < 300 lines for better maintainability

5. **Migration Strategy**: Keep old files with deprecation warnings for one release cycle, then remove

## Files to Create

- `database/models/__init__.py`
- `database/models/app_settings.py`
- `database/models/telegram.py`
- `database/models/message.py`
- `database/models/media.py`
- `database/models/auth.py`
- `database/models/deleted.py`
- `database/models/schema.py`
- `database/managers/__init__.py`
- `database/managers/base.py`
- `database/managers/settings_manager.py`
- `database/managers/telegram_credential_manager.py`
- `database/managers/group_manager.py`
- `database/managers/user_manager.py`
- `database/managers/message_manager.py`
- `database/managers/media_manager.py`
- `database/managers/reaction_manager.py`
- `database/managers/stats_manager.py`
- `database/managers/auth_manager.py`
- `database/managers/license_manager.py`
- `database/managers/db_manager.py`

## Files to Modify

- `database/__init__.py` - Update imports
- `database/models.py` - Add deprecation, re-export
- `database/db_manager.py` - Add deprecation, re-export

## Benefits

- **Maintainability**: Each file focuses on a single domain (~100-300 lines)
- **Discoverability**: Easy to find code related to specific features
- **Testability**: Smaller units easier to test in isolation
- **Collaboration**: Multiple developers can work on different domains without conflicts
- **Backward Compatible**: No breaking changes to existing code

### To-dos

- [ ] Create database/models/ directory with __init__.py and split models into domain files (app_settings, telegram, message, media, auth, deleted, schema)
- [ ] Create database/managers/base.py with BaseDatabaseManager class containing connection management, migrations, and helper functions
- [ ] Create individual manager files (settings, telegram_credential, group, user, message, media, reaction, stats, auth, license) inheriting from BaseDatabaseManager
- [ ] Create database/managers/db_manager.py that composes all domain managers and maintains the same public API
- [ ] Update database/__init__.py and managers/__init__.py to export DatabaseManager, and models/__init__.py to export all models for backward compatibility
- [ ] Add deprecation warnings to old database/models.py and database/db_manager.py files that re-export from new locations
- [ ] Test that all existing imports still work correctly and verify no breaking changes