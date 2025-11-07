"""
Main entry point for Telegram User Tracking application.
"""

import logging
import sys
import flet as ft
from pathlib import Path

# Setup logging
from utils.logging_config import setup_logging

setup_logging()  # Uses default: [INFO, WARNING, ERROR]

logger = logging.getLogger(__name__)

# Import app
from ui.app import main as app_main


def main():
    """Main entry point."""
    try:
        logger.info("Starting Telegram User Tracking application...")
        
        # Run Flet app
        # Window size is configured in ui/app.py _configure_page method
        ft.app(target=app_main)
        
    except Exception as e:
        logger.error(f"Application error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()

