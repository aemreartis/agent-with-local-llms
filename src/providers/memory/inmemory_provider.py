import time
import asyncio
from typing import Dict, Any, List, Optional
from src.interfaces.memory_interface import MemoryInterface

class InMemoryProvider(MemoryInterface):
    """In-memory memory provider for development and testing."""
    def __init__(self):
        self.storage = {}
        self.timestamps = {}
        self.max_size = 1000
        self.default_ttl = 3600
        self.cleanup_interval = 300
        self._cleanup_task = None

    async def initialize(self, config: Dict[str, Any]) -> None:
        self.max_size = config.get("max_size", 1000)
        self.default_ttl = config.get("default_ttl", 3600)
        self.cleanup_interval = config.get("cleanup_interval", 300)
        self.storage = {}
        self.timestamps = {}
        # Optionally, start a background cleanup task (not needed for tests)

    async def store(self, key: str, data: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        if len(self.storage) >= self.max_size and key not in self.storage:
            return False
        ttl = ttl or self.default_ttl
        self.storage[key] = data
        self.timestamps[key] = time.time() + ttl
        return True

    async def retrieve(self, key: str) -> List[Dict[str, Any]]:
        self._cleanup_expired()
        if key in self.storage and self.timestamps[key] > time.time():
            return [self.storage[key]]
        else:
            self.storage.pop(key, None)
            self.timestamps.pop(key, None)
            return []

    async def clear(self, key: str) -> bool:
        existed = key in self.storage
        self.storage.pop(key, None)
        self.timestamps.pop(key, None)
        return existed

    async def health_check(self) -> bool:
        return True

    def get_provider_info(self) -> Dict[str, Any]:
        return {
            "name": "inmemory",
            "type": "memory",
            "version": "1.0.0",
            "description": "In-memory memory provider for development and testing",
            "features": ["No persistence", "TTL support", "Fast", "No external dependencies"]
        }

    def _cleanup_expired(self):
        now = time.time()
        expired_keys = [k for k, t in self.timestamps.items() if t <= now]
        for k in expired_keys:
            self.storage.pop(k, None)
            self.timestamps.pop(k, None) 