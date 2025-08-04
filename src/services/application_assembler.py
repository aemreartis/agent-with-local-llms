import importlib
import logging
from typing import Dict, Any, Optional

from .service_manager import ServiceManager

logger = logging.getLogger(__name__)


class AssemblyError(Exception):
    """Exception raised for application assembly errors."""
    pass


class ApplicationAssembler:
    """Assembles the complete application from configuration."""
    
    def __init__(self):
        """Initialize the application assembler."""
        pass
    
    async def assemble_application(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Assemble the complete application from configuration."""
        try:
            # Validate configuration
            self.validate_configuration(config)
            
            # Create provider instances
            providers = await self.create_provider_instances(config.get('providers', {}))
            
            # Wire orchestrators
            orchestrators_config = config.get('components', {}).get('orchestrators', {})
            orchestrators = await self.wire_orchestrators(orchestrators_config, providers)
            
            # Create service manager
            service_manager = ServiceManager()
            
            # Register all orchestrators with service manager
            for name, orchestrator in orchestrators.items():
                await service_manager.register_service(name, orchestrator)
            
            return {
                'providers': providers,
                'orchestrators': orchestrators,
                'service_manager': service_manager
            }
            
        except Exception as e:
            if isinstance(e, AssemblyError):
                raise
            raise AssemblyError(f"Assembly failed: {str(e)}")
    
    async def create_provider_instances(self, providers_config: Dict[str, Any]) -> Dict[str, Any]:
        """Create provider instances from configuration."""
        providers = {}
        
        for category, category_config in providers_config.items():
            try:
                # Get default provider name
                default_provider = category_config.get('default')
                if not default_provider:
                    raise AssemblyError(f"No default provider specified for category: {category}")
                
                # Get provider configuration
                provider_config = category_config.get('providers', {}).get(default_provider)
                if not provider_config:
                    raise AssemblyError(f"Provider configuration not found: {default_provider}")
                
                # Import and instantiate provider
                provider_class_path = provider_config.get('class')
                if not provider_class_path:
                    raise AssemblyError(f"No class specified for provider: {default_provider}")
                
                provider_instance = await self._create_provider_instance(provider_class_path, provider_config.get('config', {}))
                providers[category] = provider_instance
                
                logger.info(f"Created provider instance: {category} -> {default_provider}")
                
            except Exception as e:
                if isinstance(e, AssemblyError):
                    raise
                raise AssemblyError(f"Failed to create provider {category}: {str(e)}")
        
        return providers
    
    async def _create_provider_instance(self, class_path: str, config: Dict[str, Any]):
        """Create a single provider instance."""
        try:
            # Import the module and class
            module_path, class_name = class_path.rsplit('.', 1)
            module = importlib.import_module(module_path)
            provider_class = getattr(module, class_name)
            
            # Create instance
            instance = provider_class()
            
            # Initialize if the instance has an initialize method
            if hasattr(instance, 'initialize') and callable(instance.initialize):
                await instance.initialize(config)
            
            return instance
            
        except ImportError as e:
            raise AssemblyError(f"Failed to import provider: {str(e)}")
        except Exception as e:
            raise AssemblyError(f"Failed to initialize provider: {str(e)}")
    
    async def wire_orchestrators(self, orchestrators_config: Dict[str, Any], providers: Dict[str, Any]) -> Dict[str, Any]:
        """Wire orchestrators with their dependencies."""
        orchestrators = {}
        
        # First pass: create all orchestrator instances
        orchestrator_instances = {}
        for name, orchestrator_config in orchestrators_config.items():
            try:
                class_path = orchestrator_config.get('class')
                if not class_path:
                    raise AssemblyError(f"No class specified for orchestrator: {name}")
                
                orchestrator_instance = await self._create_orchestrator_instance(class_path, orchestrator_config.get('config', {}))
                orchestrator_instances[name] = orchestrator_instance
                
            except Exception as e:
                if isinstance(e, AssemblyError):
                    raise
                raise AssemblyError(f"Failed to create orchestrator {name}: {str(e)}")
        
        # Second pass: wire dependencies
        for name, orchestrator_config in orchestrators_config.items():
            try:
                orchestrator_instance = orchestrator_instances[name]
                
                # Wire provider dependencies
                required_providers = orchestrator_config.get('providers', [])
                for provider_name in required_providers:
                    if provider_name not in providers:
                        raise AssemblyError(f"Provider not found: {provider_name}")
                    
                    # Set provider as attribute on orchestrator
                    setattr(orchestrator_instance, provider_name, providers[provider_name])
                
                # Wire orchestrator dependencies
                dependencies = orchestrator_config.get('dependencies', [])
                for dep_name in dependencies:
                    if dep_name not in orchestrator_instances:
                        raise AssemblyError(f"Orchestrator dependency not found: {dep_name}")
                    
                    # Set dependency as attribute on orchestrator
                    setattr(orchestrator_instance, dep_name, orchestrator_instances[dep_name])
                
                orchestrators[name] = orchestrator_instance
                logger.info(f"Wired orchestrator: {name}")
                
            except Exception as e:
                if isinstance(e, AssemblyError):
                    raise
                raise AssemblyError(f"Failed to wire orchestrator {name}: {str(e)}")
        
        return orchestrators
    
    async def _create_orchestrator_instance(self, class_path: str, config: Dict[str, Any]):
        """Create a single orchestrator instance."""
        try:
            # Import the module and class
            module_path, class_name = class_path.rsplit('.', 1)
            module = importlib.import_module(module_path)
            orchestrator_class = getattr(module, class_name)
            
            # Create instance
            instance = orchestrator_class()
            
            # Initialize if the instance has an initialize method
            if hasattr(instance, 'initialize') and callable(instance.initialize):
                await instance.initialize(config)
            
            return instance
            
        except ImportError as e:
            raise AssemblyError(f"Failed to import orchestrator: {str(e)}")
        except Exception as e:
            raise AssemblyError(f"Failed to initialize orchestrator: {str(e)}")
    
    def validate_configuration(self, config: Dict[str, Any]) -> None:
        """Validate the configuration structure."""
        if not isinstance(config, dict):
            raise AssemblyError("Configuration must be a dictionary")
        
        # Check for required sections
        required_sections = ['app', 'providers', 'components']
        for section in required_sections:
            if section not in config:
                raise AssemblyError(f"Missing required configuration sections: {section}")
        
        # Validate providers section
        providers = config.get('providers', {})
        if not isinstance(providers, dict):
            raise AssemblyError("Providers section must be a dictionary")
        
        for category, category_config in providers.items():
            if not isinstance(category_config, dict):
                raise AssemblyError(f"Provider category '{category}' must be a dictionary")
            
            if 'default' not in category_config:
                raise AssemblyError(f"Provider category '{category}' missing 'default' field")
            
            if 'providers' not in category_config:
                raise AssemblyError(f"Provider category '{category}' missing 'providers' field")
            
            providers_list = category_config.get('providers', {})
            if not isinstance(providers_list, dict):
                raise AssemblyError(f"Providers in category '{category}' must be a dictionary")
            
            for provider_name, provider_config in providers_list.items():
                if not isinstance(provider_config, dict):
                    raise AssemblyError(f"Provider '{provider_name}' configuration must be a dictionary")
                
                if 'class' not in provider_config:
                    raise AssemblyError(f"Invalid provider configuration: missing 'class' field in '{provider_name}'")
        
        # Validate components section
        components = config.get('components', {})
        if not isinstance(components, dict):
            raise AssemblyError("Components section must be a dictionary")
        
        orchestrators = components.get('orchestrators', {})
        if not isinstance(orchestrators, dict):
            raise AssemblyError("Orchestrators section must be a dictionary")
        
        for orchestrator_name, orchestrator_config in orchestrators.items():
            if not isinstance(orchestrator_config, dict):
                raise AssemblyError(f"Orchestrator '{orchestrator_name}' configuration must be a dictionary")
            
            if 'class' not in orchestrator_config:
                raise AssemblyError(f"Invalid orchestrator configuration: missing 'class' field in '{orchestrator_name}'")
            
            if 'providers' not in orchestrator_config:
                raise AssemblyError(f"Invalid orchestrator configuration: missing 'providers' field in '{orchestrator_name}'")
    
    def get_assembly_info(self) -> Dict[str, Any]:
        """Get information about the application assembler."""
        return {
            "assembler_name": "ApplicationAssembler",
            "version": "1.0.0",
            "capabilities": [
                "provider_instantiation",
                "orchestrator_wiring",
                "dependency_resolution",
                "configuration_validation",
                "service_manager_integration"
            ],
            "supported_providers": [
                "llm",
                "vector_store", 
                "search_engine",
                "reranker",
                "memory"
            ],
            "supported_orchestrators": [
                "search_orchestrator",
                "query_orchestrator", 
                "chat_service"
            ]
        }
    
    async def initialize(self) -> None:
        """Initialize the application assembler with default configuration."""
        # Mock initialization for API testing
        pass
    
    def get_chat_service(self):
        """Get chat service instance."""
        # Mock implementation for API testing
        from src.orchestration.chat_service import ChatService
        return ChatService()
    
    def get_query_orchestrator(self):
        """Get query orchestrator instance."""
        # Mock implementation for API testing
        from src.orchestration.query_orchestrator import QueryOrchestrator
        return QueryOrchestrator()
    
    def get_search_orchestrator(self):
        """Get search orchestrator instance."""
        # Mock implementation for API testing
        from src.orchestration.search_orchestrator import SearchOrchestrator
        return SearchOrchestrator()
    
    def get_agent_orchestrator(self):
        """Get agent orchestrator instance."""
        # Mock implementation for API testing
        from src.agents.agent_orchestrator import AgentOrchestrator
        return AgentOrchestrator()
    
    def get_document_pipeline(self):
        """Get document pipeline instance."""
        # Mock implementation for API testing
        from src.providers.document.document_pipeline import DocumentPipeline
        return DocumentPipeline() 