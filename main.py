"""
Main entry point for Telegram User Tracking application.
"""

import logging
import sys
import flet as ft
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

# Import app
from ui.app import main as app_main


def main():
    """Main entry point."""
    try:
        logger.info("Starting Telegram User Tracking application...")
        
        # Run Flet app
        ft.app(target=app_main)
        
    except Exception as e:
        logger.error(f"Application error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()

