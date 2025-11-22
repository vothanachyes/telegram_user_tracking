Original Propmt:
Current existing:
1. when fetching message, yes we know user in fetching group
2. when import users, yes we know user in fetching group
3. if authenticated user, and users were contacted, yes we can see common groups

TODO:
1. We need one more table in database to store groups user joined, should has column: [id, user_id, group_id, group_name, group_username] (Why need group info, because this group is group where users joined, mostly may not exist in db_table `telegram_groups` and this table only for filtering, please dont confuse) 
2. In Telegam page, add a new tab next to Users Table call it "Users Group"
- Listing should be: UserId, UserFullname (click this cell will open Telegram app with his username), Total group joined (Should be Chip of Group Profile pic, only 3 chip stacked)
- No export fuction
- On click on row => Dialog Lisitng all group he joined, Simple Card Like GroupPage, on click on card => Link to that telegram Group (in telegram app)
- For Filter should has: search (same futcion to "Users Table"), "Group Selection" dropdown (select a group to see how many users in it)(Multiple selection, similar to Dashboard page),  
3. Current existing features I mentions very above, should record users groups. 
4. The last `3` Current existing features I mentions very above not yet implemented, so I think we should have another button next to  "Group Selection dropdown" at filter, click this button will pop dialog (Full Screen) , In this dialog: Header should Telegarm Account selector (authenticated accounts), Below it is "Users Table" (May be we can reuse "Users Table", it has select box column to select any user or select all)(For fetching common group within Selected Authenticated Telegram account and selected users in this "Users Table", yes we can call this button "Sync Group" next to "Group Selection"

Please plan me, any questions, and any suggestion please.


<!-- 38d9b186-9ef6-47db-8938-653664790189 06cb6a41-6303-48f8-9705-c1d99d83a1cb -->
# User Groups Tracking Feature Implementation Plan

## Overview

Add functionality to track which groups each user has joined, display this information in a new "Users Group" tab, and provide a sync feature to discover common groups between authenticated Telegram accounts and selected users.

## Database Changes

### 1. Create New Table: `user_groups`

**File:** `database/models/schema.py`

- Add table definition with columns: `id`, `user_id`, `group_id`, `group_name`, `group_username`
- Add UNIQUE constraint on `(user_id, group_id)` to prevent duplicates
- Add indexes: `idx_user_groups_user_id`, `idx_user_groups_group_id`
- Add foreign key to `telegram_users(user_id)`
- Note: This table is separate from `telegram_groups` - it tracks groups users joined (may not exist in main groups table)

### 2. Create Migration Script

**File:** `database/migrations/add_user_groups_table.py`

- Create migration to add `user_groups` table
- Handle existing databases gracefully

### 3. Create UserGroupManager

**File:** `database/managers/user_group_manager.py`

- Methods:
- `save_user_group(user_id, group_id, group_name, group_username)` - Insert or update (ON CONFLICT UPDATE)
- `get_user_groups(user_id)` - Get all groups for a user
- `get_users_by_group(group_id)` - Get all users in a specific group
- `get_user_group_count(user_id)` - Count groups for user
- `delete_user_group(user_id, group_id)` - Remove relationship
- `get_groups_with_user_counts(group_ids)` - Get groups with user counts for filtering

### 4. Update DatabaseManager

**File:** `database/managers/db_manager.py`

- Add `_user_group` manager instance
- Expose UserGroupManager methods through db_manager

## Backend Services - Data Collection

### 5. Update MessageFetcher

**File:** `services/telegram/message_fetcher.py`

- In `fetch_messages()`, after processing each message:
- Extract group info (group_id, group_name, group_username from group entity)
- Call `db_manager.save_user_group(user_id, group_id, group_name, group_username)`
- This records user-group relationship when messages are fetched

### 6. Update MemberFetcher

**File:** `services/telegram/member_fetcher.py`

- In `fetch_members()`, after processing each member:
- Extract group info from entity
- Call `db_manager.save_user_group(user.id, group_id, group_name, group_username)`
- This records user-group relationship when users are imported

### 7. Create CommonGroupsFetcher Service

**File:** `services/telegram/common_groups_fetcher.py`

- Similar structure to `MemberFetcher`
- Methods:
- `fetch_common_groups(credential, user_ids, on_progress, cancellation_flag)`
- Iterate through authenticated account's dialogs
- For each group, check if selected users are members
- Save user-group relationships for found common groups
- Support rate limiting, time limits, progress callbacks, cancellation
- Return: `(success, fetched_count, error_message)`

## UI Components - Users Group Tab

### 8. Create UsersGroupTabComponent

**File:** `ui/pages/telegram/components/users_group_tab.py`

- Similar structure to `UsersTabComponent`
- Table columns: "No", "User ID", "Full Name", "Groups Joined" (chips column)
- Chips display: Show up to 3 group profile pictures stacked (or icons if no photo)
- Row click handler: Opens dialog showing all groups user joined
- Filters:
- Search field (same as Users Table)
- Group Selection dropdown (multiple selection, similar to Dashboard GroupSelectorComponent)
- "Sync Group" button (opens full-screen dialog)
- No export menu

### 9. Create UserGroupsDialog

**File:** `ui/dialogs/user_groups_dialog.py`

- Dialog showing all groups a user has joined
- Card layout similar to `GroupsComponents._build_group_card()`
- Each card clickable: Opens Telegram group link (`https://t.me/{group_username}` or `https://t.me/c/{group_id}`)
- Display: Group photo, group name, group username, group ID

### 10. Create SyncGroupsDialog

**File:** `ui/dialogs/sync_groups_dialog.py`

- Full-screen dialog (modal)
- Header: Telegram Account selector dropdown (all authenticated accounts from `db_manager.get_all_credentials_with_status()`)
- Body: Users Table with checkboxes
- Reuse `UsersTabComponent` table structure but add checkbox column
- "Select All" checkbox in header
- Display: Checkbox, User ID, Username, Full Name
- Footer: 
- "Sync Groups" button (starts fetching)
- Progress indicator (progress bar, status text, cancellation button)
- Rate limit and time limit settings (similar to Import Users dialog)
- On sync:
- Get selected account credential
- Get selected user IDs
- Call `CommonGroupsFetcher.fetch_common_groups()`
- Show progress updates
- Allow cancellation
- On completion: Show success message with count, refresh Users Group tab

### 11. Update TelegramPage

**File:** `ui/pages/telegram/page.py`

- Add third tab: "Users Group" tab
- Initialize `UsersGroupTabComponent`
- Add handlers for tab interactions
- Wire up sync groups dialog

### 12. Update TelegramViewModel

**File:** `ui/pages/telegram/view_model.py`

- Add methods:
- `get_users_with_group_counts(group_ids=None)` - Get users with their group counts
- `get_user_groups(user_id)` - Get all groups for a user
- `get_groups_with_user_counts(group_ids)` - For filter dropdown

### 13. Create GroupChipsComponent

**File:** `ui/components/group_chips.py`

- Reusable component for displaying group chips
- Props: `groups` (list), `max_display` (default 3)
- Display: Stacked circular images/icons (max 3 visible, "+N" indicator if more)
- Each chip clickable: Opens user groups dialog for that user
- Fallback: Icon if group photo not available

## UI Components - Filters

### 14. Update FiltersBarComponent or Create New

**File:** `ui/pages/telegram/components/filters_bar.py` or new component

- For Users Group tab: Add multi-select group dropdown
- Reuse `GroupSelectorComponent` pattern from Dashboard
- Or create simplified version for Users Group tab

## Integration Points

### 15. Update TelegramHandlers

**File:** `ui/pages/telegram/handlers/telegram_handlers.py`

- Add handler for Users Group tab row click
- Add handler for sync groups button
- Add handler for group chips click
- Wire up all interactions

## Localization

### 16. Update Locale Files

**Files:** `locales/en.json`, `locales/km.json`

- Add translations:
- "users_groups" / "Users Groups"
- "groups_joined" / "Groups Joined"
- "sync_groups" / "Sync Groups"
- "select_account" / "Select Account"
- "select_users" / "Select Users"
- "fetching_common_groups" / "Fetching Common Groups"
- "common_groups_found" / "Common Groups Found"
- "no_groups_found" / "No Groups Found"

## Testing Considerations

- Test UNIQUE constraint (try inserting duplicate)
- Test group name/username updates (ON CONFLICT UPDATE)
- Test sync groups with multiple users
- Test cancellation during sync
- Test rate limiting and time limits
- Test empty states (no groups, no users)
- Test group photo loading/fallbacks
- Test Telegram link generation (with/without username)

## File Structure Summary

**New Files:**

- `database/managers/user_group_manager.py`
- `database/migrations/add_user_groups_table.py`
- `services/telegram/common_groups_fetcher.py`
- `ui/pages/telegram/components/users_group_tab.py`
- `ui/dialogs/user_groups_dialog.py`
- `ui/dialogs/sync_groups_dialog.py`
- `ui/components/group_chips.py`

**Modified Files:**

- `database/models/schema.py`
- `database/managers/db_manager.py`
- `services/telegram/message_fetcher.py`
- `services/telegram/member_fetcher.py`
- `ui/pages/telegram/page.py`
- `ui/pages/telegram/view_model.py`
- `ui/pages/telegram/handlers/telegram_handlers.py`
- `locales/en.json`
- `locales/km.json`

### To-dos

- [ ] Create user_groups table schema with UNIQUE constraint and indexes
- [ ] Create migration script for user_groups table
- [ ] Create UserGroupManager with CRUD operations and query methods
- [ ] Integrate UserGroupManager into DatabaseManager
- [ ] Add user-group recording in MessageFetcher when processing messages
- [ ] Add user-group recording in MemberFetcher when importing users
- [ ] Create CommonGroupsFetcher service with progress, cancellation, rate limiting
- [ ] Create GroupChipsComponent for displaying stacked group profile pictures
- [ ] Create UsersGroupTabComponent with table, filters, and sync button
- [ ] Create UserGroupsDialog showing all groups a user joined with card layout
- [ ] Create SyncGroupsDialog with account selector, user table with checkboxes, and sync functionality
- [ ] Add Users Group tab to TelegramPage and wire up components
- [ ] Add view model methods for user groups data operations
- [ ] Add handlers for Users Group tab interactions and sync groups
- [ ] Add translations for new UI elements in en.json and km.json