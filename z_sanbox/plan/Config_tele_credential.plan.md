<!-- 1c4c2b0c-f643-45ae-a59c-710d99ec3a45 1f449f68-75a9-462c-ad80-8099edb53d12 -->
# Reorganize Settings Page into Tabs

## Overview

Restructure `ui/pages/settings_page.py` to use a tabbed interface with three tabs: General, Authenticate, and Configure. Each tab will have its own Save/Cancel buttons.

## Implementation Details

### 1. General Tab

- **Content**: Appearance settings (theme, language, corner radius)
- **Save/Cancel**: Per-tab buttons
- **Fields**: 
- Theme switch (dark/light)
- Language dropdown (English/Khmer)
- Corner radius slider

### 2. Authenticate Tab

- **Content**: Two separate sections for API App configuration and Account authentication
- **Save/Cancel**: Per-tab buttons
- **Section 1: API App Configuration**
- API ID text field
- API Hash text field (password type)
- Info text: "Get your API credentials from https://my.telegram.org/apps"
- Save button: Saves API ID and API Hash to settings (does not connect to Telegram)
- Status: "API App: Configured" or "API App: Not Configured"
- **Section 2: Telegram Account Connection**
- Phone number text field
- Connection status indicator (connected/disconnected with phone number)
- "Connect to Telegram" button (enabled only when API App is configured)
- "Disconnect" button (shown when connected)
- **Authentication Flow**:
- When user clicks "Connect to Telegram":

  1. Validate that API ID and API Hash are saved in settings
  2. Validate phone number format
  3. Call `telegram_service.start_session()` with callbacks
  4. Show OTP input (inline or dialog) when code is sent
  5. Handle 2FA password if required (show password field)
  6. Display success message and update connection status
  7. Save session automatically on success

- **Status Display**: 
- Show "API App: Configured" or "API App: Not Configured"
- Show "Account: Connected (phone)" or "Account: Not Connected"
- Display last connection time if available

### 3. Configure Tab

- **Content**: All fetch and download settings
- **Save/Cancel**: Per-tab buttons
- **Fields**:
- Download directory path
- Download media switch
- Max file size slider
- Fetch delay slider
- Media type checkboxes (photos, videos, documents, audio)

### 4. Technical Changes

#### File: `ui/pages/settings_page.py`

- Replace single-column layout with `ft.Tabs` component
- Create three tab content methods: `_create_general_tab()`, `_create_authenticate_tab()`, `_create_configure_tab()`
- Each tab will have its own Save/Cancel button handlers
- Add Telegram authentication flow with OTP dialog
- Add connection status display in Authenticate tab
- Split `_save_settings()` into per-tab save methods: `_save_general()`, `_save_authenticate()`, `_save_configure()`
- Add `_handle_telegram_connect()` method to initiate authentication flow
- Add OTP input dialog (can be inline in tab or separate dialog)
- Add 2FA password input (shown conditionally)

#### New Dialog: `ui/dialogs/telegram_auth_dialog.py` (optional)

- Alternative: Handle OTP/2FA inline in the Authenticate tab
- If using dialog: Create dialog for OTP code and 2FA password input

### 5. Integration Points

- Use `telegram_service.start_session()` with callbacks for OTP and 2FA
- Access `telegram_service` from parent app (via callback or service injection)
- Check `telegram_service.is_connected()` for status display
- Load saved credentials from `db_manager.get_default_credential()` to show connection status

## Files to Modify

- `ui/pages/settings_page.py` - Complete restructure with tabs

## Files to Create (if needed)

- `ui/dialogs/telegram_auth_dialog.py` - Optional dialog for OTP/2FA input (or handle inline)

## Dependencies

- TelegramService must be accessible (passed from parent or via callback)
- DatabaseManager for loading/saving settings and credentials