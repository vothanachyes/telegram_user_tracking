<!-- 90cb82c4-05df-4e20-8573-19890ccae894 393f96b1-eecd-4f49-9abd-552623743197 -->
# Fetch Data Dialog Enhancement - Account & Group Selection

## Overview

Enhance the fetch data dialog with account selection, group selection, permission validation, and account management with deletion limits. Organized into 4 phases for incremental implementation.

**Key Clarifications:**

- Multiple sessions can be saved (already supported by schema)
- Status checking: both on-demand and periodic background updates
- Account removal UI: in `authenticate_tab.py`
- No database migration needed (development phase)
- Account switching: use temporary client for fetch operations (keep current session connected)

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
- Add `delete_telegram_credential(credential_id)` - Delete credential by ID

### 1.4 Update TelegramService for Account Status

**File**: `services/telegram/telegram_service.py` (~60 lines added)

- `check_account_status(credential)` - Async check if account can connect (on-demand)
- `get_account_status(credential_id)` - Get status of specific account
- `get_all_accounts_with_status()` - Get all accounts with status info
- `fetch_messages_with_account(credential, group_id, ...)` - Fetch using temporary client
  - Creates temporary client for selected account
  - Fetches messages without disconnecting current session
  - Cleans up temporary client after fetch
- `fetch_and_validate_group(account_credential, group_id)` - Fetch group info using specific account
  - Returns: (success, group_info, error_message, has_access)
  - Uses temporary client for validation

### 1.5 Add Background Status Update Service

**File**: `services/telegram/account_status_service.py` (~100 lines, new file)

- Background service to periodically check account status
- `update_all_account_statuses()` - Check all saved accounts in background
- Runs every 5 minutes or on-demand
- Updates status in memory cache (not database)
- Can be triggered manually from UI

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
- Refresh button to update statuses on-demand

### 2.2 Add Account Management UI to Authenticate Tab

**File**: `ui/pages/settings/tabs/authenticate_tab.py` (~150 lines added)

- Add new section: "Saved Telegram Accounts"
- Display list of all saved accounts with:
  - Phone number
  - Status badge (Active/Expired/Not Available)
  - Last used date
  - Remove button for each account
- Add account button (already exists, but enhance)
- Show account count and activity limit status
- Refresh status button

### 2.3 Create Account Removal Handler

**File**: `ui/pages/settings/handlers.py` (~120 lines added)

- Create `handle_remove_account(credential_id)` method:
  - Get current user email from `auth_service.get_user_email()`
  - Check account activity limits (max 2 operations in 48h)
  - Log deletion in activity log
  - Delete credential from database
  - Delete session file from disk
  - Show error if limit reached: "Account deletion limit reached. You can delete/add accounts 2 times within 48 hours."
  - Prevent deletion if limit exceeded
- Add `_check_account_activity_limit(user_email)` helper method
- Add `_get_auth_service()` helper to access auth_service

### 2.4 Update Account Addition with Limits

**File**: `ui/pages/settings/handlers.py` (~50 lines modified)

- Update `handle_telegram_connect()` and `handle_telegram_connect_qr()` to:
  - Get current user email from auth_service
  - Check account activity limits before adding
  - Log addition in activity log after successful authentication
  - Show error if limit reached
- Integrate with account activity manager

### 2.5 Add Translation Keys

**Files**: `locales/en.json` and `locales/km.json` (~15 keys each)

- `account_status_active`: "Active"
- `account_status_expired`: "Expired"
- `account_status_not_available`: "Not Available"
- `account_deletion_limit_reached`: "Account deletion limit reached. You can delete/add accounts 2 times within 48 hours."
- `account_addition_limit_reached`: "Account addition limit reached. You can add accounts 2 times within 48 hours."
- `select_account`: "Select Account"
- `account_last_used`: "Last used: {date}"
- `cannot_select_expired_account`: "This account session has expired"
- `cannot_select_unavailable_account`: "This account is not available"
- `saved_telegram_accounts`: "Saved Telegram Accounts"
- `remove_account`: "Remove Account"
- `refresh_account_status`: "Refresh Status"
- `account_count`: "{current}/{total} accounts"
- `no_accounts_saved`: "No accounts saved"

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

### 3.2 Update Fetch Data Dialog Structure

**File**: `ui/dialogs/fetch_data_dialog.py` (~180 lines modified)

**Note**: File is currently 484 lines. To avoid exceeding 500 lines, extract account/group selection to separate methods:

- `_build_account_selection()` - Returns account selector component
- `_build_group_selection()` - Returns group selector component
- `_validate_account_group_access()` - Permission validation logic

- Add account selector component (using `_build_account_selection()`)
- Add group selector component (using `_build_group_selection()`)
- Add `_validate_account_group_access()` method:
  - Check if selected account can access selected group
  - Fetch group info using temporary client to verify access
  - Show specific error messages:
    - "Account {phone} is not a member of group {group_name}"
    - "Account {phone} does not have permission to access group {group_name}"
    - "Group not found or invalid"
    - "Account session expired, please reconnect"
- Update `_start_fetch()` to:
  - Use selected account (create temporary client)
  - Validate before fetching
  - Use `fetch_messages_with_account()` instead of `fetch_messages()`

