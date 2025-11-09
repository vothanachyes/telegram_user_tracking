<!-- d2f06169-f51e-4417-9baa-6ea8c5439781 e5985912-9749-47a0-b1d4-2b058e45f237 -->
# Font Size and Spacing Standardization Plan

## Problem Analysis
After reviewing all pages, components, and dialogs, I found significant inconsistencies:

### Font Sizes
- **Page titles**: 18, 20, 22, 24 (inconsistent)
- **Section titles**: 14, 16, 18, 20 (inconsistent)  
- **Content text**: 12, 14, 16 (inconsistent)
- **Large numbers**: 28, 32 (inconsistent)
- **Small text**: 12, 13 (inconsistent)
- Some titles are smaller than content text (e.g., title=18 vs content=20)

### Spacing
- **Container heights**: 10, 15, 20, 30, 50 (inconsistent)
- **Padding**: 10, 15, 20, 30 (inconsistent)
- **Column/Row spacing**: 2, 5, 8, 10, 15, 20 (inconsistent)
- **Card padding**: 15, 20, 30 (inconsistent)

## Standard Font Size System

### Typography Hierarchy
1. **Page Title**: `size=24` - Main page heading (e.g., "Dashboard", "Settings", "Telegram")
2. **Section Title**: `size=20` - Card/section headings within pages
3. **Subsection Title**: `size=18` - Subsections within cards
4. **Body Text**: `size=14` - Main content text, descriptions
5. **Small Text**: `size=12` - Labels, captions, secondary info, timestamps
6. **Large Numbers**: `size=32` - Statistics, large numeric values
7. **Medium Numbers**: `size=24` - Medium-sized numeric values

## Standard Spacing System

### Spacing Hierarchy (8px base unit)
1. **XS (Extra Small)**: `4px` - Tight spacing (e.g., icon + text, tight lists)
2. **SM (Small)**: `8px` - Small spacing (e.g., related items)
3. **MD (Medium)**: `12px` - Default spacing (e.g., form fields, list items)
4. **LG (Large)**: `16px` - Section spacing (e.g., between sections in cards)
5. **XL (Extra Large)**: `20px` - Major section spacing (e.g., between cards)
6. **XXL (2X Large)**: `24px` - Page-level spacing (e.g., between major page sections)
7. **XXXL (3X Large)**: `32px` - Large page spacing (e.g., top of page, large gaps)

### Padding Hierarchy
1. **XS**: `8px` - Tight padding (e.g., small badges, compact components)
2. **SM**: `12px` - Small padding (e.g., compact cards, small containers)
3. **MD**: `16px` - Default padding (e.g., standard cards, containers)
4. **LG**: `20px` - Large padding (e.g., page padding, large cards)
5. **XL**: `24px` - Extra large padding (e.g., login form, dialogs)

### Container Height Spacing
1. **XS**: `8px` - Very small vertical spacing
2. **SM**: `12px` - Small vertical spacing
3. **MD**: `16px` - Default vertical spacing
4. **LG**: `20px` - Large vertical spacing (most common)
5. **XL**: `24px` - Extra large vertical spacing
6. **XXL**: `32px` - Very large vertical spacing

## Theme Constants (All in ui/theme.py)

Add to `ThemeManager` class as properties:
- Font size properties: `font_size_page_title`, `font_size_section_title`, `font_size_subsection_title`, `font_size_body`, `font_size_small`, `font_size_large_number`, `font_size_medium_number`
- Spacing properties: `spacing_xs`, `spacing_sm`, `spacing_md`, `spacing_lg`, `spacing_xl`, `spacing_xxl`, `spacing_xxxl`
- Padding properties: `padding_xs`, `padding_sm`, `padding_md`, `padding_lg`, `padding_xl`
- Height properties: `height_xs`, `height_sm`, `height_md`, `height_lg`, `height_xl`, `height_xxl`

### Helper Methods
Add convenience methods:
- `spacing_container(size="lg")` - Create a spacing container with standard height
- Update `create_card()` to use `padding_md` by default

## Files to Update

### Core Theme
1. **ui/theme.py** - Add all font size, spacing, padding, and height properties

### Pages
1. **login_page.py** - Update font sizes and spacing
2. **dashboard_page.py** - Update font sizes and spacing
3. **about_page.py** - Update font sizes and spacing
4. **profile_page.py** - Update font sizes and spacing
5. **settings/page.py** - Update font sizes and spacing
6. **telegram/page.py** - Update font sizes and spacing
7. **user_dashboard/page.py** - Update font sizes and spacing
8. **fetch_data_page.py** - Update font sizes and spacing

