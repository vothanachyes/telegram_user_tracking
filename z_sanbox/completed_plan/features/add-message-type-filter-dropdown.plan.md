Original propmts:
In Telegram For message tab. 
i want to to add another filter dropdown, this drop down can quick filter by type:
- voice
- audio file
- photos
- videos
- files
- link
- tag  (Filter messag where has #)
- poll
- location
- @ (filter message that has mentioning other peoples)

<!-- a65d17b2-2b43-412d-9a4a-e741f8fd85d3 7f2e7de5-6a21-4089-8834-f818d3d8864b -->
# Add Message Type Filter Dropdown to Messages Tab

## Overview

Add a new filter dropdown in the Telegram messages tab that allows users to quickly filter messages by type: voice, audio file, photos, videos, files, link, tag, poll, location, and @ mentions.

## Implementation Steps

### 1. Update Database Manager (`database/managers/message_manager.py`)

- Add `message_type_filter` parameter to `get_messages()` method
- Handle special filter types:
- `"voice"` → `message_type = "voice"`
- `"audio"` → `message_type = "audio"`
- `"photos"` → `message_type = "photo"`
- `"videos"` → `message_type = "video"`
- `"files"` → `message_type = "document"`
- `"link"` → `has_link = 1`
- `"poll"` → `message_type = "poll"`
- `"location"` → `message_type = "location"`
- `"tag"` → EXISTS query on `message_tags` table
- `"mention"` → Filter messages with "@" in content (after decryption, in Python)

### 2. Update View Model (`ui/pages/telegram/view_model.py`)

- Add `message_type_filter` parameter to `get_messages()` method
- Pass the filter to `db_manager.get_messages()`

### 3. Update Filters Bar Component (`ui/pages/telegram/components/filters_bar.py`)

- Add optional `message_type_filter` parameter to constructor
- Add message type dropdown with options:
- "All Types" (default, None)
- "Voice"
- "Audio File"
- "Photos"
- "Videos"
- "Files"
- "Link"
- "Tag"
- "Poll"
- "Location"
- "@ Mention"
- Add `get_message_type_filter()` method
- Update `clear_filters()` to reset message type filter
- Add callback `on_message_type_change` parameter

### 4. Update Messages Tab Component (`ui/pages/telegram/components/messages_tab.py`)

- Pass `on_message_type_change` callback to `FiltersBarComponent`
- Update `refresh_messages()` to get message type filter from filters bar
- Pass `message_type_filter` to `view_model.get_messages()`
- Update `_has_filters()` to include message type filter
- Update `clear_filters()` to clear message type filter

### 5. Add Translations (`locales/en.json` and `locales/km.json`)

- Add translation keys:
- `"filter_by_type": "Filter by Type"`
- `"all_types": "All Types"`
- `"voice": "Voice"`
- `"audio_file": "Audio File"`
- `"photos": "Photos"`
- `"videos": "Videos"`
- `"files": "Files"`
- `"link": "Link"`
- `"tag": "Tag"`
- `"poll": "Poll"`
- `"location": "Location"`
- `"mention": "@ Mention"`

### 6. Handle Special Cases

#### For "@ Mention" filter:

- Since content is encrypted, filter after decryption in Python
- In `MessageManager.get_messages()`, after fetching and decrypting messages, filter out messages that don't contain "@" in content or caption
- This is less efficient but works without database migration

#### For "Tag" filter:

- Use EXISTS subquery: `EXISTS (SELECT 1 FROM message_tags WHERE message_tags.message_id = messages.message_id AND message_tags.group_id = messages.group_id)`
- This efficiently filters messages that have at least one tag

#### For "Link" filter:

- Use existing `has_link` boolean field: `has_link = 1`

## Files to Modify

1. `database/managers/message_manager.py` - Add message_type_filter parameter and filtering logic
2. `ui/pages/telegram/view_model.py` - Pass message_type_filter to db_manager
3. `ui/pages/telegram/components/filters_bar.py` - Add message type dropdown
4. `ui/pages/telegram/components/messages_tab.py` - Integrate message type filter
5. `locales/en.json` - Add English translations
6. `locales/km.json` - Add Khmer translations

## Notes

- The "@ Mention" filter requires filtering after decryption, which may be slower for large datasets. Consider adding a `has_mention` boolean field in a future optimization.
- The "Tag" filter uses an efficient EXISTS query on the message_tags table.
- All other filters use direct SQL conditions on indexed fields for optimal performance.
- The dropdown should be placed in the filters bar row, after the group dropdown.

### To-dos

- [ ] Update MessageManager.get_messages() to accept message_type_filter parameter and implement filtering logic for all types including special cases (link, tag, mention)
- [ ] Update TelegramViewModel.get_messages() to accept and pass message_type_filter parameter
- [ ] Add message type dropdown to FiltersBarComponent with all filter options and callback handling
- [ ] Integrate message type filter in MessagesTabComponent, update refresh_messages() and filter state checking
- [ ] Add translation keys for all message type filter options in en.json and km.json