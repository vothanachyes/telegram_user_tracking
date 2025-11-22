"""
Theme and styling management with i18n support.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Optional

import flet as ft
from config.settings import settings
from utils.constants import COLORS


# Initialize logger
logger = logging.getLogger(__name__)


def load_translations() -> Dict[str, Dict[str, str]]:
    """
    Load translations from JSON files in the locales directory.
    Returns a dictionary with language codes as keys and translation dicts as values.
    Falls back to English if a language file is missing or invalid.
    """
    translations: Dict[str, Dict[str, str]] = {}
    
    # Get project root (parent of ui directory)
    project_root = Path(__file__).parent.parent
    locales_dir = project_root / "locales"
    
    # Default English translations (fallback)
    default_en: Dict[str, str] = {}
    
    # Load English translations first (required as fallback)
    en_file = locales_dir / "en.json"
    if en_file.exists():
        try:
            with open(en_file, "r", encoding="utf-8") as f:
                default_en = json.load(f)
                translations["en"] = default_en
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Failed to load English translations: {e}")
            translations["en"] = {}
    else:
        logger.warning(f"English translation file not found: {en_file}")
        translations["en"] = {}
    
    # Load other language files
    for lang_file in locales_dir.glob("*.json"):
        lang_code = lang_file.stem
        if lang_code == "en":
            continue  # Already loaded
        
        try:
            with open(lang_file, "r", encoding="utf-8") as f:
                lang_translations = json.load(f)
                translations[lang_code] = lang_translations
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Failed to load translations for {lang_code}: {e}")
            # Use English as fallback for this language
            translations[lang_code] = default_en.copy() if default_en else {}
    
    return translations


# Load translations at module level
TRANSLATIONS = load_translations()


class ThemeManager:
    """Manages application theme and styling."""
    
    def __init__(self):
        self._current_theme = settings.theme
        self._current_language = settings.language
        self._corner_radius = settings.corner_radius
    
    @property
    def is_dark(self) -> bool:
        """Check if dark mode is active."""
        return self._current_theme == "dark"
    
    @property
    def theme_mode(self) -> ft.ThemeMode:
        """Get Flet theme mode."""
        return ft.ThemeMode.DARK if self.is_dark else ft.ThemeMode.LIGHT
    
    @property
    def primary_color(self) -> str:
        """Get primary color (theme-aware)."""
        # Use lighter color for dark mode to ensure visibility
        return COLORS["secondary"] if self.is_dark else COLORS["primary"]
    
    @property
    def primary_dark(self) -> str:
        """Get primary dark color."""
        return COLORS["primary_dark"]
    
    @property
    def background_color(self) -> str:
        """Get background color."""
        return COLORS["background_dark"] if self.is_dark else COLORS["background_light"]
    
    @property
    def surface_color(self) -> str:
        """Get surface color."""
        return COLORS["surface_dark"] if self.is_dark else COLORS["surface_light"]
    
    @property
    def text_color(self) -> str:
        """Get text color."""
        return COLORS["text_dark"] if self.is_dark else COLORS["text_light"]
    
    @property
    def text_secondary_color(self) -> str:
        """Get secondary text color."""
        return COLORS["text_secondary_dark"] if self.is_dark else COLORS["text_secondary_light"]
    
    @property
    def border_color(self) -> str:
        """Get border color."""
        return COLORS["border_dark"] if self.is_dark else COLORS["border_light"]
    
    @property
    def success_color(self) -> str:
        """Get success color."""
        return COLORS["success"]
    
    @property
    def error_color(self) -> str:
        """Get error color."""
        return COLORS["error"]
    
    @property
    def warning_color(self) -> str:
        """Get warning color."""
        return COLORS["warning"]
    
    @property
    def info_color(self) -> str:
        """Get info color."""
        return COLORS["info"]
    
    @property
    def corner_radius(self) -> int:
        """Get corner radius."""
        return self._corner_radius
    
    # Font Size Properties
    @property
    def font_size_page_title(self) -> int:
        """Get page title font size (24px)."""
        return 24
    
    @property
    def font_size_section_title(self) -> int:
        """Get section title font size (20px)."""
        return 20
    
    @property
    def font_size_subsection_title(self) -> int:
        """Get subsection title font size (18px)."""
        return 18
    
    @property
    def font_size_body(self) -> int:
        """Get body text font size (14px)."""
        return 14
    
    @property
    def font_size_small(self) -> int:
        """Get small text font size (12px)."""
        return 12
    
    @property
    def font_size_large_number(self) -> int:
        """Get large number font size (32px)."""
        return 32
    
    @property
    def font_size_medium_number(self) -> int:
        """Get medium number font size (24px)."""
        return 24
    
    # Spacing Properties (8px base unit)
    @property
    def spacing_xs(self) -> int:
        """Get extra small spacing (4px)."""
        return 4
    
    @property
    def spacing_sm(self) -> int:
        """Get small spacing (8px)."""
        return 8
    
    @property
    def spacing_md(self) -> int:
        """Get medium spacing (12px)."""
        return 12
    
    @property
    def spacing_lg(self) -> int:
        """Get large spacing (16px)."""
        return 16
    
    @property
    def spacing_xl(self) -> int:
        """Get extra large spacing (20px)."""
        return 20
    
    @property
    def spacing_xxl(self) -> int:
        """Get 2X large spacing (24px)."""
        return 24
    
    @property
    def spacing_xxxl(self) -> int:
        """Get 3X large spacing (32px)."""
        return 32
    
    # Padding Properties
    @property
    def padding_xs(self) -> int:
        """Get extra small padding (8px)."""
        return 8
    
    @property
    def padding_sm(self) -> int:
        """Get small padding (12px)."""
        return 12
    
    @property
    def padding_md(self) -> int:
        """Get medium padding (16px)."""
        return 16
    
    @property
    def padding_lg(self) -> int:
        """Get large padding (20px)."""
        return 20
    
    @property
    def padding_xl(self) -> int:
        """Get extra large padding (24px)."""
        return 24
    
    # Container Height Properties
    @property
    def height_xs(self) -> int:
        """Get extra small height (8px)."""
        return 8
    
    @property
    def height_sm(self) -> int:
        """Get small height (12px)."""
        return 12
    
    @property
    def height_md(self) -> int:
        """Get medium height (16px)."""
        return 16
    
    @property
    def height_lg(self) -> int:
        """Get large height (20px)."""
        return 20
    
    @property
    def height_xl(self) -> int:
        """Get extra large height (24px)."""
        return 24
    
    @property
    def height_xxl(self) -> int:
        """Get 2X large height (32px)."""
        return 32
    
    def set_theme(self, theme: str):
        """Set theme (dark/light)."""
        self._current_theme = theme
    
    def set_language(self, language: str):
        """Set language."""
        self._current_language = language
    
    def set_corner_radius(self, radius: int):
        """Set corner radius."""
        self._corner_radius = radius
    
    @property
    def khmer_font_family(self) -> str:
        """Get font family for Khmer text (Kantumruy Pro)."""
        return "KantumruyPro"
    
    def get_theme(self) -> ft.Theme:
        """Get Flet theme configuration."""
        theme = ft.Theme(
            color_scheme_seed=self.primary_color,
            use_material3=True
        )
        
        # Set default font family for Khmer language
        if self._current_language == "km":
            theme.text_theme = ft.TextTheme(
                body_large=ft.TextStyle(font_family=self.khmer_font_family),
                body_medium=ft.TextStyle(font_family=self.khmer_font_family),
                body_small=ft.TextStyle(font_family=self.khmer_font_family),
                title_large=ft.TextStyle(font_family=self.khmer_font_family),
                title_medium=ft.TextStyle(font_family=self.khmer_font_family),
                title_small=ft.TextStyle(font_family=self.khmer_font_family),
                label_large=ft.TextStyle(font_family=self.khmer_font_family),
                label_medium=ft.TextStyle(font_family=self.khmer_font_family),
                label_small=ft.TextStyle(font_family=self.khmer_font_family),
            )
        
        return theme
    
    def t(self, key: str) -> str:
        """
        Translate key to current language.
        Returns the key if translation not found.
        Falls back to English if current language is not available.
        """
        # Get translations for current language, fallback to English
        lang_dict = TRANSLATIONS.get(self._current_language, TRANSLATIONS.get("en", {}))
        # If key not found in current language, try English
        if key not in lang_dict and self._current_language != "en":
            lang_dict = TRANSLATIONS.get("en", {})
        return lang_dict.get(key, key)
    
    def spacing_container(self, size: str = "lg") -> ft.Container:
        """
        Create a spacing container with standard height.
        
        Args:
            size: Size of spacing (xs, sm, md, lg, xl, xxl)
        
        Returns:
            Container with appropriate height for spacing
        """
        height_map = {
            "xs": self.height_xs,
            "sm": self.height_sm,
            "md": self.height_md,
            "lg": self.height_lg,
            "xl": self.height_xl,
            "xxl": self.height_xxl
        }
        return ft.Container(height=height_map.get(size, self.height_lg))
    
    def create_card(self, content: ft.Control, **kwargs) -> ft.Container:
        """Create a themed card container."""
        # Set default padding only if not provided in kwargs
        if 'padding' not in kwargs:
            kwargs['padding'] = self.padding_md
        return ft.Container(
            content=content,
            bgcolor=self.surface_color,
            border=ft.border.all(1, self.border_color),
            border_radius=self.corner_radius,
            **kwargs
        )
    
    def create_button(
        self, 
        text: str,
        on_click=None,
        icon: Optional[str] = None,
        style: str = "primary",
        **kwargs
    ) -> ft.ElevatedButton:
        """Create a themed button."""
        colors_map = {
            "primary": COLORS["primary"],
            "success": COLORS["success"],
            "warning": COLORS["warning"],
            "error": COLORS["error"],
            "info": COLORS["info"]
        }
        
        return ft.ElevatedButton(
            text=text,
            icon=icon,
            on_click=on_click,
            style=ft.ButtonStyle(
                color=ft.Colors.WHITE,
                bgcolor=colors_map.get(style, COLORS["primary"]),
                shape=ft.RoundedRectangleBorder(radius=self.corner_radius)
            ),
            **kwargs
        )
    
    def create_text_field(
        self,
        label: str,
        value: str = "",
        password: bool = False,
        multiline: bool = False,
        **kwargs
    ) -> ft.TextField:
        """Create a themed text field."""
        return ft.TextField(
            label=label,
            value=value,
            password=password,
            multiline=multiline,
            border_radius=self.corner_radius,
            border_color=self.border_color,
            focused_border_color=self.primary_color,
            **kwargs
        )
    
    def create_dropdown(
        self,
        label: str,
        options: list,
        value: Optional[str] = None,
        **kwargs
    ) -> ft.Dropdown:
        """Create a themed dropdown."""
        return ft.Dropdown(
            label=label,
            options=[ft.dropdown.Option(opt) for opt in options],
            value=value,
            border_radius=self.corner_radius,
            border_color=self.border_color,
            focused_border_color=self.primary_color,
            **kwargs
        )
    
    def show_snackbar(
        self, 
        page: ft.Page,
        message: str,
        action_label: Optional[str] = None,
        on_action=None,
        bgcolor: Optional[str] = None
    ):
        """Show a snackbar notification."""
        snackbar = ft.SnackBar(
            content=ft.Text(message, color=ft.Colors.WHITE),
            action=action_label,
            on_action=on_action,
            bgcolor=bgcolor or self.primary_color
        )
        page.snack_bar = snackbar
        page.snack_bar.open = True
        page.update()
    
    def show_toast(
        self,
        page: ft.Page,
        message: str,
        toast_type: str = "info",
        duration: int = 3000
    ):
        """
        Show a toast notification.
        
        Args:
            page: Flet page instance
            message: Message to display
            toast_type: Type of toast (success, error, warning, info)
            duration: Duration in milliseconds before auto-dismiss
        """
        from ui.components.toast import toast, ToastType
        
        # Initialize toast if not already initialized
        if not hasattr(toast, '_page') or toast._page != page:
            toast.initialize(page)
        
        # Map string type to ToastType enum
        type_map = {
            "success": ToastType.SUCCESS,
            "error": ToastType.ERROR,
            "warning": ToastType.WARNING,
            "info": ToastType.INFO,
        }
        
        toast_type_enum = type_map.get(toast_type.lower(), ToastType.INFO)
        toast.show(message, toast_type_enum, duration)
    
    def show_toast_success(self, page: ft.Page, message: str, duration: int = 3000):
        """Show a success toast notification."""
        self.show_toast(page, message, "success", duration)
    
    def show_toast_error(self, page: ft.Page, message: str, duration: int = 4000):
        """Show an error toast notification."""
        self.show_toast(page, message, "error", duration)
    
    def show_toast_warning(self, page: ft.Page, message: str, duration: int = 3500):
        """Show a warning toast notification."""
        self.show_toast(page, message, "warning", duration)
    
    def show_toast_info(self, page: ft.Page, message: str, duration: int = 3000):
        """Show an info toast notification."""
        self.show_toast(page, message, "info", duration)
    
    def get_gradient_background(self, rotation_angle: int = 0) -> ft.LinearGradient:
        """
        Get gradient background with rotation angle.
        
        Args:
            rotation_angle: Rotation angle in degrees (0, 45, 90, 135, 180, 225, 270, 315)
        
        Returns:
            LinearGradient with appropriate begin and end points
        """
        import math
        
        # Convert angle to radians
        angle_rad = math.radians(rotation_angle)
        
        # Calculate begin and end points based on angle
        # For 0°: top-left to bottom-right (diagonal)
        # For 45°: top to bottom-right
        # For 90°: top to bottom (vertical)
        # For 135°: top-right to bottom-left
        # For 180°: right to left (horizontal)
        # etc.
        # Use unit circle to calculate direction
        begin_x = 0.5 * (1 - math.cos(angle_rad))
        begin_y = 0.5 * (1 - math.sin(angle_rad))
        end_x = 0.5 * (1 + math.cos(angle_rad))
        end_y = 0.5 * (1 + math.sin(angle_rad))
        
        return ft.LinearGradient(
            begin=ft.alignment.Alignment(begin_x, begin_y),
            end=ft.alignment.Alignment(end_x, end_y),
            colors=[self.primary_color, self.primary_dark]
        )
    
    def get_header_background_image_path(self) -> Optional[str]:
        """
        Get header background image path if it exists.
        
        Returns:
            Path to header background image or None
        """
        from pathlib import Path
        project_root = Path(__file__).parent.parent
        for ext in ['.png', '.jpg', '.jpeg']:
            bg_path = project_root / "assets" / f"header_background{ext}"
            if bg_path.exists():
                return str(bg_path)
        return None
    
    def get_header_background_image_opacity(self) -> float:
        """Get opacity for header background image (default 0.3)."""
        return 0.3
    
# Global theme manager instance
theme_manager = ThemeManager()

