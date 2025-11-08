<!-- 588eb38e-ad82-4d21-9f86-dd719da1c28b 910dce0a-e017-41fe-9acb-e2523a9ae766 -->
# Firebase User Profile Sync System Implementation

## Overview

Create a new `user_profile` collection in Firestore to manage user information (fullname, email), user status (ACTIVE, DISABLE), and sync flags. Implement automatic syncing every 5 minutes and on fetch operations, with immediate logout for DISABLED users.

## Database Schema Changes

### 1. Firestore Collection: `user_profile`

- **Document ID**: User UID
- **Fields**:
  - `email`: string (read-only, set by admin)
  - `fullname`: string (read-only, set by admin, optional)
  - `user_status`: enum string ("ACTIVE", "DISABLE")
  - `needs_sync`: boolean (indicates Firebase has updates)
  - `last_updated`: timestamp (when profile was last updated in Firebase)
  - `created_at`: timestamp

### 2. Local Database (Optional - No cache per user request)

- No local cache table needed for user_profile
- Continue using existing `user_license_cache` for license data

## Implementation Steps

### 1. Firebase Configuration Updates

**File**: `config/firebase_config.py`

- Add `get_user_profile(uid)` method to fetch user profile from Firestore
- Add `set_user_profile(uid, profile_data)` method to update profile (admin only)
- Add `check_user_status(uid)` method to get current user status
- Add `check_needs_sync(uid)` method to check if sync is needed

### 2. User Profile Model

**File**: `database/models/auth.py` (or new `database/models/user_profile.py`)

- Create `UserProfile` dataclass with:
  - `uid`: str
  - `email`: str
  - `fullname`: Optional[str]
  - `user_status`: str (enum: "ACTIVE", "DISABLE")
  - `needs_sync`: bool
  - `last_updated`: Optional[datetime]

### 3. Sync Service

**File**: `services/sync_service.py` (new)

- Create `SyncService` class with:
  - `sync_user_profile(uid)` - Sync profile from Firebase, update needs_sync to false after success
  - `sync_user_license(uid)` - Sync license data (existing logic)
  - `sync_user_devices(uid)` - Sync device list from Firebase
  - `full_sync(uid)` - Sync all user data (profile, license, devices), update needs_sync to false after all syncs complete
  - Verify sync success before updating needs_sync flag
  - Background sync thread that runs every 5 minutes
  - Integration with fetch operations to trigger sync

### 4. Auth Service Updates

**File**: `services/auth_service.py`

- Update `login()` method to:
  - Check user status after authentication
  - If DISABLED, return error and prevent login
  - Sync user profile on successful login
- Add `check_user_status()` method to verify current user status
- Add `handle_disabled_user()` method to logout and show message

### 5. License Service Updates

**File**: `services/license_service.py`

- Update `sync_from_firebase()` to check `needs_sync` flag first
- Only sync if `needs_sync` is true or cache is stale
- After sync, check if `needs_sync` is false to use cached data

### 6. Profile Page Updates

**File**: `ui/pages/profile_page.py`

- Fetch user fullname from Firebase `user_profile` collection
- Display fullname if available, handle gracefully if not set
- Show user status (ACTIVE/DISABLE) if needed
- Update UI to show syncing status

### 7. Background Sync Thread

**File**: `services/sync_service.py` or `ui/app.py`

- Start background thread on app initialization
- Run `full_sync()` every 5 minutes for logged-in users
- Handle errors gracefully (don't crash app)
- Log sync operations

### 8. Fetch Integration

**File**: `ui/dialogs/fetch_data_dialog.py` or fetch service

- Trigger `full_sync()` before starting fetch operation
- Ensure user status is ACTIVE before allowing fetch
- Show sync status in UI

### 9. User Status Enforcement

**File**: `services/auth_service.py` and `ui/app.py`

- Periodic check (every 1-2 minutes) of user status for logged-in users
- If status changes to DISABLED, immediately:
  - Logout user
  - Show dialog: "Your account has been disabled by admin. Please contact support."
  - Redirect to login page

### 10. Device Sync

**File**: `services/license_service.py` or `services/sync_service.py`

- Sync device list from Firebase `user_licenses.active_device_ids`
- Update local understanding of active devices
- Handle device removal from Firebase (admin cleared devices)

## Files to Modify

1. `config/firebase_config.py` - Add user_profile methods
2. `database/models/auth.py` - Add UserProfile model (or create new file)
3. `services/sync_service.py` - New file for sync logic
4. `services/auth_service.py` - Add status checking and disabled user handling
5. `services/license_service.py` - Update sync logic to respect needs_sync flag
6. `ui/pages/profile_page.py` - Display fullname from user_profile
7. `ui/dialogs/fetch_data_dialog.py` - Trigger sync on fetch start
8. `ui/app.py` - Initialize background sync thread
9. `utils/constants.py` - Add user status enum constants

## Constants to Add

**File**: `utils/constants.py`

```python
USER_STATUS_ACTIVE = "ACTIVE"
USER_STATUS_DISABLE = "DISABLE"
SYNC_INTERVAL_SECONDS = 300  # 5 minutes
USER_STATUS_CHECK_INTERVAL_SECONDS = 120  # 2 minutes
```

## needs_sync Flag Update Logic

- After successful sync of all data (profile, license, devices), update `needs_sync` to `false` in Firebase
- Only update if sync was actually successful (verify data was synced)
- Update happens in `sync_service.py` after `full_sync()` completes successfully
- If update fails, log error but don't block user operations (will retry on next sync)

## Error Handling

- Network failures: Log error, retry on next sync cycle
- Firebase errors: Log error, continue with cached data if available
- Status check failures: Assume ACTIVE to avoid blocking users unnecessarily
- Sync failures: Don't block user operations, log and retry
- needs_sync update failures: Log error, will retry on next sync cycle

## Testing Considerations

- Test with ACTIVE status (normal flow)
- Test with DISABLED status (block login, logout if already logged in)
- Test sync on app startup
- Test sync every 5 minutes
- Test sync on fetch start
- Test network failure scenarios
- Test with missing fullname (should handle gracefully)