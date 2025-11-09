<!-- 627b96f5-0f56-434b-b11f-02b790aa8b3f adec1e87-f127-4e66-bde4-2505e5960381 -->
# Encrypt Telegram Session Files Implementation Plan

## Overview

Implement transparent encryption for Telegram session files using a custom Telethon session class. New sessions will be encrypted by default with `.session.enc` extension, while existing unencrypted sessions remain unchanged.

## Architecture Decision

**Custom Encrypted SQLiteSession Wrapper**: Create a custom session class that wraps Telethon's SQLiteSession and transparently encrypts/decrypts the session file. This approach:

- Maintains compatibility with Telethon's session interface
- Handles encryption transparently without modifying Telethon internals
- Uses `.session.enc` extension to distinguish encrypted files
- Leverages existing `FieldEncryptionService` for encryption

## Implementation Steps

### 1. Create Encrypted Session Class

**File**: `services/telegram/sessions/encrypted_session.py` (~250 lines)

- Create `EncryptedSQLiteSession` class that wraps `telethon.sessions.SQLiteSession`
- Override `save()` method to:
  - Call parent `save()` to let Telethon save normally
  - Encrypt the session file using `FieldEncryptionService`
  - Rename to `.session.enc` extension
  - Delete original `.session` file if it exists
- Override `load()` method to:
  - Check if encrypted file (`.session.enc`) exists
  - Decrypt to temporary file
  - Let parent `load()` read from temporary file
  - Clean up temporary file after load
- Handle both `.session` and `.session.enc` files for backward compatibility
- Use encryption key from app settings (same as field encryption)

### 2. Create Session Encryption Service

**File**: `services/telegram/sessions/session_encryption_service.py` (~200 lines)

- Create `SessionEncryptionService` class
- Methods:
  - `encrypt_session_file(session_path: Path) -> bool`: Encrypt session file
  - `decrypt_session_file(encrypted_path: Path) -> Optional[Path]`: Decrypt to temp file
  - `is_encrypted(session_path: Path) -> bool`: Check if file is encrypted
  - `migrate_session_to_encrypted(session_path: Path) -> bool`: Migrate existing session
- Use `FieldEncryptionService` for encryption (reuse existing infrastructure)
- Handle file I/O errors gracefully
- Support both `.session` and `.session.enc` extensions

### 3. Update ClientManager

**File**: `services/telegram/client_manager.py`

- Modify `create_client()` to use `EncryptedSQLiteSession` instead of default session
- Update session file path handling to support `.session.enc` extension
- Ensure encrypted sessions are used for all new sessions
- Update `load_session()` to handle encrypted session files
- Update `start_session_qr()` to use encrypted sessions

### 4. Update Session Manager

**File**: `services/telegram/session_manager.py`

- Ensure session paths stored in database use `.session.enc` extension for encrypted sessions
- Handle backward compatibility with unencrypted sessions

### 5. Add Settings Support

**File**: `database/models/app_settings.py`

- Add `session_encryption_enabled` boolean field (default: True)
- Update schema migration if needed

**File**: `config/settings.py`

- Add property to check if session encryption is enabled
- Use same encryption key as field encryption (from `FieldEncryptionService`)

### 6. Handle Session File Operations

**File**: `services/telegram/client_manager.py`

- Update `_cleanup_temp_sessions()` to handle `.session.enc` files
- Update session rename logic in `start_session_qr()` to use `.session.enc` extension
- Ensure journal files (`.session-journal`) are also handled if needed

### 7. Error Handling

- Handle decryption failures gracefully (log error, fallback to unencrypted if exists)
- Handle encryption failures (log error, continue with unencrypted)
- Validate encryption key availability before encrypting
- Provide clear error messages for encryption-related failures

### 8. Testing Considerations

- Test creating new encrypted session
- Test loading encrypted session
- Test backward compatibility with unencrypted sessions
- Test encryption/decryption round-trip
- Test error handling (corrupted encrypted file, missing key, etc.)

## Technical Details

### Encryption Flow

1. **New Session Creation**:

   - Telethon creates session file (`.session`)
   - `EncryptedSQLiteSession.save()` is called
   - Session file is encrypted using `FieldEncryptionService`
   - File is renamed to `.session.enc`
   - Original `.session` file is deleted

2. **Loading Encrypted Session**:

   - `EncryptedSQLiteSession.load()` is called
   - Check if `.session.enc` exists
   - Decrypt to temporary file
   - Parent `load()` reads from temporary file
   - Temporary file is cleaned up

3. **Backward Compatibility**:

   - If `.session.enc` doesn't exist, check for `.session`
   - Load unencrypted session normally
   - New saves will encrypt it

### File Structure

```
services/telegram/sessions/
  ├── __init__.py
  ├── encrypted_session.py       # Custom EncryptedSQLiteSession class
  └── session_encryption_service.py  # Encryption/decryption utilities
```

### Integration Points

- `ClientManager.create_client()`: Use `EncryptedSQLiteSession`
- `FieldEncryptionService`: Reuse for session file encryption
- `Settings`: Check encryption enabled flag and get encryption key
- `TelegramCredentialManager`: Store `.session.enc` path in database

## Files to Create/Modify

**New Files**:

- `services/telegram/sessions/__init__.py`
- `services/telegram/sessions/encrypted_session.py`
- `services/telegram/sessions/session_encryption_service.py`

**Modified Files**:

- `services/telegram/client_manager.py` - Use encrypted session class
- `services/telegram/session_manager.py` - Handle encrypted session paths
- `database/models/app_settings.py` - Add session_encryption_enabled field
- `config/settings.py` - Add session encryption settings
- `database/models/schema.py` - Migration for new field (if needed)

## Security Considerations

- Use same encryption key as field encryption (from app settings)
- Encrypted files use `.session.enc` extension for identification
- Original unencrypted files are deleted after encryption
- Encryption key must be available before encrypting/decrypting
- Handle key unavailability gracefully (fallback to unencrypted)

## Migration Strategy

- Existing unencrypted sessions (`.session`) remain unchanged
- New sessions automatically use encryption (`.session.enc`)
- When loading, check for encrypted first, then fallback to unencrypted
- Optional: Future migration tool to encrypt existing sessions (not in scope)

## Estimated Impact

- **Lines of code**: ~500-600 lines (new + modifications)
- **Performance**: Minimal overhead (encryption only on save/load, not during use)
- **Breaking changes**: None (backward compatible with unencrypted sessions)
- **Dependencies**: No new dependencies (uses existing cryptography)

### To-dos

- [ ] Create EncryptedSQLiteSession class in services/telegram/sessions/encrypted_session.py that wraps Telethon SQLiteSession with transparent encryption/decryption
- [ ] Create SessionEncryptionService in services/telegram/sessions/session_encryption_service.py for encrypting/decrypting session files
- [ ] Update ClientManager to use EncryptedSQLiteSession instead of default session for all new sessions
- [ ] Update SessionManager to handle encrypted session paths (.session.enc extension) in database storage
- [ ] Add session_encryption_enabled field to app_settings model and update Settings class to support session encryption
- [ ] Update session file cleanup and rename operations in ClientManager to handle .session.enc files
- [ ] Add comprehensive error handling for encryption/decryption failures with graceful fallbacks