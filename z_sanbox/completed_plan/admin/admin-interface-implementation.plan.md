Original Prompts:
./admin
Admin features:
- I want ui update firbase app updated (I can maual update status updated app to Firebase)
- I want ui to CRUD licences
- I want ui for Listing all Users Using my app and CRUD
- And please add more other feature for admin.

Note:
- This admin directory will exclude in @build.py 
- This admin will share .venv in development, but may need some more deps ex: adminfirebase

Please plan create modern UI. 

<!-- a4aba2b1-b70e-4a5d-89c2-0f372d719876 99c98700-d562-43b1-b976-5427f682dbf6 -->
# Admin Interface Implementation Plan

## Overview

Create a separate admin interface with modern UI (English only, dark mode only) for managing Firebase users, licenses, app updates, and analytics. Admin uses separate authentication and Firebase Admin SDK for all operations.

## Directory Structure

```
admin/
├── __init__.py
├── main.py                    # Admin entry point
├── config/
│   ├── __init__.py
│   └── admin_config.py        # Admin-specific config (credentials path, etc.)
├── services/
│   ├── __init__.py
│   ├── admin_auth_service.py  # Admin authentication (separate from main app)
│   ├── admin_user_service.py  # User CRUD operations
│   ├── admin_license_service.py # License CRUD operations
│   ├── admin_app_update_service.py # App update management
│   ├── admin_analytics_service.py # Analytics and statistics
│   ├── admin_device_service.py # Device management
│   └── admin_export_service.py # Export reports
├── ui/
│   ├── __init__.py
│   ├── pages/
│   │   ├── __init__.py
│   │   ├── login_page.py      # Admin login page
│   │   ├── dashboard_page.py  # Analytics dashboard
│   │   ├── users_page.py      # User management (CRUD)
│   │   ├── licenses_page.py   # License management (CRUD)
│   │   ├── app_updates_page.py # App update management
│   │   ├── devices_page.py    # Device management
│   │   ├── activity_logs_page.py # Activity logs
│   │   └── bulk_operations_page.py # Bulk operations
│   ├── components/
│   │   ├── __init__.py
│   │   ├── sidebar.py         # Admin navigation sidebar
│   │   ├── user_table.py      # Reusable user table component
│   │   ├── license_table.py   # Reusable license table component
│   │   ├── stats_cards.py     # Statistics cards for dashboard
│   │   └── data_table.py      # Generic data table component
│   └── dialogs/
│       ├── __init__.py
│       ├── user_form_dialog.py # Create/Edit user dialog
│       ├── license_form_dialog.py # Create/Edit license dialog
│       ├── delete_confirm_dialog.py # Delete confirmation with warning
│       ├── app_update_form_dialog.py # App update form
│       └── bulk_operation_dialog.py # Bulk operation dialog
└── utils/
    ├── __init__.py
    └── constants.py           # Admin-specific constants
```

## Implementation Steps

### 1. Admin Configuration and Setup

**Files to create:**

- `admin/config/admin_config.py` - Admin configuration (Firebase credentials path, admin settings)
- `admin/utils/constants.py` - Admin constants (page titles, collection names, etc.)

**Key features:**

- Load Firebase Admin SDK credentials from config
- Admin-specific settings (session timeout, etc.)
- Separate from main app configuration

### 2. Admin Authentication Service

**File:** `admin/services/admin_auth_service.py`

**Features:**

- Separate admin login (not using main app auth)
- Verify admin credentials against Firebase Admin SDK
- Admin session management
- Logout functionality
- Session timeout handling

**Methods:**

- `login(email: str, password: str) -> Tuple[bool, Optional[str]]`
- `logout() -> bool`
- `is_authenticated() -> bool`
- `get_current_admin() -> Optional[dict]`

### 3. Admin Services Layer

**Files to create:**

#### `admin/services/admin_user_service.py`

- `get_all_users() -> List[dict]` - List all Firebase users
- `get_user(uid: str) -> Optional[dict]` - Get user by UID
- `create_user(email: str, password: str, display_name: Optional[str]) -> Optional[str]`
- `update_user(uid: str, **kwargs) -> bool` - Update user (email, display_name, disabled, etc.)
- `delete_user(uid: str) -> bool` - Delete user (with warning)
- `get_user_license(uid: str) -> Optional[dict]` - Get user's license
- `get_user_devices(uid: str) -> List[str]` - Get user's active devices

