"""
Cache manager for GraphRAG retrieval.

This module provides caching functionality for the GraphRAG system.
"""

import os
import time
import json
import hashlib
import logging
import functools
from typing import Dict, List, Any, Optional, Union, Callable, TypeVar, cast
from pathlib import Path

from .config import get_config

# Set up logging
logger = logging.getLogger(__name__)

# Type variables for generic functions
T = TypeVar('T')
R = TypeVar('R')


class CacheItem:
    """
    Cache item with TTL (time-to-live) support.
    """
    
    def __init__(self, value: Any, ttl: int = 3600):
        """
        Initialize a cache item.
        
        Args:
            value: The value to cache
            ttl: Time-to-live in seconds (default: 1 hour)
        """
        self.value = value
        self.created_at = time.time()
        self.ttl = ttl
    
    def is_expired(self) -> bool:
        """
        Check if the cache item has expired.
        
        Returns:
            True if the cache item has expired, False otherwise
        """
        return time.time() > self.created_at + self.ttl


class MemoryCache:
    """
    In-memory cache with TTL support.
    """
    
    def __init__(self, max_size: int = 1000, ttl: int = 3600):
        """
        Initialize the memory cache.
        
        Args:
            max_size: Maximum number of items in the cache
            ttl: Default time-to-live in seconds
        """
        self.cache: Dict[str, CacheItem] = {}
        self.max_size = max_size
        self.ttl = ttl
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get a value from the cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found or expired
        """
        if key not in self.cache:
            return None
        
        item = self.cache[key]
        
        if item.is_expired():
            # Remove expired item
            del self.cache[key]
            return None
        
        return item.value
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        Set a value in the cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds (default: use instance default)
        """
        # Check if cache is full
        if len(self.cache) >= self.max_size:
            # Remove oldest item
            oldest_key = min(self.cache.keys(), key=lambda k: self.cache[k].created_at)
            del self.cache[oldest_key]
        
        # Set new item
        self.cache[key] = CacheItem(value, ttl or self.ttl)
    
    def delete(self, key: str) -> None:
        """
        Delete a value from the cache.
        
        Args:
            key: Cache key
        """
        if key in self.cache:
            del self.cache[key]
    
    def clear(self) -> None:
        """Clear the cache."""
        self.cache.clear()


class DiskCache:
    """
    Disk-based cache with TTL support.
    """
    
    def __init__(self, directory: str = "./cache", ttl: int = 3600):
        """
        Initialize the disk cache.
        
        Args:
            directory: Directory for cache files
            ttl: Default time-to-live in seconds
        """
        self.directory = Path(directory)
        self.ttl = ttl
        
        # Create cache directory if it doesn't exist
        self.directory.mkdir(parents=True, exist_ok=True)
    
    def _get_cache_path(self, key: str) -> Path:
        """
        Get the path to a cache file.
        
        Args:
            key: Cache key
            
        Returns:
            Path to the cache file
        """
        # Use MD5 hash of key as filename
        filename = hashlib.md5(key.encode()).hexdigest() + ".json"
        return self.directory / filename
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get a value from the cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found or expired
        """
        cache_path = self._get_cache_path(key)
        
        if not cache_path.exists():
            return None
        
        try:
            with open(cache_path, "r") as f:
                cache_data = json.load(f)
            
            created_at = cache_data.get("created_at", 0)
            ttl = cache_data.get("ttl", self.ttl)
            
            # Check if expired
            if time.time() > created_at + ttl:
                # Remove expired file
                cache_path.unlink(missing_ok=True)
                return None
            
            return cache_data.get("value")
        except Exception as e:
            logger.error(f"Failed to read cache file {cache_path}: {str(e)}")
            return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        Set a value in the cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds (default: use instance default)
        """
        cache_path = self._get_cache_path(key)
        
        try:
            cache_data = {
                "key": key,
                "value": value,
                "created_at": time.time(),
                "ttl": ttl or self.ttl
            }
            
            with open(cache_path, "w") as f:
                json.dump(cache_data, f)
        except Exception as e:
            logger.error(f"Failed to write cache file {cache_path}: {str(e)}")
    
    def delete(self, key: str) -> None:
        """
        Delete a value from the cache.
        
        Args:
            key: Cache key
        """
        cache_path = self._get_cache_path(key)
        cache_path.unlink(missing_ok=True)
    
    def clear(self) -> None:
        """Clear the cache."""
        for cache_file in self.directory.glob("*.json"):
            cache_file.unlink(missing_ok=True)


