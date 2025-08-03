import pytest
import tempfile
import os
import yaml
from unittest.mock import patch, mock_open
from typing import Dict, Any

from src.config.config_loader import ConfigLoader, ConfigurationError


class TestConfigLoader:
    """Test cases for the configuration loader."""

    def test_config_loader_initialization(self):
        """Test ConfigLoader can be initialized."""
        loader = ConfigLoader()
        assert loader is not None
        assert hasattr(loader, 'load_config')
        assert hasattr(loader, 'resolve_environment_variables')

    def test_load_yaml_config_success(self):
        """Test successful YAML configuration loading."""
        yaml_content = """
        app:
          name: "test-app"
          version: "1.0.0"
        providers:
          llm:
            default: "vllm"
            providers:
              vllm:
                class: "providers.llm.vllm_provider.VLLMProvider"
                config:
                  base_url: "http://localhost:8001"
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
                                        'class': 'providers.llm.vllm_provider.VLLMProvider',
                                        'config': {'base_url': 'http://localhost:8001'}
                                    }
                                }
                            }
                        }
                    }
                    
                    loader = ConfigLoader()
                    config = loader.load_config('test_config.yaml')
                
                assert config['app']['name'] == 'test-app'
                assert config['app']['version'] == '1.0.0'
                assert config['providers']['llm']['default'] == 'vllm'

    def test_load_yaml_config_file_not_found(self):
        """Test handling of missing configuration file."""
        loader = ConfigLoader()
        
        with pytest.raises(ConfigurationError, match="Configuration file not found"):
            loader.load_config('nonexistent.yaml')

    def test_load_yaml_config_invalid_yaml(self):
        """Test handling of invalid YAML content."""
        invalid_yaml = """
        app:
          name: "test-app"
          version: "1.0.0"
        providers:
          llm:
            default: "vllm"
            providers:
              vllm:
                class: "providers.llm.vllm_provider.VLLMProvider"
                config:
                  base_url: "http://localhost:8001"
        invalid: [yaml: content
        """
        
        with patch('os.path.exists', return_value=True):
            with patch('builtins.open', mock_open(read_data=invalid_yaml)):
                with patch('yaml.safe_load') as mock_yaml_load:
                    mock_yaml_load.side_effect = yaml.YAMLError("Invalid YAML")
                    
                    loader = ConfigLoader()
                    
                    with pytest.raises(ConfigurationError, match="Invalid YAML configuration"):
                        loader.load_config('test_config.yaml')

    def test_resolve_environment_variables_simple(self):
        """Test simple environment variable resolution."""
        config = {
            'database': {
                'url': '${DATABASE_URL}',
                'port': '${DB_PORT}'
            }
        }
        
        with patch.dict(os.environ, {
            'DATABASE_URL': 'postgresql://localhost:5432/testdb',
            'DB_PORT': '5432'
        }):
            loader = ConfigLoader()
            resolved_config = loader.resolve_environment_variables(config)
            
            assert resolved_config['database']['url'] == 'postgresql://localhost:5432/testdb'
            assert resolved_config['database']['port'] == '5432'

    def test_resolve_environment_variables_missing(self):
        """Test handling of missing environment variables."""
        config = {
            'api': {
                'key': '${API_KEY}',
                'url': '${API_URL}'
            }
        }
        
        with patch.dict(os.environ, {}, clear=True):
            loader = ConfigLoader()
            
            with pytest.raises(ConfigurationError, match="Environment variable not found"):
                loader.resolve_environment_variables(config)

    def test_resolve_environment_variables_nested(self):
        """Test environment variable resolution in nested structures."""
        config = {
            'providers': {
                'llm': {
                    'vllm': {
                        'config': {
                            'base_url': '${VLLM_BASE_URL}',
                            'model': '${LLM_MODEL_NAME}'
                        }
                    }
                }
            }
        }
        
        with patch.dict(os.environ, {
            'VLLM_BASE_URL': 'http://localhost:8001',
            'LLM_MODEL_NAME': 'llama-2-7b'
        }):
            loader = ConfigLoader()
            resolved_config = loader.resolve_environment_variables(config)
            
            assert resolved_config['providers']['llm']['vllm']['config']['base_url'] == 'http://localhost:8001'
            assert resolved_config['providers']['llm']['vllm']['config']['model'] == 'llama-2-7b'

    def test_resolve_environment_variables_mixed(self):
        """Test mixed content with and without environment variables."""
        config = {
            'app': {
                'name': 'test-app',
                'debug': True,
                'api_url': '${API_URL}',
                'version': '1.0.0'
            }
        }
        
        with patch.dict(os.environ, {'API_URL': 'http://localhost:8000'}):
            loader = ConfigLoader()
            resolved_config = loader.resolve_environment_variables(config)
            
            assert resolved_config['app']['name'] == 'test-app'
            assert resolved_config['app']['debug'] is True
            assert resolved_config['app']['api_url'] == 'http://localhost:8000'
            assert resolved_config['app']['version'] == '1.0.0'

    def test_validate_config_structure_success(self):
        """Test successful configuration validation."""
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
                            'class': 'providers.llm.vllm_provider.VLLMProvider',
                            'config': {
                                'base_url': 'http://localhost:8001'
                            }
                        }
                    }
                }
            }
        }
        
        loader = ConfigLoader()
        # Should not raise any exception
        loader.validate_config_structure(config)

    def test_validate_config_structure_missing_required(self):
        """Test validation failure for missing required sections."""
        config = {
            'app': {
                'name': 'test-app'
            }
            # Missing 'providers' section
        }
        
        loader = ConfigLoader()
        
        with pytest.raises(ConfigurationError, match="Missing required configuration section"):
            loader.validate_config_structure(config)

    def test_validate_config_structure_invalid_provider(self):
        """Test validation failure for invalid provider configuration."""
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
                            # Missing 'class' field
                            'config': {
                                'base_url': 'http://localhost:8001'
                            }
                        }
                    }
                }
            }
        }
        
        loader = ConfigLoader()
        
        with pytest.raises(ConfigurationError, match="Invalid provider configuration"):
            loader.validate_config_structure(config)

    def test_load_and_validate_complete_workflow(self):
        """Test complete workflow: load, resolve env vars, and validate."""
        yaml_content = """
        app:
          name: "test-app"
          version: "1.0.0"
        providers:
          llm:
            default: "vllm"
            providers:
              vllm:
                class: "providers.llm.vllm_provider.VLLMProvider"
                config:
                  base_url: "${VLLM_BASE_URL}"
                  model: "${LLM_MODEL_NAME}"
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
                                        'class': 'providers.llm.vllm_provider.VLLMProvider',
                                        'config': {
                                            'base_url': '${VLLM_BASE_URL}',
                                            'model': '${LLM_MODEL_NAME}'
                                        }
                                    }
                                }
                            }
                        }
                    }
                    
                    with patch.dict(os.environ, {
                        'VLLM_BASE_URL': 'http://localhost:8001',
                        'LLM_MODEL_NAME': 'llama-2-7b'
                    }):
                        loader = ConfigLoader()
                        config = loader.load_config('test_config.yaml')
                        
                        # Should not raise any exception
                        assert config['app']['name'] == 'test-app'
                        assert config['providers']['llm']['providers']['vllm']['config']['base_url'] == 'http://localhost:8001'

    def test_get_config_value_simple(self):
        """Test getting simple configuration values."""
        config = {
            'app': {
                'name': 'test-app',
                'debug': True
            }
        }
        
        loader = ConfigLoader()
        value = loader.get_config_value(config, 'app.name')
        assert value == 'test-app'
        
        value = loader.get_config_value(config, 'app.debug')
        assert value is True

    def test_get_config_value_nested(self):
        """Test getting nested configuration values."""
        config = {
            'providers': {
                'llm': {
                    'default': 'vllm',
                    'providers': {
                        'vllm': {
                            'config': {
                                'base_url': 'http://localhost:8001'
                            }
                        }
                    }
                }
            }
        }
        
        loader = ConfigLoader()
        value = loader.get_config_value(config, 'providers.llm.default')
        assert value == 'vllm'
        
        value = loader.get_config_value(config, 'providers.llm.providers.vllm.config.base_url')
        assert value == 'http://localhost:8001'

    def test_get_config_value_missing(self):
        """Test getting missing configuration values."""
        config = {
            'app': {
                'name': 'test-app'
            }
        }
        
        loader = ConfigLoader()
        
        # Should return None for missing values
        value = loader.get_config_value(config, 'app.missing')
        assert value is None
        
        value = loader.get_config_value(config, 'missing.section')
        assert value is None

    def test_get_config_value_with_default(self):
        """Test getting configuration values with default fallback."""
        config = {
            'app': {
                'name': 'test-app'
            }
        }
        
        loader = ConfigLoader()
        
        # Should return default for missing values
        value = loader.get_config_value(config, 'app.missing', default='default-value')
        assert value == 'default-value'
        
        value = loader.get_config_value(config, 'missing.section', default=42)
        assert value == 42 