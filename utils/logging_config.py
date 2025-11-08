"""
Logging configuration for the application.
"""

import logging
import sys
import os
import re
import json
from pathlib import Path
from datetime import datetime
from logging.handlers import TimedRotatingFileHandler

from utils.constants import BASE_DIR


class LevelFilter(logging.Filter):
    """Filter to allow only specific log levels."""
    def __init__(self, allowed_levels):
        super().__init__()
        self.allowed_levels = allowed_levels
    
    def filter(self, record):
        return record.levelno in self.allowed_levels


class CategoryFilter(logging.Filter):
    """Filter to route logs to category-specific handlers based on logger names."""
    
    def __init__(self, category: str):
        """
        Initialize category filter.
        
        Args:
            category: One of 'database', 'firebase', 'telegram', 'flet', 'general'
        """
        super().__init__()
        self.category = category
        
        # Define logger name patterns for each category
        self.patterns = {
            'database': ['database.'],
            'firebase': ['config.firebase_config', 'services.auth_service'],
            'telegram': ['services.telegram.', 'pyrogram'],
            'flet': ['flet'],
            'general': []  # Will match everything not matched by other categories
        }
    
    def filter(self, record):
        """Filter logs based on logger name and category."""
        logger_name = record.name
        
        if self.category == 'general':
            # General category: match everything NOT matched by other categories
            for cat, patterns in self.patterns.items():
                if cat == 'general':
                    continue
                for pattern in patterns:
                    if pattern in logger_name:
                        return False  # Exclude from general
            return True  # Include in general
        
        # For specific categories: match if logger name contains pattern
        patterns = self.patterns.get(self.category, [])
        for pattern in patterns:
            if pattern in logger_name:
                return True
        
        return False


class FletDebugFilter(logging.Filter):
    """Filter to exclude Flet DEBUG logs from console output."""
    
    def __init__(self, enabled: bool = False):
        """
        Initialize Flet debug filter.
        
        Args:
            enabled: If True, allow Flet DEBUG logs. If False, filter them out.
                    Defaults to False (filter out by default).
        """
        super().__init__()
        self.enabled = enabled
    
    def filter(self, record):
        """
        Filter logs based on logger name and level.
        
        Returns:
            False to filter out Flet DEBUG logs when enabled=False
            True to allow all other logs
        """
        # If Flet debug logs are enabled, allow all logs
        if self.enabled:
            return True
        
        # Filter out if it's a Flet logger AND level is DEBUG
        if 'flet' in record.name.lower() and record.levelno == logging.DEBUG:
            return False  # Filter out
        
        return True  # Allow all other logs


class DateFolderRotatingFileHandler(TimedRotatingFileHandler):
    """File handler that creates date-based folders and rotates daily."""
    
    def __init__(self, category: str, base_dir: Path, allowed_levels=None, **kwargs):
        """
        Initialize date-based rotating file handler.
        
        Args:
            category: Log category (database, firebase, telegram, flet, general)
            base_dir: Base directory for logs (e.g., logs/)
            allowed_levels: List of allowed log levels
            **kwargs: Additional arguments for TimedRotatingFileHandler
        """
        self.category = category
        self.base_dir = Path(base_dir)
        self.allowed_levels = allowed_levels or []
        
        # Create category directory
        self.category_dir = self.base_dir / category
        self.category_dir.mkdir(parents=True, exist_ok=True)
        
        # Get today's date for filename
        today = datetime.now().strftime('%Y-%m-%d')
        log_file = self.category_dir / f"{today}.log"
        
        # Set default rotation parameters
        kwargs.setdefault('when', 'midnight')
        kwargs.setdefault('interval', 1)
        kwargs.setdefault('backupCount', 0)  # Keep all files, no automatic deletion
        
        super().__init__(
            filename=str(log_file),
            **kwargs
        )
        
        # Add level filter if specified
        if self.allowed_levels:
            level_filter = LevelFilter(self.allowed_levels)
            self.addFilter(level_filter)
        
        # Add category filter
        category_filter = CategoryFilter(category)
        self.addFilter(category_filter)
    
    def doRollover(self):
        """Override to create new date-based file on rotation."""
        # Close current file
        if self.stream:
            self.stream.close()
            self.stream = None
        
        # Get new date for filename
        today = datetime.now().strftime('%Y-%m-%d')
        log_file = self.category_dir / f"{today}.log"
        
        # Update baseFilename for next rotation
        self.baseFilename = str(log_file)
        
        # Open new file
        self.stream = self._open()


