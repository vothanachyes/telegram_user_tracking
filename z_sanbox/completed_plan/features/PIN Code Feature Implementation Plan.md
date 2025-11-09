<!-- 3358720b-49be-4bdb-9414-d7bcd3afdab8 ff946b2a-6dd1-4671-971c-25a9b6012a8a -->
# PIN Code Feature Implementation Plan

## Overview

Add a 6-digit PIN code feature to enhance app security. Users can optionally set a PIN in settings, which will be required after successful login (including auto-login). PIN is stored encrypted using the existing credential storage system.

## Current State Analysis

### Existing Functionality

- Login page with auto-login support (saved credentials)
- Settings page with General, Authenticate, and Configure tabs
- Credential storage system with encryption (`utils/credential_storage.py`)
- App settings stored in database (`app_settings` table)
- Login success flow in `ui/app.py` (`_on_login_success`)

### What's Missing

- PIN code setting in database schema and AppSettings model
- PIN configuration UI in settings page
- PIN entry dialog component
- PIN validation logic
- PIN check after login/auto-login

## Implementation Details

### 1. Database Schema Update

**File**: `database/models/schema.py`

Add PIN field to `app_settings` table:

- `pin_enabled BOOLEAN NOT NULL DEFAULT 0` - Whether PIN is enabled
- `encrypted_pin TEXT` - Encrypted PIN code (6 digits)

**Migration**: Add ALTER TABLE statement for existing databases.

### 2. Update AppSettings Model

**File**: `database/models/app_settings.py`

Add fields:

```python
pin_enabled: bool = False
encrypted_pin: Optional[str] = None
```

### 3. Update Settings Manager

**File**: `database/managers/settings_manager.py`

- Update `get_settings()` to read PIN fields
- Update `update_settings()` to save PIN fields

### 4. Add PIN Configuration to Settings Page

**File**: `ui/pages/settings_page.py`

Add to General tab:

- Toggle switch: "Enable PIN Code"
- PIN setup section (visible when enabled):
  - "Set PIN" button (opens PIN setup dialog)
  - "Change PIN" button (if PIN already set)
  - "Remove PIN" button (if PIN set)
- PIN setup dialog:
  - Enter 6-digit PIN
  - Confirm 6-digit PIN
  - Validation (must be exactly 6 digits, numeric only)
  - Show error if PINs don't match

### 5. Create PIN Entry Dialog

**File**: `ui/dialogs/pin_dialog.py` (new file)

Create reusable PIN entry dialog:

- 6-digit numeric input (masked)
- Visual feedback (dots/circles for entered digits)
- Error message display
- Submit button
- Cancel button (optional, may be disabled for required PIN)

### 6. Add PIN Validation Service

**File**: `utils/pin_validator.py` (new file)

Utility functions:

- `validate_pin_format(pin: str) -> Tuple[bool, Optional[str]]` - Validate 6-digit format
- `hash_pin(pin: str) -> str` - Hash PIN for storage (using credential_storage)
- `verify_pin(entered_pin: str, stored_hash: str) -> bool` - Verify entered PIN

### 7. Integrate PIN Check After Login

**File**: `ui/app.py`

Modify `_on_login_success()`:

- After successful login, check if PIN is enabled
- If enabled, show PIN entry dialog
- Only proceed to main app after correct PIN entry
- Handle PIN entry cancellation (logout user if required)

**File**: `ui/pages/login_page.py`

Modify `_attempt_auto_login()`:

- After successful auto-login, check if PIN is enabled
- If enabled, show PIN entry dialog before showing main app
- Handle PIN entry in auto-login flow

### 8. Update Localization

**Files**: `locales/en.json`, `locales/km.json`

Add translations:

- `pin_code`, `enable_pin_code`, `set_pin`, `change_pin`, `remove_pin`
- `enter_pin`, `confirm_pin`, `pin_mismatch`, `pin_invalid`
- `pin_required`, `pin_incorrect`

## Files to Modify

1. **`database/models/schema.py`** - Add PIN fields to schema
2. **`database/models/app_settings.py`** - Add PIN fields to model
3. **`database/managers/settings_manager.py`** - Update get/update methods
4. **`ui/pages/settings_page.py`** - Add PIN configuration UI (~100-150 lines)
5. **`ui/dialogs/pin_dialog.py`** - New PIN entry dialog (~150-200 lines)
6. **`utils/pin_validator.py`** - New PIN validation utilities (~50-80 lines)
7. **`ui/app.py`** - Add PIN check after login (~30-50 lines)
8. **`ui/pages/login_page.py`** - Add PIN check after auto-login (~30-50 lines)
9. **`locales/en.json`** - Add English translations
10. **`locales/km.json`** - Add Khmer translations

## Implementation Notes

### PIN Storage Security

- PIN is encrypted using `credential_storage.encrypt()` (same as login password)
- PIN is hashed before encryption for additional security
- PIN is never stored in plain text

### PIN Validation

- Must be exactly 6 digits
- Numeric only (0-9)
- Case-insensitive (though numeric only)

### User Experience

- PIN entry dialog shows visual feedback (dots for each digit)
- Error messages for invalid PIN format or incorrect PIN
- PIN can be enabled/disabled in settings
- If PIN is disabled, no PIN check after login

### Auto-Login Flow

- If auto-login succeeds and PIN is enabled, show PIN dialog
- User must enter correct PIN to access app
- If PIN is incorrect, show error and allow retry
- If user cancels PIN entry, logout (return to login page)

