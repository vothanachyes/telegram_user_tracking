"""
Application constants and configuration.
"""

import os
import platform
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables FIRST
load_dotenv()

# Application Info
APP_NAME = os.getenv("APP_NAME", "Telegram User Tracking")
APP_VERSION = os.getenv("APP_VERSION", "1.0.0")
DEVELOPER_NAME = os.getenv("DEVELOPER_NAME", "Vothana CHY")
DEVELOPER_EMAIL = os.getenv("DEVELOPER_EMAIL", "vothanachy.es@gmail.com")
DEVELOPER_CONTACT = os.getenv("DEVELOPER_CONTACT", "+85510826027")

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent

def get_user_data_dir() -> Path:
    """Get platform-specific user data directory for secure storage."""
    system = platform.system()
    
    if system == "Windows":
        # %APPDATA%\Telegram User Tracking
        base = Path(os.getenv("APPDATA", Path.home() / "AppData" / "Roaming"))
        return base / APP_NAME
    elif system == "Darwin":  # macOS
        # ~/Library/Application Support/Telegram User Tracking
        return Path.home() / "Library" / "Application Support" / APP_NAME
    else:  # Linux and others
        # ~/.config/Telegram User Tracking
        return Path.home() / ".config" / APP_NAME

# Get secure user data directory and ensure it exists
USER_DATA_DIR = get_user_data_dir()
USER_DATA_DIR.mkdir(parents=True, exist_ok=True)

# Database path: Use env var if set (for development), otherwise use secure directory
DATABASE_PATH = os.getenv("DATABASE_PATH", str(USER_DATA_DIR / "app.db"))

# Downloads: Can also use secure directory or keep in project for development
DEFAULT_DOWNLOAD_DIR = os.getenv("DEFAULT_DOWNLOAD_DIR", str(USER_DATA_DIR / "downloads"))

# Theme
PRIMARY_COLOR = os.getenv("PRIMARY_COLOR", "#082f49")

# Theme Colors
COLORS = {
    "primary": PRIMARY_COLOR,
    "primary_dark": "#041724",
    "primary_light": "#0c4a68",
    "secondary": "#0ea5e9",
    "success": "#10b981",
    "warning": "#f59e0b",
    "error": "#ef4444",
    "info": "#3b82f6",
    "background_dark": "#0f172a",
    "background_light": "#f8fafc",
    "surface_dark": "#1e293b",
    "surface_light": "#ffffff",
    "text_dark": "#f8fafc",
    "text_light": "#0f172a",
    "text_secondary_dark": "#94a3b8",
    "text_secondary_light": "#64748b",
    "border_dark": "#334155",
    "border_light": "#e2e8f0",
}

# Supported Languages
LANGUAGES = {
    "en": "English",
    "km": "ភាសាខ្មែរ"  # Khmer
}

# Media Types
MEDIA_TYPES = {
    "photo": "Photo",
    "video": "Video",
    "document": "Document",
    "audio": "Audio"
}

# Date Formats
DATE_FORMAT = "%Y-%m-%d"
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
TIME_FORMAT = "%H:%M:%S"

# Telegram Settings
TELEGRAM_SESSION_NAME = "telegram_session"
TELEGRAM_DEVICE_MODEL = os.getenv("TELEGRAM_DEVICE_MODEL", "ESC_APP")  # None = use Pyrogram default
MAX_FETCH_RETRIES = 3
DEFAULT_FETCH_DELAY = 1.0  # seconds
DEFAULT_MAX_FILE_SIZE_MB = 50

# UI Settings
DEFAULT_CORNER_RADIUS = 10
MIN_CORNER_RADIUS = 0
MAX_CORNER_RADIUS = 30
DEFAULT_WINDOW_WIDTH = 900
DEFAULT_WINDOW_HEIGHT = 650
MIN_WINDOW_WIDTH = 600
MIN_WINDOW_HEIGHT = 650

# Splash Screen Settings
SPLASH_SCREEN_DURATION = float(os.getenv("SPLASH_SCREEN_DURATION", "2.0"))  # Minimum duration in seconds

# Table Settings
DEFAULT_PAGE_SIZE = 50
PAGE_SIZE_OPTIONS = [25, 50, 100, 200]

# Export Settings
EXCEL_MAX_ROWS = 1048576
PDF_PAGE_SIZE = "A4"

# Firebase Settings
FIREBASE_CREDENTIALS_PATH = os.getenv("FIREBASE_CREDENTIALS_PATH", "")
FIREBASE_PROJECT_ID = os.getenv("FIREBASE_PROJECT_ID", "")
FIREBASE_WEB_API_KEY = os.getenv("FIREBASE_WEB_API_KEY", "")

# Folder Structure Template
# {rootDir}/{group_id}/{username}/{date}/{messageId_time}/
FOLDER_STRUCTURE = "{root_dir}/{group_id}/{username}/{date}/{message_id}_{time}"

# File Size Units
def format_bytes(bytes_size: int) -> str:
    """Format bytes to human readable format."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.2f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.2f} PB"

# Validation Patterns
PHONE_PATTERN = r"^\+?[1-9]\d{1,14}$"
EMAIL_PATTERN = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"

# License Tiers
LICENSE_TIER_BRONZE = "bronze"
LICENSE_TIER_SILVER = "silver"
LICENSE_TIER_GOLD = "gold"
LICENSE_TIER_PREMIUM = "premium"

# License Pricing (USD and KHR)
LICENSE_PRICING = {
    LICENSE_TIER_BRONZE: {
        "name": "Bronze",
        "price_usd": 0,
        "price_khr": 0,
        "max_groups": 1,
        "max_devices": 1,
        "period": 3,  # 7 days trial period
        "features": ["max_groups", "max_devices"]
    },
    LICENSE_TIER_SILVER: {
        "name": "Silver",
        "price_usd": 5,
        "price_khr": 20000,
        "max_groups": 3,
        "max_devices": 1,
        "period": 30,  # 30 days subscription period
        "features": ["max_groups", "max_devices"]
    },
    LICENSE_TIER_GOLD: {
        "name": "Gold",
        "price_usd": 12,
        "price_khr": 48000,
        "max_groups": 10,
        "max_devices": 2,
        "period": 30,  # 30 days subscription period
        "features": ["max_groups", "max_devices"]
    },
    LICENSE_TIER_PREMIUM: {
        "name": "Premium",
        "price_usd": 25,
        "price_khr": 100000,
        "max_groups": -1,  # -1 means unlimited
        "max_devices": 5,
        "period": 30,  # 30 days subscription period
        "features": ["unlimited_groups", "max_devices", "priority_support"]
    }
}

# Default license tier
DEFAULT_LICENSE_TIER = LICENSE_TIER_BRONZE

