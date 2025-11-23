"""
Generic reusable date range selector component.
Provides consistent UI across all features with date range selection.
"""

import flet as ft
from typing import Optional, Callable
from datetime import datetime, timedelta
from ui.theme import theme_manager


class DateRangeSelector:
    """Generic reusable date range selector with quick select dropdown."""
    
    def __init__(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        on_date_range_changed: Optional[Callable[[datetime, datetime], None]] = None,
        default_range: str = "month"  # "today", "week", "month", "year", or None for custom
    ):
        """
        Initialize date range selector.
        
        Args:
            start_date: Initial start date (defaults to first day of current month)
            end_date: Initial end date (defaults to today)
            on_date_range_changed: Callback when date range changes (receives start_date, end_date)
            default_range: Default quick select range ("today", "week", "month", "year", or None)
        """
        self.on_date_range_changed = on_date_range_changed
        self.page: Optional[ft.Page] = None
        
        # Set default dates
        today = datetime.now()
        if start_date is None or end_date is None:
            if default_range == "today":
                self.start_date = today.replace(hour=0, minute=0, second=0, microsecond=0)
                self.end_date = today
            elif default_range == "week":
                days_since_monday = today.weekday()
                self.start_date = (today - timedelta(days=days_since_monday)).replace(hour=0, minute=0, second=0, microsecond=0)
                self.end_date = today
            elif default_range == "month":
                self.start_date = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                self.end_date = today
            elif default_range == "year":
                self.start_date = today.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
                self.end_date = today
            else:
                # Default to current month
                self.start_date = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                self.end_date = today
        else:
            self.start_date = start_date
            self.end_date = end_date
        
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
        
        # Date display fields
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
        
        # Quick date select dropdown
        self.quick_date_options = [
            theme_manager.t("custom") or "Custom",
            theme_manager.t("today") or "Today",
            theme_manager.t("this_week") or "This Week",
            theme_manager.t("this_month") or "This Month",
            theme_manager.t("this_year") or "This Year",
        ]
        
        # Map default_range to dropdown value
        default_value_map = {
            "today": theme_manager.t("today") or "Today",
            "week": theme_manager.t("this_week") or "This Week",
            "month": theme_manager.t("this_month") or "This Month",
            "year": theme_manager.t("this_year") or "This Year",
        }
        default_dropdown_value = default_value_map.get(default_range, theme_manager.t("this_month") or "This Month")
        
        self.quick_date_dropdown = theme_manager.create_dropdown(
            label=theme_manager.t("quick_select") or "Quick Select",
            options=self.quick_date_options,
            value=default_dropdown_value,
            on_change=self._on_quick_date_selected,
            width=150
        )
    
    def build(self) -> ft.Row:
        """Build the date range selector component."""
        return ft.Row([
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
            ft.Container(width=10),
            self.quick_date_dropdown,
        ], spacing=10, tight=True)
    
    def get_start_date(self) -> datetime:
        """Get start date."""
        return self.start_date
    
    def get_end_date(self) -> datetime:
        """Get end date."""
        return self.end_date
    
    def set_page(self, page: ft.Page):
        """Set page reference and add date pickers to overlay."""
        self.page = page
        if page:
            if self.start_date_picker not in page.overlay:
                page.overlay.append(self.start_date_picker)
            if self.end_date_picker not in page.overlay:
                page.overlay.append(self.end_date_picker)
    
    def _on_quick_date_selected(self, e):
        """Handle quick date selection from dropdown."""
        if not e.control.value:
            return
        
        today = datetime.now()
        selected_option = e.control.value
        
        if selected_option == theme_manager.t("today") or selected_option == "Today":
            self.start_date = today.replace(hour=0, minute=0, second=0, microsecond=0)
            self.end_date = today
        elif selected_option == theme_manager.t("this_week") or selected_option == "This Week":
            days_since_monday = today.weekday()
            self.start_date = (today - timedelta(days=days_since_monday)).replace(hour=0, minute=0, second=0, microsecond=0)
            self.end_date = today
        elif selected_option == theme_manager.t("this_month") or selected_option == "This Month":
            self.start_date = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            self.end_date = today
        elif selected_option == theme_manager.t("this_year") or selected_option == "This Year":
            self.start_date = today.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
            self.end_date = today
        # "Custom" option doesn't change dates, user can pick manually
        
        # Update date display fields
        if selected_option != (theme_manager.t("custom") or "Custom"):
            self.start_date_field.value = self.start_date.strftime("%Y-%m-%d")
            self.end_date_field.value = self.end_date.strftime("%Y-%m-%d")
            
            if self.page:
                self.start_date_field.update()
                self.end_date_field.update()
        
        # Trigger callback
        if self.on_date_range_changed:
            self.on_date_range_changed(self.start_date, self.end_date)
    
    def _on_start_date_changed(self, e):
        """Handle start date picker change."""
        if e.control.value:
            self.start_date = datetime.combine(e.control.value, datetime.min.time())
            self.start_date_field.value = self.start_date.strftime("%Y-%m-%d")
            # Set quick select to "Custom" when manually picking dates
            if self.quick_date_dropdown:
                self.quick_date_dropdown.value = theme_manager.t("custom") or "Custom"
                if self.page:
                    self.quick_date_dropdown.update()
            if self.page:
                self.start_date_field.update()
            if self.on_date_range_changed:
                self.on_date_range_changed(self.start_date, self.end_date)
    
    def _on_end_date_changed(self, e):
        """Handle end date picker change."""
        if e.control.value:
            self.end_date = datetime.combine(e.control.value, datetime.max.time())
            self.end_date_field.value = self.end_date.strftime("%Y-%m-%d")
            # Set quick select to "Custom" when manually picking dates
            if self.quick_date_dropdown:
                self.quick_date_dropdown.value = theme_manager.t("custom") or "Custom"
                if self.page:
                    self.quick_date_dropdown.update()
            if self.page:
                self.end_date_field.update()
            if self.on_date_range_changed:
                self.on_date_range_changed(self.start_date, self.end_date)
    
    def _open_start_date_picker(self, e):
        """Open start date picker."""
        if not self.page or not self.start_date_picker:
            return
        
        # Ensure picker is in overlay
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
        if not self.page or not self.end_date_picker:
            return
        
        # Ensure picker is in overlay
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

