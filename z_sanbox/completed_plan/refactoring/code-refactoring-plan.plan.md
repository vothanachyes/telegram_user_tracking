<!-- 4221b5d7-8c53-4ea9-a227-bc30a0ebbd17 b899ef2c-13b1-49a9-b16f-d125bd2f2a6d -->
# Code Refactoring Plan for Maintainability and Scalability

## Overview

Refactor large files (>500 lines) in `services/` and `ui/` directories to improve maintainability, testability, and scalability. The plan follows separation of concerns, single responsibility principle, and creates reusable components.

## Current Issues Identified

### Services Layer

- **export_service.py (680 lines)**: 6 export methods with duplicated formatting code
- **telegram_service.py (614 lines)**: Complex message processing mixed with API operations
- **media_service.py (385 lines)**: Reasonable size but could benefit from strategy pattern

### UI Layer  

- **user_dashboard_page.py (861 lines)**: UI building, event handling, data fetching, export all mixed
- **telegram_page.py (844 lines)**: Similar issues - UI, filtering, export logic intertwined
- **settings_page.py (799 lines)**: Three tabs with extensive form handling logic
- **app.py (418 lines)**: Navigation and initialization logic could be separated

## Refactoring Strategy

### Phase 1: Export Service Refactoring

**Target File**: `services/export_service.py` (680 lines → ~150 lines)

**New Structure**:

```
services/
  export/
    __init__.py
    base_exporter.py          # Base exporter interface
    excel_exporter.py         # Excel-specific logic
    pdf_exporter.py           # PDF-specific logic
    formatters/
      __init__.py
      excel_formatter.py      # Excel formatting (styles, columns)
      pdf_formatter.py        # PDF formatting (styles, tables)
      data_formatter.py       # Data transformation utilities
    exporters/
      __init__.py
      messages_exporter.py    # Messages export logic
      users_exporter.py       # Users export logic
      user_data_exporter.py   # User data export logic
```

**Benefits**:

- Separate Excel/PDF concerns
- Reusable formatters
- Easier to add new export formats (CSV, JSON)
- Better testability

### Phase 2: Telegram Service Refactoring

**Target File**: `services/telegram_service.py` (614 lines → ~200 lines)

**New Structure**:

```
services/
  telegram/
    __init__.py
    client_manager.py         # Client creation, connection, session management
    message_processor.py      # Message processing logic
    reaction_processor.py     # Reaction processing logic
    user_processor.py         # User processing logic
    group_manager.py          # Group operations
```

**Benefits**:

- Clear separation of API operations vs processing logic
- Easier to test message processing independently
- Better error handling per concern

### Phase 3: UI Pages Refactoring

**Target Files**:

- `user_dashboard_page.py` (861 lines → ~200 lines)
- `telegram_page.py` (844 lines → ~200 lines)  
- `settings_page.py` (799 lines → ~200 lines)

**New Structure**:

```
ui/
  pages/
    user_dashboard/
      __init__.py
      page.py                 # Main page (orchestration)
      components/
        user_search.py        # User search component
        user_stats.py         # Statistics display
        user_messages.py      # Messages table component
      view_model.py           # Business logic (data fetching, filtering)
      handlers.py              # Event handlers
    
    telegram/
      __init__.py
      page.py                 # Main page
      components/
        messages_tab.py       # Messages tab component
        users_tab.py          # Users tab component
        filters_bar.py        # Reusable filter bar
      view_model.py           # Data operations
      handlers.py              # Event handlers
    
    settings/
      __init__.py
      page.py                 # Main page
      tabs/
        general_tab.py        # General settings tab
        authenticate_tab.py   # Auth settings tab
        configure_tab.py       # Configure settings tab
      handlers.py              # Event handlers
```

**Benefits**:

- UI components are reusable
- Business logic separated from UI
- Easier to test view models independently
- Clearer component boundaries

### Phase 4: Shared UI Components

**New Components**:

```
ui/
  components/
    export_menu.py            # Reusable export menu component
    filter_bar.py             # Reusable filter bar (dates, groups, search)
    stat_cards_grid.py        # Reusable statistics cards grid
    user_search_dropdown.py   # Reusable user search with dropdown
    file_picker_manager.py    # Centralized file picker management
```

**Benefits**:

- DRY principle - no code duplication
- Consistent UI across pages
- Easier to maintain and update

### Phase 5: App Structure Refactoring

**Target File**: `ui/app.py` (418 lines → ~200 lines)

**New Structure**:

```
ui/
  app.py                     # Main app (simplified)
  navigation/
    __init__.py
    router.py                # Page routing logic
    page_factory.py           # Page creation factory
  initialization/
    __init__.py
    service_init.py           # Service initialization
    page_config.py            # Page configuration
```

