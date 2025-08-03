from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional


class RerankerInterface(ABC):
    """Abstract interface for reranking providers.
    
    Defines the contract for all reranking implementations
    including BGE, ColBERT, and LLM-based reranking strategies.
    """
    
    @abstractmethod
    async def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize the reranker with configuration.
        
        Args:
            config: Provider-specific configuration parameters
            
        Raises:
            Exception: If initialization fails
        """
        pass
    
    @abstractmethod
    async def rerank(self, query: str, documents: List[Dict[str, Any]], top_k: Optional[int] = None) -> List[Dict[str, Any]]:
        """Rerank documents based on query relevance.
        
        Args:
            query: The search query to rank documents against
            documents: List of documents to rerank with id, content, and metadata
            top_k: Maximum number of results to return (None = return all)
            
        Returns:
            List of reranked documents with updated scores, ordered by relevance
            
        Example:
            Input documents:
            [
                {"id": "doc_1", "score": 0.7, "content": "Document content..."},
                {"id": "doc_2", "score": 0.8, "content": "Another document..."}
            ]
            
            Output (reranked):
            [
                {"id": "doc_2", "score": 0.95, "content": "Another document..."},
                {"id": "doc_1", "score": 0.90, "content": "Document content..."}
            ]
        """
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """Check if reranker is healthy and responsive.
        
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
            "capabilities": ["semantic_reranking", "relevance_scoring", "result_optimization"],
            "type": "reranker"
        } 