#### `admin/services/admin_license_service.py`

- `get_all_licenses() -> List[dict]` - List all licenses from Firestore
- `get_license(uid: str) -> Optional[dict]` - Get license by UID
- `create_license(uid: str, license_data: dict) -> bool` - Create new license
- `update_license(uid: str, license_data: dict) -> bool` - Update license
- `delete_license(uid: str) -> bool` - Delete license (with warning)
- `get_license_stats() -> dict` - License statistics (by tier, active/expired, etc.)

#### `admin/services/admin_app_update_service.py`

- `get_app_update_info() -> Optional[dict]` - Get current app update info
- `update_app_update_info(update_data: dict) -> bool` - Update app update info
- `set_update_status(is_available: bool) -> bool` - Enable/disable updates

#### `admin/services/admin_analytics_service.py`

- `get_user_stats() -> dict` - Total users, active users, new users (last 30 days)
- `get_license_stats() -> dict` - License distribution by tier, active/expired counts
- `get_device_stats() -> dict` - Total devices, average devices per user
- `get_activity_stats() -> dict` - Login activity, license renewals, etc.

#### `admin/services/admin_device_service.py`

- `get_all_devices() -> List[dict]` - List all devices across all users
- `get_user_devices(uid: str) -> List[str]` - Get devices for specific user
- `remove_device(uid: str, device_id: str) -> bool` - Remove device from user
- `get_device_stats() -> dict` - Device statistics

#### `admin/services/admin_export_service.py`

- `export_users_to_excel(file_path: str) -> bool` - Export all users to Excel
- `export_licenses_to_excel(file_path: str) -> bool` - Export all licenses to Excel
- `export_analytics_to_pdf(file_path: str) -> bool` - Export analytics report to PDF

### 4. Admin UI Pages

**All pages use dark mode only, English only.**

#### `admin/ui/pages/login_page.py`

- Admin login form (email, password)
- Error handling and validation
- Redirect to dashboard on success

#### `admin/ui/pages/dashboard_page.py`

- Analytics dashboard with statistics cards:
  - Total users, active users, new users (30 days)
  - License distribution (silver/gold/premium)
  - Active vs expired licenses
  - Total devices, average devices per user
- Charts/graphs for trends (if time permits)
- Quick actions (create user, create license, etc.)

#### `admin/ui/pages/users_page.py`

- Data table with all users
- Columns: Email, Display Name, UID, Status (Active/Disabled), License Tier, Actions
- Search and filter functionality
- Actions: View, Edit, Delete (with warning), View License, Manage Devices
- Create new user button
- Pagination for large datasets

#### `admin/ui/pages/licenses_page.py`

- Data table with all licenses
- Columns: User Email, UID, Tier, Expiration Date, Max Devices, Max Groups, Status, Actions
- Search and filter (by tier, status, expiration)
- Actions: View, Edit, Delete (with warning), Renew
- Create new license button
- Pagination

#### `admin/ui/pages/app_updates_page.py`

- Form to update app update information
- Fields: Version, Download URLs (Windows/macOS/Linux), Checksums, File Sizes, Release Date, Release Notes, Is Available
- Preview current update info
- Save button to update Firebase

#### `admin/ui/pages/devices_page.py`

- List all devices across all users
- Columns: User Email, Device ID, Added Date, Actions
- Filter by user
- Actions: Remove Device (with confirmation)
- Device statistics

#### `admin/ui/pages/activity_logs_page.py`

- Activity log table
- Columns: Timestamp, User, Action, Details
- Filter by user, date range, action type
- Export logs to Excel/PDF

#### `admin/ui/pages/bulk_operations_page.py`

- Bulk license updates (change tier, extend expiration, etc.)
- Bulk user operations (enable/disable, assign licenses)
- CSV import for users/licenses
- Progress indicators for bulk operations

### 5. Admin UI Components

#### `admin/ui/components/sidebar.py`

- Navigation sidebar with menu items:
  - Dashboard
  - Users
  - Licenses
  - App Updates
  - Devices
  - Activity Logs
  - Bulk Operations
  - Export Reports
- Logout button
- Current admin info display

