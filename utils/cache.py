"""
Efficient caching utility for Max Assistant API.

This module provides various caching mechanisms to improve performance
by storing and retrieving expensive operation results.

Features:
- Memory-based cache with TTL (Time To Live)
- Optional disk-based cache for persistent storage
- Optional Redis-based cache for distributed environments
- Decorators for easy function/method caching
- Async support for use with FastAPI endpoints
- Cache invalidation and management tools
"""

import asyncio
import functools
import hashlib
import inspect
import json
import os
import pickle
import time
from concurrent.futures import ThreadPoolExecutor
from enum import Enum
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, TypeVar, Union, cast

# Optional Redis support
try:
    import redis
    from redis.asyncio import Redis as AsyncRedis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

# Type definitions
T = TypeVar('T')
CacheKey = str
CacheValue = Any
CacheResult = Tuple[bool, Any]  # (hit, value)


class CacheType(str, Enum):
    """Supported cache storage types"""
    MEMORY = "memory"  # Simple in-memory dictionary
    DISK = "disk"      # Filesystem-based persistent cache
    REDIS = "redis"    # Redis-based distributed cache


class Cache:
    """
    Flexible caching system with multiple backend options.

    This class provides a unified interface for different cache backends
    with features like TTL, serialization, and async support.
    """

    def __init__(
        self,
        cache_type: Union[str, CacheType] = CacheType.MEMORY,
        ttl: int = 3600,
        max_size: int = 1000,
        cache_dir: str = "data/cache",
        redis_url: Optional[str] = None,
        redis_prefix: str = "max_assistant:",
        serializer: Optional[Callable[[Any], bytes]] = None,
        deserializer: Optional[Callable[[bytes], Any]] = None,
    ):
        """
        Initialize the cache with the specified backend.

        Args:
            cache_type: The type of cache to use (memory, disk, or redis)
            ttl: Default time-to-live in seconds for cached items
            max_size: Maximum number of items in memory cache
            cache_dir: Directory to store disk cache files
            redis_url: Redis connection URL for redis cache
            redis_prefix: Prefix for redis keys
            serializer: Custom serialization function (default: pickle)
            deserializer: Custom deserialization function (default: pickle)
        """
        self.cache_type = CacheType(cache_type) if isinstance(cache_type, str) else cache_type
        self.ttl = ttl
        self.max_size = max_size
        self.cache_dir = Path(cache_dir)
        self.redis_url = redis_url
        self.redis_prefix = redis_prefix

        # Use custom or default serializers
        self.serializer = serializer or pickle.dumps
        self.deserializer = deserializer or pickle.loads

        # Memory cache storage
        self._memory_cache: Dict[str, Tuple[Any, float]] = {}
        self._access_times: Dict[str, float] = {}

        # Redis client (initialized lazily)
        self._redis_client = None
        self._async_redis_client = None

        # Thread pool for async disk operations
        self._executor = ThreadPoolExecutor(max_workers=2)

        # Initialize the selected cache backend
        self._initialize_cache()

    def _initialize_cache(self) -> None:
        """Initialize the selected cache backend."""
        if self.cache_type == CacheType.DISK:
            self.cache_dir.mkdir(parents=True, exist_ok=True)

        elif self.cache_type == CacheType.REDIS:
            if not REDIS_AVAILABLE:
                raise ImportError(
                    "Redis cache requires redis package. "
                    "Install with 'pip install redis'."
                )

            if not self.redis_url:
                raise ValueError("Redis URL is required for Redis cache")

    def _get_redis_client(self):
        """Get or create a Redis client instance."""
        if self._redis_client is None:
            self._redis_client = redis.Redis.from_url(
                self.redis_url, decode_responses=False
            )
        return self._redis_client

    async def _get_async_redis_client(self):
        """Get or create an asynchronous Redis client instance."""
        if self._async_redis_client is None:
            self._async_redis_client = AsyncRedis.from_url(
                self.redis_url, decode_responses=False
            )
        return self._async_redis_client

    def _make_key(self, key: Union[str, bytes, Any]) -> str:
        """
        Create a standardized cache key from various input types.

        For complex objects, uses their JSON representation to create a hash.
        """
        if isinstance(key, str):
            raw_key = key
        elif isinstance(key, bytes):
            raw_key = key.decode('utf-8')
        else:
            # For complex objects, convert to JSON for consistent keys
            try:
                raw_key = json.dumps(key, sort_keys=True)
            except (TypeError, ValueError):
                # Fallback for non-JSON-serializable objects
                raw_key = str(key)

        # Create hash for possibly long keys
        if len(raw_key) > 64:
            return hashlib.md5(raw_key.encode('utf-8')).hexdigest()
        return raw_key

    def _get_disk_path(self, key: str) -> Path:
        """Get the file path for a disk cache key."""
        # Use the first two chars as a sharding directory to avoid too many files in one dir
        shard = key[:2] if len(key) >= 2 else "00"
        shard_dir = self.cache_dir / shard
        shard_dir.mkdir(exist_ok=True)
        return shard_dir / key

    def _cleanup_if_needed(self) -> None:
        """Cleanup the memory cache if it exceeds the maximum size."""
        if len(self._memory_cache) <= self.max_size:
            return

        # Remove least recently used items
        now = time.time()
        expired_keys = [
            k for k, t in self._memory_cache.items()
            if t[1] < now
        ]

        # First remove any expired items
        for key in expired_keys:
            del self._memory_cache[key]
            self._access_times.pop(key, None)

        # If still too large, remove oldest accessed items
        if len(self._memory_cache) > self.max_size:
            # Sort by access time, oldest first
            oldest_keys = sorted(
                self._access_times.items(),
                key=lambda x: x[1]
            )[:len(self._memory_cache) - self.max_size]

            for key, _ in oldest_keys:
                del self._memory_cache[key]
                del self._access_times[key]

    def get(self, key: Union[str, Any], default: Any = None) -> Any:
        """
        Get a value from the cache.

        Args:
            key: The cache key
            default: Value to return if key not found

        Returns:
            The cached value or default if not found
        """
        hit, value = self.get_with_status(key)
        return value if hit else default

    def get_with_status(self, key: Union[str, Any]) -> CacheResult:
        """
        Get a value from the cache with hit/miss status.

        Args:
            key: The cache key

        Returns:
            Tuple of (hit, value) where hit is a boolean indicating cache hit
        """
        cache_key = self._make_key(key)
        now = time.time()

        if self.cache_type == CacheType.MEMORY:
            if cache_key in self._memory_cache:
                value, expires_at = self._memory_cache[cache_key]
                if expires_at > now:
                    # Update access time
                    self._access_times[cache_key] = now
                    return True, value
                # Expired, remove it
                del self._memory_cache[cache_key]
                self._access_times.pop(cache_key, None)
            return False, None

        elif self.cache_type == CacheType.DISK:
            file_path = self._get_disk_path(cache_key)
            if file_path.exists():
                try:
                    with open(file_path, 'rb') as f:
                        expires_at, value_bytes = pickle.load(f)
                        if expires_at > now:
                            value = self.deserializer(value_bytes)
                            return True, value
                        # Expired, remove the file
                        os.unlink(file_path)
                except (OSError, pickle.PickleError):
                    # Handle corrupted cache files
                    try:
                        os.unlink(file_path)
                    except OSError:
                        pass
            return False, None

        elif self.cache_type == CacheType.REDIS:
            redis_key = f"{self.redis_prefix}{cache_key}"
            try:
                client = self._get_redis_client()
                value_bytes = client.get(redis_key)
                if value_bytes:
                    value = self.deserializer(value_bytes)
                    return True, value
            except Exception:
                pass
            return False, None

        return False, None

    def set(self, key: Union[str, Any], value: Any, ttl: Optional[int] = None) -> None:
        """
        Set a value in the cache.

        Args:
            key: The cache key
            value: The value to cache
            ttl: Optional TTL override in seconds
        """
        cache_key = self._make_key(key)
        expires_at = time.time() + (ttl if ttl is not None else self.ttl)

        if self.cache_type == CacheType.MEMORY:
            self._memory_cache[cache_key] = (value, expires_at)
            self._access_times[cache_key] = time.time()
            self._cleanup_if_needed()

        elif self.cache_type == CacheType.DISK:
            try:
                file_path = self._get_disk_path(cache_key)
                value_bytes = self.serializer(value)
                with open(file_path, 'wb') as f:
                    pickle.dump((expires_at, value_bytes), f)
            except (OSError, pickle.PickleError):
                # Silently fail on serialization/write errors
                pass

        elif self.cache_type == CacheType.REDIS:
            redis_key = f"{self.redis_prefix}{cache_key}"
            try:
                client = self._get_redis_client()
                value_bytes = self.serializer(value)
                client.setex(
                    redis_key,
                    int(expires_at - time.time()),
                    value_bytes
                )
            except Exception:
                # Silently fail on Redis errors
                pass

    def delete(self, key: Union[str, Any]) -> bool:
        """
        Delete a key from the cache.

        Args:
            key: The cache key

        Returns:
            True if the key was deleted, False otherwise
        """
        cache_key = self._make_key(key)

        if self.cache_type == CacheType.MEMORY:
            if cache_key in self._memory_cache:
                del self._memory_cache[cache_key]
                self._access_times.pop(cache_key, None)
                return True

        elif self.cache_type == CacheType.DISK:
            file_path = self._get_disk_path(cache_key)
            if file_path.exists():
                try:
                    os.unlink(file_path)
                    return True
                except OSError:
                    pass

        elif self.cache_type == CacheType.REDIS:
            redis_key = f"{self.redis_prefix}{cache_key}"
            try:
                client = self._get_redis_client()
                return client.delete(redis_key) > 0
            except Exception:
                pass

        return False

    def clear(self) -> None:
        """Clear all items from the cache."""
        if self.cache_type == CacheType.MEMORY:
            self._memory_cache.clear()
            self._access_times.clear()

        elif self.cache_type == CacheType.DISK:
            try:
                for path in self.cache_dir.glob('**/*'):
                    if path.is_file():
                        os.unlink(path)
            except OSError:
                pass

        elif self.cache_type == CacheType.REDIS:
            try:
                client = self._get_redis_client()
                keys = client.keys(f"{self.redis_prefix}*")
                if keys:
                    client.delete(*keys)
            except Exception:
                pass

    async def aget(self, key: Union[str, Any], default: Any = None) -> Any:
        """
        Asynchronously get a value from the cache.

        Args:
            key: The cache key
            default: Value to return if key not found

        Returns:
            The cached value or default if not found
        """
        hit, value = await self.aget_with_status(key)
        return value if hit else default

    async def aget_with_status(self, key: Union[str, Any]) -> CacheResult:
        """
        Asynchronously get a value from the cache with hit/miss status.

        Args:
            key: The cache key

        Returns:
            Tuple of (hit, value) where hit is a boolean indicating cache hit
        """
        cache_key = self._make_key(key)
        now = time.time()

        if self.cache_type == CacheType.MEMORY:
            if cache_key in self._memory_cache:
                value, expires_at = self._memory_cache[cache_key]
                if expires_at > now:
                    # Update access time
                    self._access_times[cache_key] = now
                    return True, value
                # Expired, remove it
                del self._memory_cache[cache_key]
                self._access_times.pop(cache_key, None)
            return False, None

        elif self.cache_type == CacheType.DISK:
            # Run disk operations in a thread pool
            def _disk_get():
                file_path = self._get_disk_path(cache_key)
                if file_path.exists():
                    try:
                        with open(file_path, 'rb') as f:
                            expires_at, value_bytes = pickle.load(f)
                            if expires_at > now:
                                value = self.deserializer(value_bytes)
                                return True, value
                            # Expired, remove the file
                            os.unlink(file_path)
                    except (OSError, pickle.PickleError):
                        # Handle corrupted cache files
                        try:
                            os.unlink(file_path)
                        except OSError:
                            pass
                return False, None

            return await asyncio.get_event_loop().run_in_executor(
                self._executor, _disk_get
            )

        elif self.cache_type == CacheType.REDIS:
            redis_key = f"{self.redis_prefix}{cache_key}"
            try:
                client = await self._get_async_redis_client()
                value_bytes = await client.get(redis_key)
                if value_bytes:
                    # Run deserializer in a thread if it might be CPU-intensive
                    value = await asyncio.get_event_loop().run_in_executor(
                        self._executor,
                        self.deserializer,
                        value_bytes
                    )
                    return True, value
            except Exception:
                pass
            return False, None

        return False, None

    async def aset(self, key: Union[str, Any], value: Any, ttl: Optional[int] = None) -> None:
        """
        Asynchronously set a value in the cache.

        Args:
            key: The cache key
            value: The value to cache
            ttl: Optional TTL override in seconds
        """
        cache_key = self._make_key(key)
        expires_at = time.time() + (ttl if ttl is not None else self.ttl)

        if self.cache_type == CacheType.MEMORY:
            self._memory_cache[cache_key] = (value, expires_at)
            self._access_times[cache_key] = time.time()
            self._cleanup_if_needed()

        elif self.cache_type == CacheType.DISK:
            # Serialize and write in a thread
            def _disk_set():
                try:
                    file_path = self._get_disk_path(cache_key)
                    value_bytes = self.serializer(value)
                    with open(file_path, 'wb') as f:
                        pickle.dump((expires_at, value_bytes), f)
                except (OSError, pickle.PickleError):
                    # Silently fail on serialization/write errors
                    pass

            await asyncio.get_event_loop().run_in_executor(
                self._executor, _disk_set
            )

        elif self.cache_type == CacheType.REDIS:
            redis_key = f"{self.redis_prefix}{cache_key}"
            try:
                # Serialize in a thread if it might be CPU-intensive
                value_bytes = await asyncio.get_event_loop().run_in_executor(
                    self._executor, self.serializer, value
                )

                client = await self._get_async_redis_client()
                await client.setex(
                    redis_key,
                    int(expires_at - time.time()),
                    value_bytes
                )
            except Exception:
                # Silently fail on Redis errors
                pass

    async def adelete(self, key: Union[str, Any]) -> bool:
        """
        Asynchronously delete a key from the cache.

        Args:
            key: The cache key

        Returns:
            True if the key was deleted, False otherwise
        """
        cache_key = self._make_key(key)

        if self.cache_type == CacheType.MEMORY:
            if cache_key in self._memory_cache:
                del self._memory_cache[cache_key]
                self._access_times.pop(cache_key, None)
                return True

        elif self.cache_type == CacheType.DISK:
            def _disk_delete():
                file_path = self._get_disk_path(cache_key)
                if file_path.exists():
                    try:
                        os.unlink(file_path)
                        return True
                    except OSError:
                        pass
                return False

            return await asyncio.get_event_loop().run_in_executor(
                self._executor, _disk_delete
            )

        elif self.cache_type == CacheType.REDIS:
            redis_key = f"{self.redis_prefix}{cache_key}"
            try:
                client = await self._get_async_redis_client()
                return await client.delete(redis_key) > 0
            except Exception:
                pass

        return False

    async def aclear(self) -> None:
        """Asynchronously clear all items from the cache."""
        if self.cache_type == CacheType.MEMORY:
            self._memory_cache.clear()
            self._access_times.clear()

        elif self.cache_type == CacheType.DISK:
            def _disk_clear():
                try:
                    for path in self.cache_dir.glob('**/*'):
                        if path.is_file():
                            os.unlink(path)
                except OSError:
                    pass

            await asyncio.get_event_loop().run_in_executor(
                self._executor, _disk_clear
            )

        elif self.cache_type == CacheType.REDIS:
            try:
                client = await self._get_async_redis_client()
                keys = await client.keys(f"{self.redis_prefix}*")
                if keys:
                    await client.delete(*keys)
            except Exception:
                pass


