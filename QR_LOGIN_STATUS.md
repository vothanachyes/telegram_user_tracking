# QR Code Login Status

## Current Status: **COMING SOON** 🚧

QR code login is **visible but disabled** in the UI with a "coming soon" indicator. Users can hover to see it's in development.

## Why QR Code Login Was Disabled

### Root Cause
The Pyrogram library's implementation of QR code login has a fundamental limitation:

1. **Token Expiration Issue**: Each time we call `ExportLoginToken` to check if the user scanned the QR code, Telegram creates a NEW token that expires in ~0.3 seconds
2. **Polling Creates Ephemeral Tokens**: The polling approach (calling `ExportLoginToken` repeatedly) generates many short-lived tokens
3. **Migration Fails**: When user scans → we get `LoginTokenMigrateTo` → but by the time we try `ImportLoginToken`, the token has already expired
4. **No Event Access**: Pyrogram doesn't expose `UpdateLoginToken` events during authentication, which would allow us to react instantly to scans

### What We Tried

1. ✅ **Aggressive polling** (200ms intervals) - Still too slow, tokens expire in 300ms
2. ✅ **Stuck detection** - Prevents infinite loops, shows clear error messages  
3. ✅ **Proper DC migration** - Using `ImportLoginToken` for migrations
4. ✅ **Comprehensive logging** - Full visibility into the flow
5. ❌ **Event-based approach** - Not possible with current Pyrogram architecture

### Test Results

```
Timeline from logs:
- 23:15:47.623 - QR SCAN DETECTED (LoginTokenMigrateTo)
- 23:15:47.728 - Calling ImportLoginToken (105ms later)
- 23:15:47.998 - Response: AUTH_TOKEN_EXPIRED (270ms total)

Result: Token expired before we could import it
```

## Current Implementation: Phone + OTP ✅

**Status**: **WORKING PERFECTLY** ✅

The phone number + OTP login works reliably with:
- ✅ OTP code entry
- ✅ 2FA password support
- ✅ Proper session management
- ✅ Error handling
- ✅ Clean user experience

## Feature Flag

Location: `ui/pages/settings/tabs/authenticate_tab.py`

```python
# Line 50
ENABLE_QR_LOGIN = False  # Feature flag for future implementation
```

**To enable QR code login in the future**: Change `False` to `True`

## Future Solutions

### Option 1: Wait for Pyrogram Update
- **Timeline**: Unknown
- **Effort**: Low (just enable the flag)
- **Risk**: May never happen
- **Recommendation**: Monitor Pyrogram releases

### Option 2: Switch to Telethon
- **Timeline**: 1-2 days development
- **Effort**: Medium (rewrite `client_manager.py`)
- **Risk**: Low (Telethon has proven QR support)
- **Recommendation**: Best option if QR is critical

### Option 3: Direct Telegram API
- **Timeline**: 3-5 days development  
- **Effort**: High (implement raw MTProto)
- **Risk**: High (complex protocol)
- **Recommendation**: Not worth it

## Code Locations

### UI Implementation
- `ui/pages/settings/tabs/authenticate_tab.py` (line 46-72)
  - Feature flag: `ENABLE_QR_LOGIN = False`
  - Shows QR option with 🚧 icon (disabled)
  - Tooltip on hover: "QR Code login coming soon! Currently in development. Use phone login for now."

### Phone Login (Active)
- `services/telegram/client_manager.py` (line 73-148)
  - Method: `start_session()` 
  - Handles phone + OTP + 2FA

### QR Login Code (Preserved)
- Location: Git history
- Branch: Can be recovered from commits
- Status: Fully implemented but not working due to Pyrogram limitations

## Recommendation

**✅ Use phone login** - It's stable, reliable, and works perfectly.

**❌ Don't enable QR** - Not worth the user frustration of "Authorization stuck" errors.

**⏳ Revisit later** - Check Pyrogram updates in 3-6 months, or switch to Telethon if QR becomes critical.

## Support

For questions about this decision, see the detailed conversation logs from November 7, 2025.

---
**Last Updated**: November 7, 2025  
**Decision**: Phone login only (QR disabled)  
**Status**: Production ready ✅