#### `admin/ui/components/user_table.py`

- Reusable user data table component
- Sorting, filtering, pagination
- Action buttons (Edit, Delete, etc.)

#### `admin/ui/components/license_table.py`

- Reusable license data table component
- Sorting, filtering, pagination
- Action buttons (Edit, Delete, Renew, etc.)

#### `admin/ui/components/stats_cards.py`

- Statistics card component for dashboard
- Displays metric with icon, value, label, trend indicator

#### `admin/ui/components/data_table.py`

- Generic data table component
- Configurable columns, actions, pagination
- Search and filter support

### 6. Admin Dialogs

#### `admin/ui/dialogs/user_form_dialog.py`

- Create/Edit user form
- Fields: Email, Password (create only), Display Name, Disabled status
- Validation

#### `admin/ui/dialogs/license_form_dialog.py`

- Create/Edit license form
- Fields: User UID/Email, Tier (dropdown), Expiration Date, Max Devices, Max Groups, Max Accounts, Notes
- Validation

#### `admin/ui/dialogs/delete_confirm_dialog.py`

- Delete confirmation dialog with warning
- Shows what will be deleted
- Requires confirmation text input for critical deletions
- Two-step confirmation for user/license deletion

#### `admin/ui/dialogs/app_update_form_dialog.py`

- App update form dialog
- All fields from app update service
- Validation

#### `admin/ui/dialogs/bulk_operation_dialog.py`

- Bulk operation configuration dialog
- Select operation type, target users/licenses, parameters
- Preview and confirm

### 7. Admin Main Application

**File:** `admin/main.py`

**Features:**

- Initialize Firebase Admin SDK
- Set up Flet page (dark mode only)
- Admin authentication check
- Route to login or dashboard
- Navigation between pages
- Session management

### 8. Build Configuration Updates

**File:** `scripts/build.py`

**Changes:**

- Add `'admin'` to `exclude_modules` list (line 513)
- Ensure admin directory is excluded from PyInstaller build

### 9. Dependencies

**File:** `requirements.txt`

**Add:**

- `firebase-admin>=6.2.0` - For admin operations (development only, not in main app build)

**Note:** Admin will share `.venv` but may need additional dependencies. Create `admin/requirements.txt` for admin-specific dependencies if needed.

### 10. File Size Compliance

**Follow repository rules:**

- Service files: < 300 lines (target), < 500 lines (max)
- UI Page files: < 250 lines (target), < 400 lines (max)
- Component files: < 200 lines (target), < 300 lines (max)

**Refactor if files exceed limits:**

- Split large services into smaller modules
- Extract UI components from pages
- Use composition over inheritance

## Security Considerations

1. **Admin Authentication:**

   - Separate from main app authentication
   - Store admin credentials securely (environment variables or encrypted config)
   - Session timeout after inactivity

2. **Firebase Admin SDK:**

   - Credentials file should NOT be committed to git
   - Use environment variables for credentials path
   - Admin operations require authentication

3. **Delete Operations:**

   - Always show warning dialog
   - Require confirmation text input for critical deletions
   - Log all delete operations

4. **Access Control:**

   - Admin interface should only be accessible to authorized admins
   - Consider IP whitelist for production (optional)

## Testing Considerations

1. Test admin login/logout
2. Test all CRUD operations (users, licenses)
3. Test delete operations with warnings
4. Test bulk operations
5. Test export functionality
6. Test app update management
7. Verify admin directory is excluded from builds

## Additional Features

1. **Analytics Dashboard:**

   - Real-time statistics
   - Trend charts (if time permits)
   - Quick action buttons

2. **Device Management:**

   - View all devices
   - Remove devices from users
   - Device statistics

3. **Activity Logs:**

   - Track admin actions
   - User login history
   - License changes
   - Export logs

4. **Bulk Operations:**

   - Bulk license updates
   - Bulk user operations
   - CSV import
   - Progress tracking

5. **Export Reports:**

   - Export users to Excel
   - Export licenses to Excel
   - Export analytics to PDF
   - Custom date ranges

## Notes

- Admin interface is separate from main app
- Uses Firebase Admin SDK (not REST API)
- Dark mode only, English only
- All delete operations require confirmation with warning
- Follow repository file size limits
- Admin directory excluded from builds