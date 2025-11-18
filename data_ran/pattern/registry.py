"""
Feature registry for managing enabled/disabled generators.
"""

from typing import Dict, Type, List, Optional
from data_ran.pattern.base import BaseGenerator


class FeatureRegistry:
    """Manages enabled/disabled features and generator mapping."""
    
    def __init__(self):
        """Initialize registry with empty mappings."""
        self._generators: Dict[str, Type[BaseGenerator]] = {}
        self._enabled_features: set = set()
        self._instances: Dict[str, BaseGenerator] = {}
    
    def register(self, feature_name: str, generator_class: Type[BaseGenerator]):
        """
        Register a generator class for a feature.
        
        Args:
            feature_name: Name of the feature (e.g., 'groups', 'users')
            generator_class: Generator class to register
        """
        self._generators[feature_name] = generator_class
    
    def enable_feature(self, feature_name: str):
        """Enable a feature for generation."""
        if feature_name in self._generators:
            self._enabled_features.add(feature_name)
    
    def disable_feature(self, feature_name: str):
        """Disable a feature from generation."""
        self._enabled_features.discard(feature_name)
    
    def is_enabled(self, feature_name: str) -> bool:
        """Check if a feature is enabled."""
        return feature_name in self._enabled_features
    
    def get_enabled_features(self) -> List[str]:
        """Get list of enabled feature names."""
        return list(self._enabled_features)
    
    def get_generator(self, feature_name: str) -> Optional[BaseGenerator]:
        """
        Get generator instance for a feature.
        
        Args:
            feature_name: Name of the feature
            
        Returns:
            Generator instance or None if not registered
        """
        if feature_name not in self._generators:
            return None
        
        if feature_name not in self._instances:
            self._instances[feature_name] = self._generators[feature_name]()
        
        return self._instances[feature_name]
    
    def get_generation_order(self) -> List[str]:
        """
        Get ordered list of features to generate based on dependencies.
        
        Returns:
            List of feature names in generation order
        """
        enabled = self.get_enabled_features()
        if not enabled:
            return []
        
        # Build dependency graph
        dependencies: Dict[str, List[str]] = {}
        for feature in enabled:
            generator = self.get_generator(feature)
            if generator:
                deps = generator.get_dependencies()
                dependencies[feature] = [d for d in deps if d in enabled]
        
        # Topological sort
        result = []
        visited = set()
        temp_visited = set()
        
        def visit(feature: str):
            if feature in temp_visited:
                # Circular dependency - ignore for now
                return
            if feature in visited:
                return
            
            temp_visited.add(feature)
            for dep in dependencies.get(feature, []):
                visit(dep)
            temp_visited.remove(feature)
            visited.add(feature)
            result.append(feature)
        
        for feature in enabled:
            if feature not in visited:
                visit(feature)
        
        return result
    
    def clear_instances(self):
        """Clear all generator instances (useful for testing)."""
        self._instances.clear()

