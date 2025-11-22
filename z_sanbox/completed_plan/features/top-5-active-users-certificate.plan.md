<!-- 282fe146-fc56-4949-9251-04384c313a36 de6748e7-8fde-4fb4-835c-63d36a9f486e -->
# Top 5 Active Users Certificate Implementation

## Overview

Add a certificate-style display for the top 5 most active users in a Telegram group, styled similar to an honor roll certificate. The certificate will be displayed in the Reports page and can be exported as PDF or image (PNG/JPEG).

## Components to Create

### 1. Certificate Component (`ui/components/top_users_certificate.py`)

- **Purpose**: Display certificate-style UI showing top 5 users
- **Features**:
  - Decorative border with blue/gold styling
  - Light background with subtle patterns
  - Vertical layout for 5 users (centered)
  - Each user entry: profile photo (or avatar fallback), rank badge (TOP 1-5), full name, message count
  - Bilingual title (English/Khmer)
  - Group name and date range display
  - Responsive design matching theme (dark/light mode)

### 2. Certificate Exporter (`services/export/exporters/certificate_exporter.py`)

- **Purpose**: Export certificate to PDF and image formats
- **PDF Export**:
  - Use reportlab to recreate certificate design
  - Embed user profile photos (resize if needed)
  - Decorative borders and styling
  - A4 or custom certificate size
- **Image Export**:
  - Use PIL/Pillow to create high-resolution image
  - Render certificate design programmatically
  - Support PNG and JPEG formats
  - Recommended size: 1920x1080 or A4 aspect ratio

### 3. Reports Page Integration (`ui/pages/reports/page.py`)

- **Changes**:
  - Add new tab "top_users_certificate" to tabs list
  - Create certificate component instance
  - Add export buttons (PDF and Image)
  - Use existing filters (group selection, date range)
  - Refresh certificate when filters change

### 4. Locale Updates

- **Files**: `locales/en.json`, `locales/km.json`
- **New keys**:
  - `top_users_certificate`: "Top Users Certificate" / "វិញ្ញាបនបត្រអ្នកប្រើប្រាស់កំពូល"
  - `export_to_image`: "Export to Image" / "នាំចេញទៅរូបភាព"
  - `certificate_title`: "Top Active Users Certificate" / "វិញ្ញាបនបត្រអ្នកប្រើប្រាស់សកម្មកំពូល"
  - `rank`: "Rank" / "ចំណាត់ថ្នាក់"
  - `messages_sent`: "Messages Sent" / "សារដែលបានផ្ញើ"

## Implementation Details

### Certificate Design Elements

1. **Border**: Decorative blue/gold border (similar to honor roll)
2. **Background**: Light blue/white with subtle texture
3. **Header**: 

   - Bilingual title (English + Khmer)
   - Group name
   - Date range (if filtered)

4. **User Display** (5 users, vertical):

   - Profile photo (circular, 80x80px) or gradient avatar with initial
   - Rank badge: "TOP 1", "TOP 2", etc. (blue ribbon style)
   - Full name (bold, large font)
   - Message count (smaller, below name)

5. **Footer**: Date generated, optional signature area

### Data Flow

1. Get top 5 users: `db_manager.get_top_active_users_by_group(group_id, limit=5)`
2. Apply date range filter if provided
3. Sort by message_count descending
4. Display in certificate component
5. Export uses same data to generate PDF/image

### Export Implementation

- **PDF**: Use reportlab with:
  - Custom page size (A4 landscape or portrait)
  - Image embedding for profile photos
  - Decorative elements using reportlab drawing
  - Bilingual text support
- **Image**: Use PIL with:
  - Create blank image (1920x1080 or A4 ratio)
  - Draw decorative borders and background
  - Paste user photos (resized)
  - Draw text (names, ranks, counts)
  - Save as PNG/JPEG

### File Structure

```
ui/components/
  └── top_users_certificate.py (new, ~300 lines)

services/export/exporters/
  └── certificate_exporter.py (new, ~400 lines)

ui/pages/reports/
  └── page.py (modify, add tab and integration)

locales/
  ├── en.json (add new keys)
  └── km.json (add new keys)
```

## Technical Considerations

- Profile photo handling: Check if `profile_photo_path` exists, use PIL to load/resize
- Avatar fallback: Generate gradient avatar with user initial (similar to dashboard)
- Theme support: Certificate should adapt to dark/light theme
- Performance: Cache certificate rendering if possible
- Error handling: Graceful fallback if photos missing, handle export errors

## Dependencies

- Existing: reportlab, Pillow (already in requirements.txt)
- No new dependencies needed

## Testing Checklist

- [ ] Certificate displays correctly with 5 users
- [ ] Handles cases with < 5 users gracefully
- [ ] Profile photos load correctly
- [ ] Avatar fallback works for users without photos
- [ ] Date range filtering works
- [ ] PDF export generates correctly
- [ ] Image export generates correctly
- [ ] Bilingual text displays properly
- [ ] Theme switching works
- [ ] Export file picker works on all platforms

### To-dos

- [ ] Create ui/components/top_users_certificate.py with certificate UI component displaying top 5 users with photos, ranks, names, and message counts
- [ ] Create services/export/exporters/certificate_exporter.py with PDF and image export functionality using reportlab and PIL
- [ ] Add certificate tab to ui/pages/reports/page.py with filters, export buttons, and data refresh logic
- [ ] Add bilingual translation keys for certificate feature to locales/en.json and locales/km.json
- [ ] Test certificate displays correctly with various user counts, profile photos, and theme modes
- [ ] Test PDF and image export functionality with different user data and verify output quality