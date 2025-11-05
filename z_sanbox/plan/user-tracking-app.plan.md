<!-- 5a51e451-9561-412a-be19-ae0778ab6946 198f47c4-163d-48bb-95db-3655f4df9f8b -->
# Telegram User Tracking Desktop Application

## Architecture Overview

**Desktop App** with Firebase Auth + Local SQLite + Telegram API (Pyrogram)

- Users authenticate via Firebase (requires internet)
- Data stored locally in SQLite
- Flet UI framework for cross-platform desktop (Windows, Mac, Linux)
- Theme color: #082f49

## Project Structure

```
user_tracking/
├── .env.example
├── .env
├── requirements.txt
├── README.md
├── build.py (production build script)
├── main.py (entry point)
├── config/
│   ├── settings.py (app settings management)
│   └── firebase_config.py
├── database/
│   ├── models.py (database schema)
│   ├── db_manager.py (SQLite operations)
│   └── migrations/
├── services/
│   ├── auth_service.py (Firebase authentication)
│   ├── telegram_service.py (Pyrogram integration)
│   ├── export_service.py (PDF/Excel reports)
│   ├── media_service.py (download/manage media)
│   └── connectivity_service.py (internet check)
├── ui/
│   ├── app.py (main Flet app)
│   ├── components/ (reusable UI components)
│   ├── pages/ (login, dashboard, telegram, settings, profile)
│   ├── theme.py (styling, i18n)
│   └── dialogs/ (modals, popups)
├── utils/
│   ├── validators.py
│   ├── helpers.py
│   └── constants.py
└── assets/
    └── icon.png
```

## Database Schema (SQLite)

**Tables:**

1. `app_settings` - Theme, language, download paths, Telegram API keys, delays
2. `telegram_credentials` - Saved login sessions (encrypted phone numbers)
3. `telegram_groups` - Group ID, name, last fetch date
4. `telegram_users` - User ID, username, full name, phone, profile pic path, bio
5. `messages` - Message ID, user ID, group ID, content, date, media paths, link
6. `deleted_messages` - Soft delete tracking by message ID
7. `deleted_users` - Soft delete tracking by user ID
8. `media_files` - File paths, sizes, types, associated message ID

## Implementation Details

### 1. Authentication & Connectivity

- Firebase Admin SDK for user authentication (email/password)
- Single device login enforcement via Firebase
- Continuous internet connectivity monitoring (show banner when offline)
- Telegram OTP flow with 2FA support via Pyrogram

### 2. Settings Page (Task 1)

**Appearance Section:**

- Dark/Light mode toggle
- Language selector (Khmer/English) with i18n
- Corner radius slider for cards/buttons (1-20px)

**Telegram Auth Section:**

- App ID input
- API Hash input
- Phone number (for fetching)
- Test connection button

**Fetch Settings:**

- Root download directory picker
- Toggle: Download media or not
- Max file size slider (MB)
- Delay between requests (seconds)
- Media type checkboxes (photo, video, document, audio)
- Confirmation dialog for directory changes with move option + progress bar

### 3. Telegram Service (Task 2)

**Folder Structure:** `{rootDir}/{group_id}/{username}/{date}/{messageId_time}/`

- `username`: telegram username or sanitized full name (spaces → underscores)
- `date`: YYYY-MM-DD format
- `messageId_time`: e.g., "12345_143022"

**Features:**

- Fetch by date range or specific users
- Rate limiting with configurable delay
- Progress tracking during fetch
- Media download with size limits
- Caption extraction and storage

### 4. UI Pages

**Sidebar (icon-only):**

- Dashboard
- Telegram (messages/users tables)
- Settings
- Profile
- Developer Info/Contact

**Dashboard:**

- Total messages count
- Messages by date (chart)
- Active users count
- Media storage usage
- Recent activity feed
- Group statistics

**Telegram Page (Tabs):**

*Messages Table:*

- Columns: No, UserPic, Full Name, Phone, Message, Date Sent, Media (thumbnail), Actions
- Group selector dropdown (top)
- Date range filter (default: current month)
- Search bar
- Export buttons (PDF, Excel)
- Row click → Detail dialog with CRUD (sender profile, message ID, link, edit/delete)
- Soft delete with tracking

*Users Table:*

- Columns: No, UserPic, Full Name, Phone, Short Bio, Actions
- Row click → User detail dialog with CRUD
- Delete user profile option (re-download on next fetch)
- Soft delete filters out user's messages

**Settings Page:**

- All configurable options organized in sections
- Save/Reset buttons
- Validation with helpful error messages

**Profile Page:**

- Current logged-in user info
- Logout button
- App version
- Developer contact

**Login Page:**

- Email/Password fields
- Remember me checkbox
- Firebase authentication
- Error handling

### 5. Export Features

- **Excel:** xlsxwriter with formatted tables, filters
- **PDF:** ReportLab with company branding, tables, charts

### 6. Build System

**build.py script:**

- PyInstaller configuration for Windows/Mac/Linux
- Custom icon bundling
- Version information
- Developer contact info embedded
- One-command build: `python build.py`

## Technology Stack

- **Python 3.10+**
- **Flet** (UI framework)
- **SQLite3** (database)
- **Pyrogram** (Telegram API)
- **Firebase Admin SDK** (authentication)
- **Pandas** (data manipulation)
- **xlsxwriter** (Excel export)
- **ReportLab** (PDF export)
- **PyInstaller** (building executable)

## Key Features to Implement

1. Internet connectivity checker with auto-reconnect detection
2. Telegram session management (save/load credentials)
3. Progress indicators for long operations (fetch, media download, directory move)
4. Responsive data tables with virtual scrolling for large datasets
5. Image thumbnails in table cells
6. Modern Material Design UI with rounded corners
7. Bilingual support (English/Khmer)
8. Soft delete system to avoid re-fetching deleted items
9. Directory change with optional file migration
10. Rate limiting to avoid Telegram API blocks

## Development Phases

1. Project setup + database schema + Firebase config
2. Authentication system + connectivity monitoring
3. Settings page with all configurations
4. Telegram service integration (Pyrogram)
5. Messages table + CRUD dialogs
6. Users table + CRUD dialogs
7. Dashboard with statistics
8. Export functionality (Excel, PDF)
9. Build system + icon + developer info
10. Testing + refinements

### To-dos

- [ ] Initialize project structure, create requirements.txt with all dependencies, setup .env.example
- [ ] Create SQLite database schema with all tables (settings, credentials, groups, users, messages, soft deletes)
- [ ] Implement Firebase authentication service with single-device enforcement
- [ ] Build internet connectivity monitoring service with UI indicator
- [ ] Create settings page with appearance, Telegram auth, and fetch settings sections
- [ ] Implement Pyrogram integration for fetching messages with OTP flow and rate limiting
- [ ] Build media download service with progress tracking and folder structure management
- [ ] Create messages table UI with filters, search, and detail dialog (CRUD)
- [ ] Create users table UI with filters and detail dialog (CRUD)
- [ ] Build dashboard page with statistics, charts, and activity feed
- [ ] Implement PDF and Excel export functionality with formatting
- [ ] Implement theming system (dark/light), custom corner radius, and bilingual support (English/Khmer)
- [ ] Create build.py script with PyInstaller for cross-platform executables with icon and developer info