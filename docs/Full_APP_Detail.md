# Telegram User Tracking - Complete Application Documentation

## Table of Contents

1. [Project Overview](#project-overview)
2. [Architecture](#architecture)
3. [Technology Stack](#technology-stack)
4. [Features](#features)
5. [Database Schema](#database-schema)
6. [Services & Business Logic](#services--business-logic)
7. [User Interface](#user-interface)
8. [Admin Interface](#admin-interface)
9. [Configuration](#configuration)
10. [Build & Deployment](#build--deployment)
11. [Testing](#testing)
12. [Development Guidelines](#development-guidelines)
13. [Security](#security)
14. [File Structure](#file-structure)

---

## Project Overview

**Telegram User Tracking** is a comprehensive cross-platform desktop application designed for tracking, managing, and analyzing Telegram group messages. The application provides a modern interface for fetching messages from Telegram groups, organizing them in a searchable database, and generating detailed reports.

### Purpose

The application solves the problem of managing large volumes of daily reports from team members in Telegram groups. Instead of scrolling through long chat histories, users can:

- Fetch and store messages in a structured database
- Search, filter, and analyze messages efficiently
- Track user activity and statistics
- Export data to PDF and Excel formats
- Manage multiple Telegram accounts and groups
- Monitor connectivity and handle offline scenarios

### Key Capabilities

- **Multi-Account Support**: Manage multiple Telegram accounts with session persistence
- **Advanced Filtering**: Filter messages by date, user, group, type, tags, and content
- **Media Management**: Automatic download and organization of media files
- **Analytics**: Comprehensive statistics and activity tracking
- **Export Capabilities**: Generate professional PDF and Excel reports
- **Offline Support**: Work with cached data when offline
- **License Management**: Tiered subscription system with device limits
- **Auto-Updates**: Automatic update checking and installation

---

## Architecture

### High-Level Architecture

The application follows a **layered architecture** with clear separation of concerns:

```
┌─────────────────────────────────────────────────────────┐
│                    Presentation Layer                    │
│  (Flet UI - Pages, Components, Dialogs, Navigation)     │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│                    Business Logic Layer                  │
│  (Services - Auth, Telegram, Export, Media, License)    │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│                    Data Access Layer                     │
│  (Database Managers - SQLite Operations)                 │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│                    External Services                     │
│  (Firebase, Telegram API, File System)                  │
└─────────────────────────────────────────────────────────┘
```

### Component Architecture

#### 1. **Main Application** (`main.py` → `ui/app.py`)
- Entry point with single-instance enforcement
- Initializes services and UI
- Handles authentication flow
- Manages application lifecycle

#### 2. **UI Layer** (`ui/`)
- **Pages**: Main application screens (Dashboard, Telegram, Settings, etc.)
- **Components**: Reusable UI elements (Sidebar, Tables, Filters, etc.)
- **Dialogs**: Modal dialogs for confirmations and forms
- **Navigation**: Router-based navigation system
- **Theme**: Centralized theming and internationalization

#### 3. **Service Layer** (`services/`)
- **Auth Service**: Firebase authentication with device enforcement
- **Telegram Service**: Telegram API integration (Telethon)
- **Export Service**: PDF and Excel report generation
- **Media Service**: Media download and management
- **License Service**: Subscription and limit enforcement
- **Update Service**: Automatic update checking and installation
- **Connectivity Service**: Internet connectivity monitoring

#### 4. **Data Layer** (`database/`)
- **Models**: SQLAlchemy-style ORM models
- **Managers**: Domain-specific database managers
- **Schema**: Database schema definitions
- **Migrations**: Database migration scripts

#### 5. **Utilities** (`utils/`)
- **Constants**: Application-wide constants
- **Helpers**: Utility functions
- **Validators**: Input validation
- **Logging**: Centralized logging configuration
- **Encryption**: PIN and credential encryption

### Design Patterns

1. **Singleton Pattern**: Configuration managers, services
2. **Factory Pattern**: Page creation, exporter creation
3. **Strategy Pattern**: Export formatters, data generators
4. **Observer Pattern**: Connectivity monitoring, fetch state
5. **Repository Pattern**: Database managers
6. **Facade Pattern**: Service facades (ExportService, TelegramService)

---

## Technology Stack

### Core Framework
- **Python 3.10+** (supports up to Python 3.13)
- **Flet 0.28.3+** - Cross-platform UI framework (Flutter-based)
  - Desktop support: Windows, macOS, Linux
  - Web mode for debugging

### Database
- **SQLite 3** - Local database storage
- **Pandas 2.1.0+** - Data manipulation and analysis

### Telegram Integration
- **Telethon 1.34.0+** - Telegram API client library
  - Async/await support
  - Session management
  - Media handling

### Authentication & Backend
- **Firebase Admin SDK 6.2.0+** - Server-side authentication
- **Firebase REST API** - Client-side authentication
- **PyJWT 2.8.0+** - JWT token verification
- **Firestore** - Cloud database for licenses and updates

### Export & Reporting
- **xlsxwriter 3.1.9+** - Excel file generation
- **openpyxl 3.1.2+** - Excel file reading/writing
- **ReportLab 4.0.7+** - PDF generation
- **Pillow 10.1.0+** - Image processing
- **qrcode 7.4.2+** - QR code generation

### Security & Encryption
- **cryptography 41.0.5+** - Encryption utilities
- **python-dotenv 1.0.0+** - Environment variable management

### Platform-Specific
- **pywin32 306+** - Windows authentication (Windows only)
- **python-pam 2.0.0+** - Linux authentication (Linux only)

### Build & Distribution
- **PyInstaller 6.1.0+** - Executable creation
- **PyArmor 8.5.0+** - Code obfuscation and protection
- **Inno Setup** - Windows installer creation

### Testing
- **pytest 7.0.0+** - Testing framework
- **pytest-mock 3.10.0+** - Mocking utilities
- **pytest-asyncio 0.21.0+** - Async test support

### Utilities
- **requests 2.31.0+** - HTTP client for REST API calls

---

## Features

### 1. Authentication & Security

#### Firebase Authentication
- Email/password authentication via Firebase REST API
- Single-device enforcement (configurable per license tier)
- Secure credential storage with encryption
- Auto-login with saved credentials
- PIN protection for additional security layer

#### Security Features
- Encrypted password storage
- Encrypted PIN storage (bcrypt-based)
- PIN attempt limiting with lockout
- Secure session management
- Device ID generation and tracking

### 2. Telegram Integration

#### Account Management
- Multiple Telegram account support
- Session persistence (encrypted storage)
- QR code login support
- OTP (One-Time Password) login
- 2FA (Two-Factor Authentication) support
- Account status checking (active/expired)
- Automatic session loading

#### Group Management
- Fetch group information by ID or invite link
- Track multiple groups
- Group statistics (message count, last fetch date)
- Group photo download

#### Message Fetching
- Date range filtering
- User-specific filtering
- Progress tracking with callbacks
- Rate limiting (configurable delays)
- Duplicate detection and skipping
- Message type filtering (text, photo, video, document, audio, sticker, etc.)
- Reaction tracking
- Tag extraction from messages

#### Media Handling
- Automatic media download
- Configurable media types (photos, videos, documents, audio)
- File size limits
- Organized folder structure: `{rootDir}/{group_id}/{username}/{date}/{messageId_time}/`
- Thumbnail generation
- Media file tracking in database

### 3. Data Management

#### Messages
- Full-text search
- Advanced filtering (date, user, group, type, tags, content)
- Pagination for large datasets
- Message details view
- Message editing and deletion (soft delete)
- Message link generation
- Rich content rendering (links, mentions, formatting)

#### Users
- User profile management
- User statistics (message count, activity)
- User search and filtering
- Profile photo display
- User activity tracking
- Soft delete support

#### Groups
- Group list management
- Group statistics
- Group filtering
- Last fetch date tracking

#### Tags
- Automatic tag extraction from messages (#hashtag)
- Tag-based filtering
- Tag analytics (usage statistics)
- Tag autocomplete

### 4. Dashboard & Analytics

#### Statistics
- Total messages count
- Active users count
- Messages by date (chart)
- Group statistics
- Media storage usage
- Recent activity feed

#### User Dashboard
- User-specific statistics
- Message history
- Activity timeline
- Export user data

### 5. Export Capabilities

#### Excel Export
- Messages export with statistics
- Users export
- User data export (messages + stats)
- Formatted worksheets
- Multiple sheets support

#### PDF Export
- Professional report generation
- Messages report
- Users report
- User data report
- Customizable titles and metadata

### 6. Settings & Configuration

#### Appearance
- Dark/Light theme toggle
- Language selection (English/Khmer)
- Corner radius adjustment (1-20px)
- Gradient background animation

#### Telegram Configuration
- API ID and API Hash input
- Account management
- Connection testing

#### Fetch Settings
- Download root directory
- Media download toggle
- Max file size limit
- Fetch delay configuration
- Media type selection (photos, videos, documents, audio)
- Reaction tracking toggle

#### Security Settings
- PIN enable/disable
- PIN change
- PIN recovery (with recovery data)

#### Data Management
- Database backup
- Database restore
- Sample database mode
- Data export/import

### 7. License Management

#### License Tiers
- **Silver**: Basic tier (1 device, 3 groups, 1 account)
- **Gold**: Mid-tier (2 devices, 5 groups, 2 accounts)
- **Premium**: High-tier (unlimited devices, unlimited groups, unlimited accounts)

#### License Features
- Expiration date tracking
- Device limit enforcement
- Group limit enforcement
- Account limit enforcement
- License sync from Firebase
- License status checking

### 8. Update System

#### Auto-Updates
- Automatic update checking
- Update notification toasts
- Download and install updates
- Version comparison
- Platform-specific downloads (Windows, macOS, Linux)
- Checksum verification
- Release notes display

### 9. Connectivity

#### Internet Monitoring
- Continuous connectivity checking
- Offline banner display
- Graceful offline handling
- Connection status indicators

### 10. Admin Interface

#### Admin Features
- User management (create, edit, delete)
- License management (assign, update, expire)
- Device management (view, remove)
- App update management
- Activity logs viewing
- Bulk operations
- Analytics dashboard

---

## Database Schema

### Tables

#### 1. `app_settings`
Application-wide settings (singleton table with id=1).

**Columns:**
- `id` (INTEGER, PRIMARY KEY, DEFAULT 1)
- `theme` (TEXT, DEFAULT 'dark')
- `language` (TEXT, DEFAULT 'en')
- `corner_radius` (INTEGER, DEFAULT 10)
- `telegram_api_id` (TEXT)
- `telegram_api_hash` (TEXT)
- `download_root_dir` (TEXT, DEFAULT './downloads')
- `download_media` (BOOLEAN, DEFAULT 0)
- `max_file_size_mb` (INTEGER, DEFAULT 3)
- `fetch_delay_seconds` (REAL, DEFAULT 5.0)
- `download_photos` (BOOLEAN, DEFAULT 0)
- `download_videos` (BOOLEAN, DEFAULT 0)
- `download_documents` (BOOLEAN, DEFAULT 0)
- `download_audio` (BOOLEAN, DEFAULT 0)
- `track_reactions` (BOOLEAN, DEFAULT 1)
- `reaction_fetch_delay` (REAL, DEFAULT 0.5)
- `pin_enabled` (BOOLEAN, DEFAULT 0)
- `encrypted_pin` (TEXT)
- `created_at` (TIMESTAMP)
- `updated_at` (TIMESTAMP)

#### 2. `telegram_credentials`
Stored Telegram account sessions.

**Columns:**
- `id` (INTEGER, PRIMARY KEY, AUTOINCREMENT)
- `phone_number` (TEXT, UNIQUE, NOT NULL)
- `session_string` (TEXT) - Encrypted session data
- `is_default` (BOOLEAN, DEFAULT 0)
- `last_used` (TIMESTAMP)
- `created_at` (TIMESTAMP)

#### 3. `telegram_groups`
Telegram groups being tracked.

**Columns:**
- `id` (INTEGER, PRIMARY KEY, AUTOINCREMENT)
- `group_id` (INTEGER, UNIQUE, NOT NULL) - Telegram group ID
- `group_name` (TEXT, NOT NULL)
- `group_username` (TEXT)
- `last_fetch_date` (TIMESTAMP)
- `total_messages` (INTEGER, DEFAULT 0)
- `created_at` (TIMESTAMP)
- `updated_at` (TIMESTAMP)

#### 4. `telegram_users`
Telegram users from tracked groups.

**Columns:**
- `id` (INTEGER, PRIMARY KEY, AUTOINCREMENT)
- `user_id` (INTEGER, UNIQUE, NOT NULL) - Telegram user ID
- `username` (TEXT)
- `first_name` (TEXT)
- `last_name` (TEXT)
- `full_name` (TEXT, NOT NULL)
- `phone` (TEXT)
- `bio` (TEXT)
- `profile_photo_path` (TEXT)
- `is_deleted` (BOOLEAN, DEFAULT 0)
- `created_at` (TIMESTAMP)
- `updated_at` (TIMESTAMP)

#### 5. `messages`
Fetched messages from groups.

**Columns:**
- `id` (INTEGER, PRIMARY KEY, AUTOINCREMENT)
- `message_id` (INTEGER, NOT NULL)
- `group_id` (INTEGER, NOT NULL)
- `user_id` (INTEGER, NOT NULL)
- `content` (TEXT)
- `caption` (TEXT)
- `date_sent` (TIMESTAMP, NOT NULL)
- `has_media` (BOOLEAN, DEFAULT 0)
- `media_type` (TEXT)
- `media_count` (INTEGER, DEFAULT 0)
- `message_link` (TEXT)
- `message_type` (TEXT)
- `has_sticker` (BOOLEAN, DEFAULT 0)
- `has_link` (BOOLEAN, DEFAULT 0)
- `sticker_emoji` (TEXT)
- `is_deleted` (BOOLEAN, DEFAULT 0)
- `created_at` (TIMESTAMP)
- `updated_at` (TIMESTAMP)
- **UNIQUE** (`message_id`, `group_id`)
- **FOREIGN KEY** (`group_id`) → `telegram_groups(group_id)`
- **FOREIGN KEY** (`user_id`) → `telegram_users(user_id)`

#### 6. `reactions`
Message reactions.

**Columns:**
- `id` (INTEGER, PRIMARY KEY, AUTOINCREMENT)
- `message_id` (INTEGER, NOT NULL)
- `group_id` (INTEGER, NOT NULL)
- `user_id` (INTEGER, NOT NULL)
- `emoji` (TEXT, NOT NULL)
- `message_link` (TEXT)
- `reacted_at` (TIMESTAMP)
- `created_at` (TIMESTAMP)
- **UNIQUE** (`message_id`, `group_id`, `user_id`, `emoji`)
- **FOREIGN KEY** (`message_id`, `group_id`) → `messages(message_id, group_id)`
- **FOREIGN KEY** (`user_id`) → `telegram_users(user_id)`

#### 7. `media_files`
Downloaded media files.

**Columns:**
- `id` (INTEGER, PRIMARY KEY, AUTOINCREMENT)
- `message_id` (INTEGER, NOT NULL)
- `file_path` (TEXT, NOT NULL)
- `file_name` (TEXT, NOT NULL)
- `file_size_bytes` (INTEGER, NOT NULL)
- `file_type` (TEXT, NOT NULL)
- `mime_type` (TEXT)
- `thumbnail_path` (TEXT)
- `created_at` (TIMESTAMP)
- **FOREIGN KEY** (`message_id`) → `messages(id)`

#### 8. `deleted_messages`
Soft delete tracking for messages.

**Columns:**
- `id` (INTEGER, PRIMARY KEY, AUTOINCREMENT)
- `message_id` (INTEGER, UNIQUE, NOT NULL)
- `group_id` (INTEGER, NOT NULL)
- `deleted_at` (TIMESTAMP)

#### 9. `deleted_users`
Soft delete tracking for users.

**Columns:**
- `id` (INTEGER, PRIMARY KEY, AUTOINCREMENT)
- `user_id` (INTEGER, UNIQUE, NOT NULL)
- `deleted_at` (TIMESTAMP)

#### 10. `login_credentials`
Encrypted Firebase login credentials.

**Columns:**
- `id` (INTEGER, PRIMARY KEY, AUTOINCREMENT)
- `email` (TEXT, UNIQUE, NOT NULL)
- `encrypted_password` (TEXT, NOT NULL)
- `created_at` (TIMESTAMP)
- `updated_at` (TIMESTAMP)

#### 11. `user_license_cache`
Cached license information (synced from Firebase).

**Columns:**
- `id` (INTEGER, PRIMARY KEY, AUTOINCREMENT)
- `user_email` (TEXT, UNIQUE, NOT NULL)
- `license_tier` (TEXT, DEFAULT 'silver')
- `expiration_date` (TIMESTAMP)
- `max_devices` (INTEGER, DEFAULT 1)
- `max_groups` (INTEGER, DEFAULT 3)
- `max_accounts` (INTEGER, DEFAULT 1)
- `max_account_actions` (INTEGER, DEFAULT 2)
- `last_synced` (TIMESTAMP)
- `is_active` (BOOLEAN, DEFAULT 1)
- `created_at` (TIMESTAMP)
- `updated_at` (TIMESTAMP)

#### 12. `account_activity_log`
Log of account add/delete actions.

**Columns:**
- `id` (INTEGER, PRIMARY KEY, AUTOINCREMENT)
- `user_email` (TEXT, NOT NULL)
- `action` (TEXT, NOT NULL) - 'add' or 'delete'
- `phone_number` (TEXT)
- `action_timestamp` (TIMESTAMP)

#### 13. `message_tags`
Extracted tags from messages.

**Columns:**
- `id` (INTEGER, PRIMARY KEY, AUTOINCREMENT)
- `message_id` (INTEGER, NOT NULL)
- `group_id` (INTEGER, NOT NULL)
- `user_id` (INTEGER, NOT NULL)
- `tag` (TEXT, NOT NULL) - Normalized lowercase tag (without #)
- `date_sent` (TIMESTAMP, NOT NULL) - From message.date_sent
- `created_at` (TIMESTAMP)
- **UNIQUE** (`message_id`, `group_id`, `tag`)
- **FOREIGN KEY** (`message_id`, `group_id`) → `messages(message_id, group_id)`
- **FOREIGN KEY** (`user_id`) → `telegram_users(user_id)`

### Indexes

Performance indexes on frequently queried columns:
- `idx_messages_group_id` on `messages(group_id)`
- `idx_messages_user_id` on `messages(user_id)`
- `idx_messages_date_sent` on `messages(date_sent)`
- `idx_messages_deleted` on `messages(is_deleted)`
- `idx_messages_message_type` on `messages(message_type)`
- `idx_media_files_message_id` on `media_files(message_id)`
- `idx_telegram_users_deleted` on `telegram_users(is_deleted)`
- `idx_reactions_message_id` on `reactions(message_id)`
- `idx_reactions_user_id_group_id` on `reactions(user_id, group_id)`
- `idx_message_tags_tag` on `message_tags(tag)`
- `idx_message_tags_group_id` on `message_tags(group_id)`
- `idx_message_tags_user_id` on `message_tags(user_id)`
- `idx_message_tags_date_sent` on `message_tags(date_sent)`
- `idx_message_tags_group_tag` on `message_tags(group_id, tag)`
- `idx_message_tags_user_group_tag` on `message_tags(user_id, group_id, tag)`

---

## Services & Business Logic

### 1. Authentication Service (`services/auth_service.py`)

**Purpose**: Handles Firebase authentication with device enforcement.

**Key Methods:**
- `authenticate_with_email_password(email, password)` - Authenticate via REST API
- `login(email, password, id_token)` - Complete login flow
- `logout()` - Logout current user
- `is_logged_in()` - Check authentication status
- `get_current_user()` - Get current user info

**Features:**
- REST API authentication (no Admin SDK needed in desktop app)
- Device ID generation and tracking
- License limit checking
- Token verification

### 2. Telegram Service (`services/telegram/telegram_service.py`)

**Purpose**: Orchestrates all Telegram API operations.

**Sub-Services:**
- **ClientManager**: Manages Telethon client instances
- **SessionManager**: Handles session creation and loading
- **MessageFetcher**: Fetches messages from groups
- **GroupFetcher**: Fetches group information
- **UserProcessor**: Processes and stores user data
- **MessageProcessor**: Processes and stores message data
- **ReactionProcessor**: Processes and stores reactions
- **AccountStatusChecker**: Checks account validity

**Key Methods:**
- `start_session(phone, api_id, api_hash, ...)` - Start OTP session
- `start_session_qr(api_id, api_hash, ...)` - Start QR code session
- `load_session(credential)` - Load existing session
- `fetch_messages(group_id, start_date, end_date, ...)` - Fetch messages
- `fetch_group_info(group_id, invite_link)` - Fetch group info
- `check_account_status(credential)` - Check account status
- `disconnect()` - Disconnect client

**Features:**
- On-demand connection (connect only when needed)
- Progress callbacks
- Error handling and retry logic
- Rate limiting
- Duplicate detection

### 3. Export Service (`services/export/export_service.py`)

**Purpose**: Facade for exporting data to PDF and Excel.

**Exporters:**
- **MessagesExporter**: Exports messages with statistics
- **UsersExporter**: Exports user lists
- **UserDataExporter**: Exports user-specific data

**Formatters:**
- **ExcelFormatter**: Excel-specific formatting
- **PDFFormatter**: PDF-specific formatting
- **DataFormatter**: Common data formatting

**Key Methods:**
- `export_messages_to_excel(messages, output_path, include_stats)`
- `export_messages_to_pdf(messages, output_path, title, include_stats)`
- `export_users_to_excel(users, output_path)`
- `export_users_to_pdf(users, output_path, title)`
- `export_user_data_to_excel(user, messages, stats, output_path)`
- `export_user_data_to_pdf(user, messages, stats, output_path)`

### 4. Media Service (`services/media_service.py`)

**Purpose**: Manages media file downloads and organization.

**Sub-Services:**
- **MediaDownloader**: Downloads media files
- **MediaManager**: Manages media file records
- **ThumbnailCreator**: Creates thumbnails for images/videos

**Features:**
- Organized folder structure
- File size limits
- Thumbnail generation
- Media type filtering
- Progress tracking

### 5. License Service (`services/license_service.py`)

**Purpose**: Manages user licenses and enforces limits.

**Sub-Services:**
- **LicenseChecker**: Checks license status and validity
- **LicenseSync**: Syncs license data from Firebase
- **LimitEnforcer**: Enforces device/group/account limits

**Key Methods:**
- `get_user_tier(user_email)` - Get license tier
- `check_license_status(user_email, uid)` - Check license status
- `sync_from_firebase(user_email, uid)` - Sync from Firebase
- `can_add_group(user_email, uid)` - Check group limit
- `can_add_device(device_id, user_email, uid)` - Check device limit
- `can_add_account(user_email, uid)` - Check account limit
- `get_license_info(user_email, uid)` - Get full license info

**License Tiers:**
- **Silver**: 1 device, 3 groups, 1 account
- **Gold**: 2 devices, 5 groups, 2 accounts
- **Premium**: Unlimited

### 6. Update Service (`services/update_service.py`)

**Purpose**: Handles automatic application updates.

**Sub-Services:**
- **UpdateChecker**: Checks for available updates
- **UpdateDownloader**: Downloads update files
- **UpdateInstaller**: Installs updates

**Features:**
- Periodic update checking
- Platform-specific downloads
- Checksum verification
- Update notifications
- Background download
- Installer execution

### 7. Connectivity Service (`services/connectivity_service.py`)

**Purpose**: Monitors internet connectivity.

**Features:**
- Continuous connectivity checking
- Callback notifications on status change
- Offline/online state tracking
- Network error handling

### 8. Tag Analytics Service (`services/tag_analytics_service.py`)

**Purpose**: Analyzes tag usage and statistics.

**Features:**
- Tag frequency analysis
- Tag usage by group
- Tag usage by user
- Tag trends over time

### 9. Database Services (`services/database/`)

**Purpose**: Database-level services.

**Services:**
- **EncryptionService**: Field-level encryption
- **FieldEncryptionService**: Encrypts sensitive fields
- **DbMigrationService**: Database migrations

---

## User Interface

### UI Framework: Flet

Flet is a Python framework for building cross-platform applications using Flutter's rendering engine.

### Page Structure

#### 1. Login Page (`ui/pages/login_page.py`)
- Email/password input
- Auto-login with saved credentials
- Splash screen animation
- Error handling

#### 2. Dashboard Page (`ui/pages/dashboard/page.py`)
- Statistics cards
- Charts (messages by date)
- Recent messages list
- Active users list
- Group selector
- Date range selector

#### 3. Telegram Page (`ui/pages/telegram/page.py`)
- **Messages Tab**: Message table with filtering
- **Users Tab**: User table with search
- **Groups Tab**: Group management
- Filter bar (date, user, group, type, tags)
- Export menu
- Pagination

#### 4. User Dashboard Page (`ui/pages/user_dashboard/page.py`)
- User statistics
- Message history
- Activity timeline
- Export options

#### 5. Fetch Data Page (`ui/pages/fetch_data/page.py`)
- Group selection
- Date range selection
- Account selection
- Progress tracking
- Summary display

#### 6. Groups Page (`ui/pages/groups/page.py`)
- Group list
- Add group (by ID or invite link)
- Group statistics
- Delete group

#### 7. Settings Page (`ui/pages/settings/page.py`)
- **General Tab**: Theme, language, corner radius
- **Configure Tab**: Telegram API credentials
- **Authenticate Tab**: Account management
- **Security Tab**: PIN settings
- **Data Tab**: Database backup/restore, sample database

#### 8. Profile Page (`ui/pages/profile_page.py`)
- User information
- License information
- Logout button

#### 9. About Page (`ui/pages/about/page.py`)
- Application information
- License information
- Pricing information
- Developer contact

### UI Components

#### Reusable Components (`ui/components/`)

1. **Sidebar** (`sidebar.py`)
   - Icon-based navigation
   - Current page highlighting
   - Fetch data button

2. **Top Header** (`top_header.py`)
   - App title
   - Fetch indicator
   - Settings button
   - Profile button

3. **Data Table** (`data_table/`)
   - **Table**: Main table component
   - **Pagination**: Page navigation
   - **Filtering**: Advanced filtering
   - **Builders**: Row/cell builders

4. **Filter Bar** (`filter_bar.py`)
   - Date range picker
   - User selector
   - Group selector
   - Type selector
   - Tag autocomplete

5. **Export Menu** (`export_menu.py`)
   - Export to Excel
   - Export to PDF
   - Format selection

6. **Stat Cards** (`stat_cards_grid.py`, `stat_card.py`)
   - Statistics display
   - Icon and value
   - Color themes

7. **Tag Autocomplete** (`tag_autocomplete.py`)
   - Tag search
   - Autocomplete suggestions
   - Tag selection

8. **Toast Notifications** (`toast/`)
   - Success/error/info toasts
   - Positioning system
   - Auto-dismiss

9. **Gradient Background** (`gradient_background.py`)
   - Animated gradient background
   - Theme integration

10. **Splash Screen** (`splash_screen.py`)
    - Loading animation
    - Auto-login integration

### Dialogs (`ui/dialogs/`)

1. **Confirmation Dialog** - Yes/No confirmations
2. **Message Dialog** - Information display
3. **PIN Dialog** - PIN entry
4. **Settings Dialog** - Settings forms
5. **Export Dialog** - Export options
6. **Group Dialog** - Add/edit group
7. **User Dialog** - User details
8. **Message Dialog** - Message details
9. **License Dialog** - License information
10. **Update Dialog** - Update notifications

### Theme System (`ui/theme.py`)

**Theme Manager** provides:
- Dark/Light theme switching
- Color palette management
- Internationalization (i18n)
- Corner radius management
- Gradient background generation

**Supported Languages:**
- English (`locales/en.json`)
- Khmer (`locales/km.json`)

### Navigation (`ui/navigation/`)

**Router** (`router.py`):
- Page routing logic
- Navigation state management
- Page factory integration

**Page Factory** (`page_factory.py`):
- Creates page instances
- Manages page dependencies

---

## Admin Interface

### Admin Application (`admin/main.py`)

Separate admin application for managing users, licenses, and app updates.

### Admin Pages

1. **Login Page** (`admin/ui/pages/login_page.py`)
   - Admin authentication
   - Firebase Admin SDK authentication

2. **Dashboard Page** (`admin/ui/pages/dashboard_page.py`)
   - Overview statistics
   - Recent activity
   - Quick actions

3. **Users Page** (`admin/ui/pages/users_page.py`)
   - User list
   - Create/edit/delete users
   - User details

4. **Licenses Page** (`admin/ui/pages/licenses_page.py`)
   - License list
   - Assign/update licenses
   - Expiration management

5. **Devices Page** (`admin/ui/pages/devices_page.py`)
   - Device list per user
   - Remove devices
   - Device limit management

6. **App Updates Page** (`admin/ui/pages/app_updates_page.py`)
   - Update information
   - Version management
   - Download URL management

7. **Activity Logs Page** (`admin/ui/pages/activity_logs_page.py`)
   - Account activity logs
   - User actions tracking

8. **Bulk Operations Page** (`admin/ui/pages/bulk_operations_page.py`)
   - Bulk license updates
   - Bulk user operations

### Admin Services

1. **Admin Auth Service** (`admin/services/admin_auth_service.py`)
   - Admin authentication
   - Session management

2. **Admin User Service** (`admin/services/admin_user_service.py`)
   - User CRUD operations
   - User management

3. **Admin License Service** (`admin/services/admin_license_service.py`)
   - License management
   - License assignment

4. **Admin Device Service** (`admin/services/admin_device_service.py`)
   - Device management
   - Device removal

5. **Admin App Update Service** (`admin/services/admin_app_update_service.py`)
   - Update management
   - Version control

6. **Admin Export Service** (`admin/services/admin_export_service.py`)
   - Data export
   - Report generation

7. **Admin Analytics Service** (`admin/services/admin_analytics_service.py`)
   - Analytics and statistics
   - Usage reports

---

## Configuration

### Environment Variables

Create a `.env` file in the project root or user data directory:

```env
# Firebase Configuration
FIREBASE_PROJECT_ID=your-project-id
FIREBASE_WEB_API_KEY=your-web-api-key
FIREBASE_CREDENTIALS_PATH=./config/fbsvc-xxxxx.json

# Application Configuration
APP_NAME=Telegram User Tracking
APP_VERSION=1.0.0
DEVELOPER_NAME=Vothana CHY
DEVELOPER_EMAIL=vothanachy.es@gmail.com
DEVELOPER_CONTACT=+85510826027

# Database Configuration
DATABASE_PATH=./data/app.db

# Download Configuration
DEFAULT_DOWNLOAD_DIR=./downloads

# Theme Configuration
PRIMARY_COLOR=#082f49

# Firebase Collections (for Firestore)
FIREBASE_USER_LICENSES_COLLECTION=user_licenses
FIREBASE_APP_UPDATES_COLLECTION=app_updates
FIREBASE_APP_UPDATES_DOCUMENT=latest
```

### Firebase Setup

1. **Create Firebase Project**
   - Go to [Firebase Console](https://console.firebase.google.com/)
   - Create a new project
   - Enable Email/Password authentication

2. **Get Web API Key**
   - Project Settings → General → Web API Key

3. **Download Service Account Credentials**
   - Project Settings → Service Accounts
   - Generate new private key
   - Save as JSON file (e.g., `fbsvc-xxxxx.json`)

4. **Configure Firestore**
   - Create Firestore database
   - Set up security rules (see `docs/FIRESTORE_SECURITY_RULES.md`)
   - Create collections:
     - `user_licenses` (document ID = user UID)
     - `app_updates` (document ID = `latest`)

### Telegram API Setup

1. **Get API Credentials**
   - Visit [Telegram API Development Tools](https://my.telegram.org/apps)
   - Create a new application
   - Get API ID and API Hash

2. **Configure in App**
   - Open Settings → Configure Tab
   - Enter API ID and API Hash
   - Save settings

### Sample Database Mode

Enable sample database mode for testing:

1. Create `config.json` in app data directory:
```json
{
  "sample_db_mode": true
}
```

2. Place sample database at: `{APP_DATA_DIR}/sample_db/app.db`

---

## Build & Deployment

### Local Build

Build executable for current platform:

```bash
python scripts/build.py
```

The executable will be created in `dist/` directory.

### Build Process

1. **Code Obfuscation** (PyArmor)
   - Obfuscates Python code
   - Protects source code

2. **Executable Creation** (PyInstaller)
   - Bundles Python interpreter
   - Includes dependencies
   - Creates single executable

3. **Installer Creation** (Inno Setup - Windows only)
   - Creates Windows installer
   - Includes uninstaller
   - Adds Start Menu shortcuts

### Build Configuration

Edit `scripts/build.py` to configure:
- `USE_PYARMOR`: Enable/disable obfuscation
- `REMOVE_SOURCE_FILES`: Remove source after build
- `USE_INSTALLER`: Create installer (Windows)

### Windows Build from macOS/Linux

Since PyInstaller cannot cross-compile, use **GitHub Actions**:

1. **Manual Trigger**: GitHub Actions → "Build Windows Executable" → "Run workflow"
2. **Automatic Trigger**: Push version tag (e.g., `git tag v1.0.0 && git push origin v1.0.0`)
3. **Download**: Download `.exe` from Artifacts section

See `docs/WINDOWS_BUILD_WORKFLOW.md` for details.

### Distribution

**Windows:**
- Executable: `dist/TelegramUserTracking.exe`
- Installer: `dist/TelegramUserTracking_Setup.exe`

**macOS:**
- App Bundle: `dist/TelegramUserTracking.app`

**Linux:**
- Executable: `dist/TelegramUserTracking`

---

## Testing

### Test Structure

```
tests/
├── conftest.py          # Pytest configuration and fixtures
├── fixtures/            # Test data fixtures
│   ├── sample_db.sql    # Sample database SQL
│   └── ...
├── unit/                # Unit tests
│   ├── test_auth_service.py
│   ├── test_license_service.py
│   └── ...
└── integration/         # Integration tests
    ├── test_login_flow.py
    └── ...
```

### Running Tests

```bash
# Run all tests
pytest tests/

# Run unit tests only
pytest tests/unit/

# Run integration tests only
pytest tests/integration/

# Run specific test file
pytest tests/unit/test_auth_service.py

# Run with coverage
pytest --cov=. tests/
```

### Test Coverage

Current test coverage includes:
- Authentication service (unit + integration)
- License service (unit + integration)
- Database operations
- Login flow (end-to-end)

---

## Development Guidelines

### Code Organization

**File Size Limits:**
- Service files: < 500 lines (target < 300)
- UI Page files: < 400 lines (target < 250)
- Component files: < 300 lines (target < 200)
- Utility files: < 250 lines (target < 150)

**Separation of Concerns:**
- UI: Presentation only
- Services: Business logic
- Database: Data access
- Utils: Helper functions

### Coding Standards

1. **Python 3.10+** with type hints
2. **PEP 8** style guide
3. **f-strings** for string formatting
4. **pathlib.Path** for file operations
5. **async/await** for I/O operations
6. **Error handling** with try-except
7. **Logging** for debugging and monitoring

### Dialog Usage

**ALWAYS use `page.open(dialog)` for opening dialogs:**

```python
# ✅ CORRECT
dialog = MyDialog(on_submit=handle_submit)
dialog.page = page
page.open(dialog)

# ❌ WRONG
page.dialog = dialog
dialog.open = True
page.update()
```

### Error Handling

- Use try-except for all external operations
- Log errors with context
- Show user-friendly error messages
- Never expose stack traces to users

### Logging

- Use Python's logging module
- Log levels: DEBUG, INFO, WARNING, ERROR
- Include context in log messages
- Log to both file and console
- Remove debug logs before committing

### Security

- Never hardcode credentials
- Use environment variables
- Encrypt sensitive data
- Validate user inputs
- Use parameterized queries (SQL injection prevention)

### Git & Version Control

**Do NOT commit:**
- Credentials or API keys
- Firebase config files (if sensitive)
- `data/` directory contents
- `app.log` files
- Build artifacts

**Do commit:**
- Source code
- Configuration templates
- Documentation
- Test files

---

## Security

### Authentication Security

1. **Firebase Authentication**
   - REST API for client-side (no Admin SDK exposure)
   - Admin SDK only for admin interface
   - Token verification
   - Secure credential storage

2. **PIN Protection**
   - Bcrypt-based encryption
   - PIN attempt limiting
   - Lockout after failed attempts
   - Recovery data support

3. **Session Management**
   - Encrypted session storage
   - Secure device ID generation
   - Single-device enforcement (per license tier)

### Data Security

1. **Encryption**
   - Encrypted password storage
   - Encrypted PIN storage
   - Encrypted session strings
   - Field-level encryption for sensitive data

2. **Database Security**
   - SQLite with proper access controls
   - Parameterized queries (SQL injection prevention)
   - Soft delete for data recovery

3. **File Security**
   - Secure user data directory (platform-specific)
   - Encrypted credential storage
   - Protected session files

### Code Protection

1. **PyArmor Obfuscation**
   - Code obfuscation
   - Source code protection
   - Bytecode encryption (if supported)

2. **Build Protection**
   - Remove source files after build
   - Obfuscated bytecode
   - Protected imports

---

## File Structure

### Project Root

```
telegram_user_tracking/
├── main.py                 # Application entry point
├── requirements.txt        # Python dependencies
├── README.md              # Project README
├── config.json            # App configuration (sample DB mode)
│
├── admin/                 # Admin interface
│   ├── main.py
│   ├── config/
│   ├── services/
│   └── ui/
│
├── assets/                # Static assets
│   ├── appLogo.png
│   └── icons/
│
├── config/                # Configuration files
│   ├── app_config.py
│   ├── firebase_config.py
│   └── settings.py
│
├── database/              # Database layer
│   ├── models/           # Data models
│   ├── managers/         # Database managers
│   └── migrations/       # Migration scripts
│
├── data/                 # Application data (not committed)
│   ├── app.db           # SQLite database
│   └── sample_db/      # Sample database
│
├── docs/                 # Documentation
│   ├── Full_APP_Detail.md
│   ├── QUICKSTART.md
│   └── ...
│
├── locales/              # Internationalization
│   ├── en.json
│   └── km.json
│
├── logs/                 # Log files (not committed)
│   ├── database/
│   ├── firebase/
│   └── ...
│
├── scripts/              # Build and utility scripts
│   ├── build.py
│   └── ...
│
├── services/             # Business logic
│   ├── auth_service.py
│   ├── telegram/
│   ├── export/
│   ├── media/
│   ├── license/
│   └── update/
│
├── sessions/             # Telegram sessions (not committed)
│
├── tests/                # Test suite
│   ├── unit/
│   └── integration/
│
├── ui/                   # User interface
│   ├── app.py
│   ├── components/
│   ├── dialogs/
│   ├── pages/
│   ├── navigation/
│   └── theme.py
│
└── utils/                # Utilities
    ├── constants.py
    ├── helpers.py
    ├── validators.py
    └── ...
```

### Key Directories

- **`admin/`**: Separate admin application
- **`config/`**: Configuration management
- **`database/`**: Database models and managers
- **`services/`**: Business logic services
- **`ui/`**: User interface components
- **`utils/`**: Utility functions and helpers
- **`data/`**: Application data (database, sessions)
- **`logs/`**: Log files
- **`docs/`**: Documentation
- **`scripts/`**: Build and utility scripts
- **`tests/`**: Test suite

---

## Additional Resources

### Documentation Files

- `docs/QUICKSTART.md` - Quick start guide
- `docs/WINDOWS_BUILD_WORKFLOW.md` - Windows build instructions
- `docs/FIREBASE_REST_API_MIGRATION.md` - Firebase migration guide
- `docs/FIRESTORE_SECURITY_RULES.md` - Firestore security rules
- `docs/CODE_PROTECTION_GUIDE.md` - Code protection guide
- `docs/TESTING_SINGLE_INSTANCE.md` - Single instance testing
- `docs/auto-update-system-guide.md` - Auto-update system guide

### Configuration Examples

- `.env.example` - Environment variables template
- `config.json` - App configuration example

### Scripts

- `scripts/build.py` - Build script
- `scripts/deploy_update.py` - Update deployment script
- `scripts/decrypt_pin.py` - PIN decryption utility

---

## Version History

- **1.0.0** - Initial release
  - Core features implemented
  - Firebase authentication
  - Telegram integration
  - Export capabilities
  - Admin interface
  - Auto-update system

---

## Support & Contact

**Developer**: Vothana CHY  
**Email**: vothanachy.es@gmail.com  
**Phone**: +85510826027

---

## License

MIT License

---

*This documentation is comprehensive and covers all aspects of the Telegram User Tracking application. For specific implementation details, refer to the source code and inline documentation.*

