from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional


class MemoryInterface(ABC):
    """Interface for memory providers that store and retrieve conversation history."""
    
    @abstractmethod
    async def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize the memory provider with configuration."""
        pass
    
    @abstractmethod
    async def store(self, key: str, data: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        """Store data with an optional TTL (time to live in seconds)."""
        pass
    
    @abstractmethod
    async def retrieve(self, key: str) -> List[Dict[str, Any]]:
        """Retrieve data by key."""
        pass
    
    @abstractmethod
    async def clear(self, key: str) -> bool:
        """Clear data for a specific key."""
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """Check if the memory provider is healthy."""
        pass
    
    @abstractmethod
    def get_provider_info(self) -> Dict[str, Any]:
        """Get information about the memory provider."""
        pass 