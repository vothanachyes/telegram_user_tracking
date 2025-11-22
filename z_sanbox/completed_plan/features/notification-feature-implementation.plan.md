Original Prompt:
I want to create notification feature.
- In admin app has CRUD to push notification to all users or specific selected users
- One I push, User app will got badge on notification icon at top right corner, One user click it Will go to page notification, This page  has tabs [All (Admin notification to all), Own (This user notification selected)], one user click on an item will has dialog show notification detail (This action will call firebase api to update read to their notification), (Firebase should has another collection called notification, data in each document only [notification_id, is_read]). This detail can be has image (Similar to Image I passef you). Body of notification can be HTML, RichText, Image, Link, ...

For notification should has a pulic (read only) collection for all users can read from.

- And admin UI, just simple CRUD, can be [title, sutitle, created_at, type, list of users_id, content, ....]

Flow I thought:
- Admin push notitfication
- Each user get list of notifications from public collection they can list, and list their own read notification (to see any readed=> no unread indicator)



<!-- 46de3ee4-7054-4e42-a543-e2e61f42c1a7 7a179ebc-0e1c-4c31-b408-0a1c0e724130 -->
# Notification Feature Implementation Plan

## Overview

Implement a notification system that allows admins to create and manage notifications (broadcast to all users or specific users), and enables users to view notifications with a badge indicator, filter by All/Own tabs, and mark notifications as read.

## Firebase Structure

### 1. Public Notifications Collection

**Collection:** `notifications/{notification_id}`

**Document Structure:**

- `notification_id`: string (auto-generated document ID)
- `title`: string (required)
- `subtitle`: string (optional)
- `content`: string (HTML/Markdown content)
- `image_url`: string (optional, external URL)
- `type`: string (e.g., "info", "warning", "announcement", "update")
- `target_users`: array<string> OR null (null = all users, array = specific user IDs)
- `created_at`: timestamp (Firestore timestamp)
- `created_by`: string (admin UID)
- `expires_at`: timestamp (optional, for future expiration)

### 2. User Read Status Collection

**Collection:** `user_notifications/{user_id}/notifications/{notification_id}`

**Document Structure:**

- `notification_id`: string
- `is_read`: boolean (default: false)
- `read_at`: timestamp (optional, set when marked as read)

### 3. Update Firestore Security Rules

**File:** `docs/FIRESTORE_SECURITY_RULES.md` (update existing rules)

Add rules for notifications:

```javascript
// Public notifications - all authenticated users can read
match /notifications/{notificationId} {
  allow read: if request.auth != null;
  allow write: if false; // Admin only via Admin SDK
}

// User notification read status - users can read/write their own
match /user_notifications/{userId}/notifications/{notificationId} {
  allow read, write: if request.auth != null && request.auth.uid == userId;
}
```

## Admin App - Backend Services

### 4. Create Admin Notification Service

**File:** `admin/services/admin_notification_service.py`

**Methods:**

- `_ensure_initialized()` - Ensure Firebase Admin SDK is initialized
- `create_notification(notification_data: dict) -> bool` - Create new notification
- `get_all_notifications() -> List[dict]` - Get all notifications
- `get_notification(notification_id: str) -> Optional[dict]` - Get single notification
- `update_notification(notification_id: str, data: dict) -> bool` - Update notification
- `delete_notification(notification_id: str) -> bool` - Delete notification
- `get_all_users() -> List[dict]` - Get all users for selection (reuse from admin_user_service)

**Implementation Notes:**

- Use Firebase Admin SDK (similar to `admin_license_service.py`)
- Auto-generate `notification_id` using Firestore document ID
- Set `created_at` to current timestamp
- Set `created_by` from admin auth service
- Handle `target_users: null` for broadcast notifications
- Validate required fields (title, content, type)

### 5. Update Admin Constants

**File:** `admin/utils/constants.py`

Add:

- `PAGE_NOTIFICATIONS = "notifications"`
- `FIRESTORE_NOTIFICATIONS_COLLECTION = "notifications"`
- `FIRESTORE_USER_NOTIFICATIONS_COLLECTION = "user_notifications"`

## Admin App - UI Components

### 6. Create Notification Form Dialog

**File:** `admin/ui/dialogs/notification_form_dialog.py`

**Fields:**

