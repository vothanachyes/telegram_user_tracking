<!-- 7e6b9a67-7db9-4bde-ad76-413755ddfc94 bbd44c55-a398-4749-b177-604ed09b3fff -->
# Fetch Data Dialog Enhancement - Account & Group Selection

## Overview

Enhance the fetch data dialog with account selection, group selection, permission validation, and account management with deletion limits. Organized into 4 phases for incremental implementation.

---

## Phase 1: Account Management & Status Tracking

### 1.1 Add Account Activity Tracking Table

**File**: `database/models/schema.py` (~15 lines added)

- Create `account_activity_log` table to track add/delete operations:
  - `id` (PRIMARY KEY)
  - `user_email` (TEXT, NOT NULL)
  - `action` (TEXT: 'add' or 'delete')
  - `phone_number` (TEXT)
  - `action_timestamp` (TIMESTAMP)
  - Index on `user_email` and `action_timestamp`

### 1.2 Add Account Activity Manager

**File**: `database/managers/account_activity_manager.py` (~80 lines, new file)

- `log_account_action(user_email, action, phone_number)` - Log add/delete operations
- `get_recent_activity_count(user_email, hours=48)` - Count operations in last 48 hours
- `can_perform_account_action(user_email)` - Check if user can add/delete (max 2 in 48h)
- `get_activity_log(user_email, limit=10)` - Get recent activity for display

### 1.3 Add Account Status Checking

**File**: `database/managers/telegram_credential_manager.py` (~50 lines added)

- `check_account_status(credential_id)` - Check if account session is valid
  - Returns: 'active', 'expired', 'not_connected', 'error'
- `get_credential_with_status(credential_id)` - Get credential with status info
- `get_all_credentials_with_status()` - Get all credentials with their status

### 1.4 Update TelegramService for Account Status

**File**: `services/telegram/telegram_service.py` (~40 lines added)

- `check_account_status(credential)` - Async check if account can connect
- `get_account_status(credential_id)` - Get status of specific account
- `get_all_accounts_with_status()` - Get all accounts with status info

---

## Phase 2: Account Selection UI & Deletion Limits

### 2.1 Create Account Selection Component

**File**: `ui/components/account_selector.py` (~200 lines, new file)

- Dropdown showing all saved accounts
- Display account status badges:
  - "Active" (green) - connected and valid
  - "Expired" (red) - session expired, cannot select
  - "Not Available" (gray) - not connected, cannot select
- Show phone number and last used date
- Default to currently connected/default account
- Disable expired/not available accounts in dropdown
- Show account count (e.g., "2/3 accounts")

### 2.2 Add Account Deletion with Limits

**File**: `ui/pages/settings/handlers.py` (~100 lines added)

- Update `handle_remove_account()` to:
  - Check account activity limits (max 2 operations in 48h)
  - Log deletion in activity log
  - Show error if limit reached: "Account deletion limit reached. You can delete/add accounts 2 times within 48 hours."
  - Prevent deletion if limit exceeded
- Add `_check_account_activity_limit()` helper method

### 2.3 Update Account Addition with Limits

**File**: `ui/pages/settings/handlers.py` (~50 lines modified)

- Update `handle_add_account_phone()` and `handle_add_account_qr()` to:
  - Check account activity limits before adding
  - Log addition in activity log after successful authentication
  - Show error if limit reached
- Integrate with account activity manager

### 2.4 Add Translation Keys

**Files**: `locales/en.json` and `locales/km.json` (~10 keys each)

- `account_status_active`: "Active"
- `account_status_expired`: "Expired"
- `account_status_not_available`: "Not Available"
- `account_deletion_limit_reached`: "Account deletion limit reached. You can delete/add accounts 2 times within 48 hours."
- `account_addition_limit_reached`: "Account addition limit reached. You can add accounts 2 times within 48 hours."
- `select_account`: "Select Account"
- `account_last_used`: "Last used: {date}"
- `cannot_select_expired_account`: "This account session has expired"
- `cannot_select_unavailable_account`: "This account is not available"

---

## Phase 3: Group Selection & Permission Validation

### 3.1 Create Group Selection Component

**File**: `ui/components/group_selector.py` (~150 lines, new file)

- Combined input: TextField for manual entry + Dropdown for saved groups
- Dropdown shows:
  - Group name (group_id)
  - Last fetch date (if available)
  - Group username (if available)
- Format: "Group Name (-1001234567890) - Last fetched: 2024-01-15"
- Allow manual group ID entry
- Disable group selection until account is selected

### 3.2 Add Group Info Fetching

**File**: `services/telegram/telegram_service.py` (~30 lines added)

- `fetch_and_validate_group(account_credential, group_id)` - Fetch group info using specific account
  - Returns: (success, group_info, error_message, has_access)
  - Checks if account has access to the group
  - Returns group name, username, member status

### 3.3 Add Permission Validation

**File**: `ui/dialogs/fetch_data_dialog.py` (~100 lines added)