class ANSIColors:
    """ANSI color codes for terminal output."""
    # Reset
    RESET = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    
    # Text colors
    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'
    
    # Bright colors
    BRIGHT_BLACK = '\033[90m'
    BRIGHT_RED = '\033[91m'
    BRIGHT_GREEN = '\033[92m'
    BRIGHT_YELLOW = '\033[93m'
    BRIGHT_BLUE = '\033[94m'
    BRIGHT_MAGENTA = '\033[95m'
    BRIGHT_CYAN = '\033[96m'
    BRIGHT_WHITE = '\033[97m'
    
    # Background colors
    BG_BLACK = '\033[40m'
    BG_RED = '\033[41m'
    BG_GREEN = '\033[42m'
    BG_YELLOW = '\033[43m'
    BG_BLUE = '\033[44m'
    BG_MAGENTA = '\033[45m'
    BG_CYAN = '\033[46m'
    BG_WHITE = '\033[47m'


class ColoredFormatter(logging.Formatter):
    """Custom formatter that colors different parts of log messages."""
    
    # Category colors
    CATEGORY_COLORS = {
        'database': ANSIColors.CYAN,
        'firebase': ANSIColors.YELLOW,
        'telegram': ANSIColors.GREEN,
        'flet': ANSIColors.MAGENTA,
        'general': ANSIColors.WHITE,
    }
    
    # Level colors
    LEVEL_COLORS = {
        'DEBUG': ANSIColors.BRIGHT_BLACK,
        'INFO': ANSIColors.BRIGHT_GREEN,
        'WARNING': ANSIColors.BRIGHT_YELLOW,
        'ERROR': ANSIColors.BRIGHT_RED,
        'CRITICAL': ANSIColors.BRIGHT_RED + ANSIColors.BOLD,
    }
    
    # Element colors
    DATE_COLOR = ANSIColors.BRIGHT_BLACK
    LOGGER_COLOR = ANSIColors.BRIGHT_CYAN
    URL_COLOR = ANSIColors.BRIGHT_BLUE
    JSON_COLOR = ANSIColors.BRIGHT_MAGENTA
    LIST_COLOR = ANSIColors.BRIGHT_CYAN
    NUMBER_COLOR = ANSIColors.BRIGHT_YELLOW
    EVENT_COLOR = ANSIColors.BRIGHT_GREEN
    PATH_COLOR = ANSIColors.BRIGHT_BLUE
    
    def __init__(self, *args, **kwargs):
        """Initialize colored formatter."""
        super().__init__(*args, **kwargs)
        
        # Patterns for detection
        self.url_pattern = re.compile(
            r'(https?://[^\s<>"{}|\\^`\[\]]+|www\.[^\s<>"{}|\\^`\[\]]+|ftp://[^\s<>"{}|\\^`\[\]]+)',
            re.IGNORECASE
        )
        self.json_pattern = re.compile(r'(\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}|\[[^\[\]]*(?:\[[^\[\]]*\][^\[\]]*)*\])')
        self.list_pattern = re.compile(r'(\[[^\]]+\])')
        self.number_pattern = re.compile(r'\b(\d+\.?\d*)\b')
        self.path_pattern = re.compile(r'([/\\][^\s<>"{}|\\^`\[\]]+|\.(?:py|js|ts|json|log|db|sql|txt|md|yml|yaml)\b)')
        self.event_pattern = re.compile(r'\b(event|Event|EVENT|action|Action|ACTION|trigger|Trigger|TRIGGER)\b')
        self.date_pattern = re.compile(r'\b(\d{4}-\d{2}-\d{2}|\d{2}/\d{2}/\d{4}|\d{2}-\d{2}-\d{4})\b')
        self.time_pattern = re.compile(r'\b(\d{2}:\d{2}:\d{2}(?:\.\d+)?)\b')
    
    def _get_category(self, logger_name: str) -> str:
        """Get category for a logger based on its name."""
        if 'database.' in logger_name:
            return 'database'
        elif 'config.firebase_config' in logger_name or 'services.auth_service' in logger_name:
            return 'firebase'
        elif 'services.telegram.' in logger_name or 'pyrogram' in logger_name:
            return 'telegram'
        elif logger_name == 'flet':
            return 'flet'
        else:
            return 'general'
    
    def _colorize_message(self, message: str) -> str:
        """Colorize different elements in the message."""
        result = message
        
        # Colorize URLs (do this first to avoid conflicts)
        def colorize_url(match):
            url = match.group(1)
            return f"{self.URL_COLOR}{url}{ANSIColors.RESET}"
        result = self.url_pattern.sub(colorize_url, result)
        
        # Colorize JSON objects/arrays
        def colorize_json(match):
            json_str = match.group(1)
            try:
                # Try to parse and pretty-print JSON
                parsed = json.loads(json_str)
                formatted = json.dumps(parsed, indent=2)
                # Colorize the formatted JSON
                lines = formatted.split('\n')
                colored_lines = []
                for line in lines:
                    if ':' in line:
                        key, value = line.split(':', 1)
                        colored_line = f"{self.JSON_COLOR}{key}:{ANSIColors.RESET}{value}"
                    else:
                        colored_line = f"{self.JSON_COLOR}{line}{ANSIColors.RESET}"
                    colored_lines.append(colored_line)
                return '\n'.join(colored_lines)
            except (json.JSONDecodeError, ValueError):
                # If not valid JSON, just colorize as-is
                return f"{self.JSON_COLOR}{json_str}{ANSIColors.RESET}"
        result = self.json_pattern.sub(colorize_json, result)
        
        # Colorize lists (simple array notation)
        def colorize_list(match):
            list_str = match.group(1)
            return f"{self.LIST_COLOR}{list_str}{ANSIColors.RESET}"
        result = self.list_pattern.sub(colorize_list, result)
        
        # Colorize paths and file extensions
        def colorize_path(match):
            path = match.group(1)
            return f"{self.PATH_COLOR}{path}{ANSIColors.RESET}"
        result = self.path_pattern.sub(colorize_path, result)
        
        # Colorize dates
        def colorize_date(match):
            date_str = match.group(1)
            return f"{self.DATE_COLOR}{date_str}{ANSIColors.RESET}"
        result = self.date_pattern.sub(colorize_date, result)
        
        # Colorize times
        def colorize_time(match):
            time_str = match.group(1)
            return f"{self.DATE_COLOR}{time_str}{ANSIColors.RESET}"
        result = self.time_pattern.sub(colorize_time, result)
        
        # Colorize events
        def colorize_event(match):
            event_str = match.group(1)
            return f"{self.EVENT_COLOR}{event_str}{ANSIColors.RESET}"
        result = self.event_pattern.sub(colorize_event, result)
        
        # Colorize numbers (but not dates/times/URLs that we already colored)
        # This is a simple approach - numbers that aren't part of URLs or dates
        def colorize_number(match):
            number = match.group(1)
            # Skip if it's part of a URL or date/time
            start = match.start()
            end = match.end()
            context = result[max(0, start-10):min(len(result), end+10)]
            if '://' in context or 'www.' in context.lower() or '/' in context:
                return number
            return f"{self.NUMBER_COLOR}{number}{ANSIColors.RESET}"
        result = self.number_pattern.sub(colorize_number, result)
        
        return result
    
    def format(self, record):
        """Format log record with colors."""
        # Get category
        category = self._get_category(record.name)
        category_color = self.CATEGORY_COLORS.get(category, self.CATEGORY_COLORS['general'])
        
        # Get level color
        level_color = self.LEVEL_COLORS.get(record.levelname, ANSIColors.WHITE)
        
        # Format timestamp
        timestamp = self.formatTime(record, self.datefmt)
        colored_timestamp = f"{self.DATE_COLOR}{timestamp}{ANSIColors.RESET}"
        
        # Format logger name
        logger_name = record.name
        colored_logger = f"{self.LOGGER_COLOR}{logger_name}{ANSIColors.RESET}"
        
        # Format level
        level_name = record.levelname
        colored_level = f"{level_color}{level_name}{ANSIColors.RESET}"
        
        # Colorize message
        message = record.getMessage()
        colored_message = self._colorize_message(message)
        
        # Format exception if present
        if record.exc_info:
            exc_text = self.formatException(record.exc_info)
            colored_message += f"\n{ANSIColors.BRIGHT_RED}{exc_text}{ANSIColors.RESET}"
        
        # Build final format
        category_tag = f"{category_color}[{category.upper()}]{ANSIColors.RESET}"
        formatted = (
            f"{category_tag} {colored_timestamp} - {colored_logger} - {colored_level} - {colored_message}"
        )
        
        return formatted