def cached(
    ttl: int = 3600,
    key_builder: Optional[Callable[..., Any]] = None,
    cache_instance: Optional[Cache] = None
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Decorator for caching function results.

    Args:
        ttl: Time-to-live in seconds
        key_builder: Optional function to build custom cache keys
        cache_instance: Optional custom cache instance

    Returns:
        Decorated function with caching
    """
    cache = cache_instance or Cache(ttl=ttl)

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            # Build the cache key
            if key_builder:
                key = key_builder(*args, **kwargs)
            else:
                # Default key is function name + args + kwargs
                key = {
                    'func': func.__module__ + '.' + func.__qualname__,
                    'args': args,
                    'kwargs': {k: v for k, v in kwargs.items() if isinstance(v, (str, int, float, bool, type(None)))}
                }

            # Try to get from cache
            hit, result = cache.get_with_status(key)
            if hit:
                return cast(T, result)

            # Not in cache, call the function
            result = func(*args, **kwargs)

            # Cache the result
            cache.set(key, result, ttl)

            return result

        return wrapper

    return decorator


def async_cached(
    ttl: int = 3600,
    key_builder: Optional[Callable[..., Any]] = None,
    cache_instance: Optional[Cache] = None
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Decorator for caching async function results.

    Args:
        ttl: Time-to-live in seconds
        key_builder: Optional function to build custom cache keys
        cache_instance: Optional custom cache instance

    Returns:
        Decorated async function with caching
    """
    cache = cache_instance or Cache(ttl=ttl)

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            # Build the cache key
            if key_builder:
                key = key_builder(*args, **kwargs)
            else:
                # Default key is function name + args + kwargs
                key = {
                    'func': func.__module__ + '.' + func.__qualname__,
                    'args': args,
                    'kwargs': {k: v for k, v in kwargs.items() if isinstance(v, (str, int, float, bool, type(None)))}
                }

            # Try to get from cache
            hit, result = await cache.aget_with_status(key)
            if hit:
                return cast(T, result)

            # Not in cache, call the function
            result = await func(*args, **kwargs)

            # Cache the result
            await cache.aset(key, result, ttl)

            return result

        return wrapper

    return decorator


# Global default cache instance
default_cache = Cache()


# Example usage:
if __name__ == "__main__":
    # Simple synchronous usage
    cache = Cache(cache_type=CacheType.MEMORY, ttl=60)
    cache.set("key1", "value1")
    print(cache.get("key1"))  # value1

    # Using the decorator
    @cached(ttl=60)
    def expensive_function(x, y):
        print(f"Computing {x} + {y}")
        return x + y

    print(expensive_function(1, 2))  # Computes and returns 3
    print(expensive_function(1, 2))  # Returns 3 from cache

    # Async example
    async def async_example():
        @async_cached(ttl=60)
        async def async_expensive_function(x, y):
            print(f"Async computing {x} + {y}")
            await asyncio.sleep(1)  # Simulate expensive operation
            return x + y

        print(await async_expensive_function(3, 4))  # Computes and returns 7
        print(await async_expensive_function(3, 4))  # Returns 7 from cache

    # Run the async example
    asyncio.run(async_example())