**Benefits**:

- Clear separation of concerns
- Easier to add new pages
- Better testability

## Implementation Details

### Export Service Refactoring

**Key Changes**:

1. Create `BaseExporter` abstract class with common methods
2. Extract Excel formatting to `ExcelFormatter` class
3. Extract PDF formatting to `PDFFormatter` class  
4. Create specific exporters (MessagesExporter, UsersExporter) that use formatters
5. ExportService becomes a facade that delegates to specific exporters

**Example Structure**:

```python
# services/export/formatters/excel_formatter.py
class ExcelFormatter:
    def create_header_format(self, workbook): ...
    def create_cell_format(self, workbook): ...
    def set_column_widths(self, worksheet, columns): ...

# services/export/exporters/messages_exporter.py
class MessagesExporter:
    def __init__(self, formatter):
        self.excel_formatter = ExcelFormatter()
        self.pdf_formatter = PDFFormatter()
    
    def export_to_excel(self, messages, path): ...
    def export_to_pdf(self, messages, path): ...
```

### Telegram Service Refactoring

**Key Changes**:

1. `ClientManager`: Handle all client operations (create, connect, disconnect, session)
2. `MessageProcessor`: Extract `_process_message` logic with media detection
3. `ReactionProcessor`: Extract `_process_reactions` logic
4. `UserProcessor`: Extract `_process_user` logic
5. `TelegramService`: Orchestrates processors and client manager

### UI Pages Refactoring

**Key Changes**:

1. Extract view models that handle data fetching and business logic
2. Create reusable UI components for common patterns
3. Separate event handlers into dedicated files
4. Main page files become orchestrators that compose components

**Example Structure**:

```python
# ui/pages/user_dashboard/view_model.py
class UserDashboardViewModel:
    def __init__(self, db_manager):
        self.db_manager = db_manager
    
    def search_users(self, query): ...
    def get_user_stats(self, user_id, group_id, dates): ...
    def get_user_messages(self, user_id, group_id, dates): ...

# ui/pages/user_dashboard/page.py
class UserDashboardPage:
    def __init__(self, db_manager):
        self.view_model = UserDashboardViewModel(db_manager)
        self.search_component = UserSearchComponent(...)
        self.stats_component = UserStatsComponent(...)
        # Compose components
```

## Migration Strategy

1. **Create new structure** alongside existing code
2. **Implement new modules** with same public interface
3. **Update imports** gradually (file by file)
4. **Test thoroughly** after each phase
5. **Remove old code** once migration complete

## Testing Considerations

- Each new module should be independently testable
- View models can be tested without UI
- Formatters can be tested with mock data
- Components can be tested in isolation

## File Size Targets

- Service files: < 300 lines
- UI page files: < 250 lines  
- Component files: < 200 lines
- Utility/formatter files: < 150 lines

## Benefits Summary

1. **Maintainability**: Smaller, focused files are easier to understand and modify
2. **Testability**: Separated concerns enable unit testing
3. **Reusability**: Components and formatters can be reused
4. **Scalability**: Easy to add new features without touching existing code
5. **Reliability**: Clear boundaries reduce bugs and side effects
6. **Developer Experience**: Easier to navigate and find relevant code

### To-dos

- [ ] Create export service directory structure (export/, formatters/, exporters/)
- [ ] Implement BaseExporter abstract class and ExcelFormatter class
- [ ] Implement PDFFormatter class and DataFormatter utilities
- [ ] Create MessagesExporter, UsersExporter, and UserDataExporter classes
- [ ] Refactor ExportService to use new exporters and update all imports
- [ ] Create telegram service directory structure (telegram/ subdirectory)
- [ ] Extract ClientManager class for client operations and session management
- [ ] Extract MessageProcessor, ReactionProcessor, and UserProcessor classes
- [ ] Refactor TelegramService to use processors and update all imports
- [ ] Create shared UI components (ExportMenu, FilterBar, StatCardsGrid, UserSearchDropdown)
- [ ] Create user_dashboard directory structure and extract UserDashboardViewModel
- [ ] Extract UI components (UserSearch, UserStats, UserMessages) and handlers
- [ ] Refactor UserDashboardPage to use new structure and update imports
- [ ] Create telegram page directory structure and extract TelegramViewModel
- [ ] Extract MessagesTab, UsersTab components and handlers
- [ ] Refactor TelegramPage to use new structure and update imports
- [ ] Create settings page directory structure with tabs subdirectory
- [ ] Extract GeneralTab, AuthenticateTab, ConfigureTab components
- [ ] Refactor SettingsPage to use new structure and update imports
- [ ] Extract navigation/router logic and service initialization from app.py
- [ ] Update all imports across codebase and verify functionality