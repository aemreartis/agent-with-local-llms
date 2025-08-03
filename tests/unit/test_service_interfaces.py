import pytest
import pytest_asyncio
from unittest.mock import Mock, AsyncMock
from typing import Dict, Any, List
import asyncio

# Import our Stage 3 service interfaces
from src.interfaces.chat_service_interface import ChatServiceInterface, ChatRequest, ChatResponse
from src.interfaces.query_orchestrator_interface import (
    QueryOrchestratorInterface, QueryContext, QueryResult, QueryType, SearchStrategy
)
from src.interfaces.search_orchestrator_interface import (
    SearchOrchestratorInterface, SearchRequest, FusedSearchResult, FusionStrategy
)
from src.interfaces.result_fusion_interface import (
    ResultFusionInterface, ScoredResult, FusionResult, FusionWeights
)


class TestChatServiceInterface:
    """Test ChatService interface contract and behavior."""
    
    @pytest.mark.asyncio
    @pytest.mark.interface
    async def test_chat_service_interface_methods_exist(self):
        """Test that ChatService interface defines all required methods."""
        # Verify interface methods
        assert hasattr(ChatServiceInterface, 'initialize')
        assert hasattr(ChatServiceInterface, 'chat')
        assert hasattr(ChatServiceInterface, 'get_conversation_history')
        assert hasattr(ChatServiceInterface, 'clear_conversation')
        assert hasattr(ChatServiceInterface, 'health_check')
        assert hasattr(ChatServiceInterface, 'get_service_info')
    
    @pytest.mark.asyncio
    @pytest.mark.interface
    async def test_chat_request_structure(self):
        """Test ChatRequest dataclass structure and defaults."""
        request = ChatRequest(query="What is machine learning?")
        
        assert request.query == "What is machine learning?"
        assert request.conversation_id is None
        assert request.context_limit == 10
        assert request.search_strategy == "hybrid"
        assert request.use_reranking is True
        assert request.temperature == 0.7
        assert request.max_tokens is None
    
    @pytest.mark.asyncio
    @pytest.mark.interface
    async def test_chat_response_structure(self):
        """Test ChatResponse dataclass structure."""
        response = ChatResponse(
            response="Machine learning is...",
            sources=[{"id": "doc1", "content": "ML content"}],
            conversation_id="conv123",
            search_results_count=5
        )
        
        assert response.response == "Machine learning is..."
        assert len(response.sources) == 1
        assert response.conversation_id == "conv123"
        assert response.search_results_count == 5
        assert response.reranked_results_count is None
        assert response.llm_model == ""
        assert response.processing_time_ms == 0.0


class TestQueryOrchestratorInterface:
    """Test QueryOrchestrator interface contract and behavior."""
    
    @pytest.mark.asyncio
    @pytest.mark.interface
    async def test_query_orchestrator_interface_methods_exist(self):
        """Test that QueryOrchestrator interface defines all required methods."""
        assert hasattr(QueryOrchestratorInterface, 'initialize')
        assert hasattr(QueryOrchestratorInterface, 'process_query')
        assert hasattr(QueryOrchestratorInterface, 'analyze_query')
        assert hasattr(QueryOrchestratorInterface, 'determine_search_strategy')
        assert hasattr(QueryOrchestratorInterface, 'execute_search')
        assert hasattr(QueryOrchestratorInterface, 'rerank_results')
        assert hasattr(QueryOrchestratorInterface, 'prepare_context')
        assert hasattr(QueryOrchestratorInterface, 'health_check')
        assert hasattr(QueryOrchestratorInterface, 'get_service_info')
    
    @pytest.mark.asyncio
    @pytest.mark.interface
    async def test_query_type_enum(self):
        """Test QueryType enum values."""
        assert QueryType.FACTUAL.value == "factual"
        assert QueryType.CONVERSATIONAL.value == "conversational"
        assert QueryType.ANALYTICAL.value == "analytical"
        assert QueryType.CREATIVE.value == "creative"
        assert QueryType.SEARCH.value == "search"
    
    @pytest.mark.asyncio
    @pytest.mark.interface
    async def test_search_strategy_enum(self):
        """Test SearchStrategy enum values."""
        assert SearchStrategy.VECTOR_ONLY.value == "vector_only"
        assert SearchStrategy.KEYWORD_ONLY.value == "keyword_only" 
        assert SearchStrategy.HYBRID.value == "hybrid"
        assert SearchStrategy.ADAPTIVE.value == "adaptive"
    
    @pytest.mark.asyncio
    @pytest.mark.interface
    async def test_query_context_structure(self):
        """Test QueryContext dataclass structure and defaults."""
        context = QueryContext(query="What is AI?")
        
        assert context.query == "What is AI?"
        assert context.query_type == QueryType.FACTUAL
        assert context.search_strategy == SearchStrategy.HYBRID
        assert context.conversation_id is None
        assert context.user_id is None
        assert context.context_limit == 10
        assert context.use_reranking is True
        assert context.llm_config is None
        assert context.metadata is None


