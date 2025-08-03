import json
import logging
from typing import Dict, Any, List, Optional
from src.interfaces.memory_interface import MemoryInterface

logger = logging.getLogger(__name__)


class RedisMemoryProvider(MemoryInterface):
    """Redis-based memory provider for storing conversation history."""
    
    def __init__(self):
        self.redis_client = None
        self.prefix = "agentic_rag:"
        self.default_ttl = 3600
    
    async def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize the Redis provider with configuration."""
        try:
            import redis
            from redis import asyncio as redis_async
            
            self.redis_client = redis_async.Redis(
                host=config.get("host", "localhost"),
                port=config.get("port", 6379),
                db=config.get("db", 0),
                password=config.get("password"),
                decode_responses=True
            )
            self.prefix = config.get("prefix", "agentic_rag:")
            self.default_ttl = config.get("default_ttl", 3600)
            
            logger.info(f"Redis memory provider initialized with prefix: {self.prefix}")
            
        except ImportError:
            raise ImportError("redis is required for RedisMemoryProvider. Install with: pip install redis")
        except Exception as e:
            logger.error(f"Failed to initialize Redis provider: {e}")
            raise
    
    async def store(self, key: str, data: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        """Store data with an optional TTL (time to live in seconds)."""
        try:
            if not self.redis_client:
                raise RuntimeError("Redis provider not initialized")
            
            ttl = ttl or self.default_ttl
            json_data = json.dumps(data)
            redis_key = f"{self.prefix}{key}"
            
            result = await self.redis_client.setex(redis_key, ttl, json_data)
            logger.debug(f"Stored data in Redis with key: {redis_key}, TTL: {ttl}")
            
            return bool(result)
            
        except Exception as e:
            logger.error(f"Failed to store data in Redis: {e}")
            return False
    
    async def retrieve(self, key: str) -> List[Dict[str, Any]]:
        """Retrieve data by key."""
        try:
            if not self.redis_client:
                raise RuntimeError("Redis provider not initialized")
            
            redis_key = f"{self.prefix}{key}"
            json_data = await self.redis_client.get(redis_key)
            
            if json_data is None:
                logger.debug(f"No data found in Redis for key: {redis_key}")
                return []
            
            data = json.loads(json_data)
            logger.debug(f"Retrieved data from Redis with key: {redis_key}")
            
            return [data]
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode JSON data from Redis: {e}")
            return []
        except Exception as e:
            logger.error(f"Failed to retrieve data from Redis: {e}")
            return []
    
    async def clear(self, key: str) -> bool:
        """Clear data for a specific key."""
        try:
            if not self.redis_client:
                raise RuntimeError("Redis provider not initialized")
            
            redis_key = f"{self.prefix}{key}"
            result = await self.redis_client.delete(redis_key)
            
            logger.debug(f"Cleared data from Redis with key: {redis_key}")
            return bool(result)
            
        except Exception as e:
            logger.error(f"Failed to clear data from Redis: {e}")
            return False
    
    async def health_check(self) -> bool:
        """Check if the Redis provider is healthy."""
        try:
            if not self.redis_client:
                return False
            
            await self.redis_client.ping()
            return True
            
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            return False
    
    def get_provider_info(self) -> Dict[str, Any]:
        """Get information about the Redis memory provider."""
        return {
            "name": "redis",
            "type": "memory",
            "version": "1.0.0",
            "description": "Redis-based memory provider for conversation history",
            "features": ["TTL support", "JSON serialization", "Async operations"]
        } 