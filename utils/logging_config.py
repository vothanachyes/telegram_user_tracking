"""
Logging configuration for the application.
"""

import logging
import sys
from pathlib import Path

from utils.constants import BASE_DIR


class LevelFilter(logging.Filter):
    """Filter to allow only specific log levels."""
    def __init__(self, allowed_levels):
        super().__init__()
        self.allowed_levels = allowed_levels
    
    def filter(self, record):
        return record.levelno in self.allowed_levels


def setup_logging(allowed_levels=None, log_file=None):
    """
    Setup logging configuration with custom level filtering.
    
    Args:
        allowed_levels: List of logging levels to show. 
                       Defaults to [INFO, WARNING, ERROR]
        log_file: Path to log file. Defaults to 'logs/app.log'
    """
    if allowed_levels is None:
        allowed_levels = [logging.INFO, logging.WARNING, logging.ERROR, logging.DEBUG]
        # allowed_levels = [logging.INFO, logging.WARNING, logging.ERROR, logging.CRITICAL, logging.DEBUG, logging.FATAL]
        # allowed_levels = [logging.NOTSET]

    # Set default log file path if not provided
    if log_file is None:
        log_dir = BASE_DIR / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / "app.log"
    else:
        # If a custom path is provided, ensure parent directory exists
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

    # Create handlers
    file_handler = logging.FileHandler(log_file)
    console_handler = logging.StreamHandler(sys.stdout)
    
    # Apply filter to both handlers
    file_handler.addFilter(LevelFilter(allowed_levels))
    console_handler.addFilter(LevelFilter(allowed_levels))
    
    logging.basicConfig(
        level=logging.DEBUG,  # Set to lowest level, filter will handle the rest
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[file_handler, console_handler]
    )

