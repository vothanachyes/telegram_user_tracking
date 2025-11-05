"""
Application constants and configuration.
"""

import os
from pathlib import Path

# Application Info
APP_NAME = os.getenv("APP_NAME", "Telegram User Tracking")
APP_VERSION = os.getenv("APP_VERSION", "1.0.0")
DEVELOPER_NAME = os.getenv("DEVELOPER_NAME", "Your Name")
DEVELOPER_EMAIL = os.getenv("DEVELOPER_EMAIL", "your.email@example.com")
DEVELOPER_CONTACT = os.getenv("DEVELOPER_CONTACT", "+1234567890")

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE_PATH = os.getenv("DATABASE_PATH", str(BASE_DIR / "data" / "app.db"))
DEFAULT_DOWNLOAD_DIR = os.getenv("DEFAULT_DOWNLOAD_DIR", str(BASE_DIR / "downloads"))

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
MAX_FETCH_RETRIES = 3
DEFAULT_FETCH_DELAY = 1.0  # seconds
DEFAULT_MAX_FILE_SIZE_MB = 50

# UI Settings
DEFAULT_CORNER_RADIUS = 10
MIN_CORNER_RADIUS = 0
MAX_CORNER_RADIUS = 30
DEFAULT_WINDOW_WIDTH = 1400
DEFAULT_WINDOW_HEIGHT = 900
MIN_WINDOW_WIDTH = 1200
MIN_WINDOW_HEIGHT = 700

# Table Settings
DEFAULT_PAGE_SIZE = 50
PAGE_SIZE_OPTIONS = [25, 50, 100, 200]

# Export Settings
EXCEL_MAX_ROWS = 1048576
PDF_PAGE_SIZE = "A4"

# Firebase Settings
FIREBASE_CREDENTIALS_PATH = os.getenv("FIREBASE_CREDENTIALS_PATH", "")
FIREBASE_PROJECT_ID = os.getenv("FIREBASE_PROJECT_ID", "")

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

