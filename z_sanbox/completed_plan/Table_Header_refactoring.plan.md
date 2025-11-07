<!-- b9c14cb1-b119-4bf5-956e-206b26223bf6 c3e30262-4246-400c-a7f2-960d418f08ef -->
# Inline Controls and Narrow No Column

## Changes Required

### 1. Make Controls Inline (telegram_page.py)

- Keep `wrap=True` for responsive wrapping when needed
- Move search field from DataTable component to be part of this inline row
- Adjust control widths to be responsive (use appropriate widths that allow inline display when space permits)
- All controls (search, group select, date range, refresh, menu) should be in the same Row

### 2. Update DataTable Component (data_table.py)

- Remove search field from DataTable's internal layout (lines 80-87)
- Keep search functionality but expose search field as a property so it can be placed externally
- OR: Accept search_field as optional external control parameter

### 3. Make "No" Column Narrower (data_table.py)

- Modify `_create_header()` to give first column fixed small width instead of `expand=True`
- Modify `_create_table_row()` to match - first column should have fixed width (e.g., 60-80px)
- Other columns continue using `expand=True` for proportional distribution

## Files to Modify

- `ui/pages/telegram_page.py` - Move search to inline row, remove wrap
- `ui/components/data_table.py - Remove search from layout, make first column narrow

## Implementation Details

- Search field: Move from DataTable internal layout to telegram_page.py inline row
- No column: Use fixed width (e.g., 70px) instead of expand=True for first column only
- Controls row: Single Row with spacing, no wrapping, all controls inline