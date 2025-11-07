"""
Base exporter abstract class.
"""

from abc import ABC, abstractmethod
from typing import List, Any
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class BaseExporter(ABC):
    """Abstract base class for all exporters."""
    
    @abstractmethod
    def export(self, data: Any, output_path: str, **kwargs) -> bool:
        """
        Export data to file.
        
        Args:
            data: Data to export
            output_path: Output file path
            **kwargs: Additional export options
            
        Returns:
            True if successful, False otherwise
        """
        pass
    
    def _validate_output_path(self, output_path: str) -> bool:
        """Validate output path exists and is writable."""
        try:
            path = Path(output_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            return True
        except Exception as e:
            logger.error(f"Invalid output path {output_path}: {e}")
            return False

