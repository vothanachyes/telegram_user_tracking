<!-- 687891cd-4137-48a3-9588-86ac8e8d5806 0a56819e-3c0f-4835-8151-927f27edea2c -->
# Group Management and Fetching Warnings Implementation Plan

## Overview

This plan implements:

1. **New Groups Page** - Sidebar navigation page for managing Telegram groups with listing, details view, and add functionality
2. **Fetch History Tracking** - Track multiple fetch operations per group with date ranges
3. **Group Photo Support** - Download and sync group profile photos
4. **Add Group Dialog** - Support multiple input formats (link, invite link, ID, username) with account selection and license warnings
5. **Fetching Page Warnings** - License limit warnings and Telegram rate limit warning dialog (shown every 10 minutes)

---

## Phase 1: Database Schema Updates

### 1.1 Add Group Photo Column

**File**: `database/models/schema.py` (~5 lines added)

Add `group_photo_path TEXT` column to `telegram_groups` table:

```sql
ALTER TABLE telegram_groups ADD COLUMN group_photo_path TEXT;
```

**File**: `database/models/telegram.py` (~2 lines added)

Add `group_photo_path: Optional[str] = None` to `TelegramGroup` dataclass.

**File**: `database/managers/group_manager.py` (~10 lines modified)

Update `save_group()` and `get_all_groups()` to include `group_photo_path`.

### 1.2 Create Fetch History Table

**File**: `database/models/schema.py` (~20 lines added)

Create new table `group_fetch_history`:

```sql
CREATE TABLE IF NOT EXISTS group_fetch_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    group_id INTEGER NOT NULL,
    start_date TIMESTAMP NOT NULL,
    end_date TIMESTAMP NOT NULL,
    message_count INTEGER DEFAULT 0,
    account_phone_number TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (group_id) REFERENCES telegram_groups(group_id)
);

CREATE INDEX IF NOT EXISTS idx_fetch_history_group_id ON group_fetch_history(group_id);
CREATE INDEX IF NOT EXISTS idx_fetch_history_dates ON group_fetch_history(start_date, end_date);
```

**File**: `database/models/telegram.py` (~10 lines added)

Add new dataclass:

```python
@dataclass
class GroupFetchHistory:
    id: Optional[int] = None
    group_id: int = 0
    start_date: datetime = None
    end_date: datetime = None
    message_count: int = 0
    account_phone_number: Optional[str] = None
    created_at: Optional[datetime] = None
```

### 1.3 Add Warning Dialog Timestamp Storage

**File**: `database/models/schema.py` (~5 lines added)

Add `rate_limit_warning_last_seen TIMESTAMP` to `app_settings` table:

```sql
ALTER TABLE app_settings ADD COLUMN rate_limit_warning_last_seen TIMESTAMP;
```

**File**: `database/models/app_settings.py` (~2 lines added)

Add `rate_limit_warning_last_seen: Optional[datetime] = None` to `AppSettings` dataclass.

**File**: `database/managers/settings_manager.py` (~5 lines modified)

Update `get_settings()` and `update_settings()` to include `rate_limit_warning_last_seen`.

---

## Phase 2: Group Utilities and Services

### 2.1 Group Input Parser Utility

**File**: `utils/group_parser.py` (~150 lines, new file)

Create utility to parse different group input formats:

- `parse_group_input(input_str: str) -> Tuple[Optional[int], Optional[str], Optional[str]]`
  - Returns: (group_id, username, error_message)
  - Supports:
    - Group links: `https://t.me/groupname` or `https://t.me/c/1234567890/123`
    - Invite links: `https://t.me/joinchat/...` or `https://t.me/+...`
    - Group ID: `1234567890` or `-1001234567890`
    - Raw group ID: `-1001234567890`
    - Username: `@groupname` or `groupname`

### 2.2 Fetch History Manager

**File**: `database/managers/fetch_history_manager.py` (~100 lines, new file)

Create manager for fetch history operations:

