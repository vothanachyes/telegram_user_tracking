# Telegram Rate Limits and Safety Guide

## Table of Contents

1. [Overview](#overview)
2. [2025 Rate Limits](#2025-rate-limits)
3. [Account Safety Measures](#account-safety-measures)
4. [Proxy Usage](#proxy-usage)
5. [Implementation Guidelines](#implementation-guidelines)
6. [Error Handling](#error-handling)
7. [Best Practices](#best-practices)
8. [Code Examples](#code-examples)
9. [Troubleshooting](#troubleshooting)

---

## Overview

This guide provides comprehensive information about Telegram's rate limits, restrictions, and safety measures when adding users to groups using Telethon. **Following these guidelines is critical to prevent your Telegram account from being blocked or disabled.**

### ⚠️ Critical Warning

**Violating Telegram's rate limits or engaging in spam-like behavior can result in:**
- Temporary account restrictions (24-48 hours)
- Permanent account bans
- IP address blocking
- Device fingerprinting and tracking

**Always use non-official accounts for testing and development.**

---

## 2025 Rate Limits

### Official Telegram Limits (Updated November 2025)

#### Daily Limits
- **Maximum Manual Additions**: Up to **200 members per day** per admin account
- **Recommended Safe Limits**:
  - New accounts (< 30 days): **20-50 users/day**
  - Established accounts (30-90 days): **50-100 users/day**
  - Very old accounts (> 90 days): **100-200 users/day** (Telegram's maximum)

#### Hourly Limits
- **Maximum Safe**: **10 users per hour**
- **Minimum Delay**: **30 seconds** between each addition
- **Recommended**: **5-10 users per hour** for safety

#### Per-Request Limits
- **Minimum Delay**: 30 seconds between additions
- **Contact Wait**: 2 minutes after adding user to contacts (for phone number invites)
- **FloodWait Compliance**: Always wait the full duration specified in `FloodWaitError`

### Account Age Considerations

Telegram applies different limits based on account age:

| Account Age | Recommended Daily Limit | Notes |
|------------|------------------------|-------|
| < 7 days | 10-20 users/day | Very new accounts - use extreme caution |
| 7-30 days | 20-50 users/day | New accounts - build activity history |
| 30-90 days | 50-100 users/day | Established accounts - moderate limits |
| > 90 days | 100-200 users/day | Old accounts - can use higher limits |

---

## Account Safety Measures

### 1. Account Warming (Critical for New Accounts)

**New accounts (< 30 days) should:**

1. **Wait Period**: Wait 7-14 days before bulk operations
2. **Build Activity History**:
   - Send messages to contacts
   - Join public channels
   - Browse content
   - Interact with groups naturally
3. **Progressive Limits**: Start with 10/day, gradually increase over weeks
4. **Avoid Automation**: Mix manual and automated actions

### 2. Privacy Settings Handling

#### Adding Users by Username
- ✅ Direct addition possible if user allows it
- ❌ May fail if user has privacy restrictions
- **Error**: `PrivacyRestrictedError` or `UserPrivacyError`

#### Adding Users by Phone Number
- ✅ **Must add to contacts first** (required by Telegram)
- ✅ Wait 2 minutes after adding to contacts
- ✅ Then invite to group
- ✅ Optionally remove from contacts after (if desired)

### 3. Group Permissions

**Required Permissions:**
- Account must be **admin** of the group
- Must have **"Add Members"** permission enabled
- Group must not be at member limit

**Group Type Differences:**
- **Regular Groups**: Use `AddChatUserRequest`
- **Channels/Supergroups**: Use `InviteToChannelRequest`

### 4. Anti-Spam Detection Avoidance

**Avoid These Behaviors:**
- ❌ Adding many users in rapid succession
- ❌ Adding users who don't know you
- ❌ Adding users who immediately leave
- ❌ Using account only for adding users (no other activity)
- ❌ Adding users to multiple groups rapidly
- ❌ Adding users without their consent

**Best Practices:**
- ✅ Mix adding users with normal account activity
- ✅ Add users who have shown interest
- ✅ Space operations over hours/days
- ✅ Use accounts with normal activity history
- ✅ Monitor success/failure rates

---

## Proxy Usage

### Should You Use a Proxy?

**Short Answer:** Proxies can help, but they are **NOT a replacement** for following rate limits and best practices. Use them **carefully** and only with **high-quality proxies**.

### When to Use Proxies

✅ **Consider using proxies if:**
- You're adding users from multiple accounts
- Your IP address has been flagged/blocked by Telegram
- You need to distribute requests across different IPs
- You're operating from a region with Telegram restrictions
- You want additional layer of protection for your main IP

❌ **Do NOT rely on proxies to:**
- Bypass rate limits (they don't)
- Avoid account bans (they won't prevent behavior-based bans)
- Replace proper rate limiting and delays
- Use low-quality or free proxies (they're often already flagged)

### Proxy Risks and Considerations

#### ⚠️ Critical Risks

1. **Flagged IP Addresses**: Many free/public proxies are already flagged by Telegram
   - Using a flagged proxy can **increase** your risk of being banned
   - Telegram tracks IP reputation and may restrict accounts using known bad IPs

2. **Frequent IP Switching**: Rapidly switching IPs can look suspicious
   - Telegram may flag accounts that frequently change IPs
   - Use the same proxy/IP for extended periods when possible

3. **Proxy Quality Matters**: Low-quality proxies can cause:
   - Connection instability
   - Slower response times
   - Higher chance of detection
   - Account restrictions

4. **Geographic Inconsistency**: Using proxies from different countries than your account location can be suspicious
   - If your account is registered in Country A, using proxies from Country B may raise flags
   - Try to use proxies from the same region as your account

### Proxy Best Practices

#### 1. Use High-Quality Proxies

**Recommended Proxy Types:**
- **Residential Proxies**: Best choice (appear as real user IPs)
- **Dedicated Proxies**: Good for single account use
- **Rotating Proxies**: Use carefully (don't rotate too frequently)

**Avoid:**
- ❌ Free/public proxies (almost always flagged)
- ❌ Datacenter proxies (easier to detect)
- ❌ Shared proxies used by many users
- ❌ Proxies from known VPN/proxy providers (may be flagged)

#### 2. Proxy Configuration

**Telethon supports proxies via `connection` parameter:**

```python
from telethon import TelegramClient
from telethon.network.connection.tcpfull import ConnectionTcpFull

# SOCKS5 Proxy Configuration
proxy = {
    'proxy_type': 'socks5',  # or 'http', 'socks4'
    'addr': 'proxy.example.com',
    'port': 1080,
    'username': 'your_username',  # Optional
    'password': 'your_password'   # Optional
}

# Create client with proxy
client = TelegramClient(
    'session_name',
    api_id,
    api_hash,
    connection=ConnectionTcpFull,
    proxy=proxy
)
```

**HTTP Proxy Configuration:**

```python
proxy = {
    'proxy_type': 'http',
    'addr': 'proxy.example.com',
    'port': 8080,
    'username': 'your_username',  # Optional
    'password': 'your_password'   # Optional
}
```

**SOCKS4 Proxy Configuration:**

```python
proxy = {
    'proxy_type': 'socks4',
    'addr': 'proxy.example.com',
    'port': 1080
}
```

#### 3. Proxy Rotation Strategy

**If using multiple proxies:**

```python
import random
from typing import List, Dict

class ProxyRotator:
    """Manages proxy rotation for multiple accounts."""
    
    def __init__(self, proxies: List[Dict]):
        """
        Initialize with list of proxy configurations.
        
        Args:
            proxies: List of proxy dicts with 'proxy_type', 'addr', 'port', etc.
        """
        self.proxies = proxies
        self.current_proxy_index = 0
        self.proxy_usage_count = {}  # Track usage per proxy
    
    def get_proxy(self, account_id: str = None) -> Dict:
        """
        Get proxy for account (sticky assignment recommended).
        
        Args:
            account_id: Account identifier for sticky assignment
        
        Returns:
            Proxy configuration dict
        """
        if account_id:
            # Sticky assignment: same account uses same proxy
            # This is safer than random rotation
            proxy_index = hash(account_id) % len(self.proxies)
            return self.proxies[proxy_index]
        else:
            # Round-robin rotation (use sparingly)
            proxy = self.proxies[self.current_proxy_index]
            self.current_proxy_index = (self.current_proxy_index + 1) % len(self.proxies)
            return proxy
    
    def test_proxy(self, proxy: Dict) -> bool:
        """
        Test if proxy is working.
        
        Returns:
            True if proxy is functional
        """
        try:
            # Test connection (simplified example)
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex((proxy['addr'], proxy['port']))
            sock.close()
            return result == 0
        except Exception:
            return False
```

#### 4. Proxy Testing and Validation

**Always test proxies before use:**

```python
async def test_telegram_proxy(proxy: Dict, api_id: str, api_hash: str) -> bool:
    """
    Test if proxy works with Telegram.
    
    Args:
        proxy: Proxy configuration
        api_id: Telegram API ID
        api_hash: Telegram API Hash
    
    Returns:
        True if proxy works, False otherwise
    """
    try:
        # Create test client with proxy
        test_client = TelegramClient(
            'test_session',
            api_id,
            api_hash,
            proxy=proxy
        )
        
        await test_client.connect()
        
        # Try simple operation
        if await test_client.is_user_authorized():
            await test_client.get_me()
        
        await test_client.disconnect()
        return True
    except Exception as e:
        logger.error(f"Proxy test failed: {e}")
        return False
```

### Proxy Implementation Example

```python
from telethon import TelegramClient
from telethon.network.connection.tcpfull import ConnectionTcpFull
from typing import Optional, Dict

class ProxyClientManager:
    """Client manager with proxy support."""
    
    def __init__(self, proxy: Optional[Dict] = None):
        """
        Initialize with optional proxy.
        
        Args:
            proxy: Proxy configuration dict or None
        """
        self.proxy = proxy
    
    def create_client_with_proxy(
        self,
        session_name: str,
        api_id: str,
        api_hash: str,
        proxy: Optional[Dict] = None
    ) -> TelegramClient:
        """
        Create TelegramClient with proxy support.
        
        Args:
            session_name: Session file name
            api_id: Telegram API ID
            api_hash: Telegram API Hash
            proxy: Proxy config (uses self.proxy if None)
        
        Returns:
            TelegramClient instance
        """
        # Use provided proxy or instance proxy
        active_proxy = proxy or self.proxy
        
        if active_proxy:
            logger.info(f"Creating client with proxy: {active_proxy['addr']}:{active_proxy['port']}")
            return TelegramClient(
                session_name,
                int(api_id),
                api_hash,
                connection=ConnectionTcpFull,
                proxy=active_proxy
            )
        else:
            # No proxy
            return TelegramClient(
                session_name,
                int(api_id),
                api_hash
            )
```

### Proxy Recommendations

#### ✅ Recommended Approach

1. **Use residential proxies** if available (most natural)
2. **Sticky proxy assignment** - same account uses same proxy
3. **Test proxies** before using them in production
4. **Monitor proxy health** - replace if connection issues occur
5. **Use proxies from same region** as your account
6. **Still follow rate limits** - proxies don't bypass them

#### ❌ Avoid

1. **Free/public proxies** - almost always flagged
2. **Frequent proxy rotation** - looks suspicious
3. **Using proxies to bypass limits** - they don't work that way
4. **Proxies from different countries** than account location
5. **Shared/datacenter proxies** - easier to detect

### Proxy vs No Proxy Decision Matrix

| Scenario | Use Proxy? | Reason |
|----------|-----------|--------|
| Single account, normal usage | ❌ No | Not necessary, adds complexity |
| Multiple accounts | ✅ Yes | Distribute IP load |
| IP already flagged | ✅ Yes | Need different IP |
| High-volume operations | ✅ Yes | Distribute requests |
| Testing/development | ⚠️ Maybe | Only if testing proxy functionality |
| Account in restricted region | ✅ Yes | May be required to access Telegram |

### Summary: Proxy Usage

**Key Takeaways:**

1. **Proxies are a tool, not a solution** - They help distribute requests but don't replace proper rate limiting
2. **Quality matters** - Use high-quality residential proxies, avoid free/public ones
3. **Sticky assignment** - Same account should use same proxy (don't rotate frequently)
4. **Test first** - Always test proxies before using in production
5. **Still follow limits** - Proxies don't bypass Telegram's rate limits
6. **Regional consistency** - Use proxies from same region as account when possible

**Bottom Line:** Use proxies if you have multiple accounts or your IP is flagged, but **always combine with proper rate limiting and best practices**. Proxies alone won't protect you from account bans if you violate Telegram's policies.

---

## Implementation Guidelines

### Rate Limiter Configuration

```python
# Recommended 2025 Configuration
SAFE_ADD_USER_CONFIG = {
    'min_delay_seconds': 30,           # Minimum delay between adds
    'max_per_hour': 10,                 # Maximum adds per hour
    'max_per_day_new': 50,              # New accounts (< 30 days)
    'max_per_day_established': 100,     # Established accounts (30-90 days)
    'max_per_day_old': 200,             # Very old accounts (> 90 days)
    'contact_wait_seconds': 120,       # Wait after adding to contacts
    'retry_on_flood_wait': True,        # Automatically wait on FloodWaitError
    'max_retries': 3,                   # Maximum retry attempts
    'backoff_multiplier': 2.0,          # Exponential backoff multiplier
    'account_age_threshold_1': 30,      # Days for "new" account
    'account_age_threshold_2': 90,      # Days for "established" account
}
```

### Rate Limiter Implementation

```python
from datetime import datetime, timedelta
from typing import Tuple, Optional

class AddUserLimiter:
    """Rate limiter for safely adding users to Telegram groups."""
    
    def __init__(self):
        self.daily_count = 0
        self.hourly_count = 0
        self.last_add_time: Optional[datetime] = None
        self.daily_reset_time: Optional[datetime] = None
        self.hourly_reset_time: Optional[datetime] = None
        self.account_creation_date: Optional[datetime] = None
    
    def set_account_age(self, account_creation_date: datetime):
        """Set account creation date to determine limits."""
        self.account_creation_date = account_creation_date
    
    def can_add_user(self) -> Tuple[bool, str]:
        """
        Check if user can be added based on rate limits.
        
        Returns:
            (can_add: bool, reason: str)
        """
        now = datetime.now()
        
        # Reset daily counter if needed
        if not self.daily_reset_time or now >= self.daily_reset_time:
            self.daily_count = 0
            self.daily_reset_time = now + timedelta(days=1)
        
        # Reset hourly counter if needed
        if not self.hourly_reset_time or now >= self.hourly_reset_time:
            self.hourly_count = 0
            self.hourly_reset_time = now + timedelta(hours=1)
        
        # Determine daily limit based on account age
        if self.account_creation_date:
            account_age_days = (now - self.account_creation_date).days
            if account_age_days < SAFE_ADD_USER_CONFIG['account_age_threshold_1']:
                max_daily = SAFE_ADD_USER_CONFIG['max_per_day_new']
            elif account_age_days < SAFE_ADD_USER_CONFIG['account_age_threshold_2']:
                max_daily = SAFE_ADD_USER_CONFIG['max_per_day_established']
            else:
                max_daily = SAFE_ADD_USER_CONFIG['max_per_day_old']
        else:
            # Default to conservative limit if age unknown
            max_daily = SAFE_ADD_USER_CONFIG['max_per_day_new']
        
        # Check daily limit
        if self.daily_count >= max_daily:
            reset_time = self._get_reset_time_str(self.daily_reset_time)
            return False, f"Daily limit reached ({max_daily} users/day). Resets in {reset_time}"
        
        # Check hourly limit
        if self.hourly_count >= SAFE_ADD_USER_CONFIG['max_per_hour']:
            reset_time = self._get_reset_time_str(self.hourly_reset_time)
            return False, f"Hourly limit reached ({SAFE_ADD_USER_CONFIG['max_per_hour']} users/hour). Resets in {reset_time}"
        
        # Check minimum delay
        if self.last_add_time:
            elapsed = (now - self.last_add_time).total_seconds()
            min_delay = SAFE_ADD_USER_CONFIG['min_delay_seconds']
            if elapsed < min_delay:
                wait_time = min_delay - elapsed
                return False, f"Please wait {wait_time:.0f} seconds before adding next user"
        
        return True, "OK"
    
    def record_add(self):
        """Record that a user was added."""
        self.daily_count += 1
        self.hourly_count += 1
        self.last_add_time = datetime.now()
    
    def _get_reset_time_str(self, reset_time: datetime) -> str:
        """Get human-readable time until reset."""
        delta = reset_time - datetime.now()
        hours = int(delta.total_seconds() // 3600)
        minutes = int((delta.total_seconds() % 3600) // 60)
        return f"{hours}h {minutes}m"
```

---

## Error Handling

### Critical Errors to Handle

```python
from telethon.errors import (
    # Rate Limiting Errors (CRITICAL)
    FloodWaitError,              # MUST wait specified seconds - DO NOT IGNORE
    PeerFloodError,              # Too many requests to this peer
    
    # Privacy Restriction Errors
    UserPrivacyError,            # User privacy settings block action
    PrivacyRestrictedError,      # Privacy restriction
    NotMutualContactError,      # Need to be in contacts
    UserNotMutualContactError,   # Same as above
    
    # Group/User Limit Errors
    UserChannelsTooMuchError,    # User in too many channels
    UsersTooMuchError,           # Group has too many members
    ChatWriteForbiddenError,     # No permission to add
    
    # User Status Errors
    UserBannedInChannelError,    # User is banned
    UserKickedError,             # User was kicked
    UserDeactivatedError,        # User account deactivated
    
    # Group Status Errors
    ChannelPrivateError,         # Channel is private
    ChatAdminRequiredError,      # Admin rights required
    ChatIdInvalidError,          # Invalid chat ID
    
    # Account Status Errors
    UnauthorizedError,          # Session expired
    AuthKeyUnregisteredError,    # Auth key invalid
    SessionRevokedError,         # Session revoked
)
```

### Error Handling Implementation

```python
async def add_user_safely(
    client,
    group_entity,
    user_identifier: str,
    is_phone: bool = False,
    limiter: AddUserLimiter
) -> Tuple[bool, str]:
    """
    Safely add user to group with proper error handling.
    
    Args:
        client: Telethon TelegramClient
        group_entity: Group/channel entity
        user_identifier: Username or phone number
        is_phone: True if identifier is phone number
        limiter: Rate limiter instance
    
    Returns:
        (success: bool, message: str)
    """
    from telethon.tl.functions.channels import InviteToChannelRequest
    from telethon.tl.functions.messages import AddChatUserRequest
    from telethon.tl.functions.contacts import ImportContactsRequest, DeleteContactsRequest
    from telethon.tl.types import InputPhoneContact
    from telethon.errors import FloodWaitError
    
    # Check rate limits
    can_add, reason = limiter.can_add_user()
    if not can_add:
        return False, reason
    
    try:
        # Handle phone number (must add to contacts first)
        if is_phone:
            # Add to contacts
            contact = InputPhoneContact(
                client_id=0,
                phone=user_identifier,
                first_name="",  # Optional
                last_name=""    # Optional
            )
            result = await client(ImportContactsRequest([contact]))
            
            if not result.users:
                return False, "User not found or cannot be added to contacts"
            
            user = result.users[0]
            
            # Wait after adding to contacts
            await asyncio.sleep(SAFE_ADD_USER_CONFIG['contact_wait_seconds'])
        else:
            # Get user by username
            user = await client.get_entity(user_identifier)
        
        # Determine if group is channel/supergroup or regular group
        is_channel = (
            hasattr(group_entity, 'broadcast') or 
            hasattr(group_entity, 'megagroup') or
            hasattr(group_entity, 'gigagroup')
        )
        
        # Add user to group
        if is_channel:
            await client(InviteToChannelRequest(
                channel=group_entity,
                users=[user]
            ))
        else:
            await client(AddChatUserRequest(
                chat_id=group_entity.id,
                user_id=user.id,
                fwd_limit=10  # Allow user to see last 10 messages
            ))
        
        # Record successful addition
        limiter.record_add()
        
        # Optional: Remove from contacts if added by phone
        if is_phone:
            try:
                await client(DeleteContactsRequest(id=[user.id]))
            except Exception:
                pass  # Ignore errors when removing
        
        return True, f"Successfully added {user_identifier} to group"
        
    except FloodWaitError as e:
        # CRITICAL: Always wait for FloodWaitError
        wait_time = e.seconds
        logger.warning(f"FloodWait: waiting {wait_time} seconds")
        await asyncio.sleep(wait_time)
        # Retry once after waiting
        return await add_user_safely(client, group_entity, user_identifier, is_phone, limiter)
    
    except (UserPrivacyError, PrivacyRestrictedError, NotMutualContactError) as e:
        if is_phone:
            return False, "User privacy settings prevent adding. User must be in contacts first."
        else:
            return False, "User privacy settings prevent adding. Try adding to contacts first."
    
    except (UserBannedInChannelError, UserKickedError) as e:
        return False, "User is banned or was kicked from this group"
    
    except ChatAdminRequiredError as e:
        return False, "Account must be admin with 'Add Members' permission"
    
    except (UsersTooMuchError, UserChannelsTooMuchError) as e:
        return False, "Group or user has reached member limit"
    
    except Exception as e:
        logger.error(f"Error adding user: {e}")
        return False, f"Failed to add user: {str(e)}"
```

---

## Best Practices

### 1. Use Invite Links for Bulk Additions

**For adding 50+ users, use invite links instead:**

```python
async def create_invite_link(client, group_entity) -> str:
    """Create invite link for group."""
    from telethon.tl.functions.messages import ExportChatInviteRequest
    
    result = await client(ExportChatInviteRequest(group_entity))
    return result.link
```

**Benefits:**
- Users join at their discretion
- Less likely to trigger spam detection
- No rate limits on link generation
- Better for large-scale additions

### 2. Account Activity Mixing

**Don't use account only for adding users:**

- Send messages to contacts
- Join public channels
- Browse content
- Interact with groups naturally
- Mix manual and automated actions

### 3. Monitoring and Logging

**Track all operations:**

```python
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class AddUserLogger:
    """Log all user addition operations."""
    
    def log_attempt(self, user_id: str, group_id: int, method: str):
        """Log addition attempt."""
        logger.info(f"Attempting to add user {user_id} to group {group_id} via {method}")
    
    def log_success(self, user_id: str, group_id: int, duration: float):
        """Log successful addition."""
        logger.info(f"Successfully added user {user_id} to group {group_id} in {duration:.2f}s")
    
    def log_failure(self, user_id: str, group_id: int, error: str):
        """Log failed addition."""
        logger.warning(f"Failed to add user {user_id} to group {group_id}: {error}")
    
    def log_rate_limit(self, limit_type: str, reset_time: datetime):
        """Log rate limit hit."""
        logger.warning(f"Rate limit hit: {limit_type}. Resets at {reset_time}")
```

### 4. Progressive Limits

**Start conservative, increase gradually:**

```python
def get_daily_limit(account_age_days: int, days_since_first_add: int) -> int:
    """
    Get progressive daily limit based on account age and usage history.
    
    Args:
        account_age_days: Account age in days
        days_since_first_add: Days since first addition operation
    
    Returns:
        Recommended daily limit
    """
    base_limit = 20  # Start with 20/day
    
    # Increase based on account age
    if account_age_days > 90:
        base_limit = 100
    elif account_age_days > 30:
        base_limit = 50
    
    # Increase based on usage history (if no issues)
    if days_since_first_add > 30:
        base_limit = min(base_limit + 20, 200)  # Cap at 200
    
    return base_limit
```

### 5. Stop on Warnings

**Immediately stop if you receive:**

- Any account restriction warnings
- Multiple `FloodWaitError` in short time
- `PeerFloodError` (indicates account is flagged)
- Account status changes (restricted, limited)

---

## Code Examples

### Complete Implementation Example

```python
import asyncio
import logging
from datetime import datetime
from typing import List, Tuple
from telethon import TelegramClient
from telethon.tl.types import Channel, Chat

logger = logging.getLogger(__name__)

class SafeUserAdder:
    """Safe user addition service with rate limiting and error handling."""
    
    def __init__(self, client: TelegramClient):
        self.client = client
        self.limiter = AddUserLimiter()
        self.logger = AddUserLogger()
    
    async def add_users_to_group(
        self,
        group_identifier: str,
        user_identifiers: List[str],
        are_phone_numbers: bool = False,
        account_creation_date: Optional[datetime] = None
    ) -> Tuple[int, int, List[str]]:
        """
        Add multiple users to a group safely.
        
        Args:
            group_identifier: Group ID, username, or invite link
            user_identifiers: List of usernames or phone numbers
            are_phone_numbers: True if identifiers are phone numbers
            account_creation_date: Account creation date for limit calculation
        
        Returns:
            (success_count, failure_count, error_messages)
        """
        # Set account age if provided
        if account_creation_date:
            self.limiter.set_account_age(account_creation_date)
        
        # Get group entity
        try:
            group_entity = await self.client.get_entity(group_identifier)
        except Exception as e:
            logger.error(f"Failed to get group entity: {e}")
            return 0, 0, [f"Failed to access group: {str(e)}"]
        
        success_count = 0
        failure_count = 0
        error_messages = []
        
        for user_id in user_identifiers:
            # Check if we can add (rate limit check)
            can_add, reason = self.limiter.can_add_user()
            if not can_add:
                error_messages.append(f"{user_id}: {reason}")
                failure_count += 1
                continue
            
            # Log attempt
            self.logger.log_attempt(user_id, group_entity.id, "add")
            
            # Add user
            start_time = datetime.now()
            success, message = await add_user_safely(
                self.client,
                group_entity,
                user_id,
                are_phone_numbers,
                self.limiter
            )
            
            duration = (datetime.now() - start_time).total_seconds()
            
            if success:
                success_count += 1
                self.logger.log_success(user_id, group_entity.id, duration)
            else:
                failure_count += 1
                error_messages.append(f"{user_id}: {message}")
                self.logger.log_failure(user_id, group_entity.id, message)
            
            # Wait minimum delay (if not already waited in add_user_safely)
            await asyncio.sleep(SAFE_ADD_USER_CONFIG['min_delay_seconds'])
        
        return success_count, failure_count, error_messages
```

---

## Troubleshooting

### Common Issues and Solutions

#### Issue: "FloodWaitError" occurring frequently

**Solution:**
- Increase delay between additions (60+ seconds)
- Reduce daily/hourly limits
- Check if account is flagged (may need to wait 24-48 hours)

#### Issue: "PrivacyRestrictedError" for all users

**Solution:**
- For phone numbers: Always add to contacts first
- For usernames: User has privacy restrictions - cannot add directly
- Consider using invite links instead

#### Issue: Account gets restricted after adding users

**Solution:**
- **STOP immediately** - do not add more users
- Wait 24-48 hours before resuming
- Reduce limits significantly (10-20/day)
- Mix with normal account activity
- Consider using different account

#### Issue: "ChatAdminRequiredError"

**Solution:**
- Verify account is admin of the group
- Check admin permissions include "Add Members"
- Request admin rights from group owner

#### Issue: "UsersTooMuchError"

**Solution:**
- Group has reached member limit
- Regular groups: 200 members max
- Supergroups: 200,000 members max
- Cannot add more members

#### Issue: Rate limits reset but still getting errors

**Solution:**
- Account may be temporarily flagged
- Wait additional 24 hours
- Check account status in Telegram app
- Consider using invite links instead

---

## Summary Checklist

### Before Implementation

- [ ] Understand Telegram's 200/day maximum limit
- [ ] Implement rate limiter with account age detection
- [ ] Handle all critical errors (especially FloodWaitError)
- [ ] Add logging for all operations
- [ ] Test with non-official account first
- [ ] Implement progressive limits based on account age

### During Operations

- [ ] Always check rate limits before adding
- [ ] Wait minimum 30 seconds between additions
- [ ] Never exceed 10 users per hour
- [ ] Respect FloodWaitError - wait full duration
- [ ] For phone numbers: add to contacts first, wait 2 minutes
- [ ] Monitor success/failure rates
- [ ] Log all operations

### Safety Measures

- [ ] Use conservative limits (below Telegram's maximum)
- [ ] Mix adding users with normal account activity
- [ ] Stop immediately on any warnings
- [ ] Use invite links for bulk additions (50+ users)
- [ ] Monitor account status regularly
- [ ] Have backup accounts for testing

---

## References

- [Telegram Bot API Documentation](https://core.telegram.org/api)
- [Telethon Documentation](https://docs.telethon.dev/)
- [Telegram Terms of Service](https://telegram.org/tos)
- [Telegram Privacy Policy](https://telegram.org/privacy)

---

## Last Updated

**November 23, 2025** - Based on latest Telegram API restrictions and best practices.

---

## Important Reminders

1. **200 users/day is the MAXIMUM** - use conservatively (50-100/day for safety)
2. **Always respect FloodWaitError** - never ignore or bypass
3. **Account age matters** - new accounts need lower limits
4. **Privacy settings** - phone numbers require adding to contacts first
5. **Use invite links** - better for bulk additions
6. **Monitor account status** - stop immediately on warnings
7. **Test with non-official accounts** - never risk your main account
8. **Proxies are optional** - use high-quality residential proxies if needed, but they don't replace rate limiting

---

**⚠️ Remember: Account bans are often permanent. When in doubt, use more conservative limits.**

