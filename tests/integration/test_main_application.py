import pytest
import asyncio
import tempfile
import os
from unittest.mock import Mock, AsyncMock, patch, mock_open
from typing import Dict, Any

from src.main import Application, ApplicationError


class TestApplication:
    """Test cases for the main application."""

    def test_application_initialization(self):
        """Test Application can be initialized."""
        app = Application()
        assert app is not None
        assert hasattr(app, 'start')
        assert hasattr(app, 'stop')
        assert hasattr(app, 'health_check')

    @pytest.mark.asyncio
    async def test_application_start_success(self):
        """Test successful application startup."""
        app = Application()
        
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
        
        with patch('src.main.Application._load_configuration') as mock_load_config:
            with patch('src.main.Application._assemble_application') as mock_assemble:
                with patch('src.main.Application._start_services') as mock_start_services:
                    mock_load_config.return_value = config
                    mock_assemble.return_value = {
                        'providers': {'llm': Mock()},
                        'orchestrators': {'search_orchestrator': Mock()},
                        'service_manager': Mock()
                    }
                    
                    await app.start('test_config.yaml')
                    
                    mock_load_config.assert_called_once_with('test_config.yaml')
                    mock_assemble.assert_called_once_with(config)
                    mock_start_services.assert_called_once()

    @pytest.mark.asyncio
    async def test_application_start_config_not_found(self):
        """Test handling of missing configuration file."""
        app = Application()
        
        with patch('src.main.Application._load_configuration') as mock_load_config:
            mock_load_config.side_effect = FileNotFoundError("Config file not found")
            
            with pytest.raises(ApplicationError, match="Failed to start application"):
                await app.start('nonexistent.yaml')

    @pytest.mark.asyncio
    async def test_application_start_assembly_failure(self):
        """Test handling of assembly failure."""
        app = Application()
        
        config = {'app': {'name': 'test'}}
        
        with patch('src.main.Application._load_configuration') as mock_load_config:
            with patch('src.main.Application._assemble_application') as mock_assemble:
                mock_load_config.return_value = config
                mock_assemble.side_effect = Exception("Assembly failed")
                
                with pytest.raises(ApplicationError, match="Failed to start application"):
                    await app.start('test_config.yaml')

    @pytest.mark.asyncio
    async def test_application_stop_success(self):
        """Test successful application shutdown."""
        app = Application()
        
        # Mock service manager
        mock_service_manager = AsyncMock()
        app._service_manager = mock_service_manager
        
        await app.stop()
        
        mock_service_manager.stop_all_services.assert_called_once()

    @pytest.mark.asyncio
    async def test_application_stop_no_service_manager(self):
        """Test application shutdown when no service manager exists."""
        app = Application()
        
        # Should not raise any exception
        await app.stop()

    @pytest.mark.asyncio
    async def test_application_health_check_success(self):
        """Test successful health check."""
        app = Application()
        
        # Mock service manager
        mock_service_manager = AsyncMock()
        mock_service_manager.health_check_all_services.return_value = {
            'search_orchestrator': {'status': 'healthy'},
            'query_orchestrator': {'status': 'healthy'}
        }
        app._service_manager = mock_service_manager
        
        health_status = await app.health_check()
        
        assert 'overall_health' in health_status
        assert 'services' in health_status
        assert health_status['overall_health'] is True
        assert len(health_status['services']) == 2

    @pytest.mark.asyncio
    async def test_application_health_check_unhealthy(self):
        """Test health check with unhealthy services."""
        app = Application()
        
        # Mock service manager
        mock_service_manager = AsyncMock()
        mock_service_manager.health_check_all_services.return_value = {
            'search_orchestrator': {'status': 'healthy'},
            'query_orchestrator': {'status': 'unhealthy'}
        }
        app._service_manager = mock_service_manager
        
        health_status = await app.health_check()
        
        assert health_status['overall_health'] is False

    @pytest.mark.asyncio
    async def test_application_health_check_no_service_manager(self):
        """Test health check when no service manager exists."""
        app = Application()
        
        health_status = await app.health_check()
        
        assert health_status['overall_health'] is False
        assert health_status['services'] == {}

    @pytest.mark.asyncio
    async def test_load_configuration_success(self):
        """Test successful configuration loading."""
        app = Application()
        
        yaml_content = """
        app:
          name: "test-app"
          version: "1.0.0"
        providers:
          llm:
            default: "vllm"
            providers:
              vllm:
                class: "src.providers.llm.vllm_provider.VLLMProvider"
                config:
                  base_url: "http://localhost:8001"
        components:
          orchestrators:
            search_orchestrator:
              class: "src.orchestration.search_orchestrator.SearchOrchestrator"
              providers: ["vector_store"]
        """
        
        with patch('os.path.exists', return_value=True):
            with patch('builtins.open', mock_open(read_data=yaml_content)):
                with patch('yaml.safe_load') as mock_yaml_load:
                    mock_yaml_load.return_value = {
                        'app': {'name': 'test-app', 'version': '1.0.0'},
                        'providers': {
                            'llm': {
                                'default': 'vllm',
                                'providers': {
                                    'vllm': {
                                        'class': 'src.providers.llm.vllm_provider.VLLMProvider',
                                        'config': {'base_url': 'http://localhost:8001'}
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
                    
                    config = await app._load_configuration('test_config.yaml')
                    
                    assert config['app']['name'] == 'test-app'
                    assert 'providers' in config
                    assert 'components' in config

    @pytest.mark.asyncio
    async def test_load_configuration_file_not_found(self):
        """Test handling of missing configuration file."""
        app = Application()
        
        with patch('builtins.open') as mock_open:
            mock_open.side_effect = FileNotFoundError("File not found")
            
            with pytest.raises(ApplicationError, match="Configuration file not found"):
                await app._load_configuration('nonexistent.yaml')

    @pytest.mark.asyncio
    async def test_assemble_application_success(self):
        """Test successful application assembly."""
        app = Application()
        
        config = {
            'app': {'name': 'test-app'},
            'providers': {
                'llm': {
                    'default': 'vllm',
                    'providers': {
                        'vllm': {
                            'class': 'src.providers.llm.vllm_provider.VLLMProvider',
                            'config': {'base_url': 'http://localhost:8001'}
                        }
                    }
                },
                'vector_store': {
                    'default': 'qdrant',
                    'providers': {
                        'qdrant': {
                            'class': 'src.providers.vector_stores.qdrant_provider.QdrantProvider',
                            'config': {'url': 'http://localhost:6333'}
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
        
        # Mock the entire assembly process
        with patch('src.services.application_assembler.ApplicationAssembler.assemble_application') as mock_assemble:
            mock_assemble.return_value = {
                'providers': {'llm': Mock(), 'vector_store': Mock()},
                'orchestrators': {'search_orchestrator': Mock()},
                'service_manager': Mock()
            }
            
            result = await app._assemble_application(config)
            
            assert 'providers' in result
            assert 'orchestrators' in result
            assert 'service_manager' in result
            mock_assemble.assert_called_once_with(config)

    @pytest.mark.asyncio
    async def test_start_services_success(self):
        """Test successful service startup."""
        app = Application()
        
        # Mock service manager
        mock_service_manager = AsyncMock()
        app._service_manager = mock_service_manager
        
        await app._start_services()
        
        mock_service_manager.start_all_services.assert_called_once()

    @pytest.mark.asyncio
    async def test_start_services_failure(self):
        """Test handling of service startup failure."""
        app = Application()
        
        # Mock service manager
        mock_service_manager = AsyncMock()
        mock_service_manager.start_all_services.side_effect = Exception("Startup failed")
        app._service_manager = mock_service_manager
        
        with pytest.raises(ApplicationError, match="Failed to start services"):
            await app._start_services()

    def test_get_application_info(self):
        """Test getting application information."""
        app = Application()
        
        info = app.get_application_info()
        
        assert "app_name" in info
        assert "version" in info
        assert "status" in info
        assert "started_at" in info
        assert "uptime_seconds" in info

    @pytest.mark.asyncio
    async def test_application_lifecycle_workflow(self):
        """Test complete application lifecycle workflow."""
        app = Application()
        
        # Mock configuration
        config = {
            'app': {'name': 'test-app'},
            'providers': {
                'llm': {
                    'default': 'vllm',
                    'providers': {
                        'vllm': {
                            'class': 'src.providers.llm.vllm_provider.VLLMProvider',
                            'config': {'base_url': 'http://localhost:8001'}
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
        
        with patch('src.main.Application._load_configuration') as mock_load_config:
            with patch('src.main.Application._assemble_application') as mock_assemble:
                with patch('src.main.Application._start_services') as mock_start_services:
                    mock_load_config.return_value = config
                    mock_assemble.return_value = {
                        'providers': {'llm': Mock()},
                        'orchestrators': {'search_orchestrator': Mock()},
                        'service_manager': Mock()
                    }
                    
                    # Start application
                    await app.start('test_config.yaml')
                    
                    # Check health
                    health_status = await app.health_check()
                    assert 'overall_health' in health_status
                    
                    # Stop application
                    await app.stop()
                    
                    # Verify all methods were called
                    mock_load_config.assert_called_once()
                    mock_assemble.assert_called_once()
                    mock_start_services.assert_called_once() 