"""
Application constants and configuration.
"""

import os
import sys
import platform
import logging
from pathlib import Path
from dotenv import load_dotenv

# Application Info (needed for get_user_data_dir)
APP_NAME = os.getenv("APP_NAME", "Telegram User Tracking")

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

# Load environment variables AFTER user data dir is defined
# Priority: 1) User data directory .env (for bundled apps), 2) Current directory .env (for dev)
if getattr(sys, 'frozen', False):
    # Running from bundle - look for .env in user data directory
    env_file = USER_DATA_DIR / ".env"
    if env_file.exists():
        load_dotenv(env_file)
        logger = logging.getLogger(__name__)
        logger.debug(f"Loaded .env from user data directory: {env_file}")
    else:
        # Fallback to current directory (if .env exists there)
        load_dotenv()
else:
    # Development - load from project root
    load_dotenv()

# Application Info (reload after .env is loaded)
APP_NAME = os.getenv("APP_NAME", "Telegram User Tracking")
APP_VERSION = os.getenv("APP_VERSION", "1.0.0")
DEVELOPER_NAME = os.getenv("DEVELOPER_NAME", "Vothana CHY")
DEVELOPER_EMAIL = os.getenv("DEVELOPER_EMAIL", "vothanachy.es@gmail.com")
DEVELOPER_CONTACT = os.getenv("DEVELOPER_CONTACT", "+85510826027")

def get_app_data_dir() -> Path:
    """
    Get application data directory (for logs, sessions, etc.).
    
    Priority:
    1. If running from PyInstaller bundle (production) → use USER_DATA_DIR
    2. If APP_DATA_DIR env var is set → use that
    3. Otherwise (development) → use BASE_DIR (project root)
    
    Returns:
        Path to application data directory
    """
    # Check if running from PyInstaller bundle (production)
    if getattr(sys, 'frozen', False):
        # Production: use user data directory
        return USER_DATA_DIR
    
    # Development: check environment variable
    app_data_dir = os.getenv("APP_DATA_DIR", "").strip()
    if app_data_dir:
        # Use custom directory from env var
        return Path(app_data_dir)
    
    # Default: use project root (current development behavior)
    return BASE_DIR

# Application data directory (for logs, sessions, etc.)
APP_DATA_DIR = get_app_data_dir()

def _resolve_path(env_var: str, default_path: Path, base_dir: Path = None) -> str:
    """
    Resolve a path from environment variable or default.
    If env var is a relative path and base_dir is provided, resolve relative to base_dir.
    If env var is absolute, use it as-is.
    
    Args:
        env_var: Environment variable name
        default_path: Default Path object (used if env var not set)
        base_dir: Base directory for resolving relative paths (defaults to APP_DATA_DIR)
                  If None, paths are resolved relative to BASE_DIR
    
    Returns:
        Resolved path as string
    """
    env_value = os.getenv(env_var, "").strip()
    
    if not env_value:
        # Use default path
        return str(default_path)
    
    env_path = Path(env_value)
    
    # If path is absolute, use it as-is
    if env_path.is_absolute():
        return str(env_path)
    
    # If path is relative, resolve it relative to base_dir (or BASE_DIR if base_dir is None)
    # This allows relative paths like "./data/app.db" or "data/app.db" to be resolved
    # relative to APP_DATA_DIR when APP_DATA_DIR is set
    if base_dir is None:
        base_dir = BASE_DIR
    
    # Normalize the relative path (remove ./ prefix if present)
    normalized_path = env_path.as_posix().lstrip('./')
    resolved = (base_dir / normalized_path).resolve()
    return str(resolved)

# Database path: Use env var if set (for development), otherwise use secure directory
# NOTE: For authenticated users, per-user databases are stored in USER_DATA_DIR/databases/app_{firebase_uid}.db
# This DATABASE_PATH is used as a fallback for non-authenticated users or when Firebase is not configured.
# See utils/database_path.py for per-user database path generation.
# If DATABASE_PATH is a relative path and APP_DATA_DIR is set, it will be resolved relative to APP_DATA_DIR.
DATABASE_PATH = _resolve_path("DATABASE_PATH", USER_DATA_DIR / "app.db", APP_DATA_DIR)

# Sample database path
SAMPLE_DATABASE_PATH = str(APP_DATA_DIR / "sample_db" / "app.db")

# Downloads: Can also use secure directory or keep in project for development
# If DEFAULT_DOWNLOAD_DIR is a relative path and APP_DATA_DIR is set, it will be resolved relative to APP_DATA_DIR.
DEFAULT_DOWNLOAD_DIR = _resolve_path("DEFAULT_DOWNLOAD_DIR", USER_DATA_DIR / "downloads", APP_DATA_DIR)

# Theme
PRIMARY_COLOR = os.getenv("PRIMARY_COLOR", "#082f49")

# Theme Colors
COLORS = {
    "primary": PRIMARY_COLOR,
    "primary_dark": "#041724",
    "primary_light": "#0c4a68",
    "secondary": "#075985",  # Much darker blue for reduced eye strain in dark mode
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
TELEGRAM_DEVICE_MODEL = os.getenv("TELEGRAM_DEVICE_MODEL", "ESC_APP")  # Device model for Telethon
MAX_FETCH_RETRIES = 3
DEFAULT_FETCH_DELAY = 5.0  # seconds
DEFAULT_MAX_FILE_SIZE_MB = 3

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
# Note: License tiers are now managed in the admin app and stored in Firestore.
# Use services/license/license_tier_service.py to fetch tier definitions dynamically.

# Default license tier (fallback when no license found)
DEFAULT_LICENSE_TIER = "premium"

# Update System Settings
UPDATE_CHECK_INTERVAL_SECONDS = 3600  # 1 hour
UPDATES_DIR_NAME = "updates"
FIREBASE_APP_UPDATES_COLLECTION = "app_updates"
FIRESTORE_NOTIFICATIONS_COLLECTION = "notifications"
FIRESTORE_USER_NOTIFICATIONS_COLLECTION = "user_notifications"
FIREBASE_APP_UPDATES_DOCUMENT = "latest"

