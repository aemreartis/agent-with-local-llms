import json
import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from src.interfaces.memory_interface import MemoryInterface

logger = logging.getLogger(__name__)


class HybridMemoryProvider(MemoryInterface):
    """
    Hybrid memory provider that combines Redis (short-term) and PostgreSQL (long-term).
    
    Strategy:
    - Redis: Fast access for active conversations (TTL-based)
    - PostgreSQL: Persistent storage for completed conversations
    - Automatic migration: Move from Redis to PostgreSQL when TTL expires
    """
    
    def __init__(self):
        self.redis_provider = None
        self.postgresql_provider = None
        self.redis_ttl = 3600  # 1 hour default
        self.migration_enabled = True
        self.migration_batch_size = 100
    
    async def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize both Redis and PostgreSQL providers."""
        try:
            # Import provider classes
            from src.providers.memory.redis_provider import RedisMemoryProvider
            from src.providers.memory.postgresql_provider import PostgreSQLMemoryProvider
            
            # Initialize Redis provider
            self.redis_provider = RedisMemoryProvider()
            redis_config = config.get("redis", {})
            await self.redis_provider.initialize(redis_config)
            
            # Initialize PostgreSQL provider
            self.postgresql_provider = PostgreSQLMemoryProvider()
            postgresql_config = config.get("postgresql", {})
            await self.postgresql_provider.initialize(postgresql_config)
            
            # Configure hybrid settings
            self.redis_ttl = config.get("redis_ttl", 3600)
            self.migration_enabled = config.get("migration_enabled", True)
            self.migration_batch_size = config.get("migration_batch_size", 100)
            
            logger.info(f"Hybrid memory provider initialized - Redis TTL: {self.redis_ttl}s, Migration: {self.migration_enabled}")
            
        except Exception as e:
            logger.error(f"Failed to initialize hybrid memory provider: {e}")
            raise
    
    async def store(self, key: str, data: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        """
        Store data in Redis (short-term) with automatic migration to PostgreSQL.
        
        Strategy:
        1. Store in Redis with TTL for fast access
        2. If migration enabled, also store in PostgreSQL for persistence
        3. Redis serves as cache, PostgreSQL as backup
        """
        try:
            # Add metadata for tracking
            data_with_metadata = {
                **data,
                "_hybrid_metadata": {
                    "stored_at": datetime.now().isoformat(),
                    "redis_ttl": ttl or self.redis_ttl,
                    "migrated_to_postgresql": False
                }
            }
            
            # Store in Redis (primary for active conversations)
            redis_success = await self.redis_provider.store(
                key, data_with_metadata, ttl or self.redis_ttl
            )
            
            # Store in PostgreSQL (backup for persistence)
            postgresql_success = await self.postgresql_provider.store(
                key, data_with_metadata
            )
            
            if redis_success:
                logger.debug(f"Stored data in Redis with key: {key}, TTL: {ttl or self.redis_ttl}")
            
            if postgresql_success:
                logger.debug(f"Stored data in PostgreSQL with key: {key}")
            
            # Return success if either storage worked
            return redis_success or postgresql_success
            
        except Exception as e:
            logger.error(f"Failed to store data in hybrid provider: {e}")
            return False
    
    async def retrieve(self, key: str) -> List[Dict[str, Any]]:
        """
        Retrieve data with fallback strategy.
        
        Strategy:
        1. Try Redis first (fastest)
        2. If not found in Redis, try PostgreSQL
        3. If found in PostgreSQL, optionally restore to Redis
        """
        try:
            # Try Redis first (fast access)
            redis_data = await self.redis_provider.retrieve(key)
            
            if redis_data:
                logger.debug(f"Retrieved data from Redis with key: {key}")
                return redis_data
            
            # Fallback to PostgreSQL
            postgresql_data = await self.postgresql_provider.retrieve(key)
            
            if postgresql_data:
                logger.debug(f"Retrieved data from PostgreSQL with key: {key}")
                
                # Optionally restore to Redis for faster future access
                if self.migration_enabled:
                    await self._restore_to_redis(key, postgresql_data)
                
                return postgresql_data
            
            logger.debug(f"No data found in either Redis or PostgreSQL for key: {key}")
            return []
            
        except Exception as e:
            logger.error(f"Failed to retrieve data from hybrid provider: {e}")
            return []
    
    async def _restore_to_redis(self, key: str, data: List[Dict[str, Any]]) -> None:
        """Restore data from PostgreSQL to Redis for faster access."""
        try:
            for item in data:
                # Remove migration metadata if present
                if "_hybrid_metadata" in item:
                    item["_hybrid_metadata"]["migrated_to_postgresql"] = True
                
                await self.redis_provider.store(key, item, self.redis_ttl)
            
            logger.debug(f"Restored data to Redis from PostgreSQL for key: {key}")
            
        except Exception as e:
            logger.warning(f"Failed to restore data to Redis: {e}")
    
    async def clear(self, key: str) -> bool:
        """Clear data from both Redis and PostgreSQL."""
        try:
            redis_success = await self.redis_provider.clear(key)
            postgresql_success = await self.postgresql_provider.clear(key)
            
            logger.debug(f"Cleared data from Redis: {redis_success}, PostgreSQL: {postgresql_success}")
            
            return redis_success or postgresql_success
            
        except Exception as e:
            logger.error(f"Failed to clear data from hybrid provider: {e}")
            return False
    
    async def health_check(self) -> bool:
        """Check health of both providers."""
        try:
            redis_healthy = await self.redis_provider.health_check()
            postgresql_healthy = await self.postgresql_provider.health_check()
            
            overall_healthy = redis_healthy or postgresql_healthy  # At least one must be healthy
            
            logger.debug(f"Hybrid health check - Redis: {redis_healthy}, PostgreSQL: {postgresql_healthy}")
            
            return overall_healthy
            
        except Exception as e:
            logger.error(f"Health check failed for hybrid provider: {e}")
            return False
    
    def get_provider_info(self) -> Dict[str, Any]:
        """Get information about the hybrid memory provider."""
        return {
            "provider_type": "hybrid",
            "redis_ttl": self.redis_ttl,
            "migration_enabled": self.migration_enabled,
            "migration_batch_size": self.migration_batch_size,
            "redis_info": self.redis_provider.get_provider_info() if self.redis_provider else None,
            "postgresql_info": self.postgresql_provider.get_provider_info() if self.postgresql_provider else None
        }
    
    async def migrate_expired_conversations(self) -> int:
        """
        Migrate expired conversations from Redis to PostgreSQL.
        This is typically called by a background task.
        """
        if not self.migration_enabled:
            return 0
        
        try:
            # This would require Redis SCAN to find expired keys
            # For now, we'll implement a simple migration strategy
            logger.info("Starting conversation migration from Redis to PostgreSQL")
            
            # In a real implementation, you would:
            # 1. Scan Redis for keys that are about to expire
            # 2. Retrieve them from Redis
            # 3. Store them in PostgreSQL with permanent storage
            # 4. Remove from Redis
            
            migrated_count = 0
            logger.info(f"Migrated {migrated_count} conversations to PostgreSQL")
            return migrated_count
            
        except Exception as e:
            logger.error(f"Failed to migrate conversations: {e}")
            return 0
    
    async def get_conversation_stats(self) -> Dict[str, Any]:
        """Get statistics about conversation storage."""
        try:
            redis_info = self.redis_provider.get_provider_info() if self.redis_provider else {}
            postgresql_info = self.postgresql_provider.get_provider_info() if self.postgresql_provider else {}
            
            return {
                "redis_stats": redis_info,
                "postgresql_stats": postgresql_info,
                "hybrid_config": {
                    "redis_ttl": self.redis_ttl,
                    "migration_enabled": self.migration_enabled
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get conversation stats: {e}")
            return {} 