### Components
1. **stat_card.py** - Update font sizes and spacing
2. **top_header.py** - Update font sizes and spacing
3. **sidebar.py** - Update spacing
4. All other components - Review and standardize

### Dialogs
1. **message_detail_dialog.py** - Update font sizes and spacing
2. **user_detail_dialog.py** - Update font sizes and spacing
3. **pin_dialog.py** - Update font sizes and spacing
4. **fetch_data_dialog.py** - Update font sizes and spacing
5. **add_account_dialog.py** - Update font sizes and spacing
6. All other dialogs - Review and standardize

### Settings Tabs
1. **settings/tabs/general_tab.py** - Update font sizes and spacing
2. **settings/tabs/authenticate_tab.py** - Update font sizes and spacing
3. **settings/tabs/configure_tab.py** - Update font sizes and spacing

### Telegram Components
1. **telegram/components/messages_tab.py** - Update font sizes and spacing
2. **telegram/components/users_tab.py** - Update font sizes and spacing
3. **telegram/components/filters_bar.py** - Update font sizes and spacing

### User Dashboard Components
1. **user_dashboard/components/user_search.py** - Update font sizes and spacing
2. **user_dashboard/components/user_stats.py** - Update font sizes and spacing
3. **user_dashboard/components/user_messages.py** - Update font sizes and spacing

### Fetch Data Components
1. **fetch_data/components.py** - Update font sizes and spacing

## Implementation Steps

1. **Add all constants to theme.py** - Add font size, spacing, padding, and height properties to ThemeManager
2. **Add helper methods** - Add spacing_container() and update create_card()
3. **Update all page titles** - Standardize to 24px using theme_manager.font_size_page_title
4. **Update all section titles** - Standardize to 20px using theme_manager.font_size_section_title
5. **Update all subsection titles** - Standardize to 18px using theme_manager.font_size_subsection_title
6. **Update all body text** - Standardize to 14px using theme_manager.font_size_body
7. **Update all small text** - Standardize to 12px using theme_manager.font_size_small
8. **Update all large numbers** - Standardize to 32px using theme_manager.font_size_large_number
9. **Replace all hardcoded spacing** - Use theme_manager.spacing_* properties
10. **Replace all hardcoded padding** - Use theme_manager.padding_* properties
11. **Replace all Container(height=X)** - Use theme_manager.spacing_container() or theme_manager.height_*
12. **Review and fix any remaining inconsistencies** - Ensure hierarchy is maintained

## Testing Checklist
- [ ] All page titles are 24px (from theme)
- [ ] All section titles are 20px (from theme)
- [ ] All subsection titles are 18px (from theme)
- [ ] All body text is 14px (from theme)
- [ ] All small text is 12px (from theme)
- [ ] All large numbers are 32px (from theme)
- [ ] All spacing uses theme constants
- [ ] All padding uses theme constants
- [ ] All container heights use theme constants
- [ ] Visual hierarchy is clear (titles > content)
- [ ] No title is smaller than its content
- [ ] Consistency across all pages
- [ ] Consistency across all dialogs
- [ ] Consistency across all components
- [ ] All values are accessible from theme_manager

### To-dos

- [ ] Add all font size, spacing, padding, and height properties to ThemeManager in ui/theme.py
- [ ] Add spacing_container() helper method and update create_card() to use theme padding
- [ ] Update all page main titles to use theme_manager.font_size_page_title (24px)
- [ ] Update all section/card titles to use theme_manager.font_size_section_title (20px)
- [ ] Update all subsection titles to use theme_manager.font_size_subsection_title (18px)
- [ ] Standardize all body text to use theme_manager.font_size_body (14px)
- [ ] Standardize all small text to use theme_manager.font_size_small (12px)
- [ ] Standardize all large numbers to use theme_manager.font_size_large_number (32px)
- [ ] Replace all hardcoded spacing values with theme_manager.spacing_* properties
- [ ] Replace all hardcoded padding values with theme_manager.padding_* properties
- [ ] Replace all Container(height=X) with theme_manager.spacing_container() or theme_manager.height_*
- [ ] Verify visual hierarchy is correct (titles > content) and all values come from theme