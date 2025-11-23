<!-- b9455684-c160-4591-bb33-3bf87a7da48a bc293810-24ae-4ed7-b9ce-afc62dfe5979 -->
# User Activities Tracking System Implementation Plan

## Overview

Implement a comprehensive user activity tracking system that stores user activities in Firebase, manages device information, enables device revocation with auto-logout, and provides both client and admin interfaces for device management.

## Architecture

### Firebase Collections Structure

1. **`user_activities/{uid}`** - Main user activity document

   - `total_devices_logged_on` (number)
   - `total_telegram_accounts_authenticated` (number)
   - `total_telegram_groups_added` (number)
   - `current_app_version` (string)
   - `is_blocked` (boolean) - Blocked for excessive account add/delete
   - `blocked_reason` (string, optional)
   - `blocked_at` (timestamp, optional)
   - `last_updated` (timestamp)
   - `created_at` (timestamp)

2. **`user_licenses/{uid}/user_devices/{device_id}`** - Device subcollection

   - `device_id` (string)
   - `device_name` (string) - e.g., "Windows PC", "MacBook Pro"
   - `platform` (string) - "Windows", "macOS", "Linux"
   - `last_login` (timestamp)
   - `first_login` (timestamp)
   - `is_active` (boolean)
   - `revoked_at` (timestamp, optional)

## Implementation Steps

### Phase 1: Firebase Structure & Services

#### 1.1 Update Firebase Config (Client)

**File**: `config/firebase_config.py`

- Add `get_user_activities(uid)` - Read user activities from Firestore
- Add `update_user_activities(uid, updates)` - Update activities (client can only update certain fields)
- Add `get_user_devices(uid)` - Get all devices from subcollection
- Add `add_user_device(uid, device_id, device_info)` - Add device info
- Add `remove_user_device(uid, device_id)` - Remove device (admin only)
- Add `check_device_revoked(uid, device_id)` - Check if device is revoked

#### 1.2 Create User Activities Service (Client)

**File**: `services/user_activities_service.py` (new, ~200 lines)

- `sync_activities_to_firebase()` - Sync local counts to Firebase
- `increment_devices_count()` - Track device login
- `increment_accounts_count()` - Track Telegram account authentication
- `increment_groups_count()` - Track group addition
- `update_app_version()` - Update current app version
- `check_if_blocked()` - Check if user is blocked
- `get_activities()` - Get current activities

#### 1.3 Create Device Manager Service (Client)

**File**: `services/device_manager_service.py` (new, ~150 lines)

- `register_device()` - Register current device with Firebase
- `get_all_devices()` - Get all user's devices from Firebase
- `revoke_device(device_id)` - Revoke own device (remove from active_devices)
- `check_device_status()` - Check if current device is revoked
- `get_device_info()` - Get current device info (name, platform)

### Phase 2: Activity Tracking Integration

#### 2.1 Track Device Logins

**File**: `services/auth_service.py`

- In `login()` method: After successful login, call `user_activities_service.increment_devices_count()`
- Register device with `device_manager_service.register_device()`
- Check if device is revoked before allowing login

#### 2.2 Track Telegram Account Authentication

**File**: `services/telegram/session_manager.py`

- In `start_session()` and `start_session_qr()`: After successful authentication, call `user_activities_service.increment_accounts_count()`

#### 2.3 Track Group Addition

**File**: `database/managers/group_manager.py` or `services/telegram/message_fetcher.py`

- When group is saved: Call `user_activities_service.increment_groups_count()`

#### 2.4 Track App Version

**File**: `services/user_activities_service.py`

- On app startup (if logged in): Call `update_app_version()` with `APP_VERSION` from constants

### Phase 3: Device Revocation & Auto-Logout

#### 3.1 Periodic Device Status Check

**File**: `services/device_manager_service.py`

- Add background task that checks device status every 5 minutes
- If device is revoked, trigger auto-logout

#### 3.2 Auto-Logout on Revocation

**File**: `ui/app.py` or create `services/device_revocation_handler.py` (~100 lines)

- Listen for device revocation events
- Show notification: "Your device has been revoked. Logging out..."
- Call `auth_service.logout()`
- Redirect to login page

#### 3.3 Check Before Critical Operations

**Files**: Multiple service files

- `services/auth_service.py` - Check before login
- `services/telegram/message_fetcher.py` - Check before fetch
- `ui/dialogs/fetch_data_dialog.py` - Check before fetch dialog

### Phase 4: Client UI - Device Management

#### 4.1 Create Devices Tab Component

**File**: `ui/pages/settings/tabs/devices_tab/page.py` (new, ~250 lines)

- Display list of all user's devices
- Show: Device name, platform, last login, status (Active/Revoked)
- "Revoke" button for each device (except current device)
- Refresh button to reload devices
- Empty state when no devices

#### 4.2 Add Devices Tab to Settings

**File**: `ui/pages/settings/page.py`

- Add "Devices" tab to settings page
- Integrate `DevicesTab` component

#### 4.3 Device Revocation Dialog

**File**: `ui/dialogs/revoke_device_dialog.py` (new, ~100 lines)

- Confirmation dialog for device revocation
- Show device info before revoking
- Handle revocation and refresh list

### Phase 5: Admin Services

#### 5.1 Admin User Activities Service

