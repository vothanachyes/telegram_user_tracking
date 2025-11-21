# Firebase REST API Migration

## Overview

The desktop application has been refactored to use Firebase REST API instead of Firebase Admin SDK. This eliminates the security risk of exposing Admin credentials in the built executable.

## What Changed

### Before (Admin SDK)
- ❌ Firebase Admin SDK credentials bundled in executable
- ❌ Full Admin access exposed to anyone who extracts the app
- ❌ Security risk: credentials could be extracted and misused

### After (REST API)
- ✅ No Admin SDK credentials in desktop app
- ✅ Uses Firebase REST API with ID token authentication
- ✅ Read-only access to Firestore (users can only read their own license)
- ✅ Write operations are admin-only (via deployment scripts)

## Changes Made

### 1. `config/firebase_config.py`
- Removed Firebase Admin SDK imports
- Added PyJWT for token decoding
- Implemented Firestore REST API client
- All write operations return `False` (admin-only)

### 2. `services/auth_service.py`
- Updated to initialize Firebase with ID token
- Removed Admin SDK calls (set_custom_claims, add_device_to_license)
- Uses token-based authentication

### 3. `services/license/license_sync.py`
- Removed license creation (admin-only)
- Removed auto-renewal (admin-only)
- Now read-only: syncs license data from Firestore to local cache

### 4. `requirements.txt`
- Removed `firebase-admin` (not needed in desktop app)
- Added `PyJWT>=2.8.0` for token decoding
- Admin SDK only needed in deployment scripts

### 5. `scripts/build.py`
- Updated to exclude Firebase credentials from bundle
- Added automatic removal of credentials after build
- Updated messaging about credentials

## What Still Uses Admin SDK

### Deployment Scripts (Correct Usage)
- `scripts/deploy_update.py` - Still uses Admin SDK (correct - it's an admin tool)
- Admin operations should only be done via deployment scripts or admin panel

## Firestore Security Rules

You **must** configure Firestore security rules to allow users to read their own license. See `docs/FIRESTORE_SECURITY_RULES.md` for the rules.

## Migration Steps

1. ✅ Code refactored to use REST API
2. ⚠️ **Deploy Firestore security rules** (see `docs/FIRESTORE_SECURITY_RULES.md`)
3. ✅ Build script updated to exclude credentials
4. ✅ Requirements updated

## Testing

After deploying security rules, test:
- User can login with email/password
- User can read their own license from Firestore
- User cannot read other users' licenses
- User cannot write to Firestore
- License sync works correctly

## Benefits

1. **Security**: No Admin credentials in desktop app
2. **Compliance**: Follows Firebase best practices for client apps
3. **Maintainability**: Clear separation between admin and client operations
4. **Scalability**: Can add backend API later if needed

## Notes

- Device management (adding/removing devices) is now admin-only
- License creation/renewal is now admin-only
- Custom claims (device enforcement) is now admin-only
- These operations should be done via:
  - Deployment scripts (Admin SDK)
  - Admin panel (if you build one)
  - Firebase Console (manual)

## Backward Compatibility

- Existing users will continue to work
- License data structure unchanged
- Local cache format unchanged
- Only the Firebase access method changed

