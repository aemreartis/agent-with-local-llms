import os
import re
from typing import Dict, Any, Optional
import yaml


class ConfigurationError(Exception):
    """Exception raised for configuration-related errors."""
    pass


class ConfigLoader:
    """Loads and validates configuration files with environment variable resolution."""
    
    def __init__(self):
        """Initialize the configuration loader."""
        pass
    
    def load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from YAML file with environment variable resolution."""
        try:
            if not os.path.exists(config_path):
                raise ConfigurationError(f"Configuration file not found: {config_path}")
            
            with open(config_path, 'r', encoding='utf-8') as file:
                config = yaml.safe_load(file)
            
            if config is None:
                raise ConfigurationError("Empty configuration file")
            
            # Resolve environment variables
            config = self.resolve_environment_variables(config)
            
            # Validate configuration structure
            self.validate_config_structure(config)
            
            return config
            
        except yaml.YAMLError as e:
            raise ConfigurationError(f"Invalid YAML configuration: {str(e)}")
        except Exception as e:
            if isinstance(e, ConfigurationError):
                raise
            raise ConfigurationError(f"Error loading configuration: {str(e)}")
    
    def resolve_environment_variables(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively resolve environment variables in configuration."""
        if isinstance(config, dict):
            resolved = {}
            for key, value in config.items():
                resolved[key] = self.resolve_environment_variables(value)
            return resolved
        elif isinstance(config, list):
            return [self.resolve_environment_variables(item) for item in config]
        elif isinstance(config, str):
            return self._resolve_string_variables(config)
        else:
            return config
    
    def _resolve_string_variables(self, value: str) -> str:
        """Resolve environment variables in a string value."""
        if not isinstance(value, str):
            return value
        
        # Pattern to match ${VAR_NAME} or $VAR_NAME
        pattern = r'\$\{([^}]+)\}|\$([a-zA-Z_][a-zA-Z0-9_]*)'
        
        def replace_var(match):
            var_name = match.group(1) or match.group(2)
            if var_name in os.environ:
                return os.environ[var_name]
            else:
                raise ConfigurationError(f"Environment variable not found: {var_name}")
        
        return re.sub(pattern, replace_var, value)
    
    def validate_config_structure(self, config: Dict[str, Any]) -> None:
        """Validate the configuration structure."""
        if not isinstance(config, dict):
            raise ConfigurationError("Configuration must be a dictionary")
        
        # Check for required sections
        required_sections = ['app', 'providers']
        for section in required_sections:
            if section not in config:
                raise ConfigurationError(f"Missing required configuration section: {section}")
        
        # Validate providers section
        providers = config.get('providers', {})
        if not isinstance(providers, dict):
            raise ConfigurationError("Providers section must be a dictionary")
        
        # Validate each provider category
        for category, category_config in providers.items():
            if not isinstance(category_config, dict):
                raise ConfigurationError(f"Provider category '{category}' must be a dictionary")
            
            # Check for required fields in provider category
            if 'default' not in category_config:
                raise ConfigurationError(f"Provider category '{category}' missing 'default' field")
            
            if 'providers' not in category_config:
                raise ConfigurationError(f"Provider category '{category}' missing 'providers' field")
            
            # Validate individual providers
            providers_list = category_config.get('providers', {})
            if not isinstance(providers_list, dict):
                raise ConfigurationError(f"Providers in category '{category}' must be a dictionary")
            
            for provider_name, provider_config in providers_list.items():
                if not isinstance(provider_config, dict):
                    raise ConfigurationError(f"Provider '{provider_name}' configuration must be a dictionary")
                
                # Check for required fields in provider config
                if 'class' not in provider_config:
                    raise ConfigurationError(f"Invalid provider configuration: missing 'class' field in '{provider_name}'")
                
                if 'config' not in provider_config:
                    raise ConfigurationError(f"Invalid provider configuration: missing 'config' field in '{provider_name}'")
    
    def get_config_value(self, config: Dict[str, Any], path: str, default: Any = None) -> Any:
        """Get a configuration value using dot notation path."""
        if not path:
            return config
        
        keys = path.split('.')
        current = config
        
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return default
        
        return current 