- Title (TextField, required)
- Subtitle (TextField, optional)
- Content (TextField, multiline, required) - Supports HTML/Markdown
- Image URL (TextField, optional)
- Type (Dropdown: "info", "warning", "announcement", "update")
- Target Users (Multi-select dropdown or chips) - "All Users" option + user selection
- Expires At (Date picker, optional)

**Features:**

- Preview content (optional, for HTML rendering)
- User selection with search/filter
- Validation before submit
- Similar structure to `LicenseFormDialog`

### 7. Create Notifications Page

**File:** `admin/ui/pages/notifications_page.py`

**Features:**

- Data table showing: Title, Subtitle, Type, Target (All/Specific), Created At, Actions
- Create button (opens NotificationFormDialog)
- Edit action (opens NotificationFormDialog with data)
- Delete action (opens DeleteConfirmDialog)
- Filter/search by title, type, target
- Similar structure to `AdminLicensesPage`

### 8. Update Admin Sidebar

**File:** `admin/ui/components/sidebar.py`

Add navigation item for Notifications page with icon `ft.Icons.NOTIFICATIONS`

### 9. Update Admin Main Router

**File:** `admin/main.py`

- Add import for `AdminNotificationsPage`
- Add case in `_create_page_content()` for `PAGE_NOTIFICATIONS`
- Add route constant

### 10. Update Admin Dialogs Init

**File:** `admin/ui/dialogs/__init__.py`

Add export for `NotificationFormDialog`

## User App - Backend Services

### 11. Create Notification Service

**File:** `services/notification_service.py`

**Methods:**

- `get_notifications(user_id: str) -> Tuple[List[dict], List[dict]]` - Returns (all_notifications, user_specific_notifications)
  - Fetch from `notifications` collection
  - Filter: `target_users == null OR user_id in target_users`
  - Separate into "All" (broadcast) and "Own" (user-specific)
- `get_unread_count(user_id: str) -> int` - Count unread notifications
  - Get all relevant notifications
  - Get read statuses from `user_notifications/{user_id}/notifications`
  - Count where notification exists but not read
- `mark_as_read(user_id: str, notification_id: str) -> bool` - Mark notification as read
  - Create/update document in `user_notifications/{user_id}/notifications/{notification_id}`
  - Set `is_read: true`, `read_at: timestamp`
  - Use Firebase REST API (similar to `firebase_config.get_user_license()`)
- `get_read_statuses(user_id: str) -> Dict[str, bool]` - Get all read statuses for user
  - Fetch all documents from `user_notifications/{user_id}/notifications`
  - Return dict mapping `notification_id -> is_read`

**Implementation Notes:**

- Use Firebase REST API (not Admin SDK) - similar to `firebase_config.py`
- Handle pagination for large notification lists
- Cache read statuses locally to reduce API calls
- Handle network errors gracefully

### 12. Extend Firebase Config

**File:** `config/firebase_config.py`

Add methods:

- `get_notifications(id_token: Optional[str] = None) -> List[dict]` - Get all notifications
- `get_user_notification_status(user_id: str, notification_id: str, id_token: Optional[str] = None) -> Optional[dict]` - Get read status
- `mark_notification_read(user_id: str, notification_id: str, id_token: Optional[str] = None) -> bool` - Mark as read
- `get_user_notification_statuses(user_id: str, id_token: Optional[str] = None) -> Dict[str, bool]` - Get all statuses

**Implementation:**

- Use Firestore REST API endpoints
- Convert Firestore document format using existing `_convert_firestore_document()` method
- Handle query parameters for filtering (`target_users == null OR user_id in target_users`)

## User App - UI Components

### 13. Update Top Header Component

**File:** `ui/components/top_header.py`

**Changes:**

- Add notification icon button (bell icon) with badge
- Badge shows unread count (red circle with number)
- Click navigates to notifications page
- Update badge periodically (polling every 30-60 seconds)
- Add method `update_notification_badge()` to refresh count
- Similar to existing `update_fetch_indicator()` pattern

**Implementation:**

- Use `ft.IconButton` with `ft.Badge` or `ft.Stack` for badge overlay
- Call `notification_service.get_unread_count()` to get count
- Store badge reference for updates

### 14. Create Notifications Page

**File:** `ui/pages/notifications/page.py`

**Structure:**

- Header with title
- Tabs: "All" (broadcast notifications) and "Own" (user-specific)
- List view with notification cards
- Each card shows: Title, Subtitle, Date, Type badge, Unread indicator
- Click card opens detail dialog
- Empty state when no notifications

**Features:**