- `save_fetch_history(history: GroupFetchHistory) -> Optional[int]`
- `get_fetch_history_by_group(group_id: int) -> List[GroupFetchHistory]`
- `get_all_fetch_history() -> List[GroupFetchHistory]`

### 2.3 Group Photo Downloader

**File**: `services/telegram/group_photo_downloader.py` (~80 lines, new file)

Create service to download group photos:

- `async download_group_photo(client, group_id: int, group_username: Optional[str]) -> Optional[str]`
  - Downloads group photo from Telegram
  - Saves to `downloads/groups/{group_id}/photo.jpg`
  - Returns file path or None

**File**: `services/telegram/group_manager.py` (~20 lines added)

Add photo download integration to `fetch_group_info()` method.

---

## Phase 3: Groups Page Implementation

### 3.1 Create Groups Page

**File**: `ui/pages/groups/page.py` (~200 lines, new file)

Main page orchestration:

- Group listing with cards/list view
- Add group button
- Click group to show details
- Refresh/sync button

**File**: `ui/pages/groups/view_model.py` (~100 lines, new file)

View model for groups page state:

- Groups list
- Selected group
- Loading states

**File**: `ui/pages/groups/components.py` (~200 lines, new file)

UI components:

- Group list/cards
- Group detail view
- Empty state

**File**: `ui/pages/groups/handlers.py` (~150 lines, new file)

Event handlers:

- Add group button click
- Group click handler
- Sync/refresh group details
- Fetch history display

### 3.2 Add Groups Page to Navigation

**File**: `ui/components/sidebar.py` (~5 lines modified)

Add groups button to sidebar:

```python
self._create_nav_button("groups", ft.Icons.GROUP, theme_manager.t("groups")),
```

**File**: `ui/navigation/page_factory.py` (~10 lines modified)

Add groups page creation:

- Import `GroupsPage`
- Add `elif page_id == "groups":` case
- Create `_create_groups_page()` method

**File**: `ui/pages/__init__.py` (~2 lines added)

Export `GroupsPage`.

### 3.3 Group Detail Dialog

**File**: `ui/dialogs/group_detail_dialog.py` (~250 lines, new file)

Dialog showing group details:

- Group photo display
- Group information (name, username, ID)
- Fetch history table/list (date ranges, message counts)
- Sync/refresh button to refetch from Telegram
- No delete button (future feature)

---

## Phase 4: Add Group Dialog

### 4.1 Create Add Group Dialog

**File**: `ui/dialogs/add_group_dialog.py` (~400 lines, new file)

Dialog for adding new groups:

- **Input field** supporting multiple formats (link, invite link, ID, username)
- **Account selector** component (reuse `AccountSelector`)
- **License warning** - Show current/max groups from license
- **Preview section** - Show group details after fetching (name, username, photo, member count if available)
- **Confirmation dialog** - Final confirmation before adding
- **Error handling** - Show red info for permission denied groups

**Features**:

