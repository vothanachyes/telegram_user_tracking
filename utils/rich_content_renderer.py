"""
Rich content renderer utility for rendering formatted text, links, and other rich content in Flet UI.
"""

import re
import flet as ft
from typing import List, Optional, Tuple

from ui.theme import theme_manager


# URL pattern for detecting links in text
URL_PATTERN = re.compile(
    r'https?://[^\s<>"{}|\\^`\[\]]+|'
    r'www\.[^\s<>"{}|\\^`\[\]]+|'
    r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
)


class RichContentRenderer:
    """Renders rich content (links, formatted text) in Flet UI components."""
    
    @staticmethod
    def render_text_with_links(
        text: str,
        max_lines: Optional[int] = None,
        overflow: ft.TextOverflow = ft.TextOverflow.ELLIPSIS,
        size: Optional[int] = None,
        color: Optional[str] = None,
        weight: Optional[ft.FontWeight] = None,
        on_link_click: Optional[callable] = None
    ) -> ft.Row:
        """
        Render text with clickable links.
        
        Args:
            text: Text content that may contain URLs
            max_lines: Maximum number of lines to display
            overflow: Text overflow behavior
            size: Font size
            color: Text color
            weight: Font weight
            on_link_click: Optional callback for link clicks (receives url as parameter)
            
        Returns:
            ft.Row containing text spans with clickable links
        """
        if not text:
            return ft.Row([ft.Text("", size=size, color=color, weight=weight)])
        
        # Find all URLs in the text
        parts: List[Tuple[str, bool, Optional[str]]] = []  # (text, is_link, url)
        last_end = 0
        has_links = False
        
        for match in URL_PATTERN.finditer(text):
            has_links = True
            # Add text before the link
            if match.start() > last_end:
                parts.append((text[last_end:match.start()], False, None))
            
            # Add the link
            link_text = match.group(0)
            # Normalize link (add https:// if missing)
            if link_text.startswith('www.'):
                link_url = f"https://{link_text}"
            elif not link_text.startswith(('http://', 'https://')):
                # Email address
                link_url = f"mailto:{link_text}"
            else:
                link_url = link_text
            
            parts.append((link_text, True, link_url))
            last_end = match.end()
        
        # Add remaining text
        if last_end < len(text):
            parts.append((text[last_end:], False, None))
        
        # If no links found, return simple text
        if not has_links:
            return ft.Row([
                ft.Text(
                    text,
                    size=size,
                    color=color or theme_manager.text_color,
                    weight=weight,
                    max_lines=max_lines,
                    overflow=overflow
                )
            ])
        
        # Build row with text spans and clickable links
        controls: List[ft.Control] = []
        for part_text, is_link, url in parts:
            
            if is_link and url:
                # Create clickable link
                link_color = theme_manager.primary_color
                if theme_manager.is_dark:
                    # Use lighter color in dark mode for better contrast
                    from utils.constants import COLORS
                    link_color = COLORS.get("secondary", theme_manager.primary_color)
                
                link_control = ft.TextButton(
                    content=ft.Text(
                        part_text,
                        size=size or theme_manager.font_size_body,
                        color=link_color,
                        weight=weight,
                        max_lines=1,
                        overflow=overflow
                    ),
                    on_click=lambda e, u=url: RichContentRenderer._handle_link_click(u, on_link_click),
                    tooltip=url
                )
                controls.append(link_control)
            else:
                # Regular text
                controls.append(
                    ft.Text(
                        part_text,
                        size=size or theme_manager.font_size_body,
                        color=color or theme_manager.text_color,
                        weight=weight,
                        max_lines=max_lines if not controls else None,  # Only apply max_lines to first text
                        overflow=overflow
                    )
                )
        
        return ft.Row(controls, wrap=True, spacing=0)
    
    @staticmethod
    def render_simple_link(
        url: str,
        text: Optional[str] = None,
        icon: Optional[str] = None,
        size: Optional[int] = None,
        tooltip: Optional[str] = None,
        on_click: Optional[callable] = None
    ) -> ft.Control:
        """
        Render a simple clickable link.
        
        Args:
            url: Link URL
            text: Link text (defaults to URL if not provided)
            icon: Optional icon name (e.g., "OPEN_IN_NEW")
            size: Font size
            tooltip: Tooltip text
            on_click: Optional click handler (receives url as parameter)
            
        Returns:
            ft.Control (TextButton or IconButton)
        """
        if icon:
            return ft.IconButton(
                icon=getattr(ft.Icons, icon, ft.Icons.OPEN_IN_NEW),
                icon_color=theme_manager.primary_color,
                tooltip=tooltip or url,
                on_click=lambda e: RichContentRenderer._handle_link_click(url, on_click),
                icon_size=size or 20
            )
        else:
            link_color = theme_manager.primary_color
            if theme_manager.is_dark:
                from utils.constants import COLORS
                link_color = COLORS.get("secondary", theme_manager.primary_color)
            
            return ft.TextButton(
                content=ft.Text(
                    text or url,
                    size=size or theme_manager.font_size_body,
                    color=link_color,
                    max_lines=1,
                    overflow=ft.TextOverflow.ELLIPSIS
                ),
                on_click=lambda e: RichContentRenderer._handle_link_click(url, on_click),
                tooltip=tooltip or url
            )
    
    @staticmethod
    def extract_links(text: str) -> List[str]:
        """
        Extract all links from text.
        
        Args:
            text: Text to search for links
            
        Returns:
            List of URLs found in text
        """
        if not text:
            return []
        
        links = []
        for match in URL_PATTERN.finditer(text):
            link = match.group(0)
            if link.startswith('www.'):
                link = f"https://{link}"
            links.append(link)
        
        return links
    
    @staticmethod
    def has_links(text: str) -> bool:
        """
        Check if text contains any links.
        
        Args:
            text: Text to check
            
        Returns:
            True if text contains links, False otherwise
        """
        if not text:
            return False
        return bool(URL_PATTERN.search(text))
    
    @staticmethod
    def _handle_link_click(url: str, custom_handler: Optional[callable] = None):
        """
        Handle link click event.
        
        Args:
            url: URL to open
            custom_handler: Optional custom handler function
        """
        if custom_handler:
            try:
                custom_handler(url)
            except Exception:
                # Fallback to default behavior
                RichContentRenderer._open_link(url)
        else:
            RichContentRenderer._open_link(url)
    
    @staticmethod
    def _open_link(url: str):
        """
        Open a link in the default browser.
        
        Args:
            url: URL to open
        """
        import webbrowser
        try:
            webbrowser.open(url)
        except Exception:
            pass  # Silently fail if browser can't be opened

