"""
Main entry point for Telegram User Tracking application.
"""

import logging
import sys
import os
import argparse
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
        # Parse command-line arguments
        parser = argparse.ArgumentParser(description='Telegram User Tracking Application')
        parser.add_argument(
            '--web',
            action='store_true',
            help='Run in web browser mode for debugging (can also use FLET_WEB_MODE=true)'
        )
        parser.add_argument(
            '--port',
            type=int,
            default=8550,
            help='Port for web mode (default: 8550)'
        )
        args = parser.parse_args()
        
        # Check for web mode: command-line argument or environment variable
        web_mode = args.web or os.getenv("FLET_WEB_MODE", "").lower() in ("true", "1", "yes")
        
        if web_mode:
            logger.info("Starting Telegram User Tracking application in WEB MODE (for debugging)...")
            logger.info(f"App will be available at http://localhost:{args.port}")
            logger.info("Press Ctrl+C to stop the server")
            # Run in web browser mode
            ft.app(
                target=app_main,
                view=ft.AppView.WEB_BROWSER,
                port=args.port,
                web_renderer=ft.WebRenderer.AUTO
            )
        else:
            logger.info("Starting Telegram User Tracking application...")
            # Run Flet app in desktop mode
            # Window size is configured in ui/app.py _configure_page method
            ft.app(target=app_main)
        
    except Exception as e:
        logger.error(f"Application error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()

