"""
Caching Layer for Khronos Research System

Provides multi-tier caching:
- In-memory cache (always available)
- Redis cache (optional, for distributed systems)
- Automatic cache invalidation
- Configurable TTLs (time-to-live)

Supports:
- Query result caching
- Metric calculation caching
- Peer analysis caching
- API response caching
"""

import json
import hashlib
from abc import ABC, abstractmethod
from typing import Any, Optional, Callable, TypeVar
from datetime import datetime, timedelta
from functools import wraps
import logging

logger = logging.getLogger(__name__)

T = TypeVar('T')

# Default cache TTLs (in seconds)
DEFAULT_TTL = 3600  # 1 hour
METRIC_TTL = 86400  # 24 hours
PEER_ANALYSIS_TTL = 86400  # 24 hours
QUERY_TTL = 1800  # 30 minutes


class CacheBackend(ABC):
    """Abstract base class for cache backends."""

    @abstractmethod
    def get(self, key: str) -> Optional[Any]:
        """Retrieve value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found
        """
        pass

    @abstractmethod
    def set(self, key: str, value: Any, ttl: int) -> None:
        """Store value in cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds
        """
        pass

    @abstractmethod
    def delete(self, key: str) -> None:
        """Delete value from cache.

        Args:
            key: Cache key
        """
        pass

    @abstractmethod
    def clear_pattern(self, pattern: str) -> None:
        """Delete all keys matching pattern.

        Args:
            pattern: Pattern (e.g., 'metric:*')
        """
        pass

    @abstractmethod
    def flush(self) -> None:
        """Clear entire cache."""
        pass


class InMemoryCache(CacheBackend):
    """Simple in-memory cache using dict with TTL support."""

    def __init__(self):
        """Initialize in-memory cache."""
        self._cache: dict[str, tuple[Any, datetime]] = {}

    def get(self, key: str) -> Optional[Any]:
        """Retrieve value from in-memory cache."""
        if key not in self._cache:
            return None

        value, expiry = self._cache[key]
        if datetime.now() > expiry:
            del self._cache[key]
            return None

        return value

    def set(self, key: str, value: Any, ttl: int) -> None:
        """Store value in in-memory cache."""
        expiry = datetime.now() + timedelta(seconds=ttl)
        self._cache[key] = (value, expiry)

    def delete(self, key: str) -> None:
        """Delete value from in-memory cache."""
        if key in self._cache:
            del self._cache[key]

    def clear_pattern(self, pattern: str) -> None:
        """Delete all keys matching pattern."""
        keys_to_delete = [k for k in self._cache.keys() if self._match_pattern(k, pattern)]
        for key in keys_to_delete:
            del self._cache[key]

    def flush(self) -> None:
        """Clear entire in-memory cache."""
        self._cache.clear()

    @staticmethod
    def _match_pattern(key: str, pattern: str) -> bool:
        """Check if key matches pattern (simple glob-style matching)."""
        if pattern == "*":
            return True
        if pattern.endswith("*"):
            return key.startswith(pattern[:-1])
        return key == pattern

    def get_stats(self) -> dict[str, Any]:
        """Get cache statistics."""
        return {
            "size": len(self._cache),
            "memory_estimate": sum(
                len(str(v[0])) for v in self._cache.values()
            )
        }


class RedisCache(CacheBackend):
    """Redis-based distributed cache."""

    def __init__(self, host: str = "localhost", port: int = 6379, db: int = 0):
        """Initialize Redis cache.

        Args:
            host: Redis host
            port: Redis port
            db: Redis database number
        """
        try:
            import redis
            self.redis = redis.Redis(host=host, port=port, db=db, decode_responses=True)
            self.redis.ping()
            logger.info("Connected to Redis cache")
        except Exception as e:
            logger.warning(f"Failed to connect to Redis: {e}. Falling back to in-memory cache.")
            self.redis = None

    def get(self, key: str) -> Optional[Any]:
        """Retrieve value from Redis cache."""
        if not self.redis:
            return None

        try:
            value = self.redis.get(key)
            if value:
                return json.loads(value)
        except Exception as e:
            logger.warning(f"Redis get error for {key}: {e}")

        return None

    def set(self, key: str, value: Any, ttl: int) -> None:
        """Store value in Redis cache."""
        if not self.redis:
            return

        try:
            self.redis.setex(key, ttl, json.dumps(value, default=str))
        except Exception as e:
            logger.warning(f"Redis set error for {key}: {e}")

    def delete(self, key: str) -> None:
        """Delete value from Redis cache."""
        if not self.redis:
            return

        try:
            self.redis.delete(key)
        except Exception as e:
            logger.warning(f"Redis delete error for {key}: {e}")

    def clear_pattern(self, pattern: str) -> None:
        """Delete all keys matching pattern."""
        if not self.redis:
            return

        try:
            keys = self.redis.keys(pattern)
            if keys:
                self.redis.delete(*keys)
        except Exception as e:
            logger.warning(f"Redis pattern delete error: {e}")

    def flush(self) -> None:
        """Clear entire Redis cache."""
        if not self.redis:
            return

        try:
            self.redis.flushdb()
        except Exception as e:
            logger.warning(f"Redis flush error: {e}")


