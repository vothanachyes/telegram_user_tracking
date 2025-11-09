<!-- 04083930-fd46-4bb2-9ed3-82f1297893ed 5ad2b0f8-641c-4dcd-91f5-0c81a692f1e3 -->
# Encrypt user_license_cache and Telegram API Credentials at Data Level

## Overview

Implement field-level encryption for sensitive data in two tables:

1. `user_license_cache` table - encrypt all license-related fields
2. `app_settings` table - encrypt `telegram_api_id` and `telegram_api_hash`

All sensitive fields will be encrypted before storage and decrypted when retrieved, using the existing `CredentialStorage` encryption service. No migration needed - clean start with new database.

## Current State

- `user_license_cache` table stores license data in plain text
- `app_settings` table stores `telegram_api_id` and `telegram_api_hash` in plain text
- `user_email` is used as a lookup key (WHERE user_email = ?)
- Existing `CredentialStorage` class provides Fernet-based encryption (used for passwords)

## Implementation Strategy

### user_license_cache - Fields to Encrypt

- `license_tier` (TEXT) - Encrypt as string
- `expiration_date` (TIMESTAMP) - Encrypt as ISO format string
- `max_devices` (INTEGER) - Encrypt as string representation
- `max_groups` (INTEGER) - Encrypt as string representation
- `max_accounts` (INTEGER) - Encrypt as string representation
- `max_account_actions` (INTEGER) - Encrypt as string representation
- `is_active` (BOOLEAN) - Encrypt as string ("True"/"False")
- `last_synced` (TIMESTAMP) - Encrypt as ISO format string

### user_license_cache - Fields to Keep Unencrypted

- `user_email` - Used as lookup key, keep unencrypted for query performance
- `id`, `created_at`, `updated_at` - Metadata fields

### app_settings - Fields to Encrypt

- `telegram_api_id` (TEXT) - Encrypt as string
- `telegram_api_hash` (TEXT) - Encrypt as string

### app_settings - Fields to Keep Unencrypted

- All other settings fields (theme, language, etc.)
- `id`, `created_at`, `updated_at` - Metadata fields

## Implementation Steps

### 1. Update LicenseManager

**File**: `database/managers/license_manager.py`

**Changes**:

- Import `credential_storage` from `utils.credential_storage`
- Modify `save_license_cache()`:
  - Encrypt all sensitive fields before inserting
  - Convert datetime objects to ISO strings before encryption
  - Convert integers/booleans to strings before encryption
  - Handle None values (store as None, don't encrypt)
- Modify `get_license_cache()`:
  - Decrypt all encrypted fields after retrieval
  - Convert decrypted strings back to appropriate types
  - Handle decryption errors gracefully (log error, return None)

### 2. Update SettingsManager

**File**: `database/managers/settings_manager.py`

**Changes**:

- Import `credential_storage` from `utils.credential_storage`
- Modify `get_settings()`:
  - Decrypt `telegram_api_id` and `telegram_api_hash` after retrieval
  - Handle decryption errors gracefully (log error, return None for that field)
- Modify `update_settings()`:
  - Encrypt `telegram_api_id` and `telegram_api_hash` before updating
  - Handle None values (store as None, don't encrypt)

### 3. Error Handling

- Wrap encryption/decryption in try-except blocks
- Log errors but don't crash the application
- If decryption fails, log error and return None for that field
- If encryption fails, log error and return False from save operation

### 4. Update Tests

**Files**:

- `tests/unit/test_license_service.py` - Add encryption tests for license cache
- `tests/integration/test_licensing.py` - Add integration tests
- Create/update tests for settings encryption

## Technical Details

### Encryption Pattern

```python
# Encrypting
encrypted_value = credential_storage.encrypt(str(value)) if value is not None else None

# Decrypting
try:
    if encrypted_value:
        decrypted_value = credential_storage.decrypt(encrypted_value)
        # Convert back to original type if needed
    else:
        decrypted_value = None
except Exception as e:
    logger.error(f"Decryption failed: {e}")
    decrypted_value = None
```

### Type Conversions for License Cache

- `datetime` → ISO string → encrypt → store
- `int` → string → encrypt → store
- `bool` → "True"/"False" string → encrypt → store
- `None` → None (don't encrypt, store as NULL)

### Type Conversions for Settings

- `telegram_api_id` (str) → encrypt → store
- `telegram_api_hash` (str) → encrypt → store
- `None` → None (don't encrypt, store as NULL)

## Files to Modify

1. `database/managers/license_manager.py` - Add encryption/decryption logic for license cache
2. `database/managers/settings_manager.py` - Add encryption/decryption logic for API credentials
3. `tests/unit/test_license_service.py` - Add encryption tests
4. `tests/integration/test_licensing.py` - Add integration tests
5. Create/update tests for settings encryption

## Files to Review (No Changes)

- `utils/credential_storage.py` - Already provides encryption (reuse)
- `database/models/auth.py` - Model remains the same (encryption is transparent)
- `database/models/app_settings.py` - Model remains the same (encryption is transparent)
- `services/license/license_sync.py` - No changes needed (uses LicenseManager)
- `services/license/license_checker.py` - No changes needed (uses LicenseManager)
- `config/settings.py` - No changes needed (uses SettingsManager)

## Security Considerations

- Uses same encryption as login credentials (device-specific key)
- All sensitive license data encrypted at rest
- Telegram API credentials encrypted at rest
- `user_email` remains unencrypted for query performance
- Encryption key is device-specific (cannot decrypt on different device)
- No migration needed - clean start with new database

## Testing Checklist

- [ ] New license cache entries are encrypted
- [ ] Encrypted license cache entries are decrypted correctly
- [ ] Error handling for corrupted encrypted license data
- [ ] All license operations work correctly (save, get, delete)
- [ ] License sync still works correctly
- [ ] License checker still works correctly
- [ ] Telegram API credentials are encrypted on save
- [ ] Telegram API credentials are decrypted on read
- [ ] Error handling for corrupted encrypted API credentials
- [ ] All settings operations work correctly
- [ ] Telegram authentication still works with encrypted credentials

### To-dos

- [x] Update LicenseManager.save_license_cache() to encrypt all sensitive fields before database insertion
- [x] Update LicenseManager.get_license_cache() to decrypt all encrypted fields after database retrieval
- [x] Update SettingsManager.update_settings() to encrypt telegram_api_id and telegram_api_hash before database update
- [x] Update SettingsManager.get_settings() to decrypt telegram_api_id and telegram_api_hash after database retrieval
- [x] Add comprehensive error handling for encryption/decryption failures in both managers
- [x] Add unit and integration tests for encryption and decryption of both license cache and API credentials