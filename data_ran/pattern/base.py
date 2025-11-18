"""
Base generator abstract class for Strategy pattern.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any


class BaseGenerator(ABC):
    """Abstract base class for all data generators."""
    
    @abstractmethod
    def generate(self, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Generate data based on configuration.
        
        Args:
            config: Configuration dictionary with generation parameters
            
        Returns:
            List of generated data dictionaries
        """
        pass
    
    @abstractmethod
    def get_dependencies(self) -> List[str]:
        """
        Return list of required feature names that must be generated first.
        
        Returns:
            List of feature names (e.g., ['groups', 'users'])
        """
        pass
    
    def get_feature_name(self) -> str:
        """
        Return the feature name for this generator.
        
        Returns:
            Feature name string
        """
        return self.__class__.__name__.replace('Generator', '').lower()

