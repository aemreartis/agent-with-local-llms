"""
LLM Interface - Abstract base class for all LLM providers.

This interface defines the contract that all LLM providers must implement.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional


class LLMInterface(ABC):
    """Abstract interface for LLM providers."""
    
    @abstractmethod
    async def initialize(self, config: Dict[str, Any]) -> None:
        """
        Initialize the LLM provider with configuration.
        
        Args:
            config: Provider-specific configuration dictionary
            
        Raises:
            ValueError: If configuration is invalid
            ConnectionError: If unable to connect to LLM service
        """
        pass
    
    @abstractmethod
    async def generate(self, prompt: str, context: Optional[List[str]] = None, **kwargs) -> str:
        """
        Generate text response from prompt.
        
        Args:
            prompt: Input text prompt
            context: Optional context documents to include
            **kwargs: Provider-specific generation parameters (temperature, max_tokens, etc.)
            
        Returns:
            Generated text response
            
        Raises:
            ConnectionError: If LLM service is unavailable
            ValueError: If prompt is invalid
        """
        pass
    
    @abstractmethod
    async def embed(self, text: str) -> List[float]:
        """
        Generate embeddings for input text.
        
        Args:
            text: Input text to embed
            
        Returns:
            List of float values representing the embedding vector
            
        Raises:
            ConnectionError: If embedding service is unavailable
            ValueError: If text is invalid or too long
        """
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """
        Check if the LLM provider is healthy and available.
        
        Returns:
            True if provider is healthy, False otherwise
            
        Note:
            This method should not raise exceptions - return False on any failure
        """
        pass
    
    def get_provider_info(self) -> Dict[str, Any]:
        """
        Get information about this provider.
        
        Returns:
            Dictionary containing provider metadata (name, version, capabilities, etc.)
        """
        return {
            "name": self.__class__.__name__,
            "version": "1.0",
            "capabilities": ["generation", "embedding"],
            "type": "llm"
        } 