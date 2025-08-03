"""
Vector Store Interface - Abstract base class for all vector store providers.

This interface defines the contract that all vector database providers must implement.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional


class VectorStoreInterface(ABC):
    """Abstract interface for vector store providers."""
    
    @abstractmethod
    async def initialize(self, config: Dict[str, Any]) -> None:
        """
        Initialize the vector store provider with configuration.
        
        Args:
            config: Provider-specific configuration dictionary
                   (collection_name, dimension, index_params, etc.)
            
        Raises:
            ValueError: If configuration is invalid
            ConnectionError: If unable to connect to vector store service
        """
        pass
    
    @abstractmethod
    async def store(self, 
                   vector: List[float], 
                   metadata: Dict[str, Any],
                   document_id: Optional[str] = None) -> str:
        """
        Store a vector with associated metadata.
        
        Args:
            vector: The embedding vector to store
            metadata: Associated metadata (content, source, etc.)
            document_id: Optional custom document ID
            
        Returns:
            The document ID of the stored vector
            
        Raises:
            ValueError: If vector dimension doesn't match collection
            ConnectionError: If vector store service is unavailable
        """
        pass
    
    @abstractmethod
    async def retrieve(self, 
                      query_vector: List[float], 
                      top_k: int = 10,
                      filter_conditions: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Retrieve similar vectors based on query vector.
        
        Args:
            query_vector: The query embedding vector
            top_k: Number of top similar vectors to return
            filter_conditions: Optional metadata filters
            
        Returns:
            List of dictionaries containing:
            - id: Document ID
            - score: Similarity score
            - metadata: Associated metadata
            
        Raises:
            ValueError: If query vector dimension doesn't match
            ConnectionError: If vector store service is unavailable
        """
        pass
    
    @abstractmethod
    async def delete(self, document_id: str) -> bool:
        """
        Delete a document by ID.
        
        Args:
            document_id: The document ID to delete
            
        Returns:
            True if document was deleted, False if not found
            
        Raises:
            ConnectionError: If vector store service is unavailable
        """
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """
        Check if the vector store provider is healthy and available.
        
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
            Dictionary containing provider metadata
        """
        return {
            "name": self.__class__.__name__,
            "version": "1.0",
            "capabilities": ["storage", "retrieval", "similarity_search", "metadata_filtering"],
            "type": "vector_store"
        }
    
    async def update(self, 
                    document_id: str, 
                    vector: Optional[List[float]] = None,
                    metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Update an existing document's vector and/or metadata.
        
        Args:
            document_id: The document ID to update
            vector: Optional new vector (if None, keep existing)
            metadata: Optional new metadata (if None, keep existing)
            
        Returns:
            True if document was updated, False if not found
            
        Note:
            This is an optional method with default implementation.
            Providers can override for optimized updates.
        """
        # Default implementation: delete and re-store
        if await self.delete(document_id):
            if vector and metadata:
                await self.store(vector, metadata, document_id)
                return True
        return False
    
    async def batch_store(self, 
                         vectors: List[List[float]], 
                         metadata_list: List[Dict[str, Any]],
                         document_ids: Optional[List[str]] = None) -> List[str]:
        """
        Store multiple vectors in batch for efficiency.
        
        Args:
            vectors: List of embedding vectors to store
            metadata_list: List of associated metadata dictionaries
            document_ids: Optional list of custom document IDs
            
        Returns:
            List of document IDs for the stored vectors
            
        Note:
            This is an optional method with default implementation.
            Providers should override for optimized batch operations.
        """
        # Default implementation: sequential storage
        stored_ids = []
        for i, (vector, metadata) in enumerate(zip(vectors, metadata_list)):
            doc_id = document_ids[i] if document_ids else None
            stored_id = await self.store(vector, metadata, doc_id)
            stored_ids.append(stored_id)
        return stored_ids 