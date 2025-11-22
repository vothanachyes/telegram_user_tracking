<!-- 41982b4b-45e1-41cc-957c-564e741e01fe 21d0edbb-0950-44b9-80ad-5a15e20b3edd -->
# Sample Database Integration Plan

## Overview

Integrate the data generator UI (`data_ran/ui/main_ui.py`) into the production app with a database switching mechanism. Users can switch between production database and sample database for testing purposes.

## Implementation Details

### 1. Configuration Management

**File**: `config/app_config.py` (new file, ~150 lines)

Create a new configuration manager to handle sample_db state:

- Store state in `APP_DATA_DIR/config.json`
- Methods: `is_sample_db_mode()`, `set_sample_db_mode(enabled)`, `get_sample_db_path()`
- Default sample_db path: `APP_DATA_DIR/sample_db/app.db`
- Handle JSON file creation/reading with error handling

**File**: `utils/constants.py` (~5 lines added)

Add constant for sample database path:

- `SAMPLE_DATABASE_PATH = str(APP_DATA_DIR / "sample_db" / "app.db")`

### 2. Settings Page - New Data Tab

**File**: `ui/pages/settings/tabs/data_tab.py` (new file, ~250 lines)

Create new Data tab component:

- Switch button to toggle between production and sample_db
- Show current database mode status
- When in sample_db mode: Show "Generate Data" button
- When in production mode: Show switch to enable sample_db
- Handle switch click → show warning dialog
- Handle generate data button → open data generator UI

**File**: `ui/pages/settings/tabs/__init__.py` (~5 lines added)

Export DataTab:

- Add `from .data_tab import DataTab`

**File**: `ui/pages/settings/page.py` (~30 lines modified)

Add Data tab to settings:

- Import DataTab
- Initialize DataTab instance
- Add new tab to tabs_widget (after Security tab)
- Conditionally hide Security tab when in sample_db mode
- Pass necessary dependencies (db_manager, page reference)

### 3. Warning Dialog

**File**: `ui/dialogs/sample_db_warning_dialog.py` (new file, ~120 lines)

Create warning dialog for database switch:

- Warning message about data limitations
- Explain that real account/login is disabled
- Explain that logout is disabled
- Explain Security tab is hidden
- Confirm/Cancel buttons
- On confirm: Set sample_db mode in config, show restart required message

### 4. Internationalization

**File**: `locales/en.json` (~15 lines added)

Add translation keys:

- `data_tab`: "Data"
- `sample_db_mode`: "Sample Database Mode"
- `switch_to_sample_db`: "Switch to Sample Database"
- `switch_to_production_db`: "Switch to Production Database"
- `current_database_mode`: "Current Database Mode"
- `production_database`: "Production Database"
- `sample_database`: "Sample Database"
- `generate_test_data`: "Generate Test Data"
- `sample_db_warning_title`: "Switch to Sample Database?"
- `sample_db_warning_message`: "Warning: Switching to sample database mode will disable real account login, logout functionality, and hide the Security tab. This mode is for testing data generation only. You will need to restart the application after switching."
- `sample_db_restart_required`: "Please restart the application to complete the database switch."
- `sample_db_switch_back_warning`: "Switching back to production database will restore all functionality. You will need to restart the application."

**File**: `locales/km.json` (~15 lines added)

Add Khmer translations for all new keys.

### 5. Database Manager Updates

**File**: `config/settings.py` (~20 lines modified)

Update Settings class to check sample_db mode:

- Check `app_config.is_sample_db_mode()` when initializing db_manager
- Use sample_db path if in sample_db mode
- Reload db_manager when switching modes

**File**: `database/db_manager.py` (~10 lines modified)

Ensure DatabaseManager can handle sample_db path correctly.

### 6. Authentication Restrictions

**File**: `ui/pages/settings/tabs/authenticate_tab/page.py` (~15 lines modified)

Disable account management when in sample_db mode:

- Check `app_config.is_sample_db_mode()` on initialization
- Disable "Add Account" button when in sample_db mode
- Show informational message explaining why it's disabled

**File**: `ui/pages/telegram/page.py` (~20 lines modified)

Disable Telegram connection when in sample_db mode:

- Check `app_config.is_sample_db_mode()` 
- Disable connect/fetch buttons
- Show informational message explaining why it's disabled

### 7. Logout Button Restriction

**File**: `ui/pages/profile_page.py` (~15 lines modified)

Disable logout button when in sample_db mode:

- Check `app_config.is_sample_db_mode()`
- Hide or disable logout button
- Show informational message if needed

**File**: `ui/components/top_header.py` (~10 lines modified)

Check if logout button exists in top header and disable it in sample_db mode.

### 8. Data Generator Integration

**File**: `ui/pages/settings/tabs/data_tab.py` (~50 lines added to existing)

Add method to open data generator:

- Create new Flet page/window for data generator
- Initialize DataGeneratorApp with sample_db path
- Handle window close and cleanup
- Use `data_ran/ui/main_ui.py` as base

**File**: `data_ran/ui/main_ui.py` (~10 lines modified)

Update DataGeneratorApp to accept db_path parameter:

- Modify `__init__` to accept optional `db_path` parameter
- Pass db_path to DatabaseDumper

### 9. App Initialization

**File**: `ui/app.py` (~15 lines modified)

Check sample_db mode on startup:

- Import app_config
- Check if in sample_db mode before showing login
- If in sample_db mode: Skip login, show main app directly
- Ensure db_manager uses correct database path

**File**: `main.py` (~5 lines modified)

Ensure app_config is initialized early if needed.

### 10. Security Tab Hiding

**File**: `ui/pages/settings/page.py` (~20 lines modified)

Conditionally show/hide Security tab:

- Check `app_config.is_sample_db_mode()` in `_build_tabs()`
- Only add Security tab if not in sample_db mode
- Update tab indices accordingly

## Implementation Order

1. Create app_config.py for configuration management
2. Add i18n strings
3. Create sample_db_warning_dialog
4. Create data_tab component
5. Integrate data_tab into settings page
6. Update database manager to use sample_db path
7. Add authentication restrictions
8. Add logout button restrictions
9. Hide Security tab in sample_db mode
10. Integrate data generator UI
11. Update app initialization

## Testing Considerations

- Test switching to sample_db mode and restart
- Test switching back to production mode
- Verify all restrictions are enforced in sample_db mode
- Verify data generator works with sample_db
- Test i18n strings in both languages
- Verify Security tab is hidden in sample_db mode
- Test that logout is disabled in sample_db mode

### To-dos

- [ ] Create config/app_config.py to manage sample_db state in APP_DATA_DIR/config.json
- [ ] Add i18n translation keys for Data tab, warnings, and messages in locales/en.json and locales/km.json
- [ ] Create ui/dialogs/sample_db_warning_dialog.py with warning message and restart requirement
- [ ] Create ui/pages/settings/tabs/data_tab.py with switch button and generate data button
- [ ] Integrate DataTab into settings page and conditionally hide Security tab
- [ ] Update config/settings.py to use sample_db path when in sample_db mode
- [ ] Disable Telegram account management and connection in sample_db mode
- [ ] Disable logout button in profile page and top header when in sample_db mode
- [ ] Integrate data_ran/ui/main_ui.py to open in new window/dialog when Generate Data button is clicked
- [ ] Update ui/app.py to skip login and use correct database path when in sample_db mode