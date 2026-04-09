import redis.asyncio as redis
import json
from typing import Optional, Any
from datetime import timedelta

from app.config import settings
from app.core.logger import logger


class RedisClient:
    """Redis client wrapper for caching and session management"""

    def __init__(self):
        self.client: Optional[redis.Redis] = None
        self._initialized = False

    async def initialize(self):
        """Initialize Redis connection"""
        try:
            self.client = await redis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True
            )
            await self.client.ping()
            self._initialized = True
            logger.info("Redis client initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Redis: {e}")
            raise

    async def close(self):
        """Close Redis connection"""
        if self.client:
            await self.client.close()
            logger.info("Redis connection closed")

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if not self._initialized:
            return None
        value = await self.client.get(key)
        if value:
            try:
                return json.loads(value)
            except:
                return value
        return None

    async def set(self, key: str, value: Any, ttl: int = None):
        """Set value in cache"""
        if not self._initialized:
            return
        if isinstance(value, (dict, list)):
            value = json.dumps(value)
        if ttl:
            await self.client.setex(key, ttl, value)
        else:
            await self.client.set(key, value)

    async def delete(self, key: str):
        """Delete key from cache"""
        if self._initialized:
            await self.client.delete(key)

    async def exists(self, key: str) -> bool:
        """Check if key exists"""
        if not self._initialized:
            return False
        return await self.client.exists(key) > 0

    async def increment(self, key: str, amount: int = 1) -> int:
        """Increment counter"""
        if not self._initialized:
            return 0
        return await self.client.incr(key, amount)

    async def expire(self, key: str, ttl: int):
        """Set expiration on key"""
        if self._initialized:
            await self.client.expire(key, ttl)

    async def ping(self) -> bool:
        """Check Redis connectivity"""
        if not self._initialized:
            return False
        try:
            return await self.client.ping()
        except:
            return False


redis_client = RedisClient()