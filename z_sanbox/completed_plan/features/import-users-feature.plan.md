<!-- 6292ab01-60bb-42ae-af70-0685d535ae44 6e82d75c-1602-46ad-b16f-49e2cd94d56d -->
# Import Users Feature Implementation Plan

## Overview

Add functionality to import all members from a Telegram group with real-time progress tracking, configurable fetch limits, and visual feedback via pie chart.

## Components to Create/Modify

### 1. UI Components

#### 1.1 Modify Users Tab (`ui/pages/telegram/components/users_tab.py`)

- Add "Import Users" button in top right (next to refresh and export menu)
- Button should be disabled when no group is selected
- Connect button to open import dialog

#### 1.2 Create Import Users Dialog (`ui/dialogs/import_users_dialog.py`)

- Settings section:
  - Rate limit slider (delay between fetches): 0-10 seconds, default from app settings
  - Fetch limit input (max number of members): optional, no limit if empty
  - Time limit input (minutes): default 30, optional
  - "Skip Deleted" checkbox: default checked
- Progress section:
  - Real-time pie chart showing:
    - Total Fetched (green)
    - Skipped - Already Exist (yellow)
    - Skipped - Deleted (orange)
    - Actual Total (blue) - sum of all categories
  - Progress text showing current status
  - Stop button (visible during fetch)
- Use `page.open(dialog)` pattern for opening

#### 1.3 Create Pie Chart Component (`ui/components/pie_chart.py`)

- Custom pie chart using Flet's Container/Stack with colored segments
- Update method to refresh chart data in real-time
- Display legend with counts and percentages

### 2. Service Layer

#### 2.1 Create Member Fetcher Service (`services/telegram/member_fetcher.py`)

- `fetch_members()` method:
  - Accepts: group_id, rate_limit, fetch_limit, time_limit, skip_deleted
  - Uses Telethon's `iter_participants()` with `aggressive=True` for large groups
  - Implements rate limiting with delays
  - Checks time limit and stops if exceeded
  - Checks fetch limit and stops if reached
  - Skips existing users if skip_deleted is True
  - Skips deleted users if skip_deleted is True
  - Returns progress via callbacks:
    - `on_progress(fetched, skipped_exist, skipped_deleted, total)`
    - `on_member(user, status)` - status: 'fetched', 'skipped_exist', 'skipped_deleted'
  - Supports cancellation via flag
- Handle Telethon errors (FloodWaitError, etc.)
- Use temporary client pattern (connect on demand)

#### 2.2 Update User Processor (`services/telegram/user_processor.py`)

- Add method `process_member()` similar to `process_user()` but:
  - Check if user exists before processing
  - Return status: 'fetched', 'skipped_exist', 'skipped_deleted'
  - Handle skip_deleted flag

### 3. Database Layer

#### 3.1 Update User Manager (`database/managers/user_manager.py`)

- Ensure `save_user()` handles upsert correctly (already exists)
- Add method `user_exists(user_id)` to check existence
- Add method `is_user_deleted(user_id)` to check deletion status

### 4. View Model

#### 4.1 Create Import Users View Model (`ui/pages/telegram/view_models/import_users_view_model.py`)

- Track state:
  - `is_importing: bool`
  - `fetched_count: int`
  - `skipped_exist_count: int`
  - `skipped_deleted_count: int`
  - `total_count: int`
  - `current_status: str`
- Reset method
- Update methods for each metric

### 5. Handlers

#### 5.1 Update Telegram Handlers (`ui/pages/telegram/handlers.py`)

- Add `handle_import_users()` method:
  - Get selected group from users_tab
  - Validate group is selected
  - Open import dialog
  - Handle dialog callbacks

#### 5.2 Create Import Users Handler (`ui/pages/telegram/handlers/import_users_handler.py`)

- Handle async import process
- Manage cancellation
- Update view model and UI in real-time
- Handle errors and show user-friendly messages

## Implementation Details

### Telethon Member Fetching

```python
# Use iter_participants with aggressive mode
async for user in client.iter_participants(group_entity, aggressive=True):
    # Process user
    # Check limits
    # Apply rate limiting
    # Check cancellation
```

### Pie Chart Implementation

- Use Flet's Stack with positioned Containers
- Calculate angles based on percentages
- Use Container with border_radius for circular segments
- Update on each progress callback

### Real-time Updates

- Use `page.update()` in progress callbacks
- Update pie chart data structure
- Update text labels with counts

### Cancellation

- Use `asyncio.Task.cancel()` pattern
- Set cancellation flag in view model
- Check flag in fetch loop

### Error Handling

- Handle FloodWaitError with automatic retry
- Handle network errors with retry logic
- Show user-friendly error messages
- Log errors for debugging

## Additional Features (Suggestions)

1. **Export Imported Members**: Button to export newly imported members to Excel/PDF
2. **Filter by Import Date**: Add filter in users table to show only recently imported members
3. **Import History**: Track import sessions with timestamps and statistics
4. **Resume Import**: If import stops, allow resuming from last position
5. **Batch Size Control**: Allow user to set batch size for processing
6. **Profile Photo Download**: Option to download profile photos during import
7. **Duplicate Detection**: Show warning if user already exists with different data

## File Structure

```
ui/
  dialogs/
    import_users_dialog.py (NEW)
  components/
    pie_chart.py (NEW)
  pages/
    telegram/
      components/
        users_tab.py (MODIFY)
      handlers/
        import_users_handler.py (NEW)
      view_models/
        import_users_view_model.py (NEW)

services/
  telegram/
    member_fetcher.py (NEW)

database/
  managers/
    user_manager.py (MODIFY - add helper methods if needed)
```

## Testing Considerations

- Test with small groups (< 100 members)
- Test with large groups (> 10,000 members)
- Test cancellation mid-process
- Test time limit expiration
- Test fetch limit reached
- Test skip_deleted flag behavior
- Test rate limiting
- Test error recovery (FloodWaitError, network errors)
- Test UI responsiveness during import

## Localization

- Add translation keys for:
  - "Import Users"
  - "Rate Limit (seconds)"
  - "Fetch Limit"
  - "Time Limit (minutes)"
  - "Skip Deleted"
  - "Total Fetched"
  - "Skipped - Already Exist"
  - "Skipped - Deleted"
  - "Actual Total"
  - "Importing members..."
  - "Import completed"
  - "Import stopped"