- Add account selector component
- Add group selector component
- Add `_validate_account_group_access()` method:
  - Check if selected account can access selected group
  - Fetch group info to verify access
  - Show specific error messages:
    - "Account {phone} is not a member of group {group_name}"
    - "Account {phone} does not have permission to access group {group_name}"
    - "Group not found or invalid"
    - "Account session expired, please reconnect"
- Update `_start_fetch()` to validate before fetching

### 3.4 Update Fetch Data Dialog UI

**File**: `ui/dialogs/fetch_data_dialog.py` (~80 lines modified)

- Add account selector above group selector
- Add group selector (replacing manual group_id_field)
- Show group info after selection (name, last fetch date)
- Disable group selector until account is selected
- Show loading state when fetching group info
- Display last fetch date for selected group

### 3.5 Add Translation Keys

**Files**: `locales/en.json` and `locales/km.json` (~8 keys each)

- `select_group`: "Select Group"
- `enter_group_id_manually`: "Or enter Group ID manually"
- `group_not_found`: "Group not found or invalid"
- `account_not_member": "Account {phone} is not a member of group {group_name}"
- `account_no_permission": "Account {phone} does not have permission to access group {group_name}"
- `fetching_group_info": "Fetching group information..."
- `group_info_loaded": "Group: {name} (Last fetched: {date})"
- `select_account_first": "Please select an account first"

---

## Phase 4: Testing & Edge Cases

### 4.1 Unit Tests for Account Activity

**File**: `tests/unit/test_account_activity.py` (~150 lines, new file)

- Test `log_account_action()` - verify logging works
- Test `get_recent_activity_count()` - verify 48-hour window
- Test `can_perform_account_action()` - verify limit enforcement
- Test edge cases:
  - Exactly 2 operations in 48h (should block)
  - 2 operations 49 hours ago (should allow)
  - Multiple users (should not interfere)

### 4.2 Unit Tests for Account Status

**File**: `tests/unit/test_account_status.py` (~100 lines, new file)

- Test `check_account_status()` with:
  - Active session
  - Expired session
  - Invalid session
  - Not connected account
- Test status filtering in dropdown

### 4.3 Integration Tests for Fetch Dialog

**File**: `tests/integration/test_fetch_dialog.py` (~200 lines, new file)

- Test account selection flow
- Test group selection (manual and dropdown)
- Test permission validation:
  - Valid account + valid group
  - Valid account + invalid group
  - Expired account + valid group
  - Valid account + group user is not member of
- Test account activity limits during fetch operations
- Test error messages display correctly

### 4.4 Edge Case Handling

**Files**: Multiple files (~50 lines total)

- Handle account switching during fetch
- Handle group ID validation (negative numbers, format)
- Handle network errors during group info fetch
- Handle session expiration during validation
- Handle empty account/group lists
- Handle concurrent operations

---

## Files to Create

- `database/managers/account_activity_manager.py` - Account activity tracking
- `ui/components/account_selector.py` - Account selection component
- `ui/components/group_selector.py` - Group selection component
- `tests/unit/test_account_activity.py` - Activity tests
- `tests/unit/test_account_status.py` - Status tests
- `tests/integration/test_fetch_dialog.py` - Integration tests

## Files to Modify

- `database/models/schema.py` - Add account_activity_log table
- `database/managers/telegram_credential_manager.py` - Add status checking
- `services/telegram/telegram_service.py` - Add account status and group validation
- `ui/dialogs/fetch_data_dialog.py` - Add account/group selectors and validation
- `ui/pages/settings/handlers.py` - Add deletion limits
- `locales/en.json` - Add translations
- `locales/km.json` - Add translations

## Technical Details

### Account Activity Limits

- Maximum 2 add/delete operations per 48 hours (rolling window)
- Applies to ALL license tiers
- Counts both additions and deletions together
- Resets after 48 hours from first operation in window
- Prevents abuse of account switching to bypass license limits

### Account Status

- **Active**: Session valid, can connect, can be selected
- **Expired**: Session expired, cannot connect, disabled in dropdown
- **Not Available**: Not connected, cannot be selected, disabled in dropdown

### Permission Validation Flow

1. User selects account
2. User selects/enters group ID
3. System fetches group info using selected account
4. System checks if account is member of group
5. If valid, proceed with fetch
6. If invalid, show specific error message

### Group Selection

- Dropdown shows saved groups with last fetch date
- Manual entry still allowed for new groups
- Group info fetched when account is selected and group is chosen
- Last fetch date displayed for user verification

## Database Schema Addition

```sql
CREATE TABLE IF NOT EXISTS account_activity_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_email TEXT NOT NULL,
    action TEXT NOT NULL,  -- 'add' or 'delete'
    phone_number TEXT,
    action_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_account_activity_user_email ON account_activity_log(user_email);
CREATE INDEX IF NOT EXISTS idx_account_activity_timestamp ON account_activity_log(action_timestamp);
```