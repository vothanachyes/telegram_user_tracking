"""
Template loader utility for loading and processing HTML/Markdown templates.
"""

import logging
import re
from pathlib import Path
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class TemplateLoader:
    """Utility for loading and processing notification templates."""
    
    def __init__(self, templates_dir: Optional[Path] = None):
        """
        Initialize template loader.
        
        Args:
            templates_dir: Path to templates directory. If None, uses default admin/templates/html/
        """
        if templates_dir is None:
            # Get admin directory (parent of utils)
            admin_dir = Path(__file__).parent.parent
            self.templates_dir = admin_dir / "templates" / "html"
        else:
            self.templates_dir = Path(templates_dir)
        
        # Ensure templates directory exists
        self.templates_dir.mkdir(parents=True, exist_ok=True)
    
    def load_template(self, template_filename: str) -> str:
        """
        Load template file content.
        
        Args:
            template_filename: Name of template file (e.g., "new_user_greeting.html")
        
        Returns:
            Template content as string
        
        Raises:
            FileNotFoundError: If template file doesn't exist
            IOError: If file cannot be read
        """
        template_path = self.templates_dir / template_filename
        
        if not template_path.exists():
            raise FileNotFoundError(f"Template not found: {template_path}")
        
        try:
            with open(template_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            logger.debug(f"Loaded template: {template_filename}")
            return content
        
        except Exception as e:
            logger.error(f"Error loading template {template_filename}: {e}", exc_info=True)
            raise IOError(f"Failed to load template: {e}")
    
    def replace_variables(self, template_content: str, variables: Dict[str, str]) -> str:
        """
        Replace variables in template content.
        
        Variables use {{variable_name}} syntax.
        
        Args:
            template_content: Template content with variables
            variables: Dictionary of variable names to values
        
        Returns:
            Template content with variables replaced
        """
        if not template_content:
            return template_content
        
        result = template_content
        
        # Replace all variables in the format {{variable_name}}
        # Match {{variable_name}} but not nested braces
        pattern = r'\{\{(\w+)\}\}'
        
        def replace_var(match):
            var_name = match.group(1)
            if var_name in variables:
                value = variables[var_name]
                # Handle None values
                if value is None:
                    return ""
                return str(value)
            else:
                # Variable not found - leave as is
                logger.warning(f"Variable {var_name} not found in variables dict")
                return match.group(0)  # Return original {{variable_name}}
        
        result = re.sub(pattern, replace_var, result)
        
        return result
    
    def get_available_templates(self) -> List[str]:
        """
        Get list of available template files.
        
        Returns:
            List of template filenames (HTML and MD files)
        """
        templates = []
        
        if not self.templates_dir.exists():
            logger.warning(f"Templates directory does not exist: {self.templates_dir}")
            return templates
        
        try:
            # Get all .html and .md files
            for ext in ["*.html", "*.md"]:
                for template_file in self.templates_dir.glob(ext):
                    if template_file.is_file():
                        templates.append(template_file.name)
            
            # Sort alphabetically
            templates.sort()
            
            logger.debug(f"Found {len(templates)} templates in {self.templates_dir}")
            return templates
        
        except Exception as e:
            logger.error(f"Error getting available templates: {e}", exc_info=True)
            return []
    
    def load_and_replace(self, template_filename: str, variables: Dict[str, str]) -> str:
        """
        Load template and replace variables in one step.
        
        Args:
            template_filename: Name of template file
            variables: Dictionary of variable names to values
        
        Returns:
            Processed template content with variables replaced
        
        Raises:
            FileNotFoundError: If template file doesn't exist
            IOError: If file cannot be read
        """
        template_content = self.load_template(template_filename)
        return self.replace_variables(template_content, variables)


# Global template loader instance
template_loader = TemplateLoader()

