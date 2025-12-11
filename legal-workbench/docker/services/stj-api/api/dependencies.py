"""
Dependency injection for FastAPI.

Provides database connections, caching, and shared resources.
"""
from __future__ import annotations

import sys
import logging
from pathlib import Path
from typing import Generator, Optional
from functools import lru_cache
from datetime import datetime, timedelta

# Add backend path to sys.path to import existing modules
BACKEND_PATH = Path(__file__).parent.parent.parent.parent / "ferramentas/stj-dados-abertos"
sys.path.insert(0, str(BACKEND_PATH))

from src.database import STJDatabase
from config import DATABASE_PATH

logger = logging.getLogger(__name__)

# Global database instance (singleton pattern)
_db_instance: Optional[STJDatabase] = None


def get_database() -> Generator[STJDatabase, None, None]:
    """
    Dependency injection for database connection.

    Returns a connected STJDatabase instance that is automatically
    closed after the request completes.

    Yields:
        STJDatabase: Connected database instance
    """
    global _db_instance

    try:
        # Create singleton instance if not exists
        if _db_instance is None:
            logger.info("Initializing database connection")
            _db_instance = STJDatabase(db_path=DATABASE_PATH)
            _db_instance.connect()

        yield _db_instance

    except Exception as e:
        logger.error(f"Database error: {e}")
        raise


def close_database():
    """Close global database connection (called on shutdown)."""
    global _db_instance

    if _db_instance:
        logger.info("Closing database connection")
        _db_instance.close()
        _db_instance = None


# Simple in-memory cache for frequent queries
class QueryCache:
    """
    Simple in-memory cache for query results.

    Uses TTL (time-to-live) to expire cached entries.
    """

    def __init__(self, ttl_seconds: int = 300):
        """
        Initialize cache.

        Args:
            ttl_seconds: Time-to-live for cache entries (default: 5 minutes)
        """
        self._cache: dict[str, tuple[datetime, any]] = {}
        self._ttl = timedelta(seconds=ttl_seconds)

    def get(self, key: str) -> Optional[any]:
        """
        Get value from cache if not expired.

        Args:
            key: Cache key

        Returns:
            Cached value or None if expired/missing
        """
        if key in self._cache:
            timestamp, value = self._cache[key]
            if datetime.now() - timestamp < self._ttl:
                return value
            else:
                # Expired, remove from cache
                del self._cache[key]
        return None

    def set(self, key: str, value: any):
        """
        Set value in cache.

        Args:
            key: Cache key
            value: Value to cache
        """
        self._cache[key] = (datetime.now(), value)

    def clear(self):
        """Clear all cache entries."""
        self._cache.clear()

    def invalidate(self, pattern: Optional[str] = None):
        """
        Invalidate cache entries matching pattern.

        Args:
            pattern: String pattern to match (None = clear all)
        """
        if pattern is None:
            self.clear()
        else:
            keys_to_delete = [k for k in self._cache.keys() if pattern in k]
            for key in keys_to_delete:
                del self._cache[key]


# Global cache instance
_cache_instance = QueryCache(ttl_seconds=300)  # 5 minutes TTL


@lru_cache()
def get_cache() -> QueryCache:
    """
    Get global cache instance.

    Returns:
        QueryCache: Global cache instance
    """
    return _cache_instance


def invalidate_cache():
    """Invalidate all cache entries (called after sync operations)."""
    cache = get_cache()
    cache.clear()
    logger.info("Cache invalidated")
