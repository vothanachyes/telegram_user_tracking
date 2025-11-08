<!-- 396497f7-f51a-4be4-88a0-ad9c1ee265d3 2359fbae-8647-4251-aaf6-4a80e91492ee -->
# Auto-Login Implementation Plan

## Overview

Add automatic login functionality to the login page when saved credentials are found. The implementation will attempt to authenticate using saved credentials on page load, handle Firebase token expiration and device enforcement, and gracefully show the login form if auto-login fails.

## Current State Analysis

### Existing Functionality

- Login page loads and pre-fills saved credentials (email/password) from database
- Credentials are stored encrypted via `credential_storage`
- "Remember Me" checkbox controls credential persistence
- Device enforcement is checked in `auth_service.login()` (lines 138-144)
- License expiration is checked after login in `_check_license_on_startup()`
- Firebase ID tokens are NOT stored (they expire after ~1 hour, so we authenticate fresh each time)

### What's Missing

- No automatic login attempt when saved credentials are found
- User must manually click "Login" button even when credentials are pre-filled

## Implementation Details

### 1. Add Auto-Login Method to LoginPage

**File**: `ui/pages/login_page.py`

Add a new method `_attempt_auto_login()` that:

- Checks if saved credentials exist (already loaded in `__init__`)
- Shows loading indicator during auto-login attempt
- Calls `auth_service.login()` with saved credentials
- Handles success: calls `on_login_success()` callback
- Handles failure: shows login form with error message (if applicable)
- Runs asynchronously to avoid blocking UI

### 2. Trigger Auto-Login on Page Load

**File**: `ui/pages/login_page.py`

Modify `__init__` or add a lifecycle method to:

- Check if both email and password are available from saved credentials
- If yes, trigger auto-login attempt after a brief delay (to allow UI to render)
- Use `page.run_task()` or `asyncio.create_task()` for async execution

### 3. Handle Error Cases

**File**: `ui/pages/login_page.py`

Auto-login should handle:

- **Invalid credentials**: Show login form with pre-filled fields (user can correct and retry)
- **Token expiration**: Not applicable (we authenticate fresh each time)
- **Device enforcement**: Show error message from `auth_service.login()` (already implemented)
- **Network errors**: Show login form, allow manual retry
- **Firebase not initialized**: Show error, allow manual login

### 4. User Experience Considerations

- Show loading indicator during auto-login (use existing `loading_indicator`)
- Brief delay before auto-login (e.g., 300-500ms) to allow UI to render smoothly
- If auto-login fails, show login form with pre-filled credentials (current behavior)
- Don't show error message for auto-login failures unless it's a specific error (device enforcement, etc.)
- Silent failure is acceptable - user can manually click login button

## Files to Modify

1. **`ui/pages/login_page.py`** (~50-70 lines added)

   - Add `_attempt_auto_login()` method
   - Add auto-login trigger in `__init__` or via lifecycle hook
   - Handle async execution properly

## Implementation Notes

### Token Expiration

- Firebase ID tokens expire after ~1 hour, but we don't store them
- We authenticate fresh each time using email/password via REST API
- No token expiration check needed - Firebase will reject expired tokens automatically

### Device Enforcement & License Checks (AUTOMATIC)

**All checks are automatically performed by `auth_service.login()` method:**

1. **Single-Device Enforcement** (lines 138-144):

   - Checks if user is logged in on another device via Firebase custom claims
   - Returns error: "This account is already logged in on another device..."

2. **Device Limit Check** (lines 146-154):

   - Calls `license_service.can_add_device()` which checks:
     - **Max devices limit** (based on license tier: Bronze=1, Silver=2, Gold=3, Premium=5)
     - **License expiration** (expired licenses are auto-renewed for Bronze tier)
     - **Active devices count** (compares against max_devices)
   - Returns error if device limit reached: "Device limit reached. Maximum X devices allowed..."

3. **License Expiration** (checked in `can_add_device`):

   - Expired Bronze licenses are auto-renewed (grace period)
   - Expired paid tiers are converted to Bronze and renewed
   - License status is also checked after login in `_check_license_on_startup()`

**Since auto-login calls `auth_service.login()`, all these checks happen automatically:**

- ✅ Max device limit enforcement
- ✅ License expiration checking  
- ✅ Single-device enforcement
- ✅ User account status (disabled check)

**No additional code needed** - the existing `login()` method handles everything!

## Testing Considerations

- Test with valid saved credentials → should auto-login
- Test with invalid saved credentials → should show login form
- Test with device enforcement violation → should show error message
- Test with network error → should show login form
- Test with no saved credentials → should show login form normally
- Test with "Remember Me" unchecked → should not auto-login (credentials deleted)

## Code Structure

```python
# In LoginPage.__init__ or new method
async def _attempt_auto_login(self):
    """Attempt to auto-login with saved credentials."""
    saved_email, saved_password = self._load_saved_credentials()
    
    if not saved_email or not saved_password:
        return  # No credentials to use
    
    # Show loading
    self._set_loading(True)
    
    # Initialize auth service
    if not auth_service.initialize():
        self._set_loading(False)
        return  # Silent failure
    
    # Attempt login
    success, error = auth_service.login(saved_email, saved_password)
    
    if success:
        self.on_login_success()
    else:
        # Silent failure - user can manually login
        self._set_loading(False)
        # Optionally show error for specific cases (device enforcement)
        if error and "device" in error.lower():
            self._show_error(error)
```

## Success Criteria

- ✅ Auto-login works when saved credentials exist
- ✅ Loading indicator shows during auto-login
- ✅ Login form appears if auto-login fails
- ✅ Device enforcement errors are shown to user
- ✅ No breaking changes to existing login flow
- ✅ Graceful handling of all error cases

### To-dos

- [x] Add _attempt_auto_login() method to LoginPage class that handles async authentication with saved credentials
- [x] Add auto-login trigger in LoginPage initialization that checks for saved credentials and attempts login
- [ ] Implement error handling for auto-login failures (device enforcement, network errors, invalid credentials)
- [ ] Test auto-login with various scenarios: valid credentials, invalid credentials, device enforcement, network errors