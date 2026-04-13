"""Redis caching layer with graceful degradation."""

from typing import Any

import structlog
from redis.asyncio import Redis

logger = structlog.get_logger()

_redis: Redis | None = None


async def init_redis() -> None:
    global _redis
    from src.config import get_settings

    settings = get_settings()
    if not settings.redis_url:
        logger.info("redis_disabled", reason="REDIS_URL not set")
        return
    try:
        _redis = Redis.from_url(settings.redis_url, decode_responses=True)
        await _redis.ping()  # type: ignore[misc]
        logger.info("redis_connected")
    except Exception:
        logger.warning("redis_connection_failed", exc_info=True)
        _redis = None


async def close_redis() -> None:
    global _redis
    if _redis:
        await _redis.aclose()
        _redis = None


def get_redis_client() -> Redis | None:
    return _redis


async def cache_get(key: str) -> str | None:
    if not _redis:
        return None
    try:
        result: str | None = await _redis.get(key)
        return result
    except Exception:
        logger.warning("cache_get_failed", key=key, exc_info=True)
        return None


async def cache_set(key: str, value: str, ttl: int = 300) -> None:
    if not _redis:
        return
    try:
        await _redis.set(key, value, ex=ttl)
    except Exception:
        logger.warning("cache_set_failed", key=key, exc_info=True)


async def cache_delete_pattern(pattern: str) -> None:
    if not _redis:
        return
    try:
        keys: Any = []
        async for key in _redis.scan_iter(match=pattern):
            keys.append(key)
        if keys:
            await _redis.delete(*keys)
    except Exception:
        logger.warning("cache_delete_failed", pattern=pattern, exc_info=True)
