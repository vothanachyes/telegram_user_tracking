"""
Reusable statistics cards grid component.
"""

import flet as ft
from typing import List, Dict, Optional
from ui.theme import theme_manager
from ui.components.stat_card import StatCard


class StatCardsGrid:
    """Reusable grid component for displaying statistics cards."""
    
    def __init__(
        self,
        title: Optional[str] = None,
        cards_per_row: int = 4,
        spacing: int = 15
    ):
        """
        Initialize statistics cards grid.
        
        Args:
            title: Optional title for the grid
            cards_per_row: Number of cards per row (default: 4)
            spacing: Spacing between cards (default: 15)
        """
        self.title = title
        self.cards_per_row = cards_per_row
        self.spacing = spacing
        self.cards: List[StatCard] = []
        
        self.container = ft.Container(
            content=self._build_empty_state(),
            padding=10,
            expand=True
        )
    
    def build(self) -> ft.Container:
        """Build and return the grid container."""
        return self.container
    
    def update_cards(self, cards: List[StatCard], title: Optional[str] = None):
        """
        Update the grid with new cards.
        
        Args:
            cards: List of StatCard components
            title: Optional title override
        """
        self.cards = cards
        if title is not None:
            self.title = title
        
        if not cards:
            self.container.content = self._build_empty_state()
            return
        
        # Build rows
        rows = []
        if self.title:
            rows.append(
                ft.Text(
                    self.title,
                    size=20,
                    weight=ft.FontWeight.BOLD
                )
            )
            rows.append(ft.Divider())
        
        # Group cards into rows
        for i in range(0, len(cards), self.cards_per_row):
            row_cards = cards[i:i + self.cards_per_row]
            rows.append(
                ft.Row(
                    row_cards,
                    spacing=self.spacing,
                    wrap=True
                )
            )
        
        self.container.content = ft.Column(
            rows,
            spacing=self.spacing,
            expand=True
        )
    
    def update_from_dict(
        self,
        stats: Dict[str, any],
        stat_definitions: List[Dict[str, str]],
        title: Optional[str] = None
    ):
        """
        Update cards from a dictionary of statistics.
        
        Args:
            stats: Dictionary with stat keys and values
            stat_definitions: List of dicts with keys: 'key', 'label', 'icon', 'color' (optional)
            title: Optional title override
        """
        cards = []
        for stat_def in stat_definitions:
            stat_key = stat_def.get('key')
            stat_value = str(stats.get(stat_key, 0))
            stat_label = stat_def.get('label', stat_key)
            stat_icon = stat_def.get('icon', ft.Icons.INFO)
            stat_color = stat_def.get('color', theme_manager.primary_color)
            
            cards.append(
                StatCard(
                    title=stat_label,
                    value=stat_value,
                    icon=stat_icon,
                    color=stat_color
                )
            )
        
        self.update_cards(cards, title)
    
    def show_empty_state(self, message: Optional[str] = None):
        """
        Show empty state message.
        
        Args:
            message: Optional custom message
        """
        self.container.content = ft.Column([
            ft.Text(
                message or theme_manager.t("no_data_available"),
                size=16,
                color=theme_manager.text_secondary_color,
                text_align=ft.TextAlign.CENTER
            )
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=20)
    
    def _build_empty_state(self) -> ft.Column:
        """Build empty state column."""
        return ft.Column([
            ft.Text(
                theme_manager.t("no_data_available"),
                size=16,
                color=theme_manager.text_secondary_color,
                text_align=ft.TextAlign.CENTER
            )
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=20)

