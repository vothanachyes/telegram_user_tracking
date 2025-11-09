<!-- c5c898b0-5daa-4268-a374-08203a93f7b2 4ec9ff95-26f4-4767-ade7-8bd1033eedde -->
# Pyrogram to Telethon Migration Plan

## Overview

Complete migration from Pyrogram to Telethon library while maintaining all existing functionality. All Pyrogram code will be moved to `services/telegram/pyrogram/` folder and marked as deprecated.

## Key Differences to Address

### Client Initialization

- **Pyrogram**: `Client(name, api_id, api_hash, phone_number, workdir)`
- **Telethon**: `TelegramClient(session_name, api_id, api_hash)`
- Session files: Pyrogram uses `.session` files, Telethon also uses `.session` but different format

### Connection & Authentication

- **Pyrogram**: `client.connect()`, `client.get_me()`, `client.send_code()`, `client.sign_in()`
- **Telethon**: `client.connect()`, `client.get_me()`, `client.send_code_request()`, `client.sign_in()`
- QR Login: Telethon has better QR code support via `client.qr_login()`

### Message Fetching

- **Pyrogram**: `client.get_chat_history(group_id)` (async iterator)
- **Telethon**: `client.iter_messages(entity)` (async iterator)

### Group Operations

- **Pyrogram**: `client.get_chat(identifier)` (handles both ID and invite link)
- **Telethon**: `client.get_entity(identifier)` (handles ID, username, invite link)

### Error Handling

- **Pyrogram**: `pyrogram.errors.FloodWait`, `Unauthorized`, etc.
- **Telethon**: `telethon.errors.FloodWaitError`, `UnauthorizedError`, etc.

### Media Download

- **Pyrogram**: `client.download_media(message.photo, file_name=path)`
- **Telethon**: `client.download_media(message, file=path)` or `await client.download_file()`

### Reactions

- **Pyrogram**: `client.get_reactions(chat_id, message_id)`
- **Telethon**: Different API structure, need to check message.reactions attribute

## Implementation Steps

### Phase 1: Setup & Dependencies

1. **Update requirements.txt**

   - Remove: `pyrogram>=2.0.106`, `tgcrypto>=1.2.5`
   - Add: `telethon>=1.34.0`
   - Keep: All other dependencies unchanged

2. **Create deprecated folder structure**

   - Create `services/telegram/pyrogram/` directory
   - Add `__init__.py` with deprecation notice

### Phase 2: Core Client Management Migration

3. **Migrate `services/telegram/client_manager.py`**

   - Replace `from pyrogram import Client` with `from telethon import TelegramClient`
   - Update `create_client()` to use Telethon client initialization
   - Update `start_session()` for phone/OTP flow (Telethon API)
   - Add `start_session_qr()` using Telethon's `qr_login()` method
   - Update `load_session()` to use Telethon session format
   - Update error handling (Telethon exceptions)
   - Update `is_authorized()` check
   - **Target**: ~250 lines (maintain structure)

4. **Migrate `services/telegram/client_utils.py`**

   - Update `create_temporary_client()` to use Telethon
   - Update client connection/disconnection logic
   - **Target**: ~70 lines

5. **Migrate `services/telegram/session_manager.py`**

   - Update session file path handling (Telethon format)
   - Update credential saving logic
   - **Target**: ~120 lines

### Phase 3: Message & Group Operations

6. **Migrate `services/telegram/message_fetcher.py`**

   - Replace `get_chat_history()` with `iter_messages()`
   - Update message iteration logic
   - Update FloodWait error handling
   - **Target**: ~420 lines

7. **Migrate `services/telegram/group_fetcher.py`**

   - Update `get_chat()` to `get_entity()`
   - Update error handling for Telethon exceptions
   - **Target**: ~180 lines

8. **Migrate `services/telegram/group_manager.py`**

   - Update `get_chat()` to `get_entity()`
   - Update group ID conversion logic (Telethon handles IDs differently)
   - Update ChatType checks (Telethon uses different types)
   - Update dialog iteration for caching
   - **Target**: ~230 lines

9. **Migrate `services/telegram/group_photo_downloader.py`**

   - Update photo download using Telethon API
   - Update `chat.photo` access pattern
   - **Target**: ~75 lines

### Phase 4: Data Processing

10. **Migrate `services/telegram/message_processor.py`**

    - Update message attribute access (Telethon message structure)
    - Update media type detection (different attribute names)
    - Update sticker/photo/video/document detection
    - **Target**: ~160 lines

11. **Migrate `services/telegram/user_processor.py`**

    - Update user attribute access (Telethon user structure)
    - Update phone number access pattern
    - **Target**: ~60 lines

12. **Migrate `services/telegram/reaction_processor.py`**

    - Update reaction API (Telethon has different structure)
    - Update `get_reactions()` equivalent
    - Update reaction emoji extraction
    - **Target**: ~190 lines

### Phase 5: Media & Account Services

