Propmt: 
Yes, you idea is legend. 
default not encrypted 
- Use have to enable encrytion in Setting tab
- one user switch to enable => I want to have dialog show total existing data encrypted and not yet encrypt. In this dialog has information about how encrypt, what to be encrypted, ... and has 2 button Cancel/Start (Also warning this action cannot be undo, after encrypt => data encrypted in database)
- one user click start => run migration encrypt to not yet encrypted data.
- should show progress
- no cancel button to cancel this process

Note: Please aware export fuction may take longer time than before because data encrypted need to decrypted for write to eexcel/pdf  (If user has tousand of data to export)

<!-- 8e5f4e24-559d-469a-b32c-625c2e75f7d5 23ecf45d-8855-421a-83f6-c2fa3cdf8576 -->
# Encryption Enablement with Migration Dialog

## Overview

When a user enables encryption in Settings → Security tab, show a confirmation dialog with data statistics, then run migration with progress tracking. Export functions already handle decryption automatically via MessageManager.

## Implementation Steps

### 1. Create Encryption Statistics Service

**File**: `services/database/encryption_stats_service.py` (~150 lines)

Create a service to count encrypted vs unencrypted records:

- `count_encrypted_messages()` - Count messages with `ENC:` prefix in content/caption/message_link
- `count_unencrypted_messages()` - Count messages without `ENC:` prefix
- `count_encrypted_users()` - Count users with encrypted fields
- `count_unencrypted_users()` - Count users without encrypted fields
- `count_encrypted_credentials()` - Count encrypted credentials
- `count_unencrypted_credentials()` - Count unencrypted credentials
- `get_encryption_statistics()` - Return dict with all counts

Use SQL queries with `LIKE 'ENC:%'` pattern matching to identify encrypted fields.

### 2. Create Enable Encryption Dialog

**File**: `ui/dialogs/enable_encryption_dialog.py` (~300 lines)

Dialog structure:

- **Information Section**:
  - Title: "Enable Database Encryption"
  - Explanation text about encryption (what it does, how it works)
  - List of what will be encrypted:
    - Messages: content, caption, message_link
    - Users: username, first_name, last_name, full_name, phone, bio
    - Credentials: phone_number, session_string
    - Reactions: message_link
    - Group fetch history: account_phone_number, account_full_name, account_username
    - Account activity log: phone_number

- **Statistics Section**:
  - Show counts from `EncryptionStatsService`:
    - "Already Encrypted: X messages, Y users, Z credentials"
    - "Will Be Encrypted: X messages, Y users, Z credentials"
  - Display in a formatted card with icons

- **Warning Section**:
  - Red warning box: "⚠️ WARNING: This action cannot be undone. Once encrypted, data will be encrypted in the database. Make sure you have a backup."
  - Note about device-specific encryption (data encrypted on this device cannot be decrypted on another device)