- Tab switching (All/Own)
- Notification cards with preview
- Unread indicator (dot or badge)
- Date formatting
- Type color coding

### 15. Create Notification Detail Dialog

**File:** `ui/dialogs/notification_detail_dialog.py`

**Content:**

- Title (large, bold)
- Subtitle (if exists)
- Image (if `image_url` exists, use `ft.Image`)
- Content (render HTML/Markdown using `ft.Markdown` or `ft.Html`)
- Date and type badge
- Close button

**Behavior:**

- On open, automatically call `mark_as_read()`
- Update badge count after marking as read
- Handle image loading errors gracefully
- Support HTML content rendering (may need WebView for full HTML)

### 16. Update Router

**File:** `ui/navigation/router.py`

- Add "notifications" page ID
- Add case in page factory/router to create NotificationsPage
- Handle navigation to notifications page

### 17. Update Page Factory

**File:** `ui/navigation/page_factory.py`

Add factory method for creating NotificationsPage instance

### 18. Update Sidebar (Optional)

**File:** `ui/components/sidebar.py`

Optionally add navigation item for notifications (or rely on header icon only)

## Localization

### 19. Update Locale Files

**Files:** `locales/en.json`, `locales/km.json`

Add translations:

- "notifications" / "Notifications"
- "notification" / "Notification"
- "all_notifications" / "All Notifications"
- "my_notifications" / "My Notifications"
- "mark_as_read" / "Mark as Read"
- "unread" / "Unread"
- "read" / "Read"
- "notification_type_info" / "Info"
- "notification_type_warning" / "Warning"
- "notification_type_announcement" / "Announcement"
- "notification_type_update" / "Update"
- "no_notifications" / "No Notifications"
- "notification_detail" / "Notification Detail"
- "created_at" / "Created At"
- "target_all_users" / "All Users"
- "target_specific_users" / "Specific Users"

## Testing Considerations

- Test notification creation (all users vs specific users)
- Test read status tracking (mark as read, verify in Firebase)
- Test badge count calculation (unread notifications)
- Test tab filtering (All vs Own)
- Test HTML/Markdown content rendering
- Test image loading (valid URL, invalid URL, missing image)
- Test empty states (no notifications, no unread)
- Test network errors (offline, API failures)
- Test pagination for large notification lists
- Test notification expiration (if implemented)

## File Structure Summary

**New Files:**

- `admin/services/admin_notification_service.py`
- `admin/ui/pages/notifications_page.py`
- `admin/ui/dialogs/notification_form_dialog.py`
- `services/notification_service.py`
- `ui/pages/notifications/page.py`
- `ui/dialogs/notification_detail_dialog.py`

**Modified Files:**

- `docs/FIRESTORE_SECURITY_RULES.md` (add notification rules)
- `admin/utils/constants.py` (add notification constants)
- `admin/ui/components/sidebar.py` (add notifications nav item)
- `admin/main.py` (add notifications route)
- `admin/ui/dialogs/__init__.py` (export NotificationFormDialog)
- `config/firebase_config.py` (add notification REST API methods)
- `ui/components/top_header.py` (add notification icon with badge)
- `ui/navigation/router.py` (add notifications route)
- `ui/navigation/page_factory.py` (add notifications page factory)
- `locales/en.json` (add translations)
- `locales/km.json` (add translations)

### To-dos

- [ ] Update Firestore security rules to allow read access to notifications collection and read/write access to user_notifications collection
- [ ] Create AdminNotificationService with CRUD operations using Firebase Admin SDK
- [ ] Create NotificationFormDialog with fields for title, subtitle, content (HTML/Markdown), image URL, type, target users, and expiration
- [ ] Create AdminNotificationsPage with data table, create/edit/delete actions, and filters
- [ ] Add notifications navigation item to admin sidebar and update main router
- [ ] Extend FirebaseConfig with REST API methods for getting notifications, getting read statuses, and marking notifications as read
- [ ] Create NotificationService with methods to get notifications (All/Own), get unread count, mark as read, and get read statuses
- [ ] Add notification icon with badge to TopHeader component, implement badge count updates, and navigation to notifications page
- [ ] Create NotificationsPage with All/Own tabs, notification cards list, and empty states
- [ ] Create NotificationDetailDialog to display full notification content (HTML/Markdown, images), automatically mark as read on open
- [ ] Add notifications route to user app router and page factory
- [ ] Add notification-related translations to en.json and km.json locale files