<!-- d39d7aab-1bf2-495a-92d3-20ea81bad376 174f1ee9-6517-4219-a3f7-e557fc1f4767 -->
# Table Enhancement Plan

## Overview

Enhance the Message and User tables in the Telegram page with improved alignment, clickable links, group filtering, and filter management.

## Changes Required

### 1. DataTable Component Enhancements (`ui/components/data_table.py`)

- Add support for column-specific alignment (center/left)
- Add support for clickable cells (for links)
- Add clear filter button that appears when filters are active
- Center-align all table headers
- Support custom cell renderers (for icons/links)

### 2. Helper Functions (`utils/helpers.py`)

- Add `get_telegram_user_link(username: Optional[str]) -> Optional[str]` function to generate user profile links (format: `https://t.me/{username}`)

### 3. Database Manager (`database/db_manager.py`)

- Add `get_users_by_group(group_id: int, include_deleted: bool = False) -> List[TelegramUser]` method to fetch users from a specific group by querying messages

### 4. Telegram Page - Messages Tab (`ui/pages/telegram_page.py`)

- Modify `_create_messages_table()` to:
- Add "Link" column at the end with Telegram icon
- Center-align all columns except "Message"
- Pass message_link data for each row
- Modify `_refresh_messages()` to include message_link in row data
- Add clear filter button next to search field (show when group/date filters are active)
- Ensure group selection is required (show empty state if no group selected)

### 5. Telegram Page - Users Tab (`ui/pages/telegram_page.py`)

- Add group selector dropdown (similar to messages tab)
- Modify `_create_users_tab()` to include group selector and clear button
- Modify `_create_users_table()` to:
- Center-align all columns except "Bio"
- Make "Username" and "Full Name" clickable (open Telegram profile)
- Filter users by selected group
- Add `_on_users_group_selected()` handler
- Modify `_refresh_users()` to filter by selected group
- Ensure group selection is required (show empty state if no group selected)

## Implementation Details

### Message Table Columns

- Current: ["No", "User", "Phone", "Message", "Date", "Media", "Type"]
- New: ["No", "User", "Phone", "Message", "Date", "Media", "Type", "Link"]
- Alignment: All center except "Message" (left)
- Link column: Telegram icon button that opens message_link

### User Table Columns

- Current: ["No", "Username", "Full Name", "Phone", "Bio"]
- Alignment: All center except "Bio" (left)
- Clickable: "Username" and "Full Name" open `https://t.me/{username}` (if username exists)

### Clear Filter Button

- Position: Before search button (left side)
- Visibility: Show when any filter is active (group selected, date range set, or search query)
- Action: Clear all filters and reset to default state
clear
### Group Selection Requirement

- Both tables: Show empty state message if no group is selected
- Default: No data shown until group is selected
- Users table: Filter users to only those who have sent messages in the selected group

### To-dos

- [ ] Add helper function get_telegram_user_link() in utils/helpers.py
- [ ] Add get_users_by_group() method in database/db_manager.py
- [ ] Enhance DataTable component to support column alignment, clickable cells, and clear filter button
- [ ] Update messages table: add Link column, center alignment, and clear filter button
- [ ] Update users table: add group selector, center alignment, clickable username/fullname, and clear filter button