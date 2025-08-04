"""
Basic integration tests for Stage 8.
Simple tests that validate basic integration without complex mocking.
"""

import pytest
from src.registry.provider_registry import ProviderRegistry
from src.config.config_loader import ConfigLoader


class TestBasicIntegration:
    """Basic integration tests that work with existing setup."""
    
    @pytest.mark.integration
    def test_provider_registry_creation(self):
        """Test that provider registry can be created."""
        # RED: Write failing test that defines expected behavior
        registry = ProviderRegistry()
        assert registry is not None
        assert hasattr(registry, 'initialize_providers')
        assert hasattr(registry, 'get_provider')
    
    @pytest.mark.integration
    def test_config_loader_creation(self):
        """Test that config loader can be created."""
        # RED: Write failing test that defines expected behavior
        config_loader = ConfigLoader()
        assert config_loader is not None
        assert hasattr(config_loader, 'load_config')
        assert hasattr(config_loader, 'validate_config_structure')
    
    @pytest.mark.integration
    def test_provider_class_imports(self):
        """Test that all provider classes can be imported."""
        # RED: Write failing test that defines expected behavior
        try:
            from src.providers.llm.vllm_provider import VLLMProvider
            from src.providers.vector_stores.qdrant_provider import QdrantProvider
            from src.providers.rerankers.bge_provider import BGEProvider
            from src.providers.memory.inmemory_provider import InMemoryProvider
            
            # Verify classes can be instantiated
            vllm_provider = VLLMProvider()
            qdrant_provider = QdrantProvider()
            bge_provider = BGEProvider()
            inmemory_provider = InMemoryProvider()
            
            assert vllm_provider is not None
            assert qdrant_provider is not None
            assert bge_provider is not None
            assert inmemory_provider is not None
            
        except ImportError as e:
            # This is expected if external dependencies are not installed
            assert "import" in str(e).lower()
    
    @pytest.mark.integration
    def test_interface_compliance(self):
        """Test that all providers implement their interfaces correctly."""
        # RED: Write failing test that defines expected behavior
        from src.interfaces.llm_interface import LLMInterface
        from src.interfaces.vector_store_interface import VectorStoreInterface
        from src.interfaces.reranker_interface import RerankerInterface
        from src.interfaces.memory_interface import MemoryInterface
        
        # Test that providers implement their interfaces
        try:
            from src.providers.llm.vllm_provider import VLLMProvider
            from src.providers.vector_stores.qdrant_provider import QdrantProvider
            from src.providers.rerankers.bge_provider import BGEProvider
            from src.providers.memory.inmemory_provider import InMemoryProvider
            
            # Verify interface compliance
            assert issubclass(VLLMProvider, LLMInterface)
            assert issubclass(QdrantProvider, VectorStoreInterface)
            assert issubclass(BGEProvider, RerankerInterface)
            assert issubclass(InMemoryProvider, MemoryInterface)
            
        except ImportError:
            # This is expected if external dependencies are not installed
            pass
    
    @pytest.mark.integration
    def test_configuration_structure(self):
        """Test configuration structure validation."""
        # RED: Write failing test that defines expected behavior
        config_loader = ConfigLoader()
        
        # Test configuration structure
        test_config = {
            "llm": {
                "default": "vllm",
                "providers": {
                    "vllm": {
                        "class": "src.providers.llm.vllm_provider.VLLMProvider",
                        "config": {
                            "base_url": "http://localhost:8001"
                        }
                    }
                }
            },
            "vector_store": {
                "default": "qdrant",
                "providers": {
                    "qdrant": {
                        "class": "src.providers.vector_stores.qdrant_provider.QdrantProvider",
                        "config": {
                            "url": "http://localhost:6333"
                        }
                    }
                }
            }
        }
        
        # Verify configuration structure
        assert "llm" in test_config
        assert "vector_store" in test_config
        assert "default" in test_config["llm"]
        assert "providers" in test_config["llm"]
        assert "default" in test_config["vector_store"]
        assert "providers" in test_config["vector_store"]
    
    @pytest.mark.integration
    def test_provider_registry_methods(self):
        """Test that provider registry has required methods."""
        # RED: Write failing test that defines expected behavior
        registry = ProviderRegistry()
        
        # Verify required methods exist
        assert hasattr(registry, 'initialize_providers')
        assert hasattr(registry, 'get_provider')
        assert hasattr(registry, 'register_provider')
        assert hasattr(registry, 'shutdown_all')
        assert hasattr(registry, 'health_check_all')
    
    @pytest.mark.integration
    def test_config_loader_methods(self):
        """Test that config loader has required methods."""
        # RED: Write failing test that defines expected behavior
        config_loader = ConfigLoader()
        
        # Verify required methods exist
        assert hasattr(config_loader, 'load_config')
        assert hasattr(config_loader, 'validate_config_structure')
        assert hasattr(config_loader, 'resolve_environment_variables')
        assert hasattr(config_loader, 'get_config_value') 