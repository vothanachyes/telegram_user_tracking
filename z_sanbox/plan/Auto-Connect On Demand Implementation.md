<!-- e05eebcb-fd9f-4870-bde6-c71b4cf30af1 49d00e9e-ec00-4a03-8902-f6df50a39e63 -->
# Auto-Connect On Demand Implementation

## Problem

Currently, the app auto-loads a Telegram session on startup, keeping the client connected and pinging the Telegram API every 5 seconds even when idle. This causes unnecessary network traffic and resource usage.

## Solution

Implement connect-on-demand pattern where:

- No auto-connect on app startup
- Client connects only when operations are needed
- Client disconnects after operations complete
- Manual connect/disconnect buttons still work for persistent connections
- Account-specific operations use temporary clients (already implemented)

## Changes Required

### 1. Remove Auto-Load on Startup

**File**: `ui/app.py`

- Remove the auto-load call from `_show_main_app()` method (lines 194-198)
- Keep the method but remove the auto-load logic

### 2. Update Fetch Dialog to Connect On Demand

**File**: `ui/dialogs/fetch_data_dialog.py`

- Remove `auto_load_session()` call from `_try_connect_and_fetch()` (line 533)
- Update `_fetch_messages_async()` to handle connection on demand:
  - If account is selected: use `fetch_messages_with_account()` (already uses temporary client - good)
  - If no account selected: connect temporarily using default account, fetch, then disconnect
- Update connection logic to use temporary client pattern for default account too

### 3. Update TelegramService Methods

**File**: `services/telegram/telegram_service.py`

#### Update `fetch_messages()` method (lines 171-250):

- Remove dependency on persistent `self.client`
- Connect temporarily using default credential if available
- Disconnect after fetch completes
- Use temporary client pattern similar to `fetch_messages_with_account()`

#### Update `fetch_group_info()` method (lines 158-169):

- Remove dependency on persistent `self.client`
- Connect temporarily using default credential if available
- Disconnect after operation completes
- Or update to accept optional credential parameter

### 4. Update Account Status Checks

**File**: `services/telegram/telegram_service.py`

- Verify `get_all_accounts_with_status()` (line 331) already uses temporary clients
- Ensure all status checks use temporary clients (already implemented - verify)

### 5. Keep Manual Connect/Disconnect Working

**Files**: `ui/pages/settings/tabs/authenticate_tab.py`, `ui/pages/settings/handlers.py`

- Manual "Connect" button should still work and keep connection persistent
- Manual "Disconnect" button should disconnect the persistent connection
- These are user-initiated actions, so they should maintain connection until user disconnects

## Implementation Details

### Pattern for Connect-On-Demand:

```python
# Pattern to use in fetch_messages() and fetch_group_info()
temp_client = None
try:
    # Get default credential
    credential = self.db_manager.get_default_credential()
    if not credential:
        return False, 0, "No Telegram account configured"
    
    # Create temporary client
    temp_client = await self._create_temporary_client(credential)
    if not temp_client:
        return False, 0, "Failed to connect or session expired"
    
    # Perform operation with temp_client
    # ...
finally:
    # Always disconnect
    if temp_client:
        await temp_client.disconnect()
```

### Benefits:

- No constant pinging when app is idle
- Reduced network usage
- Better resource management
- Manual connect still available for users who want persistent connection
- Account-specific operations already use temporary clients (no changes needed)

## Testing Checklist

- [ ] App starts without auto-connecting
- [ ] Fetch dialog works with account selection (uses temporary client)
- [ ] Fetch dialog works without account selection (connects on demand, disconnects after)
- [ ] Manual connect button works and stays connected
- [ ] Manual disconnect button works
- [ ] Account status checks work (already use temporary clients)
- [ ] No pinging in logs when app is idle
- [ ] Pinging only occurs during active operations

### To-dos

- [ ] Remove auto-load session call from ui/app.py _show_main_app() method
- [ ] Update fetch_data_dialog.py to connect on demand instead of auto-loading, handle both account-selected and no-account cases
- [ ] Update TelegramService.fetch_messages() to use temporary client pattern instead of persistent client
- [ ] Update TelegramService.fetch_group_info() to use temporary client pattern instead of persistent client
- [ ] Verify manual connect/disconnect buttons still work for persistent connections
- [ ] Test all scenarios: idle app (no pinging), fetch with account, fetch without account, manual connect/disconnect