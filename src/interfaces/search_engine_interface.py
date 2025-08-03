from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional


class SearchEngineInterface(ABC):
    """Abstract interface for search engine providers.
    
    Defines the contract for all search engine implementations
    including keyword search, full-text search, and hybrid search strategies.
    """
    
    @abstractmethod
    async def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize the search engine with configuration.
        
        Args:
            config: Provider-specific configuration parameters
            
        Raises:
            Exception: If initialization fails
        """
        pass
    
    @abstractmethod
    async def search(self, query: str, top_k: int = 10, **kwargs) -> List[Dict[str, Any]]:
        """Perform search query and return ranked results.
        
        Args:
            query: Search query string
            top_k: Maximum number of results to return
            **kwargs: Additional search parameters (filters, etc.)
            
        Returns:
            List of search results with id, score, and content/metadata
            
        Example:
            [
                {"id": "doc_1", "score": 0.95, "content": "Document content..."},
                {"id": "doc_2", "score": 0.85, "content": "Another document..."}
            ]
        """
        pass
    
    @abstractmethod 
    async def index(self, documents: List[Dict[str, Any]]) -> bool:
        """Index documents for search.
        
        Args:
            documents: List of documents to index with id, content, and metadata
            
        Returns:
            True if indexing successful, False otherwise
            
        Example:
            documents = [
                {"id": "doc_1", "content": "Text content", "metadata": {...}},
                {"id": "doc_2", "content": "More content", "metadata": {...}}
            ]
        """
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """Check if search engine is healthy and responsive.
        
        Returns:
            True if healthy, False otherwise
        """
        pass
    
    def get_provider_info(self) -> Dict[str, Any]:
        """Get provider information and capabilities.
        
        Returns:
            Dictionary with provider metadata
        """
        return {
            "name": self.__class__.__name__,
            "version": "1.0",
            "capabilities": ["keyword_search", "full_text_search", "indexing"],
            "type": "search_engine"
        } 