**File**: `admin/services/admin_user_activities_service.py` (new, ~200 lines)

- `get_user_activities(uid)` - Get user activities
- `get_all_activities()` - Get all users' activities
- `block_user(uid, reason)` - Block user for excessive account operations
- `unblock_user(uid)` - Unblock user
- `get_blocked_users()` - Get all blocked users
- `get_activities_stats()` - Get statistics

#### 5.2 Admin Device Service Updates

**File**: `admin/services/admin_device_service.py`

- Update `get_all_devices()` to include device info from subcollection
- Update `remove_device()` to:
  - Remove from `active_devices` array in license
  - Mark device as revoked in `user_devices` subcollection
  - Set `revoked_at` timestamp
- Add `get_user_devices_with_info(uid)` - Get devices with full info

### Phase 6: Admin UI - User Activities Page

#### 6.1 Create User Activities Page

**File**: `admin/ui/pages/user_activities_page.py` (new, ~300 lines)

- Data table showing:
  - User Email
  - Total Devices
  - Total Accounts
  - Total Groups
  - App Version
  - Status (Active/Blocked)
  - Actions (View Details, Unblock if blocked)
- Search and filter functionality
- View details dialog showing full activity info

#### 6.2 Update Devices Page

**File**: `admin/ui/pages/devices_page.py`

- Add columns: Device Name, Platform, Last Login
- Show device info from subcollection
- Improve device removal to mark as revoked

#### 6.3 Add Navigation

**File**: `admin/ui/components/sidebar.py`

- Add "User Activities" menu item
- Link to new `user_activities_page.py`

### Phase 7: Account Activity Blocking Integration

#### 7.1 Check Block Status Before Account Operations

**File**: `database/managers/account_activity_manager.py`

- In `can_perform_account_action()`: Check if user is blocked in Firebase
- Return appropriate error if blocked

#### 7.2 Auto-Block on Threshold

**File**: `services/user_activities_service.py` or create `services/account_blocking_service.py` (~150 lines)

- After logging account action: Check if threshold exceeded
- If exceeded: Call admin service to block user (or set flag in Firebase)
- Note: Client can only set flag, admin confirms block

#### 7.3 Admin Unblock Functionality

**File**: `admin/services/admin_user_activities_service.py`

- `unblock_user(uid)` - Remove block flag and reason
- Update `user_activities` document

## Data Flow

### Device Registration Flow

1. User logs in → `auth_service.login()`
2. Check if device exists in Firebase
3. If new: Register device with info (name, platform, timestamp)
4. Add device_id to `active_devices` array (admin operation, but can be done via client on first login)
5. Increment `total_devices_logged_on` in `user_activities`

### Device Revocation Flow

1. Admin revokes device → `admin_device_service.remove_device()`
2. Remove from `active_devices` array
3. Mark device as revoked in `user_devices` subcollection
4. Client checks device status (periodic or on-action)
5. If revoked: Auto-logout user

### Activity Tracking Flow

1. User performs action (login, add account, add group)
2. Local service increments counter
3. Sync to Firebase `user_activities` collection
4. Admin views activities in admin panel

## Security Considerations

- Client can only read/write their own `user_activities` document
- Client can only read their own `user_devices` subcollection
- Only admin can revoke devices and block users
- Device revocation check happens before critical operations
- Firestore security rules must be updated

## Firestore Security Rules

Add to Firestore security rules:

```javascript
// User activities - users can read/write their own
match /user_activities/{uid} {
  allow read, write: if request.auth != null && request.auth.uid == uid;
}

// User devices - users can read their own, write only if not revoked
match /user_licenses/{uid}/user_devices/{deviceId} {
  allow read: if request.auth != null && request.auth.uid == uid;
  allow write: if request.auth != null && request.auth.uid == uid 
    && !resource.data.get('revoked_at', null);
}
```

## Files to Create

1. `services/user_activities_service.py` (~200 lines)
2. `services/device_manager_service.py` (~150 lines)
3. `services/device_revocation_handler.py` (~100 lines)
4. `ui/pages/settings/tabs/devices_tab/page.py` (~250 lines)
5. `ui/dialogs/revoke_device_dialog.py` (~100 lines)
6. `admin/services/admin_user_activities_service.py` (~200 lines)
7. `admin/ui/pages/user_activities_page.py` (~300 lines)

## Files to Modify

1. `config/firebase_config.py` - Add methods for activities and devices
2. `services/auth_service.py` - Track device login, check revocation
3. `services/telegram/session_manager.py` - Track account authentication
4. `database/managers/group_manager.py` - Track group addition
5. `admin/services/admin_device_service.py` - Update device removal
6. `admin/ui/pages/devices_page.py` - Show device info
7. `admin/ui/components/sidebar.py` - Add navigation
8. `ui/pages/settings/page.py` - Add devices tab
9. `database/managers/account_activity_manager.py` - Check block status

## Testing Considerations

- Test device registration on first login
- Test device revocation and auto-logout
- Test activity tracking increments
- Test admin blocking/unblocking
- Test client device management UI
- Test periodic device status checks
- Test app version tracking

## Migration Notes

- Existing users: Initialize `user_activities` document on first login
- Existing devices: Migrate device IDs to `user_devices` subcollection with basic info
- No breaking changes to existing functionality