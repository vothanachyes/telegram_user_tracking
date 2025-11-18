<!-- d830066b-32d3-48cc-b9eb-0df0eae04129 e0eaf391-cd74-4514-a0f6-453b024104e1 -->
# PIN Recovery Feature in Security Tab

## Overview

Add a PIN recovery section to the Security tab that allows users to export device information and encrypted PIN in JSON format. This helps users recover their PIN if they forget it by providing the necessary information to decrypt it on the same device.

## Implementation Details

### 1. Add PIN Recovery Section to Security Tab

**File**: `ui/pages/settings/tabs/security_tab/page.py`

Add a new PIN Recovery card section that:

- Is protected by Windows authentication (same as other Security tab features)
- Displays device information and encrypted PIN in JSON format
- Shows masked content (asterisks) in the UI
- Provides a "Copy to Clipboard" button that copies the full unmasked JSON

**Components to add:**

- `pin_recovery_json_field`: Text field displaying masked JSON (read-only, password mode)
- `copy_pin_recovery_btn`: Button to copy full JSON to clipboard (disabled until authenticated)
- `pin_recovery_card`: Card container for the PIN recovery section

**Methods to add:**

- `_get_pin_recovery_data()`: Generate JSON with device info and encrypted PIN
- `_get_masked_json()`: Return JSON with values masked using asterisks
- `_copy_pin_recovery_data()`: Copy full JSON to clipboard

### 2. Device Information Collection

**File**: `ui/pages/settings/tabs/security_tab/page.py`

Use `platform` module to get:

- `platform.node()` → `hostname`
- `platform.machine()` → `machine`
- `platform.system()` → `system`

Get encrypted PIN from `self.current_settings.encrypted_pin`

**JSON Structure:**

```json
{
  "hostname": "device-hostname",
  "machine": "x86_64",
  "system": "Darwin",
  "encrypted_pin": "encrypted_pin_string"
}
```

### 3. Masked Display Implementation

**File**: `ui/pages/settings/tabs/security_tab/page.py`

- Display JSON with all values masked using asterisks (e.g., `"hostname": "********"`)
- Use `password=True` on the text field for additional masking
- Keep the full JSON in memory for copying

**Masking logic:**

- Replace all non-structural characters (values, not keys) with asterisks
- Preserve JSON structure (keys, brackets, commas, colons)
- Example: `"hostname": "********"` instead of `"hostname": "MyComputer"`

### 4. Copy to Clipboard Functionality

**File**: `ui/pages/settings/tabs/security_tab/page.py`

- Use `page.set_clipboard()` to copy full unmasked JSON
- Show success snackbar after copying
- Only enabled when authenticated

### 5. UI Integration

**File**: `ui/pages/settings/tabs/security_tab/page.py`

- Add PIN Recovery card after Encryption card in `build()` method
- Add to `protected_content` Column (so it's covered by auth overlay)
- Disable copy button until authenticated (in `_update_ui()` method)
- Only show section if PIN is enabled (`pin_enabled` is True)

### 6. Localization

**Files**: `locales/en.json`, `locales/km.json`

Add translations:

- `pin_recovery`: "PIN Recovery"
- `pin_recovery_info`: "Export device information and encrypted PIN for PIN recovery"
- `pin_recovery_data`: "PIN Recovery Data"
- `copy_pin_recovery_data`: "Copy to Clipboard"
- `pin_recovery_data_copied`: "PIN recovery data copied to clipboard"
- `pin_recovery_not_available`: "PIN recovery is only available when PIN is enabled"

## Files to Modify

1. **`ui/pages/settings/tabs/security_tab/page.py`** (~100-150 lines added)

   - Add PIN recovery section UI components
   - Add methods for generating and masking JSON
   - Add copy to clipboard functionality
   - Integrate with authentication system

2. **`locales/en.json`** (~6 new translation keys)

   - Add English translations for PIN recovery feature

3. **`locales/km.json`** (~6 new translation keys)

   - Add Khmer translations for PIN recovery feature

## Implementation Notes

### Security Considerations

- PIN recovery section is protected by Windows authentication (same as other Security tab features)
- Only shows when PIN is enabled
- Masked display prevents accidental exposure
- Full data only accessible via authenticated copy action

### User Experience

- Clear visual indication that content is masked
- Success feedback when copying to clipboard
- Section only visible when PIN is enabled
- Consistent with existing Security tab authentication pattern

### JSON Format

- Clean, readable JSON format
- Includes all necessary information for PIN decryption
- Can be used with the decryption script provided earlier