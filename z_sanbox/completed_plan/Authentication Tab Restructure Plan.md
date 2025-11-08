<!-- 28267399-96fe-4445-8096-3cc793ed2ad0 e35aa584-337a-4b34-9ba2-2c6c893aa30a -->
# Authentication Tab Restructure Plan

## Overview

Restructure the Authentication tab to use left navigation with two selectable sections:

1. **Accounts**: Account management (add, delete) with license limit enforcement
2. **Configuration**: Telegram app configuration (API_ID, API_HASH)

## Account Limits by License Tier

- Bronze: 1 account
- Silver: 1 account  
- Gold: 3 accounts
- Premium: 5 accounts

## Implementation Steps

### 1. Add Account Limits to License System

**File**: `utils/constants.py` (~10 lines added)

- Add `max_accounts` to each tier in `LICENSE_PRICING`:
  - Bronze: `max_accounts: 1`
  - Silver: `max_accounts: 1`
  - Gold: `max_accounts: 3`
  - Premium: `max_accounts: 5`

**File**: `database/models/schema.py` (~2 lines modified)

- Add `max_accounts INTEGER NOT NULL DEFAULT 1` to `user_license_cache` table

**File**: `services/license_service.py` (~50 lines added)

- Add `can_add_account(user_email, uid)` method:
  - Check license status
  - Get current account count from database
  - Compare with `max_accounts` from license tier
  - Return `(can_add, error_message, current_count, max_count)`
- Update `check_license_status()` to include `max_accounts` in return dict
- Update `sync_from_firebase()` to sync `max_accounts` field

**File**: `database/managers/license_manager.py` (~20 lines added)

- Update license cache model to include `max_accounts`
- Update sync methods to handle `max_accounts` field

### 2. Create Add Account Dialog

**File**: `ui/dialogs/add_account_dialog.py` (~150 lines, new file)

- Create dialog component with:
  - Phone number input field
  - Login method selection (phone/QR - QR disabled for now)
  - OTP/2FA password fields (similar to existing auth flow)
  - Validation for phone number format
  - Account existence check before submission
- Validate account doesn't exist (phone number, session file)
- Show error messages for duplicate accounts
- Integrate with Telegram connection flow

### 3. Restructure AuthenticateTab with Left Navigation

**File**: `ui/pages/settings/tabs/authenticate_tab.py` (~400 lines modified)

- Replace current single-column layout with left navigation structure:
  - Left sidebar: Navigation buttons for "Accounts" and "Configuration"
  - Right content area: Dynamic content based on selected section
- **Accounts Section**:
  - Account count display: "X/Y acc" (e.g., "2/5 acc") with hover tooltip showing license tier info
  - Add Account button (disabled when limit reached)
  - Accounts list with status badges and delete buttons
  - Refresh status button
- **Configuration Section**:
  - API_ID and API_HASH fields
  - API status text
  - Save/Cancel buttons
- Implement section switching logic
- Update all existing methods to work with new structure

### 4. Add Account Validation Logic

**File**: `database/managers/telegram_credential_manager.py` (~30 lines added)

- Add `account_exists(phone_number)` method:
  - Check if phone number exists in database
  - Check if session file exists on disk
  - Return boolean and reason if exists
- Add `get_account_count()` method to count total saved accounts

**File**: `ui/pages/settings/handlers.py` (~100 lines added)

- Add `handle_add_account()` method:
  - Check license limit using `license_service.can_add_account()`
  - Validate account doesn't exist using `telegram_credential_manager.account_exists()`
  - Show add account dialog
  - Handle account addition flow
  - Update account count display after successful addition
- Update `handle_telegram_connect()` to check account limits before connecting
- Add account count update logic

### 5. Add Translation Keys

**Files**: `locales/en.json` and `locales/km.json` (~15 keys each)

- `accounts_section`: "Accounts"
- `configuration_section`: "Configuration"
- `account_count_display`: "Accounts: {current}/{max}"
- `account_limit_reached`: "Account limit reached. You have {current}/{max} accounts. Upgrade your license to add more."
- `account_already_exists`: "This account already exists. Phone number: {phone}"
- `add_account`: "Add Account"
- `account_count_tooltip`: "You have {current} out of {max} accounts allowed by your {tier} license"
- `no_accounts_limit`: "No account limit" (for unlimited tiers if needed)

### 6. Update UI Components

**File**: `ui/pages/settings/tabs/authenticate_tab.py` (continued)

- Create `_build_left_navigation()` method for sidebar
- Create `_build_accounts_section()` method (enhanced version)
- Create `_build_configuration_section()` method (extracted from current API config)
- Add account count display component with hover tooltip
- Update `build()` method to use new layout structure
- Handle section switching with state management

## Technical Details

### Layout Structure

```
┌─────────────────────────────────────────┐
│  Authentication Tab                      │
├──────────┬──────────────────────────────┤
│ Accounts │  [Selected Section Content]  │
│ Config   │                              │
└──────────┴──────────────────────────────┘
```

### Account Validation

When adding an account, validate:

1. Phone number format (existing validator)
2. Phone number not in database
3. Session file doesn't exist on disk
4. License limit not exceeded
5. Account activity limits (existing 48h limit check)

### Account Count Display

- Format: "2/5 acc" (compact)
- Hover tooltip: "You have 2 out of 5 accounts allowed by your Premium license"
- Update dynamically when accounts are added/removed
- Disable "Add Account" button when limit reached

## Files to Modify

- `utils/constants.py` - Add max_accounts to license tiers
- `database/models/schema.py` - Add max_accounts to license cache
- `services/license_service.py` - Add can_add_account method
- `database/managers/license_manager.py` - Handle max_accounts field
- `database/managers/telegram_credential_manager.py` - Add validation methods
- `ui/pages/settings/tabs/authenticate_tab.py` - Restructure with navigation
- `ui/pages/settings/handlers.py` - Add account management handlers
- `locales/en.json` - Add translations
- `locales/km.json` - Add translations

## Files to Create

- `ui/dialogs/add_account_dialog.py` - Add account dialog component