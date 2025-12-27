"""
Redis Cache Service for The Grey Tutor

Provides caching for LLM responses to reduce API costs and improve response times.
"""

import hashlib
import json
import logging
import os
from typing import Optional, Any

logger = logging.getLogger(__name__)

# Redis client - lazy initialized
_redis_client = None

def get_redis_client():
    """Get or create Redis client connection."""
    global _redis_client
    if _redis_client is None:
        try:
            import redis
            redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
            _redis_client = redis.from_url(redis_url, decode_responses=True)
            # Test connection
            _redis_client.ping()
            logger.info(f"Connected to Redis at {redis_url}")
        except ImportError:
            logger.warning("Redis package not installed. Using in-memory cache fallback.")
            _redis_client = InMemoryCache()
        except Exception as e:
            logger.warning(f"Failed to connect to Redis: {e}. Using in-memory cache fallback.")
            _redis_client = InMemoryCache()
    return _redis_client


class InMemoryCache:
    """Fallback in-memory cache when Redis is not available."""
    
    def __init__(self):
        self._cache = {}
        logger.info("Using in-memory cache (Redis fallback)")
    
    def get(self, key: str) -> Optional[str]:
        return self._cache.get(key)
    
    def set(self, key: str, value: str, ex: int = None) -> bool:
        self._cache[key] = value
        return True
    
    def delete(self, key: str) -> int:
        if key in self._cache:
            del self._cache[key]
            return 1
        return 0
    
    def ping(self) -> bool:
        return True
    
    def keys(self, pattern: str = "*") -> list:
        import fnmatch
        return [k for k in self._cache.keys() if fnmatch.fnmatch(k, pattern)]
    
    def flushdb(self) -> bool:
        self._cache.clear()
        return True


def normalize_query(text: str) -> str:
    """
    Normalize a query for better cache hit rates.
    
    - Lowercase
    - Strip leading/trailing whitespace
    - Remove punctuation
    - Collapse multiple spaces to single space
    """
    import re
    # Lowercase and strip
    text = text.lower().strip()
    # Remove punctuation (keep alphanumeric and spaces)
    text = re.sub(r'[^\w\s]', '', text)
    # Collapse multiple spaces
    text = re.sub(r'\s+', ' ', text)
    return text


def generate_cache_key(prefix: str, content: str, normalize: bool = False) -> str:
    """Generate a cache key from content using MD5 hash."""
    if normalize:
        content = normalize_query(content)
    content_hash = hashlib.md5(content.encode()).hexdigest()
    return f"{prefix}:{content_hash}"


class LLMCache:
    """
    Cache for LLM responses.
    
    Caches based on full prompt (context + question) with light normalization.
    This ensures different questions get different cache entries even if they
    contain similar keywords.
    """
    
    PREFIX = "llm"
    DEFAULT_TTL = 60 * 60 * 24 * 7  # 7 days
    
    @classmethod
    def get(cls, prompt: str) -> Optional[str]:
        """Get cached LLM response for a prompt."""
        try:
            client = get_redis_client()
            # Use full prompt with light normalization (case + whitespace only)
            key = generate_cache_key(cls.PREFIX, prompt, normalize=True)
            cached = client.get(key)
            if cached:
                logger.info(f"[CACHE HIT] LLM response found in cache")
                return cached
            logger.debug(f"[CACHE MISS] No cached LLM response")
            return None
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            return None
    
    @classmethod
    def set(cls, prompt: str, response: str, ttl: int = None) -> bool:
        """Cache an LLM response."""
        try:
            client = get_redis_client()
            key = generate_cache_key(cls.PREFIX, prompt, normalize=True)
            ttl = ttl or cls.DEFAULT_TTL
            client.set(key, response, ex=ttl)
            logger.info(f"[CACHE SET] LLM response cached (TTL: {ttl}s)")
            return True
        except Exception as e:
            logger.error(f"Cache set error: {e}")
            return False
    
    @classmethod
    def invalidate(cls, prompt: str) -> bool:
        """Invalidate a specific cached response."""
        try:
            client = get_redis_client()
            key = generate_cache_key(cls.PREFIX, prompt, normalize=True)
            return client.delete(key) > 0
        except Exception as e:
            logger.error(f"Cache invalidate error: {e}")
            return False
    
    @classmethod
    def get_stats(cls) -> dict:
        """Get cache statistics."""
        try:
            client = get_redis_client()
            keys = client.keys(f"{cls.PREFIX}:*")
            return {
                "cached_responses": len(keys),
                "prefix": cls.PREFIX
            }
        except Exception as e:
            logger.error(f"Cache stats error: {e}")
            return {"error": str(e)}


class QuizQuestionCache:
    """
    Cache for quiz questions.
    
    Caches questions by entity/topic to avoid regenerating
    the same questions repeatedly.
    """
    
    PREFIX = "quiz"
    DEFAULT_TTL = 60 * 60 * 24 * 3  # 3 days (shorter TTL for variety)
    
    @classmethod
    def get_stats(cls) -> dict:
        """Get cache statistics."""
        try:
            client = get_redis_client()
            keys = client.keys(f"{cls.PREFIX}:*")
            return {
                "cached_questions": len(keys),
                "prefix": cls.PREFIX
            }
        except Exception as e:
            logger.error(f"Quiz cache stats error: {e}")
            return {"error": str(e)}
    
    @classmethod
    def get(cls, entity: str, question_type: str, difficulty: int) -> Optional[dict]:
        """Get cached quiz question."""
        try:
            client = get_redis_client()
            content = f"{entity}:{question_type}:{difficulty}"
            key = generate_cache_key(cls.PREFIX, content)
            cached = client.get(key)
            if cached:
                logger.info(f"[CACHE HIT] Quiz question found for {entity}")
                return json.loads(cached)
            return None
        except Exception as e:
            logger.error(f"Quiz cache get error: {e}")
            return None
    
    @classmethod
    def set(cls, entity: str, question_type: str, difficulty: int, question: dict, ttl: int = None) -> bool:
        """Cache a quiz question."""
        try:
            client = get_redis_client()
            content = f"{entity}:{question_type}:{difficulty}"
            key = generate_cache_key(cls.PREFIX, content)
            ttl = ttl or cls.DEFAULT_TTL
            client.set(key, json.dumps(question), ex=ttl)
            logger.info(f"[CACHE SET] Quiz question cached for {entity}")
            return True
        except Exception as e:
            logger.error(f"Quiz cache set error: {e}")
            return False


async def init_redis():
    """Initialize Redis connection on startup."""
    get_redis_client()


async def close_redis():
    """Close Redis connection on shutdown."""
    global _redis_client
    if _redis_client and hasattr(_redis_client, 'close'):
        _redis_client.close()
    _redis_client = None
