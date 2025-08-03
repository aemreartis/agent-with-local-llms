import re
import string
from typing import List, Dict, Any, Optional
try:
    from rank_bm25 import BM25Okapi
except ImportError:
    BM25Okapi = None

from src.interfaces.search_engine_interface import SearchEngineInterface


class BM25Provider(SearchEngineInterface):
    """BM25 Search Engine Provider.
    
    Implements keyword-based search using the BM25 algorithm
    with configurable tokenization and ranking parameters.
    """
    
    def __init__(self):
        """Initialize the BM25 provider."""
        self.k1: float = 1.2  # BM25 k1 parameter
        self.b: float = 0.75  # BM25 b parameter
        self.epsilon: float = 0.25  # BM25 epsilon parameter
        self.tokenizer: str = "simple"
        self.lowercase: bool = True
        self.remove_punctuation: bool = True
        self.bm25_index: Optional[BM25Okapi] = None
        self.documents: List[Dict[str, Any]] = []
        self.tokenized_corpus: List[List[str]] = []
        self._initialized: bool = False
    
    async def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize the BM25 provider with configuration.
        
        Args:
            config: Configuration dictionary containing:
                - k1: BM25 k1 parameter (optional, default 1.2)
                - b: BM25 b parameter (optional, default 0.75)
                - epsilon: BM25 epsilon parameter (optional, default 0.25)
                - tokenizer: Tokenization method (optional, default "simple")
                - lowercase: Convert to lowercase (optional, default True)
                - remove_punctuation: Remove punctuation (optional, default True)
        """
        if BM25Okapi is None:
            raise ImportError("rank_bm25 is required for BM25Provider. Install with: pip install rank-bm25")
        
        self.k1 = config.get("k1", 1.2)
        self.b = config.get("b", 0.75)
        self.epsilon = config.get("epsilon", 0.25)
        self.tokenizer = config.get("tokenizer", "simple")
        self.lowercase = config.get("lowercase", True)
        self.remove_punctuation = config.get("remove_punctuation", True)
        
        # Initialize empty index
        self.documents = []
        self.tokenized_corpus = []
        self.bm25_index = None
        
        self._initialized = True
    
    async def search(self, query: str, top_k: int = 10, **kwargs) -> List[Dict[str, Any]]:
        """Perform BM25 search and return ranked results.
        
        Args:
            query: Search query string
            top_k: Maximum number of results to return
            **kwargs: Additional parameters including filters
            
        Returns:
            List of search results with id, score, content, and metadata
            
        Raises:
            Exception: If search fails or provider not initialized
        """
        if not self._initialized:
            raise Exception("Provider not initialized. Call initialize() first.")
        
        if not self.documents or self.bm25_index is None:
            return []
        
        try:
            # Tokenize query
            query_tokens = self._tokenize(query)
            
            if not query_tokens:
                return []
            
            # Get BM25 scores for all documents
            scores = self.bm25_index.get_scores(query_tokens)
            
            # Create result tuples (score, document_index)
            scored_results = []
            for i, score in enumerate(scores):
                if score > 0:  # Only include documents with positive scores
                    scored_results.append((score, i))
            
            # Sort by score (descending)
            scored_results.sort(key=lambda x: x[0], reverse=True)
            
            # Apply filters if provided
            filters = kwargs.get("filters", {})
            
            # Build final results
            results = []
            for score, doc_idx in scored_results[:top_k * 3]:  # Get more to account for filtering
                document = self.documents[doc_idx]
                
                # Apply metadata filters
                if filters:
                    if not self._matches_filters(document.get("metadata", {}), filters):
                        continue
                
                result = {
                    "id": document["id"],
                    "score": float(score),
                    "content": document["content"],
                    "metadata": document.get("metadata", {})
                }
                results.append(result)
                
                # Stop when we have enough results
                if len(results) >= top_k:
                    break
            
            return results
            
        except Exception as e:
            raise Exception(f"BM25 search failed: {str(e)}")
    
    async def index(self, documents: List[Dict[str, Any]]) -> bool:
        """Index documents for BM25 search.
        
        Args:
            documents: List of documents with id, content, and metadata
            
        Returns:
            True if indexing successful
            
        Raises:
            Exception: If indexing fails or provider not initialized
        """
        if not self._initialized:
            raise Exception("Provider not initialized. Call initialize() first.")
        
        if BM25Okapi is None:
            raise Exception("rank_bm25 is required for indexing")
        
        try:
            # Store documents
            self.documents = documents.copy()
            
            # Tokenize all document content
            self.tokenized_corpus = []
            for doc in self.documents:
                content = doc.get("content", "")
                tokens = self._tokenize(content)
                self.tokenized_corpus.append(tokens)
            
            # Create BM25 index if we have documents
            if self.tokenized_corpus:
                self.bm25_index = BM25Okapi(
                    self.tokenized_corpus,
                    k1=self.k1,
                    b=self.b,
                    epsilon=self.epsilon
                )
            else:
                self.bm25_index = None
            
            return True
            
        except Exception as e:
            raise Exception(f"BM25 indexing failed: {str(e)}")
    
    async def health_check(self) -> bool:
        """Check if BM25 provider is healthy and responsive.
        
        Returns:
            True if healthy, False otherwise
        """
        return self._initialized
    
    def get_provider_info(self) -> Dict[str, Any]:
        """Get provider information and capabilities.
        
        Returns:
            Dictionary with provider metadata
        """
        return {
            "name": "BM25Provider",
            "version": "1.0",
            "capabilities": ["keyword_search", "full_text_search", "indexing"],
            "type": "search_engine",
            "parameters": {
                "k1": self.k1,
                "b": self.b,
                "epsilon": self.epsilon,
                "tokenizer": self.tokenizer
            },
            "indexed_documents": len(self.documents),
            "initialized": self._initialized
        }
    
    def _tokenize(self, text: str) -> List[str]:
        """Tokenize text based on configuration.
        
        Args:
            text: Text to tokenize
            
        Returns:
            List of tokens
        """
        if not text:
            return []
        
        # Convert to lowercase if configured
        if self.lowercase:
            text = text.lower()
        
        # Remove punctuation if configured
        if self.remove_punctuation:
            # Remove punctuation but keep spaces
            text = text.translate(str.maketrans("", "", string.punctuation))
        
        if self.tokenizer == "simple":
            # Simple whitespace tokenization
            tokens = text.split()
        else:
            # More advanced tokenization could be added here
            # For now, fallback to simple
            tokens = text.split()
        
        # Filter out empty tokens
        tokens = [token for token in tokens if token.strip()]
        
        return tokens
    
    def _matches_filters(self, metadata: Dict[str, Any], filters: Dict[str, Any]) -> bool:
        """Check if document metadata matches the provided filters.
        
        Args:
            metadata: Document metadata
            filters: Filter conditions to match
            
        Returns:
            True if all filters match, False otherwise
        """
        for filter_key, filter_value in filters.items():
            if filter_key not in metadata:
                return False
            
            metadata_value = metadata[filter_key]
            
            # Support different filter types
            if isinstance(filter_value, str):
                if str(metadata_value) != filter_value:
                    return False
            elif isinstance(filter_value, (int, float)):
                if metadata_value != filter_value:
                    return False
            elif isinstance(filter_value, list):
                if metadata_value not in filter_value:
                    return False
            else:
                # Default string comparison
                if str(metadata_value) != str(filter_value):
                    return False
        
        return True
    
    async def add_documents(self, documents: List[Dict[str, Any]]) -> bool:
        """Add documents to existing index.
        
        Args:
            documents: List of documents to add
            
        Returns:
            True if successful
        """
        if not self._initialized:
            raise Exception("Provider not initialized. Call initialize() first.")
        
        # Add to existing documents
        self.documents.extend(documents)
        
        # Rebuild index with all documents
        return await self.index(self.documents)
    
    async def remove_documents(self, document_ids: List[str]) -> bool:
        """Remove documents from index.
        
        Args:
            document_ids: List of document IDs to remove
            
        Returns:
            True if successful
        """
        if not self._initialized:
            raise Exception("Provider not initialized. Call initialize() first.")
        
        # Remove documents with matching IDs
        self.documents = [doc for doc in self.documents if doc["id"] not in document_ids]
        
        # Rebuild index with remaining documents
        return await self.index(self.documents)
    
    def get_document_count(self) -> int:
        """Get the number of indexed documents.
        
        Returns:
            Number of documents in the index
        """
        return len(self.documents)
    
    def get_vocabulary_size(self) -> int:
        """Get the size of the vocabulary.
        
        Returns:
            Number of unique terms in the index
        """
        if self.bm25_index is None:
            return 0
        
        # Get unique tokens from all documents
        vocabulary = set()
        for tokens in self.tokenized_corpus:
            vocabulary.update(tokens)
        
        return len(vocabulary) 