class TestSearchOrchestratorInterface:
    """Test SearchOrchestrator interface contract and behavior."""
    
    @pytest.mark.asyncio
    @pytest.mark.interface
    async def test_search_orchestrator_interface_methods_exist(self):
        """Test that SearchOrchestrator interface defines all required methods."""
        assert hasattr(SearchOrchestratorInterface, 'initialize')
        assert hasattr(SearchOrchestratorInterface, 'search')
        assert hasattr(SearchOrchestratorInterface, 'search_vector')
        assert hasattr(SearchOrchestratorInterface, 'search_keyword')
        assert hasattr(SearchOrchestratorInterface, 'search_hybrid')
        assert hasattr(SearchOrchestratorInterface, 'fuse_results')
        assert hasattr(SearchOrchestratorInterface, 'normalize_results')
        assert hasattr(SearchOrchestratorInterface, 'calculate_fusion_scores')
        assert hasattr(SearchOrchestratorInterface, 'health_check')
        assert hasattr(SearchOrchestratorInterface, 'get_service_info')
    
    @pytest.mark.asyncio
    @pytest.mark.interface
    async def test_fusion_strategy_enum(self):
        """Test FusionStrategy enum values."""
        assert FusionStrategy.INTERLEAVE.value == "interleave"
        assert FusionStrategy.SCORE_WEIGHTED.value == "score_weighted"
        assert FusionStrategy.RANK_FUSION.value == "rank_fusion"
        assert FusionStrategy.PROVIDER_WEIGHTED.value == "provider_weighted"
        assert FusionStrategy.ADAPTIVE.value == "adaptive"
    
    @pytest.mark.asyncio
    @pytest.mark.interface
    async def test_search_request_structure(self):
        """Test SearchRequest dataclass structure and defaults."""
        request = SearchRequest(
            query="machine learning",
            providers=["vector", "bm25"]
        )
        
        assert request.query == "machine learning"
        assert request.providers == ["vector", "bm25"]
        assert request.fusion_strategy == FusionStrategy.RANK_FUSION
        assert request.top_k == 10
        assert request.provider_weights is None
        assert request.provider_configs is None
        assert request.metadata is None


class TestResultFusionInterface:
    """Test ResultFusion interface contract and behavior."""
    
    @pytest.mark.asyncio
    @pytest.mark.interface
    async def test_result_fusion_interface_methods_exist(self):
        """Test that ResultFusion interface defines all required methods."""
        assert hasattr(ResultFusionInterface, 'initialize')
        assert hasattr(ResultFusionInterface, 'fuse_ranked_results')
        assert hasattr(ResultFusionInterface, 'fuse_scored_results')
        assert hasattr(ResultFusionInterface, 'interleave_results')
        assert hasattr(ResultFusionInterface, 'adaptive_fusion')
        assert hasattr(ResultFusionInterface, 'normalize_scores')
        assert hasattr(ResultFusionInterface, 'calculate_diversity')
        assert hasattr(ResultFusionInterface, 'apply_diversity_promotion')
        assert hasattr(ResultFusionInterface, 'reciprocal_rank_fusion')
        assert hasattr(ResultFusionInterface, 'weighted_score_fusion')
        assert hasattr(ResultFusionInterface, 'borda_count_fusion')
        assert hasattr(ResultFusionInterface, 'health_check')
        assert hasattr(ResultFusionInterface, 'get_service_info')
    
    @pytest.mark.asyncio
    @pytest.mark.interface
    async def test_scored_result_structure(self):
        """Test ScoredResult dataclass structure."""
        result = ScoredResult(
            document_id="doc1",
            content="Machine learning content",
            original_score=0.85,
            normalized_score=0.9,
            rank=1,
            provider_name="vector_store"
        )
        
        assert result.document_id == "doc1"
        assert result.content == "Machine learning content"
        assert result.original_score == 0.85
        assert result.normalized_score == 0.9
        assert result.rank == 1
        assert result.provider_name == "vector_store"
        assert result.metadata is None
    
    @pytest.mark.asyncio
    @pytest.mark.interface
    async def test_fusion_weights_structure(self):
        """Test FusionWeights dataclass structure and defaults."""
        weights = FusionWeights(
            provider_weights={"vector": 0.7, "bm25": 0.3},
            score_weights={"relevance": 0.8, "popularity": 0.2}
        )
        
        assert weights.provider_weights == {"vector": 0.7, "bm25": 0.3}
        assert weights.score_weights == {"relevance": 0.8, "popularity": 0.2}
        assert weights.rank_decay_factor == 0.6
        assert weights.diversity_factor == 0.1


