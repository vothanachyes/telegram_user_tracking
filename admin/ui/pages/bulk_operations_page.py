"""
Admin bulk operations page.
"""

import flet as ft
from admin.ui.components.data_table import DataTable


class AdminBulkOperationsPage(ft.Container):
    """Admin bulk operations page."""
    
    # Dark theme colors
    BG_COLOR = "#1e1e1e"
    TEXT_COLOR = "#ffffff"
    
    def __init__(self, page: ft.Page):
        self.page = page
        
        super().__init__(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Text(
                                "Bulk Operations",
                                size=28,
                                weight=ft.FontWeight.BOLD,
                                color=self.TEXT_COLOR,
                            ),
                        ],
                    ),
                    ft.Divider(height=20, color="transparent"),
                    ft.Text(
                        "Bulk operations feature - to be implemented",
                        color=self.TEXT_COLOR,
                    ),
                ],
                spacing=10,
                expand=True,
            ),
            padding=ft.padding.all(20),
            bgcolor=self.BG_COLOR,
            expand=True,
        )

