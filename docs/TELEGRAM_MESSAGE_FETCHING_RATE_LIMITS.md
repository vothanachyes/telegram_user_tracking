# Telegram Message Fetching Rate Limits and Safety Guide

## Table of Contents

1. [Overview](#overview)
2. [2025 Rate Limits](#2025-rate-limits)
3. [Account Safety Measures](#account-safety-measures)
4. [Current Implementation Analysis](#current-implementation-analysis)
5. [Implementation Guidelines](#implementation-guidelines)
6. [Error Handling](#error-handling)
7. [Best Practices](#best-practices)
8. [Code Examples](#code-examples)
9. [Troubleshooting](#troubleshooting)
10. [Comparison: Adding Users vs Fetching Messages](#comparison-adding-users-vs-fetching-messages)

---

## Overview

This guide provides comprehensive information about Telegram's rate limits, restrictions, and safety measures when **fetching messages from groups** using Telethon. Unlike adding users, message fetching is generally safer, but proper rate limiting is still essential to prevent account restrictions.

### ⚠️ Important Notes

**Message fetching is safer than adding users, but:**
- Rate limits still apply and must be respected
- FloodWaitError can occur if limits are exceeded
- Continuous 24/7 fetching can trigger anti-spam detection
- Account restrictions are still possible with abusive behavior

**Always use non-official accounts for testing and development.**

---

## 2025 Rate Limits

### Official Telegram Limits for Message Fetching (Updated November 2025)

#### Message Fetching Limits

- **No Official Daily Limit**: Unlike adding users, there's no hard daily limit for reading messages (you're a member of the group)
- **Rate Limits are Per-Request**: Based on request frequency, not total volume
- **Recommended Safe Limits**:
  - **Delay Between Messages**: 1-5 seconds (default: 5 seconds)
  - **Maximum Messages Per Minute**: 20-30 messages
  - **Maximum Messages Per Hour**: 1000-2000 messages (conservative)
  - **No Hard Daily Limit**: But avoid continuous 24/7 fetching

#### Reaction Fetching Limits

- **Additional API Calls Required**: Reactions require separate API calls
- **Recommended Delay**: 0.5-1.0 seconds between reaction fetches
- **Best Practice**: Only fetch reactions for messages that have them
- **Consideration**: Disable reaction tracking for very large historical fetches

#### Per-Request Limits

- **Minimum Delay**: 1 second between message fetches (recommended: 5 seconds)
- **FloodWait Compliance**: Always wait the full duration specified in `FloodWaitError`
- **Batch Size**: Fetch in batches of 7-30 days for large date ranges
- **Break Periods**: Take 5-10 minute breaks between large batches

### Account Age Considerations

Telegram applies different limits based on account age, but message fetching is generally more lenient:

| Account Age | Recommended Delay | Notes |
|------------|------------------|-------|
| < 7 days | 5-10 seconds | Very new accounts - use extra caution |
| 7-30 days | 3-5 seconds | New accounts - build activity history |
| 30-90 days | 2-5 seconds | Established accounts - normal limits |
| > 90 days | 1-5 seconds | Old accounts - can use lower delays |

---

## Account Safety Measures

### 1. Fetching Behavior Best Practices

**Good Practices:**
- ✅ Use date ranges to limit fetch scope
- ✅ Skip already-fetched messages (check database first)
- ✅ Use `iter_messages()` with `offset_date` for efficiency
- ✅ Fetch in batches (7-30 day chunks)
- ✅ Take breaks between large fetches
- ✅ Monitor for FloodWaitError and adjust delays

**Avoid These Behaviors:**
- ❌ Fetching from many groups simultaneously
- ❌ Continuous 24/7 fetching without breaks
- ❌ Fetching very old messages in bulk (years of history at once)
- ❌ Ignoring FloodWaitError
- ❌ Fetching the same group repeatedly in short periods

### 2. Group Access Requirements

**Required Access:**
- Account must be a **member** of the group
- For private groups: Must have been added/invited
- For public groups: Can join via invite link
- **No admin permissions required** for reading messages

**Access Errors:**
- `ChannelPrivateError`: Channel is private or you're not a member
- `ChatIdInvalidError`: Invalid chat ID or group doesn't exist
- `UnauthorizedError`: Session expired or invalid

### 3. Anti-Spam Detection Avoidance

**Avoid These Behaviors:**
- ❌ Fetching from 10+ groups simultaneously
- ❌ Continuous 24/7 fetching without breaks
- ❌ Fetching very old messages in bulk (years of history)
- ❌ Ignoring FloodWaitError repeatedly
- ❌ Using account only for fetching (no other activity)

**Best Practices:**
- ✅ Fetch in batches (1-7 days at a time)
- ✅ Take breaks between large fetches (5-10 minutes)
- ✅ Monitor for FloodWaitError and adjust delays
- ✅ Use incremental fetching (fetch only new messages periodically)
- ✅ Mix fetching with normal account activity
- ✅ Use accounts with normal activity history

### 4. Incremental Fetching Strategy

**For Regular Updates:**
- Fetch only new messages since last fetch
- Use `offset_date` to start from last fetch date
- Reduces API calls and improves efficiency
- Lower risk of rate limiting

**For Historical Fetching:**
- Fetch in 7-30 day batches
- Take breaks between batches
- Monitor for FloodWaitError
- Consider disabling reactions for very old messages

---

## Current Implementation Analysis

### Your App's Current Implementation

Your app currently implements the following rate limiting:

#### Message Fetching Delay
```python
# From services/telegram/message_fetcher.py
fetch_delay = settings.settings.fetch_delay_seconds  # Default: 5.0 seconds

if fetch_delay > 0:
    if delay_callback:
        await delay_callback(fetch_delay, "Rate limit delay")
    else:
        await asyncio.sleep(fetch_delay)
```

#### FloodWaitError Handling
```python
except FloodWaitError as e:
    logger.warning(f"FloodWait: waiting {e.seconds} seconds")
    if delay_callback:
        await delay_callback(e.seconds, "Flood wait")
    else:
        await asyncio.sleep(e.seconds)
```

#### Reaction Fetching Delay
```python
# From services/telegram/reaction_processor.py
reaction_delay = settings.settings.reaction_fetch_delay  # Default: 0.5 seconds
```

#### Current Settings (from database/models/app_settings.py)
- `fetch_delay_seconds`: **5.0 seconds** (default) ✅ Good
- `reaction_fetch_delay`: **0.5 seconds** (default) ✅ Acceptable
- `track_reactions`: **True** (default) - Can be disabled for large fetches

#### Implementation Strengths
- ✅ FloodWaitError handling implemented correctly
- ✅ Configurable delay (fetch_delay_seconds)
- ✅ Skips existing messages (checks database first)
- ✅ Uses efficient `iter_messages()` with `offset_date`
- ✅ Reaction fetching with separate delay
- ✅ Progress callbacks for user feedback
- ✅ Error logging and handling

#### Potential Enhancements
- Consider batch fetching for large date ranges (> 30 days)
- Add dynamic delay based on fetch progress
- Consider disabling reactions for very old messages (> 1 year)
- Add break periods between large batches
- Monitor and log FloodWaitError frequency

---

## Implementation Guidelines

### Recommended Configuration

```python
# Recommended 2025 Configuration for Message Fetching
SAFE_FETCH_MESSAGES_CONFIG = {
    'min_delay_seconds': 1.0,           # Minimum delay between messages (1-5 seconds)
    'default_delay_seconds': 5.0,       # Default delay (your current setting)
    'max_messages_per_minute': 20,      # Maximum messages per minute
    'max_messages_per_hour': 1000,      # Maximum messages per hour (conservative)
    'batch_size_days': 7,               # Fetch in 7-day batches
    'break_after_batch_minutes': 5,     # Break after each batch
    'reaction_delay_seconds': 0.5,      # Delay for reaction fetching
    'retry_on_flood_wait': True,        # Automatically wait on FloodWaitError
    'max_retries': 3,                   # Maximum retry attempts
    'skip_existing_messages': True,     # Skip already-fetched messages
    'disable_reactions_for_old_messages_days': 365,  # Disable reactions for messages > 1 year
}
```

### Dynamic Delay Strategy

For large historical fetches, consider increasing delay as fetch progresses:

```python
def get_dynamic_delay(message_count: int, base_delay: float = 5.0) -> float:
    """
    Get dynamic delay based on fetch progress.
    Increase delay as fetch progresses to avoid rate limits.
    
    Args:
        message_count: Number of messages fetched so far
        base_delay: Base delay in seconds (default: 5.0)
    
    Returns:
        Delay in seconds
    """
    if message_count < 100:
        return base_delay  # 5 seconds
    elif message_count < 500:
        return base_delay * 1.5  # 7.5 seconds
    elif message_count < 1000:
        return base_delay * 2.0  # 10 seconds
    else:
        return base_delay * 2.5  # 12.5 seconds
```

### Batch Fetching Strategy

Instead of fetching years of history at once, fetch in smaller batches:

```python
from datetime import datetime, timedelta
import asyncio

async def fetch_messages_in_batches(
    client,
    group_id: int,
    start_date: datetime,
    end_date: datetime,
    batch_size_days: int = 7,
    break_minutes: int = 5
):
    """
    Fetch messages in smaller batches to avoid rate limits.
    
    Args:
        client: Telethon TelegramClient
        group_id: Group ID to fetch from
        start_date: Start date for fetching
        end_date: End date for fetching
        batch_size_days: Number of days per batch (default: 7)
        break_minutes: Minutes to wait between batches (default: 5)
    """
    current_start = start_date
    batch_count = 0
    
    while current_start < end_date:
        current_end = min(
            current_start + timedelta(days=batch_size_days),
            end_date
        )
        
        logger.info(f"Fetching batch {batch_count + 1}: {current_start.date()} to {current_end.date()}")
        
        # Fetch batch
        success, count, error = await fetch_messages(
            client, 
            group_id, 
            current_start, 
            current_end
        )
        
        if not success:
            logger.error(f"Batch {batch_count + 1} failed: {error}")
            break
        
        logger.info(f"Batch {batch_count + 1} complete: {count} messages")
        
        # Break between batches (except for last batch)
        if current_end < end_date:
            logger.info(f"Taking {break_minutes} minute break before next batch...")
            await asyncio.sleep(break_minutes * 60)
        
        current_start = current_end
        batch_count += 1
    
    logger.info(f"Completed {batch_count} batches")
```

### Reaction Fetching Optimization

Your reaction processor is good, but consider these optimizations:

```python
async def should_fetch_reactions(
    message_date: datetime,
    disable_for_old_days: int = 365
) -> bool:
    """
    Determine if reactions should be fetched for a message.
    
    Args:
        message_date: Date of the message
        disable_for_old_days: Disable reactions for messages older than this
    
    Returns:
        True if reactions should be fetched
    """
    if not settings.settings.track_reactions:
        return False
    
    # Don't fetch reactions for very old messages
    age_days = (datetime.now() - message_date).days
    if age_days > disable_for_old_days:
        return False
    
    return True
```

---

## Error Handling

### Critical Errors to Handle

```python
from telethon.errors import (
    # Rate Limiting Errors (CRITICAL)
    FloodWaitError,              # MUST wait specified seconds - DO NOT IGNORE
    
    # Access Errors
    ChannelPrivateError,         # Channel is private or you're not a member
    ChatAdminRequiredError,      # Admin rights required (for some operations)
    ChatIdInvalidError,          # Invalid chat ID or group doesn't exist
    
    # Account Status Errors
    UnauthorizedError,          # Session expired
    AuthKeyUnregisteredError,    # Auth key invalid
    SessionRevokedError,         # Session revoked
    
    # Network Errors
    TimeoutError,                # Network timeout
    ConnectionError,             # Connection issues
)
```

### Error Handling Implementation

```python
async def fetch_messages_safely(
    client,
    group_id: int,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    max_retries: int = 3
) -> Tuple[bool, int, Optional[str]]:
    """
    Safely fetch messages with proper error handling.
    
    Args:
        client: Telethon TelegramClient
        group_id: Group ID to fetch from
        start_date: Optional start date
        end_date: Optional end date
        max_retries: Maximum retry attempts
    
    Returns:
        (success: bool, message_count: int, error_message: str)
    """
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            # Get entity
            entity = await client.get_entity(group_id)
            
            message_count = 0
            fetch_delay = settings.settings.fetch_delay_seconds
            
            async for telegram_msg in client.iter_messages(entity, offset_date=start_date, reverse=True):
                try:
                    # Check date range
                    if end_date and telegram_msg.date > end_date:
                        break
                    if start_date and telegram_msg.date < start_date:
                        continue
                    
                    # Process message
                    # ... your message processing logic ...
                    message_count += 1
                    
                    # Rate limit delay
                    if fetch_delay > 0:
                        await asyncio.sleep(fetch_delay)
                
                except FloodWaitError as e:
                    logger.warning(f"FloodWait: waiting {e.seconds} seconds")
                    await asyncio.sleep(e.seconds)
                    # Continue with next message
                    continue
                
                except Exception as e:
                    logger.error(f"Error processing message {telegram_msg.id}: {e}")
                    continue
            
            return True, message_count, None
        
        except FloodWaitError as e:
            wait_time = e.seconds
            logger.warning(f"FloodWait at fetch level: waiting {wait_time} seconds")
            await asyncio.sleep(wait_time)
            retry_count += 1
            continue
        
        except ChannelPrivateError as e:
            return False, 0, "Channel is private or you're not a member"
        
        except ChatIdInvalidError as e:
            return False, 0, "Invalid chat ID or group doesn't exist"
        
        except UnauthorizedError as e:
            return False, 0, "Session expired. Please re-authenticate."
        
        except (TimeoutError, ConnectionError) as e:
            logger.warning(f"Network error: {e}. Retrying...")
            retry_count += 1
            await asyncio.sleep(5)  # Wait before retry
            continue
        
        except Exception as e:
            logger.error(f"Unexpected error fetching messages: {e}")
            return False, 0, str(e)
    
    return False, 0, f"Failed after {max_retries} retries"
```

---

## Best Practices

### 1. Incremental Fetching for Regular Updates

**For regular updates, fetch only new messages:**

```python
async def fetch_new_messages_only(
    client,
    group_id: int,
    last_fetch_date: datetime
) -> Tuple[bool, int, Optional[str]]:
    """
    Fetch only new messages since last fetch.
    More efficient and lower risk than full historical fetch.
    """
    return await fetch_messages_safely(
        client,
        group_id,
        start_date=last_fetch_date,
        end_date=datetime.now()
    )
```

**Benefits:**
- Fewer API calls
- Faster execution
- Lower risk of rate limiting
- Better for regular monitoring

### 2. Batch Fetching for Historical Data

**For large historical fetches, use batches:**

```python
# Fetch 1 year of history in 7-day batches
start_date = datetime(2024, 1, 1)
end_date = datetime(2024, 12, 31)

await fetch_messages_in_batches(
    client,
    group_id,
    start_date,
    end_date,
    batch_size_days=7,
    break_minutes=5
)
```

**Benefits:**
- Reduces risk of rate limiting
- Allows progress monitoring
- Can pause/resume if needed
- Better error recovery

### 3. Monitoring and Logging

**Track all fetch operations:**

```python
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class MessageFetchLogger:
    """Log all message fetch operations."""
    
    def log_fetch_start(self, group_id: int, start_date: datetime, end_date: datetime):
        """Log fetch start."""
        logger.info(
            f"Starting fetch for group {group_id} "
            f"from {start_date.date()} to {end_date.date()}"
        )
    
    def log_fetch_progress(self, group_id: int, message_count: int, total_processed: int):
        """Log fetch progress."""
        logger.info(
            f"Group {group_id}: Fetched {message_count} messages "
            f"(processed: {total_processed})"
        )
    
    def log_fetch_complete(self, group_id: int, message_count: int, duration: float):
        """Log fetch completion."""
        logger.info(
            f"Completed fetch for group {group_id}: {message_count} messages "
            f"in {duration:.2f} seconds"
        )
    
    def log_flood_wait(self, group_id: int, wait_seconds: int):
        """Log flood wait occurrence."""
        logger.warning(
            f"Group {group_id}: FloodWait - waiting {wait_seconds} seconds"
        )
    
    def log_fetch_error(self, group_id: int, error: str):
        """Log fetch error."""
        logger.error(f"Group {group_id}: Fetch error - {error}")
```

### 4. Progressive Limits

**Start conservative, increase gradually if no issues:**

```python
def get_safe_delay(account_age_days: int, fetch_history_days: int) -> float:
    """
    Get safe delay based on account age and fetch scope.
    
    Args:
        account_age_days: Account age in days
        fetch_history_days: Number of days to fetch
    
    Returns:
        Recommended delay in seconds
    """
    base_delay = 5.0  # Base delay
    
    # Increase delay for new accounts
    if account_age_days < 30:
        base_delay = 7.0
    elif account_age_days < 7:
        base_delay = 10.0
    
    # Increase delay for large historical fetches
    if fetch_history_days > 365:
        base_delay *= 1.5
    elif fetch_history_days > 90:
        base_delay *= 1.2
    
    return base_delay
```

### 5. Stop on Warnings

**Immediately stop if you receive:**
- Multiple `FloodWaitError` in short time (3+ in 1 hour)
- Account restriction warnings
- `UnauthorizedError` (session expired)
- Account status changes (restricted, limited)

---

## Code Examples

### Complete Implementation Example

```python
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional, Tuple
from telethon import TelegramClient
from telethon.errors import FloodWaitError, ChannelPrivateError

logger = logging.getLogger(__name__)

class SafeMessageFetcher:
    """Safe message fetching service with rate limiting and error handling."""
    
    def __init__(self, client: TelegramClient):
        self.client = client
        self.fetch_delay = 5.0  # Default delay
        self.logger = MessageFetchLogger()
    
    async def fetch_messages(
        self,
        group_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        batch_size_days: Optional[int] = None
    ) -> Tuple[bool, int, Optional[str]]:
        """
        Fetch messages from a group safely.
        
        Args:
            group_id: Group ID to fetch from
            start_date: Optional start date
            end_date: Optional end date
            batch_size_days: Optional batch size (None = no batching)
        
        Returns:
            (success, message_count, error_message)
        """
        try:
            # Determine if batching is needed
            if batch_size_days and start_date and end_date:
                days_diff = (end_date - start_date).days
                if days_diff > batch_size_days:
                    return await self._fetch_in_batches(
                        group_id, start_date, end_date, batch_size_days
                    )
            
            # Single fetch
            return await self._fetch_single_batch(
                group_id, start_date, end_date
            )
        
        except Exception as e:
            logger.error(f"Error in fetch_messages: {e}")
            return False, 0, str(e)
    
    async def _fetch_single_batch(
        self,
        group_id: int,
        start_date: Optional[datetime],
        end_date: Optional[datetime]
    ) -> Tuple[bool, int, Optional[str]]:
        """Fetch a single batch of messages."""
        try:
            entity = await self.client.get_entity(group_id)
            
            self.logger.log_fetch_start(group_id, start_date or datetime.min, end_date or datetime.now())
            
            message_count = 0
            processed_count = 0
            start_time = datetime.now()
            
            async for telegram_msg in self.client.iter_messages(
                entity,
                offset_date=start_date,
                reverse=True
            ):
                try:
                    processed_count += 1
                    
                    # Check date range
                    if end_date and telegram_msg.date > end_date:
                        break
                    if start_date and telegram_msg.date < start_date:
                        continue
                    
                    # Process message (your logic here)
                    # message = await self.process_message(telegram_msg)
                    # self.save_message(message)
                    message_count += 1
                    
                    # Progress logging
                    if message_count % 100 == 0:
                        self.logger.log_fetch_progress(group_id, message_count, processed_count)
                    
                    # Rate limit delay
                    if self.fetch_delay > 0:
                        await asyncio.sleep(self.fetch_delay)
                
                except FloodWaitError as e:
                    self.logger.log_flood_wait(group_id, e.seconds)
                    await asyncio.sleep(e.seconds)
                    continue
                
                except Exception as e:
                    logger.error(f"Error processing message {telegram_msg.id}: {e}")
                    continue
            
            duration = (datetime.now() - start_time).total_seconds()
            self.logger.log_fetch_complete(group_id, message_count, duration)
            
            return True, message_count, None
        
        except ChannelPrivateError:
            return False, 0, "Channel is private or you're not a member"
        except Exception as e:
            self.logger.log_fetch_error(group_id, str(e))
            return False, 0, str(e)
    
    async def _fetch_in_batches(
        self,
        group_id: int,
        start_date: datetime,
        end_date: datetime,
        batch_size_days: int
    ) -> Tuple[bool, int, Optional[str]]:
        """Fetch messages in batches."""
        current_start = start_date
        total_messages = 0
        batch_count = 0
        
        while current_start < end_date:
            current_end = min(
                current_start + timedelta(days=batch_size_days),
                end_date
            )
            
            logger.info(f"Fetching batch {batch_count + 1}: {current_start.date()} to {current_end.date()}")
            
            success, count, error = await self._fetch_single_batch(
                group_id, current_start, current_end
            )
            
            if not success:
                logger.error(f"Batch {batch_count + 1} failed: {error}")
                return False, total_messages, error
            
            total_messages += count
            batch_count += 1
            
            # Break between batches (except for last batch)
            if current_end < end_date:
                logger.info("Taking 5 minute break before next batch...")
                await asyncio.sleep(300)  # 5 minutes
            
            current_start = current_end
        
        logger.info(f"Completed {batch_count} batches: {total_messages} total messages")
        return True, total_messages, None
```

---

## Troubleshooting

### Common Issues and Solutions

#### Issue: Frequent FloodWaitError

**Symptoms:**
- Getting FloodWaitError every few messages
- Wait times increasing (10s, 30s, 60s+)

**Solutions:**
- Increase delay between messages (try 10-15 seconds)
- Reduce batch size (smaller date ranges)
- Add longer breaks between batches (10-15 minutes)
- Check if account is flagged (may need to wait 24-48 hours)
- Consider using a different account

#### Issue: Slow Fetching

**Symptoms:**
- Fetching takes very long
- Processing thousands of messages

**Solutions:**
- This is normal for large date ranges
- Consider fetching in smaller batches
- Use `offset_date` to start from specific dates (you already do this)
- Skip already-fetched messages (you already do this)
- Consider disabling reactions for very old messages

#### Issue: Missing Messages

**Symptoms:**
- Some messages not appearing in results
- Date range seems incomplete

**Solutions:**
- Check date range (timezone issues)
- Verify account has access to group
- Check if messages were deleted
- Verify group_id is correct
- Check if messages are outside date range

#### Issue: Account Gets Restricted

**Symptoms:**
- Account shows restrictions
- Cannot fetch from groups
- Session errors

**Solutions:**
- **STOP immediately** - do not continue fetching
- Wait 24-48 hours before resuming
- Reduce delays significantly (10-15 seconds)
- Fetch smaller batches (1-3 days)
- Mix with normal account activity
- Consider using different account

#### Issue: "ChannelPrivateError" or "ChatIdInvalidError"

**Solutions:**
- Verify account is a member of the group
- Check if group still exists
- Verify group_id is correct
- For private groups, ensure you were added/invited
- Try joining via invite link if public group

#### Issue: Rate Limits Reset But Still Getting Errors

**Solutions:**
- Account may be temporarily flagged
- Wait additional 24 hours
- Check account status in Telegram app
- Reduce delays further (15-20 seconds)
- Fetch even smaller batches (1 day at a time)

---

## Comparison: Adding Users vs Fetching Messages

| Aspect | Adding Users | Fetching Messages |
|--------|-------------|-------------------|
| **Daily Limit** | 200 users/day (hard limit) | No hard daily limit |
| **Hourly Limit** | 10 users/hour | ~1000 messages/hour (conservative) |
| **Delay Required** | 30+ seconds | 1-5 seconds |
| **Account Risk** | High (can get banned) | Low (reading is safer) |
| **Admin Required** | Yes | No (just need membership) |
| **FloodWait Frequency** | Common | Less common |
| **Best Practice** | Use invite links for bulk | Fetch in batches for large ranges |
| **Error Handling** | Critical | Important but less critical |
| **Testing Account** | Essential | Recommended |

### Key Differences

1. **Risk Level**: Fetching messages is much safer than adding users
2. **Rate Limits**: No hard daily limit for fetching, but frequency limits apply
3. **Delays**: Much shorter delays needed (1-5s vs 30s+)
4. **Account Requirements**: No admin needed, just membership
5. **Error Frequency**: FloodWaitError less common for fetching

---

## Summary Checklist

### Before Fetching

- [ ] Verify account is a member of the group
- [ ] Use reasonable date ranges (avoid years of history at once)
- [ ] Check if messages already exist (skip duplicates)
- [ ] Set appropriate delay (5 seconds is good default)
- [ ] Enable FloodWaitError handling
- [ ] Consider batch fetching for large date ranges (> 30 days)

### During Fetching

- [ ] Monitor for FloodWaitError
- [ ] Respect all delays (never bypass)
- [ ] Use progress callbacks to show status
- [ ] Allow cancellation if needed
- [ ] Log fetch progress
- [ ] Take breaks between large batches

### Safety Measures

- [ ] Fetch in batches for large date ranges
- [ ] Take breaks between large fetches (5-10 minutes)
- [ ] Monitor account status regularly
- [ ] Use incremental fetching for regular updates
- [ ] Consider disabling reactions for historical fetches
- [ ] Stop immediately on account warnings

### Current Implementation Status

- ✅ FloodWaitError handling implemented
- ✅ Configurable delay (fetch_delay_seconds: 5.0s)
- ✅ Skips existing messages
- ✅ Uses efficient iter_messages with offset_date
- ✅ Reaction fetching with separate delay (0.5s)
- ✅ Progress callbacks
- ✅ Error logging

### Recommendations for Enhancement

- Consider batch fetching for large date ranges (> 30 days)
- Add dynamic delay based on fetch progress
- Consider disabling reactions for very old messages (> 1 year)
- Add break periods between large batches
- Monitor and log FloodWaitError frequency
- Add incremental fetching option (fetch only new messages)

---

## References

- [Telegram Bot API Documentation](https://core.telegram.org/api)
- [Telethon Documentation](https://docs.telethon.dev/)
- [Telegram Terms of Service](https://telegram.org/tos)
- [Telegram Privacy Policy](https://telegram.org/privacy)

---

## Last Updated

**November 23, 2025** - Based on latest Telegram API restrictions and best practices for message fetching.

---

## Important Reminders

1. **5 seconds delay is a good default** - Don't go below 1 second
2. **Always respect FloodWaitError** - Never ignore or bypass
3. **Fetch in batches** - For date ranges > 30 days
4. **Skip existing messages** - Avoid redundant API calls
5. **Monitor for warnings** - Stop if account gets restricted
6. **Use incremental fetching** - For regular updates, fetch only new messages
7. **Take breaks** - Between large batches to avoid continuous fetching
8. **Test with non-official accounts** - Never risk your main account

---

**⚠️ Remember: While message fetching is safer than adding users, account restrictions are still possible with abusive behavior. When in doubt, use more conservative limits and longer delays.**