### 3.3 Add Translation Keys

**Files**: `locales/en.json` and `locales/km.json` (~8 keys each)

- `select_group`: "Select Group"
- `enter_group_id_manually`: "Or enter Group ID manually"
- `group_not_found`: "Group not found or invalid"
- `account_not_member`: "Account {phone} is not a member of group {group_name}"
- `account_no_permission`: "Account {phone} does not have permission to access group {group_name}"
- `fetching_group_info`: "Fetching group information..."
- `group_info_loaded`: "Group: {name} (Last fetched: {date})"
- `select_account_first`: "Please select an account first"

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
  - Rolling window calculation

### 4.2 Unit Tests for Account Status

**File**: `tests/unit/test_account_status.py` (~100 lines, new file)

- Test `check_account_status()` with:
  - Active session
  - Expired session
  - Invalid session
  - Not connected account
- Test status filtering in dropdown
- Test background status update service

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
- Test temporary client creation and cleanup

### 4.4 Edge Case Handling

**Files**: Multiple files (~80 lines total)

- Handle account switching during fetch (temporary client)
- Handle group ID validation (negative numbers, format)
- Handle network errors during group info fetch
- Handle session expiration during validation
- Handle empty account/group lists
- Handle concurrent operations
- Handle user not logged in when logging activity
- Handle auth_service unavailable

---

## Files to Create

- `database/managers/account_activity_manager.py` - Account activity tracking
- `services/telegram/account_status_service.py` - Background status updates
- `ui/components/account_selector.py` - Account selection component
- `ui/components/group_selector.py` - Group selection component (renamed from group_selector.py to avoid conflict)
- `tests/unit/test_account_activity.py` - Activity tests
- `tests/unit/test_account_status.py` - Status tests
- `tests/integration/test_fetch_dialog.py` - Integration tests

## Files to Modify

- `database/models/schema.py` - Add account_activity_log table
- `database/managers/telegram_credential_manager.py` - Add status checking and deletion
- `services/telegram/telegram_service.py` - Add account status, temporary client support, and group validation
- `ui/dialogs/fetch_data_dialog.py` - Add account/group selectors and validation (extract methods to stay under 500 lines)
- `ui/pages/settings/tabs/authenticate_tab.py` - Add account management UI
- `ui/pages/settings/handlers.py` - Add account removal handler and activity limits
- `locales/en.json` - Add translations (fix syntax errors)
- `locales/km.json` - Add translations (fix syntax errors)

## Technical Details

### Account Activity Limits

- Maximum 2 add/delete operations per 48 hours (rolling window)
- Applies to ALL license tiers
- Counts both additions and deletions together
- Rolling window: counts operations in last 48 hours from current time
- Prevents abuse of account switching to bypass license limits
- Per user (based on user_email from auth_service)

### Account Status

- **Active**: Session valid, can connect, can be selected
- **Expired**: Session expired, cannot connect, disabled in dropdown
- **Not Available**: Not connected, cannot be selected, disabled in dropdown
- Status checked on-demand when needed
- Background service updates statuses every 5 minutes
- Status can be manually refreshed from UI

### Account Switching Strategy

- Use temporary client for fetch operations
- Keep current session connected
- Create temporary client for selected account
- Perform fetch operation
- Clean up temporary client after fetch
- Restore original client state

### Permission Validation Flow

1. User selects account
2. User selects/enters group ID
3. System creates temporary client for selected account
4. System fetches group info using temporary client
5. System checks if account is member of group
6. If valid, proceed with fetch using temporary client
7. Clean up temporary client after fetch
8. If invalid, show specific error message and clean up

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

## Implementation Notes

1. **Auth Service Access**: Ensure handlers can access `auth_service.get_user_email()`. May need to pass auth_service instance or import from services.

2. **File Size Management**: `fetch_data_dialog.py` is 484 lines. Extract account/group selection to separate methods to stay under 500 lines.

3. **Temporary Client Management**: Implement proper cleanup of temporary clients to avoid resource leaks. Use context managers or try/finally blocks.

4. **Status Caching**: Consider caching account statuses in memory to avoid repeated checks. Update cache on status refresh.

5. **Error Handling**: Handle cases where auth_service is unavailable, user not logged in, or network errors during status checks.

### To-dos

- [x] Add account_activity_log table to schema.py
- [x] Create account_activity_manager.py with logging and limit checking
- [x] Add status checking methods to telegram_credential_manager.py
- [x] Add account status methods and temporary client support to telegram_service.py
- [x] Create account_status_service.py for background status updates
- [x] Create account_selector.py component with status badges
- [x] Add account management UI section to authenticate_tab.py
- [x] Create handle_remove_account() method in handlers.py with activity limits
- [x] Update account addition handlers to check activity limits
- [x] Add translation keys for account management (en.json and km.json)
- [x] Create group_selector.py component with manual entry and dropdown
- [x] Update fetch_data_dialog.py with account/group selectors and validation
- [x] Add translation keys for group selection and validation
- [x] Create test_account_activity.py unit tests
- [x] Create test_account_status.py unit tests
- [x] Create test_fetch_dialog.py integration tests
- [x] Handle edge cases: network errors, session expiration, empty lists, concurrent operations