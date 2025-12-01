"""
Query caching utilities for Hospital Dashboard

Provides in-memory caching for expensive database queries and KPI calculations
to improve dashboard performance.
"""

import logging
from typing import Any, Optional, Callable, Dict, Tuple
import hashlib
import json
import time
from functools import wraps
from collections import OrderedDict

logger = logging.getLogger(__name__)


class LRUCache:
    """
    Least Recently Used (LRU) Cache implementation

    Stores items in memory with automatic eviction of least recently used items
    when the cache reaches max_size.

    Attributes:
        max_size (int): Maximum number of items to store
        ttl (int): Time-to-live in seconds (None for no expiration)
    """

    def __init__(self, max_size: int = 1000, ttl: Optional[int] = None):
        """
        Initialize LRU Cache

        Args:
            max_size: Maximum number of items to cache
            ttl: Time-to-live in seconds (None for no expiration)
        """
        self.max_size = max_size
        self.ttl = ttl
        self.cache: OrderedDict = OrderedDict()
        self.timestamps: Dict[str, float] = {}
        self.hits = 0
        self.misses = 0

    def _is_expired(self, key: str) -> bool:
        """Check if cached item has expired"""
        if self.ttl is None:
            return False

        if key not in self.timestamps:
            return True

        age = time.time() - self.timestamps[key]
        return age > self.ttl

    def get(self, key: str) -> Optional[Any]:
        """
        Get item from cache

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found/expired
        """
        if key not in self.cache:
            self.misses += 1
            return None

        # Check expiration
        if self._is_expired(key):
            self.misses += 1
            del self.cache[key]
            del self.timestamps[key]
            return None

        # Move to end (mark as recently used)
        self.cache.move_to_end(key)
        self.hits += 1
        return self.cache[key]

    def set(self, key: str, value: Any) -> None:
        """
        Store item in cache

        Args:
            key: Cache key
            value: Value to cache
        """
        # Remove oldest item if at capacity
        if key not in self.cache and len(self.cache) >= self.max_size:
            oldest_key = next(iter(self.cache))
            del self.cache[oldest_key]
            del self.timestamps[oldest_key]
            logger.debug(f"Evicted oldest cache entry: {oldest_key}")

        # Add/update item
        self.cache[key] = value
        self.cache.move_to_end(key)
        self.timestamps[key] = time.time()

    def clear(self) -> None:
        """Clear all cached items"""
        self.cache.clear()
        self.timestamps.clear()
        self.hits = 0
        self.misses = 0
        logger.info("Cache cleared")

    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics

        Returns:
            Dict with cache stats (hits, misses, size, hit_rate)
        """
        total_requests = self.hits + self.misses
        hit_rate = self.hits / total_requests if total_requests > 0 else 0

        return {
            'hits': self.hits,
            'misses': self.misses,
            'size': len(self.cache),
            'max_size': self.max_size,
            'hit_rate': hit_rate,
            'ttl': self.ttl
        }

    def __len__(self) -> int:
        """Return current cache size"""
        return len(self.cache)


class QueryCache:
    """
    Query-specific cache for database queries and KPI calculations

    Uses LRU caching with intelligent key generation based on query parameters.
    """

    def __init__(self, max_size: int = 500, ttl: int = 3600):
        """
        Initialize Query Cache

        Args:
            max_size: Maximum number of queries to cache
            ttl: Time-to-live in seconds (default: 1 hour)
        """
        self.cache = LRUCache(max_size=max_size, ttl=ttl)

    def _make_key(self, *args, **kwargs) -> str:
        """
        Generate cache key from function arguments

        Args:
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            str: Hash key for cache lookup
        """
        # Convert args and kwargs to JSON-serializable format
        key_data = {
            'args': args,
            'kwargs': kwargs
        }

        # Create hash of serialized data
        key_json = json.dumps(key_data, sort_keys=True, default=str)
        key_hash = hashlib.md5(key_json.encode()).hexdigest()

        return key_hash

    def get(self, *args, **kwargs) -> Optional[Any]:
        """
        Get cached result for query with given parameters

        Args:
            *args: Query arguments
            **kwargs: Query keyword arguments

        Returns:
            Cached result or None
        """
        key = self._make_key(*args, **kwargs)
        result = self.cache.get(key)

        if result is not None:
            logger.debug(f"Cache HIT: {args[:2]}")  # Log first 2 args
        else:
            logger.debug(f"Cache MISS: {args[:2]}")

        return result

    def set(self, result: Any, *args, **kwargs) -> None:
        """
        Cache query result

        Args:
            result: Query result to cache
            *args: Query arguments
            **kwargs: Query keyword arguments
        """
        key = self._make_key(*args, **kwargs)
        self.cache.set(key, result)
        logger.debug(f"Cached result: {args[:2]}")

    def clear(self) -> None:
        """Clear all cached queries"""
        self.cache.clear()

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return self.cache.get_stats()


# Global cache instances
kpi_cache = QueryCache(max_size=500, ttl=3600)  # 1 hour TTL
benchmark_cache = QueryCache(max_size=500, ttl=3600)
financial_statement_cache = QueryCache(max_size=200, ttl=1800)  # 30 min TTL


def cached_query(cache: QueryCache = None, ttl: Optional[int] = None):
    """
    Decorator to cache function results

    Args:
        cache: QueryCache instance to use (creates new if None)
        ttl: Time-to-live override (seconds)

    Returns:
        Decorated function with caching

    Example:
        >>> @cached_query(cache=kpi_cache)
        >>> def get_kpis(ccn, year):
        >>>     # Expensive database query
        >>>     return results
    """
    if cache is None:
        cache = QueryCache(ttl=ttl or 3600)

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Try to get from cache
            cached_result = cache.get(*args, **kwargs)
            if cached_result is not None:
                return cached_result

            # Not in cache, execute function
            result = func(*args, **kwargs)

            # Cache the result
            cache.set(result, *args, **kwargs)

            return result

        # Add cache management methods to wrapped function
        wrapper.cache = cache
        wrapper.cache_clear = cache.clear
        wrapper.cache_stats = cache.get_stats

        return wrapper

    return decorator


def clear_all_caches():
    """Clear all global caches"""
    kpi_cache.clear()
    benchmark_cache.clear()
    financial_statement_cache.clear()
    logger.info("All caches cleared")


def get_all_cache_stats() -> Dict[str, Dict]:
    """
    Get statistics for all caches

    Returns:
        Dict mapping cache names to their stats
    """
    return {
        'kpi_cache': kpi_cache.get_stats(),
        'benchmark_cache': benchmark_cache.get_stats(),
        'financial_statement_cache': financial_statement_cache.get_stats()
    }
