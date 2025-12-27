# Cache service for The Grey Tutor
# Uses Redis for persistent caching with in-memory fallback

from .redis_cache import init_redis, close_redis, LLMCache, QuizQuestionCache, get_redis_client

__all__ = ['init_redis', 'close_redis', 'LLMCache', 'QuizQuestionCache', 'get_redis_client']
