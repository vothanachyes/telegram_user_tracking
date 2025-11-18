"""
Tag extraction utility for extracting hashtags from message content.
"""

import re
from typing import List, Set


class TagExtractor:
    """Extracts and normalizes tags from text content."""
    
    # Regex pattern: # followed by word characters (alphanumeric, underscore) or Unicode characters
    # Supports Unicode characters (e.g., Chinese, Japanese, etc.)
    TAG_PATTERN = re.compile(r'#[\w\u4e00-\u9fff]+')
    
    @staticmethod
    def extract_tags(text: str) -> List[str]:
        """
        Extract tags from text content.
        
        Args:
            text: Text content to extract tags from
            
        Returns:
            List of normalized tags (without # prefix, lowercase)
        """
        if not text:
            return []
        
        # Find all tag matches
        matches = TagExtractor.TAG_PATTERN.findall(text)
        
        # Normalize tags: remove # prefix, convert to lowercase, strip whitespace
        normalized_tags: Set[str] = set()
        for match in matches:
            # Remove # prefix and normalize
            tag = match[1:].strip().lower()
            if tag:  # Only add non-empty tags
                normalized_tags.add(tag)
        
        return sorted(list(normalized_tags))
    
    @staticmethod
    def extract_tags_from_content_and_caption(content: str = None, caption: str = None) -> List[str]:
        """
        Extract tags from both content and caption fields.
        
        Args:
            content: Message content text
            caption: Message caption text
            
        Returns:
            List of unique normalized tags
        """
        tags: Set[str] = set()
        
        if content:
            tags.update(TagExtractor.extract_tags(content))
        
        if caption:
            tags.update(TagExtractor.extract_tags(caption))
        
        return sorted(list(tags))