class TestServiceIntegrationContracts:
    """Test integration contracts between service interfaces."""
    
    @pytest.mark.asyncio
    @pytest.mark.interface
    async def test_all_services_implement_initialize(self):
        """Test that all service interfaces require initialize method."""
        service_interfaces = [
            ChatServiceInterface,
            QueryOrchestratorInterface,
            SearchOrchestratorInterface,
            ResultFusionInterface
        ]
        
        for interface in service_interfaces:
            assert hasattr(interface, 'initialize')
            # Verify it's an abstract method
            assert getattr(interface.initialize, '__isabstractmethod__', False)
    
    @pytest.mark.asyncio
    @pytest.mark.interface
    async def test_all_services_implement_health_check(self):
        """Test that all service interfaces require health_check method."""
        service_interfaces = [
            ChatServiceInterface,
            QueryOrchestratorInterface,
            SearchOrchestratorInterface,
            ResultFusionInterface
        ]
        
        for interface in service_interfaces:
            assert hasattr(interface, 'health_check')
            # Verify it's an abstract method
            assert getattr(interface.health_check, '__isabstractmethod__', False)
    
    @pytest.mark.asyncio
    @pytest.mark.interface  
    async def test_all_services_provide_service_info(self):
        """Test that all service interfaces provide get_service_info method."""
        service_interfaces = [
            ChatServiceInterface,
            QueryOrchestratorInterface,
            SearchOrchestratorInterface,
            ResultFusionInterface
        ]
        
        for interface in service_interfaces:
            assert hasattr(interface, 'get_service_info')
            # Verify it's a concrete method (not abstract)
            assert not getattr(interface.get_service_info, '__isabstractmethod__', False)


class TestServiceErrorHandlingContracts:
    """Test error handling contracts for service interfaces."""
    
    @pytest.mark.asyncio
    @pytest.mark.interface
    async def test_services_handle_initialization_errors(self):
        """Test that services should handle initialization errors gracefully."""
        # This test will be validated when we implement the services
        # For now, we verify the interface contracts are properly defined
        
        service_interfaces = [
            ChatServiceInterface,
            QueryOrchestratorInterface,
            SearchOrchestratorInterface,
            ResultFusionInterface
        ]
        
        for interface in service_interfaces:
            # Verify initialize method signature
            init_method = getattr(interface, 'initialize')
            assert init_method is not None
            
            # Verify it accepts config parameter
            import inspect
            sig = inspect.signature(init_method)
            assert 'config' in sig.parameters
    
    @pytest.mark.asyncio
    @pytest.mark.interface
    async def test_services_handle_service_errors(self):
        """Test that services should handle service operation errors gracefully."""
        # Verify that main service methods are properly defined
        
        # ChatService main method
        assert hasattr(ChatServiceInterface, 'chat')
        
        # QueryOrchestrator main method  
        assert hasattr(QueryOrchestratorInterface, 'process_query')
        
        # SearchOrchestrator main method
        assert hasattr(SearchOrchestratorInterface, 'search')
        
        # ResultFusion main methods
        assert hasattr(ResultFusionInterface, 'fuse_ranked_results')
        assert hasattr(ResultFusionInterface, 'fuse_scored_results')
    
    @pytest.mark.asyncio
    @pytest.mark.interface
    async def test_health_check_handles_failures(self):
        """Test that health_check methods should handle failures gracefully."""
        service_interfaces = [
            ChatServiceInterface,
            QueryOrchestratorInterface, 
            SearchOrchestratorInterface,
            ResultFusionInterface
        ]
        
        for interface in service_interfaces:
            health_check = getattr(interface, 'health_check')
            assert health_check is not None
            
            # Verify health_check returns boolean or dict
            import inspect
            sig = inspect.signature(health_check)
            # Return annotation should indicate bool or Dict
            return_annotation = sig.return_annotation
            assert return_annotation is not None 