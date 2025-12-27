"""
Cache management endpoints for The Grey Tutor.

Provides endpoints to view cache statistics and manage the LLM response cache.
"""

from fastapi import APIRouter

router = APIRouter()


@router.get("/stats")
async def get_cache_stats():
    """Get cache statistics including number of cached responses."""
    try:
        from ...services.redis_cache import LLMCache, QuizQuestionCache, get_redis_client
        
        # Test Redis connection
        client = get_redis_client()
        redis_connected = True
        try:
            client.ping()
        except:
            redis_connected = False
        
        return {
            "status": "ok",
            "redis_connected": redis_connected,
            "llm_cache": LLMCache.get_stats(),
            "quiz_cache": QuizQuestionCache.get_stats() if hasattr(QuizQuestionCache, 'get_stats') else {}
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "redis_connected": False
        }


@router.delete("/clear")
async def clear_cache():
    """Clear all cached LLM responses."""
    try:
        from ...services.redis_cache import get_redis_client
        
        client = get_redis_client()
        # Only clear LLM and quiz caches, not other data
        llm_keys = client.keys("llm:*")
        quiz_keys = client.keys("quiz:*")
        
        deleted = 0
        for key in llm_keys + quiz_keys:
            client.delete(key)
            deleted += 1
        
        return {
            "status": "ok",
            "deleted_keys": deleted
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }
