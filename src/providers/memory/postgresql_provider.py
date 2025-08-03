import json
import logging
from typing import Dict, Any, List, Optional
from src.interfaces.memory_interface import MemoryInterface

logger = logging.getLogger(__name__)


class PostgreSQLMemoryProvider(MemoryInterface):
    """PostgreSQL-based memory provider for storing conversation history."""
    
    def __init__(self):
        self.pool = None
        self.table_name = "conversation_memory"
    
    async def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize the PostgreSQL provider with configuration."""
        try:
            import asyncpg
            
            self.pool = await asyncpg.create_pool(
                host=config.get("host", "localhost"),
                port=config.get("port", 5432),
                database=config.get("database", "agentic_rag"),
                user=config.get("username", "postgres"),
                password=config.get("password"),
                max_size=config.get("max_connections", 10)
            )
            self.table_name = config.get("table_name", "conversation_memory")
            
            # Create table if it doesn't exist
            await self._create_table()
            
            logger.info(f"PostgreSQL memory provider initialized with table: {self.table_name}")
            
        except ImportError:
            raise ImportError("asyncpg is required for PostgreSQLMemoryProvider. Install with: pip install asyncpg")
        except Exception as e:
            logger.error(f"Failed to initialize PostgreSQL provider: {e}")
            raise
    
    async def _create_table(self):
        """Create the conversation memory table if it doesn't exist."""
        create_table_sql = f"""
        CREATE TABLE IF NOT EXISTS {self.table_name} (
            id SERIAL PRIMARY KEY,
            key_name VARCHAR(255) NOT NULL,
            data JSONB NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );
        CREATE INDEX IF NOT EXISTS idx_{self.table_name}_key ON {self.table_name}(key_name);
        """
        
        async with self.pool.acquire() as conn:
            await conn.execute(create_table_sql)
    
    async def store(self, key: str, data: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        """Store data with an optional TTL (time to live in seconds)."""
        try:
            if not self.pool:
                raise RuntimeError("PostgreSQL provider not initialized")
            
            # For PostgreSQL, we'll store TTL in the data itself for now
            # In a production system, you might want to use a separate TTL column
            if ttl:
                data_with_ttl = {**data, "_ttl": ttl, "_expires_at": None}  # Would implement expiration logic
            else:
                data_with_ttl = data
            
            json_data = json.dumps(data_with_ttl)
            
            # Upsert: insert if not exists, update if exists
            upsert_sql = f"""
            INSERT INTO {self.table_name} (key_name, data, updated_at)
            VALUES ($1, $2, CURRENT_TIMESTAMP)
            ON CONFLICT (key_name) 
            DO UPDATE SET 
                data = $2,
                updated_at = CURRENT_TIMESTAMP
            """
            
            async with self.pool.acquire() as conn:
                await conn.execute(upsert_sql, key, json_data)
            
            logger.debug(f"Stored data in PostgreSQL with key: {key}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store data in PostgreSQL: {e}")
            return False
    
    async def retrieve(self, key: str) -> List[Dict[str, Any]]:
        """Retrieve data by key."""
        try:
            if not self.pool:
                raise RuntimeError("PostgreSQL provider not initialized")
            
            select_sql = f"""
            SELECT data FROM {self.table_name}
            WHERE key_name = $1
            ORDER BY updated_at DESC
            """
            
            async with self.pool.acquire() as conn:
                rows = await conn.fetch(select_sql, key)
            
            if not rows:
                logger.debug(f"No data found in PostgreSQL for key: {key}")
                return []
            
            results = []
            for row in rows:
                try:
                    data = json.loads(row['data'])
                    # Remove internal TTL fields if present
                    data.pop('_ttl', None)
                    data.pop('_expires_at', None)
                    results.append(data)
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to decode JSON data from PostgreSQL: {e}")
                    continue
            
            logger.debug(f"Retrieved {len(results)} records from PostgreSQL with key: {key}")
            return results
            
        except Exception as e:
            logger.error(f"Failed to retrieve data from PostgreSQL: {e}")
            return []
    
    async def clear(self, key: str) -> bool:
        """Clear data for a specific key."""
        try:
            if not self.pool:
                raise RuntimeError("PostgreSQL provider not initialized")
            
            delete_sql = f"""
            DELETE FROM {self.table_name}
            WHERE key_name = $1
            """
            
            async with self.pool.acquire() as conn:
                result = await conn.execute(delete_sql, key)
            
            logger.debug(f"Cleared data from PostgreSQL with key: {key}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to clear data from PostgreSQL: {e}")
            return False
    
    async def health_check(self) -> bool:
        """Check if the PostgreSQL provider is healthy."""
        try:
            if not self.pool:
                return False
            
            async with self.pool.acquire() as conn:
                result = await conn.fetchval("SELECT 1")
                return result == 1
            
        except Exception as e:
            logger.error(f"PostgreSQL health check failed: {e}")
            return False
    
    def get_provider_info(self) -> Dict[str, Any]:
        """Get information about the PostgreSQL memory provider."""
        return {
            "name": "postgresql",
            "type": "memory",
            "version": "1.0.0",
            "description": "PostgreSQL-based memory provider for conversation history",
            "features": ["JSONB storage", "ACID compliance", "Async operations", "Indexed queries"]
        } 