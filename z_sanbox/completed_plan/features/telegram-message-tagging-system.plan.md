<!-- 0a6c1a35-1150-4978-9c3a-6e2643535b12 606387a4-3655-4bdb-9b42-009894266748 -->
# Telegram Message Tagging System Implementation

## Overview
Implement a tagging system that extracts tags (prefixed with #) from message content, stores them in a normalized table for efficient querying, and provides filtering and autocomplete functionality in the UI.

## Database Schema Changes

### 1. Create Message Tags Table
**File**: `database/models/schema.py`

Add to `CREATE_TABLES_SQL`:
```sql
-- Message Tags Table
CREATE TABLE IF NOT EXISTS message_tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    message_id INTEGER NOT NULL,
    group_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    tag TEXT NOT NULL,  -- Tag without # prefix (normalized lowercase)
    date_sent TIMESTAMP NOT NULL,  -- From message.date_sent for analytics
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(message_id, group_id, tag),
    FOREIGN KEY (message_id, group_id) REFERENCES messages(message_id, group_id),
    FOREIGN KEY (user_id) REFERENCES telegram_users(user_id)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_message_tags_tag ON message_tags(tag);
CREATE INDEX IF NOT EXISTS idx_message_tags_group_id ON message_tags(group_id);
CREATE INDEX IF NOT EXISTS idx_message_tags_user_id ON message_tags(user_id);
CREATE INDEX IF NOT EXISTS idx_message_tags_date_sent ON message_tags(date_sent);
CREATE INDEX IF NOT EXISTS idx_message_tags_group_tag ON message_tags(group_id, tag);
CREATE INDEX IF NOT EXISTS idx_message_tags_user_group_tag ON message_tags(user_id, group_id, tag);
```

### 2. Add Migration Logic
**File**: `database/managers/base.py`

Add to `_run_migrations()` method:
- Check if `message_tags` table exists
- Create table and indexes if missing
- Handle migration for existing databases

## Data Models

### 3. Create MessageTag Model
**File**: `database/models/message.py`

Add `MessageTag` dataclass:
```python
@dataclass
class MessageTag:
    """Message tag model."""
    id: Optional[int] = None
    message_id: int = 0
    group_id: int = 0
    user_id: int = 0
    tag: str = ""  # Normalized tag without #
    date_sent: Optional[datetime] = None
    created_at: Optional[datetime] = None
```

## Tag Extraction Logic

### 4. Create Tag Extractor Utility
**File**: `utils/tag_extractor.py` (~100 lines)

Create utility to extract tags from text:
- Regex pattern: `#[\w\u4e00-\u9fff]+` (supports alphanumeric, underscore, and Unicode characters)
- Normalize tags: lowercase, strip whitespace
- Extract from both `content` and `caption` fields
- Return list of unique normalized tags (without # prefix)

### 5. Update Message Processor
**File**: `services/telegram/message_processor.py`

In `process_message()` method:
- After extracting content and caption, extract tags using `TagExtractor`
- Store tags in message object (optional field for now, tags will be saved separately)
- Keep original content unchanged (tags remain in content for display)

## Database Operations

### 6. Create Tag Manager
**File**: `database/managers/tag_manager.py` (~250 lines)

Implement `TagManager` class with methods:
- `save_tags(message_id, group_id, user_id, tags, date_sent)` - Save tags for a message
- `get_tags_by_message(message_id, group_id)` - Get all tags for a message
- `get_messages_by_tag(tag, group_id, limit, offset)` - Get messages containing a tag
- `get_tag_suggestions(prefix, group_id, limit=10)` - Get tag suggestions for autocomplete
- `get_tag_counts_by_group(group_id)` - Get tag usage counts per group
- `get_tag_counts_by_user(group_id, user_id)` - Get tag usage counts per user
- `delete_tags_for_message(message_id, group_id)` - Remove tags when message is deleted

### 7. Update Message Manager
**File**: `database/managers/message_manager.py`

In `save_message()` method:
- After saving message, extract tags and save via `TagManager`
- In `soft_delete_message()`: also delete associated tags
- In `get_messages()`: add optional `tags` parameter to filter by tags

Add new method:
- `get_messages_by_tags(tags: List[str], group_id, ...)` - Filter messages by multiple tags

## UI Components

### 8. Create Tag Autocomplete Component
**File**: `ui/components/tag_autocomplete.py` (~200 lines)

Create component that:
- Detects `#` prefix in search input
- Shows dropdown with tag suggestions as user types
- Filters suggestions based on current group context
- Handles tag selection and search query updates
- Integrates with existing `TableFiltering` component

### 9. Update Search/Filter Component
**File**: `ui/components/data_table/filtering.py`

Enhance `TableFiltering` class:
- Add tag autocomplete integration
- Detect `#` prefix in search query
- Show tag suggestions dropdown
- Handle tag-based filtering separately from text search
- Update `filter_rows()` to support tag filtering when query starts with `#`

### 10. Update Messages Tab
**File**: `ui/pages/telegram/components/messages_tab.py`

Integrate tag autocomplete:
- Pass group context to search field
- Connect tag suggestions to message filtering
- Update message refresh to include tag filtering

### 11. Update View Models
**File**: `ui/pages/telegram/page.py` or relevant view model files

Add tag filtering support:
- Update message fetching to accept tag filters
- Connect UI tag selection to database queries
- Handle tag-based message filtering

## Integration Points

### 12. Update Message Saving Flow
**Files**: 
- `services/telegram/telegram_service.py` or message saving service
- `database/managers/message_manager.py`

Ensure tags are extracted and saved when messages are processed:
- Extract tags during message processing
- Save tags after message is successfully saved
- Handle errors gracefully (log but don't fail message save)

### 13. Add Tag Display (Optional Enhancement)
**File**: `ui/components/message_tag_display.py` (~100 lines)

Create component to display tags in message list:
- Show tags as chips/badges
- Make tags clickable to filter by tag
- Style tags with # prefix for visual consistency

## Future Analytics Foundation

### 14. Create Tag Analytics Service (Foundation)
**File**: `services/tag_analytics_service.py` (~150 lines)

Create service for future analytics:
- `get_top_tags_by_group(group_id, limit)` - Most used tags
- `get_tag_usage_by_user(group_id, tag)` - Which users use a tag
- `get_tag_usage_by_date(group_id, tag, start_date, end_date)` - Tag usage over time
- `get_user_tag_stats(group_id, user_id)` - User's tag usage statistics

## Testing Considerations

- Test tag extraction with various formats (#tag, #TAG, #tag_name, #tag123)
- Test tag normalization (case-insensitive, whitespace handling)
- Test tag filtering performance with large datasets
- Test autocomplete with many tags
- Test tag saving/retrieval with encrypted message content
- Test tag deletion when messages are deleted

## Migration Strategy

1. Add `message_tags` table via migration in `BaseDatabaseManager._run_migrations()`
2. For existing messages: optionally backfill tags (can be done later or on-demand)
3. New messages: automatically extract and save tags going forward

## Files to Create

- `utils/tag_extractor.py` - Tag extraction utility
- `database/managers/tag_manager.py` - Tag database operations
- `ui/components/tag_autocomplete.py` - Tag autocomplete UI component
- `services/tag_analytics_service.py` - Analytics service (foundation)

## Files to Modify

- `database/models/schema.py` - Add message_tags table
- `database/models/message.py` - Add MessageTag model
- `database/managers/base.py` - Add migration for message_tags table
- `database/managers/message_manager.py` - Integrate tag saving and filtering
- `services/telegram/message_processor.py` - Extract tags from messages
- `ui/components/data_table/filtering.py` - Add tag autocomplete support
- `ui/pages/telegram/components/messages_tab.py` - Integrate tag filtering

## Implementation Order

1. Database schema and migration
2. Tag extraction utility
3. Tag manager (database operations)
4. Message processor integration
5. Message manager updates
6. UI autocomplete component
7. Search/filter integration
8. Testing and refinement

### To-dos

- [ ] Add message_tags table to database schema with indexes
- [ ] Add migration logic in BaseDatabaseManager to create message_tags table
- [ ] Create MessageTag dataclass in database/models/message.py
- [ ] Create tag extraction utility (utils/tag_extractor.py) to extract #tags from text
- [ ] Create TagManager class with save, query, and analytics methods
- [ ] Integrate tag extraction in MessageProcessor.process_message()
- [ ] Update MessageManager to save tags and add tag filtering to get_messages()
- [ ] Create tag autocomplete UI component with dropdown suggestions
- [ ] Enhance TableFiltering to detect # prefix and show tag autocomplete
- [ ] Integrate tag autocomplete into messages tab and connect to filtering
- [ ] Create TagAnalyticsService foundation for future analytics features