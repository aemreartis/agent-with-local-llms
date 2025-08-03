from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum


class QueryType(Enum):
    """Types of queries for different processing strategies."""
    FACTUAL = "factual"
    CONVERSATIONAL = "conversational" 
    ANALYTICAL = "analytical"
    CREATIVE = "creative"
    SEARCH = "search"


class SearchStrategy(Enum):
    """Search strategies for query processing."""
    VECTOR_ONLY = "vector_only"
    KEYWORD_ONLY = "keyword_only"
    HYBRID = "hybrid"
    ADAPTIVE = "adaptive"  # Choose strategy based on query analysis


@dataclass
class QueryContext:
    """Context information for query processing."""
    query: str
    query_type: QueryType = QueryType.FACTUAL
    search_strategy: SearchStrategy = SearchStrategy.HYBRID
    conversation_id: Optional[str] = None
    user_id: Optional[str] = None
    context_limit: int = 10
    use_reranking: bool = True
    llm_config: Dict[str, Any] = None
    metadata: Dict[str, Any] = None


@dataclass
class QueryResult:
    """Result from query processing."""
    original_query: str
    processed_query: str
    search_results: List[Dict[str, Any]]
    reranked_results: Optional[List[Dict[str, Any]]] = None
    context_documents: List[Dict[str, Any]] = None
    llm_response: Optional[str] = None
    query_type: QueryType = QueryType.FACTUAL
    search_strategy_used: SearchStrategy = SearchStrategy.HYBRID
    processing_steps: List[str] = None
    timing_info: Dict[str, float] = None
    metadata: Dict[str, Any] = None


class QueryOrchestratorInterface(ABC):
    """Interface for orchestrating query processing workflows across multiple providers."""
    
    @abstractmethod
    async def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize the query orchestrator with provider registry and configuration."""
        pass
    
    @abstractmethod
    async def process_query(self, context: QueryContext) -> QueryResult:
        """
        Process a query through the complete workflow:
        1. Analyze query to determine type and strategy
        2. Execute search using appropriate providers
        3. Optionally rerank results
        4. Prepare context for LLM
        5. Return comprehensive results
        """
        pass
    
    @abstractmethod
    async def analyze_query(self, query: str) -> QueryType:
        """Analyze query to determine the most appropriate processing approach."""
        pass
    
    @abstractmethod
    async def determine_search_strategy(self, query: str, query_type: QueryType) -> SearchStrategy:
        """Determine the optimal search strategy based on query characteristics."""
        pass
    
    @abstractmethod
    async def execute_search(self, query: str, strategy: SearchStrategy, limit: int = 10) -> List[Dict[str, Any]]:
        """Execute search using the specified strategy and providers."""
        pass
    
    @abstractmethod
    async def rerank_results(self, query: str, results: List[Dict[str, Any]], top_k: Optional[int] = None) -> List[Dict[str, Any]]:
        """Rerank search results using the configured reranker provider."""
        pass
    
    @abstractmethod
    async def prepare_context(self, query: str, results: List[Dict[str, Any]], max_context: int = 10) -> List[Dict[str, Any]]:
        """Prepare context documents for LLM processing."""
        pass
    
    @abstractmethod
    async def health_check(self) -> Dict[str, bool]:
        """Check health of all orchestrated providers."""
        pass
    
    def get_service_info(self) -> Dict[str, Any]:
        """Get information about the query orchestrator."""
        return {
            "name": self.__class__.__name__,
            "version": "1.0", 
            "capabilities": [
                "query_analysis",
                "multi_strategy_search",
                "adaptive_routing",
                "result_reranking", 
                "context_preparation",
                "workflow_orchestration"
            ],
            "type": "query_orchestrator",
            "supported_query_types": [qt.value for qt in QueryType],
            "supported_search_strategies": [ss.value for ss in SearchStrategy]
        } 