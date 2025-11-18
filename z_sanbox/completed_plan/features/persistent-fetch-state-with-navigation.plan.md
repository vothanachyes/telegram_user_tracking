<!-- cd2fe177-7bac-44f0-9091-4c11cbea5621 9e786d88-fc00-4034-85b4-e2389ecd21e3 -->
# Persistent Fetch State with Navigation

## Overview

Currently, fetch progress is lost when navigating away from the fetch page. This plan implements:

1. Global fetch state manager that persists across page navigations
2. Small fetch indicator in top header showing fetched message count
3. Confirmation dialog when closing app during fetch
4. Allow navigation during fetch (remove blocking)

## Implementation Steps

### 1. Create Global Fetch State Manager

**File**: `services/fetch_state_manager.py` (new)

- Singleton service to manage fetch state globally
- Store: `is_fetching`, `processed_count`, `error_count`, `skipped_count`, `estimated_total`, `group_id`, `group_name`
- Methods: `start_fetch()`, `update_progress()`, `stop_fetch()`, `reset()`, `get_state()`
- Thread-safe state updates

### 2. Update FetchDataPage to Use Global State

**File**: `ui/pages/fetch_data/page.py`

- Replace local `view_model` state with global `fetch_state_manager`
- Keep local view_model for UI-specific state (message cards, animations)
- Sync local view_model with global state for display
- Update progress callbacks to use global state manager

### 3. Remove Navigation Blocking

**File**: `ui/navigation/router.py`

- Remove lines 48-62 that block navigation during fetch
- Allow navigation even when fetch is in progress

### 4. Add Fetch Indicator to TopHeader

**File**: `ui/components/top_header.py`

- Add small indicator container in top right (before About button)
- Show when `fetch_state_manager.is_fetching` is True
- Display: icon + "Fetching: X messages" (compact format)
- Click to navigate to fetch_data page
- Update indicator when global state changes

### 5. Handle Window Close Event

**File**: `ui/app.py`

- Add `page.window.on_event` handler for window close event
- Check `fetch_state_manager.is_fetching` before allowing close
- Show confirmation dialog: "Are you sure to close app? Fetching data."
- Use `DialogManager.show_confirmation_dialog()` with proper handlers
- Prevent close if user cancels

### 6. Update Sidebar to Allow Navigation

**File**: `ui/components/sidebar.py`

- Remove navigation blocking in `_create_nav_button` (lines 65-74)
- Remove `disabled=self._is_fetching` from buttons
- Keep fetch button disabled during fetch (optional)

### 7. Update Fetch Handlers

**File**: `ui/pages/fetch_data/handlers.py`

- Update progress callbacks to use global state manager
- Ensure state persists when page is navigated away

### 8. Add Localization Strings

**Files**: `locales/en.json`, `locales/km.json`

- Add: `"fetching_indicator": "Fetching: {count} messages"`
- Add: `"close_app_during_fetch_title": "Close Application?"`
- Add: `"close_app_during_fetch_message": "Are you sure to close app? Fetching data."`

## Key Design Decisions

1. **State Separation**: 

- Global state: Progress counters, fetch status (persists across navigation)
- Local state: UI animations, message cards (page-specific)

2. **Indicator Placement**: TopHeader top-right corner, visible on all pages when fetching

3. **Window Close**: Intercept at Flet page level, show modal confirmation

4. **Navigation**: Always allowed, fetch continues in background

## Testing Considerations

- Start fetch, navigate to another page, verify indicator shows progress
- Navigate back to fetch page, verify state is preserved
- Try closing app during fetch, verify confirmation dialog appears
- Complete fetch, verify indicator disappears
- Test with multiple page navigations during fetch