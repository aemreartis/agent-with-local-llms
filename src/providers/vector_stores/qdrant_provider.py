import uuid
from typing import List, Dict, Any, Optional
try:
    from qdrant_client import AsyncQdrantClient
    from qdrant_client.models import (
        Distance, VectorParams, CreateCollection, PointStruct,
        Filter, FieldCondition, MatchValue, PointIdsList
    )
except ImportError:
    # For testing without qdrant-client installed
    AsyncQdrantClient = None
    Distance = None
    VectorParams = None
    CreateCollection = None
    PointStruct = None
    Filter = None
    FieldCondition = None
    MatchValue = None
    PointIdsList = None

from src.interfaces.vector_store_interface import VectorStoreInterface


class QdrantProvider(VectorStoreInterface):
    """Qdrant Vector Store Provider.
    
    Connects to a Qdrant vector database for storing and retrieving embeddings
    with metadata filtering capabilities.
    """
    
    def __init__(self):
        """Initialize the Qdrant provider."""
        self.client: Optional[AsyncQdrantClient] = None
        self.url: Optional[str] = None
        self.collection_name: Optional[str] = None
        self.vector_size: int = 768
        self.distance: str = "Cosine"
        self.api_key: Optional[str] = None
        self.timeout: float = 30.0
        self._initialized: bool = False
    
    async def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize the Qdrant provider with configuration.
        
        Args:
            config: Configuration dictionary containing:
                - url: Qdrant server URL (required)
                - collection_name: Collection name (optional, default "documents")
                - vector_size: Vector dimensions (optional, default 768)
                - distance: Distance metric (optional, default "Cosine")
                - api_key: API key for authentication (optional)
                - timeout: Connection timeout (optional, default 30.0)
                - recreate_collection: Whether to recreate collection (optional, default False)
                
        Raises:
            ValueError: If required configuration is missing
        """
        if "url" not in config:
            raise ValueError("url is required for Qdrant provider")
        
        if AsyncQdrantClient is None:
            raise ImportError("qdrant_client is required for QdrantProvider. Install with: pip install qdrant-client")
        
        self.url = config["url"]
        self.collection_name = config.get("collection_name", "documents")
        self.vector_size = config.get("vector_size", 768)
        self.distance = config.get("distance", "Cosine")
        self.api_key = config.get("api_key")
        self.timeout = config.get("timeout", 30.0)
        recreate_collection = config.get("recreate_collection", False)
        
        # Initialize Qdrant client
        self.client = AsyncQdrantClient(
            url=self.url,
            api_key=self.api_key,
            timeout=self.timeout
        )
        
        # Create collection if it doesn't exist or if recreate is requested
        collection_exists = await self.client.collection_exists(self.collection_name)
        
        if recreate_collection and collection_exists:
            await self.client.delete_collection(self.collection_name)
            collection_exists = False
        
        if not collection_exists:
            # Map distance string to Qdrant Distance enum
            distance_map = {
                "Cosine": Distance.COSINE,
                "Dot": Distance.DOT,
                "Euclid": Distance.EUCLID,
                "Manhattan": Distance.MANHATTAN
            }
            
            await self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=self.vector_size,
                    distance=distance_map.get(self.distance, Distance.COSINE)
                )
            )
        
        self._initialized = True
    
    async def store(self, vector: List[float], metadata: Dict[str, Any], document_id: Optional[str] = None) -> str:
        """Store a vector with metadata in Qdrant.
        
        Args:
            vector: Embedding vector to store
            metadata: Associated metadata
            document_id: Optional document ID (generates UUID if not provided)
            
        Returns:
            Document ID of the stored vector
            
        Raises:
            Exception: If storage fails or provider not initialized
        """
        if not self._initialized or self.client is None:
            raise Exception("Provider not initialized. Call initialize() first.")
        
        # Generate ID if not provided
        if document_id is None:
            document_id = str(uuid.uuid4())
        
        try:
            # Create point for storage
            point = PointStruct(
                id=document_id,
                vector=vector,
                payload=metadata
            )
            
            # Store in Qdrant
            operation_info = await self.client.upsert(
                collection_name=self.collection_name,
                points=[point]
            )
            
            return document_id
            
        except Exception as e:
            raise Exception(f"Failed to store vector in Qdrant: {str(e)}")
    
    async def retrieve(self, query_vector: List[float], top_k: int = 10, filter_conditions: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Retrieve similar vectors from Qdrant.
        
        Args:
            query_vector: Query vector for similarity search
            top_k: Maximum number of results to return
            filter_conditions: Optional metadata filters
            
        Returns:
            List of similar vectors with scores and metadata
            
        Raises:
            Exception: If retrieval fails or provider not initialized
        """
        if not self._initialized or self.client is None:
            raise Exception("Provider not initialized. Call initialize() first.")
        
        try:
            # Build query filter if conditions provided
            query_filter = None
            if filter_conditions:
                must_conditions = []
                for key, value in filter_conditions.items():
                    must_conditions.append(
                        FieldCondition(
                            key=key,
                            match=MatchValue(value=value)
                        )
                    )
                
                if must_conditions:
                    query_filter = Filter(must=must_conditions)
            
            # Perform similarity search
            search_results = await self.client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                query_filter=query_filter,
                limit=top_k,
                with_payload=True,
                with_vectors=False
            )
            
            # Format results
            results = []
            for result in search_results:
                results.append({
                    "id": result.id,
                    "score": result.score,
                    "metadata": result.payload or {}
                })
            
            return results
            
        except Exception as e:
            raise Exception(f"Failed to retrieve vectors from Qdrant: {str(e)}")
    
    async def delete(self, document_id: str) -> bool:
        """Delete a vector from Qdrant.
        
        Args:
            document_id: ID of the document to delete
            
        Returns:
            True if deletion successful, False otherwise
        """
        if not self._initialized or self.client is None:
            return False
        
        try:
            # Delete point by ID
            operation_info = await self.client.delete(
                collection_name=self.collection_name,
                points_selector=PointIdsList(points=[document_id])
            )
            
            return True
            
        except Exception:
            return False
    
    async def health_check(self) -> bool:
        """Check if Qdrant provider is healthy and responsive.
        
        Returns:
            True if healthy, False otherwise
        """
        if not self._initialized or self.client is None:
            return False
        
        try:
            # Try to get collections list as health check
            await self.client.get_collections()
            return True
        except Exception:
            return False
    
    def get_provider_info(self) -> Dict[str, Any]:
        """Get provider information and capabilities.
        
        Returns:
            Dictionary with provider metadata
        """
        return {
            "name": "QdrantProvider",
            "version": "1.0",
            "capabilities": ["storage", "retrieval", "similarity_search", "metadata_filtering"],
            "type": "vector_store",
            "url": self.url,
            "collection_name": self.collection_name,
            "vector_size": self.vector_size,
            "distance": self.distance,
            "initialized": self._initialized
        }
    
    async def update(self, document_id: str, vector: Optional[List[float]] = None, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Update an existing vector and/or its metadata.
        
        Args:
            document_id: ID of the document to update
            vector: New vector (optional)
            metadata: New metadata (optional)
            
        Returns:
            True if update successful, False otherwise
        """
        if not self._initialized or self.client is None:
            return False
        
        try:
            # Get existing point to preserve data not being updated
            existing_points = await self.client.retrieve(
                collection_name=self.collection_name,
                ids=[document_id],
                with_payload=True,
                with_vectors=bool(vector is None)  # Only get vector if we're not updating it
            )
            
            if not existing_points:
                return False  # Document doesn't exist
            
            existing_point = existing_points[0]
            
            # Use provided values or keep existing ones
            new_vector = vector if vector is not None else existing_point.vector
            new_metadata = metadata if metadata is not None else existing_point.payload
            
            # Create updated point
            updated_point = PointStruct(
                id=document_id,
                vector=new_vector,
                payload=new_metadata
            )
            
            # Update in Qdrant
            await self.client.upsert(
                collection_name=self.collection_name,
                points=[updated_point]
            )
            
            return True
            
        except Exception:
            return False
    
    async def batch_store(self, vectors: List[List[float]], metadata_list: List[Dict[str, Any]], document_ids: Optional[List[str]] = None) -> List[str]:
        """Store multiple vectors in batch for efficiency.
        
        Args:
            vectors: List of vectors to store
            metadata_list: List of metadata dictionaries
            document_ids: Optional list of document IDs (generates UUIDs if not provided)
            
        Returns:
            List of document IDs for the stored vectors
            
        Raises:
            Exception: If batch storage fails or provider not initialized
        """
        if not self._initialized or self.client is None:
            raise Exception("Provider not initialized. Call initialize() first.")
        
        if len(vectors) != len(metadata_list):
            raise ValueError("Number of vectors must match number of metadata items")
        
        # Generate IDs if not provided
        if document_ids is None:
            document_ids = [str(uuid.uuid4()) for _ in vectors]
        elif len(document_ids) != len(vectors):
            raise ValueError("Number of document IDs must match number of vectors")
        
        try:
            # Create points for batch storage
            points = []
            for vector, metadata, doc_id in zip(vectors, metadata_list, document_ids):
                points.append(PointStruct(
                    id=doc_id,
                    vector=vector,
                    payload=metadata
                ))
            
            # Batch store in Qdrant
            operation_info = await self.client.upsert(
                collection_name=self.collection_name,
                points=points
            )
            
            return document_ids
            
        except Exception as e:
            raise Exception(f"Failed to batch store vectors in Qdrant: {str(e)}")
    
    async def graceful_shutdown(self) -> None:
        """Gracefully shutdown the provider and cleanup resources."""
        if self.client is not None:
            await self.client.close()
            self.client = None
        self._initialized = False 