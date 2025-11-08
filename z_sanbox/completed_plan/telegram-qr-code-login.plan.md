<!-- bdda3cf6-8b7a-40e0-b519-caaf680833e6 5f60885a-4c4e-4a1f-a939-ebe9b741cf2b -->
# QR Code Telegram Login Implementation

## Overview

Add QR code authentication as an alternative to phone number + OTP login. Users will be able to choose between phone/OTP authentication or QR code scanning.

## Implementation Steps

### 1. Add QR Code Library Dependency

- Add `qrcode[pil]>=7.4.2` to `requirements.txt` for QR code generation
- Pillow is already available for image handling

### 2. Create QR Code Dialog Component

- Create `ui/dialogs/qr_code_dialog.py` (~200 lines)
- Display QR code image generated from Pyrogram's QR login token
- Show loading state while waiting for scan
- Show success/error messages
- Auto-refresh QR code if it expires
- Include instructions for users

### 3. Extend ClientManager for QR Code Login

- Update `services/telegram/client_manager.py` (~80 lines added)
- Add `start_session_qr()` method that:
  - Creates client without phone number (only api_id and api_hash)
  - Uses `client.invoke(auth.ExportLoginToken(...))` to generate QR token
  - Converts token to QR code image
  - Polls `auth.ExportLoginToken` to check for login completion
  - Uses `auth.AcceptLoginToken` when scan is detected
  - Handles 2FA if required
  - Returns success/error status and QR code data

### 4. Extend TelegramService

- Update `services/telegram/telegram_service.py` (~30 lines added)
- Add `start_session_qr()` method that wraps ClientManager's QR login
- Save credentials after successful QR login

### 5. Update Authentication UI

- Update `ui/pages/settings/tabs/authenticate_tab.py` (~100 lines added)
- Add toggle/button to choose between "Phone Login" and "QR Code Login"
- Show phone field only for phone login
- Show QR code dialog for QR login option

### 6. Update Settings Handlers

- Update `ui/pages/settings/handlers.py` (~50 lines added)
- Add `handle_telegram_connect_qr()` method
- Handle QR code dialog display and polling
- Integrate with existing error handling

### 7. Add Translations

- Update `locales/en.json` and `locales/km.json`
- Add keys: `login_with_qr_code`, `scan_qr_code`, `qr_code_instructions`, `qr_code_expired`, `qr_code_scanning`, `qr_code_success`, `choose_login_method`, `phone_login`, `qr_code_login`

### 8. Handle Edge Cases

- QR code expiration (regenerate automatically)
- Network errors during polling
- 2FA requirement after QR scan
- User cancellation

## Files to Modify

- `requirements.txt` - Add qrcode library
- `services/telegram/client_manager.py` - Add QR login method
- `services/telegram/telegram_service.py` - Add QR login wrapper
- `ui/dialogs/qr_code_dialog.py` - New file for QR dialog
- `ui/pages/settings/tabs/authenticate_tab.py` - Add QR login option
- `ui/pages/settings/handlers.py` - Add QR login handler
- `locales/en.json` - Add English translations
- `locales/km.json` - Add Khmer translations

## Technical Details

- Pyrogram's `qr_login()` returns a QR code token that needs to be converted to an image
- QR code expires after ~30 seconds, need to regenerate
- Polling interval: check every 2-3 seconds for login completion
- QR code login doesn't require phone number input
- After QR scan, user may still need to enter 2FA password if enabled

### To-dos

- [ ] Add qrcode[pil] library to requirements.txt
- [ ] Create ui/dialogs/qr_code_dialog.py component to display QR code and handle scanning flow
- [ ] Add start_session_qr() method to ClientManager for QR code authentication
- [ ] Add start_session_qr() method to TelegramService wrapper
- [ ] Update authenticate_tab.py to add QR code login option with toggle/button
- [ ] Add handle_telegram_connect_qr() method to settings handlers
- [ ] Add QR code related translations to en.json and km.json