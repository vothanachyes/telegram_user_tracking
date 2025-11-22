"""
Admin-specific constants.
"""

# Firestore Collections
FIRESTORE_USER_LICENSES_COLLECTION = "user_licenses"
FIRESTORE_APP_UPDATES_COLLECTION = "app_updates"
FIRESTORE_APP_UPDATES_DOCUMENT = "latest"

# Admin Session
ADMIN_SESSION_TIMEOUT_MINUTES = 60  # 1 hour

# Page IDs
PAGE_LOGIN = "login"
PAGE_DASHBOARD = "dashboard"
PAGE_USERS = "users"
PAGE_LICENSES = "licenses"
PAGE_APP_UPDATES = "app_updates"
PAGE_DEVICES = "devices"
PAGE_ACTIVITY_LOGS = "activity_logs"
PAGE_BULK_OPERATIONS = "bulk_operations"

# License Tiers (from main app constants)
LICENSE_TIER_BRONZE = "bronze"
LICENSE_TIER_SILVER = "silver"
LICENSE_TIER_GOLD = "gold"
LICENSE_TIER_PREMIUM = "premium"

LICENSE_TIERS = [
    LICENSE_TIER_BRONZE,
    LICENSE_TIER_SILVER,
    LICENSE_TIER_GOLD,
    LICENSE_TIER_PREMIUM,
]

# Table Pagination
DEFAULT_PAGE_SIZE = 25
MAX_PAGE_SIZE = 100

