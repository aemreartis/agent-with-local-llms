import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from typing import Dict, Any, List
import sys


class TestPostgreSQLMemoryProvider:
    """Test suite for PostgreSQL Memory Provider implementation."""
    
    @pytest.fixture
    def sample_config(self):
        """Sample configuration for PostgreSQL provider."""
        return {
            "host": "localhost",
            "port": 5432,
            "database": "agentic_rag",
            "username": "postgres",
            "password": "password",
            "table_name": "conversation_memory",
            "max_connections": 10
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
            "timestamp": "2024-01-01T12:00:00Z",
            "metadata": {"session_duration": 300}
        }
    
    def _setup_asyncpg_mock(self):
        """Helper to setup asyncpg mock."""
        mock_asyncpg_module = MagicMock()
        return mock_asyncpg_module
    
    def _setup_pool_mock(self):
        """Helper to setup pool mock with proper async context manager."""
        mock_pool = AsyncMock()
        mock_connection = AsyncMock()
        
        # Create a proper async context manager
        class MockAsyncContextManager:
            def __init__(self, connection):
                self.connection = connection
            
            async def __aenter__(self):
                return self.connection
            
            async def __aexit__(self, exc_type, exc_val, exc_tb):
                return None
        
        # Make acquire return the context manager directly (not as a coroutine)
        mock_pool.acquire = MagicMock(return_value=MockAsyncContextManager(mock_connection))
        return mock_pool, mock_connection
    
    @pytest.mark.asyncio
    async def test_postgresql_provider_initialization(self, sample_config):
        """Test PostgreSQL provider initialization."""
        mock_asyncpg_module = self._setup_asyncpg_mock()
        with patch.dict('sys.modules', {'asyncpg': mock_asyncpg_module}):
            with patch('asyncpg.create_pool', new_callable=AsyncMock) as mock_create_pool:
                mock_pool, mock_connection = self._setup_pool_mock()
                mock_create_pool.return_value = mock_pool
                
                from src.providers.memory.postgresql_provider import PostgreSQLMemoryProvider
                
                provider = PostgreSQLMemoryProvider()
                await provider.initialize(sample_config)
                
                assert provider.pool == mock_pool
                assert provider.table_name == "conversation_memory"
                mock_create_pool.assert_called_once_with(
                    host="localhost",
                    port=5432,
                    database="agentic_rag",
                    user="postgres",
                    password="password",
                    max_size=10
                )
    
    @pytest.mark.asyncio
    async def test_postgresql_provider_store_success(self, sample_config, sample_data):
        """Test successful data storage in PostgreSQL."""
        mock_asyncpg_module = self._setup_asyncpg_mock()
        with patch.dict('sys.modules', {'asyncpg': mock_asyncpg_module}):
            with patch('asyncpg.create_pool', new_callable=AsyncMock) as mock_create_pool:
                mock_pool, mock_connection = self._setup_pool_mock()
                mock_create_pool.return_value = mock_pool
                mock_connection.execute.return_value = "INSERT 1"
                
                from src.providers.memory.postgresql_provider import PostgreSQLMemoryProvider
                
                provider = PostgreSQLMemoryProvider()
                await provider.initialize(sample_config)
                
                result = await provider.store("conv_123", sample_data)
                
                assert result is True
                mock_connection.execute.assert_called()
                # Check that the SQL contains the expected table name
                call_args = mock_connection.execute.call_args[0][0]
                assert "conversation_memory" in call_args
                # Check that the key is passed as a parameter (PostgreSQL uses $1, $2, etc.)
                call_args_params = mock_connection.execute.call_args[0][1:]
                assert "conv_123" in call_args_params
    
    @pytest.mark.asyncio
    async def test_postgresql_provider_store_failure(self, sample_config, sample_data):
        """Test data storage failure handling."""
        mock_asyncpg_module = self._setup_asyncpg_mock()
        with patch.dict('sys.modules', {'asyncpg': mock_asyncpg_module}):
            with patch('asyncpg.create_pool', new_callable=AsyncMock) as mock_create_pool:
                mock_pool, mock_connection = self._setup_pool_mock()
                mock_create_pool.return_value = mock_pool
                
                # Set up the mock to fail only on store operation, not initialization
                def execute_side_effect(sql, *args):
                    if "INSERT INTO" in sql or "ON CONFLICT" in sql:
                        raise Exception("Database connection failed")
                    return "CREATE TABLE"
                
                mock_connection.execute.side_effect = execute_side_effect
                
                from src.providers.memory.postgresql_provider import PostgreSQLMemoryProvider
                
                provider = PostgreSQLMemoryProvider()
                await provider.initialize(sample_config)
                
                result = await provider.store("conv_123", sample_data)
                
                assert result is False
    
    @pytest.mark.asyncio
    async def test_postgresql_provider_retrieve_success(self, sample_config, sample_data):
        """Test successful data retrieval from PostgreSQL."""
        mock_asyncpg_module = self._setup_asyncpg_mock()
        with patch.dict('sys.modules', {'asyncpg': mock_asyncpg_module}):
            with patch('asyncpg.create_pool', new_callable=AsyncMock) as mock_create_pool:
                mock_pool, mock_connection = self._setup_pool_mock()
                mock_create_pool.return_value = mock_pool
                mock_connection.fetch.return_value = [
                    {"data": '{"conversation_id": "conv_123", "user_id": "user_456", "messages": [{"role": "user", "content": "Hello"}, {"role": "assistant", "content": "Hi there!"}], "timestamp": "2024-01-01T12:00:00Z", "metadata": {"session_duration": 300}}'}
                ]
                
                from src.providers.memory.postgresql_provider import PostgreSQLMemoryProvider
                
                provider = PostgreSQLMemoryProvider()
                await provider.initialize(sample_config)
                
                result = await provider.retrieve("conv_123")
                
                assert result == [sample_data]
                mock_connection.fetch.assert_called_once()
                # Check that the SQL contains the expected table name
                call_args = mock_connection.fetch.call_args[0][0]
                assert "conversation_memory" in call_args
                # Check that the key is passed as a parameter (PostgreSQL uses $1, $2, etc.)
                call_args_params = mock_connection.fetch.call_args[0][1:]
                assert "conv_123" in call_args_params
    
    @pytest.mark.asyncio
    async def test_postgresql_provider_retrieve_not_found(self, sample_config):
        """Test data retrieval when key doesn't exist."""
        mock_asyncpg_module = self._setup_asyncpg_mock()
        with patch.dict('sys.modules', {'asyncpg': mock_asyncpg_module}):
            with patch('asyncpg.create_pool', new_callable=AsyncMock) as mock_create_pool:
                mock_pool, mock_connection = self._setup_pool_mock()
                mock_create_pool.return_value = mock_pool
                mock_connection.fetch.return_value = []
                
                from src.providers.memory.postgresql_provider import PostgreSQLMemoryProvider
                
                provider = PostgreSQLMemoryProvider()
                await provider.initialize(sample_config)
                
                result = await provider.retrieve("nonexistent_key")
                
                assert result == []
    
    @pytest.mark.asyncio
    async def test_postgresql_provider_retrieve_invalid_json(self, sample_config):
        """Test data retrieval with invalid JSON handling."""
        mock_asyncpg_module = self._setup_asyncpg_mock()
        with patch.dict('sys.modules', {'asyncpg': mock_asyncpg_module}):
            with patch('asyncpg.create_pool', new_callable=AsyncMock) as mock_create_pool:
                mock_pool, mock_connection = self._setup_pool_mock()
                mock_create_pool.return_value = mock_pool
                mock_connection.fetch.return_value = [{"data": "invalid json"}]
                
                from src.providers.memory.postgresql_provider import PostgreSQLMemoryProvider
                
                provider = PostgreSQLMemoryProvider()
                await provider.initialize(sample_config)
                
                result = await provider.retrieve("conv_123")
                
                assert result == []
    
    @pytest.mark.asyncio
    async def test_postgresql_provider_clear_success(self, sample_config):
        """Test successful data clearing from PostgreSQL."""
        mock_asyncpg_module = self._setup_asyncpg_mock()
        with patch.dict('sys.modules', {'asyncpg': mock_asyncpg_module}):
            with patch('asyncpg.create_pool', new_callable=AsyncMock) as mock_create_pool:
                mock_pool, mock_connection = self._setup_pool_mock()
                mock_create_pool.return_value = mock_pool
                mock_connection.execute.return_value = "DELETE 1"
                
                from src.providers.memory.postgresql_provider import PostgreSQLMemoryProvider
                
                provider = PostgreSQLMemoryProvider()
                await provider.initialize(sample_config)
                
                result = await provider.clear("conv_123")
                
                assert result is True
                # Check that execute was called (including initialization and clear)
                assert mock_connection.execute.call_count >= 2
                # Verify the clear operation was called with the right parameters
                clear_calls = [call for call in mock_connection.execute.call_args_list if "DELETE FROM" in call[0][0]]
                assert len(clear_calls) == 1
                assert "conv_123" in clear_calls[0][0][1:]  # Check parameters
    
    @pytest.mark.asyncio
    async def test_postgresql_provider_clear_failure(self, sample_config):
        """Test data clearing failure handling."""
        mock_asyncpg_module = self._setup_asyncpg_mock()
        with patch.dict('sys.modules', {'asyncpg': mock_asyncpg_module}):
            with patch('asyncpg.create_pool', new_callable=AsyncMock) as mock_create_pool:
                mock_pool, mock_connection = self._setup_pool_mock()
                mock_create_pool.return_value = mock_pool
                
                # Set up the mock to fail only on clear operation, not initialization
                def execute_side_effect(sql, *args):
                    if "DELETE FROM" in sql:
                        raise Exception("Database connection failed")
                    return "CREATE TABLE"
                
                mock_connection.execute.side_effect = execute_side_effect
                
                from src.providers.memory.postgresql_provider import PostgreSQLMemoryProvider
                
                provider = PostgreSQLMemoryProvider()
                await provider.initialize(sample_config)
                
                result = await provider.clear("conv_123")
                
                assert result is False
    
    @pytest.mark.asyncio
    async def test_postgresql_provider_health_check_success(self, sample_config):
        """Test successful health check."""
        mock_asyncpg_module = self._setup_asyncpg_mock()
        with patch.dict('sys.modules', {'asyncpg': mock_asyncpg_module}):
            with patch('asyncpg.create_pool', new_callable=AsyncMock) as mock_create_pool:
                mock_pool, mock_connection = self._setup_pool_mock()
                mock_create_pool.return_value = mock_pool
                mock_connection.fetchval.return_value = 1
                
                from src.providers.memory.postgresql_provider import PostgreSQLMemoryProvider
                
                provider = PostgreSQLMemoryProvider()
                await provider.initialize(sample_config)
                
                result = await provider.health_check()
                
                assert result is True
                mock_connection.fetchval.assert_called_once_with("SELECT 1")
    
    @pytest.mark.asyncio
    async def test_postgresql_provider_health_check_failure(self, sample_config):
        """Test health check failure."""
        mock_asyncpg_module = self._setup_asyncpg_mock()
        with patch.dict('sys.modules', {'asyncpg': mock_asyncpg_module}):
            with patch('asyncpg.create_pool', new_callable=AsyncMock) as mock_create_pool:
                mock_pool, mock_connection = self._setup_pool_mock()
                mock_create_pool.return_value = mock_pool
                mock_connection.fetchval.side_effect = Exception("Database connection failed")
                
                from src.providers.memory.postgresql_provider import PostgreSQLMemoryProvider
                
                provider = PostgreSQLMemoryProvider()
                await provider.initialize(sample_config)
                
                result = await provider.health_check()
                
                assert result is False
    
    def test_postgresql_provider_get_provider_info(self, sample_config):
        """Test provider info retrieval."""
        mock_asyncpg_module = self._setup_asyncpg_mock()
        with patch.dict('sys.modules', {'asyncpg': mock_asyncpg_module}):
            from src.providers.memory.postgresql_provider import PostgreSQLMemoryProvider
            
            provider = PostgreSQLMemoryProvider()
            
            info = provider.get_provider_info()
            
            assert info["name"] == "postgresql"
            assert info["type"] == "memory"
            assert "version" in info
            assert "description" in info
    
    @pytest.mark.asyncio
    async def test_postgresql_provider_interface_compliance(self, sample_config, sample_data):
        """Test that PostgreSQL provider implements MemoryInterface correctly."""
        mock_asyncpg_module = self._setup_asyncpg_mock()
        with patch.dict('sys.modules', {'asyncpg': mock_asyncpg_module}):
            with patch('asyncpg.create_pool', new_callable=AsyncMock) as mock_create_pool:
                mock_pool, mock_connection = self._setup_pool_mock()
                mock_create_pool.return_value = mock_pool
                mock_connection.execute.return_value = "INSERT 1"
                mock_connection.fetch.return_value = [{"data": '{"conversation_id": "conv_123"}'}]
                mock_connection.fetchval.return_value = 1
                
                from src.providers.memory.postgresql_provider import PostgreSQLMemoryProvider
                from src.interfaces.memory_interface import MemoryInterface
                
                provider = PostgreSQLMemoryProvider()
                
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
                assert provider.get_provider_info()["name"] == "postgresql"
    
    @pytest.mark.asyncio
    async def test_postgresql_provider_table_creation(self, sample_config):
        """Test that the provider creates the table if it doesn't exist."""
        mock_asyncpg_module = self._setup_asyncpg_mock()
        with patch.dict('sys.modules', {'asyncpg': mock_asyncpg_module}):
            with patch('asyncpg.create_pool', new_callable=AsyncMock) as mock_create_pool:
                mock_pool, mock_connection = self._setup_pool_mock()
                mock_create_pool.return_value = mock_pool
                mock_connection.execute.return_value = "CREATE TABLE"
                
                from src.providers.memory.postgresql_provider import PostgreSQLMemoryProvider
                
                provider = PostgreSQLMemoryProvider()
                await provider.initialize(sample_config)
                
                # Check that table creation SQL was executed
                mock_connection.execute.assert_called()
                # Find the table creation call
                table_creation_calls = [
                    call for call in mock_connection.execute.call_args_list
                    if "CREATE TABLE" in str(call[0][0])
                ]
                assert len(table_creation_calls) > 0 