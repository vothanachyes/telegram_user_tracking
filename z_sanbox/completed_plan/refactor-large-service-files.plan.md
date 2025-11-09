<!-- e1a05a8f-4f17-4664-85e2-324de241ed2d b8d16943-cf71-41fd-bba8-949d4df489b6 -->
# Refactor Large Service Files

## Overview

Refactor four service files that exceed or approach the 400-line limit:

- `license_service.py` (477 lines) - **EXCEEDS LIMIT**
- `update_service.py` (390 lines) - **APPROACHING LIMIT**
- `media_service.py` (384 lines) - **APPROACHING LIMIT**
- `telegram/telegram_service.py` (771 lines) - **EXCEEDS LIMIT**

## Refactoring Strategy

### 1. License Service (477 lines → ~4 files)

**Current structure:**

- License status checking
- Firebase sync logic
- Limit enforcement (groups, devices, accounts)
- License info retrieval

**New structure:**

```
services/
  license_service.py (~150 lines) - Main orchestrator
  license/
    __init__.py
    license_checker.py (~150 lines) - Status checking, tier retrieval
    license_sync.py (~150 lines) - Firebase sync, cache management
    limit_enforcer.py (~150 lines) - can_add_group, can_add_device, can_add_account
```

**Responsibilities:**

- `license_service.py`: Main service class, delegates to sub-modules
- `license_checker.py`: `get_user_tier()`, `check_license_status()`, `get_license_info()`
- `license_sync.py`: `sync_from_firebase()`, cache management
- `limit_enforcer.py`: `can_add_group()`, `can_add_device()`, `can_add_account()`, `enforce_group_limit()`, `get_active_devices()`

### 2. Update Service (390 lines → ~4 files)

**Current structure:**

- Update checking
- Update downloading
- Checksum verification
- Update installation

**New structure:**

```
services/
  update_service.py (~150 lines) - Main orchestrator
  update/
    __init__.py
    update_checker.py (~100 lines) - check_for_updates(), _update_loop()
    update_downloader.py (~100 lines) - download_update(), verify_checksum()
    update_installer.py (~100 lines) - install_update(), platform-specific logic
```

**Responsibilities:**

- `update_service.py`: Main service class, lifecycle management (start/stop)
- `update_checker.py`: `check_for_updates()`, `_update_loop()`
- `update_downloader.py`: `download_update()`, `verify_checksum()`
- `update_installer.py`: `install_update()`, platform-specific installation logic

### 3. Media Service (384 lines → ~4 files)

**Current structure:**

- Media downloading (photos, videos, documents, audio)
- Thumbnail creation
- Media management (get, delete)

**New structure:**

```
services/
  media_service.py (~100 lines) - Main orchestrator
  media/
    __init__.py
    media_downloader.py (~200 lines) - download_message_media(), _download_photo(), _download_video(), _download_document(), _download_audio()
    media_manager.py (~80 lines) - get_media_for_message(), delete_media_files()
    thumbnail_creator.py (~50 lines) - _create_thumbnail(), _create_progress_wrapper()
```

**Responsibilities:**

- `media_service.py`: Main service class, coordinates downloads
- `media_downloader.py`: All download methods for different media types
- `media_manager.py`: Database operations for media files
- `thumbnail_creator.py`: Thumbnail creation and progress wrapper utilities

### 4. Telegram Service (771 lines → ~6 files)

**Current structure:**

- Session management (start, load, disconnect)
- Group fetching operations
- Message fetching operations
- Account status checking
- Temporary client management

**New structure:**

```
services/
  telegram/
    telegram_service.py (~150 lines) - Main orchestrator
    session_manager.py (~200 lines) - Session lifecycle (start_session, start_session_qr, load_session, disconnect, auto_load_session)
    message_fetcher.py (~250 lines) - fetch_messages(), fetch_messages_with_account()
    group_fetcher.py (~150 lines) - fetch_group_info(), fetch_and_validate_group()
    account_status_checker.py (~200 lines) - check_account_status(), get_account_status(), get_all_accounts_with_status()
    client_utils.py (~50 lines) - _create_temporary_client(), create_client()
```

**Responsibilities:**

- `telegram_service.py`: Main service class, coordinates all operations
- `session_manager.py`: All session-related operations (start, load, disconnect, auto-load)
- `message_fetcher.py`: Message fetching with temporary clients, progress callbacks
- `group_fetcher.py`: Group information fetching and validation
- `account_status_checker.py`: Account status checking with retry logic and error handling
- `client_utils.py`: Utility functions for creating temporary clients

## Implementation Steps

1. **Create new directory structures** for each service category
2. **Extract classes/modules** from existing files into new files
3. **Update main service files** to use composition pattern
4. **Update all imports** across the codebase
5. **Test** to ensure functionality is preserved
6. **Verify** file sizes are within limits

## Files to Modify

**New files to create:**

- `services/license/__init__.py`
- `services/license/license_checker.py`
- `services/license/license_sync.py`
- `services/license/limit_enforcer.py`
- `services/update/__init__.py`
- `services/update/update_checker.py`
- `services/update/update_downloader.py`
- `services/update/update_installer.py`
- `services/media/__init__.py`
- `services/media/media_downloader.py`
- `services/media/media_manager.py`
- `services/media/thumbnail_creator.py`
- `services/telegram/session_manager.py`
- `services/telegram/message_fetcher.py`
- `services/telegram/group_fetcher.py`
- `services/telegram/account_status_checker.py`
- `services/telegram/client_utils.py`

**Files to refactor:**

- `services/license_service.py` (477 → ~150 lines)
- `services/update_service.py` (390 → ~150 lines)
- `services/media_service.py` (384 → ~100 lines)
- `services/telegram/telegram_service.py` (771 → ~150 lines)

**Files that may need import updates:**

- All files importing from these services (to be discovered during implementation)
- `services/telegram/account_status_service.py` (uses `telegram_service.check_account_status()`)