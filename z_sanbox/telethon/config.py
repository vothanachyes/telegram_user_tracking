"""
Configuration settings for Telegram Group Exporter.
All values must be provided via .env file.
"""
from datetime import datetime
from pathlib import Path
from typing import Optional
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Application configuration."""
    
    # Telegram API credentials (required)
    API_ID: int = int(os.getenv("API_ID") or "0")
    API_HASH: str = os.getenv("API_HASH") or ""
    PHONE_NUMBER: str = os.getenv("PHONE_NUMBER") or ""
    
    # Group settings (required)
    GROUP_ID: int = int(os.getenv("GROUP_ID") or "0")
    
    # Export settings (required)
    _export_folder_str: str = os.getenv("EXPORT_FOLDER") or ""
    EXPORT_FOLDER: Path = Path(_export_folder_str) if _export_folder_str else Path(".")
    MAX_FILE_SIZE_MB: float = float(os.getenv("MAX_FILE_SIZE_MB") or "500")
    RATE_LIMIT: float = float(os.getenv("RATE_LIMIT") or "2")
    MAX_RETRIES: int = int(os.getenv("MAX_RETRIES") or "3")
    
    # Date range (required)
    START_DATE_STR: str = os.getenv("START_DATE") or ""
    END_DATE_STR: str = os.getenv("END_DATE") or ""
    
    # Session file (optional, defaults to user_session)
    SESSION_NAME: str = os.getenv("SESSION_NAME", "user_session")
    
    @classmethod
    def _parse_date(cls, date_str: str) -> Optional[datetime]:
        """Parse date string in format YYYY-MM-DD or YYYY-MM-DD HH:MM:SS."""
        if not date_str:
            return None
        try:
            # Try with time first
            if len(date_str) > 10:
                return datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
            else:
                return datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            return None
    
    @classmethod
    def get_start_date(cls) -> datetime:
        """Get start date from config."""
        return cls._parse_date(cls.START_DATE_STR) or datetime(2025, 4, 28)
    
    @classmethod
    def get_end_date(cls) -> datetime:
        """Get end date from config."""
        return cls._parse_date(cls.END_DATE_STR) or datetime(2025, 7, 31, 23, 59, 59)
    
    @classmethod
    def validate(cls) -> tuple[bool, Optional[str]]:
        """Validate configuration settings."""
        if not cls.API_ID or cls.API_ID == 0:
            return False, "API_ID must be set in .env file"
        
        if not cls.API_HASH:
            return False, "API_HASH must be set in .env file"
        
        if not cls.PHONE_NUMBER:
            return False, "PHONE_NUMBER must be set in .env file"
        
        if not cls.GROUP_ID or cls.GROUP_ID == 0:
            return False, "GROUP_ID must be set in .env file"
        
        if not cls._export_folder_str or not cls._export_folder_str.strip():
            return False, "EXPORT_FOLDER must be set in .env file"
        
        # Resolve relative paths to absolute paths for consistency
        cls.EXPORT_FOLDER = Path(cls._export_folder_str).resolve()
        
        if cls.MAX_FILE_SIZE_MB <= 0:
            return False, "MAX_FILE_SIZE_MB must be greater than 0"
        
        if cls.RATE_LIMIT < 0:
            return False, "RATE_LIMIT must be non-negative"
        
        start_date = cls.get_start_date()
        end_date = cls.get_end_date()
        
        if not cls.START_DATE_STR:
            return False, "START_DATE must be set in .env file (format: YYYY-MM-DD or YYYY-MM-DD HH:MM:SS)"
        
        if not cls.END_DATE_STR:
            return False, "END_DATE must be set in .env file (format: YYYY-MM-DD or YYYY-MM-DD HH:MM:SS)"
        
        if start_date >= end_date:
            return False, "START_DATE must be before END_DATE"
        
        return True, None
    
    @classmethod
    def get_session_path(cls) -> Path:
        """Get the full path to the session file."""
        return Path(cls.SESSION_NAME + ".session")
    
    @classmethod
    def ensure_export_folder(cls) -> None:
        """Ensure the export folder exists."""
        cls.EXPORT_FOLDER.mkdir(parents=True, exist_ok=True)

