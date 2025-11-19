"""
Date range selector component for dashboard.
"""

import flet as ft
from typing import Callable, Optional
from datetime import datetime, timedelta
from ui.theme import theme_manager


class DateRangeSelectorComponent:
    """Component for date range selection with quick buttons."""
    
    def __init__(
        self,
        start_date: datetime,
        end_date: datetime,
        on_date_range_changed: Callable[[datetime, datetime], None]
    ):
        self.start_date = start_date
        self.end_date = end_date
        self.on_date_range_changed = on_date_range_changed
        self.page: Optional[ft.Page] = None
        self.active_quick_button: Optional[ft.TextButton] = None
        
        # Create date pickers
        self.start_date_picker = ft.DatePicker(
            first_date=datetime(2020, 1, 1),
            last_date=datetime.now(),
            on_change=self._on_start_date_changed
        )
        self.end_date_picker = ft.DatePicker(
            first_date=datetime(2020, 1, 1),
            last_date=datetime.now(),
            on_change=self._on_end_date_changed
        )
        
        # Create component
        self.component = self._create_component()
    
    def _create_component(self) -> ft.Container:
        """Create the date range selector component."""
        # Date display fields - use Text instead of TextField to avoid duplication
        self.start_date_field = ft.Text(
            value=self.start_date.strftime("%Y-%m-%d"),
            size=theme_manager.font_size_body,
            weight=ft.FontWeight.W_500
        )
        self.end_date_field = ft.Text(
            value=self.end_date.strftime("%Y-%m-%d"),
            size=theme_manager.font_size_body,
            weight=ft.FontWeight.W_500
        )
        
        # Quick selection buttons - store references for later access
        self.today_btn = ft.TextButton(
            theme_manager.t("today") or "Today",
            on_click=lambda _: self._set_date_range("today")
        )
        self.week_btn = ft.TextButton(
            theme_manager.t("this_week") or "This Week",
            on_click=lambda _: self._set_date_range("week")
        )
        self.month_btn = ft.TextButton(
            theme_manager.t("this_month") or "This Month",
            on_click=lambda _: self._set_date_range("month")
        )
        self.year_btn = ft.TextButton(
            theme_manager.t("this_year") or "This Year",
            on_click=lambda _: self._set_date_range("year")
        )
        
        # Set default to month (active state)
        # Use Color constant with opacity since primary_color is a string
        primary_color_obj = ft.Colors.BLUE_700 if not theme_manager.is_dark else ft.Colors.CYAN_700
        self.month_btn.style = ft.ButtonStyle(
            color=theme_manager.primary_color,
            bgcolor=ft.Colors.with_opacity(0.1, primary_color_obj)
        )
        self.active_quick_button = self.month_btn
        
        return ft.Container(
            content=ft.Row([
                ft.Row([
                    ft.Text(
                        theme_manager.t("date_range") or "Date Range:",
                        size=theme_manager.font_size_body,
                        weight=ft.FontWeight.W_500
                    ),
                    ft.ElevatedButton(
                        content=ft.Row([
                            ft.Icon(ft.Icons.CALENDAR_TODAY, size=18),
                            self.start_date_field
                        ], spacing=8, tight=True),
                        on_click=self._open_start_date_picker,
                        style=ft.ButtonStyle(
                            bgcolor=theme_manager.surface_color,
                            color=theme_manager.text_color,
                            side=ft.BorderSide(1, theme_manager.border_color),
                        ),
                        height=40
                    ),
                    ft.Text(" - ", size=theme_manager.font_size_body),
                    ft.ElevatedButton(
                        content=ft.Row([
                            ft.Icon(ft.Icons.CALENDAR_TODAY, size=18),
                            self.end_date_field
                        ], spacing=8, tight=True),
                        on_click=self._open_end_date_picker,
                        style=ft.ButtonStyle(
                            bgcolor=theme_manager.surface_color,
                            color=theme_manager.text_color,
                            side=ft.BorderSide(1, theme_manager.border_color),
                        ),
                        height=40
                    ),
                ], spacing=10, tight=True),
                ft.Container(width=20),
                ft.Row([
                    ft.Text(
                        theme_manager.t("quick_select") or "Quick Select:",
                        size=theme_manager.font_size_body,
                        weight=ft.FontWeight.W_500
                    ),
                    self.today_btn,
                    self.week_btn,
                    self.month_btn,
                    self.year_btn,
                ], spacing=5, tight=True),
            ], alignment=ft.MainAxisAlignment.START, spacing=10),
            padding=ft.padding.symmetric(vertical=10, horizontal=0)
        )
    
    def _set_date_range(self, range_type: str):
        """Set date range based on quick selection."""
        today = datetime.now()
        
        if range_type == "today":
            self.start_date = today.replace(hour=0, minute=0, second=0, microsecond=0)
            self.end_date = today
        elif range_type == "week":
            days_since_monday = today.weekday()
            self.start_date = (today - timedelta(days=days_since_monday)).replace(hour=0, minute=0, second=0, microsecond=0)
            self.end_date = today
        elif range_type == "month":
            self.start_date = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            self.end_date = today
        elif range_type == "year":
            self.start_date = today.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
            self.end_date = today
        
        # Update date fields
        self.start_date_field.value = self.start_date.strftime("%Y-%m-%d")
        self.end_date_field.value = self.end_date.strftime("%Y-%m-%d")
        
        # Update active button style
        if self.active_quick_button:
            self.active_quick_button.style = None
        
        # Find and update the clicked button using stored references
        primary_color_obj = ft.Colors.BLUE_700 if not theme_manager.is_dark else ft.Colors.CYAN_700
        button_map = {
            "today": self.today_btn,
            "week": self.week_btn,
            "month": self.month_btn,
            "year": self.year_btn
        }
        
        if range_type in button_map:
            btn = button_map[range_type]
            btn.style = ft.ButtonStyle(
                color=theme_manager.primary_color,
                bgcolor=ft.Colors.with_opacity(0.1, primary_color_obj)
            )
            self.active_quick_button = btn
        
        # Notify parent
        self.on_date_range_changed(self.start_date, self.end_date)
        
        if self.page:
            self.page.update()
    
    def _on_start_date_changed(self, e):
        """Handle start date picker change."""
        if e.control.value:
            self.start_date = datetime.combine(e.control.value, datetime.min.time())
            self.start_date_field.value = self.start_date.strftime("%Y-%m-%d")
            # Clear active quick button since custom date is selected
            if self.active_quick_button:
                self.active_quick_button.style = None
                self.active_quick_button = None
            self.on_date_range_changed(self.start_date, self.end_date)
            if self.page:
                self.page.update()
    
    def _on_end_date_changed(self, e):
        """Handle end date picker change."""
        if e.control.value:
            self.end_date = datetime.combine(e.control.value, datetime.max.time())
            self.end_date_field.value = self.end_date.strftime("%Y-%m-%d")
            # Clear active quick button since custom date is selected
            if self.active_quick_button:
                self.active_quick_button.style = None
                self.active_quick_button = None
            self.on_date_range_changed(self.start_date, self.end_date)
            if self.page:
                self.page.update()
    
    def _open_start_date_picker(self, e):
        """Open start date picker."""
        if not self.page:
            return
        
        # Ensure picker is in overlay (only once)
        if self.start_date_picker not in self.page.overlay:
            self.page.overlay.append(self.start_date_picker)
        
        # Set the picker's current value
        try:
            if isinstance(self.start_date, datetime):
                self.start_date_picker.value = self.start_date.date()
            else:
                self.start_date_picker.value = self.start_date
        except:
            pass
        
        # Open the picker using page.open() method
        try:
            self.page.open(self.start_date_picker)
        except Exception:
            # Fallback if page.open() doesn't work
            try:
                if hasattr(self.start_date_picker, 'pick_date'):
                    self.start_date_picker.pick_date()
            except:
                pass
        
        if self.page:
            self.page.update()
    
    def _open_end_date_picker(self, e):
        """Open end date picker."""
        if not self.page:
            return
        
        # Ensure picker is in overlay (only once)
        if self.end_date_picker not in self.page.overlay:
            self.page.overlay.append(self.end_date_picker)
        
        # Set the picker's current value
        try:
            if isinstance(self.end_date, datetime):
                self.end_date_picker.value = self.end_date.date()
            else:
                self.end_date_picker.value = self.end_date
        except:
            pass
        
        # Open the picker using page.open() method
        try:
            self.page.open(self.end_date_picker)
        except Exception:
            # Fallback if page.open() doesn't work
            try:
                if hasattr(self.end_date_picker, 'pick_date'):
                    self.end_date_picker.pick_date()
            except:
                pass
        
        if self.page:
            self.page.update()
    
    def build(self) -> ft.Container:
        """Build and return the component."""
        return self.component
    
    def set_page(self, page: ft.Page):
        """Set page reference and add date pickers to overlay."""
        self.page = page
        if page:
            # Only add to overlay if not already present (prevent duplicates)
            if self.start_date_picker not in page.overlay:
                page.overlay.append(self.start_date_picker)
            if self.end_date_picker not in page.overlay:
                page.overlay.append(self.end_date_picker)

