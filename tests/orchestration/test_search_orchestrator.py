import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any, List

from src.interfaces.search_orchestrator_interface import (
    SearchOrchestratorInterface,
    SearchRequest,
    FusedSearchResult,
    ProviderSearchResult,
    FusionStrategy
)
from src.registry.provider_registry import ProviderRegistry


class TestSearchOrchestrator:
    """Test suite for Search Orchestrator implementation."""
    
    @pytest.fixture
    def mock_provider_registry(self):
        """Create a mock provider registry for testing."""
        registry = MagicMock(spec=ProviderRegistry)
        registry.get_provider = AsyncMock()
        return registry
    
    @pytest.fixture
    def search_orchestrator_config(self):
        """Configuration for search orchestrator."""
        return {
            "default_fusion_strategy": "rank_fusion",
            "provider_weights": {
                "vector": 0.6,
                "keyword": 0.4
            },
            "parallel_execution": True,
            "timeout_seconds": 5.0,
            "rrf_k_parameter": 60.0
        }
    
    @pytest.fixture
    def sample_search_request(self):
        """Sample search request for testing."""
        return SearchRequest(
            query="test query",
            providers=["vector", "bm25"],
            fusion_strategy=FusionStrategy.RANK_FUSION,
            top_k=10
        )
    
    @pytest.fixture
    def mock_vector_results(self):
        """Mock vector search results."""
        return [
            {"id": "doc1", "content": "vector result 1", "score": 0.9},
            {"id": "doc2", "content": "vector result 2", "score": 0.8}
        ]
    
    @pytest.fixture
    def mock_keyword_results(self):
        """Mock keyword search results."""
        return [
            {"id": "doc3", "content": "keyword result 1", "score": 0.85},
            {"id": "doc4", "content": "keyword result 2", "score": 0.75}
        ]
    
    async def test_search_orchestrator_implements_interface(self):
        """Test that SearchOrchestrator implements the correct interface."""
        from src.orchestration.search_orchestrator import SearchOrchestrator
        
        orchestrator = SearchOrchestrator()
        assert isinstance(orchestrator, SearchOrchestratorInterface)
    
    async def test_initialize_with_provider_registry(self, mock_provider_registry, search_orchestrator_config):
        """Test initialization with provider registry."""
        from src.orchestration.search_orchestrator import SearchOrchestrator
        
        orchestrator = SearchOrchestrator()
        orchestrator.registry = mock_provider_registry
        await orchestrator.initialize(search_orchestrator_config)
        
        # Verify that providers are requested from registry
        mock_provider_registry.get_provider.assert_called()
    
    async def test_vector_search_only(self, mock_provider_registry, search_orchestrator_config):
        """Test vector search using QdrantProvider."""
        from src.orchestration.search_orchestrator import SearchOrchestrator
        
        # Mock vector store provider
        mock_vector_provider = AsyncMock()
        mock_vector_provider.retrieve.return_value = [
            {"id": "doc1", "content": "test content", "score": 0.9}
        ]
        mock_provider_registry.get_provider.return_value = mock_vector_provider
        
        orchestrator = SearchOrchestrator()
        orchestrator.registry = mock_provider_registry
        await orchestrator.initialize(search_orchestrator_config)
        
        result = await orchestrator.search_vector("test query", top_k=5)
        
        assert isinstance(result, ProviderSearchResult)
        assert result.provider_name == "vector"
        assert result.provider_type == "vector_store"
        assert len(result.results) > 0
        assert result.query_time_ms > 0
    
    async def test_keyword_search_only(self, mock_provider_registry, search_orchestrator_config):
        """Test keyword search using BM25Provider."""
        from src.orchestration.search_orchestrator import SearchOrchestrator
        
        # Mock search engine provider
        mock_keyword_provider = AsyncMock()
        mock_keyword_provider.search.return_value = [
            {"id": "doc1", "content": "test content", "score": 0.85}
        ]
        mock_provider_registry.get_provider.return_value = mock_keyword_provider
        
        orchestrator = SearchOrchestrator()
        orchestrator.registry = mock_provider_registry
        await orchestrator.initialize(search_orchestrator_config)
        
        result = await orchestrator.search_keyword("test query", top_k=5)
        
        assert isinstance(result, ProviderSearchResult)
        assert result.provider_name == "keyword"
        assert result.provider_type == "search_engine"
        assert len(result.results) > 0
        assert result.query_time_ms > 0
    
    async def test_hybrid_search_fusion(self, mock_provider_registry, search_orchestrator_config, sample_search_request):
        """Test hybrid search with result fusion."""
        from src.orchestration.search_orchestrator import SearchOrchestrator
        
        # Mock both providers
        mock_vector_provider = AsyncMock()
        mock_vector_provider.retrieve.return_value = [
            {"id": "doc1", "content": "vector result", "score": 0.9}
        ]
        
        mock_keyword_provider = AsyncMock()
        mock_keyword_provider.search.return_value = [
            {"id": "doc2", "content": "keyword result", "score": 0.85}
        ]
        
        # Configure registry to return different providers
        def get_provider_side_effect(category, name=None):
            if category == "vector_store":
                return mock_vector_provider
            elif category == "search_engine":
                return mock_keyword_provider
            return AsyncMock()
        
        mock_provider_registry.get_provider.side_effect = get_provider_side_effect
        
        orchestrator = SearchOrchestrator()
        orchestrator.registry = mock_provider_registry
        await orchestrator.initialize(search_orchestrator_config)
        
        result = await orchestrator.search_hybrid("test query", top_k=10)
        
        assert isinstance(result, FusedSearchResult)
        assert result.query == "test query"
        assert result.fusion_strategy_used == FusionStrategy.RANK_FUSION
        assert result.total_providers_used == 2
        assert len(result.fused_results) > 0
        assert result.total_query_time_ms > 0
        assert result.fusion_time_ms > 0
    
    async def test_parallel_provider_execution(self, mock_provider_registry, search_orchestrator_config, sample_search_request):
        """Test parallel execution of multiple providers."""
        from src.orchestration.search_orchestrator import SearchOrchestrator
        
        # Mock providers with delays to test parallelism
        async def delayed_vector_search(*args, **kwargs):
            await asyncio.sleep(0.1)  # Simulate processing time
            return [{"id": "doc1", "content": "vector result", "score": 0.9}]
        
        async def delayed_keyword_search(*args, **kwargs):
            await asyncio.sleep(0.1)  # Simulate processing time
            return [{"id": "doc2", "content": "keyword result", "score": 0.85}]
        
        mock_vector_provider = AsyncMock()
        mock_vector_provider.retrieve = delayed_vector_search
        
        mock_keyword_provider = AsyncMock()
        mock_keyword_provider.search = delayed_keyword_search
        
        def get_provider_side_effect(category, name=None):
            if category == "vector_store":
                return mock_vector_provider
            elif category == "search_engine":
                return mock_keyword_provider
            return AsyncMock()
        
        mock_provider_registry.get_provider.side_effect = get_provider_side_effect
        
        orchestrator = SearchOrchestrator()
        orchestrator.registry = mock_provider_registry
        await orchestrator.initialize(search_orchestrator_config)
        
        start_time = asyncio.get_event_loop().time()
        result = await orchestrator.search(sample_search_request)
        end_time = asyncio.get_event_loop().time()
        
        # If truly parallel, total time should be less than sum of individual times
        # (0.1 + 0.1 = 0.2 seconds)
        assert (end_time - start_time) < 0.15  # Should be much less than 0.2
        assert isinstance(result, FusedSearchResult)
    
    async def test_reciprocal_rank_fusion(self, mock_provider_registry, search_orchestrator_config):
        """Test RRF fusion algorithm."""
        from src.orchestration.search_orchestrator import SearchOrchestrator
        
        # Create provider results with different rankings
        provider_results = [
            ProviderSearchResult(
                provider_name="vector",
                provider_type="vector_store",
                results=[
                    {"id": "doc1", "content": "result 1", "score": 0.9, "rank": 1},
                    {"id": "doc2", "content": "result 2", "score": 0.8, "rank": 2}
                ],
                query_time_ms=50.0,
                total_results=2
            ),
            ProviderSearchResult(
                provider_name="keyword",
                provider_type="search_engine", 
                results=[
                    {"id": "doc2", "content": "result 2", "score": 0.85, "rank": 1},
                    {"id": "doc3", "content": "result 3", "score": 0.75, "rank": 2}
                ],
                query_time_ms=30.0,
                total_results=2
            )
        ]
        
        orchestrator = SearchOrchestrator()
        await orchestrator.initialize(search_orchestrator_config)
        
        fused_results = await orchestrator.fuse_results(
            provider_results, 
            FusionStrategy.RANK_FUSION, 
            top_k=5
        )
        
        assert len(fused_results) > 0
        # doc2 should have higher RRF score (rank 1 in keyword + rank 2 in vector)
        # doc1 should have lower RRF score (rank 1 in vector only)
        # doc3 should have lowest RRF score (rank 2 in keyword only)
        
        # Verify results are sorted by RRF score
        if len(fused_results) >= 2:
            assert fused_results[0]["rrf_score"] >= fused_results[1]["rrf_score"]
    
    async def test_result_normalization(self, mock_provider_registry, search_orchestrator_config):
        """Test normalization of results from different providers."""
        from src.orchestration.search_orchestrator import SearchOrchestrator
        
        # Results with different score ranges
        vector_results = [
            {"id": "doc1", "content": "result 1", "score": 0.95},
            {"id": "doc2", "content": "result 2", "score": 0.85}
        ]
        
        keyword_results = [
            {"id": "doc3", "content": "result 3", "score": 0.75},
            {"id": "doc4", "content": "result 4", "score": 0.65}
        ]
        
        orchestrator = SearchOrchestrator()
        await orchestrator.initialize(search_orchestrator_config)
        
        # Test normalization
        normalized_vector = await orchestrator.normalize_results(vector_results, "vector")
        normalized_keyword = await orchestrator.normalize_results(keyword_results, "keyword")
        
        assert len(normalized_vector) == len(vector_results)
        assert len(normalized_keyword) == len(keyword_results)
        
        # Check that normalized scores are in reasonable range (0-1)
        for result in normalized_vector + normalized_keyword:
            assert 0 <= result["normalized_score"] <= 1
    
    async def test_provider_failure_handling(self, mock_provider_registry, search_orchestrator_config, sample_search_request):
        """Test graceful handling of provider failures."""
        from src.orchestration.search_orchestrator import SearchOrchestrator
        
        # Mock vector provider to fail
        mock_vector_provider = AsyncMock()
        mock_vector_provider.retrieve.side_effect = Exception("Vector provider failed")
        
        # Mock keyword provider to succeed
        mock_keyword_provider = AsyncMock()
        mock_keyword_provider.search.return_value = [
            {"id": "doc1", "content": "keyword result", "score": 0.85}
        ]
        
        def get_provider_side_effect(category, name=None):
            if category == "vector_store":
                return mock_vector_provider
            elif category == "search_engine":
                return mock_keyword_provider
            return AsyncMock()
        
        mock_provider_registry.get_provider.side_effect = get_provider_side_effect
        
        orchestrator = SearchOrchestrator()
        orchestrator.registry = mock_provider_registry
        await orchestrator.initialize(search_orchestrator_config)
        
        # Should not raise exception, should handle failure gracefully
        result = await orchestrator.search(sample_search_request)
        
        assert isinstance(result, FusedSearchResult)
        # Should still have results from working provider
        assert len(result.provider_results) >= 1
        assert result.provider_results[0].provider_name == "keyword"
    
    async def test_fusion_strategies(self, mock_provider_registry, search_orchestrator_config):
        """Test different fusion strategies."""
        from src.orchestration.search_orchestrator import SearchOrchestrator
        
        provider_results = [
            ProviderSearchResult(
                provider_name="vector",
                provider_type="vector_store",
                results=[{"id": "doc1", "content": "result 1", "score": 0.9}],
                query_time_ms=50.0,
                total_results=1
            ),
            ProviderSearchResult(
                provider_name="keyword",
                provider_type="search_engine",
                results=[{"id": "doc2", "content": "result 2", "score": 0.85}],
                query_time_ms=30.0,
                total_results=1
            )
        ]
        
        orchestrator = SearchOrchestrator()
        await orchestrator.initialize(search_orchestrator_config)
        
        # Test different fusion strategies
        strategies = [
            FusionStrategy.RANK_FUSION,
            FusionStrategy.SCORE_WEIGHTED,
            FusionStrategy.INTERLEAVE
        ]
        
        for strategy in strategies:
            fused_results = await orchestrator.fuse_results(
                provider_results, 
                strategy, 
                top_k=5
            )
            assert len(fused_results) > 0
    
    async def test_health_check(self, mock_provider_registry, search_orchestrator_config):
        """Test health check functionality."""
        from src.orchestration.search_orchestrator import SearchOrchestrator
        
        # Mock healthy providers
        mock_vector_provider = AsyncMock()
        mock_vector_provider.health_check.return_value = True
        
        mock_keyword_provider = AsyncMock()
        mock_keyword_provider.health_check.return_value = True
        
        def get_provider_side_effect(category, name=None):
            if category == "vector_store":
                return mock_vector_provider
            elif category == "search_engine":
                return mock_keyword_provider
            return AsyncMock()
        
        mock_provider_registry.get_provider.side_effect = get_provider_side_effect
        
        orchestrator = SearchOrchestrator()
        orchestrator.registry = mock_provider_registry
        await orchestrator.initialize(search_orchestrator_config)
        
        health_status = await orchestrator.health_check()
        
        assert isinstance(health_status, dict)
        assert "vector_store" in health_status
        assert "search_engine" in health_status
        assert health_status["vector_store"] is True
        assert health_status["search_engine"] is True
    
    def test_get_service_info(self):
        """Test service info method."""
        from src.orchestration.search_orchestrator import SearchOrchestrator
        
        orchestrator = SearchOrchestrator()
        service_info = orchestrator.get_service_info()
        
        assert isinstance(service_info, dict)
        assert "name" in service_info
        assert "version" in service_info
        assert "capabilities" in service_info
        assert "type" in service_info
        assert service_info["type"] == "search_orchestrator" 