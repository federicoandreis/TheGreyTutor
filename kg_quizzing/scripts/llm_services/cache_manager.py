"""
Cache Manager Module for LLM Services.

This module provides caching functionality for LLM services to reduce API calls
and improve performance.
"""
import os
import json
import logging
from typing import Dict, Any, Optional

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class CacheManager:
    """Manager for caching LLM service results."""
    
    def __init__(self, cache_dir: str, cache_file: str):
        """
        Initialize the cache manager.
        
        Args:
            cache_dir: Directory to store the cache
            cache_file: Name of the cache file
        """
        self.cache_dir = cache_dir
        self.cache_file = cache_file
        self.cache_path = os.path.join(cache_dir, cache_file)
        self.cache = self._load_cache()
        
        # Create the cache directory if it doesn't exist
        os.makedirs(cache_dir, exist_ok=True)
        
        logger.info(f"Initialized cache manager with cache file {self.cache_path}")
    
    def _load_cache(self) -> Dict[str, Any]:
        """
        Load the cache from disk.
        
        Returns:
            Dictionary containing the cache
        """
        if os.path.exists(self.cache_path):
            try:
                with open(self.cache_path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to load cache: {e}")
        
        return {}
    
    def _save_cache(self):
        """Save the cache to disk."""
        try:
            with open(self.cache_path, 'w') as f:
                json.dump(self.cache, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save cache: {e}")
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get a value from the cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value if found, None otherwise
        """
        return self.cache.get(key)
    
    def set(self, key: str, value: Any):
        """
        Set a value in the cache.
        
        Args:
            key: Cache key
            value: Value to cache
        """
        self.cache[key] = value
        self._save_cache()
    
    def has(self, key: str) -> bool:
        """
        Check if a key exists in the cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if the key exists, False otherwise
        """
        return key in self.cache
    
    def clear(self):
        """Clear the cache."""
        self.cache = {}
        self._save_cache()
    
    def size(self) -> int:
        """
        Get the size of the cache.
        
        Returns:
            Number of items in the cache
        """
        return len(self.cache)


# Create cache managers for different services
def create_question_cache():
    """
    Create a cache manager for question generation.
    
    Returns:
        CacheManager instance for question generation
    """
    return CacheManager("question_cache", "question_cache.json")


def create_assessment_cache():
    """
    Create a cache manager for answer assessment.
    
    Returns:
        CacheManager instance for answer assessment
    """
    return CacheManager("assessment_cache", "assessment_cache.json")