## Testing Considerations

### Unit Tests

**File**: `tests/unit/test_pin_validator.py` (new file)

Test PIN validation utilities:

- `test_validate_pin_format_valid()` - Valid 6-digit PIN
- `test_validate_pin_format_too_short()` - PIN less than 6 digits
- `test_validate_pin_format_too_long()` - PIN more than 6 digits
- `test_validate_pin_format_non_numeric()` - PIN with non-numeric characters
- `test_validate_pin_format_empty()` - Empty PIN
- `test_hash_pin()` - PIN hashing functionality
- `test_verify_pin_correct()` - Correct PIN verification
- `test_verify_pin_incorrect()` - Incorrect PIN verification
- `test_encrypt_decrypt_pin()` - PIN encryption/decryption using credential_storage

**File**: `tests/unit/test_settings_manager.py` (new file or extend existing)

Test PIN settings in database:

- `test_get_settings_with_pin()` - Load settings with PIN enabled
- `test_get_settings_without_pin()` - Load settings with PIN disabled
- `test_update_settings_enable_pin()` - Enable PIN in settings
- `test_update_settings_disable_pin()` - Disable PIN in settings
- `test_update_settings_change_pin()` - Change existing PIN
- `test_update_settings_remove_pin()` - Remove PIN from settings

**File**: `tests/unit/test_pin_dialog.py` (new file)

Test PIN dialog component:

- `test_pin_dialog_creation()` - Dialog initializes correctly
- `test_pin_dialog_6_digit_input()` - Accepts 6-digit input
- `test_pin_dialog_rejects_invalid_input()` - Rejects non-numeric input
- `test_pin_dialog_rejects_short_input()` - Rejects less than 6 digits
- `test_pin_dialog_submit_callback()` - Submit callback called with correct PIN
- `test_pin_dialog_cancel_callback()` - Cancel callback works

### Integration Tests

**File**: `tests/integration/test_pin_flow.py` (new file)

Test complete PIN flow:

- `test_pin_setup_in_settings()` - Set PIN in settings page
- `test_pin_change_in_settings()` - Change existing PIN
- `test_pin_remove_in_settings()` - Remove PIN from settings
- `test_pin_after_login()` - PIN required after successful login
- `test_pin_after_auto_login()` - PIN required after auto-login
- `test_pin_disabled_no_check()` - No PIN check when disabled
- `test_pin_incorrect_retry()` - Retry after incorrect PIN
- `test_pin_warning_displayed()` - Warning message displayed in settings

### Test Scenarios

1. **PIN Setup Flow**

   - Enable PIN toggle in settings
   - Set new PIN (6 digits)
   - Confirm PIN matches
   - Verify PIN saved encrypted

2. **PIN Change Flow**

   - Change existing PIN
   - Verify old PIN no longer works
   - Verify new PIN works

3. **PIN Removal Flow**

   - Remove PIN from settings
   - Verify PIN check skipped after login

4. **PIN After Login**

   - Login with credentials
   - PIN dialog appears
   - Enter correct PIN → access granted
   - Enter incorrect PIN → error shown, retry allowed

5. **PIN After Auto-Login**

   - Auto-login succeeds
   - PIN dialog appears
   - Enter correct PIN → access granted

6. **PIN Validation**

   - Test 5-digit PIN (should fail)
   - Test 7-digit PIN (should fail)
   - Test alphanumeric PIN (should fail)
   - Test 6-digit numeric PIN (should pass)

7. **PIN Warning Display**

   - Warning shown in settings when PIN enabled
   - Warning shown in PIN setup dialog
   - Warning uses appropriate color (orange/yellow)

8. **Localization**

   - Test PIN strings in English
   - Test PIN strings in Khmer
   - Test warning message in both languages

### Test Fixtures

**File**: `tests/fixtures/pin_fixtures.py` (new file)

Add fixtures:

- `sample_pin_settings()` - Settings with PIN enabled
- `sample_encrypted_pin()` - Encrypted PIN for testing
- `mock_pin_dialog()` - Mock PIN dialog component

## Success Criteria

- ✅ PIN can be set/changed/removed in settings
- ✅ PIN is stored encrypted
- ✅ PIN is checked after login (including auto-login)
- ✅ PIN entry dialog works correctly
- ✅ PIN validation works (format and verification)
- ✅ PIN can be enabled/disabled
- ✅ Warning message displayed that PIN is stored locally only (not on server)
- ✅ Localization support (English/Khmer)
- ✅ No breaking changes to existing login flow

### To-dos

- [ ] Add PIN fields (pin_enabled, encrypted_pin) to app_settings table schema and create migration
- [ ] Add pin_enabled and encrypted_pin fields to AppSettings dataclass
- [ ] Update SettingsManager.get_settings() and update_settings() to handle PIN fields
- [ ] Create utils/pin_validator.py with PIN format validation and encryption/verification functions
- [ ] Create ui/dialogs/pin_dialog.py with 6-digit PIN entry dialog component
- [ ] Add PIN configuration UI to settings page General tab (enable toggle, set/change/remove buttons)
- [ ] Add PIN check in ui/app.py _on_login_success() method after successful login
- [ ] Add PIN check in ui/pages/login_page.py _attempt_auto_login() after successful auto-login
- [ ] Add PIN-related translations to locales/en.json and locales/km.json