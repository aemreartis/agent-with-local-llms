from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum


class FusionStrategy(Enum):
    """Strategies for combining results from multiple search providers."""
    INTERLEAVE = "interleave"  # Alternate results from each provider
    SCORE_WEIGHTED = "score_weighted"  # Combine based on relevance scores
    RANK_FUSION = "rank_fusion"  # Reciprocal rank fusion (RRF)
    PROVIDER_WEIGHTED = "provider_weighted"  # Weight by provider importance
    ADAPTIVE = "adaptive"  # Choose fusion strategy based on query/results


@dataclass
class SearchRequest:
    """Request structure for multi-provider search."""
    query: str
    providers: List[str]  # e.g., ["vector", "bm25"]
    fusion_strategy: FusionStrategy = FusionStrategy.RANK_FUSION
    top_k: int = 10
    provider_weights: Optional[Dict[str, float]] = None
    provider_configs: Optional[Dict[str, Dict[str, Any]]] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class ProviderSearchResult:
    """Result from a single search provider."""
    provider_name: str
    provider_type: str  # "vector_store", "search_engine"
    results: List[Dict[str, Any]]
    query_time_ms: float
    total_results: int
    metadata: Dict[str, Any] = None


@dataclass
class FusedSearchResult:
    """Combined result from multiple search providers."""
    query: str
    provider_results: List[ProviderSearchResult]
    fused_results: List[Dict[str, Any]]
    fusion_strategy_used: FusionStrategy
    total_providers_used: int
    total_query_time_ms: float
    fusion_time_ms: float
    metadata: Dict[str, Any] = None


class SearchOrchestratorInterface(ABC):
    """Interface for orchestrating multi-provider search and result fusion."""
    
    @abstractmethod
    async def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize the search orchestrator with provider registry and configuration."""
        pass
    
    @abstractmethod
    async def search(self, request: SearchRequest) -> FusedSearchResult:
        """
        Execute multi-provider search and fusion:
        1. Execute search across specified providers in parallel
        2. Collect and normalize results
        3. Apply fusion strategy to combine results
        4. Return unified result set
        """
        pass
    
    @abstractmethod
    async def search_vector(self, query: str, top_k: int = 10, **kwargs) -> ProviderSearchResult:
        """Execute vector-based search using the configured vector store provider."""
        pass
    
    @abstractmethod
    async def search_keyword(self, query: str, top_k: int = 10, **kwargs) -> ProviderSearchResult:
        """Execute keyword-based search using the configured search engine provider."""
        pass
    
    @abstractmethod
    async def search_hybrid(self, query: str, top_k: int = 10, fusion_strategy: FusionStrategy = FusionStrategy.RANK_FUSION) -> FusedSearchResult:
        """Execute hybrid search combining vector and keyword approaches."""
        pass
    
    @abstractmethod
    async def fuse_results(self, provider_results: List[ProviderSearchResult], strategy: FusionStrategy, top_k: int = 10, **kwargs) -> List[Dict[str, Any]]:
        """Fuse results from multiple providers using the specified strategy."""
        pass
    
    @abstractmethod
    async def normalize_results(self, results: List[Dict[str, Any]], provider_name: str) -> List[Dict[str, Any]]:
        """Normalize results from different providers to a common format."""
        pass
    
    @abstractmethod
    async def calculate_fusion_scores(self, provider_results: List[ProviderSearchResult], strategy: FusionStrategy) -> Dict[str, float]:
        """Calculate fusion scores for combining results."""
        pass
    
    @abstractmethod
    async def health_check(self) -> Dict[str, bool]:
        """Check health of all search providers."""
        pass
    
    def get_service_info(self) -> Dict[str, Any]:
        """Get information about the search orchestrator."""
        return {
            "name": self.__class__.__name__,
            "version": "1.0",
            "capabilities": [
                "multi_provider_search",
                "parallel_execution", 
                "result_fusion",
                "hybrid_search",
                "score_normalization",
                "adaptive_strategies"
            ],
            "type": "search_orchestrator",
            "supported_fusion_strategies": [fs.value for fs in FusionStrategy]
        } 