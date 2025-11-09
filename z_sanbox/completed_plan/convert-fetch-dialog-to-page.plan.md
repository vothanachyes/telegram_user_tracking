<!-- e180ec70-55f1-4053-b396-40be3b7bc2db 0db1e506-fcee-45a3-87f3-a2babd05101d -->
# Convert Fetch Data Dialog to Full Page

## Overview

Transform `ui/dialogs/fetch_data_dialog.py` into a full page (`ui/pages/fetch_data_page.py`) with animated message cards, real-time fetch progress, error handling, and post-fetch summary.

## Key Features

### 1. Page Structure

- Create `ui/pages/fetch_data_page.py` following the pattern of other pages (like `TelegramPage`)
- Extends `ft.Container` with `set_page()` method
- Add to `ui/pages/__init__.py` and `ui/navigation/page_factory.py`
- Update `ui/app.py` to navigate to page instead of opening dialog

### 2. Animated Message Cards

- **Three-card carousel layout**: Left (saved), Middle (currently processing - larger, centered), Right (next to process)
- **Card content**: Sender profile (name, username, avatar if available), datetime, message preview/content, media indicators
- **Animation sequence**:
  - New message appears on right
  - Current message (middle) slides left while shrinking height
  - Middle card fades out (opacity 0) and is removed
  - Right card moves to center and expands
  - Previous left card is removed
- Use Flet animations: `ft.Animation`, `ft.AnimatedSwitcher`, or manual transitions with `Container` transforms

### 3. Message Count Estimate

- Before fetch starts, show estimated message count
- Option A: Quick scan using `get_chat_history()` with date filtering (may be slow)
- Option B: Show "Calculating..." and update during fetch
- Display in header section: "Estimated messages: X" or "Messages in range: X"

### 4. Error Handling

- When error occurs during message processing:
  - Display error message in card (red text/icon)
  - Sleep for 1.5 seconds (`await asyncio.sleep(1.5)`)
  - Animate card out and continue to next message
- Log errors but don't stop fetch process

### 5. Sender Profile Display

- Show sender info during fetch (not saved, just display):
  - Profile picture (if available from Pyrogram user object)
  - Full name
  - Username (@username)
  - Phone number (if available)
- Display in message card similar to `MessageDetailDialog` sender section

### 6. Post-Fetch Summary Table

- After all messages fetched, show temporary summary table
- Columns: User Name, Messages Sent, Reactions Given (if tracked), Media Shared
- Group by user_id, aggregate counts
- Use `ft.DataTable` or custom table component
- Display below animated cards section

### 7. Finish Button

- After fetch completes and summary is shown
- Button: "Finish" or "Done"
- On click: Reset page to initial state (clean all cards, hide summary, reset form)
- Navigate back or stay on page (user's choice)

## Implementation Details

### File Structure

```
ui/pages/fetch_data_page.py          # Main page (new)
ui/pages/fetch_data/
  ├── __init__.py
  ├── components.py                  # Message card component, summary table
  ├── view_model.py                  # Data logic, state management
  └── handlers.py                    # Event handlers, fetch logic
```

### Key Components

#### MessageCard Component

- Displays: sender profile, datetime, message content preview, error state
- Animation states: entering, active, exiting
- Handles opacity and transform animations

#### FetchViewModel

- Manages: current messages queue, fetch state, error tracking
- Tracks: processed count, error count, user summary data
- Provides: message callbacks, progress updates

#### FetchHandlers

- Handles: form validation, account/group validation, fetch execution
- Manages: message_callback integration, error handling with delays
- Updates: UI state, card animations, summary data

### Integration Points

1. **Page Factory** (`ui/navigation/page_factory.py`):

   - Add `_create_fetch_data_page()` method
   - Register "fetch_data" page ID

2. **Router** (`ui/navigation/router.py`):

   - No changes needed (uses existing navigation)

3. **App** (`ui/app.py`):

   - Change `_show_fetch_dialog()` to `router.navigate_to("fetch_data")`

4. **Sidebar** (`ui/components/sidebar.py`):

   - Update fetch button to navigate instead of callback

### Animation Implementation

- Use Flet's `ft.AnimatedSwitcher` for card transitions
- Or manual animation with `Container` properties:
  - `animate=ft.Animation(duration=300, curve=ft.AnimationCurve.EASE_IN_OUT)`
  - `opacity`, `transform`, `scale` properties
- Maintain 3-card queue: `[previous, current, next]`
- On new message: shift queue, animate transitions

### Error Handling Flow

**DEPRECATED** - Old error handling approach (kept for reference):

```python
try:
    # Process message
    message = await process_message(...)
    # Show success card
except Exception as e:
    # Show error in card
    error_card = create_error_card(str(e))
    # Display for 1.5s
    await asyncio.sleep(1.5)
    # Animate out and continue
```

**Current Implementation**: Error handling should be integrated into the message processing callback, showing error state in the message card itself, with automatic 1.5s delay before transitioning to next message.

### Summary Table Data

- Track during fetch: `{user_id: {messages: count, reactions: count, media: count}}`
- After fetch: Convert to list, sort by message count
- Display in `ft.DataTable` with columns

## Migration Notes

- Keep original dialog file for reference (or remove after migration)
- Ensure all validation logic is preserved
- Maintain license checking, account/group validation
- Preserve date range selection, account/group selectors

## Testing Considerations

- Test with various message types (text, media, errors)
- Test animation smoothness with rapid message flow
- Test error handling and 1.5s delay
- Test summary table accuracy
- Test finish button reset functionality

### To-dos

- [ ] Create ui/pages/fetch_data_page.py with basic page structure following other pages pattern
- [ ] Create ui/pages/fetch_data/components.py with MessageCard component and summary table component
- [ ] Create ui/pages/fetch_data/view_model.py for state management and data tracking
- [ ] Create ui/pages/fetch_data/handlers.py for fetch logic, validation, and error handling with delays
- [ ] Implement 3-card carousel animation system with slide, scale, and opacity transitions
- [ ] Add message count estimation/display before and during fetch
- [ ] Add sender profile display in message cards (avatar, name, username, phone)
- [ ] Add error display in cards with 1.5s delay before continuing to next message
- [ ] Create post-fetch summary table showing user statistics (messages, reactions, media)
- [ ] Add finish button that resets page to initial clean state
- [ ] Add fetch_data page to PageFactory and register in page_factory.py
- [ ] Update app.py and sidebar to navigate to page instead of opening dialog
- [ ] Test animations, error handling, summary table, and finish button functionality