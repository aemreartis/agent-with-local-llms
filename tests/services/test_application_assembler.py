import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from typing import Dict, Any

from src.services.application_assembler import ApplicationAssembler, AssemblyError


class TestApplicationAssembler:
    """Test cases for the application assembler."""

    def test_application_assembler_initialization(self):
        """Test ApplicationAssembler can be initialized."""
        assembler = ApplicationAssembler()
        assert assembler is not None
        assert hasattr(assembler, 'assemble_application')
        assert hasattr(assembler, 'wire_orchestrators')
        assert hasattr(assembler, 'create_provider_instances')

    @pytest.mark.asyncio
    async def test_assemble_application_success(self):
        """Test successful application assembly."""
        assembler = ApplicationAssembler()
        
        # Mock configuration
        config = {
            'app': {
                'name': 'test-app',
                'version': '1.0.0'
            },
            'providers': {
                'llm': {
                    'default': 'vllm',
                    'providers': {
                        'vllm': {
                            'class': 'src.providers.llm.vllm_provider.VLLMProvider',
                            'config': {
                                'base_url': 'http://localhost:8001'
                            }
                        }
                    }
                },
                'vector_store': {
                    'default': 'qdrant',
                    'providers': {
                        'qdrant': {
                            'class': 'src.providers.vector_stores.qdrant_provider.QdrantProvider',
                            'config': {
                                'url': 'http://localhost:6333'
                            }
                        }
                    }
                }
            },
            'components': {
                'orchestrators': {
                    'search_orchestrator': {
                        'class': 'src.orchestration.search_orchestrator.SearchOrchestrator',
                        'providers': ['vector_store', 'search_engine']
                    },
                    'query_orchestrator': {
                        'class': 'src.orchestration.query_orchestrator.QueryOrchestrator',
                        'providers': ['llm', 'reranker']
                    },
                    'chat_service': {
                        'class': 'src.orchestration.chat_service.ChatService',
                        'providers': ['memory']
                    }
                }
            }
        }
        
        with patch('src.services.application_assembler.ApplicationAssembler.create_provider_instances') as mock_create_providers:
            with patch('src.services.application_assembler.ApplicationAssembler.wire_orchestrators') as mock_wire_orchestrators:
                mock_create_providers.return_value = {
                    'llm': Mock(),
                    'vector_store': Mock(),
                    'search_engine': Mock(),
                    'reranker': Mock(),
                    'memory': Mock()
                }
                
                mock_wire_orchestrators.return_value = {
                    'search_orchestrator': Mock(),
                    'query_orchestrator': Mock(),
                    'chat_service': Mock()
                }
                
                result = await assembler.assemble_application(config)
                
                assert 'providers' in result
                assert 'orchestrators' in result
                assert 'service_manager' in result
                assert len(result['providers']) == 5
                assert len(result['orchestrators']) == 3

    @pytest.mark.asyncio
    async def test_assemble_application_missing_config(self):
        """Test handling of missing configuration."""
        assembler = ApplicationAssembler()
        
        with pytest.raises(AssemblyError, match="Missing required configuration sections"):
            await assembler.assemble_application({})

    @pytest.mark.asyncio
    async def test_create_provider_instances_success(self):
        """Test successful provider instance creation."""
        assembler = ApplicationAssembler()
        
        providers_config = {
            'llm': {
                'default': 'vllm',
                'providers': {
                    'vllm': {
                        'class': 'src.providers.llm.vllm_provider.VLLMProvider',
                        'config': {
                            'base_url': 'http://localhost:8001'
                        }
                    }
                }
            }
        }
        
        with patch('importlib.import_module') as mock_import:
            mock_module = Mock()
            mock_provider_class = Mock()
            mock_provider_instance = AsyncMock()
            mock_provider_instance.initialize = AsyncMock()
            mock_provider_class.return_value = mock_provider_instance
            mock_module.VLLMProvider = mock_provider_class
            mock_import.return_value = mock_module
            
            providers = await assembler.create_provider_instances(providers_config)
            
            assert 'llm' in providers
            assert providers['llm'] == mock_provider_instance
            mock_provider_instance.initialize.assert_called_once_with({'base_url': 'http://localhost:8001'})

    @pytest.mark.asyncio
    async def test_create_provider_instances_import_error(self):
        """Test handling of provider import errors."""
        assembler = ApplicationAssembler()
        
        providers_config = {
            'llm': {
                'default': 'vllm',
                'providers': {
                    'vllm': {
                        'class': 'src.providers.llm.nonexistent_provider.NonexistentProvider',
                        'config': {}
                    }
                }
            }
        }
        
        with patch('importlib.import_module') as mock_import:
            mock_import.side_effect = ImportError("Module not found")
            
            with pytest.raises(AssemblyError, match="Failed to import provider"):
                await assembler.create_provider_instances(providers_config)

    @pytest.mark.asyncio
    async def test_create_provider_instances_initialization_error(self):
        """Test handling of provider initialization errors."""
        assembler = ApplicationAssembler()
        
        providers_config = {
            'llm': {
                'default': 'vllm',
                'providers': {
                    'vllm': {
                        'class': 'src.providers.llm.vllm_provider.VLLMProvider',
                        'config': {
                            'base_url': 'http://localhost:8001'
                        }
                    }
                }
            }
        }
        
        with patch('importlib.import_module') as mock_import:
            mock_module = Mock()
            mock_provider_class = Mock()
            mock_provider_instance = AsyncMock()
            mock_provider_instance.initialize = AsyncMock(side_effect=Exception("Init failed"))
            mock_provider_class.return_value = mock_provider_instance
            mock_module.VLLMProvider = mock_provider_class
            mock_import.return_value = mock_module
            
            with pytest.raises(AssemblyError, match="Failed to initialize provider"):
                await assembler.create_provider_instances(providers_config)

    @pytest.mark.asyncio
    async def test_wire_orchestrators_success(self):
        """Test successful orchestrator wiring."""
        assembler = ApplicationAssembler()
        
        orchestrators_config = {
            'search_orchestrator': {
                'class': 'src.orchestration.search_orchestrator.SearchOrchestrator',
                'providers': ['vector_store', 'search_engine']
            },
            'query_orchestrator': {
                'class': 'src.orchestration.query_orchestrator.QueryOrchestrator',
                'providers': ['llm', 'reranker']
            }
        }
        
        providers = {
            'vector_store': Mock(),
            'search_engine': Mock(),
            'llm': Mock(),
            'reranker': Mock()
        }
        
        with patch('importlib.import_module') as mock_import:
            mock_module = Mock()
            mock_orchestrator_class = Mock()
            mock_orchestrator_instance = AsyncMock()
            mock_orchestrator_instance.initialize = AsyncMock()
            mock_orchestrator_class.return_value = mock_orchestrator_instance
            mock_module.SearchOrchestrator = mock_orchestrator_class
            mock_module.QueryOrchestrator = mock_orchestrator_class
            mock_import.return_value = mock_module
            
            orchestrators = await assembler.wire_orchestrators(orchestrators_config, providers)
            
            assert 'search_orchestrator' in orchestrators
            assert 'query_orchestrator' in orchestrators
            assert orchestrators['search_orchestrator'] == mock_orchestrator_instance
            assert orchestrators['query_orchestrator'] == mock_orchestrator_instance

    @pytest.mark.asyncio
    async def test_wire_orchestrators_missing_provider(self):
        """Test handling of missing provider dependencies."""
        assembler = ApplicationAssembler()
        
        orchestrators_config = {
            'search_orchestrator': {
                'class': 'src.orchestration.search_orchestrator.SearchOrchestrator',
                'providers': ['vector_store', 'nonexistent_provider']
            }
        }
        
        providers = {
            'vector_store': Mock()
            # Missing 'nonexistent_provider'
        }
        
        with pytest.raises(AssemblyError, match="Provider not found"):
            await assembler.wire_orchestrators(orchestrators_config, providers)

    @pytest.mark.asyncio
    async def test_wire_orchestrators_import_error(self):
        """Test handling of orchestrator import errors."""
        assembler = ApplicationAssembler()
        
        orchestrators_config = {
            'search_orchestrator': {
                'class': 'src.orchestration.nonexistent_orchestrator.NonexistentOrchestrator',
                'providers': ['vector_store']
            }
        }
        
        providers = {
            'vector_store': Mock()
        }
        
        with patch('importlib.import_module') as mock_import:
            mock_import.side_effect = ImportError("Module not found")
            
            with pytest.raises(AssemblyError, match="Failed to import orchestrator"):
                await assembler.wire_orchestrators(orchestrators_config, providers)

    @pytest.mark.asyncio
    async def test_wire_orchestrators_initialization_error(self):
        """Test handling of orchestrator initialization errors."""
        assembler = ApplicationAssembler()
        
        orchestrators_config = {
            'search_orchestrator': {
                'class': 'src.orchestration.search_orchestrator.SearchOrchestrator',
                'providers': ['vector_store']
            }
        }
        
        providers = {
            'vector_store': Mock()
        }
        
        with patch('importlib.import_module') as mock_import:
            mock_module = Mock()
            mock_orchestrator_class = Mock()
            mock_orchestrator_instance = AsyncMock()
            mock_orchestrator_instance.initialize = AsyncMock(side_effect=Exception("Init failed"))
            mock_orchestrator_class.return_value = mock_orchestrator_instance
            mock_module.SearchOrchestrator = mock_orchestrator_class
            mock_import.return_value = mock_module
            
            with pytest.raises(AssemblyError, match="Failed to initialize orchestrator"):
                await assembler.wire_orchestrators(orchestrators_config, providers)

    @pytest.mark.asyncio
    async def test_wire_chat_service_with_dependencies(self):
        """Test wiring ChatService with its dependencies."""
        assembler = ApplicationAssembler()
        
        orchestrators_config = {
            'chat_service': {
                'class': 'src.orchestration.chat_service.ChatService',
                'providers': ['memory'],
                'dependencies': ['query_orchestrator']
            },
            'query_orchestrator': {
                'class': 'src.orchestration.query_orchestrator.QueryOrchestrator',
                'providers': ['llm', 'reranker']
            }
        }
        
        providers = {
            'memory': Mock(),
            'llm': Mock(),
            'reranker': Mock()
        }
        
        with patch('importlib.import_module') as mock_import:
            mock_module = Mock()
            mock_chat_class = Mock()
            mock_query_class = Mock()
            mock_chat_instance = AsyncMock()
            mock_query_instance = AsyncMock()
            mock_chat_instance.initialize = AsyncMock()
            mock_query_instance.initialize = AsyncMock()
            mock_chat_class.return_value = mock_chat_instance
            mock_query_class.return_value = mock_query_instance
            mock_module.ChatService = mock_chat_class
            mock_module.QueryOrchestrator = mock_query_class
            mock_import.return_value = mock_module
            
            orchestrators = await assembler.wire_orchestrators(orchestrators_config, providers)
            
            assert 'chat_service' in orchestrators
            assert 'query_orchestrator' in orchestrators
            # Verify that chat_service has query_orchestrator as dependency
            assert hasattr(mock_chat_instance, 'query_orchestrator')
            assert mock_chat_instance.query_orchestrator == mock_query_instance

    @pytest.mark.asyncio
    async def test_validate_configuration_success(self):
        """Test successful configuration validation."""
        assembler = ApplicationAssembler()
        
        config = {
            'app': {'name': 'test-app'},
            'providers': {
                'llm': {
                    'default': 'vllm',
                    'providers': {
                        'vllm': {
                            'class': 'src.providers.llm.vllm_provider.VLLMProvider',
                            'config': {}
                        }
                    }
                }
            },
            'components': {
                'orchestrators': {
                    'search_orchestrator': {
                        'class': 'src.orchestration.search_orchestrator.SearchOrchestrator',
                        'providers': ['vector_store']
                    }
                }
            }
        }
        
        # Should not raise any exception
        assembler.validate_configuration(config)

    @pytest.mark.asyncio
    async def test_validate_configuration_missing_sections(self):
        """Test validation failure for missing configuration sections."""
        assembler = ApplicationAssembler()
        
        config = {
            'app': {'name': 'test-app'}
            # Missing 'providers' and 'components' sections
        }
        
        with pytest.raises(AssemblyError, match="Missing required configuration sections"):
            assembler.validate_configuration(config)

    @pytest.mark.asyncio
    async def test_validate_configuration_invalid_orchestrator(self):
        """Test validation failure for invalid orchestrator configuration."""
        assembler = ApplicationAssembler()
        
        config = {
            'app': {'name': 'test-app'},
            'providers': {
                'llm': {
                    'default': 'vllm',
                    'providers': {
                        'vllm': {
                            'class': 'src.providers.llm.vllm_provider.VLLMProvider',
                            'config': {}
                        }
                    }
                }
            },
            'components': {
                'orchestrators': {
                    'search_orchestrator': {
                        # Missing 'class' field
                        'providers': ['vector_store']
                    }
                }
            }
        }
        
        with pytest.raises(AssemblyError, match="Invalid orchestrator configuration"):
            assembler.validate_configuration(config)

    def test_get_assembly_info(self):
        """Test getting assembly information."""
        assembler = ApplicationAssembler()
        
        info = assembler.get_assembly_info()
        
        assert "assembler_name" in info
        assert "version" in info
        assert "capabilities" in info
        assert "supported_providers" in info
        assert "supported_orchestrators" in info 