class CacheManager:
    """
    Cache manager that combines memory and disk caches.
    """
    
    def __init__(self, memory_cache: Optional[MemoryCache] = None,
                disk_cache: Optional[DiskCache] = None):
        """
        Initialize the cache manager.
        
        Args:
            memory_cache: Memory cache instance
            disk_cache: Disk cache instance
        """
        config = get_config().cache
        
        self.enabled = config.enabled
        self.memory_cache = memory_cache or MemoryCache(
            max_size=config.max_size,
            ttl=config.ttl
        )
        self.disk_cache = disk_cache or DiskCache(
            directory=config.directory,
            ttl=config.ttl
        )
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get a value from the cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found or expired
        """
        if not self.enabled:
            return None
        
        # Try memory cache first
        value = self.memory_cache.get(key)
        
        if value is not None:
            return value
        
        # Try disk cache
        value = self.disk_cache.get(key)
        
        if value is not None:
            # Store in memory cache for faster access next time
            self.memory_cache.set(key, value)
            return value
        
        return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        Set a value in the cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds
        """
        if not self.enabled:
            return
        
        # Set in both memory and disk caches
        self.memory_cache.set(key, value, ttl)
        self.disk_cache.set(key, value, ttl)
    
    def delete(self, key: str) -> None:
        """
        Delete a value from the cache.
        
        Args:
            key: Cache key
        """
        if not self.enabled:
            return
        
        # Delete from both memory and disk caches
        self.memory_cache.delete(key)
        self.disk_cache.delete(key)
    
    def clear(self) -> None:
        """Clear the cache."""
        if not self.enabled:
            return
        
        # Clear both memory and disk caches
        self.memory_cache.clear()
        self.disk_cache.clear()


# Global cache manager instance
_cache_manager: Optional[CacheManager] = None


def get_cache_manager() -> CacheManager:
    """
    Get the global cache manager instance.
    
    Returns:
        CacheManager instance
    """
    global _cache_manager
    
    if _cache_manager is None:
        _cache_manager = CacheManager()
    
    return _cache_manager


def set_cache_manager(cache_manager: CacheManager) -> None:
    """
    Set the global cache manager instance.
    
    Args:
        cache_manager: CacheManager instance
    """
    global _cache_manager
    _cache_manager = cache_manager


def cached(ttl: Optional[int] = None):
    """
    Decorator for caching function results.
    
    Args:
        ttl: Time-to-live in seconds
        
    Returns:
        Decorated function
    """
    def decorator(func: Callable[..., R]) -> Callable[..., R]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> R:
            # Get cache manager
            cache_manager = get_cache_manager()
            
            if not cache_manager.enabled:
                # Caching is disabled, just call the function
                return func(*args, **kwargs)
            
            # Create cache key
            # Include function name, args, and kwargs in the key
            key_parts = [func.__module__, func.__name__]
            
            # Add args
            for arg in args:
                try:
                    # Try to convert to JSON string
                    key_parts.append(json.dumps(arg, sort_keys=True))
                except (TypeError, ValueError):
                    # If not JSON serializable, use string representation
                    key_parts.append(str(arg))
            
            # Add kwargs
            for k, v in sorted(kwargs.items()):
                key_parts.append(k)
                try:
                    # Try to convert to JSON string
                    key_parts.append(json.dumps(v, sort_keys=True))
                except (TypeError, ValueError):
                    # If not JSON serializable, use string representation
                    key_parts.append(str(v))
            
            # Create cache key
            cache_key = ":".join(key_parts)
            
            # Try to get from cache
            cached_value = cache_manager.get(cache_key)
            
            if cached_value is not None:
                logger.debug(f"Cache hit for {func.__name__}")
                return cast(R, cached_value)
            
            # Call the function
            logger.debug(f"Cache miss for {func.__name__}")
            result = func(*args, **kwargs)
            
            # Cache the result
            cache_manager.set(cache_key, result, ttl)
            
            return result
        
        return wrapper
    
    return decorator
