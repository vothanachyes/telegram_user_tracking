"""
AI-powered content generator for Khmer and English names, messages, and data.
"""

import json
import random
from pathlib import Path
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class AIContentGenerator:
    """Generates realistic Khmer and English content."""
    
    def __init__(self, use_ai: bool = False, ai_api_key: Optional[str] = None):
        """
        Initialize AI content generator.
        
        Args:
            use_ai: Whether to use AI API (if available)
            ai_api_key: API key for AI service (optional)
        """
        self.use_ai = use_ai
        self.ai_api_key = ai_api_key
        
        # Load content data from JSON file
        self._load_content_data()
    
    def _load_content_data(self) -> None:
        """Load content data from JSON file."""
        try:
            # Get the directory where this script is located
            script_dir = Path(__file__).parent
            json_path = script_dir / "content_data.json"
            
            if not json_path.exists():
                logger.error(f"Content data file not found: {json_path}")
                raise FileNotFoundError(f"Content data file not found: {json_path}")
            
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            # Extract data into class attributes for easy access
            khmer_data = data.get("khmer", {})
            english_data = data.get("english", {})
            
            self.KHMER_FIRST_NAMES = khmer_data.get("first_names", [])
            self.KHMER_LAST_NAMES = khmer_data.get("last_names", [])
            self.KHMER_MESSAGE_TEMPLATES = khmer_data.get("message_templates", [])
            self.KHMER_GROUP_NAMES = khmer_data.get("group_names", [])
            self.KHMER_HASHTAGS = khmer_data.get("hashtags", [])
            
            self.ENGLISH_FIRST_NAMES = english_data.get("first_names", [])
            self.ENGLISH_LAST_NAMES = english_data.get("last_names", [])
            self.ENGLISH_MESSAGE_TEMPLATES = english_data.get("message_templates", [])
            self.ENGLISH_GROUP_NAMES = english_data.get("group_names", [])
            self.ENGLISH_HASHTAGS = english_data.get("hashtags", [])
            
            logger.debug("Content data loaded successfully from JSON")
            
        except Exception as e:
            logger.error(f"Failed to load content data: {e}")
            # Fallback to empty lists to prevent crashes
            self.KHMER_FIRST_NAMES = []
            self.KHMER_LAST_NAMES = []
            self.KHMER_MESSAGE_TEMPLATES = []
            self.KHMER_GROUP_NAMES = []
            self.KHMER_HASHTAGS = []
            self.ENGLISH_FIRST_NAMES = []
            self.ENGLISH_LAST_NAMES = []
            self.ENGLISH_MESSAGE_TEMPLATES = []
            self.ENGLISH_GROUP_NAMES = []
            self.ENGLISH_HASHTAGS = []
            raise
    
    def generate_khmer_name(self) -> Dict[str, str]:
        """
        Generate a realistic Khmer name.
        
        Returns:
            Dictionary with first_name, last_name, full_name, username
        """
        first_name = random.choice(self.KHMER_FIRST_NAMES)
        last_name = random.choice(self.KHMER_LAST_NAMES)
        full_name = f"{first_name} {last_name}"
        username = f"{first_name.lower()}_{last_name.lower()}_{random.randint(100, 999)}"
        
        return {
            "first_name": first_name,
            "last_name": last_name,
            "full_name": full_name,
            "username": username
        }
    
    def generate_english_name(self) -> Dict[str, str]:
        """
        Generate a realistic English name.
        
        Returns:
            Dictionary with first_name, last_name, full_name, username
        """
        first_name = random.choice(self.ENGLISH_FIRST_NAMES)
        last_name = random.choice(self.ENGLISH_LAST_NAMES)
        full_name = f"{first_name} {last_name}"
        username = f"{first_name.lower()}_{last_name.lower()}{random.randint(10, 99)}"
        
        return {
            "first_name": first_name,
            "last_name": last_name,
            "full_name": full_name,
            "username": username
        }
    
    def generate_message(
        self, 
        language: str, 
        context: Optional[str] = None,
        include_tags: bool = True,
        tag_count: int = 0
    ) -> str:
        """
        Generate a realistic message in specified language.
        
        Args:
            language: 'khmer', 'english', or 'mixed'
            context: Optional context for message
            include_tags: Whether to include hashtags
            tag_count: Number of tags to include
            
        Returns:
            Generated message string
        """
        if language == "khmer":
            template = random.choice(self.KHMER_MESSAGE_TEMPLATES)
        elif language == "english":
            template = random.choice(self.ENGLISH_MESSAGE_TEMPLATES)
        else:  # mixed
            khmer_part = random.choice(self.KHMER_MESSAGE_TEMPLATES)
            english_part = random.choice(self.ENGLISH_MESSAGE_TEMPLATES)
            template = f"{khmer_part} {english_part}"
        
        message = template
        
        if include_tags and tag_count > 0:
            tags = []
            if language == "khmer":
                tags = random.sample(self.KHMER_HASHTAGS, min(tag_count, len(self.KHMER_HASHTAGS)))
            elif language == "english":
                tags = random.sample(self.ENGLISH_HASHTAGS, min(tag_count, len(self.ENGLISH_HASHTAGS)))
            else:  # mixed
                khmer_tags = random.sample(self.KHMER_HASHTAGS, min(tag_count // 2 + 1, len(self.KHMER_HASHTAGS)))
                english_tags = random.sample(self.ENGLISH_HASHTAGS, min(tag_count - len(khmer_tags), len(self.ENGLISH_HASHTAGS)))
                tags = khmer_tags + english_tags
            
            tag_string = " ".join([f"#{tag}" for tag in tags[:tag_count]])
            message = f"{message} {tag_string}"
        
        return message
    
    def generate_group_name(self, language: str) -> str:
        """
        Generate a realistic group name.
        
        Args:
            language: 'khmer', 'english', or 'mixed'
            
        Returns:
            Group name string
        """
        if language == "khmer":
            return random.choice(self.KHMER_GROUP_NAMES)
        elif language == "english":
            return random.choice(self.ENGLISH_GROUP_NAMES)
        else:  # mixed
            khmer_name = random.choice(self.KHMER_GROUP_NAMES)
            english_name = random.choice(self.ENGLISH_GROUP_NAMES)
            return f"{khmer_name} / {english_name}"
    
    def generate_tags(self, message: str, count: int, language: str) -> List[str]:
        """
        Generate relevant tags based on message content.
        
        Args:
            message: Message content
            count: Number of tags to generate
            language: 'khmer', 'english', or 'mixed'
            
        Returns:
            List of tag strings (without # prefix)
        """
        if language == "khmer":
            tags = random.sample(self.KHMER_HASHTAGS, min(count, len(self.KHMER_HASHTAGS)))
        elif language == "english":
            tags = random.sample(self.ENGLISH_HASHTAGS, min(count, len(self.ENGLISH_HASHTAGS)))
        else:  # mixed
            khmer_count = count // 2
            english_count = count - khmer_count
            khmer_tags = random.sample(self.KHMER_HASHTAGS, min(khmer_count, len(self.KHMER_HASHTAGS)))
            english_tags = random.sample(self.ENGLISH_HASHTAGS, min(english_count, len(self.ENGLISH_HASHTAGS)))
            tags = khmer_tags + english_tags
        
        return tags[:count]

