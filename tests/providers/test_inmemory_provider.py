import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from typing import Dict, Any, List
import time
import asyncio


class TestInMemoryProvider:
    """Test suite for In-Memory Provider implementation."""
    
    @pytest.fixture
    def sample_config(self):
        """Sample configuration for In-Memory provider."""
        return {
            "max_size": 1000,
            "default_ttl": 3600,
            "cleanup_interval": 300
        }
    
    @pytest.fixture
    def sample_data(self):
        """Sample data to store in memory."""
        return {
            "conversation_id": "conv_123",
            "user_id": "user_456",
            "messages": [
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi there!"}
            ],
            "timestamp": "2024-01-01T12:00:00Z"
        }
    
    @pytest.mark.asyncio
    async def test_inmemory_provider_initialization(self, sample_config):
        """Test In-Memory provider initialization."""
        from src.providers.memory.inmemory_provider import InMemoryProvider
        
        provider = InMemoryProvider()
        await provider.initialize(sample_config)
        
        assert provider.max_size == 1000
        assert provider.default_ttl == 3600
        assert provider.cleanup_interval == 300
        assert provider.storage == {}
        assert provider.timestamps == {}
    
    @pytest.mark.asyncio
    async def test_inmemory_provider_store_success(self, sample_config, sample_data):
        """Test successful data storage in memory."""
        from src.providers.memory.inmemory_provider import InMemoryProvider
        
        provider = InMemoryProvider()
        await provider.initialize(sample_config)
        
        result = await provider.store("conv_123", sample_data)
        
        assert result is True
        assert "conv_123" in provider.storage
        assert provider.storage["conv_123"] == sample_data
        assert "conv_123" in provider.timestamps
    
    @pytest.mark.asyncio
    async def test_inmemory_provider_store_with_ttl(self, sample_config, sample_data):
        """Test data storage with custom TTL."""
        from src.providers.memory.inmemory_provider import InMemoryProvider
        
        provider = InMemoryProvider()
        await provider.initialize(sample_config)
        
        result = await provider.store("conv_123", sample_data, ttl=1800)
        
        assert result is True
        assert "conv_123" in provider.storage
        assert provider.storage["conv_123"] == sample_data
        assert "conv_123" in provider.timestamps
        # Check that TTL is set correctly
        assert provider.timestamps["conv_123"] > time.time()
    
    @pytest.mark.asyncio
    async def test_inmemory_provider_store_max_size_limit(self, sample_config, sample_data):
        """Test that storage respects max size limit."""
        from src.providers.memory.inmemory_provider import InMemoryProvider
        
        # Set a very small max_size for testing
        test_config = {"max_size": 2, "default_ttl": 3600, "cleanup_interval": 300}
        
        provider = InMemoryProvider()
        await provider.initialize(test_config)
        
        # Store first item
        result1 = await provider.store("key1", {"data": "value1"})
        assert result1 is True
        
        # Store second item
        result2 = await provider.store("key2", {"data": "value2"})
        assert result2 is True
        
        # Try to store third item - should fail due to max size
        result3 = await provider.store("key3", {"data": "value3"})
        assert result3 is False
        assert "key3" not in provider.storage
    
    @pytest.mark.asyncio
    async def test_inmemory_provider_retrieve_success(self, sample_config, sample_data):
        """Test successful data retrieval from memory."""
        from src.providers.memory.inmemory_provider import InMemoryProvider
        
        provider = InMemoryProvider()
        await provider.initialize(sample_config)
        
        # Store data first
        await provider.store("conv_123", sample_data)
        
        # Retrieve data
        result = await provider.retrieve("conv_123")
        
        assert result == [sample_data]
    
    @pytest.mark.asyncio
    async def test_inmemory_provider_retrieve_not_found(self, sample_config):
        """Test data retrieval when key doesn't exist."""
        from src.providers.memory.inmemory_provider import InMemoryProvider
        
        provider = InMemoryProvider()
        await provider.initialize(sample_config)
        
        result = await provider.retrieve("nonexistent_key")
        
        assert result == []
    
    @pytest.mark.asyncio
    async def test_inmemory_provider_retrieve_expired(self, sample_config, sample_data):
        """Test data retrieval when data has expired."""
        from src.providers.memory.inmemory_provider import InMemoryProvider
        
        provider = InMemoryProvider()
        await provider.initialize(sample_config)
        
        # Store data with very short TTL
        await provider.store("conv_123", sample_data, ttl=1)
        
        # Wait for expiration
        await asyncio.sleep(1.1)
        
        # Try to retrieve expired data
        result = await provider.retrieve("conv_123")
        
        assert result == []
        # Check that expired data is cleaned up
        assert "conv_123" not in provider.storage
    
    @pytest.mark.asyncio
    async def test_inmemory_provider_clear_success(self, sample_config, sample_data):
        """Test successful data clearing from memory."""
        from src.providers.memory.inmemory_provider import InMemoryProvider
        
        provider = InMemoryProvider()
        await provider.initialize(sample_config)
        
        # Store data first
        await provider.store("conv_123", sample_data)
        assert "conv_123" in provider.storage
        
        # Clear data
        result = await provider.clear("conv_123")
        
        assert result is True
        assert "conv_123" not in provider.storage
        assert "conv_123" not in provider.timestamps
    
    @pytest.mark.asyncio
    async def test_inmemory_provider_clear_not_found(self, sample_config):
        """Test data clearing when key doesn't exist."""
        from src.providers.memory.inmemory_provider import InMemoryProvider
        
        provider = InMemoryProvider()
        await provider.initialize(sample_config)
        
        result = await provider.clear("nonexistent_key")
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_inmemory_provider_health_check_success(self, sample_config):
        """Test successful health check."""
        from src.providers.memory.inmemory_provider import InMemoryProvider
        
        provider = InMemoryProvider()
        await provider.initialize(sample_config)
        
        result = await provider.health_check()
        
        assert result is True
    
    def test_inmemory_provider_get_provider_info(self, sample_config):
        """Test provider info retrieval."""
        from src.providers.memory.inmemory_provider import InMemoryProvider
        
        provider = InMemoryProvider()
        
        info = provider.get_provider_info()
        
        assert info["name"] == "inmemory"
        assert info["type"] == "memory"
        assert "version" in info
        assert "description" in info
    
    @pytest.mark.asyncio
    async def test_inmemory_provider_interface_compliance(self, sample_config, sample_data):
        """Test that In-Memory provider implements MemoryInterface correctly."""
        from src.providers.memory.inmemory_provider import InMemoryProvider
        from src.interfaces.memory_interface import MemoryInterface
        
        provider = InMemoryProvider()
        
        # Check interface compliance
        assert isinstance(provider, MemoryInterface)
        assert hasattr(provider, 'initialize')
        assert hasattr(provider, 'store')
        assert hasattr(provider, 'retrieve')
        assert hasattr(provider, 'clear')
        assert hasattr(provider, 'health_check')
        assert hasattr(provider, 'get_provider_info')
        
        # Test all methods work
        await provider.initialize(sample_config)
        assert await provider.store("test", sample_data) is True
        assert await provider.retrieve("test") == [sample_data]
        assert await provider.clear("test") is True
        assert await provider.health_check() is True
        assert provider.get_provider_info()["name"] == "inmemory"
    
    @pytest.mark.asyncio
    async def test_inmemory_provider_cleanup_expired_data(self, sample_config, sample_data):
        """Test that expired data is automatically cleaned up."""
        from src.providers.memory.inmemory_provider import InMemoryProvider
        
        provider = InMemoryProvider()
        await provider.initialize(sample_config)
        
        # Store data with very short TTL
        await provider.store("conv_123", sample_data, ttl=1)
        assert "conv_123" in provider.storage
        
        # Wait for expiration
        await asyncio.sleep(1.1)
        
        # Trigger cleanup by calling retrieve
        result = await provider.retrieve("conv_123")
        
        assert result == []
        assert "conv_123" not in provider.storage
        assert "conv_123" not in provider.timestamps
    
    @pytest.mark.asyncio
    async def test_inmemory_provider_multiple_keys(self, sample_config, sample_data):
        """Test handling multiple keys in storage."""
        from src.providers.memory.inmemory_provider import InMemoryProvider
        
        provider = InMemoryProvider()
        await provider.initialize(sample_config)
        
        # Store multiple items
        await provider.store("key1", {"data": "value1"})
        await provider.store("key2", {"data": "value2"})
        await provider.store("key3", {"data": "value3"})
        
        # Retrieve all items
        result1 = await provider.retrieve("key1")
        result2 = await provider.retrieve("key2")
        result3 = await provider.retrieve("key3")
        
        assert result1 == [{"data": "value1"}]
        assert result2 == [{"data": "value2"}]
        assert result3 == [{"data": "value3"}]
        
        # Clear one item
        await provider.clear("key2")
        result2_after_clear = await provider.retrieve("key2")
        assert result2_after_clear == []
        
        # Other items should still exist
        result1_after_clear = await provider.retrieve("key1")
        result3_after_clear = await provider.retrieve("key3")
        assert result1_after_clear == [{"data": "value1"}]
        assert result3_after_clear == [{"data": "value3"}]
    
    @pytest.mark.asyncio
    async def test_inmemory_provider_storage_persistence(self, sample_config, sample_data):
        """Test that data persists across multiple operations."""
        from src.providers.memory.inmemory_provider import InMemoryProvider
        
        provider = InMemoryProvider()
        await provider.initialize(sample_config)
        
        # Store data
        await provider.store("conv_123", sample_data)
        
        # Verify storage
        assert len(provider.storage) == 1
        assert len(provider.timestamps) == 1
        
        # Retrieve data
        result = await provider.retrieve("conv_123")
        assert result == [sample_data]
        
        # Verify storage is still intact
        assert len(provider.storage) == 1
        assert len(provider.timestamps) == 1
        
        # Update data
        updated_data = {**sample_data, "updated": True}
        await provider.store("conv_123", updated_data)
        
        # Verify updated data
        result_updated = await provider.retrieve("conv_123")
        assert result_updated == [updated_data] 