class ColoredConsoleHandler(logging.StreamHandler):
    """Console handler with category-based colors and enhanced message colorization."""
    
    def __init__(self, allowed_levels=None):
        """Initialize colored console handler."""
        super().__init__(sys.stdout)
        
        if allowed_levels:
            level_filter = LevelFilter(allowed_levels)
            self.addFilter(level_filter)
        
        # Add Flet debug filter based on environment variable
        # Default: filter out Flet DEBUG logs (enabled=False)
        # Set FLET_DEBUG_LOGS_ENABLED=true in .env to show them
        flet_debug_enabled = os.getenv("FLET_DEBUG_LOGS_ENABLED", "").lower() in ("true", "1", "yes")
        flet_debug_filter = FletDebugFilter(enabled=flet_debug_enabled)
        self.addFilter(flet_debug_filter)
        
        # Create custom colored formatter
        formatter = ColoredFormatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        self.setFormatter(formatter)


def setup_logging(allowed_levels=None, log_file=None, separate_by_category=True):
    """
    Setup logging configuration with category separation and custom level filtering.
    
    Args:
        allowed_levels: List of logging levels to show. 
                       Defaults to [INFO, WARNING, ERROR, DEBUG]
        log_file: Path to log file (deprecated, kept for backward compatibility).
                 If separate_by_category is True, this is ignored.
        separate_by_category: If True, separate logs into category-specific files.
                             Defaults to True.
    """
    if allowed_levels is None:
        allowed_levels = [logging.INFO, logging.WARNING, logging.ERROR, logging.DEBUG]

    # Set up log directory
    log_dir = BASE_DIR / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)  # Set to lowest level, filter will handle the rest
    root_logger.handlers = []  # Clear any existing handlers
    
    if separate_by_category:
        # Create category-specific file handlers
        categories = ['database', 'firebase', 'telegram', 'flet', 'general']
        
        for category in categories:
            handler = DateFolderRotatingFileHandler(
                category=category,
                base_dir=log_dir,
                allowed_levels=allowed_levels
            )
            
            # Plain format for file handler (no colors in log files)
            file_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(file_formatter)
            
            root_logger.addHandler(handler)
        
        # Create colored console handler (shows all logs)
        console_handler = ColoredConsoleHandler(allowed_levels=allowed_levels)
        root_logger.addHandler(console_handler)
    else:
        # Backward compatibility: single log file
        if log_file is None:
            log_file = log_dir / "app.log"
        else:
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file)
        file_handler.addFilter(LevelFilter(allowed_levels))
        
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(file_formatter)
        
        console_handler = ColoredConsoleHandler(allowed_levels=allowed_levels)
        
        root_logger.addHandler(file_handler)
        root_logger.addHandler(console_handler)

