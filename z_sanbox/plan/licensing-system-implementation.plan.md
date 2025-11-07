<!-- cc45e83d-f296-44fb-ad4f-80d10c941902 5605b4ee-d80c-4f34-bfe0-829f66892ca5 -->
# Licensing System Implementation Plan

## Overview

Add a three-tier licensing system with Firebase-based license tracking, device/group limits enforcement, and a new About page with pricing display. Users contact admin for upgrades (no payment integration).

## Subscription Tiers (Cambodian Market Pricing)

### Silver Tier - $5/month (20,000 KHR)

- Max 3 groups
- 1 device allowed
- Target: Individual users, small team leads

### Gold Tier - $12/month (48,000 KHR)

- Max 10 groups
- 2 devices allowed
- Target: Team leads managing multiple projects

### Premium Tier - $25/month (100,000 KHR)

- Unlimited groups
- 5 devices allowed
- Priority support
- Target: Senior managers, business intelligence teams

## Implementation Steps

### 1. Firebase Firestore Integration

Create a new Firestore collection `user_licenses` to store:

- User ID (uid from Firebase Auth)
- License tier (silver, gold, premium)
- Expiration date
- Active device IDs (array)
- Max devices allowed
- Max groups allowed
- Purchase/renewal history
- Admin notes

Files to create/modify:

- `config/firebase_config.py` - Add Firestore initialization and methods
- `services/license_service.py` - New service for license management

### 2. Database Schema Updates

Add local SQLite tables for caching license info:

**user_license_cache table:**

- user_email
- license_tier
- expiration_date
- max_devices
- max_groups
- last_synced
- is_active

Modify: `database/models.py`, `database/db_manager.py`

### 3. License Service Layer

Create `services/license_service.py` with methods:

- `check_license_status()` - Verify active subscription
- `get_user_tier()` - Return current tier
- `sync_from_firebase()` - Pull latest license data
- `can_add_group()` - Check group limit
- `can_add_device()` - Check device limit
- `get_active_devices()` - List registered devices
- `enforce_group_limit()` - Block if over limit

### 4. Top Header/Navigation Bar Component

Create `ui/components/top_header.py`:

- Left side: Time-based greeting ("Good morning/afternoon/evening [User]") → Dashboard on click
- Right side: About icon button → Navigate to About page
- Use Row layout, full width, minimal height (~50-60px)
- Match theme colors

Modify `ui/app.py`:

- Add top_header between connectivity_banner and main content Row
- Pass navigation callback to header

### 5. About Page with Tabs

Create `ui/pages/about_page.py`:

- Tab 1: **About** - App info, developer info (moved from profile_page.py)
- Tab 2: **Pricing** - Subscription tier cards

**About Tab Content:**

- App name, version, description
- Developer info (name, email, contact)
- Features overview
- License info (current tier, expiration, devices used)

**Pricing Tab Content:**

- Three pricing cards (similar to Cursor website style)
- Feature comparison table
- Each card shows:
  - Tier name with icon
  - Price (USD and KHR)
  - Max groups
  - Max devices
  - Feature list with checkmarks
  - "Contact Admin" button (opens email or shows contact info)
- Highlight user's current tier

### 6. Group Limit Enforcement

Modify `ui/dialogs/fetch_data_dialog.py` and `services/telegram_service.py`:

- Before allowing group selection/add, call `license_service.can_add_group()`
- If limit reached, show dialog:
  - Current tier and limit
  - Groups currently tracked
  - Upgrade prompt with "Contact Admin" button
  - Prevent fetch operation

### 7. Device Limit Enforcement

Modify `services/auth_service.py`:

- On login, check device count via `license_service.can_add_device()`
- Store active device IDs in Firebase
- If limit reached, show list of active devices and prompt to:
  - Contact admin to upgrade
  - Deactivate a device (admin action)

### 8. Profile Page Updates

Modify `ui/pages/profile_page.py`:

- Add license status card showing:
  - Current tier (with color badge)
  - Expiration date (with countdown if < 7 days)
  - Devices used (X/Y)
  - Groups used (X/Y)
  - "View Pricing" button → Navigate to About page, Pricing tab
- Keep existing logout functionality

### 9. Translations

Add to `locales/en.json` and `locales/km.json`:

- Tier names
- Pricing page labels
- License status messages
- Upgrade prompts
- Time greetings (morning, afternoon, evening)
- About page content

English additions:

```
"good_morning": "Good Morning",
"good_afternoon": "Good Afternoon", 
"good_evening": "Good Evening",
"about": "About",
"pricing": "Pricing",
"subscription": "Subscription",
"license_tier": "License Tier",
"expires_on": "Expires On",
"active_devices": "Active Devices",
"groups_used": "Groups Used",
"upgrade_required": "Upgrade Required",
"contact_admin_to_upgrade": "Contact admin to upgrade your subscription",
"silver_tier": "Silver",
"gold_tier": "Gold",
"premium_tier": "Premium",
"per_month": "per month",
"max_groups": "Max Groups",
"max_devices": "Max Devices",
"contact_admin": "Contact Admin",
"current_plan": "Current Plan",
"upgrade_to": "Upgrade to",
"feature_unlimited_groups": "Unlimited Groups",
"feature_priority_support": "Priority Support"
```

### 10. Constants and Configuration

Modify `utils/constants.py`:

- Add tier definitions (SILVER, GOLD, PREMIUM)
- Add pricing constants (USD and KHR)
- Add max group/device limits per tier

## Marketing Suggestions (Cambodian Market)

### Target Audience

1. **Team Leads in Tech Companies** - Managing developer/marketing teams using Telegram
2. **SME Business Owners** - Monitoring employee communication and customer groups
3. **Project Managers** - Tracking multiple project group communications
4. **HR Departments** - Monitoring company group activity and compliance

### Value Propositions

- "Track your team's Telegram activity and never miss important updates"
- "Khmer language support for local businesses"
- "Secure tracking with Firebase authentication"
- "Export reports to Excel/PDF for management review"

### Marketing Channels

1. **Facebook Business Groups** - Target Cambodian business/tech groups
2. **LinkedIn** - Professional networking in Cambodia
3. **Telegram Groups** - Ironically, promote in business/tech Telegram groups
4. **Word of Mouth** - Offer referral discounts (10% off for referrer and referee)

### Localization

- All marketing materials in both English and Khmer
- Pricing in both USD and KHR
- Local payment methods consideration (future: ABA, Wing, etc.)
- Cambodian business hour support

### Promotional Strategy

- **Launch Offer**: First 50 users get 20% off for 6 months
- **Annual Plans**: 2 months free (10 months price for 12 months)
- **Team Discounts**: 3+ licenses get 15% off
- **Free Consultation**: 30-minute demo for potential Gold/Premium users

## Technical Implementation Notes

### Firebase Requirements

- Enable Firestore in Firebase Console
- Create indexes for queries (uid, expiration_date)
- Set up security rules to prevent client-side tampering
- Only server (Firebase Admin SDK) can write license data

### Admin Management

For now, admin manually:

1. Creates user in Firebase Auth
2. Adds license document to Firestore with tier and expiration
3. Notifies user credentials via email
4. User logs in and sees their tier/limits

Future enhancement: Admin dashboard web app

### License Expiration Handling

- Check on every app launch
- Show warning when < 7 days to expiration
- Block all tracking features when expired
- Show "Contact Admin to Renew" dialog

### Upgrade Flow (Manual)

1. User clicks "Contact Admin" or "Upgrade"
2. Opens email client with pre-filled template:

   - Current tier
   - Desired tier
   - Reason for upgrade
   - Device info

3. Admin processes request
4. Admin updates Firestore license
5. User receives email confirmation
6. User refreshes app to see new tier

## Files Summary

**New Files:**

- `services/license_service.py`
- `ui/components/top_header.py`
- `ui/pages/about_page.py`

**Modified Files:**

- `config/firebase_config.py`
- `database/models.py`
- `database/db_manager.py`
- `services/auth_service.py`
- `ui/app.py`
- `ui/pages/profile_page.py`
- `ui/dialogs/fetch_data_dialog.py`
- `services/telegram_service.py`
- `locales/en.json`
- `locales/km.json`
- `utils/constants.py`

## Testing Checklist

- Login with expired license → blocked
- Try adding group beyond limit → blocked with upgrade prompt
- Try logging in on multiple devices → blocked at device limit
- Time-based greeting shows correct message
- Pricing cards display correctly in both languages
- License info syncs from Firebase to local cache
- Profile page shows accurate tier info

### To-dos

- [ ] Add Firestore initialization and CRUD methods to firebase_config.py for user_licenses collection
- [ ] Add user_license_cache table to models.py and create migration in db_manager.py
- [ ] Create license_service.py with tier checking, limit enforcement, and Firebase sync logic
- [ ] Add tier definitions, pricing, and limits to constants.py
- [ ] Add all licensing-related translations to en.json and km.json
- [ ] Create top_header.py component with greeting and About navigation
- [ ] Create about_page.py with About and Pricing tabs, including pricing cards UI
- [ ] Integrate top_header into main app.py layout and wire navigation
- [ ] Add license status card to profile_page.py showing tier, expiration, and limits
- [ ] Add group limit checks in fetch_data_dialog.py and telegram_service.py with upgrade prompts
- [ ] Add device limit checks in auth_service.py during login with device management UI
- [ ] Add license expiration check on app launch in app.py with renewal prompts