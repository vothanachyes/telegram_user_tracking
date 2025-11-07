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
        """Get primary color."""
        return COLORS["primary"]
    
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
    def corner_radius(self) -> int:
        """Get corner radius."""
        return self._corner_radius
    
    def set_theme(self, theme: str):
        """Set theme (dark/light)."""
        self._current_theme = theme
    
    def set_language(self, language: str):
        """Set language."""
        self._current_language = language
    
    def set_corner_radius(self, radius: int):
        """Set corner radius."""
        self._corner_radius = radius
    
    def get_theme(self) -> ft.Theme:
        """Get Flet theme configuration."""
        return ft.Theme(
            color_scheme_seed=self.primary_color,
            use_material3=True
        )
    
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
    
    def create_card(self, content: ft.Control, **kwargs) -> ft.Container:
        """Create a themed card container."""
        # Set default padding only if not provided in kwargs
        if 'padding' not in kwargs:
            kwargs['padding'] = 15
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
    
    def show_dialog(
        self,
        page: ft.Page,
        title: str,
        content: ft.Control,
        actions: Optional[list] = None
    ):
        """Show a dialog."""
        dialog = ft.AlertDialog(
            title=ft.Text(title),
            content=content,
            actions=actions or [],
            actions_alignment=ft.MainAxisAlignment.END
        )
        page.dialog = dialog
        dialog.open = True
        page.update()


# Global theme manager instance
theme_manager = ThemeManager()

