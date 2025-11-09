<!-- c5138394-c743-48a3-af85-8b368e0e5e49 5f4cf325-90b8-4633-bc00-c33420307a23 -->
# UI Header and Styling Updates

## Overview
Update the application's visual design with a smaller header, gradient backgrounds, image support, smaller sidebar, consistent page titles, and animated gradient background.

## Changes Required

### 1. Top Header Component (`ui/components/top_header.py`)
- Reduce header height from 60px to 45px
- Reduce greeting text size from 18 to smaller (e.g., 14-16)
- Add gradient background using primary colors
- Add background image support (`assets/header_background.png` or `.jpg`)
  - Image should be low opacity (adjustable, default ~0.3)
  - Image should be centered and maintain center position on screen width changes
  - Use `ft.Container` with `Stack` for layering (gradient + image + content)
- Add avatar icon (`ft.Icons.PERSON`) to the left of greeting text
  - Make it replaceable with image in the future (use conditional rendering)
- Reduce padding to match smaller header

### 2. Sidebar Component (`ui/components/sidebar.py`)
- Reduce sidebar width from 80px to smaller (e.g., 60-70px)
- Adjust button sizes proportionally
- Reduce icon sizes if needed

### 3. Page Titles Consistency
Update all page files to use consistent title size of 18:
- `ui/pages/dashboard_page.py` (currently 32)
- `ui/pages/telegram_page.py` (currently 32)
- `ui/pages/user_dashboard_page.py` (check for title)
- `ui/pages/fetch_data_page.py` (currently 32)
- `ui/pages/settings/page.py` (if has title)
- Any other pages with titles

### 4. Page Content Spacing
- Increase spacing between header and page content
- Add top padding/margin to page containers (e.g., increase from current spacing)

### 5. App Background Gradient (`ui/initialization/page_config.py` or `ui/app.py`)
- Replace solid background color with gradient (primary to primary_dark)
- Implement rotation mechanism that rotates gradient 45° every 5 minutes
- Use `ft.Container` with gradient decoration
- Create a background service/component to handle rotation timer
- Store current rotation angle and update every 5 minutes

### 6. Theme Manager (`ui/theme.py`)
- Add method to get gradient background with rotation angle
- Add support for header background image path
- Add opacity setting for header background image

## Implementation Details

### Header Background Image
- Check if `assets/header_background.png` or `.jpg` exists
- Use `ft.Image` with `fit=ft.ImageFit.COVER` and `opacity` property
- Center image using `alignment` and `repeat` properties
- Layer: Container (gradient) → Image (low opacity) → Content

### Gradient Rotation
- Use threading or async timer to update rotation every 5 minutes
- Store rotation angle (0, 45, 90, 135, 180, 225, 270, 315, then back to 0)
- Update page background gradient decoration on rotation
- Use `ft.LinearGradient` with `begin` and `end` points based on angle

### Avatar Icon
- Use `ft.IconButton` or `ft.CircleAvatar` with `ft.Icons.PERSON`
- Position to left of greeting text
- Make it easy to replace with image later (check for image path first, fallback to icon)

## Files to Modify
1. `ui/components/top_header.py` - Header redesign
2. `ui/components/sidebar.py` - Reduce width
3. `ui/pages/dashboard_page.py` - Title size and spacing
4. `ui/pages/telegram_page.py` - Title size and spacing
5. `ui/pages/user_dashboard_page.py` - Title size and spacing (if applicable)
6. `ui/pages/fetch_data_page.py` - Title size and spacing
7. `ui/pages/settings/page.py` - Title size and spacing (if applicable)
8. `ui/theme.py` - Add gradient and image support methods
9. `ui/initialization/page_config.py` - Update background to gradient
10. `ui/app.py` - Add gradient rotation timer/service

## Testing Considerations
- Verify header looks good with and without background image
- Test gradient rotation animation
- Ensure all page titles are consistent size
- Check spacing on all pages
- Verify sidebar width reduction doesn't break layout
- Test on different screen widths for header image centering

### To-dos

- [ ] Update TopHeader component: reduce height to 45px, smaller greeting text, add gradient background, add background image support, add avatar icon
- [ ] Reduce sidebar width from 80px to 60-70px and adjust button sizes
- [ ] Update all page titles to size 18 (dashboard, telegram, user_dashboard, fetch_data, settings)
- [ ] Increase spacing between header and page content on all pages
- [ ] Replace app background with gradient (primary to primary_dark) and implement 45° rotation every 5 minutes
- [ ] Add gradient and image support methods to ThemeManager