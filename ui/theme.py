"""
Theme and styling management with i18n support.
"""

import flet as ft
from typing import Dict, Optional
from config.settings import settings
from utils.constants import COLORS


# Translation dictionaries
TRANSLATIONS = {
    "en": {
        # General
        "app_name": "Telegram User Tracking",
        "welcome": "Welcome",
        "loading": "Loading...",
        "save": "Save",
        "cancel": "Cancel",
        "delete": "Delete",
        "edit": "Edit",
        "close": "Close",
        "confirm": "Confirm",
        "yes": "Yes",
        "no": "No",
        "search": "Search",
        "filter": "Filter",
        "export": "Export",
        "refresh": "Refresh",
        "settings": "Settings",
        "logout": "Logout",
        
        # Auth
        "login": "Login",
        "email": "Email",
        "password": "Password",
        "remember_me": "Remember me",
        "login_error": "Login failed",
        "logout_success": "Logged out successfully",
        
        # Navigation
        "dashboard": "Dashboard",
        "telegram": "Telegram",
        "messages": "Messages",
        "users": "Users",
        "profile": "Profile",
        
        # Dashboard
        "total_messages": "Total Messages",
        "total_users": "Total Users",
        "total_groups": "Total Groups",
        "media_storage": "Media Storage",
        "messages_today": "Messages Today",
        "messages_this_month": "Messages This Month",
        "recent_activity": "Recent Activity",
        "statistics": "Statistics",
        
        # Messages
        "message": "Message",
        "date_sent": "Date Sent",
        "has_media": "Has Media",
        "media_type": "Media Type",
        "message_link": "Message Link",
        "fetch_messages": "Fetch Messages",
        "select_group": "Select Group",
        "start_date": "Start Date",
        "end_date": "End Date",
        "fetching": "Fetching...",
        "fetch_complete": "Fetch complete",
        
        # Users
        "username": "Username",
        "full_name": "Full Name",
        "phone": "Phone",
        "bio": "Bio",
        "profile_photo": "Profile Photo",
        "user_details": "User Details",
        
        # Settings
        "appearance": "Appearance",
        "theme": "Theme",
        "dark_mode": "Dark Mode",
        "light_mode": "Light Mode",
        "language": "Language",
        "corner_radius": "Corner Radius",
        "telegram_auth": "Telegram Authentication",
        "api_id": "API ID",
        "api_hash": "API Hash",
        "test_connection": "Test Connection",
        "fetch_settings": "Fetch Settings",
        "download_directory": "Download Directory",
        "download_media": "Download Media",
        "max_file_size": "Max File Size (MB)",
        "fetch_delay": "Fetch Delay (seconds)",
        "media_types": "Media Types to Download",
        "photos": "Photos",
        "videos": "Videos",
        "documents": "Documents",
        "audio": "Audio",
        "settings_saved": "Settings saved successfully",
        
        # Export
        "export_to_excel": "Export to Excel",
        "export_to_pdf": "Export to PDF",
        "export_success": "Export successful",
        "export_error": "Export failed",
        
        # Errors
        "error": "Error",
        "success": "Success",
        "warning": "Warning",
        "info": "Info",
        "no_data": "No data available",
        "connection_error": "Connection error",
        "offline": "You are offline",
        "online": "Connected",
        
        # Developer
        "developer_info": "Developer Info",
        "version": "Version",
        "contact": "Contact",
    },
    
    "km": {  # Khmer translations
        # General
        "app_name": "តាមដានអ្នកប្រើ Telegram",
        "welcome": "សូមស្វាគមន៍",
        "loading": "កំពុងផ្ទុក...",
        "save": "រក្សាទុក",
        "cancel": "បោះបង់",
        "delete": "លុប",
        "edit": "កែសម្រួល",
        "close": "បិទ",
        "confirm": "បញ្ជាក់",
        "yes": "បាទ/ចាស",
        "no": "ទេ",
        "search": "ស្វែងរក",
        "filter": "តម្រង",
        "export": "នាំចេញ",
        "refresh": "ផ្ទុកឡើងវិញ",
        "settings": "ការកំណត់",
        "logout": "ចាកចេញ",
        
        # Auth
        "login": "ចូល",
        "email": "អ៊ីមែល",
        "password": "ពាក្យសម្ងាត់",
        "remember_me": "ចងចាំខ្ញុំ",
        "login_error": "ការចូលបានបរាជ័យ",
        "logout_success": "បានចាកចេញដោយជោគជ័យ",
        
        # Navigation
        "dashboard": "ផ្ទាំងគ្រប់គ្រង",
        "telegram": "តេឡេក្រាម",
        "messages": "សារ",
        "users": "អ្នកប្រើ",
        "profile": "ប្រវត្តិរូប",
        
        # Dashboard
        "total_messages": "សារសរុប",
        "total_users": "អ្នកប្រើសរុប",
        "total_groups": "ក្រុមសរុប",
        "media_storage": "ឃ្លាំងផ្ទុកមេឌៀ",
        "messages_today": "សារថ្ងៃនេះ",
        "messages_this_month": "សារខែនេះ",
        "recent_activity": "សកម្មភាពថ្មីៗ",
        "statistics": "ស្ថិតិ",
        
        # Messages
        "message": "សារ",
        "date_sent": "កាលបរិច្ឆេទផ្ញើ",
        "has_media": "មានមេឌៀ",
        "media_type": "ប្រភេទមេឌៀ",
        "message_link": "តំណសារ",
        "fetch_messages": "ទាញយកសារ",
        "select_group": "ជ្រើសរើសក្រុម",
        "start_date": "កាលបរិច្ឆេទចាប់ផ្តើម",
        "end_date": "កាលបរិច្ឆេទបញ្ចប់",
        "fetching": "កំពុងទាញយក...",
        "fetch_complete": "ទាញយករួចរាល់",
        
        # Users
        "username": "ឈ្មោះអ្នកប្រើ",
        "full_name": "ឈ្មោះពេញ",
        "phone": "ទូរស័ព្ទ",
        "bio": "ជីវប្រវត្តិ",
        "profile_photo": "រូបថតប្រវត្តិរូប",
        "user_details": "ព័ត៌មានលម្អិតអ្នកប្រើ",
        
        # Settings
        "appearance": "រូបរាង",
        "theme": "ស្បែក",
        "dark_mode": "របៀបងងឹត",
        "light_mode": "របៀបភ្លឺ",
        "language": "ភាសា",
        "corner_radius": "កាច់ជ្រុង",
        "telegram_auth": "ការផ្ទៀងផ្ទាត់ Telegram",
        "api_id": "លេខ API",
        "api_hash": "លេខកូដ API",
        "test_connection": "សាកល្បងការតភ្ជាប់",
        "fetch_settings": "ការកំណត់ទាញយក",
        "download_directory": "ថតទាញយក",
        "download_media": "ទាញយកមេឌៀ",
        "max_file_size": "ទំហំឯកសារអតិបរមា (MB)",
        "fetch_delay": "ការពន្យាពេលទាញយក (វិនាទី)",
        "media_types": "ប្រភេទមេឌៀដែលត្រូវទាញយក",
        "photos": "រូបថត",
        "videos": "វីដេអូ",
        "documents": "ឯកសារ",
        "audio": "សម្លេង",
        "settings_saved": "បានរក្សាទុកការកំណត់ដោយជោគជ័យ",
        
        # Export
        "export_to_excel": "នាំចេញទៅ Excel",
        "export_to_pdf": "នាំចេញទៅ PDF",
        "export_success": "នាំចេញបានជោគជ័យ",
        "export_error": "នាំចេញបានបរាជ័យ",
        
        # Errors
        "error": "កំហុស",
        "success": "ជោគជ័យ",
        "warning": "ការព្រមាន",
        "info": "ព័ត៌មាន",
        "no_data": "គ្មានទិន្នន័យ",
        "connection_error": "កំហុសក្នុងការតភ្ជាប់",
        "offline": "អ្នកស្ថិតក្រៅបណ្តាញ",
        "online": "បានតភ្ជាប់",
        
        # Developer
        "developer_info": "ព័ត៌មានអ្នកបង្កើត",
        "version": "កំណែ",
        "contact": "ទំនាក់ទំនង",
    }
}


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
        """
        lang_dict = TRANSLATIONS.get(self._current_language, TRANSLATIONS["en"])
        return lang_dict.get(key, key)
    
    def create_card(self, content: ft.Control, **kwargs) -> ft.Container:
        """Create a themed card container."""
        return ft.Container(
            content=content,
            bgcolor=self.surface_color,
            border=ft.border.all(1, self.border_color),
            border_radius=self.corner_radius,
            padding=15,
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
                color=ft.colors.WHITE,
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
            content=ft.Text(message, color=ft.colors.WHITE),
            action=action_label,
            on_action=on_action,
            bgcolor=bgcolor or self.primary_color
        )
        page.snack_bar = snackbar
        page.snack_bar.open = True
        page.update()
    
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

