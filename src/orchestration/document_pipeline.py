"""
Orchestration-level Document Pipeline

Provides high-level document processing orchestration with vector store integration,
quality validation, and metadata management.
"""

import logging
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from src.providers.document.document_pipeline import DocumentPipeline as ProviderDocumentPipeline
from src.interfaces.document_interface import ChunkingStrategy, DocumentType
from src.registry.provider_registry import ProviderRegistry

logger = logging.getLogger(__name__)


class DocumentPipeline:
    """Orchestration-level document pipeline with vector store integration."""
    
    def __init__(self, registry: ProviderRegistry):
        """Initialize the orchestration document pipeline."""
        self.registry = registry
        self.provider_pipeline = None
        self.vector_store = None
        self.search_engine = None
        self.llm_provider = None
        self.memory_provider = None
        self.initialized = False
    
    async def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize the document pipeline with all required components."""
        try:
            # Initialize provider pipeline
            self.provider_pipeline = ProviderDocumentPipeline()
            await self.provider_pipeline.initialize(config.get("document_pipeline", {}))
            
            # Get required providers from registry
            self.vector_store = await self.registry.get_provider("vector_store")
            self.search_engine = await self.registry.get_provider("search_engine")
            self.llm_provider = await self.registry.get_provider("llm")
            self.memory_provider = await self.registry.get_provider("memory")
            
            self.initialized = True
            logger.info("Orchestration document pipeline initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize orchestration document pipeline: {str(e)}")
            raise
    
    async def process_document(self, file_path: str, metadata: Dict[str, Any], 
                             validate_quality: bool = False) -> Dict[str, Any]:
        """Process a document and store it in the vector store."""
        if not self.initialized:
            await self.initialize({})
        
        try:
            # Generate document ID
            document_id = str(uuid.uuid4())
            
            # Process document through provider pipeline
            chunking_strategy = ChunkingStrategy.FIXED_SIZE
            document = await self.provider_pipeline.process_file(file_path, chunking_strategy)
            
            # Store chunks in vector store
            vector_ids = []
            for chunk in document.chunks:
                # Create vector embedding
                embedding = await self.llm_provider.embed(chunk.content)
                
                # Store in vector store
                chunk_metadata = {
                    **metadata,
                    **chunk.metadata,
                    "document_id": document_id,
                    "chunk_id": chunk.chunk_id,
                    "processed_at": datetime.now(timezone.utc).isoformat()
                }
                
                vector_id = await self.vector_store.store(embedding, chunk_metadata)
                vector_ids.append(vector_id)
            
            # Calculate quality score if requested
            quality_score = None
            if validate_quality:
                quality_score = await self._calculate_quality_score(document)
            
            # Store document metadata in memory
            document_metadata = {
                "document_id": document_id,
                "title": metadata.get("title", "Untitled"),
                "type": metadata.get("type", "unknown"),
                "file_path": file_path,
                "chunk_count": len(document.chunks),
                "vector_ids": vector_ids,
                "quality_score": quality_score,
                "processed_at": datetime.now(timezone.utc).isoformat()
            }
            
            await self.memory_provider.store(
                f"document:{document_id}",
                document_metadata,
                metadata={"type": "document_metadata"}
            )
            
            return {
                "success": True,
                "document_id": document_id,
                "chunks": [
                    {
                        "content": chunk.content,
                        "metadata": chunk.metadata
                    } for chunk in document.chunks
                ],
                "vector_ids": vector_ids,
                "quality_score": quality_score
            }
            
        except Exception as e:
            logger.error(f"Failed to process document {file_path}: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def update_document(self, document_id: str, file_path: str, 
                            metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing document with new content."""
        if not self.initialized:
            await self.initialize({})
        
        try:
            # Get existing document metadata
            existing_metadata = await self.memory_provider.retrieve(f"document:{document_id}")
            if not existing_metadata:
                return {
                    "success": False,
                    "error": f"Document {document_id} not found"
                }
            
            # Delete existing vectors
            for vector_id in existing_metadata.get("vector_ids", []):
                await self.vector_store.delete(vector_id)
            
            # Process updated document
            result = await self.process_document(file_path, metadata)
            if not result["success"]:
                return result
            
            # Update document metadata
            result["document_id"] = document_id  # Keep original ID
            result["updated_chunks"] = result.pop("chunks")
            
            # Update stored metadata
            await self.memory_provider.store(
                f"document:{document_id}",
                {
                    **existing_metadata,
                    **result,
                    "updated_at": datetime.now(timezone.utc).isoformat()
                },
                metadata={"type": "document_metadata"}
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to update document {document_id}: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def delete_document(self, document_id: str) -> Dict[str, Any]:
        """Delete a document and all its associated data."""
        if not self.initialized:
            await self.initialize({})
        
        try:
            # Get document metadata
            document_metadata = await self.memory_provider.retrieve(f"document:{document_id}")
            if not document_metadata:
                return {
                    "success": False,
                    "error": f"Document {document_id} not found"
                }
            
            # Delete vectors from vector store
            for vector_id in document_metadata.get("vector_ids", []):
                await self.vector_store.delete(vector_id)
            
            # Delete document metadata from memory
            await self.memory_provider.delete(f"document:{document_id}")
            
            return {
                "success": True,
                "document_id": document_id,
                "deleted_at": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to delete document {document_id}: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_document_info(self, document_id: str) -> Dict[str, Any]:
        """Get information about a document."""
        if not self.initialized:
            await self.initialize({})
        
        try:
            document_metadata = await self.memory_provider.retrieve(f"document:{document_id}")
            if not document_metadata:
                return {
                    "success": False,
                    "error": f"Document {document_id} not found"
                }
            
            return {
                "success": True,
                "document_info": document_metadata
            }
            
        except Exception as e:
            logger.error(f"Failed to get document info for {document_id}: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def list_documents(self, document_type: Optional[str] = None) -> Dict[str, Any]:
        """List all documents, optionally filtered by type."""
        if not self.initialized:
            await self.initialize({})
        
        try:
            # This would require a more sophisticated memory provider implementation
            # For now, return a mock response
            return {
                "success": True,
                "documents": [],
                "total_count": 0
            }
            
        except Exception as e:
            logger.error(f"Failed to list documents: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _calculate_quality_score(self, document) -> float:
        """Calculate a quality score for the document."""
        try:
            # Simple quality scoring based on content length and structure
            total_content_length = sum(len(chunk.content) for chunk in document.chunks)
            chunk_count = len(document.chunks)
            
            # Base score on content length and chunk distribution
            if total_content_length < 100:
                return 0.1  # Very low quality
            elif total_content_length < 500:
                return 0.3  # Low quality
            elif total_content_length < 2000:
                return 0.6  # Medium quality
            elif total_content_length < 10000:
                return 0.8  # Good quality
            else:
                return 0.9  # High quality
            
        except Exception as e:
            logger.error(f"Failed to calculate quality score: {str(e)}")
            return 0.5  # Default medium quality
    
    async def health_check(self) -> bool:
        """Check if the document pipeline is healthy."""
        try:
            if not self.initialized:
                return False
            
            # Check provider pipeline health
            if not await self.provider_pipeline.health_check():
                return False
            
            # Check vector store health
            if not await self.vector_store.health_check():
                return False
            
            # Check memory provider health
            if not await self.memory_provider.health_check():
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Document pipeline health check failed: {str(e)}")
            return False 