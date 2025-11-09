<!-- 21ca1bc2-e041-4fc5-acd1-97d3d83b6d36 e3643e30-6bbb-4f80-abed-d0fa5c59101d -->
# Database Security Settings Tab Implementation Plan

## Overview

Add a new "Security" tab in the settings page that allows users to:

- Change database file path (with data migration option)
- View and manage database encryption settings
- Read privacy disclaimers about data storage
- Access protected by Windows authentication (password/fingerprint)

## Architecture Decisions Needed

### 1. Database Encryption Method

**Options:**

- **SQLCipher**: Industry-standard encrypted SQLite extension
  - Pros: Transparent encryption, good performance, widely used
  - Cons: Requires compiled extension, more complex setup
- **File-level encryption**: Encrypt entire .db file using AES-256
  - Pros: Simpler implementation, no external dependencies
  - Cons: Must decrypt entire file for any operation, performance impact

**Recommendation**: SQLCipher for production, file-level encryption for MVP

### 2. Windows Authentication

**Options:**

- Windows Hello (fingerprint/face) via `pywin32` + Windows Security APIs
- Windows password prompt via credential dialog
- Both (try Hello first, fallback to password)

**Implementation**: Use `pywin32` for Windows-specific authentication APIs

### 3. Database Path Migration

**Options:**

- Manual migration (user copies files)
- Automatic migration on path change
- Path change only allowed when DB is empty

**Recommendation**: Automatic migration with confirmation dialog

### 4. Encryption Key Storage

**Options:**

- Plain text in settings (protected by Windows auth)
- Encrypted using Windows DPAPI
- Derived from user master password

**Recommendation**: Encrypted using Windows DPAPI for security

## Implementation Structure

### Files to Create/Modify

1. **New Tab Component**

   - `ui/pages/settings/tabs/security_tab/page.py` - Main tab component
   - `ui/pages/settings/tabs/security_tab/components.py` - UI components
   - `ui/pages/settings/tabs/security_tab/view_model.py` - Data logic
   - `ui/pages/settings/tabs/security_tab/handlers.py` - Event handlers

2. **Database Encryption Service**

   - `services/database/encryption_service.py` - Encryption/decryption logic
   - `services/database/db_migration_service.py` - Database path migration

3. **Windows Authentication Utility**

   - `utils/windows_auth.py` - Windows Hello/password authentication

4. **Database Models Update**

   - `database/models/app_settings.py` - Add `db_path`, `encryption_enabled`, `encryption_key_hash` fields
   - `database/models/schema.py` - Add migration for new fields

5. **Settings Page Update**

   - `ui/pages/settings/page.py` - Add Security tab
   - `ui/pages/settings/tabs/__init__.py` - Export SecurityTab

6. **i18n Updates**

   - `locales/en.json` - English translations
   - `locales/km.json` - Khmer translations

7. **Dependencies**

   - `requirements.txt` - Add `pywin32` (Windows), `pysqlcipher3` or `cryptography` for encryption

## Key Features

### Security Tab UI Components

- Database path selector (file picker for directory)
- Current path display
- Encryption toggle switch
- Encryption key display (masked with reveal button)
- Change encryption key button
- Privacy disclaimer card
- Migration status indicator

### Windows Authentication Flow

1. User clicks Security tab
2. Check if Windows authentication required
3. Show authentication dialog (fingerprint/password)
4. On success, unlock tab content
5. Cache authentication for session (optional timeout)

### Database Path Change Flow

1. User selects new path
2. Validate path (writable, sufficient space)
3. Show migration confirmation dialog
4. Copy database file and related files (WAL, SHM)
5. Update settings with new path
6. Restart database connection with new path
7. Verify migration success

### Encryption Implementation Flow

1. Generate default encryption key (if not exists)
2. Encrypt key using Windows DPAPI
3. Store encrypted key hash in settings
4. Apply encryption to database (SQLCipher or file-level)
5. On key change: re-encrypt database with new key

## Privacy Disclaimer Content

**English:**

"Your Privacy Matters: We only store your login credentials and license information on our secure servers. All your Telegram data (messages, users, groups, media) is stored locally on your device in the database file you control. You can change the database location and encryption settings at any time. We cannot access your local data."

**Khmer:**

[Translation needed]

## Technical Considerations

### SQLCipher Integration

- Use `pysqlcipher3` package (Python bindings for SQLCipher)
- Set encryption key via `PRAGMA key = 'key'` on connection
- Change key via `PRAGMA rekey = 'new_key'`

### Windows Authentication

- Use `win32api` and `win32security` from `pywin32`
- For Windows Hello: Use `Windows.Security.Credentials.UI` API
- For password: Use credential prompt dialog

### Database Migration

- Copy: `app.db`, `app.db-wal`, `app.db-shm`
- Verify file integrity after copy
- Handle active connections (close before migration)

### Error Handling

- Handle encryption failures gracefully
- Provide rollback mechanism for failed migrations
- Show clear error messages for authentication failures

## Testing Requirements

1. Test Windows authentication on Windows 10/11
2. Test database path change with existing data
3. Test encryption enable/disable
4. Test encryption key change
5. Test migration with large databases
6. Test error scenarios (insufficient permissions, disk full, etc.)

## Security Considerations

1. Never log encryption keys
2. Clear encryption keys from memory after use
3. Use secure random key generation
4. Validate all user inputs
5. Handle authentication failures securely
6. Encrypt encryption key using DPAPI

## Dependencies to Add

```txt
pywin32>=306; sys_platform == "win32"
pysqlcipher3>=0.5.0; sys_platform == "win32"  # For SQLCipher
# OR
cryptography>=41.0.0  # For file-level encryption
```

## Migration Path

1. Add new fields to `app_settings` table (migration script)
2. Default encryption: disabled
3. Default path: current `DATABASE_PATH`
4. On first access: generate default encryption key
5. Allow users to enable encryption and change settings

### To-dos

- [ ] Add database path and encryption fields to AppSettings model and schema
- [ ] Create Windows authentication utility (utils/windows_auth.py)
- [ ] Create database encryption service (services/database/encryption_service.py)
- [ ] Create database migration service (services/database/db_migration_service.py)
- [ ] Create Security tab components (page.py, components.py, view_model.py, handlers.py)
- [ ] Add Security tab to settings page and update tab exports
- [ ] Add i18n translations for Security tab (en.json, km.json)
- [ ] Update requirements.txt with Windows authentication and encryption dependencies
- [ ] Update DatabaseManager to support encrypted connections and path changes