class HybridCache(CacheBackend):
    """Hybrid cache: uses Redis if available, falls back to in-memory."""

    def __init__(self, redis_config: Optional[dict[str, Any]] = None):
        """Initialize hybrid cache.

        Args:
            redis_config: Redis configuration dict (host, port, db)
        """
        self.memory_cache = InMemoryCache()

        if redis_config:
            self.redis_cache: Optional[CacheBackend] = RedisCache(**redis_config)
        else:
            self.redis_cache = None

    def get(self, key: str) -> Optional[Any]:
        """Retrieve value from cache."""
        # Try Redis first
        if self.redis_cache:
            value = self.redis_cache.get(key)
            if value is not None:
                return value

        # Fall back to memory
        return self.memory_cache.get(key)

    def set(self, key: str, value: Any, ttl: int) -> None:
        """Store value in cache."""
        # Store in memory
        self.memory_cache.set(key, value, ttl)

        # Store in Redis if available
        if self.redis_cache:
            self.redis_cache.set(key, value, ttl)

    def delete(self, key: str) -> None:
        """Delete value from cache."""
        self.memory_cache.delete(key)
        if self.redis_cache:
            self.redis_cache.delete(key)

    def clear_pattern(self, pattern: str) -> None:
        """Delete all keys matching pattern."""
        self.memory_cache.clear_pattern(pattern)
        if self.redis_cache:
            self.redis_cache.clear_pattern(pattern)

    def flush(self) -> None:
        """Clear entire cache."""
        self.memory_cache.flush()
        if self.redis_cache:
            self.redis_cache.flush()


# Global cache instance
_cache: Optional[CacheBackend] = None


def get_cache(use_redis: bool = False, redis_config: Optional[dict[str, Any]] = None) -> CacheBackend:
    """Get or create global cache instance.

    Args:
        use_redis: Enable Redis caching
        redis_config: Redis configuration

    Returns:
        CacheBackend instance
    """
    global _cache
    if _cache is None:
        if use_redis:
            _cache = HybridCache(redis_config)
        else:
            _cache = InMemoryCache()
    return _cache


def reset_cache() -> None:
    """Reset global cache instance (useful for testing)."""
    global _cache
    _cache = None


def cached(
    ttl: int = DEFAULT_TTL,
    key_prefix: str = "",
) -> Callable:
    """Decorator for caching function results.

    Args:
        ttl: Time-to-live in seconds
        key_prefix: Prefix for cache keys

    Example:
        @cached(ttl=3600, key_prefix="metrics")
        def calculate_metrics(ticker: str) -> dict:
            return {...}
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            cache = get_cache()

            # Generate cache key
            key_parts = [key_prefix or func.__name__]
            key_parts.extend(str(arg) for arg in args if arg is not None)
            key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()) if v is not None)
            cache_key = ":".join(key_parts)

            # Try to get from cache
            cached_value = cache.get(cache_key)
            if cached_value is not None:
                logger.debug(f"Cache hit: {cache_key}")
                return cached_value

            # Compute value
            logger.debug(f"Cache miss: {cache_key}")
            result = func(*args, **kwargs)

            # Store in cache
            cache.set(cache_key, result, ttl)

            return result

        return wrapper

    return decorator


def cache_key(*parts: str) -> str:
    """Generate a cache key from parts.

    Args:
        parts: Key components

    Returns:
        Cache key (e.g., "metrics:FFC:2026")

    Example:
        key = cache_key("metrics", "FFC", "2026")
        # Returns: "metrics:FFC:2026"
    """
    return ":".join(str(p) for p in parts if p)


def invalidate_cache(pattern: str) -> None:
    """Invalidate cache entries matching pattern.

    Args:
        pattern: Pattern to match (e.g., "metrics:*")

    Example:
        invalidate_cache("metrics:FFC:*")  # Invalidate all FFC metrics
        invalidate_cache("peer:*")  # Invalidate all peer analysis
    """
    cache = get_cache()
    cache.clear_pattern(pattern)
    logger.info(f"Invalidated cache pattern: {pattern}")
