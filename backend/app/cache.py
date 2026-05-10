from redis import Redis

from app.config import settings

_redis_client: Redis | None = None


def get_redis_client() -> Redis:
    """Return a shared Redis client for cache and session metadata."""
    global _redis_client
    if _redis_client is None:
        _redis_client = Redis.from_url(settings.REDIS_URL, decode_responses=True)
    return _redis_client
