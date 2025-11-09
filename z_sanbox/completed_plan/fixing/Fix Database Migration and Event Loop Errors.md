<!-- e97028a8-b1e9-455f-8795-965d94cab125 d28886f1-d35e-463a-bfa9-b03280be07d0 -->
# Fix Database Migration and Event Loop Errors

## Issues Identified

1. **Database Migration Error**: `table user_license_cache has no column named max_account_actions`

   - The migration in `database/managers/base.py` creates `user_license_cache` table without `max_accounts` and `max_account_actions` columns
   - `database/managers/license_manager.py` tries to INSERT/UPDATE using these columns
   - The `get_license_cache()` method already handles missing columns gracefully, but `save_license_cache()` fails

2. **Event Loop Closed Errors**: Multiple `RuntimeError: Event loop is closed` errors

   - `ui/components/sidebar.py` line 151: `_update_buttons()` calls `page.update()` without validation
   - `ui/navigation/router.py` lines 55, 68, 164: `navigate_to()`, `refresh_current_page()`, and `update_connectivity_banner()` call `page.update()` without validation
   - These occur during app shutdown or cleanup when event loop is already closed

## Solution

### 1. Database Migration Fix

**File**: `database/managers/base.py`

Add migration logic after the `user_license_cache` table creation (around line 230) to check for and add missing columns:

```python
# After creating user_license_cache table, check for missing columns
if cursor.fetchone():  # Table exists
    cursor = conn.execute("PRAGMA table_info(user_license_cache)")
    license_columns = {row[1] for row in cursor.fetchall()}
    
    # Add max_accounts column if missing
    if 'max_accounts' not in license_columns:
        conn.execute("ALTER TABLE user_license_cache ADD COLUMN max_accounts INTEGER NOT NULL DEFAULT 1")
        logger.info("Added max_accounts column to user_license_cache table")
    
    # Add max_account_actions column if missing
    if 'max_account_actions' not in license_columns:
        conn.execute("ALTER TABLE user_license_cache ADD COLUMN max_account_actions INTEGER NOT NULL DEFAULT 2")
        logger.info("Added max_account_actions column to user_license_cache table")
```

Also update the initial table creation (lines 214-227) to include these columns for new databases.

### 2. Event Loop Validation Helper

**File**: `utils/helpers.py` (or create new utility)

Add a helper function to safely update pages:

```python
def safe_page_update(page: Optional[ft.Page]) -> bool:
    """
    Safely update a Flet page, handling closed event loops gracefully.
    
    Args:
        page: Flet page instance
        
    Returns:
        True if update succeeded, False otherwise
    """
    if not page:
        return False
    
    try:
        # Check if event loop is still running
        import asyncio
        try:
            loop = asyncio.get_event_loop()
            if loop.is_closed():
                return False
        except RuntimeError:
            # No event loop in current thread
            pass
        
        page.update()
        return True
    except RuntimeError as e:
        if "Event loop is closed" in str(e):
            return False
        raise
    except Exception:
        return False
```

### 3. Update Sidebar Component

**File**: `ui/components/sidebar.py`

- Import the safe update helper
- Replace `self.page.update()` on line 151 with `safe_page_update(self.page)`
- Update exception handling to catch `RuntimeError` specifically

### 4. Update Router Component

**File**: `ui/navigation/router.py`

- Import the safe update helper
- Replace all `self.page.update()` calls (lines 55, 68, 164) with `safe_page_update(self.page)`
- The `update_connectivity_banner()` method already has try-except, but should use the helper for consistency

## Implementation Steps

1. Add migration logic to `database/managers/base.py` for missing columns
2. Update table creation in `database/managers/base.py` to include all columns
3. Create `safe_page_update()` helper function in `utils/helpers.py`
4. Update `ui/components/sidebar.py` to use safe update
5. Update `ui/navigation/router.py` to use safe update
6. Test with existing database (should migrate automatically)
7. Test with new database (should create with all columns)

## Testing

- Verify migration works on existing database with missing columns
- Verify new database creation includes all columns
- Verify no event loop errors during app shutdown
- Verify UI updates still work normally during normal operation

### To-dos

- [x] Add migration logic in database/managers/base.py to check and add missing max_accounts and max_account_actions columns to user_license_cache table
- [x] Update user_license_cache table creation in base.py to include max_accounts and max_account_actions columns for new databases
- [x] Create safe_page_update() helper function in utils/helpers.py to safely handle page updates with event loop validation
- [x] Update ui/components/sidebar.py to use safe_page_update() instead of direct page.update() calls
- [ ] Update ui/navigation/router.py to use safe_page_update() in navigate_to(), refresh_current_page(), and update_connectivity_banner() methods