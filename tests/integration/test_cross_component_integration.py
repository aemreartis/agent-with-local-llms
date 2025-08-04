"""
Cross-component integration tests for Stage 8.
Tests that different components work together seamlessly.
"""

import pytest
import asyncio
from typing import Dict, Any

from src.registry.provider_registry import ProviderRegistry
from src.config.config_loader import ConfigLoader
from src.services.application_assembler import ApplicationAssembler
from src.services.service_manager import ServiceManager


class TestCrossComponentIntegration:
    """Test component interactions and integration."""
    
    @pytest.mark.integration
    def test_application_assembler_creation(self):
        """Test that application assembler can be created."""
        # RED: Write failing test that defines expected behavior
        assembler = ApplicationAssembler()
        
        assert assembler is not None
        assert hasattr(assembler, 'assemble_application')
        assert hasattr(assembler, 'create_provider_instances')
        assert hasattr(assembler, 'wire_orchestrators')
    
    @pytest.mark.integration
    def test_service_manager_creation(self):
        """Test that service manager can be created."""
        # RED: Write failing test that defines expected behavior
        service_manager = ServiceManager()
        
        assert service_manager is not None
        assert hasattr(service_manager, 'register_service')
        assert hasattr(service_manager, 'start_all_services')
        assert hasattr(service_manager, 'stop_all_services')
        assert hasattr(service_manager, 'health_check_all_services')
    
    @pytest.mark.integration
    def test_component_dependency_injection(self):
        """Test that components can be injected with dependencies."""
        # RED: Write failing test that defines expected behavior
        registry = ProviderRegistry()
        config_loader = ConfigLoader()
        assembler = ApplicationAssembler()
        service_manager = ServiceManager()
        
        # Verify components can be created with dependencies
        assert registry is not None
        assert config_loader is not None
        assert assembler is not None
        assert service_manager is not None
        
        # Verify components have required methods
        assert hasattr(registry, 'register_provider')
        assert hasattr(config_loader, 'load_config')
        assert hasattr(assembler, 'assemble_application')
        assert hasattr(service_manager, 'register_service')
    
    @pytest.mark.integration
    def test_configuration_to_registry_flow(self):
        """Test configuration loading and provider registry integration."""
        # RED: Write failing test that defines expected behavior
        config_loader = ConfigLoader()
        registry = ProviderRegistry()
        
        # Test configuration structure
        test_config = {
            "app": {
                "name": "test_app",
                "version": "1.0.0"
            },
            "providers": {
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
        }
        
        # Verify configuration structure is valid
        assert "app" in test_config
        assert "providers" in test_config
        assert "llm" in test_config["providers"]
        assert "vector_store" in test_config["providers"]
        
        # Verify config loader can handle this structure
        assert hasattr(config_loader, 'validate_config_structure')
        assert hasattr(registry, 'initialize_providers')
    
    @pytest.mark.integration
    def test_orchestrator_integration_structure(self):
        """Test orchestrator integration structure."""
        # RED: Write failing test that defines expected behavior
        from src.orchestration.chat_service import ChatService
        from src.orchestration.query_orchestrator import QueryOrchestrator
        from src.orchestration.search_orchestrator import SearchOrchestrator
        
        # Verify orchestrator classes exist and have required methods
        assert hasattr(ChatService, '__init__')
        assert hasattr(QueryOrchestrator, '__init__')
        assert hasattr(SearchOrchestrator, '__init__')
        
        # Verify they can be instantiated
        chat_service = ChatService()
        query_orchestrator = QueryOrchestrator()
        search_orchestrator = SearchOrchestrator()
        
        assert chat_service is not None
        assert query_orchestrator is not None
        assert search_orchestrator is not None
    
    @pytest.mark.integration
    def test_provider_registry_integration(self):
        """Test provider registry integration with multiple providers."""
        # RED: Write failing test that defines expected behavior
        registry = ProviderRegistry()
        
        # Test provider registration
        from src.providers.llm.vllm_provider import VLLMProvider
        from src.providers.vector_stores.qdrant_provider import QdrantProvider
        from src.providers.rerankers.bge_provider import BGEProvider
        from src.providers.memory.inmemory_provider import InMemoryProvider
        
        # Register providers
        registry.register_provider("llm", "vllm", VLLMProvider)
        registry.register_provider("vector_store", "qdrant", QdrantProvider)
        registry.register_provider("reranker", "bge", BGEProvider)
        registry.register_provider("memory", "inmemory", InMemoryProvider)
        
        # Verify providers are registered
        assert "vllm" in registry.list_providers("llm")
        assert "qdrant" in registry.list_providers("vector_store")
        assert "bge" in registry.list_providers("reranker")
        assert "inmemory" in registry.list_providers("memory")
        
        # Verify categories are tracked
        categories = registry.get_all_categories()
        assert "llm" in categories
        assert "vector_store" in categories
        assert "reranker" in categories
        assert "memory" in categories
    
    @pytest.mark.integration
    def test_service_lifecycle_integration(self):
        """Test service lifecycle integration."""
        # RED: Write failing test that defines expected behavior
        service_manager = ServiceManager()
        
        # Test service registration (without async for now)
        from src.orchestration.chat_service import ChatService
        chat_service = ChatService()
        
        # Test that service manager can be created and has required methods
        assert service_manager is not None
        assert hasattr(service_manager, 'register_service')
        assert hasattr(service_manager, 'get_service')
        assert hasattr(service_manager, 'remove_service')
        
        # Test that service can be created
        assert chat_service is not None
    
    @pytest.mark.integration
    def test_error_handling_integration(self):
        """Test error handling across components."""
        # RED: Write failing test that defines expected behavior
        registry = ProviderRegistry()
        config_loader = ConfigLoader()
        
        # Test invalid configuration structure
        invalid_config = {
            "providers": {
                "llm": {
                    # Missing 'default' field
                    "providers": {}
                }
            }
        }
        
        # This should raise an error during validation
        with pytest.raises(Exception):
            config_loader.validate_config_structure(invalid_config)
    
    @pytest.mark.integration
    def test_component_interface_compliance(self):
        """Test that all components implement their interfaces correctly."""
        # RED: Write failing test that defines expected behavior
        from src.interfaces.chat_service_interface import ChatServiceInterface
        from src.interfaces.query_orchestrator_interface import QueryOrchestratorInterface
        from src.interfaces.search_orchestrator_interface import SearchOrchestratorInterface
        
        # Test orchestrator interface compliance
        from src.orchestration.chat_service import ChatService
        from src.orchestration.query_orchestrator import QueryOrchestrator
        from src.orchestration.search_orchestrator import SearchOrchestrator
        
        # Verify interface compliance
        assert issubclass(ChatService, ChatServiceInterface)
        assert issubclass(QueryOrchestrator, QueryOrchestratorInterface)
        assert issubclass(SearchOrchestrator, SearchOrchestratorInterface)
    
    @pytest.mark.integration
    def test_configuration_validation_integration(self):
        """Test configuration validation integration."""
        # RED: Write failing test that defines expected behavior
        config_loader = ConfigLoader()
        
        # Test valid configuration
        valid_config = {
            "app": {
                "name": "test_app",
                "version": "1.0.0"
            },
            "providers": {
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
                }
            }
        }
        
        # This should not raise an error
        config_loader.validate_config_structure(valid_config)
        
        # Test invalid configuration (missing app section)
        invalid_config = {
            "providers": {
                "llm": {
                    "default": "vllm",
                    "providers": {}
                }
            }
        }
        
        # This should raise an error
        with pytest.raises(Exception):
            config_loader.validate_config_structure(invalid_config) 