import pytest
import yaml
import tempfile
import os
from unittest.mock import patch, MagicMock
from typing import Dict, Any
import importlib

class TestMemoryProviderIntegration:
    """Test integration of memory providers with the provider registry."""
    
    @pytest.fixture
    def sample_providers_config(self):
        """Sample providers.yaml configuration for memory providers."""
        return {
            "memory": {
                "default": "inmemory",
                "providers": {
                    "inmemory": {
                        "class": "src.providers.memory.inmemory_provider.InMemoryProvider",
                        "config": {
                            "max_size": 1000,
                            "default_ttl": 3600,
                            "cleanup_interval": 300
                        }
                    },
                    "redis": {
                        "class": "src.providers.memory.redis_provider.RedisMemoryProvider",
                        "config": {
                            "host": "localhost",
                            "port": 6379,
                            "db": 0,
                            "password": None,
                            "prefix": "agentic_rag:",
                            "default_ttl": 3600
                        }
                    },
                    "postgresql": {
                        "class": "src.providers.memory.postgresql_provider.PostgreSQLMemoryProvider",
                        "config": {
                            "host": "localhost",
                            "port": 5432,
                            "database": "agentic_rag",
                            "username": "postgres",
                            "password": "password",
                            "table_name": "conversation_memory",
                            "max_connections": 10
                        }
                    }
                }
            }
        }
    
    @pytest.fixture
    def temp_config_file(self, sample_providers_config):
        """Create a temporary config file for testing."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(sample_providers_config, f)
            temp_file = f.name
        
        yield temp_file
        
        # Cleanup
        os.unlink(temp_file)
    
    @pytest.mark.asyncio
    async def test_memory_provider_registration_from_config(self, sample_providers_config):
        """Test that memory providers can be registered from configuration."""
        from src.registry.provider_registry import ProviderRegistry
        
        registry = ProviderRegistry()
        
        # Mock the import system to avoid actual provider instantiation
        with patch('importlib.import_module') as mock_import:
            # Setup mock returns for each provider
            mock_inmemory_module = MagicMock()
            mock_inmemory_module.InMemoryProvider = MagicMock()
            
            mock_redis_module = MagicMock()
            mock_redis_module.RedisMemoryProvider = MagicMock()
            
            mock_postgresql_module = MagicMock()
            mock_postgresql_module.PostgreSQLMemoryProvider = MagicMock()
            
            mock_import.side_effect = lambda module: {
                'src.providers.memory.inmemory_provider': mock_inmemory_module,
                'src.providers.memory.redis_provider': mock_redis_module,
                'src.providers.memory.postgresql_provider': mock_postgresql_module
            }.get(module, MagicMock())
            
            # Register providers from config
            memory_config = sample_providers_config["memory"]
            for name, provider_config in memory_config["providers"].items():
                class_path = provider_config["class"]
                module_path, class_name = class_path.rsplit(".", 1)
                
                # Import the class
                module = importlib.import_module(module_path)
                provider_class = getattr(module, class_name)
                
                # Register the provider
                registry.register_provider("memory", name, provider_class)
            
            # Verify providers are registered
            assert "memory" in registry.get_all_categories()
            assert "inmemory" in registry.list_providers("memory")
            assert "redis" in registry.list_providers("memory")
            assert "postgresql" in registry.list_providers("memory")
    
    @pytest.mark.asyncio
    async def test_memory_provider_initialization_from_config(self, sample_providers_config):
        """Test that memory providers can be initialized with configuration."""
        from src.registry.provider_registry import ProviderRegistry
        
        registry = ProviderRegistry()
        
        # Mock external dependencies for Redis and PostgreSQL
        with patch.dict('sys.modules', {
            'redis': MagicMock(),
            'asyncpg': MagicMock()
        }):
            # Import actual provider classes
            from src.providers.memory.inmemory_provider import InMemoryProvider
            from src.providers.memory.redis_provider import RedisMemoryProvider
            from src.providers.memory.postgresql_provider import PostgreSQLMemoryProvider
            
            # Register providers
            registry.register_provider("memory", "inmemory", InMemoryProvider)
            registry.register_provider("memory", "redis", RedisMemoryProvider)
            registry.register_provider("memory", "postgresql", PostgreSQLMemoryProvider)
            
            # Initialize providers with config
            memory_config = sample_providers_config["memory"]
            configs = {
                "memory": {
                    name: provider_config["config"]
                    for name, provider_config in memory_config["providers"].items()
                }
            }
            
            await registry.initialize_providers(configs)
            
            # Verify providers are initialized
            inmemory_provider = await registry.get_provider("memory", "inmemory")
            assert inmemory_provider is not None
            assert hasattr(inmemory_provider, 'storage')
            
            # Test health check
            health_status = await registry.health_check_all()
            assert any("memory:inmemory" in key for key in health_status.keys())
    
    @pytest.mark.asyncio
    async def test_memory_provider_dynamic_selection(self, sample_providers_config):
        """Test that the default memory provider can be dynamically selected."""
        from src.registry.provider_registry import ProviderRegistry
        
        registry = ProviderRegistry()
        
        # Mock external dependencies
        with patch.dict('sys.modules', {
            'redis': MagicMock(),
            'asyncpg': MagicMock()
        }):
            # Import and register providers
            from src.providers.memory.inmemory_provider import InMemoryProvider
            from src.providers.memory.redis_provider import RedisMemoryProvider
            from src.providers.memory.postgresql_provider import PostgreSQLMemoryProvider
            
            registry.register_provider("memory", "inmemory", InMemoryProvider)
            registry.register_provider("memory", "redis", RedisMemoryProvider)
            registry.register_provider("memory", "postgresql", PostgreSQLMemoryProvider)
            
            # Test default provider selection (should be first registered)
            default_provider = await registry.get_provider("memory")
            assert default_provider is not None
            assert isinstance(default_provider, InMemoryProvider)
            
            # Test specific provider selection
            redis_provider = await registry.get_provider("memory", "redis")
            assert redis_provider is not None
            assert isinstance(redis_provider, RedisMemoryProvider)
    
    @pytest.mark.asyncio
    async def test_memory_provider_config_loading_from_file(self, temp_config_file):
        """Test loading memory provider configuration from a YAML file."""
        from src.registry.provider_registry import ProviderRegistry
        
        registry = ProviderRegistry()
        
        # Load config from file
        with open(temp_config_file, 'r') as f:
            config = yaml.safe_load(f)
        
        # Mock external dependencies
        with patch.dict('sys.modules', {
            'redis': MagicMock(),
            'asyncpg': MagicMock()
        }):
            # Import and register providers
            from src.providers.memory.inmemory_provider import InMemoryProvider
            from src.providers.memory.redis_provider import RedisMemoryProvider
            from src.providers.memory.postgresql_provider import PostgreSQLMemoryProvider
            
            registry.register_provider("memory", "inmemory", InMemoryProvider)
            registry.register_provider("memory", "redis", RedisMemoryProvider)
            registry.register_provider("memory", "postgresql", PostgreSQLMemoryProvider)
            
            # Initialize with config from file
            memory_config = config["memory"]
            configs = {
                "memory": {
                    name: provider_config["config"]
                    for name, provider_config in memory_config["providers"].items()
                }
            }
            
            await registry.initialize_providers(configs)
            
            # Verify configuration was applied
            inmemory_provider = await registry.get_provider("memory", "inmemory")
            assert inmemory_provider.max_size == 1000
            assert inmemory_provider.default_ttl == 3600
            assert inmemory_provider.cleanup_interval == 300
    
    @pytest.mark.asyncio
    async def test_memory_provider_interface_compliance(self):
        """Test that all memory providers implement the MemoryInterface correctly."""
        from src.interfaces.memory_interface import MemoryInterface
        
        # Mock external dependencies
        with patch.dict('sys.modules', {
            'redis': MagicMock(),
            'asyncpg': MagicMock()
        }):
            from src.providers.memory.inmemory_provider import InMemoryProvider
            from src.providers.memory.redis_provider import RedisMemoryProvider
            from src.providers.memory.postgresql_provider import PostgreSQLMemoryProvider
            
            # Test interface compliance
            providers = [
                InMemoryProvider(),
                RedisMemoryProvider(),
                PostgreSQLMemoryProvider()
            ]
            
            for provider in providers:
                # Check that all required methods exist
                assert hasattr(provider, 'initialize')
                assert hasattr(provider, 'store')
                assert hasattr(provider, 'retrieve')
                assert hasattr(provider, 'clear')
                assert hasattr(provider, 'health_check')
                assert hasattr(provider, 'get_provider_info')
                
                # Check that provider info is returned correctly
                info = provider.get_provider_info()
                assert isinstance(info, dict)
                assert "name" in info
                assert "type" in info
                assert info["type"] == "memory"
    
    @pytest.mark.asyncio
    async def test_memory_provider_registry_shutdown(self):
        """Test that memory providers are properly shut down by the registry."""
        from src.registry.provider_registry import ProviderRegistry
        
        registry = ProviderRegistry()
        
        # Mock external dependencies
        with patch.dict('sys.modules', {
            'redis': MagicMock(),
            'asyncpg': MagicMock()
        }):
            from src.providers.memory.inmemory_provider import InMemoryProvider
            
            # Register and initialize provider
            registry.register_provider("memory", "inmemory", InMemoryProvider)
            await registry.get_provider("memory", "inmemory")
            
            # Verify provider is initialized
            assert len(registry._provider_instances) > 0
            
            # Shutdown all providers
            await registry.shutdown_all()
            
            # Verify instances are cleared
            assert len(registry._provider_instances) == 0 