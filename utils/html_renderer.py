"""
HTML renderer utility for converting HTML content to Flet UI components using BeautifulSoup4.
Supports CSS styling from <style> tags and inline styles.
"""

import logging
import re
import webbrowser
from typing import List, Optional, Dict, Tuple
import flet as ft
from bs4 import BeautifulSoup, Tag, NavigableString
from ui.theme import theme_manager

logger = logging.getLogger(__name__)

# Pattern to detect HTML tags
HTML_TAG_PATTERN = re.compile(r'<[^>]+>', re.IGNORECASE)


class CSSParser:
    """Parse CSS rules from style tags."""
    
    @staticmethod
    def parse_css(css_text: str) -> Dict[str, Dict[str, str]]:
        """
        Parse CSS text and return a dictionary of selectors to properties.
        
        Args:
            css_text: CSS text content
            
        Returns:
            Dictionary mapping selectors to property dictionaries
        """
        rules = {}
        if not css_text:
            return rules
        
        # Remove comments
        css_text = re.sub(r'/\*.*?\*/', '', css_text, flags=re.DOTALL)
        
        # Split by rules (semicolon outside braces)
        rule_pattern = r'([^{]+)\{([^}]+)\}'
        for match in re.finditer(rule_pattern, css_text):
            selector = match.group(1).strip()
            properties_text = match.group(2).strip()
            
            # Parse properties
            properties = {}
            for prop_match in re.finditer(r'([^:]+):([^;]+);?', properties_text):
                prop_name = prop_match.group(1).strip()
                prop_value = prop_match.group(2).strip()
                properties[prop_name] = prop_value
            
            # Handle multiple selectors (comma-separated)
            for sel in selector.split(','):
                sel = sel.strip()
                # Normalize selector (remove whitespace)
                sel = re.sub(r'\s+', ' ', sel)
                if sel:
                    rules[sel] = properties
        
        return rules
    
    @staticmethod
    def get_matching_rules(element: Tag, css_rules: Dict[str, Dict[str, str]]) -> Dict[str, str]:
        """
        Get CSS rules that match an element.
        
        Args:
            element: BeautifulSoup Tag element
            css_rules: Dictionary of CSS rules
            
        Returns:
            Merged properties dictionary (inline styles take precedence)
        """
        properties = {}
        
        # Get element classes
        classes = element.get('class', [])
        if not isinstance(classes, list):
            classes = [classes] if classes else []
        
        # Get element tag name
        tag_name = element.name.lower()
        
        # Match rules
        for selector, rule_props in css_rules.items():
            if CSSParser._selector_matches(selector, element, tag_name, classes):
                # Merge properties (later rules override earlier ones)
                properties.update(rule_props)
        
        return properties
    
    @staticmethod
    def _selector_matches(selector: str, element: Tag, tag_name: str, classes: List[str]) -> bool:
        """Check if a CSS selector matches an element."""
        selector = selector.strip()
        
        # Simple class selector (.class)
        if selector.startswith('.'):
            class_name = selector[1:].strip()
            return class_name in classes
        
        # Simple tag selector (tag)
        if selector == tag_name:
            return True
        
        # Tag with class (tag.class)
        if '.' in selector and not selector.startswith('.'):
            parts = selector.split('.')
            if len(parts) == 2 and parts[0].strip() == tag_name:
                return parts[1].strip() in classes
        
        # Descendant selector (tag .class or .class tag)
        if ' ' in selector:
            parts = selector.split()
            # Simple case: check if all parts match
            if len(parts) == 2:
                if parts[0] == tag_name or (parts[0].startswith('.') and parts[0][1:] in classes):
                    return True
        
        return False


