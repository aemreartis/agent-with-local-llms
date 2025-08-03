from typing import Dict, List, Any, Optional, Type
import asyncio
import importlib
from abc import ABC


class ProviderRegistry:
    """Central registry for managing all providers in the system.
    
    Handles provider registration, instantiation, initialization,
    and lifecycle management for all component types.
    """
    
    def __init__(self):
        """Initialize the provider registry."""
        self._provider_classes: Dict[str, Type] = {}  # category:name -> class
        self._provider_instances: Dict[str, Any] = {}  # category:name -> instance
        self._provider_configs: Dict[str, Dict[str, Any]] = {}  # category:name -> config
        self._categories: Dict[str, List[str]] = {}  # category -> [names]
    
    def register_provider(self, category: str, name: str, provider_class: Type) -> None:
        """Register a provider class for later instantiation.
        
        Args:
            category: Provider category (e.g., 'llm', 'vector_store')
            name: Provider name (e.g., 'vllm', 'qdrant')
            provider_class: The provider class to register
            
        Example:
            registry.register_provider("llm", "vllm", VLLMProvider)
        """
        key = f"{category}:{name}"
        self._provider_classes[key] = provider_class
        
        # Track categories and names
        if category not in self._categories:
            self._categories[category] = []
        if name not in self._categories[category]:
            self._categories[category].append(name)
    
    async def get_provider(self, category: str, name: Optional[str] = None, config: Optional[Dict[str, Any]] = None) -> Any:
        """Get an initialized provider instance.
        
        Args:
            category: Provider category (e.g., 'llm', 'vector_store')
            name: Provider name (e.g., 'vllm', 'qdrant'). If None, uses first available.
            config: Configuration for provider initialization
            
        Returns:
            Initialized provider instance
            
        Raises:
            KeyError: If provider not found
            Exception: If provider initialization fails
        """
        # Use first available provider if name not specified
        if name is None:
            if category not in self._categories or not self._categories[category]:
                raise KeyError(f"No providers registered for category '{category}'")
            name = self._categories[category][0]
        
        key = f"{category}:{name}"
        
        # Return existing instance if already initialized
        if key in self._provider_instances:
            return self._provider_instances[key]
        
        # Get provider class
        if key not in self._provider_classes:
            raise KeyError(f"Provider '{name}' not found in category '{category}'")
        
        provider_class = self._provider_classes[key]
        
        # Instantiate provider
        provider_instance = provider_class()
        
        # Initialize provider if config provided or stored
        if config is not None:
            self._provider_configs[key] = config
        
        if key in self._provider_configs:
            await provider_instance.initialize(self._provider_configs[key])
        
        # Store initialized instance
        self._provider_instances[key] = provider_instance
        
        return provider_instance
    
    def list_providers(self, category: str) -> List[str]:
        """List all registered provider names for a category.
        
        Args:
            category: Provider category to list
            
        Returns:
            List of provider names in the category
        """
        return self._categories.get(category, []).copy()
    
    async def initialize_providers(self, configs: Dict[str, Dict[str, Any]]) -> None:
        """Initialize multiple providers with their configurations.
        
        Args:
            configs: Nested dict of {category: {name: config}}
            
        Example:
            configs = {
                "llm": {
                    "vllm": {"base_url": "http://localhost:8000", "model": "llama-2-7b"}
                },
                "vector_store": {
                    "qdrant": {"url": "http://localhost:6333", "collection": "documents"}
                }
            }
        """
        # Store configs for later use
        for category, category_configs in configs.items():
            for name, config in category_configs.items():
                key = f"{category}:{name}"
                self._provider_configs[key] = config
        
        # Initialize providers concurrently
        initialization_tasks = []
        for category, category_configs in configs.items():
            for name in category_configs.keys():
                task = self.get_provider(category, name)
                initialization_tasks.append(task)
        
        if initialization_tasks:
            await asyncio.gather(*initialization_tasks, return_exceptions=True)
    
    async def health_check_all(self) -> Dict[str, bool]:
        """Check health of all initialized providers.
        
        Returns:
            Dict mapping provider keys to health status
        """
        health_results = {}
        
        health_check_tasks = []
        provider_keys = []
        
        for key, provider in self._provider_instances.items():
            if hasattr(provider, 'health_check'):
                health_check_tasks.append(provider.health_check())
                provider_keys.append(key)
        
        if health_check_tasks:
            results = await asyncio.gather(*health_check_tasks, return_exceptions=True)
            
            for key, result in zip(provider_keys, results):
                if isinstance(result, Exception):
                    health_results[key] = False
                else:
                    health_results[key] = bool(result)
        
        return health_results
    
    def get_all_categories(self) -> List[str]:
        """Get all registered provider categories.
        
        Returns:
            List of category names
        """
        return list(self._categories.keys())
    
    def get_provider_info(self, category: str, name: str) -> Optional[Dict[str, Any]]:
        """Get information about a registered provider.
        
        Args:
            category: Provider category
            name: Provider name
            
        Returns:
            Provider info dict or None if not found
        """
        key = f"{category}:{name}"
        if key in self._provider_instances:
            provider = self._provider_instances[key]
            if hasattr(provider, 'get_provider_info'):
                return provider.get_provider_info()
        elif key in self._provider_classes:
            provider_class = self._provider_classes[key]
            return {
                "name": provider_class.__name__,
                "category": category,
                "status": "registered",
                "initialized": False
            }
        return None
    
    async def shutdown_all(self) -> None:
        """Gracefully shutdown all providers."""
        shutdown_tasks = []
        
        for provider in self._provider_instances.values():
            if hasattr(provider, 'graceful_shutdown'):
                shutdown_tasks.append(provider.graceful_shutdown())
        
        if shutdown_tasks:
            await asyncio.gather(*shutdown_tasks, return_exceptions=True)
        
        # Clear instances
        self._provider_instances.clear() 