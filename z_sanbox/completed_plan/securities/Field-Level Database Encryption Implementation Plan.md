<!-- 0208a117-c5b1-4e78-9194-12d2fc52a515 f7fa66aa-4765-49a2-a294-eb9a3fda6d33 -->
# Field-Level Database Encryption Implementation Plan

## Overview

Implement transparent field-level encryption for sensitive database fields to protect user data if the database file is copied. Encryption/decryption will be handled at the database manager layer, keeping the application code unchanged.

## Sensitive Fields to Encrypt

### High Priority (PII & Credentials)

- **telegram_credentials**: `phone_number`, `session_string`
- **telegram_users**: `phone`, `username`, `first_name`, `last_name`, `full_name`, `bio`
- **messages**: `content`, `caption`, `message_link`
- **reactions**: `message_link`
- **group_fetch_history**: `account_phone_number`, `account_full_name`, `account_username`
- **account_activity_log**: `phone_number`

### Medium Priority (IDs - if requested)

- **messages**: `user_id`, `group_id` (integers)
- **reactions**: `user_id`, `group_id`, `message_id` (integers)
- **telegram_users**: `user_id` (integer)
- **telegram_groups**: `group_id` (integer), `group_username`

## Implementation Steps

### 1. Create Field-Level Encryption Service

**File**: `services/database/field_encryption_service.py` (~200 lines)

- Create `FieldEncryptionService` class using Fernet (AES-128) or AES-256
- Methods: `encrypt_field(value: str) -> str`, `decrypt_field(encrypted: str) -> str`
- Handle None/empty values gracefully
- Use encryption key from app settings (same as file-level encryption or separate)
- Support key rotation/rekeying

### 2. Update Database Managers

Modify all managers to encrypt on write and decrypt on read:

**Files to update**:

- `database/managers/telegram_credential_manager.py` - encrypt `phone_number`, `session_string`
- `database/managers/user_manager.py` - encrypt `phone`, `username`, `first_name`, `last_name`, `full_name`, `bio`
- `database/managers/message_manager.py` - encrypt `content`, `caption`, `message_link`, optionally `user_id`, `group_id`
- `database/managers/reaction_manager.py` - encrypt `message_link`, optionally IDs
- `database/managers/fetch_history_manager.py` - encrypt `account_phone_number`, `account_full_name`, `account_username`
- `database/managers/account_activity_manager.py` - encrypt `phone_number`
- `database/managers/group_manager.py` - optionally encrypt `group_username`, `group_id`

**Pattern for each manager**:

- Inject `FieldEncryptionService` in `__init__`
- Encrypt fields before INSERT/UPDATE
- Decrypt fields after SELECT
- Handle None values and empty strings

### 3. Database Migration for Existing Data

**File**: `database/migrations/migrate_to_field_encryption.py` (~150 lines)

- Create migration script to encrypt all existing data
- Run on app startup if encryption is enabled
- Track migration status in `app_settings` table
- Provide rollback capability

### 4. Update Schema (if needed)

**File**: `database/models/schema.py`

- Add `encryption_enabled` flag to `app_settings` table
- Migration to add column if not exists

### 5. Integration Points

- Update `BaseDatabaseManager` to initialize `FieldEncryptionService`
- Ensure encryption key is available from settings
- Handle encryption errors gracefully (log and continue with unencrypted fallback if needed)

### 6. Testing Considerations

- Test encryption/decryption round-trip
- Test with None/empty values
- Test migration of existing data
- Test query performance impact
- Test error handling (corrupted encrypted data)

## Technical Decisions Needed

1. **Integer ID Encryption**: Should `user_id`, `group_id`, `message_id` be encrypted? (Affects query performance)
2. **Encryption Key Source**: Use existing file-level encryption key or generate separate key?
3. **Migration Strategy**: Auto-migrate on startup or manual migration command?
4. **Performance**: Cache decrypted values or decrypt on every read?

## Files to Create/Modify

**New Files**:

- `services/database/field_encryption_service.py` - Core encryption service
- `database/migrations/migrate_to_field_encryption.py` - Data migration script

**Modified Files**:

- `database/managers/base.py` - Add encryption service initialization
- `database/managers/telegram_credential_manager.py` - Add encryption
- `database/managers/user_manager.py` - Add encryption
- `database/managers/message_manager.py` - Add encryption
- `database/managers/reaction_manager.py` - Add encryption
- `database/managers/fetch_history_manager.py` - Add encryption
- `database/managers/account_activity_manager.py` - Add encryption
- `database/managers/group_manager.py` - Add encryption (optional)
- `database/models/schema.py` - Add encryption_enabled flag
- `config/settings.py` - Add field encryption key management

## Estimated Impact

- **Lines of code**: ~800-1000 lines (new + modifications)
- **Performance**: Minimal impact (encryption is fast, but adds overhead to every read/write)
- **Breaking changes**: None (transparent to application code)
- **Migration**: Required for existing databases

### To-dos

- [x] Create FieldEncryptionService class in services/database/field_encryption_service.py with encrypt/decrypt methods, key management, and error handling
- [x] Update BaseDatabaseManager to initialize and provide FieldEncryptionService to all managers
- [ ] Add encryption to TelegramCredentialManager for phone_number and session_string fields
- [ ] Add encryption to UserManager for phone, username, first_name, last_name, full_name, bio fields
- [ ] Add encryption to MessageManager for content, caption, message_link fields (and optionally user_id, group_id)
- [ ] Add encryption to ReactionManager for message_link field (and optionally IDs)
- [ ] Add encryption to FetchHistoryManager for account_phone_number, account_full_name, account_username fields
- [ ] Add encryption to AccountActivityManager for phone_number field
- [x] Add encryption_enabled flag to app_settings table schema and update SettingsManager
- [ ] Create migration script to encrypt all existing data in database, with rollback capability
- [ ] Update config/settings.py to manage field encryption key (generate, store, retrieve)
- [ ] Test encryption/decryption works correctly for all field types (strings, None, empty strings)