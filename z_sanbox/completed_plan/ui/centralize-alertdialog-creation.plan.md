<!-- cfa5cc02-795e-4bba-8d6a-bf4dc159809f 09647774-7ff8-4403-8c8a-5729a92399be -->
# Centralize AlertDialog Creation Pattern

## Problem
Multiple AlertDialogs throughout the app have inconsistent patterns, especially for nested confirmation dialogs. The main issue is that when showing a confirmation dialog from within another dialog, the main dialog needs to be restored on cancel, which is currently only handled correctly in `message_detail_dialog.py`.

## Solution
Add centralized dialog methods to `ThemeManager` in `ui/theme.py` that handle:
- Nested confirmation dialogs (with main dialog restoration)
- Simple info/error dialogs
- Custom content dialogs
- Proper page reference handling

## Implementation

### 1. Create Centralized Dialog Utility (`ui/dialogs/dialog.py`)

Create a new file `ui/dialogs/dialog.py` with a `DialogManager` class containing:

- `show_confirmation_dialog()` - For nested confirmation dialogs
  - Parameters: page, title, message, on_confirm, on_cancel, confirm_text, cancel_text, confirm_color, main_dialog (optional)
  - Handles main dialog restoration on cancel if `main_dialog` is provided
  - Uses elevation=24 for nested dialogs
  
- `show_simple_dialog()` - For simple info/error dialogs
  - Parameters: page, title, message, actions (optional)
  - Simple wrapper for common dialog patterns
  
- `show_custom_dialog()` - For dialogs with custom content
  - Parameters: page, title, content, actions, modal, elevation
  - Flexible dialog creation with full control

- `_get_page_from_event()` - Helper to extract page from event/control
  - Private method to handle page reference extraction consistently

- Move existing `show_dialog()` from `theme.py` to this class (if needed for backward compatibility)

Export a global `dialog_manager` instance similar to `theme_manager`.

### 2. Refactor Existing AlertDialog Usages

Update all files that create AlertDialogs:

**Priority 1 - Nested Confirmation Dialogs:**
- `ui/dialogs/message_detail_dialog.py` - `_delete_message()` method
- `ui/dialogs/user_detail_dialog.py` - `_delete_user()` and `_delete_profile_photo()` methods

**Priority 2 - Simple Dialogs:**
- `ui/dialogs/fetch_data_dialog.py` - `_show_upgrade_dialog()` method
- `ui/app.py` - License expired dialog
- `ui/pages/profile_page.py` - Logout confirmation dialog

**Priority 3 - Custom Dialogs:**
- `ui/pages/settings/handlers.py` - `_show_auth_dialog()` (TelegramAuthDialog - keep as is, but ensure it works)
- `ui/pages/settings_page.py` - `_show_auth_dialog()` (TelegramAuthDialog - keep as is)

### 3. Key Features

- **Nested Dialog Support**: When `main_dialog` is provided, automatically restores it on cancel
- **Consistent Page Handling**: Uses helper method to get page from event/control/self
- **Proper Elevation**: Nested dialogs use elevation=24 to appear above main dialog
- **Error Handling**: All methods handle missing page references gracefully
- **Backward Compatible**: Existing `show_dialog` method enhanced or replaced

### 4. Files to Modify

1. `ui/theme.py` - Add new dialog methods (~150 lines)
2. `ui/dialogs/message_detail_dialog.py` - Refactor `_delete_message()` (~15 lines changed)
3. `ui/dialogs/user_detail_dialog.py` - Refactor `_delete_user()` and `_delete_profile_photo()` (~30 lines changed)
4. `ui/dialogs/fetch_data_dialog.py` - Refactor `_show_upgrade_dialog()` (~10 lines changed)
5. `ui/app.py` - Refactor license expired dialog (~15 lines changed)
6. `ui/pages/profile_page.py` - Refactor `_handle_logout()` (~15 lines changed)

### 5. Testing Considerations

- Verify nested confirmation dialogs restore main dialog on cancel
- Verify nested confirmation dialogs close both dialogs on confirm
- Verify simple dialogs work correctly
- Verify page reference extraction works from events
- Test error cases (missing page, etc.)
