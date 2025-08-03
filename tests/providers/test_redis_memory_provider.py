import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from typing import Dict, Any, List
import sys


class TestRedisMemoryProvider:
    """Test suite for Redis Memory Provider implementation."""
    
    @pytest.fixture
    def sample_config(self):
        """Sample configuration for Redis provider."""
        return {
            "host": "localhost",
            "port": 6379,
            "db": 0,
            "password": None,
            "prefix": "agentic_rag:",
            "default_ttl": 3600
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
    
    def _setup_redis_mock(self):
        """Helper to setup Redis mock."""
        mock_redis_module = MagicMock()
        mock_redis_module.asyncio = MagicMock()
        return mock_redis_module
    
    @pytest.mark.asyncio
    async def test_redis_provider_initialization(self, sample_config):
        """Test Redis provider initialization."""
        mock_redis_module = self._setup_redis_mock()
        with patch.dict('sys.modules', {'redis': mock_redis_module}):
            with patch('redis.asyncio.Redis') as mock_redis:
                mock_redis_instance = AsyncMock()
                mock_redis.return_value = mock_redis_instance
                
                from src.providers.memory.redis_provider import RedisMemoryProvider
                
                provider = RedisMemoryProvider()
                await provider.initialize(sample_config)
                
                assert provider.redis_client == mock_redis_instance
                assert provider.prefix == "agentic_rag:"
                assert provider.default_ttl == 3600
                mock_redis.assert_called_once_with(
                    host="localhost",
                    port=6379,
                    db=0,
                    password=None,
                    decode_responses=True
                )
    
    @pytest.mark.asyncio
    async def test_redis_provider_store_success(self, sample_config, sample_data):
        """Test successful data storage in Redis."""
        mock_redis_module = self._setup_redis_mock()
        with patch.dict('sys.modules', {'redis': mock_redis_module}):
            with patch('redis.asyncio.Redis') as mock_redis:
                mock_redis_instance = AsyncMock()
                mock_redis.return_value = mock_redis_instance
                mock_redis_instance.setex.return_value = True
                
                from src.providers.memory.redis_provider import RedisMemoryProvider
                
                provider = RedisMemoryProvider()
                await provider.initialize(sample_config)
                
                result = await provider.store("conv_123", sample_data, ttl=1800)
                
                assert result is True
                mock_redis_instance.setex.assert_called_once_with(
                    "agentic_rag:conv_123",
                    1800,
                    '{"conversation_id": "conv_123", "user_id": "user_456", "messages": [{"role": "user", "content": "Hello"}, {"role": "assistant", "content": "Hi there!"}], "timestamp": "2024-01-01T12:00:00Z"}'
                )
    
    @pytest.mark.asyncio
    async def test_redis_provider_store_with_default_ttl(self, sample_config, sample_data):
        """Test data storage with default TTL."""
        mock_redis_module = self._setup_redis_mock()
        with patch.dict('sys.modules', {'redis': mock_redis_module}):
            with patch('redis.asyncio.Redis') as mock_redis:
                mock_redis_instance = AsyncMock()
                mock_redis.return_value = mock_redis_instance
                mock_redis_instance.setex.return_value = True
                
                from src.providers.memory.redis_provider import RedisMemoryProvider
                
                provider = RedisMemoryProvider()
                await provider.initialize(sample_config)
                
                result = await provider.store("conv_123", sample_data)
                
                assert result is True
                mock_redis_instance.setex.assert_called_once_with(
                    "agentic_rag:conv_123",
                    3600,  # default_ttl
                    '{"conversation_id": "conv_123", "user_id": "user_456", "messages": [{"role": "user", "content": "Hello"}, {"role": "assistant", "content": "Hi there!"}], "timestamp": "2024-01-01T12:00:00Z"}'
                )
    
    @pytest.mark.asyncio
    async def test_redis_provider_store_failure(self, sample_config, sample_data):
        """Test data storage failure handling."""
        mock_redis_module = self._setup_redis_mock()
        with patch.dict('sys.modules', {'redis': mock_redis_module}):
            with patch('redis.asyncio.Redis') as mock_redis:
                mock_redis_instance = AsyncMock()
                mock_redis.return_value = mock_redis_instance
                mock_redis_instance.setex.side_effect = Exception("Redis connection failed")
                
                from src.providers.memory.redis_provider import RedisMemoryProvider
                
                provider = RedisMemoryProvider()
                await provider.initialize(sample_config)
                
                result = await provider.store("conv_123", sample_data)
                
                assert result is False
    
    @pytest.mark.asyncio
    async def test_redis_provider_retrieve_success(self, sample_config, sample_data):
        """Test successful data retrieval from Redis."""
        mock_redis_module = self._setup_redis_mock()
        with patch.dict('sys.modules', {'redis': mock_redis_module}):
            with patch('redis.asyncio.Redis') as mock_redis:
                mock_redis_instance = AsyncMock()
                mock_redis.return_value = mock_redis_instance
                mock_redis_instance.get.return_value = '{"conversation_id": "conv_123", "user_id": "user_456", "messages": [{"role": "user", "content": "Hello"}, {"role": "assistant", "content": "Hi there!"}], "timestamp": "2024-01-01T12:00:00Z"}'
                
                from src.providers.memory.redis_provider import RedisMemoryProvider
                
                provider = RedisMemoryProvider()
                await provider.initialize(sample_config)
                
                result = await provider.retrieve("conv_123")
                
                assert result == [sample_data]
                mock_redis_instance.get.assert_called_once_with("agentic_rag:conv_123")
    
    @pytest.mark.asyncio
    async def test_redis_provider_retrieve_not_found(self, sample_config):
        """Test data retrieval when key doesn't exist."""
        mock_redis_module = self._setup_redis_mock()
        with patch.dict('sys.modules', {'redis': mock_redis_module}):
            with patch('redis.asyncio.Redis') as mock_redis:
                mock_redis_instance = AsyncMock()
                mock_redis.return_value = mock_redis_instance
                mock_redis_instance.get.return_value = None
                
                from src.providers.memory.redis_provider import RedisMemoryProvider
                
                provider = RedisMemoryProvider()
                await provider.initialize(sample_config)
                
                result = await provider.retrieve("nonexistent_key")
                
                assert result == []
    
    @pytest.mark.asyncio
    async def test_redis_provider_retrieve_invalid_json(self, sample_config):
        """Test data retrieval with invalid JSON handling."""
        mock_redis_module = self._setup_redis_mock()
        with patch.dict('sys.modules', {'redis': mock_redis_module}):
            with patch('redis.asyncio.Redis') as mock_redis:
                mock_redis_instance = AsyncMock()
                mock_redis.return_value = mock_redis_instance
                mock_redis_instance.get.return_value = "invalid json"
                
                from src.providers.memory.redis_provider import RedisMemoryProvider
                
                provider = RedisMemoryProvider()
                await provider.initialize(sample_config)
                
                result = await provider.retrieve("conv_123")
                
                assert result == []
    
    @pytest.mark.asyncio
    async def test_redis_provider_clear_success(self, sample_config):
        """Test successful data clearing from Redis."""
        mock_redis_module = self._setup_redis_mock()
        with patch.dict('sys.modules', {'redis': mock_redis_module}):
            with patch('redis.asyncio.Redis') as mock_redis:
                mock_redis_instance = AsyncMock()
                mock_redis.return_value = mock_redis_instance
                mock_redis_instance.delete.return_value = 1
                
                from src.providers.memory.redis_provider import RedisMemoryProvider
                
                provider = RedisMemoryProvider()
                await provider.initialize(sample_config)
                
                result = await provider.clear("conv_123")
                
                assert result is True
                mock_redis_instance.delete.assert_called_once_with("agentic_rag:conv_123")
    
    @pytest.mark.asyncio
    async def test_redis_provider_clear_failure(self, sample_config):
        """Test data clearing failure handling."""
        mock_redis_module = self._setup_redis_mock()
        with patch.dict('sys.modules', {'redis': mock_redis_module}):
            with patch('redis.asyncio.Redis') as mock_redis:
                mock_redis_instance = AsyncMock()
                mock_redis.return_value = mock_redis_instance
                mock_redis_instance.delete.side_effect = Exception("Redis connection failed")
                
                from src.providers.memory.redis_provider import RedisMemoryProvider
                
                provider = RedisMemoryProvider()
                await provider.initialize(sample_config)
                
                result = await provider.clear("conv_123")
                
                assert result is False
    
    @pytest.mark.asyncio
    async def test_redis_provider_health_check_success(self, sample_config):
        """Test successful health check."""
        mock_redis_module = self._setup_redis_mock()
        with patch.dict('sys.modules', {'redis': mock_redis_module}):
            with patch('redis.asyncio.Redis') as mock_redis:
                mock_redis_instance = AsyncMock()
                mock_redis.return_value = mock_redis_instance
                mock_redis_instance.ping.return_value = True
                
                from src.providers.memory.redis_provider import RedisMemoryProvider
                
                provider = RedisMemoryProvider()
                await provider.initialize(sample_config)
                
                result = await provider.health_check()
                
                assert result is True
                mock_redis_instance.ping.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_redis_provider_health_check_failure(self, sample_config):
        """Test health check failure."""
        mock_redis_module = self._setup_redis_mock()
        with patch.dict('sys.modules', {'redis': mock_redis_module}):
            with patch('redis.asyncio.Redis') as mock_redis:
                mock_redis_instance = AsyncMock()
                mock_redis.return_value = mock_redis_instance
                mock_redis_instance.ping.side_effect = Exception("Redis connection failed")
                
                from src.providers.memory.redis_provider import RedisMemoryProvider
                
                provider = RedisMemoryProvider()
                await provider.initialize(sample_config)
                
                result = await provider.health_check()
                
                assert result is False
    
    def test_redis_provider_get_provider_info(self, sample_config):
        """Test provider info retrieval."""
        mock_redis_module = self._setup_redis_mock()
        with patch.dict('sys.modules', {'redis': mock_redis_module}):
            from src.providers.memory.redis_provider import RedisMemoryProvider
            
            provider = RedisMemoryProvider()
            
            info = provider.get_provider_info()
            
            assert info["name"] == "redis"
            assert info["type"] == "memory"
            assert "version" in info
            assert "description" in info
    
    @pytest.mark.asyncio
    async def test_redis_provider_interface_compliance(self, sample_config, sample_data):
        """Test that Redis provider implements MemoryInterface correctly."""
        mock_redis_module = self._setup_redis_mock()
        with patch.dict('sys.modules', {'redis': mock_redis_module}):
            with patch('redis.asyncio.Redis') as mock_redis:
                mock_redis_instance = AsyncMock()
                mock_redis.return_value = mock_redis_instance
                mock_redis_instance.setex.return_value = True
                mock_redis_instance.get.return_value = '{"conversation_id": "conv_123"}'
                mock_redis_instance.delete.return_value = 1
                mock_redis_instance.ping.return_value = True
                
                from src.providers.memory.redis_provider import RedisMemoryProvider
                from src.interfaces.memory_interface import MemoryInterface
                
                provider = RedisMemoryProvider()
                
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
                assert await provider.retrieve("test") == [{"conversation_id": "conv_123"}]
                assert await provider.clear("test") is True
                assert await provider.health_check() is True
                assert provider.get_provider_info()["name"] == "redis" 