import os
import redis

_client: redis.Redis | None = None

_PREFIX = "summary:article:"
_TTL = 30 * 24 * 60 * 60  # 30 days safety net; primary eviction is allkeys-lfu


def _get_client() -> redis.Redis:
    global _client
    if _client is None:
        url = os.getenv("REDIS_URL", "redis://localhost:6379")
        _client = redis.from_url(url, decode_responses=True)
    return _client


def get_cached_summary(article_id: int) -> str | None:
    try:
        return _get_client().get(f"{_PREFIX}{article_id}")
    except redis.RedisError:
        return None


def set_cached_summary(article_id: int, summary: str) -> None:
    try:
        _get_client().setex(f"{_PREFIX}{article_id}", _TTL, summary)
    except redis.RedisError:
        pass


def delete_cached_summary(article_id: int) -> bool:
    try:
        deleted = _get_client().delete(f"{_PREFIX}{article_id}")
        return deleted > 0
    except redis.RedisError:
        return False
