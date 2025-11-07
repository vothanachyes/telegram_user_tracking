"""
Logging configuration for the application.
"""

import logging
import sys
from pathlib import Path


class LevelFilter(logging.Filter):
    """Filter to allow only specific log levels."""
    def __init__(self, allowed_levels):
        super().__init__()
        self.allowed_levels = allowed_levels
    
    def filter(self, record):
        return record.levelno in self.allowed_levels


def setup_logging(allowed_levels=None, log_file='app.log'):
    """
    Setup logging configuration with custom level filtering.
    
    Args:
        allowed_levels: List of logging levels to show. 
                       Defaults to [INFO, WARNING, ERROR]
        log_file: Path to log file. Defaults to 'app.log'
    """
    if allowed_levels is None:
        allowed_levels = [logging.INFO, logging.WARNING, logging.ERROR]
    
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

