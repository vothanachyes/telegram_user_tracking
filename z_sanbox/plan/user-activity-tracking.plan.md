<!-- 628d2264-4809-4792-8ea9-f495316c12f9 3b4d7111-0333-41f3-af95-a0b77dd7ff6e -->
# User Activity Tracking Implementation Plan

## Overview
Extend the application to track comprehensive user activity metrics including reactions, detailed message type breakdowns (stickers, videos, links, photos, documents, audio, text), and aggregate statistics per user per group.

## Database Schema Changes

### 1. Create Reactions Table
- **File**: `database/models.py`
- Add `Reaction` dataclass and `reactions` table schema
- Fields: 
  - `id`: PRIMARY KEY
  - `message_id`: INTEGER (Telegram message ID that was reacted to)
  - `group_id`: INTEGER (group where the message exists)
  - `user_id`: INTEGER (user who reacted)
  - `emoji`: TEXT (emoji used for reaction)
  - `message_link`: TEXT (Telegram link to the original message - for easy navigation)
  - `reacted_at`: TIMESTAMP (when reaction was made, use message date_sent as proxy)
- Foreign keys: `(message_id, group_id)` references `messages(message_id, group_id)`, `user_id` references `telegram_users(user_id)`
- Index on `(user_id, group_id)` for fast aggregation queries
- Index on `message_id` for message-level queries
- Index on `message_link` for quick lookups
- UNIQUE constraint on `(message_id, group_id, user_id, emoji)` to prevent duplicate reactions

### 2. Extend Messages Table
- **File**: `database/models.py`
- Add new fields to `Message` model:
  - `message_type`: TEXT field (text, sticker, video, photo, document, audio, voice, video_note, location, contact, link, poll, etc.)
  - `has_sticker`: BOOLEAN
  - `has_link`: BOOLEAN (detect URLs in content)
  - `sticker_emoji`: TEXT (if sticker, store emoji)
- Update SQL schema in `CREATE_TABLES_SQL` to add these columns with migration support

### 3. Create User Activity Stats View/Table (Optional)
- Consider creating a materialized view or summary table for faster queries
- Fields: `user_id`, `group_id`, `total_messages`, `total_reactions`, `total_stickers`, `total_videos`, `total_photos`, `total_links`, `total_documents`, `total_audio`, `last_activity_date`
- Update on message/reaction insert/update

## Service Layer Changes

### 4. Update Telegram Service - Message Processing
- **File**: `services/telegram_service.py`
- Enhance `_process_message()` method to:
  - Detect message type: check `telegram_msg.sticker`, `telegram_msg.animation`, `telegram_msg.location`, `telegram_msg.contact`, `telegram_msg.poll`, etc.
  - Detect links in text content using regex pattern
  - Store sticker emoji if present
  - Set appropriate flags (has_sticker, has_link, message_type)

### 5. Add Reaction Processing
- **File**: `services/telegram_service.py`
- Create `_process_reactions()` method:
  - Check if `telegram_msg.reactions` exists
  - For each reaction, use `client.get_reactions()` to get list of users who reacted
  - Save each reaction to database with user_id who reacted
  - Handle rate limiting (reactions require additional API calls)
  - Make this optional/configurable due to API overhead

### 6. Update Fetch Messages Flow
- **File**: `services/telegram_service.py`
- In `fetch_messages()`, after processing message:
  - Call `_process_reactions()` if enabled in settings
  - Add delay between reaction API calls to avoid rate limits
  - Add progress callback for reaction fetching

## Database Manager Changes

### 7. Add Reaction CRUD Operations
- **File**: `database/db_manager.py`
- Methods:
  - `save_reaction(reaction: Reaction) -> Optional[int]`
  - `get_reactions_by_message(message_id: int, group_id: int) -> List[Reaction]`
  - `get_reactions_by_user(user_id: int, group_id: Optional[int] = None) -> List[Reaction]`
  - `delete_reaction(reaction_id: int) -> bool`

### 8. Add User Activity Statistics Queries
- **File**: `database/db_manager.py`
- Method: `get_user_activity_stats(user_id: int, group_id: Optional[int] = None, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> Dict[str, Any]`
- Returns dictionary with:
  - `total_messages`: int
  - `total_reactions`: int (reactions given by user)
  - `total_stickers`: int
  - `total_videos`: int
  - `total_photos`: int
  - `total_links`: int
  - `total_documents`: int
  - `total_audio`: int
  - `total_text_messages`: int
  - `first_activity_date`: Optional[datetime]
  - `last_activity_date`: Optional[datetime]
  - `messages_by_group`: Dict[group_id, count] (if group_id not specified)

### 9. Add Message Type Breakdown Queries
- **File**: `database/db_manager.py`
- Method: `get_message_type_breakdown(user_id: int, group_id: Optional[int] = None) -> Dict[str, int]`
- Returns count of each message type for the user

### 10. Database Migration Support
- **File**: `database/db_manager.py`
- Add migration method to handle schema updates:
  - Check if new columns exist, add if missing
  - Create reactions table if not exists
  - Add indexes
  - Handle existing data (set defaults for new fields)

## Settings & Configuration

### 11. Add Settings for Reaction Tracking
- **File**: `config/settings.py` and `database/models.py`
- Add to `AppSettings`:
  - `track_reactions`: BOOLEAN (default: True)
  - `reaction_fetch_delay`: REAL (delay between reaction API calls, default: 0.5 seconds)

## UI Components (Future Enhancement)

### 12. User Activity Display
- Note: Separate plan exists for user detail page (`each_user_dashboard_raw.plan.md`)
- This plan focuses on data collection; UI will consume the statistics via `get_user_activity_stats()`

## Implementation Order

1. **Phase 1: Database Schema** (Steps 1-3)
   - Create reactions table
   - Extend messages table
   - Add migration support

2. **Phase 2: Data Collection** (Steps 4-6)
   - Update message processing
   - Add reaction processing
   - Integrate into fetch flow

3. **Phase 3: Data Access** (Steps 7-10)
   - Add database manager methods
   - Add statistics queries
   - Test with sample data

4. **Phase 4: Configuration** (Step 11)
   - Add settings for reaction tracking
   - Make it configurable

## Technical Considerations

- **Rate Limiting**: Reaction fetching requires additional API calls. Implement delays and make it optional.
- **Performance**: Consider batch processing reactions or making it a background task.
- **Backward Compatibility**: Migration must handle existing messages (set defaults for new fields).
- **Data Accuracy**: Link detection should use robust regex pattern for URLs.
- **Error Handling**: Gracefully handle cases where reaction data is unavailable (privacy settings, deleted messages).

## Testing Strategy

- Test with groups that have reactions enabled
- Test with various message types (sticker, video, link, etc.)
- Test aggregation queries with multiple users and groups
- Test migration on existing databases
- Verify performance with large datasets