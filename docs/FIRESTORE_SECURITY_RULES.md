# Firestore Security Rules

This document describes the Firestore security rules needed for the Telegram User Tracking desktop application.

## Overview

The desktop app uses Firebase REST API with ID token authentication (no Admin SDK). Firestore security rules must be configured to allow users to read their own license data.

## Security Rules

Add these rules to your Firestore database in Firebase Console:

```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    // User licenses - users can only read their own license
    match /user_licenses/{userId} {
      // Allow read if the user is authenticated and the document ID matches their UID
      allow read: if request.auth != null && request.auth.uid == userId;
      // Deny all writes - only admin can write via Admin SDK
      allow write: if false;
    }
    
    // App updates - allow read for authenticated users
    match /app_updates/{document=**} {
      allow read: if request.auth != null;
      // Deny all writes - only admin can write via Admin SDK
      allow write: if false;
    }
    
    // Deny all other collections
    match /{document=**} {
      allow read, write: if false;
    }
  }
}
```

## Deployment

1. Go to Firebase Console → Firestore Database → Rules
2. Paste the rules above
3. Click "Publish"

## Testing

After deploying rules, test that:
- Authenticated users can read their own license (`/user_licenses/{their_uid}`)
- Users cannot read other users' licenses
- Users cannot write to any collection
- Authenticated users can read app updates

## Admin Operations

All write operations (creating licenses, updating licenses, app updates) must be done via:
- Deployment scripts (using Admin SDK)
- Admin panel (if you have one)
- Firebase Console (manual)

The desktop app is **read-only** for security.

## Notes

- The desktop app no longer uses Admin SDK credentials
- All authentication is done via Firebase REST API with ID tokens
- Firestore access uses ID token authentication
- This eliminates the security risk of exposing Admin credentials in the desktop app

