"""
Admin license tiers management page.
"""

import flet as ft
import logging
from typing import Optional, List, Dict
from admin.services.admin_license_tier_service import admin_license_tier_service
from admin.ui.dialogs import LicenseTierFormDialog, DeleteConfirmDialog

logger = logging.getLogger(__name__)


class AdminLicenseTiersPage(ft.Container):
    """Admin license tiers management page."""
    
    # Dark theme colors
    BG_COLOR = "#1e1e1e"
    TEXT_COLOR = "#ffffff"
    TEXT_SECONDARY = "#aaaaaa"
    PRIMARY_COLOR = "#0078d4"
    CARD_BG = "#252525"
    CARD_HOVER_BG = "#2a2a2a"
    BORDER_COLOR = "#333333"
    BORDER_HOVER_COLOR = "#404040"
    
    def __init__(self, page: ft.Page):
        self.page = page
        self.tiers: List[Dict] = []
        self.filtered_tiers: List[Dict] = []
        
        # Search field with clear button
        self.search_input = ft.TextField(
            hint_text="Search by name, tier key...",
            bgcolor=self.CARD_BG,
            color=self.TEXT_COLOR,
            border_color=self.BORDER_COLOR,
            border_radius=8,
            on_change=self._on_search,
            expand=True,
            prefix_icon=ft.Icons.SEARCH,
            suffix_icon=ft.Icons.CLEAR if hasattr(ft.Icons, 'CLEAR') else None,
        )
        
        self.search_field = ft.Container(
            content=self.search_input,
            expand=True,
        )
        
        # Cards container with better spacing
        self.cards_container = ft.Row(
            controls=[],
            wrap=True,
            spacing=20,
            run_spacing=20,
            expand=True,
        )
        
        # Result count text
        self.result_count_text = ft.Text(
            "",
            size=13,
            color=self.TEXT_SECONDARY,
        )
        
        # Scrollable container for cards
        self.scrollable_content = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            self.search_field,
                        ],
                        spacing=10,
                    ),
                    ft.Row(
                        controls=[
                            self.result_count_text,
                        ],
                    ),
                    ft.Divider(height=15, color="transparent"),
                    ft.Container(
                        content=ft.Column(
                            controls=[self.cards_container],
                            scroll=ft.ScrollMode.AUTO,
                            spacing=0,
                            expand=True,
                        ),
                        expand=True,
                    ),
                ],
                spacing=5,
                expand=True,
            ),
            expand=True,
        )
        
        self.create_button = ft.ElevatedButton(
            text="+ Create Tier",
            icon=ft.Icons.ADD,
            bgcolor=self.PRIMARY_COLOR,
            color=self.TEXT_COLOR,
            on_click=self._on_create_tier,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=8),
                padding=ft.padding.symmetric(horizontal=20, vertical=12),
            ),
        )
        
        self.sync_to_json_button = ft.ElevatedButton(
            text="Sync to JSON",
            icon=ft.Icons.DOWNLOAD,
            bgcolor="#4caf50",
            color=self.TEXT_COLOR,
            on_click=self._on_sync_to_json,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=8),
                padding=ft.padding.symmetric(horizontal=20, vertical=12),
            ),
        )
        
        super().__init__(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Row(
                                controls=[
                                    ft.Icon(ft.Icons.STAR, size=32, color=self.PRIMARY_COLOR),
                            ft.Text(
                                "License Tiers",
                                size=28,
                                weight=ft.FontWeight.BOLD,
                                color=self.TEXT_COLOR,
                                    ),
                                ],
                                spacing=12,
                            ),
                            ft.Row(
                                controls=[
                                    self.sync_to_json_button,
                                    self.create_button,
                                ],
                                spacing=12,
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    ft.Divider(height=20, color="transparent"),
                    self.scrollable_content,
                ],
                spacing=10,
                expand=True,
            ),
            padding=ft.padding.all(20),
            bgcolor=self.BG_COLOR,
            expand=True,
        )
        
        self._load_tiers()
    
    def _load_tiers(self, show_loading: bool = False):
        """Load license tiers and populate cards."""
        try:
            # Only show loading state if explicitly requested and control is on page
            if show_loading:
                self._safe_update(lambda: self._show_loading())
            
            self.tiers = admin_license_tier_service.get_all_tiers()
            # Sort tiers by price (USD first, then KHR) in ascending order
            self.tiers = self._sort_tiers_by_price(self.tiers)
            self.filtered_tiers = self.tiers.copy()
            self._render_cards()
            
        except Exception as e:
            logger.error(f"Error loading license tiers: {e}", exc_info=True)
            self._safe_update(lambda: self._show_error(str(e)))
    
    def _sort_tiers_by_price(self, tiers: List[Dict]) -> List[Dict]:
        """Sort tiers by price in ascending order (USD first, then KHR)."""
        def get_sort_key(tier: Dict) -> tuple:
            """Get sort key for tier: (price_usd, price_khr)."""
            price_usd = float(tier.get("price_usd", 0) or 0)
            price_khr = float(tier.get("price_khr", 0) or 0)
            # Sort by USD first, then KHR
            return (price_usd, price_khr)
        
        return sorted(tiers, key=get_sort_key)
    
    def _safe_update(self, update_func):
        """Safely execute update function only if control is on page."""
        try:
            # Try to update - if control is not on page, this will raise AssertionError
            update_func()
        except AssertionError:
            # Control not on page yet, skip update
            pass
    
    def _show_loading(self):
        """Show loading state."""
        self.result_count_text.value = "Loading..."
        self.cards_container.controls = [
            ft.Container(
                content=ft.Column(
                    controls=[
                        ft.ProgressRing(color=self.PRIMARY_COLOR, width=50, height=50),
                        ft.Text("Loading license tiers...", color=self.TEXT_SECONDARY, size=14),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=15,
                ),
                padding=ft.padding.all(60),
                alignment=ft.alignment.center,
                expand=True,
            )
        ]
        self.update()
    
    def _show_error(self, error_msg: str):
        """Show error state."""
        self.result_count_text.value = "Error loading tiers"
        self.cards_container.controls = [
            ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Container(
                            content=ft.Icon(ft.Icons.ERROR_OUTLINE, size=64, color="#f44336"),
                            padding=ft.padding.all(20),
                            bgcolor="#f4433610",
                            border_radius=50,
                        ),
                        ft.Text(
                            "Failed to load license tiers",
                            size=18,
                            color=self.TEXT_COLOR,
                            weight=ft.FontWeight.BOLD,
                        ),
                        ft.Text(
                            error_msg,
                            size=12,
                            color=self.TEXT_SECONDARY,
                            text_align=ft.TextAlign.CENTER,
                        ),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=15,
                ),
                padding=ft.padding.all(40),
                alignment=ft.alignment.center,
            )
        ]
        self.update()
    
    def _on_search(self, e: ft.ControlEvent):
        """Handle search input."""
        query = e.control.value.lower().strip()
        if not query:
            self.filtered_tiers = self.tiers.copy()
        else:
            self.filtered_tiers = [
                tier for tier in self.tiers
                if query in tier.get("name", "").lower()
                or query in tier.get("tier_key", "").lower()
            ]
        # Maintain price order after filtering
        self.filtered_tiers = self._sort_tiers_by_price(self.filtered_tiers)
        self._render_cards()
    
    def _render_cards(self):
        """Render license tier cards."""
        self.cards_container.controls = []
        
        # Update result count
        total_count = len(self.tiers)
        filtered_count = len(self.filtered_tiers)
        if filtered_count == total_count:
            self.result_count_text.value = f"Showing {total_count} tier{'s' if total_count != 1 else ''}"
        else:
            self.result_count_text.value = f"Showing {filtered_count} of {total_count} tier{'s' if total_count != 1 else ''}"
        
        if not self.filtered_tiers:
            # Show empty state
            empty_text = "No license tiers match your search" if self.search_input.value else "No license tiers found"
            self.cards_container.controls.append(
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Container(
                                content=ft.Icon(ft.Icons.SEARCH_OFF, size=72, color=self.TEXT_SECONDARY),
                                padding=ft.padding.all(20),
                                bgcolor=f"{self.TEXT_SECONDARY}10",
                                border_radius=50,
                            ),
                            ft.Text(
                                empty_text,
                                size=18,
                                color=self.TEXT_COLOR,
                                weight=ft.FontWeight.BOLD,
                            ),
                            ft.Text(
                                "Try adjusting your search or create a new tier",
                                size=13,
                                color=self.TEXT_SECONDARY,
                                text_align=ft.TextAlign.CENTER,
                            ),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=15,
                    ),
                    padding=ft.padding.all(60),
                    alignment=ft.alignment.center,
                    width=500,
                )
            )
        else:
            for tier in self.filtered_tiers:
                card = self._create_tier_card(tier)
                self.cards_container.controls.append(card)
        
        # Only update if control is on the page
        self._safe_update(lambda: self.update())
    
    def _create_tier_card(self, tier: Dict) -> ft.Container:
        """Create a modern card for a license tier."""
        tier_key = tier.get("tier_key", "")
        tier_name = tier.get("name", tier_key)
        
        # Format price with better display
        price_usd = tier.get("price_usd", 0)
        price_khr = tier.get("price_khr", 0)
        if price_usd == 0 and price_khr == 0:
            price_str = "Free"
            price_length = 4
        else:
            # Format USD price (remove .0 if it's a whole number)
            if isinstance(price_usd, float) and price_usd.is_integer():
                usd_str = f"${int(price_usd)}"
            else:
                usd_str = f"${price_usd}"
            
            if price_khr > 0:
                # Format KHR price (remove .0 if it's a whole number)
                if isinstance(price_khr, float) and price_khr.is_integer():
                    khr_str = f"{int(price_khr):,} KHR"
                else:
                    khr_str = f"{price_khr:,.0f} KHR"
                price_str = f"{usd_str} / {khr_str}"
            else:
                price_str = usd_str
            
            # Estimate length for font size calculation
            price_length = len(price_str)
        
        # Format limits
        max_groups = tier.get("max_groups", 1)
        max_groups_str = "Unlimited" if max_groups == -1 else str(max_groups)
        max_devices = tier.get("max_devices", 1)
        max_accounts = tier.get("max_accounts", 1)
        period = tier.get("period", 30)
        
        # Get in-use count
        in_use_count = admin_license_tier_service.get_tiers_in_use_count(tier_key)
        
        # Get tier color based on tier key with better colors
        tier_colors = {
            "bronze": "#cd7f32",
            "silver": "#c0c0c0",
            "gold": "#ffd700",
            "premium": "#9b59b6",
        }
        tier_color = tier_colors.get(tier_key.lower(), self.PRIMARY_COLOR)
        
        # Create card with hover effect
        card_container = ft.Container(
            content=ft.Column(
                controls=[
                    # Header with tier name and badge
                    ft.Row(
                        controls=[
                            ft.Container(
                                content=ft.Text(
                                    tier_name,
                                    size=22,
                                    weight=ft.FontWeight.BOLD,
                                    color=self.TEXT_COLOR,
                                ),
                                expand=True,
                            ),
                            ft.Container(
                                content=ft.Text(
                                    tier_key.upper(),
                                    size=10,
                                    weight=ft.FontWeight.BOLD,
                                    color=tier_color,
                                ),
                                padding=ft.padding.symmetric(horizontal=10, vertical=5),
                                bgcolor=f"{tier_color}25",
                                border=ft.border.all(1, f"{tier_color}50"),
                                border_radius=6,
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    ft.Divider(height=18, color="transparent"),
                    # Price section with better styling (no wrap, adaptive font size)
                    ft.Container(
                        content=ft.Row(
                            controls=[
                                ft.Container(
                                    content=ft.Icon(ft.Icons.ATTACH_MONEY, size=24, color=tier_color),
                                    padding=ft.padding.all(8),
                                    bgcolor=f"{tier_color}15",
                                    border_radius=8,
                                ),
                                ft.Container(
                                    content=ft.Text(
                                        price_str,
                                        size=26 if price_length <= 20 else (22 if price_length <= 30 else 18),
                                        weight=ft.FontWeight.BOLD,
                                        color=tier_color,
                                        no_wrap=True,
                                        overflow=ft.TextOverflow.ELLIPSIS,
                                    ),
                                    expand=True,
                                ),
                            ],
                            spacing=12,
                            wrap=False,
                        ),
                        padding=ft.padding.symmetric(vertical=8),
                    ),
                    ft.Divider(height=20, color="transparent"),
                    # Divider line
                    ft.Container(
                        height=1,
                        bgcolor=self.BORDER_COLOR,
                        border_radius=1,
                    ),
                    ft.Divider(height=20, color="transparent"),
                    # Limits section with better visual hierarchy
                    ft.Container(
                        content=ft.Column(
                            controls=[
                                self._create_info_row("Groups", max_groups_str, ft.Icons.GROUP, tier_color),
                                self._create_info_row("Devices", str(max_devices), ft.Icons.DEVICES, tier_color),
                                self._create_info_row("Accounts", str(max_accounts), ft.Icons.PERSON, tier_color),
                                self._create_info_row("Period", f"{period} days", ft.Icons.CALENDAR_TODAY, tier_color),
                            ],
                            spacing=12,
                        ),
                    ),
                    ft.Divider(height=20, color="transparent"),
                    # Footer with in-use count and actions
                    ft.Container(
                        content=ft.Row(
                            controls=[
                                ft.Container(
                                    content=ft.Row(
                                        controls=[
                                            ft.Icon(ft.Icons.INFO_OUTLINE, size=16, color=self.TEXT_SECONDARY),
                                            ft.Text(
                                                f"In Use: {in_use_count}",
                                                size=12,
                                                color=self.TEXT_SECONDARY,
                                            ),
                                        ],
                                        spacing=6,
                                    ),
                                    padding=ft.padding.symmetric(horizontal=8, vertical=6),
                                    bgcolor=f"{self.TEXT_SECONDARY}10",
                                    border_radius=6,
                                ),
                                ft.Row(
                                    controls=[
                                        ft.IconButton(
                                            icon=ft.Icons.EDIT,
                                            icon_color=self.PRIMARY_COLOR,
                                            icon_size=20,
                                            tooltip="Edit Tier",
                                            bgcolor=f"{self.PRIMARY_COLOR}15",
                                            style=ft.ButtonStyle(
                                                shape=ft.RoundedRectangleBorder(radius=6),
                                            ),
                                            on_click=lambda e, t=tier: self._on_edit_tier(t),
                                        ),
                                        ft.IconButton(
                                            icon=ft.Icons.DELETE,
                                            icon_color="#f44336",
                                            icon_size=20,
                                            tooltip="Delete Tier",
                                            bgcolor="#f4433615",
                                            style=ft.ButtonStyle(
                                                shape=ft.RoundedRectangleBorder(radius=6),
                                            ),
                                            on_click=lambda e, t=tier: self._on_delete_tier(t),
                                        ),
                                    ],
                                    spacing=8,
                                ),
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        ),
                    ),
                ],
                spacing=0,
            ),
            width=340,
            padding=ft.padding.all(24),
            bgcolor=self.CARD_BG,
            border=ft.border.all(1, self.BORDER_COLOR),
            border_radius=16,
            shadow=[
                ft.BoxShadow(
                    spread_radius=0,
                    blur_radius=20,
                    color="#00000030",
                    offset=ft.Offset(0, 4),
                ),
            ],
        )
        
        # Add hover effect
        def on_hover(e: ft.ControlEvent):
            if e.data == "true":
                card_container.bgcolor = self.CARD_HOVER_BG
                card_container.border = ft.border.all(1, self.BORDER_HOVER_COLOR)
                card_container.shadow = [
                    ft.BoxShadow(
                        spread_radius=0,
                        blur_radius=30,
                        color="#00000050",
                        offset=ft.Offset(0, 8),
                    ),
                ]
            else:
                card_container.bgcolor = self.CARD_BG
                card_container.border = ft.border.all(1, self.BORDER_COLOR)
                card_container.shadow = [
                    ft.BoxShadow(
                        spread_radius=0,
                        blur_radius=20,
                        color="#00000030",
                        offset=ft.Offset(0, 4),
                    ),
                ]
            card_container.update()
        
        card_container.on_hover = on_hover
        
        return card_container
    
    def _create_info_row(self, label: str, value: str, icon: str, accent_color: str) -> ft.Row:
        """Create an info row for card details with improved styling."""
        return ft.Row(
            controls=[
                ft.Container(
                    content=ft.Icon(icon, size=18, color=accent_color),
                    padding=ft.padding.all(6),
                    bgcolor=f"{accent_color}15",
                    border_radius=6,
                ),
                ft.Column(
                    controls=[
                        ft.Text(
                            label,
                            size=11,
                            color=self.TEXT_SECONDARY,
                            weight=ft.FontWeight.NORMAL,
                        ),
                        ft.Text(
                            value,
                            size=15,
                            color=self.TEXT_COLOR,
                            weight=ft.FontWeight.BOLD,
                        ),
                    ],
                    spacing=2,
                    expand=True,
                ),
            ],
            spacing=12,
            alignment=ft.MainAxisAlignment.START,
        )
    
    def _on_create_tier(self, e: ft.ControlEvent):
        """Handle create tier button click."""
        dialog = LicenseTierFormDialog(
            tier_data=None,
            on_submit=self._handle_create_tier,
        )
        dialog.page = self.page
        try:
            self.page.open(dialog)
        except Exception as ex:
            logger.error(f"Error opening create tier dialog: {ex}")
            self.page.dialog = dialog
            dialog.open = True
            self.page.update()
    
    def _on_edit_tier(self, tier: dict):
        """Handle edit tier action."""
        dialog = LicenseTierFormDialog(
            tier_data=tier,
            on_submit=self._handle_update_tier,
        )
        dialog.page = self.page
        try:
            self.page.open(dialog)
        except Exception as ex:
            logger.error(f"Error opening edit tier dialog: {ex}")
            self.page.dialog = dialog
            dialog.open = True
            self.page.update()
    
    def _on_delete_tier(self, tier: dict):
        """Handle delete tier action."""
        tier_key = tier.get("tier_key", "unknown")
        tier_name = tier.get("name", tier_key)
        in_use_count = admin_license_tier_service.get_tiers_in_use_count(tier_key)
        
        warning_msg = f"Are you sure you want to delete the '{tier_name}' tier?"
        if in_use_count > 0:
            warning_msg += f"\n\n⚠️ WARNING: This tier is currently used by {in_use_count} license(s). Deleting it may cause issues."
        
        dialog = DeleteConfirmDialog(
            title="Delete License Tier",
            message=warning_msg,
            item_name=tier_key,
            on_confirm=lambda: self._handle_delete_tier(tier_key),
        )
        dialog.page = self.page
        try:
            self.page.open(dialog)
        except Exception as ex:
            logger.error(f"Error opening delete confirmation dialog: {ex}")
            self.page.dialog = dialog
            dialog.open = True
            self.page.update()
    
    def _on_sync_to_json(self, e: ft.ControlEvent):
        """Handle sync to JSON button click."""
        try:
            # Disable button during sync
            self.sync_to_json_button.disabled = True
            self.sync_to_json_button.text = "Syncing..."
            self.sync_to_json_button.update()
            
            success = admin_license_tier_service.sync_tiers_to_json()
            
            if success:
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text("License tiers synced to JSON file successfully"),
                    bgcolor="#4caf50",
                )
            else:
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text("Failed to sync license tiers to JSON. Please check logs."),
                    bgcolor="#f44336",
                )
            
            self.page.snack_bar.open = True
            self.page.update()
            
        except Exception as e:
            logger.error(f"Error syncing tiers to JSON: {e}", exc_info=True)
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(f"Error syncing tiers to JSON: {str(e)}"),
                bgcolor="#f44336",
            )
            self.page.snack_bar.open = True
            self.page.update()
        finally:
            self.sync_to_json_button.disabled = False
            self.sync_to_json_button.text = "Sync to JSON"
            self.sync_to_json_button.update()
    
    def _handle_create_tier(self, tier_key: str, tier_data: dict, update_existing: bool):
        """Handle tier creation."""
        try:
            success = admin_license_tier_service.create_tier(tier_key, tier_data)
            
            if success:
                # Reload tiers
                self._reload_tiers()
                
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text(f"License tier '{tier_key}' created successfully"),
                    bgcolor="#4caf50",
                )
            else:
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text("Failed to create license tier. Please check logs."),
                    bgcolor="#f44336",
                )
            
            self.page.snack_bar.open = True
            self.page.update()
            
        except Exception as e:
            logger.error(f"Error creating license tier: {e}", exc_info=True)
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(f"Error creating license tier: {str(e)}"),
                bgcolor="#f44336",
            )
            self.page.snack_bar.open = True
            self.page.update()
    
    def _handle_update_tier(self, tier_key: str, tier_data: dict, update_existing: bool):
        """Handle tier update."""
        try:
            success = admin_license_tier_service.update_tier(tier_key, tier_data)
            
            if success:
                # Update existing licenses if requested
                if update_existing:
                    updated_count = admin_license_tier_service.update_existing_licenses(tier_key, tier_data)
                    if updated_count > 0:
                        logger.info(f"Updated {updated_count} existing licenses for tier {tier_key}")
                
                # Reload tiers
                self._reload_tiers()
                
                update_msg = f"License tier '{tier_key}' updated successfully"
                if update_existing:
                    updated_count = admin_license_tier_service.update_existing_licenses(tier_key, tier_data)
                    update_msg += f" ({updated_count} licenses updated)"
                
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text(update_msg),
                    bgcolor="#4caf50",
                )
            else:
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text("Failed to update license tier. Please check logs."),
                    bgcolor="#f44336",
                )
            
            self.page.snack_bar.open = True
            self.page.update()
            
        except Exception as e:
            logger.error(f"Error updating license tier: {e}", exc_info=True)
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(f"Error updating license tier: {str(e)}"),
                bgcolor="#f44336",
            )
            self.page.snack_bar.open = True
            self.page.update()
    
    def _handle_delete_tier(self, tier_key: str):
        """Handle tier deletion."""
        try:
            success = admin_license_tier_service.delete_tier(tier_key)
            
            if success:
                # Reload tiers
                self._reload_tiers()
                
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text(f"License tier '{tier_key}' deleted successfully"),
                    bgcolor="#4caf50",
                )
            else:
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text("Failed to delete license tier. Please check logs."),
                    bgcolor="#f44336",
                )
            
            self.page.snack_bar.open = True
            self.page.update()
            
        except Exception as e:
            logger.error(f"Error deleting license tier: {e}", exc_info=True)
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(f"Error deleting license tier: {str(e)}"),
                bgcolor="#f44336",
            )
            self.page.snack_bar.open = True
            self.page.update()
    
    def _reload_tiers(self):
        """Reload tiers cards."""
        self._load_tiers(show_loading=True)