class HTMLRenderer:
    """Renders HTML content to Flet UI components using BeautifulSoup4."""
    
    @staticmethod
    def render_html_to_flet(html_content: str) -> ft.Control:
        """
        Render HTML content to Flet components.
        
        Args:
            html_content: HTML string to render
            
        Returns:
            ft.Container with ft.Column containing parsed Flet components
        """
        if not html_content or not html_content.strip():
            return ft.Text("", size=theme_manager.font_size_body)
        
        try:
            # Parse HTML with BeautifulSoup4
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Extract and parse CSS from <style> tags
            css_rules = {}
            for style_tag in soup.find_all('style'):
                css_text = style_tag.string or ''
                css_rules.update(CSSParser.parse_css(css_text))
            
            # Find body or main content
            body = soup.find('body')
            if body:
                root_element = body
            else:
                # If no body, use the whole document
                root_element = soup
            
            # Convert parsed HTML to Flet components
            controls = HTMLRenderer._parse_element(root_element, css_rules=css_rules, is_root=True)
            
            if not controls:
                # If parsing produced no controls, return plain text
                return ft.Text(
                    html_content,
                    size=theme_manager.font_size_body,
                    color=theme_manager.text_color,
                )
            
            return ft.Container(
                content=ft.Column(
                    controls=controls,
                    spacing=0,
                    scroll=ft.ScrollMode.AUTO,
                ),
                padding=ft.padding.all(0),
                border_radius=0,
            )
        except Exception as e:
            logger.error(f"Error rendering HTML: {e}", exc_info=True)
            # Fallback to plain text
            return ft.Text(
                html_content,
                size=theme_manager.font_size_body,
                color=theme_manager.text_color,
            )
    
    @staticmethod
    def _parse_element(
        element, 
        css_rules: Dict[str, Dict[str, str]] = None,
        is_root: bool = False
    ) -> List[ft.Control]:
        """
        Parse a BeautifulSoup element and convert to Flet controls.
        
        Args:
            element: BeautifulSoup element or NavigableString
            css_rules: Dictionary of CSS rules
            is_root: Whether this is the root element
            
        Returns:
            List of Flet controls
        """
        if css_rules is None:
            css_rules = {}
        
        controls: List[ft.Control] = []
        
        if isinstance(element, NavigableString):
            # Plain text node
            text = str(element).strip()
            if text:
                controls.append(
                    ft.Text(
                        text,
                        size=theme_manager.font_size_body,
                        color=theme_manager.text_color,
                    )
                )
        elif isinstance(element, Tag):
            tag_name = element.name.lower()
            
            # Skip script, style, head, meta, title tags
            if tag_name in ['script', 'style', 'head', 'meta', 'title']:
                return controls
            
            # Get CSS properties for this element
            css_props = CSSParser.get_matching_rules(element, css_rules) if css_rules else {}
            
            # Get inline style
            inline_style = element.get('style', '')
            inline_props = HTMLRenderer._parse_inline_style(inline_style)
            
            # Merge: inline styles override CSS rules
            all_props = {**css_props, **inline_props}
            
            # Get children
            children = list(element.children)
            
            # Handle different tag types
            if tag_name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                text = element.get_text(strip=True)
                if text:
                    size = HTMLRenderer._get_font_size(all_props, HTMLRenderer._get_heading_size(tag_name))
                    color = HTMLRenderer._get_color(all_props, theme_manager.text_color)
                    weight = HTMLRenderer._get_font_weight(all_props, ft.FontWeight.BOLD)
                    
                    text_control = ft.Text(
                        text,
                        size=size,
                        weight=weight,
                        color=color,
                    )
                    
                    # Wrap in container if there are background/padding styles
                    container = HTMLRenderer._apply_container_styles(text_control, all_props, tag_name, element)
                    controls.append(container)
                    controls.append(ft.Divider(height=HTMLRenderer._get_margin_bottom(all_props, 8), color="transparent"))
            
            elif tag_name in ['p', 'div']:
                # Parse children
                child_controls = []
                for child in children:
                    child_controls.extend(HTMLRenderer._parse_element(child, css_rules))
                
                if child_controls or element.get_text(strip=True):
                    # Create container for this element
                    content = ft.Column(controls=child_controls, spacing=0) if child_controls else None
                    if not content:
                        # If no child controls but has text, create text control
                        text = element.get_text(strip=True)
                        if text:
                            content = ft.Text(
                                text,
                                size=HTMLRenderer._get_font_size(all_props, theme_manager.font_size_body),
                                color=HTMLRenderer._get_color(all_props, theme_manager.text_color),
                                weight=HTMLRenderer._get_font_weight(all_props, ft.FontWeight.NORMAL),
                            )
                    
                    if content:
                        # Pass element to check for CSS classes
                        container = HTMLRenderer._apply_container_styles(content, all_props, tag_name, element)
                        controls.append(container)
                        # Add margin bottom
                        margin_bottom = HTMLRenderer._get_margin_bottom(all_props, 8)
                        if margin_bottom > 0:
                            controls.append(ft.Divider(height=margin_bottom, color="transparent"))
            
            elif tag_name in ['strong', 'b']:
                text = element.get_text(strip=True)
                if text:
                    controls.append(
                        ft.Text(
                            text,
                            size=HTMLRenderer._get_font_size(all_props, theme_manager.font_size_body),
                            weight=ft.FontWeight.BOLD,
                            color=HTMLRenderer._get_color(all_props, theme_manager.text_color),
                        )
                    )
            
            elif tag_name in ['em', 'i']:
                text = element.get_text(strip=True)
                if text:
                    controls.append(
                        ft.Text(
                            text,
                            size=HTMLRenderer._get_font_size(all_props, theme_manager.font_size_body),
                            color=HTMLRenderer._get_color(all_props, theme_manager.text_color),
                        )
                    )
            
            elif tag_name == 'span':
                text = element.get_text(strip=True)
                if text:
                    controls.append(
                        ft.Text(
                            text,
                            size=HTMLRenderer._get_font_size(all_props, theme_manager.font_size_body),
                            weight=HTMLRenderer._get_font_weight(all_props, ft.FontWeight.NORMAL),
                            color=HTMLRenderer._get_color(all_props, theme_manager.text_color),
                        )
                    )
            
            elif tag_name == 'a':
                # Get link URL
                href = element.get('href', '').strip()
                text = element.get_text(strip=True) or href
                
                if text:
                    link_color = HTMLRenderer._get_color(all_props, theme_manager.primary_color)
                    
                    # Create clickable link button
                    if href:
                        # Create a clickable button for the link
                        link_button = ft.TextButton(
                            content=ft.Text(
                                text,
                                size=HTMLRenderer._get_font_size(all_props, theme_manager.font_size_body),
                                color=link_color,
                            ),
                            on_click=lambda e, url=href: HTMLRenderer._open_link(url),
                            tooltip=href,
                        )
                        controls.append(link_button)
                    else:
                        # No href, just show text (anchor without link)
                        controls.append(
                            ft.Text(
                                text,
                                size=HTMLRenderer._get_font_size(all_props, theme_manager.font_size_body),
                                color=link_color,
                            )
                        )
            
            elif tag_name == 'button':
                # Get button text and onclick handler
                text = element.get_text(strip=True)
                onclick = element.get('onclick', '').strip()
                button_type = element.get('type', 'button').strip().lower()
                
                if text or onclick:
                    # Determine button style based on CSS
                    bg_color = HTMLRenderer._get_background_color(all_props)
                    
                    # Check for primary button classes
                    classes = element.get('class', [])
                    if not isinstance(classes, list):
                        classes = [classes] if classes else []
                    class_str = ' '.join(classes).lower()
                    
                    has_primary_style = (
                        bg_color == theme_manager.primary_color or
                        'primary' in class_str or
                        'btn-primary' in class_str
                    )
                    
                    # Use ElevatedButton for primary buttons, TextButton for others
                    if has_primary_style or bg_color:
                        button = ft.ElevatedButton(
                            text=text or "Button",
                            on_click=lambda e, handler=onclick: HTMLRenderer._handle_button_click(handler) if handler else None,
                            style=ft.ButtonStyle(
                                color=HTMLRenderer._get_color(all_props, theme_manager.text_color),
                                bgcolor=bg_color or theme_manager.primary_color,
                            ),
                        )
                    else:
                        button = ft.TextButton(
                            text=text or "Button",
                            on_click=lambda e, handler=onclick: HTMLRenderer._handle_button_click(handler) if handler else None,
                            style=ft.ButtonStyle(
                                color=HTMLRenderer._get_color(all_props, theme_manager.primary_color),
                            ),
                        )
                    
                    controls.append(button)
            
            elif tag_name in ['ul', 'ol']:
                for child in children:
                    if isinstance(child, Tag) and child.name == 'li':
                        child_controls = HTMLRenderer._parse_element(child, css_rules)
                        controls.extend(child_controls)
            
            elif tag_name == 'li':
                text = element.get_text(strip=True)
                if text:
                    prefix = "• " if element.find_parent('ul') else ""
                    controls.append(
                        ft.Text(
                            f"{prefix}{text}",
                            size=HTMLRenderer._get_font_size(all_props, theme_manager.font_size_body),
                            color=HTMLRenderer._get_color(all_props, theme_manager.text_color),
                        )
                    )
            
            else:
                # Unknown tag - parse children or get text
                if children:
                    for child in children:
                        controls.extend(HTMLRenderer._parse_element(child, css_rules))
                else:
                    text = element.get_text(strip=True)
                    if text:
                        controls.append(
                            ft.Text(
                                text,
                                size=HTMLRenderer._get_font_size(all_props, theme_manager.font_size_body),
                                color=HTMLRenderer._get_color(all_props, theme_manager.text_color),
                            )
                        )
        
        elif hasattr(element, 'children'):
            for child in element.children:
                controls.extend(HTMLRenderer._parse_element(child, css_rules))
        
        return controls
    
    @staticmethod
    def _apply_container_styles(
        content: ft.Control, 
        props: Dict[str, str], 
        tag_name: str, 
        element: Optional[Tag] = None
    ) -> ft.Control:
        """Apply container styles (background, padding, border, etc.) to a control."""
        # Check if we need a container
        needs_container = any(key in props for key in [
            'background', 'background-color', 'padding', 'margin', 
            'border-radius', 'border', 'text-align'
        ])
        
        if not needs_container:
            return content
        
        # Create container with styles
        container_kwargs = {'content': content}
        
        # Background color
        bg_color = HTMLRenderer._get_background_color(props)
        if bg_color:
            container_kwargs['bgcolor'] = bg_color
        
        # Padding
        padding = HTMLRenderer._parse_padding(props)
        if padding:
            container_kwargs['padding'] = padding
        
        # Border radius
        border_radius = HTMLRenderer._parse_border_radius(props)
        if border_radius is not None:
            container_kwargs['border_radius'] = border_radius
        
        # Border
        border = HTMLRenderer._parse_border(props)
        if border:
            container_kwargs['border'] = border
        elif bg_color and theme_manager.is_dark:
            # In dark mode, if there's a background color but no border, add a subtle border for visibility
            # Check if this looks like a card
            is_card = HTMLRenderer._is_card_element(element, props, tag_name, bg_color, padding, border_radius)
            if is_card:
                # Add a subtle border to make card visible in dark mode
                container_kwargs['border'] = ft.border.all(1, theme_manager.border_color)
        
        # Text alignment
        text_align = props.get('text-align', '').strip()
        if text_align == 'center':
            container_kwargs['alignment'] = ft.alignment.center
        elif text_align == 'right':
            container_kwargs['alignment'] = ft.alignment.center_right
        
        return ft.Container(**container_kwargs)
    
    @staticmethod
    def _is_card_element(
        element: Optional[Tag],
        props: Dict[str, str],
        tag_name: str,
        bg_color: Optional[str],
        padding: Optional[ft.padding],
        border_radius: Optional[int]
    ) -> bool:
        """Check if an element looks like a card."""
        if not bg_color:
            return False
        
        # Check for card-like CSS classes
        if element:
            classes = element.get('class', [])
            if not isinstance(classes, list):
                classes = [classes] if classes else []
            card_classes = ['card', 'welcome-card', 'panel', 'box', 'container']
            if any(cls in card_classes for cls in classes):
                return True
        
        # Check for card-like styling (background + padding/border-radius/box-shadow)
        has_card_styling = (
            bg_color and 
            (padding is not None or border_radius is not None or props.get('box-shadow')) and
            tag_name in ['div', 'section', 'article']
        )
        return has_card_styling
    
    @staticmethod
    def _parse_inline_style(style_str: str) -> Dict[str, str]:
        """Parse inline style string to properties dictionary."""
        props = {}
        if not style_str:
            return props
        
        for prop_match in re.finditer(r'([^:]+):([^;]+);?', style_str):
            prop_name = prop_match.group(1).strip()
            prop_value = prop_match.group(2).strip()
            props[prop_name] = prop_value
        
        return props
    
    @staticmethod
    def _get_font_size(props: Dict[str, str], default: int) -> int:
        """Extract font size from CSS properties."""
        font_size = props.get('font-size', '').strip()
        if font_size:
            # Remove 'px' and convert to int
            font_size = font_size.replace('px', '').strip()
            try:
                return int(float(font_size))
            except ValueError:
                pass
        return default
    
    @staticmethod
    def _get_color(props: Dict[str, str], default: str) -> str:
        """Extract color from CSS properties with dark mode support."""
        color = props.get('color', '').strip()
        if color:
            # Check if color is dark (for dark mode compatibility)
            if HTMLRenderer._is_dark_color(color) and theme_manager.is_dark:
                # In dark mode, if CSS specifies a dark color, use theme text color instead
                return default
            return color
        return default
    
    @staticmethod
    def _is_dark_color(color: str) -> bool:
        """Check if a color is dark (needs light text in dark mode)."""
        if not color:
            return False
        
        # Remove whitespace and convert to lowercase
        color = color.strip().lower()
        
        # Check for common dark colors
        dark_colors = [
            '#000', '#000000', 'black', 'rgb(0, 0, 0)',
            '#333', '#333333', 'rgb(51, 51, 51)',
            '#666', '#666666', 'rgb(102, 102, 102)',
        ]
        
        if color in dark_colors:
            return True
        
        # Check hex colors
        if color.startswith('#'):
            try:
                # Remove # and parse
                hex_color = color[1:]
                if len(hex_color) == 3:
                    hex_color = ''.join([c*2 for c in hex_color])
                if len(hex_color) == 6:
                    r = int(hex_color[0:2], 16)
                    g = int(hex_color[2:4], 16)
                    b = int(hex_color[4:6], 16)
                    # Calculate luminance
                    luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
                    # If luminance is less than 0.5, it's a dark color
                    return luminance < 0.5
            except (ValueError, IndexError):
                pass
        
        return False
    
    @staticmethod
    def _get_background_color(props: Dict[str, str]) -> Optional[str]:
        """Extract background color from CSS properties with dark mode support."""
        bg = props.get('background-color', '').strip() or props.get('background', '').strip()
        if bg:
            # Handle gradient - use first color
            if 'gradient' in bg.lower():
                # Extract first color from gradient
                color_match = re.search(r'#[\da-fA-F]{6}|rgb\([^)]+\)', bg)
                if color_match:
                    bg_color = color_match.group(0)
                    # In dark mode, adjust light backgrounds
                    if theme_manager.is_dark and HTMLRenderer._is_light_color(bg_color):
                        # Use a lighter surface color for cards in dark mode for better contrast
                        return HTMLRenderer._get_card_bg_color_dark()
                    return bg_color
                # For gradient, use a default color or primary color
                return theme_manager.primary_color
            # In dark mode, adjust light backgrounds
            if theme_manager.is_dark and HTMLRenderer._is_light_color(bg):
                # Use a lighter surface color for cards in dark mode for better contrast
                return HTMLRenderer._get_card_bg_color_dark()
            return bg
        return None
    
    @staticmethod
    def _get_card_bg_color_dark() -> str:
        """Get a card background color for dark mode with better contrast."""
        # Use a slightly lighter color than surface_color for better visibility
        # This creates contrast between card and dialog background
        from utils.constants import COLORS
        # Try to get a lighter shade, or use a fixed lighter color
        surface_dark = COLORS.get("surface_dark", "#1e293b")
        # Lighten the color slightly for cards
        # Convert hex to RGB, lighten, convert back
        try:
            if surface_dark.startswith('#'):
                hex_color = surface_dark[1:]
                if len(hex_color) == 6:
                    r = int(hex_color[0:2], 16)
                    g = int(hex_color[2:4], 16)
                    b = int(hex_color[4:6], 16)
                    # Lighten by 15-20%
                    r = min(255, int(r * 1.2))
                    g = min(255, int(g * 1.2))
                    b = min(255, int(b * 1.2))
                    return f"#{r:02x}{g:02x}{b:02x}"
        except (ValueError, IndexError):
            pass
        # Fallback to a fixed lighter color
        return "#2d3748"  # Lighter than typical dark surface
    
    @staticmethod
    def _is_light_color(color: str) -> bool:
        """Check if a color is light (needs dark text)."""
        if not color:
            return False
        
        # Remove whitespace and convert to lowercase
        color = color.strip().lower()
        
        # Check for common light colors
        light_colors = [
            '#fff', '#ffffff', 'white', 'rgb(255, 255, 255)',
            '#f5f5f5', '#f8f9fa', '#ffffff',
        ]
        
        if color in light_colors:
            return True
        
        # Check hex colors
        if color.startswith('#'):
            try:
                # Remove # and parse
                hex_color = color[1:]
                if len(hex_color) == 3:
                    hex_color = ''.join([c*2 for c in hex_color])
                if len(hex_color) == 6:
                    r = int(hex_color[0:2], 16)
                    g = int(hex_color[2:4], 16)
                    b = int(hex_color[4:6], 16)
                    # Calculate luminance
                    luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
                    # If luminance is greater than 0.7, it's a light color
                    return luminance > 0.7
            except (ValueError, IndexError):
                pass
        
        return False
    
    @staticmethod
    def _get_font_weight(props: Dict[str, str], default: ft.FontWeight) -> ft.FontWeight:
        """Extract font weight from CSS properties."""
        weight = props.get('font-weight', '').strip()
        if weight:
            weight_lower = weight.lower()
            if 'bold' in weight_lower or weight_lower in ['600', '700', '800', '900']:
                return ft.FontWeight.BOLD
        return default
    
    @staticmethod
    def _parse_padding(props: Dict[str, str]) -> Optional[ft.padding]:
        """Parse padding from CSS properties."""
        padding = props.get('padding', '').strip()
        if padding:
            # Handle different padding formats
            values = [v.strip() for v in padding.split()]
            if len(values) == 1:
                # All sides
                try:
                    px = int(float(values[0].replace('px', '')))
                    return ft.padding.all(px)
                except ValueError:
                    pass
            elif len(values) == 2:
                # Vertical, horizontal
                try:
                    v = int(float(values[0].replace('px', '')))
                    h = int(float(values[1].replace('px', '')))
                    return ft.padding.symmetric(vertical=v, horizontal=h)
                except ValueError:
                    pass
            elif len(values) == 4:
                # Top, right, bottom, left
                try:
                    top = int(float(values[0].replace('px', '')))
                    right = int(float(values[1].replace('px', '')))
                    bottom = int(float(values[2].replace('px', '')))
                    left = int(float(values[3].replace('px', '')))
                    return ft.padding.only(top=top, right=right, bottom=bottom, left=left)
                except ValueError:
                    pass
        
        # Check individual padding properties
        padding_top = props.get('padding-top', '').strip()
        padding_bottom = props.get('padding-bottom', '').strip()
        padding_left = props.get('padding-left', '').strip()
        padding_right = props.get('padding-right', '').strip()
        
        if any([padding_top, padding_bottom, padding_left, padding_right]):
            top = int(float(padding_top.replace('px', ''))) if padding_top else 0
            bottom = int(float(padding_bottom.replace('px', ''))) if padding_bottom else 0
            left = int(float(padding_left.replace('px', ''))) if padding_left else 0
            right = int(float(padding_right.replace('px', ''))) if padding_right else 0
            return ft.padding.only(top=top, right=right, bottom=bottom, left=left)
        
        return None
    
    @staticmethod
    def _parse_border_radius(props: Dict[str, str]) -> Optional[int]:
        """Parse border radius from CSS properties."""
        radius = props.get('border-radius', '').strip()
        if radius:
            try:
                return int(float(radius.replace('px', '')))
            except ValueError:
                pass
        return None
    
    @staticmethod
    def _parse_border(props: Dict[str, str]) -> Optional[ft.border]:
        """Parse border from CSS properties."""
        border_left = props.get('border-left', '').strip()
        if border_left:
            # Parse border-left: 4px solid #667eea
            parts = border_left.split()
            if len(parts) >= 3:
                try:
                    width = int(float(parts[0].replace('px', '')))
                    color = parts[-1] if parts[-1].startswith('#') else theme_manager.primary_color
                    return ft.border.only(left=ft.border.BorderSide(width, color))
                except (ValueError, IndexError):
                    pass
        
        # Check for other border properties
        border = props.get('border', '').strip()
        if border:
            parts = border.split()
            if len(parts) >= 3:
                try:
                    width = int(float(parts[0].replace('px', '')))
                    color = parts[-1] if parts[-1].startswith('#') else None
                    if color:
                        return ft.border.all(width, color)
                except (ValueError, IndexError):
                    pass
        
        return None
    
    @staticmethod
    def _get_margin_bottom(props: Dict[str, str], default: int) -> int:
        """Get margin-bottom value."""
        margin_bottom = props.get('margin-bottom', '').strip()
        if margin_bottom:
            try:
                return int(float(margin_bottom.replace('px', '')))
            except ValueError:
                pass
        
        margin = props.get('margin', '').strip()
        if margin:
            values = margin.split()
            if len(values) >= 2:
                try:
                    return int(float(values[2].replace('px', '')))
                except (ValueError, IndexError):
                    pass
        
        return default
    
    @staticmethod
    def _get_heading_size(tag_name: str) -> int:
        """Get default font size for heading tag."""
        size_map = {
            'h1': theme_manager.font_size_page_title,
            'h2': int(theme_manager.font_size_page_title * 0.85),
            'h3': int(theme_manager.font_size_page_title * 0.7),
            'h4': int(theme_manager.font_size_page_title * 0.6),
            'h5': int(theme_manager.font_size_page_title * 0.5),
            'h6': int(theme_manager.font_size_page_title * 0.45),
        }
        return size_map.get(tag_name, theme_manager.font_size_body)
    
    @staticmethod
    def _open_link(url: str) -> None:
        """Open a link in the default browser."""
        if not url:
            return
        
        try:
            # Handle relative URLs (e.g., #section, /path)
            if url.startswith('#'):
                # Anchor link - could scroll to section, but for now just log
                logger.debug(f"Anchor link clicked: {url}")
                return
            elif url.startswith('/'):
                # Relative path - could be handled by app, but for now just log
                logger.debug(f"Relative path clicked: {url}")
                return
            
            # Open external URLs in browser
            webbrowser.open(url)
            logger.info(f"Opened link: {url}")
        except Exception as e:
            logger.error(f"Failed to open link {url}: {e}", exc_info=True)
    
    @staticmethod
    def _handle_button_click(onclick_handler: str) -> None:
        """Handle button onclick attribute (JavaScript code)."""
        if not onclick_handler:
            return
        
        try:
            # For now, we can't execute JavaScript in Flet
            # But we can try to extract URLs from common patterns like:
            # - window.open('url')
            # - location.href = 'url'
            # - window.location = 'url'
            
            # Extract URL from window.open('url')
            open_match = re.search(r"window\.open\(['\"]([^'\"]+)['\"]", onclick_handler)
            if open_match:
                url = open_match.group(1)
                HTMLRenderer._open_link(url)
                return
            
            # Extract URL from location.href = 'url' or window.location = 'url'
            location_match = re.search(r"(?:location\.href|window\.location)\s*=\s*['\"]([^'\"]+)['\"]", onclick_handler)
            if location_match:
                url = location_match.group(1)
                HTMLRenderer._open_link(url)
                return
            
            # If no URL pattern found, just log it
            logger.debug(f"Button onclick handler (not supported): {onclick_handler}")
        except Exception as e:
            logger.error(f"Error handling button click: {e}", exc_info=True)
    
    @staticmethod
    def is_html(content: str) -> bool:
        """Check if content contains HTML tags."""
        if not content:
            return False
        return bool(HTML_TAG_PATTERN.search(content))
