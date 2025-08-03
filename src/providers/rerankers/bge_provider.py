import asyncio
from typing import List, Dict, Any, Optional
import logging

# Conditional imports for BGE reranking functionality
try:
    from FlagEmbedding import FlagReranker
except ImportError:
    FlagReranker = None

from src.interfaces.reranker_interface import RerankerInterface

logger = logging.getLogger(__name__)


class BGEProvider(RerankerInterface):
    """BGE (BAAI General Embedding) Reranker Provider for semantic document reranking."""
    
    def __init__(self):
        self.model = None
        self.model_name = None
        self.device = "cpu"
        self.batch_size = 16
        self.max_length = 512
        self._initialized = False
    
    async def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize the BGE reranker model with configuration."""
        if FlagReranker is None:
            raise ImportError(
                "FlagEmbedding is required for BGE reranker. "
                "Install with: pip install FlagEmbedding"
            )
        
        try:
            # Extract configuration with defaults
            self.model_name = config.get("model_name", "BAAI/bge-reranker-base")
            self.device = config.get("device", "cpu")
            self.batch_size = config.get("batch_size", 16)
            self.max_length = config.get("max_length", 512)
            
            # Initialize the BGE reranker model
            self.model = FlagReranker(
                model_name_or_path=self.model_name,
                use_fp16=self.device != "cpu",  # Use FP16 for GPU, FP32 for CPU
                device=self.device
            )
            
            self._initialized = True
            logger.info(f"BGE reranker initialized with model: {self.model_name}")
            
        except Exception as e:
            logger.error(f"Failed to initialize BGE reranker: {e}")
            raise
    
    async def rerank(
        self, 
        query: str, 
        documents: List[Dict[str, Any]], 
        top_k: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Rerank documents based on their relevance to the query using BGE."""
        if not self._initialized or self.model is None:
            raise RuntimeError("BGE reranker not initialized. Call initialize() first.")
        
        if not documents:
            return []
        
        try:
            # Prepare query-document pairs for BGE reranking
            query_doc_pairs = []
            for doc in documents:
                content = doc.get("content", "")
                query_doc_pairs.append([query, content])
            
            # Process in batches for efficiency
            all_scores = []
            for i in range(0, len(query_doc_pairs), self.batch_size):
                batch_pairs = query_doc_pairs[i:i + self.batch_size]
                
                # Get relevance scores from BGE model
                batch_scores = self.model.compute_score(batch_pairs)
                
                # Ensure scores is a list (handle single score case)
                if not isinstance(batch_scores, list):
                    batch_scores = [batch_scores]
                
                all_scores.extend(batch_scores)
            
            # Combine documents with their BGE scores
            scored_documents = []
            for doc, score in zip(documents, all_scores):
                doc_copy = doc.copy()
                
                # Add BGE score to metadata
                if "metadata" not in doc_copy:
                    doc_copy["metadata"] = {}
                doc_copy["metadata"]["bge_score"] = float(score)
                
                scored_documents.append(doc_copy)
            
            # Sort by BGE score in descending order (highest relevance first)
            scored_documents.sort(key=lambda x: x["metadata"]["bge_score"], reverse=True)
            
            # Apply top_k limit if specified
            if top_k is not None:
                scored_documents = scored_documents[:top_k]
            
            return scored_documents
            
        except Exception as e:
            logger.error(f"Error during BGE reranking: {e}")
            raise
    
    async def health_check(self) -> bool:
        """Check if the BGE reranker is healthy and functional."""
        try:
            return self._initialized and self.model is not None
        except Exception as e:
            logger.error(f"BGE reranker health check failed: {e}")
            return False
    
    def get_provider_info(self) -> Dict[str, Any]:
        """Get information about the BGE reranker provider."""
        return {
            "name": "BGEProvider",
            "version": "1.0",
            "capabilities": [
                "semantic_reranking",
                "relevance_scoring", 
                "result_optimization",
                "batch_processing"
            ],
            "type": "reranker",
            "model_name": self.model_name,
            "device": self.device,
            "batch_size": self.batch_size,
            "max_length": self.max_length,
            "initialized": self._initialized
        }
    
    async def graceful_shutdown(self) -> None:
        """Gracefully shutdown the BGE reranker provider."""
        try:
            if self.model is not None:
                # BGE model doesn't need explicit cleanup, but we reset state
                self.model = None
                self._initialized = False
                logger.info("BGE reranker provider shutdown completed")
        except Exception as e:
            logger.error(f"Error during BGE reranker shutdown: {e}")
    
    def supports_batch_reranking(self) -> bool:
        """Check if provider supports batch reranking operations."""
        return True
    
    def get_max_batch_size(self) -> int:
        """Get the maximum supported batch size for reranking."""
        return self.batch_size
    
    async def get_reranking_stats(self) -> Dict[str, Any]:
        """Get statistics about reranking operations."""
        return {
            "model_name": self.model_name,
            "device": self.device,
            "batch_size": self.batch_size,
            "max_length": self.max_length,
            "initialized": self._initialized,
            "supports_batch": self.supports_batch_reranking()
        } 