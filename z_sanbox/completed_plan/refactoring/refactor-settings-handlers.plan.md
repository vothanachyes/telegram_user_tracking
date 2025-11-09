<!-- 326d074a-f595-4df9-9afe-53585aae7dd5 d81c32bc-2fca-44ce-9c54-6adb04381373 -->
# Comprehensive File Refactoring Plan

Multiple files exceed the repository's file size limits. This plan addresses all large files that need refactoring.

## Files Exceeding Limits

### Critical (Exceeds Maximum):
1. **`ui/pages/settings/handlers.py`** - 1273 lines (max: 500) ❌
2. **`ui/pages/settings/tabs/authenticate_tab.py`** - 802 lines (max: 400) ❌
3. **`services/telegram/telegram_service.py`** - 771 lines (max: 500) ❌
4. **`ui/pages/fetch_data_page.py`** - 489 lines (max: 400) ❌
5. **`ui/pages/fetch_data/components.py`** - 447 lines (max: 300) ❌
6. **`ui/pages/about_page.py`** - 441 lines (max: 400) ❌
7. **`ui/components/data_table.py`** - 379 lines (max: 300) ❌
8. **`ui/components/toast.py`** - 334 lines (max: 300) ❌

### Warning (Approaching Maximum):
9. **`ui/pages/dashboard_page.py`** - 404 lines (max: 400) ⚠️
10. **`services/license_service.py`** - 477 lines (max: 500) ⚠️
11. **`ui/pages/user_dashboard/handlers.py`** - 374 lines (max: 400) ⚠️
12. **`services/update_service.py`** - 390 lines (max: 500) ⚠️
13. **`services/media_service.py`** - 384 lines (max: 500) ⚠️

## Refactoring Strategy

### Phase 1: Settings Handlers (Priority 1)
Split `settings/handlers.py` (1273 lines) into:
- `handlers/base.py` - Base utilities (~150 lines)
- `handlers/authentication.py` - Auth handlers (~400 lines)
- `handlers/account.py` - Account management (~250 lines)
- `handlers/configuration.py` - Config handlers (~80 lines)
- `handlers/dialogs.py` - Dialog management (~200 lines)
- `handlers.py` - Main facade (~150 lines)

### Phase 2: Authenticate Tab (Priority 2)
Split `settings/tabs/authenticate_tab.py` (802 lines) into:
- `authenticate_tab/page.py` - Main orchestration (~200 lines)
- `authenticate_tab/components.py` - UI components (~300 lines)
- `authenticate_tab/view_model.py` - State management (~150 lines)
- `authenticate_tab/utils.py` - Helper methods (~150 lines)

### Phase 3: Telegram Service (Priority 3)
Split `services/telegram/telegram_service.py` (771 lines) into:
- `telegram/telegram_service.py` - Main orchestrator (~200 lines)
- `telegram/session_manager.py` - Session management (~200 lines)
- `telegram/fetch_manager.py` - Data fetching logic (~200 lines)
- `telegram/connection_manager.py` - Connection handling (~170 lines)

### Phase 4: Fetch Data Page (Priority 4)
Split `fetch_data_page.py` (489 lines) into:
- `fetch_data/page.py` - Main orchestration (~200 lines)
- `fetch_data/progress_ui.py` - Progress UI components (~150 lines)
- `fetch_data/summary_ui.py` - Summary display (~140 lines)

### Phase 5: Components (Priority 5)
- **`components/data_table.py`** (379 lines) → Split into base table + specialized tables
- **`components/toast.py`** (334 lines) → Extract toast types into separate modules
- **`fetch_data/components.py`** (447 lines) → Already split into MessageCard and SummaryTable, verify structure

### Phase 6: Other Pages (Priority 6)
- **`about_page.py`** (441 lines) → Split into sections/components
- **`dashboard_page.py`** (404 lines) → Extract components if needed

## Implementation Order

1. **Settings handlers** - Most critical, used by multiple tabs
2. **Authenticate tab** - Large UI component, affects user experience
3. **Telegram service** - Core service, affects multiple features
4. **Fetch data page** - User-facing feature
5. **Components** - Reusable UI elements
6. **Other pages** - Lower priority, can be done incrementally

### To-dos

- [ ] Phase 1: Refactor settings/handlers.py (1273 lines) - Split into base, authentication, account, configuration, and dialog handlers
- [ ] Phase 2: Refactor settings/tabs/authenticate_tab.py (802 lines) - Split into page, components, view_model, and utils
- [ ] Phase 3: Refactor services/telegram/telegram_service.py (771 lines) - Split into main service, session_manager, fetch_manager, and connection_manager
- [ ] Phase 4: Refactor fetch_data_page.py (489 lines) - Split into page, progress_ui, and summary_ui
- [ ] Phase 5: Refactor components - data_table.py (379 lines) and toast.py (334 lines)
- [ ] Phase 6: Refactor other pages - about_page.py (441 lines) and dashboard_page.py (404 lines)