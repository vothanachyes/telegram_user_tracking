"""
Page configuration utilities.
"""

import flet as ft
import platform
import logging
from pathlib import Path
from ui.theme import theme_manager
from config.settings import settings
import sys
from utils.constants import (
    BASE_DIR,
    DEFAULT_WINDOW_WIDTH,
    DEFAULT_WINDOW_HEIGHT,
    MIN_WINDOW_WIDTH,
    MIN_WINDOW_HEIGHT
)

# Try to import screen size utilities
try:
    import tkinter as tk
    _tkinter_available = True
except ImportError:
    _tkinter_available = False

if platform.system() == 'Windows':
    try:
        import ctypes
        _ctypes_available = True
    except ImportError:
        _ctypes_available = False
else:
    _ctypes_available = False

# Get the correct base directory for assets (works in both dev and bundle)
def get_assets_base_dir():
    """Get the base directory for assets, handling both dev and PyInstaller bundle."""
    if getattr(sys, 'frozen', False):
        # Running from PyInstaller bundle - assets are in Resources
        if platform.system() == 'Darwin':
            # macOS: Resources is in Contents/Resources
            bundle_dir = Path(sys.executable).parent.parent.parent
            return bundle_dir / 'Contents' / 'Resources'
        else:
            # Windows/Linux: assets are in the same directory as the executable
            return Path(sys.executable).parent
    else:
        # Development: use project root
        return BASE_DIR

logger = logging.getLogger(__name__)


def _get_screen_size() -> tuple[int, int]:
    """
    Get screen width and height in pixels.
    
    Returns:
        Tuple of (width, height) in pixels
    """
    try:
        if platform.system() == 'Windows' and _ctypes_available:
            # Windows: Use ctypes to get screen size (most efficient, no visible window)
            user32 = ctypes.windll.user32
            width = user32.GetSystemMetrics(0)  # SM_CXSCREEN
            height = user32.GetSystemMetrics(1)  # SM_CYSCREEN
            return width, height
        elif _tkinter_available:
            # Cross-platform: Use tkinter (works on Windows, macOS, Linux)
            # Create root window but keep it completely hidden to avoid flicker
            try:
                root = tk.Tk()
                root.withdraw()  # Hide the window immediately
                # Try to make it completely invisible (may not work on all platforms)
                try:
                    root.attributes('-alpha', 0)
                    root.overrideredirect(True)
                except:
                    pass  # Some platforms don't support these attributes
                # Get screen size quickly
                width = root.winfo_screenwidth()
                height = root.winfo_screenheight()
                root.destroy()
                return width, height
            except Exception as e:
                logger.warning(f"Tkinter screen size detection failed: {e}")
                return 1920, 1080
        else:
            # Fallback: Return default screen size
            logger.warning("Could not determine screen size, using default 1920x1080")
            return 1920, 1080
    except Exception as e:
        logger.warning(f"Error getting screen size: {e}, using default 1920x1080")
        return 1920, 1080


class PageConfig:
    """Handles page configuration and setup."""
    
    @staticmethod
    def configure_page(page: ft.Page):
        """
        Configure page settings.
        
        Args:
            page: Flet page instance to configure
        """
        # Window position is set in main() function before this is called
        # Here we just ensure window size constraints are set
        try:
            page.window.width = DEFAULT_WINDOW_WIDTH
            page.window.height = DEFAULT_WINDOW_HEIGHT
            page.window.min_width = MIN_WINDOW_WIDTH
            page.window.min_height = MIN_WINDOW_HEIGHT
        except (AttributeError, Exception) as e:
            logger.warning(f"Could not set window size: {e}")
        
        # Configure custom fonts first (before setting theme)
        try:
            assets_base = get_assets_base_dir()
            fonts_dir = assets_base / 'assets' / 'fonts'
            
            # Register Kantumruy Pro font for Khmer text
            kantumruy_pro_regular = fonts_dir / 'KantumruyPro-Regular.ttf'
            kantumruy_pro_bold = fonts_dir / 'KantumruyPro-Bold.ttf'
            
            page.fonts = {}
            
            if kantumruy_pro_regular.exists():
                page.fonts["KantumruyPro"] = str(kantumruy_pro_regular.resolve())
                logger.info(f"Kantumruy Pro Regular font loaded: {kantumruy_pro_regular}")
            else:
                logger.warning(f"Kantumruy Pro Regular font not found at: {kantumruy_pro_regular}")
            
            if kantumruy_pro_bold.exists():
                # Flet supports font families with variants
                # For bold, we can use the same family name and Flet will handle weight
                logger.info(f"Kantumruy Pro Bold font found: {kantumruy_pro_bold}")
        except Exception as e:
            logger.warning(f"Could not load custom fonts: {e}")
        
        # Set other page properties
        page.title = settings.app_name
        page.theme_mode = theme_manager.theme_mode
        page.theme = theme_manager.get_theme()
        
        try:
            # Set window icon from assets/icons directory
            system = platform.system()
            assets_base = get_assets_base_dir()
            
            if system == 'Windows':
                icon_path = assets_base / 'assets' / 'icons' / 'win' / 'icon.ico'
                if icon_path.exists():
                    try:
                        icon_path_abs = icon_path.resolve()
                        page.window.icon = str(icon_path_abs)
                        logger.info(f"Window icon set: {icon_path_abs}")
                    except (AttributeError, Exception) as e:
                        logger.warning(f"Could not set window icon: {e}")
            elif system == 'Darwin':  # macOS
                icon_path = assets_base / 'assets' / 'icons' / 'mac' / 'icon.icns'
                if icon_path.exists():
                    try:
                        icon_path_abs = icon_path.resolve()
                        page.window.icon = str(icon_path_abs)
                        logger.info(f"Window icon set: {icon_path_abs}")
                    except (AttributeError, Exception) as e:
                        logger.warning(f"Could not set window icon: {e}")
                else:
                    logger.warning(f"Mac icon not found at: {icon_path}")
            elif system == 'Linux':
                icon_path = assets_base / 'assets' / 'icons' / 'linux' / 'icon.png'
                if icon_path.exists():
                    try:
                        icon_path_abs = icon_path.resolve()
                        page.window.icon = str(icon_path_abs)
                        logger.info(f"Window icon set: {icon_path_abs}")
                    except (AttributeError, Exception) as e:
                        logger.warning(f"Could not set window icon: {e}")
        except AttributeError:
            pass
        
        page.padding = 0
        # Background will be handled by gradient container in router
        # Keep background color as fallback
        page.bgcolor = theme_manager.background_color
        
        from ui.components.toast import toast
        toast.initialize(page, position="top-right")
        
        # Update once after all properties are set to minimize flickering
        page.update()
    
    @staticmethod
    def update_theme(page: ft.Page):
        """
        Update page theme after settings change.
        
        Args:
            page: Flet page instance
        """
        page.theme_mode = theme_manager.theme_mode
        page.theme = theme_manager.get_theme()
        # Background will be handled by gradient container in router
        # Keep background color as fallback
        page.bgcolor = theme_manager.background_color
        page.update()

