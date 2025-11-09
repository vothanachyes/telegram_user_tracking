"""
User dashboard page for viewing individual user details and activity.
"""

import flet as ft
from typing import Optional
from datetime import datetime, timedelta
from ui.theme import theme_manager
from ui.components import DataTable
from ui.dialogs import UserDetailDialog
from database.db_manager import DatabaseManager
from database.models import TelegramUser
from services.export import ExportService
from utils.helpers import format_datetime, get_telegram_user_link


class UserDashboardPage(ft.Container):
    """User dashboard page for viewing user details and activity."""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.export_service = ExportService(db_manager)
        self.selected_user: Optional[TelegramUser] = None
        self.selected_group: Optional[int] = None
        self.page: Optional[ft.Page] = None
        
        # File pickers for export
        self.user_excel_picker = ft.FilePicker(
            on_result=self._on_user_excel_picked
        )
        self.user_pdf_picker = ft.FilePicker(
            on_result=self._on_user_pdf_picked
        )
        
        # Search field with dropdown
        self.search_field = ft.TextField(
            hint_text=theme_manager.t("search_user"),
            prefix_icon=ft.Icons.SEARCH,
            on_change=self._on_search_change,
            on_focus=self._on_search_focus,
            on_blur=self._on_search_blur,
            width=300,
            border_radius=theme_manager.corner_radius
        )
        
        self.search_dropdown = ft.Container(
            visible=False,
            bgcolor=theme_manager.surface_color,
            border=ft.border.all(1, theme_manager.border_color),
            border_radius=theme_manager.corner_radius,
            padding=5,
            width=300,
            content=ft.Column([], spacing=2, scroll=ft.ScrollMode.AUTO, tight=True)
        )
        
        # Date filters (default: current month)
        today = datetime.now()
        first_day = today.replace(day=1)
        
        self.start_date_field = ft.TextField(
            label=theme_manager.t("start_date"),
            value=first_day.strftime("%Y-%m-%d"),
            width=140,
            border_radius=theme_manager.corner_radius,
            on_change=self._on_date_change
        )
        
        self.end_date_field = ft.TextField(
            label=theme_manager.t("end_date"),
            value=today.strftime("%Y-%m-%d"),
            width=140,
            border_radius=theme_manager.corner_radius,
            on_change=self._on_date_change
        )
        
        # Group selector
        groups = self.db_manager.get_all_groups()
        group_options = [f"{g.group_name} ({g.group_id})" for g in groups]
        if group_options:
            # Select first group by default
            self.selected_group = groups[0].group_id if groups else None
            default_group_value = group_options[0] if group_options else None
        else:
            default_group_value = None
        
        self.group_dropdown = theme_manager.create_dropdown(
            label=theme_manager.t("select_group"),
            options=group_options if group_options else ["No groups"],
            value=default_group_value,
            on_change=self._on_group_selected,
            width=250
        )
        
        # Export menu
        export_menu = ft.PopupMenuButton(
            icon=ft.Icons.MORE_VERT,
            tooltip=theme_manager.t("export"),
            items=[
                ft.PopupMenuItem(
                    text=theme_manager.t("export_to_excel"),
                    icon=ft.Icons.TABLE_CHART,
                    on_click=self._export_user_excel
                ),
                ft.PopupMenuItem(
                    text=theme_manager.t("export_to_pdf"),
                    icon=ft.Icons.PICTURE_AS_PDF,
                    on_click=self._export_user_pdf
                ),
            ]
        )
        
        # Telegram button
        self.telegram_button = ft.IconButton(
            icon=ft.Icons.TELEGRAM,
            tooltip=theme_manager.t("open_in_telegram"),
            disabled=True,
            on_click=self._open_telegram_user
        )
        
        # User detail section
        self.user_detail_section = self._create_user_detail_section()
        
        # Tabs
        self.tabs = ft.Tabs(
            selected_index=0,
            animation_duration=300,
            tabs=[
                ft.Tab(
                    text=theme_manager.t("general"),
                    icon=ft.Icons.DASHBOARD,
                    content=self._create_general_tab()
                ),
                ft.Tab(
                    text=theme_manager.t("messages"),
                    icon=ft.Icons.MESSAGE,
                    content=self._create_messages_tab()
                ),
            ],
            expand=True
        )
        
        super().__init__(
            content=ft.Column([
                # Top Header
                self._create_header(),
                # User detail section
                self.user_detail_section,
                # Tabs
                self.tabs,
            ], spacing=15, expand=True),
            padding=20,
            expand=True
        )
    
    def set_page(self, page: ft.Page):
        """Set page reference and add file pickers to overlay."""
        self.page = page
        if not hasattr(page, 'overlay') or page.overlay is None:
            page.overlay = []
        
        pickers = [self.user_excel_picker, self.user_pdf_picker]
        for picker in pickers:
            if picker not in page.overlay:
                page.overlay.append(picker)
        page.update()
    
    def _create_header(self) -> ft.Container:
        """Create top header with search and actions."""
        return ft.Container(
            content=ft.Row([
                # Left: Search field with dropdown
                ft.Column([
                    self.search_field,
                    self.search_dropdown,
                ], spacing=0, tight=True),
                # Right: Telegram button and Export menu
                ft.Row([
                    self.telegram_button,
                    export_menu,
                ], spacing=10),
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            padding=10
        )
    
    def _create_user_detail_section(self) -> ft.Container:
        """Create user detail section (similar to user_detail_dialog profile photo section)."""
        return theme_manager.create_card(
            content=ft.Row([
                # Profile photo and info
                ft.Row([
                    ft.Icon(
                        ft.Icons.ACCOUNT_CIRCLE,
                        size=80,
                        color=theme_manager.primary_color
                    ),
                    ft.Column([
                        ft.Text(
                            theme_manager.t("select_user_to_view_details"),
                            size=18,
                            weight=ft.FontWeight.BOLD
                        ),
                        ft.Text(
                            theme_manager.t("search_user_to_get_started"),
                            size=14,
                            color=theme_manager.text_secondary_color
                        ),
                    ], spacing=5)
                ], spacing=20, alignment=ft.MainAxisAlignment.START),
                # Right: View details button
                ft.Container(
                    content=ft.IconButton(
                        icon=ft.Icons.EDIT,
                        tooltip=theme_manager.t("view_user_details"),
                        disabled=True,
                        on_click=self._open_user_detail_dialog
                    ),
                    alignment=ft.alignment.center_right
                ),
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            visible=False
        )
    
    def _create_general_tab(self) -> ft.Container:
        """Create General tab with statistics."""
        self.stats_container = ft.Container(
            content=ft.Column([
                ft.Text(
                    theme_manager.t("select_user_to_view_statistics"),
                    size=16,
                    color=theme_manager.text_secondary_color,
                    text_align=ft.TextAlign.CENTER
                )
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=20),
            padding=20,
            expand=True
        )
        
        return ft.Container(
            content=self.stats_container,
            padding=10,
            expand=True
        )
    
    def _create_messages_tab(self) -> ft.Container:
        """Create Messages tab with filtered messages table."""
        refresh_btn = ft.IconButton(
            icon=ft.Icons.REFRESH,
            tooltip=theme_manager.t("refresh"),
            on_click=self._refresh_messages
        )
        
        # Messages table
        self.messages_table = self._create_messages_table()
        
        return ft.Container(
            content=ft.Column([
                # Filters row
                ft.Row([
                    self.start_date_field,
                    self.end_date_field,
                    ft.Container(width=20),
                    self.group_dropdown,
                    refresh_btn,
                ], spacing=10, wrap=False),
                # Table
                ft.Container(
                    content=self.messages_table,
                    expand=True,
                    width=None
                ),
            ], spacing=15, expand=True),
            padding=10,
            expand=True
        )
    
    def _create_messages_table(self) -> DataTable:
        """Create messages data table."""
        rows = []
        row_metadata = []
        
        if self.selected_user and self.selected_group:
            messages = self.db_manager.get_messages(
                group_id=self.selected_group,
                user_id=self.selected_user.user_id,
                start_date=self._get_start_date(),
                end_date=self._get_end_date(),
                limit=100
            )
            
            for idx, msg in enumerate(messages, 1):
                rows.append([
                    idx,
                    msg.content[:100] + "..." if msg.content and len(msg.content) > 100 else msg.content or "",
                    format_datetime(msg.date_sent, "%Y-%m-%d %H:%M"),
                    "Yes" if msg.has_media else "No",
                    msg.media_type or "-",
                    "",  # Link column
                ])
                
                row_meta = {
                    'cells': {
                        5: {
                            'link': msg.message_link,
                            'renderer': 'icon'
                        } if msg.message_link else {}
                    }
                }
                row_metadata.append(row_meta)
        
        column_alignments = ["center", "left", "center", "center", "center", "center"]
        
        return DataTable(
            columns=["No", "Message", "Date", "Media", "Type", "Link"],
            rows=rows,
            on_row_click=self._on_message_click,
            page_size=50,
            column_alignments=column_alignments,
            row_metadata=row_metadata,
            searchable=False
        )
    
    def _on_search_change(self, e):
        """Handle search field change."""
        query = e.control.value
        if not query or len(query) < 2:
            self.search_dropdown.visible = False
            self.search_dropdown.content.controls = []
            if self.page:
                self.search_dropdown.update()
            return
        
        # Search users
        users = self.db_manager.search_users(query, limit=10)
        
        # Update dropdown
        dropdown_items = []
        for user in users:
            display_name = user.full_name
            username_display = f"@{user.username}" if user.username else ""
            phone_display = user.phone or ""
            
            item = ft.Container(
                content=ft.Column([
                    ft.Text(display_name, size=14, weight=ft.FontWeight.BOLD),
                    ft.Row([
                        ft.Text(username_display, size=12, color=theme_manager.text_secondary_color) if username_display else ft.Container(),
                        ft.Text(phone_display, size=12, color=theme_manager.text_secondary_color) if phone_display else ft.Container(),
                    ], spacing=10, wrap=False)
                ], spacing=2, tight=True),
                padding=10,
                on_click=lambda e, u=user: self._select_user(u),
                data=user,
                bgcolor=theme_manager.surface_color,
                border_radius=theme_manager.corner_radius
            )
            dropdown_items.append(item)
        
        self.search_dropdown.content.controls = dropdown_items
        self.search_dropdown.visible = len(users) > 0
        if self.page:
            self.search_dropdown.update()
    
    def _on_search_focus(self, e):
        """Handle search field focus."""
        if self.search_dropdown.content.controls:
            self.search_dropdown.visible = True
            if self.page:
                self.search_dropdown.update()
    
    def _on_search_blur(self, e):
        """Handle search field blur - hide dropdown after delay."""
        # Use a small delay to allow click events
        if self.page:
            import threading
            def hide_dropdown():
                import time
                time.sleep(0.2)
                self.search_dropdown.visible = False
                if self.page:
                    try:
                        self.search_dropdown.update()
                    except:
                        pass
            threading.Thread(target=hide_dropdown, daemon=True).start()
    
    def _select_user(self, user: TelegramUser):
        """Select a user and update the UI."""
        self.selected_user = user
        self.search_field.value = user.full_name
        self.search_dropdown.visible = False
        
        # Update Telegram button
        user_link = get_telegram_user_link(user.username)
        self.telegram_button.disabled = not user_link
        if user_link:
            self.telegram_button.data = user_link
        
        # Update user detail section
        self._update_user_detail_section()
        
        # Update statistics
        self._update_statistics()
        
        # Refresh messages
        self._refresh_messages(None)
        
        if self.page:
            self.page.update()
    
    def _update_user_detail_section(self):
        """Update user detail section with selected user info."""
        if not self.selected_user:
            self.user_detail_section.visible = False
            return
        
        user = self.selected_user
        profile_photo = ft.Icon(
            ft.Icons.ACCOUNT_CIRCLE,
            size=80,
            color=theme_manager.primary_color
        ) if not user.profile_photo_path else ft.Image(
            src=user.profile_photo_path,
            width=80,
            height=80,
            fit=ft.ImageFit.COVER,
            border_radius=40
        )
        
        self.user_detail_section.content = ft.Row([
            ft.Row([
                profile_photo,
                ft.Column([
                    ft.Text(
                        user.full_name,
                        size=18,
                        weight=ft.FontWeight.BOLD
                    ),
                    ft.Text(
                        f"User ID: {user.user_id}",
                        size=14,
                        color=theme_manager.text_secondary_color
                    ),
                    ft.Text(
                        f"Profile Photo: {'Available' if user.profile_photo_path else 'Not Available'}",
                        size=12,
                        color=theme_manager.text_secondary_color
                    ),
                ], spacing=5)
            ], spacing=20, alignment=ft.MainAxisAlignment.START),
            ft.Container(
                content=ft.IconButton(
                    icon=ft.Icons.EDIT,
                    tooltip=theme_manager.t("view_user_details"),
                    on_click=self._open_user_detail_dialog
                ),
                alignment=ft.alignment.center_right
            ),
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
        
        self.user_detail_section.visible = True
    
    def _update_statistics(self):
        """Update statistics in General tab."""
        if not self.selected_user:
            self.stats_container.content = ft.Column([
                ft.Text(
                    theme_manager.t("select_user_to_view_statistics"),
                    size=16,
                    color=theme_manager.text_secondary_color,
                    text_align=ft.TextAlign.CENTER
                )
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=20)
            return
        
        # Get user activity stats
        stats = self.db_manager.get_user_activity_stats(
            user_id=self.selected_user.user_id,
            group_id=self.selected_group,
            start_date=self._get_start_date(),
            end_date=self._get_end_date()
        )
        
        # Create statistics cards
        stats_cards = [
            self._create_stat_card(
                theme_manager.t("total_messages"),
                str(stats.get('total_messages', 0)),
                ft.Icons.MESSAGE
            ),
            self._create_stat_card(
                theme_manager.t("total_reactions"),
                str(stats.get('total_reactions', 0)),
                ft.Icons.FAVORITE
            ),
            self._create_stat_card(
                theme_manager.t("total_stickers"),
                str(stats.get('total_stickers', 0)),
                ft.Icons.EMOJI_EMOTIONS
            ),
            self._create_stat_card(
                theme_manager.t("total_videos"),
                str(stats.get('total_videos', 0)),
                ft.Icons.VIDEOCAM
            ),
            self._create_stat_card(
                theme_manager.t("total_photos"),
                str(stats.get('total_photos', 0)),
                ft.Icons.PHOTO
            ),
            self._create_stat_card(
                theme_manager.t("total_links"),
                str(stats.get('total_links', 0)),
                ft.Icons.LINK
            ),
            self._create_stat_card(
                theme_manager.t("total_documents"),
                str(stats.get('total_documents', 0)),
                ft.Icons.DESCRIPTION
            ),
            self._create_stat_card(
                theme_manager.t("total_audio"),
                str(stats.get('total_audio', 0)),
                ft.Icons.AUDIOTRACK
            ),
        ]
        
        self.stats_container.content = ft.Column([
            ft.Text(
                theme_manager.t("user_activity_statistics"),
                size=20,
                weight=ft.FontWeight.BOLD
            ),
            ft.Divider(),
            ft.Row(
                stats_cards[:4],
                spacing=15,
                wrap=True
            ),
            ft.Row(
                stats_cards[4:],
                spacing=15,
                wrap=True
            ),
        ], spacing=15, expand=True)
    
    def _create_stat_card(self, label: str, value: str, icon: str) -> ft.Container:
        """Create a statistics card."""
        return theme_manager.create_card(
            content=ft.Column([
                ft.Icon(icon, size=32, color=theme_manager.primary_color),
                ft.Text(
                    value,
                    size=24,
                    weight=ft.FontWeight.BOLD,
                    color=theme_manager.primary_color
                ),
                ft.Text(
                    label,
                    size=12,
                    color=theme_manager.text_secondary_color
                ),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=5),
            width=150
        )
    
    def _on_date_change(self, e):
        """Handle date field change."""
        if self.selected_user:
            self._update_statistics()
            self._refresh_messages(None)
    
    def _on_group_selected(self, e):
        """Handle group selection."""
        if e.control.value and e.control.value != "No groups":
            group_str = e.control.value
            group_id = int(group_str.split("(")[-1].strip(")"))
            self.selected_group = group_id
        else:
            self.selected_group = None
        
        # Update statistics and messages
        if self.selected_user:
            self._update_statistics()
            self._refresh_messages(None)
    
    def _get_start_date(self) -> Optional[datetime]:
        """Get start date from field."""
        try:
            if self.start_date_field.value:
                return datetime.strptime(self.start_date_field.value, "%Y-%m-%d")
        except:
            pass
        return None
    
    def _get_end_date(self) -> Optional[datetime]:
        """Get end date from field."""
        try:
            if self.end_date_field.value:
                return datetime.strptime(self.end_date_field.value, "%Y-%m-%d")
        except:
            pass
        return None
    
    def _refresh_messages(self, e):
        """Refresh messages table."""
        if not self.selected_user:
            self.messages_table.refresh([], [])
            return
        
        messages = self.db_manager.get_messages(
            group_id=self.selected_group,
            user_id=self.selected_user.user_id,
            start_date=self._get_start_date(),
            end_date=self._get_end_date(),
            limit=100
        )
        
        rows = []
        row_metadata = []
        for idx, msg in enumerate(messages, 1):
            rows.append([
                idx,
                msg.content[:100] + "..." if msg.content and len(msg.content) > 100 else msg.content or "",
                format_datetime(msg.date_sent, "%Y-%m-%d %H:%M"),
                "Yes" if msg.has_media else "No",
                msg.media_type or "-",
                "",  # Link column
            ])
            
            row_meta = {
                'cells': {
                    5: {
                        'link': msg.message_link,
                        'renderer': 'icon'
                    } if msg.message_link else {}
                }
            }
            row_metadata.append(row_meta)
        
        self.messages_table.refresh(rows, row_metadata)
    
    def _on_message_click(self, row_index: int):
        """Handle message row click."""
        if not self.selected_user or not self.selected_group:
            return
        
        messages = self.db_manager.get_messages(
            group_id=self.selected_group,
            user_id=self.selected_user.user_id,
            start_date=self._get_start_date(),
            end_date=self._get_end_date(),
            limit=100
        )
        
        if row_index < len(messages):
            from ui.dialogs.message_detail_dialog import MessageDetailDialog
            message = messages[row_index]
            
            dialog = MessageDetailDialog(
                db_manager=self.db_manager,
                message=message,
                on_delete=lambda: self._refresh_messages(None),
                on_update=lambda: self._refresh_messages(None)
            )
            
            if self.page:
                dialog.page = self.page
                self.page.open(dialog)
    
    def _open_user_detail_dialog(self, e):
        """Open user detail dialog."""
        if not self.selected_user:
            return
        
        dialog = UserDetailDialog(
            db_manager=self.db_manager,
            user=self.selected_user,
            on_delete=lambda: self._on_user_deleted(),
            on_update=lambda: self._on_user_updated()
        )
        
        if self.page:
            dialog.page = self.page
            self.page.open(dialog)
    
    def _on_user_deleted(self):
        """Handle user deletion."""
        self.selected_user = None
        self.search_field.value = ""
        self.telegram_button.disabled = True
        self.user_detail_section.visible = False
        self._update_statistics()
        self._refresh_messages(None)
        if self.page:
            self.page.update()
    
    def _on_user_updated(self):
        """Handle user update."""
        if self.selected_user:
            # Refresh user data
            updated_user = self.db_manager.get_user_by_id(self.selected_user.user_id)
            if updated_user:
                self.selected_user = updated_user
                self._update_user_detail_section()
                if self.page:
                    self.page.update()
    
    def _open_telegram_user(self, e):
        """Open Telegram user link."""
        if self.telegram_button.data:
            import webbrowser
            webbrowser.open(self.telegram_button.data)
    
    def _export_user_excel(self, e):
        """Export user data to Excel."""
        if not self.page or not self.selected_user:
            theme_manager.show_snackbar(
                self.page,
                theme_manager.t("select_user_first"),
                bgcolor=ft.Colors.ORANGE
            )
            return
        
        # Ensure file picker is in overlay
        if not hasattr(self.page, 'overlay') or self.page.overlay is None:
            self.page.overlay = []
        if self.user_excel_picker not in self.page.overlay:
            self.page.overlay.append(self.user_excel_picker)
        
        default_name = f"user_{self.selected_user.user_id}_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        try:
            self.user_excel_picker.save_file(
                dialog_title=theme_manager.t("export_to_excel"),
                file_name=default_name,
                file_type=ft.FilePickerFileType.CUSTOM,
                allowed_extensions=["xlsx"]
            )
        except Exception as ex:
            theme_manager.show_snackbar(
                self.page,
                f"Error: {str(ex)}",
                bgcolor=ft.Colors.RED
            )
    
    def _on_user_excel_picked(self, e: ft.FilePickerResultEvent):
        """Handle Excel file picker result."""
        if not self.page or not e.path or not self.selected_user:
            return
        
        try:
            # Get user messages
            messages = self.db_manager.get_messages(
                user_id=self.selected_user.user_id,
                group_id=self.selected_group,
                start_date=self._get_start_date(),
                end_date=self._get_end_date()
            )
            
            # Export user data
            if self.export_service.export_user_data_to_excel(
                user=self.selected_user,
                messages=messages,
                stats=self.db_manager.get_user_activity_stats(
                    user_id=self.selected_user.user_id,
                    group_id=self.selected_group,
                    start_date=self._get_start_date(),
                    end_date=self._get_end_date()
                ),
                output_path=e.path
            ):
                theme_manager.show_snackbar(
                    self.page,
                    f"{theme_manager.t('export_success')}: {e.path}",
                    bgcolor=ft.Colors.GREEN
                )
            else:
                theme_manager.show_snackbar(
                    self.page,
                    theme_manager.t("export_error"),
                    bgcolor=ft.Colors.RED
                )
        except Exception as ex:
            theme_manager.show_snackbar(
                self.page,
                f"{theme_manager.t('export_error')}: {str(ex)}",
                bgcolor=ft.Colors.RED
            )
    
    def _export_user_pdf(self, e):
        """Export user data to PDF."""
        if not self.page or not self.selected_user:
            theme_manager.show_snackbar(
                self.page,
                theme_manager.t("select_user_first"),
                bgcolor=ft.Colors.ORANGE
            )
            return
        
        if not hasattr(self.page, 'overlay') or self.page.overlay is None:
            self.page.overlay = []
        if self.user_pdf_picker not in self.page.overlay:
            self.page.overlay.append(self.user_pdf_picker)
        
        default_name = f"user_{self.selected_user.user_id}_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        try:
            self.user_pdf_picker.save_file(
                dialog_title=theme_manager.t("export_to_pdf"),
                file_name=default_name,
                file_type=ft.FilePickerFileType.CUSTOM,
                allowed_extensions=["pdf"]
            )
        except Exception as ex:
            theme_manager.show_snackbar(
                self.page,
                f"Error: {str(ex)}",
                bgcolor=ft.Colors.RED
            )
    
    def _on_user_pdf_picked(self, e: ft.FilePickerResultEvent):
        """Handle PDF file picker result."""
        if not self.page or not e.path or not self.selected_user:
            return
        
        try:
            messages = self.db_manager.get_messages(
                user_id=self.selected_user.user_id,
                group_id=self.selected_group,
                start_date=self._get_start_date(),
                end_date=self._get_end_date()
            )
            
            if self.export_service.export_user_data_to_pdf(
                user=self.selected_user,
                messages=messages,
                stats=self.db_manager.get_user_activity_stats(
                    user_id=self.selected_user.user_id,
                    group_id=self.selected_group,
                    start_date=self._get_start_date(),
                    end_date=self._get_end_date()
                ),
                output_path=e.path
            ):
                theme_manager.show_snackbar(
                    self.page,
                    f"{theme_manager.t('export_success')}: {e.path}",
                    bgcolor=ft.Colors.GREEN
                )
            else:
                theme_manager.show_snackbar(
                    self.page,
                    theme_manager.t("export_error"),
                    bgcolor=ft.Colors.RED
                )
        except Exception as ex:
            theme_manager.show_snackbar(
                self.page,
                f"{theme_manager.t('export_error')}: {str(ex)}",
                bgcolor=ft.Colors.RED
            )