- **Buttons**:
  - Cancel button (closes dialog, doesn't enable encryption)
  - Start button (starts migration, disables Cancel button)

### 3. Add Progress Tracking to Migration

**File**: `database/migrations/migrate_to_field_encryption.py`

Modify `migrate()` method to accept progress callback:

- Add `progress_callback: Optional[Callable[[str, int, int], None]] = None` parameter
- Callback signature: `(stage: str, current: int, total: int)`
- Stages: "telegram_credentials", "telegram_users", "messages", "reactions", "group_fetch_history", "account_activity_log"
- Call callback after each record: `progress_callback(stage, current_index, total_count)`
- Update existing `run()` method to pass None for backward compatibility

### 4. Update Security Tab to Handle Encryption Switch

**File**: `ui/pages/settings/tabs/security_tab/page.py`

Add `on_change` handler to `encryption_switch`:

- In `__init__`, add: `self.encryption_switch.on_change = self._on_encryption_switch_changed`
- Create `_on_encryption_switch_changed()` method:
  - If switching from False to True:
    - Check if already authenticated (if not, show error)
    - Load encryption statistics using `EncryptionStatsService`
    - Show `EnableEncryptionDialog` with statistics
    - If user clicks Start in dialog:
      - Enable encryption in settings (call `app_settings.enable_field_encryption()`)
      - Run migration with progress updates
      - Update switch state on success
    - If user clicks Cancel or closes dialog:
      - Revert switch to False
  - If switching from True to False:
    - Show confirmation dialog (existing behavior or new simple confirm)
    - Call `app_settings.disable_field_encryption()`

### 5. Create Migration Progress Dialog

**File**: `ui/dialogs/encryption_migration_progress_dialog.py` (~200 lines)

Progress dialog shown during migration:

- **Progress Bar**: `ft.ProgressBar()` with indeterminate or percentage
- **Stage Text**: Current stage being processed (e.g., "Encrypting messages...")
- **Progress Text**: "Processing X of Y records"
- **Statistics**: Real-time counts of encrypted records
- **No Cancel Button**: Dialog cannot be closed during migration (modal, no close button)
- Update via callback from migration script

### 6. Integrate Progress Dialog with Migration

**File**: `ui/pages/settings/tabs/security_tab/page.py`

In `_on_encryption_switch_changed()`:

- After user clicks Start in confirmation dialog:
  - Show `EncryptionMigrationProgressDialog`
  - Create progress callback that updates dialog:
    ```python
    def on_progress(stage: str, current: int, total: int):
        progress_dialog.update_progress(stage, current, total)
        if page:
            page.update()
    ```

  - Run migration in background thread:
    ```python
    def run_migration():
        success = migration.migrate(progress_callback=on_progress)
        if page:
            page.run(lambda _: self._handle_migration_complete(success))
    ```

  - On completion:
    - Close progress dialog
    - Show success/error message
    - Update encryption switch state
    - Refresh settings

### 7. Verify Export Functions Handle Decryption

**Files**: `services/export/exporters/messages_exporter.py`, `services/export/formatters/data_formatter.py`

Verify that export functions receive decrypted data:

- `MessageManager.get_messages()` already decrypts fields automatically
- Export functions receive `Message` objects with decrypted content
- No changes needed - decryption is transparent to export layer
- Add comment in export code noting that decryption happens automatically

### 8. Add Translation Keys

**File**: `ui/theme/translations.py` (or wherever translations are stored)

Add translation keys:

- `enable_encryption_dialog_title`
- `enable_encryption_dialog_info`
- `encryption_what_will_be_encrypted`
- `encryption_already_encrypted`
- `encryption_will_be_encrypted`
- `encryption_warning_irreversible`
- `encryption_warning_device_specific`
- `encryption_migration_in_progress`
- `encryption_migration_complete`
- `encryption_migration_failed`

## File Structure

```
services/database/
  └── encryption_stats_service.py (NEW)

ui/dialogs/
  ├── enable_encryption_dialog.py (NEW)
  └── encryption_migration_progress_dialog.py (NEW)

database/migrations/
  └── migrate_to_field_encryption.py (MODIFY - add progress callback)

ui/pages/settings/tabs/security_tab/
  └── page.py (MODIFY - add switch handler)
```

## Key Implementation Details

1. **Statistics Counting**: Use SQL `LIKE 'ENC:%'` to identify encrypted fields. Count only non-NULL, non-empty fields.

2. **Progress Updates**: Migration runs in background thread, updates UI via `page.run()` to ensure thread safety.

3. **Error Handling**: If migration fails, show error dialog, revert encryption switch, allow user to retry.

4. **Backup**: Migration script already creates backup (`app.db.pre_encryption_backup`). Mention this in dialog.

5. **Export Performance**: Export functions already receive decrypted data from `MessageManager`, so no changes needed. The decryption overhead is minimal per message.

## Testing Considerations

- Test with empty database
- Test with partially encrypted database (some records encrypted, some not)
- Test with large database (1000+ messages) to verify progress updates
- Test cancellation (user closes confirmation dialog)
- Test error handling (simulate migration failure)
- Verify export still works after encryption is enabled