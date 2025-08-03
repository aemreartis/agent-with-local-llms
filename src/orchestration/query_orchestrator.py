import asyncio
import time
from typing import Dict, List, Any, Optional

from src.interfaces.query_orchestrator_interface import (
    QueryOrchestratorInterface,
    QueryContext,
    QueryResult,
    QueryType,
    SearchStrategy
)
from src.interfaces.search_orchestrator_interface import SearchOrchestratorInterface
from src.interfaces.llm_interface import LLMInterface
from src.interfaces.reranker_interface import RerankerInterface


class QueryOrchestrator(QueryOrchestratorInterface):
    """Orchestrates the complete query processing workflow."""
    
    def __init__(self):
        """Initialize the query orchestrator."""
        self.search_orchestrator: Optional[SearchOrchestratorInterface] = None
        self.llm_provider: Optional[LLMInterface] = None
        self.reranker_provider: Optional[RerankerInterface] = None
        self.config: Optional[Dict[str, Any]] = None
        self.default_search_strategy: str = "hybrid"
        self.context_limit: int = 10
        self.use_reranking: bool = True
    
    async def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize the query orchestrator with configuration."""
        self.config = config
        self.default_search_strategy = config.get("default_search_strategy", "hybrid")
        self.context_limit = config.get("context_limit", 10)
        self.use_reranking = config.get("use_reranking", True)
    
    async def analyze_query(self, query: str) -> QueryType:
        """Analyze query to determine its type."""
        query_lower = query.lower()
        
        # Check for analytical keywords first (more specific)
        if any(word in query_lower for word in ["compare", "contrast", "analyze", "difference", "similarities"]):
            return QueryType.ANALYTICAL
        
        # Check for creative keywords
        if any(word in query_lower for word in ["create", "generate", "write", "design", "imagine"]):
            return QueryType.CREATIVE
        
        # Check for search keywords
        if any(word in query_lower for word in ["search", "find", "look", "locate"]):
            return QueryType.SEARCH
        
        # Check for conversational keywords
        if any(word in query_lower for word in ["help", "explain", "understand", "can you"]):
            return QueryType.CONVERSATIONAL
        
        # Default to factual for what/when/where/who/how/why questions
        if any(word in query_lower for word in ["what", "when", "where", "who", "how", "why"]):
            return QueryType.FACTUAL
        
        # Default to conversational
        return QueryType.CONVERSATIONAL
    
    async def determine_search_strategy(self, query_type: QueryType) -> SearchStrategy:
        """Determine the best search strategy based on query type."""
        strategy_mapping = {
            QueryType.FACTUAL: SearchStrategy.HYBRID,
            QueryType.ANALYTICAL: SearchStrategy.HYBRID,
            QueryType.CREATIVE: SearchStrategy.VECTOR_ONLY,
            QueryType.SEARCH: SearchStrategy.KEYWORD_ONLY,
            QueryType.CONVERSATIONAL: SearchStrategy.VECTOR_ONLY
        }
        return strategy_mapping.get(query_type, SearchStrategy.HYBRID)
    
    async def execute_search(self, context: QueryContext) -> List[Dict[str, Any]]:
        """Execute search based on the query context."""
        if not self.search_orchestrator:
            return []
        
        # Create search request
        from src.interfaces.search_orchestrator_interface import SearchRequest, FusionStrategy
        
        if context.search_strategy == SearchStrategy.HYBRID:
            providers = ["vector", "bm25"]
        elif context.search_strategy == SearchStrategy.VECTOR_ONLY:
            providers = ["vector"]
        elif context.search_strategy == SearchStrategy.KEYWORD_ONLY:
            providers = ["bm25"]
        else:
            providers = ["vector", "bm25"]  # Default to hybrid
        
        search_request = SearchRequest(
            query=context.query,
            providers=providers,
            fusion_strategy=FusionStrategy.RANK_FUSION,
            top_k=context.context_limit
        )
        
        result = await self.search_orchestrator.search(search_request)
        return result.fused_results if result else []
    
    async def rerank_results(self, query: str, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Rerank search results using the reranker provider."""
        if not self.reranker_provider or not self.use_reranking:
            return results
        
        try:
            reranked_results = await self.reranker_provider.rerank(query, results)
            return reranked_results
        except Exception:
            return results
    
    async def prepare_context(self, query: str, results: List[Dict[str, Any]]) -> str:
        """Prepare context from search results for LLM generation."""
        if not results:
            return ""
        
        # Extract content from results
        contents = []
        for result in results[:self.context_limit]:
            if "content" in result:
                contents.append(result["content"])
        
        return "\n\n".join(contents)
    
    async def generate_response(self, query: str, context: str) -> str:
        """Generate response using the LLM provider."""
        if not self.llm_provider:
            return "Error: LLM provider not available"
        
        try:
            # Create prompt with context
            prompt = f"Context:\n{context}\n\nQuestion: {query}\n\nAnswer:"
            
            response = await self.llm_provider.generate(prompt)
            return response
        except Exception as e:
            return f"Error processing query: {str(e)}"
    
    async def process_query(self, context: QueryContext) -> QueryResult:
        """Process a complete query workflow."""
        start_time = time.time()
        error_occurred = False
        
        try:
            # Analyze query if not provided
            if context.query_type is None:
                context.query_type = await self.analyze_query(context.query)
            
            # Determine search strategy if not provided
            if context.search_strategy is None:
                context.search_strategy = await self.determine_search_strategy(context.query_type)
            
            # Execute search
            search_results = await self.execute_search(context)
            
            # Rerank results if enabled
            if self.use_reranking:
                search_results = await self.rerank_results(context.query, search_results)
            
            # Prepare context for LLM
            prepared_context = await self.prepare_context(context.query, search_results)
            
            # Generate response
            llm_response = await self.generate_response(context.query, prepared_context)
            
            # Check if LLM response indicates an error
            if llm_response.startswith("Error") or "Error processing query" in llm_response:
                error_occurred = True
            
            # Prepare sources
            sources = []
            for result in search_results:
                if "id" in result:
                    sources.append({
                        "id": result["id"],
                        "content": result.get("content", ""),
                        "score": result.get("score", 0.0)
                    })
            
            total_time = time.time() - start_time
            
            return QueryResult(
                original_query=context.query,
                processed_query=context.query,
                search_results=search_results,
                reranked_results=search_results if self.use_reranking else None,
                context_documents=sources,
                llm_response=llm_response,
                query_type=context.query_type,
                search_strategy_used=context.search_strategy,
                processing_steps=["query_analysis", "search_execution", "reranking", "context_preparation", "llm_generation"],
                timing_info={"total_time_seconds": total_time},
                metadata={"error_occurred": error_occurred}
            )
            
        except Exception as e:
            error_occurred = True
            total_time = time.time() - start_time
            
            return QueryResult(
                original_query=context.query,
                processed_query=context.query,
                search_results=[],
                reranked_results=None,
                context_documents=[],
                llm_response=f"Error processing query: {str(e)}",
                query_type=context.query_type,
                search_strategy_used=context.search_strategy,
                processing_steps=["error_occurred"],
                timing_info={"total_time_seconds": total_time},
                metadata={"error_occurred": error_occurred}
            )
    
    async def health_check(self) -> Dict[str, bool]:
        """Check health of all dependencies."""
        health_status = {
            "search_orchestrator": False,
            "llm_provider": False,
            "reranker_provider": False,
            "overall_health": False
        }
        
        try:
            if self.search_orchestrator:
                search_health = await self.search_orchestrator.health_check()
                health_status["search_orchestrator"] = search_health.get("overall_health", False)
            
            if self.llm_provider:
                health_status["llm_provider"] = await self.llm_provider.health_check()
            
            if self.reranker_provider:
                health_status["reranker_provider"] = await self.reranker_provider.health_check()
            
            # Overall health is True if at least search orchestrator and LLM are healthy
            health_status["overall_health"] = (
                health_status["search_orchestrator"] and 
                health_status["llm_provider"]
            )
            
        except Exception:
            pass
        
        return health_status
    
    def get_service_info(self) -> Dict[str, Any]:
        """Get service information."""
        return {
            "service_name": "QueryOrchestrator",
            "version": "1.0.0",
            "capabilities": [
                "query_analysis",
                "search_strategy_determination", 
                "multi_provider_search",
                "result_reranking",
                "context_preparation",
                "llm_response_generation"
            ],
            "dependencies": [
                "SearchOrchestrator",
                "LLMProvider", 
                "RerankerProvider"
            ]
        } 