- Parse input using `group_parser.py`
- Fetch group info using selected account
- Show preview with group photo
- Check license limits before allowing add
- Handle permission errors (show red info, don't allow add)

### 4.2 Integrate Add Group Dialog

**File**: `ui/pages/groups/handlers.py` (~20 lines added)

Add handler to open add group dialog from groups page.

---

## Phase 5: Fetching Page Warnings

### 5.1 License Warning on Fetching Page

**File**: `ui/pages/fetch_data/page.py` (~30 lines added)

Add warning banner/alert:

- Show if new group will be auto-saved during fetch
- Show current/max groups from license
- Display before start fetch button

**File**: `ui/pages/fetch_data/handlers.py` (~20 lines added)

Check if selected group is new (not in database) and show warning.

### 5.2 Rate Limit Warning Dialog

**File**: `ui/dialogs/rate_limit_warning_dialog.py` (~100 lines, new file)

Create warning dialog:

- Warning message about Telegram rate limits
- Advice to use non-official accounts
- Single "Confirm" button
- Store last seen timestamp in app_settings

**File**: `ui/pages/fetch_data/handlers.py` (~50 lines added)

Add logic to show warning dialog:

- Check `rate_limit_warning_last_seen` from settings
- Show if > 10 minutes since last seen
- Update timestamp when user confirms
- Show before starting fetch operation

**File**: `database/managers/settings_manager.py` (~10 lines added)

Add methods:

- `get_rate_limit_warning_last_seen() -> Optional[datetime]`
- `update_rate_limit_warning_last_seen(timestamp: datetime) -> bool`

---

## Phase 6: Fetch History Integration

### 6.1 Track Fetch Operations

**File**: `services/telegram/message_fetcher.py` (~20 lines added)

After successful fetch, save fetch history:

- Create `GroupFetchHistory` record
- Include start_date, end_date, message_count, account_phone_number

**File**: `database/managers/db_manager.py` (~10 lines added)

Add method to save fetch history (delegate to `FetchHistoryManager`).

### 6.2 Display Fetch History

**File**: `ui/dialogs/group_detail_dialog.py` (~50 lines added)

Add fetch history section:

- Table/list showing all fetch operations
- Columns: Date Range, Message Count, Account
- Sort by date (newest first)

---

## Phase 7: Localization

### 7.1 Add Translation Keys

**File**: `locales/en.json` (~30 lines added)

Add keys:

- `groups`: "Groups"
- `add_group`: "Add Group"
- `group_details`: "Group Details"
- `group_photo`: "Group Photo"
- `fetch_history`: "Fetch History"
- `date_range`: "Date Range"
- `sync_group`: "Sync Group"
- `group_added_successfully`: "Group added successfully"
- `rate_limit_warning_title`: "Telegram Rate Limit Warning"
- `rate_limit_warning_message`: "Warning: Quickly fetching data from Telegram or excessive use may result in your account being blocked or disabled by Telegram. We recommend using a non-official account to avoid unexpected complaints from Telegram."
- `new_group_warning`: "This group will be automatically saved when you start fetching."
- `license_group_limit_warning`: "You have {current}/{max} groups. Your license allows up to {max} groups."

**File**: `locales/km.json` (~30 lines added)

Add Khmer translations for all new keys.

---

## Implementation Notes

1. **File Size Compliance**: All new files stay under line limits:

   - Page files: < 250 lines
   - Component files: < 200 lines
   - Handler files: < 150 lines
   - Service files: < 300 lines

2. **Dialog Pattern**: Use `page.open(dialog)` for all dialogs (as per repo rules).

3. **Error Handling**: All Telegram operations wrapped in try-except with user-friendly error messages.

4. **Async Operations**: All Telegram API calls use async/await properly.

5. **Database Migrations**: Schema changes use ALTER TABLE (SQLite compatible).

6. **Photo Storage**: Group photos stored in `downloads/groups/{group_id}/photo.jpg`.

7. **Warning Dialog Timing**: 10-minute interval configurable (hardcoded for now, can be moved to settings later).

---

## Testing Checklist

- [ ] Groups page displays all groups
- [ ] Add group dialog accepts all input formats
- [ ] License warnings show correctly
- [ ] Group photos download and display
- [ ] Fetch history tracks correctly
- [ ] Rate limit warning shows every 10 minutes
- [ ] Permission denied groups show red info
- [ ] Group detail dialog shows all information
- [ ] Sync group updates group details
- [ ] New group warning shows on fetching page

### To-dos

- [ ] Update database schema: add group_photo_path column, create group_fetch_history table, add rate_limit_warning_last_seen to app_settings
- [ ] Create group input parser utility and fetch history manager
- [ ] Create group photo downloader service and integrate with group manager
- [ ] Create Groups page with listing, detail view, and handlers
- [ ] Add Groups button to sidebar and register page in PageFactory
- [ ] Create Add Group dialog with input parsing, account selection, license warnings, and preview
- [ ] Create Group Detail dialog showing group info, photo, and fetch history
- [ ] Integrate fetch history tracking into message fetcher
- [ ] Add license warnings and rate limit warning dialog to fetching page
- [ ] Add all translation keys for new features in English and Khmer