13. **Migrate `services/media/media_downloader.py`**

    - Update `download_media()` calls to Telethon API
    - Update progress callback handling
    - Update file download methods
    - **Target**: ~310 lines

14. **Migrate `services/telegram/account_status_checker.py`**

    - Update error types (Telethon exceptions)
    - Update session validation logic
    - Update database lock handling (Telethon uses different session storage)
    - **Target**: ~270 lines

### Phase 6: Service Orchestration

15. **Migrate `services/telegram/telegram_service.py`**

    - Update imports (remove Pyrogram, add Telethon)
    - Update type hints (`Client` → `TelegramClient`)
    - Update property types
    - **Target**: ~255 lines

### Phase 7: Move Deprecated Code

16. **Move all Pyrogram files to deprecated folder**

    - Move all files from `services/telegram/*.py` (except new Telethon versions) to `services/telegram/pyrogram/`
    - Add deprecation notice at top of each file
    - Update `__init__.py` in pyrogram folder

17. **Update imports across codebase**

    - Search for any remaining Pyrogram imports
    - Update UI components that reference Telegram client
    - Update any test files

### Phase 8: Testing & Validation

18. **Update session file handling**

    - Note: Existing Pyrogram `.session` files won't work with Telethon
    - Users will need to re-authenticate (expected behavior)
    - Update session file naming if needed

19. **Test all functionality**

    - Phone/OTP login
    - QR code login (new with Telethon)
    - Message fetching
    - Group fetching
    - Media downloading
    - Reaction tracking
    - Account status checking

## File Structure After Migration

```
services/telegram/
├── __init__.py
├── client_manager.py          # NEW: Telethon implementation
├── client_utils.py            # NEW: Telethon implementation
├── session_manager.py          # NEW: Telethon implementation
├── message_fetcher.py         # NEW: Telethon implementation
├── group_fetcher.py            # NEW: Telethon implementation
├── group_manager.py           # NEW: Telethon implementation
├── message_processor.py       # NEW: Telethon implementation
├── user_processor.py           # NEW: Telethon implementation
├── reaction_processor.py      # NEW: Telethon implementation
├── account_status_checker.py   # NEW: Telethon implementation
├── group_photo_downloader.py   # NEW: Telethon implementation
├── telegram_service.py         # NEW: Telethon implementation
└── pyrogram/                   # NEW: Deprecated folder
    ├── __init__.py
    ├── client_manager.py       # OLD: Deprecated
    ├── client_utils.py         # OLD: Deprecated
    ├── session_manager.py      # OLD: Deprecated
    └── ... (all other old files)
```

## Critical Migration Points

1. **Session Files**: Pyrogram and Telethon use incompatible session formats. Users must re-authenticate.

2. **Group ID Handling**: Telethon handles group IDs differently. Need to ensure proper conversion.

3. **Message Iteration**: `iter_messages()` has different parameters than `get_chat_history()`.

4. **Error Types**: All exception handling must be updated to Telethon error types.

5. **QR Code Login**: Telethon's QR login is more reliable - can enable this feature.

6. **Media Download**: Telethon's download API is slightly different - need to update all download calls.

## Notes

- All functionality must remain the same from user perspective
- No breaking changes to public APIs
- Maintain backward compatibility with database schema
- Session files will need to be regenerated (expected)
- Telethon has better QR code support - can enable QR login feature

### To-dos

- [ ] Update requirements.txt: remove pyrogram/tgcrypto, add telethon
- [ ] Create services/telegram/pyrogram/ folder structure with __init__.py and deprecation notices
- [ ] Migrate client_manager.py: replace Pyrogram Client with Telethon TelegramClient, update all methods
- [ ] Migrate client_utils.py: update temporary client creation for Telethon
- [ ] Migrate session_manager.py: update session handling for Telethon format
- [ ] Migrate message_fetcher.py: replace get_chat_history with iter_messages, update error handling
- [ ] Migrate group_fetcher.py: replace get_chat with get_entity, update error handling
- [ ] Migrate group_manager.py: update group operations, ID conversion, and ChatType handling
- [ ] Migrate message_processor.py: update message attribute access for Telethon message structure
- [ ] Migrate user_processor.py: update user attribute access for Telethon user structure
- [ ] Migrate reaction_processor.py: update reaction API and emoji extraction for Telethon
- [ ] Migrate media_downloader.py: update download_media calls and progress handling for Telethon
- [ ] Migrate account_status_checker.py: update error types and session validation for Telethon
- [ ] Migrate group_photo_downloader.py: update photo download API for Telethon
- [ ] Migrate telegram_service.py: update imports, type hints, and client references
- [ ] Move all old Pyrogram files to services/telegram/pyrogram/ folder with deprecation notices
- [ ] Search and update any remaining Pyrogram imports across codebase (UI, tests, etc.)
- [ ] Test all functionality: login, message fetching, group operations, media download, reactions