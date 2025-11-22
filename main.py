"""
Main entry point for Telegram User Tracking application.
"""

import logging
import sys
import os
import argparse
import atexit
import platform
import flet as ft
from pathlib import Path

# Set process name early on macOS to prevent duplicate dock icons
if platform.system() == 'Darwin':
    try:
        # Try using setproctitle library if available (more reliable)
        try:
            import setproctitle
            setproctitle.setproctitle('TelegramUserTracking')
        except ImportError:
            # Fallback: try using ctypes (may not work on all macOS versions)
            import ctypes
            try:
                libc = ctypes.CDLL('/usr/lib/libc.dylib')
                # prctl is not available on macOS, so we skip this
                # The bundle identifier in Info.plist should be sufficient
                pass
            except Exception:
                pass
    except Exception:
        # If setting process name fails, continue anyway
        # The bundle identifier in Info.plist should handle dock icon grouping
        pass

# Setup logging
from utils.logging_config import setup_logging

setup_logging()  # Uses default: [INFO, WARNING, ERROR]

logger = logging.getLogger(__name__)

# Import app
from ui.app import main as app_main
from utils.single_instance import SingleInstance


def main():
    """Main entry point."""
    # Initialize single instance lock FIRST (before any imports that might fail)
    single_instance = None
    try:
        single_instance = SingleInstance()
        
        # Check if another instance is already running
        if single_instance.is_already_running():
            logger.warning("Another instance of the application is already running.")
            print("Another instance of the application is already running.")
            print("Please close the existing instance before starting a new one.")
            sys.exit(1)
        
        # Register cleanup function to release lock on exit
        atexit.register(single_instance.release)
    except Exception as e:
        logger.error(f"Error initializing single instance lock: {e}", exc_info=True)
        # Continue anyway - better to have duplicate instances than no app at all
        single_instance = None
    
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
            # Window size is configured in page_config.py via page.window properties
            # Note: Dock icon is set via Info.plist in the app bundle
            ft.app(
                target=app_main,
                name="TelegramUserTracking"  # App name for macOS
            )
        
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Application error: {e}", exc_info=True)
        sys.exit(1)
    finally:
        # Ensure lock is released
        if single_instance:
            try:
                single_instance.release()
            except Exception:
                pass  # Ignore errors during cleanup


if __name__ == "__main__":
    main()

