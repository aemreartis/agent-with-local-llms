import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any, List

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


class TestQueryOrchestrator:
    """Test suite for Query Orchestrator implementation."""
    
    @pytest.fixture
    def mock_search_orchestrator(self):
        """Create a mock search orchestrator for testing."""
        orchestrator = MagicMock(spec=SearchOrchestratorInterface)
        orchestrator.search = AsyncMock()
        return orchestrator
    
    @pytest.fixture
    def mock_llm_provider(self):
        """Create a mock LLM provider for testing."""
        provider = MagicMock(spec=LLMInterface)
        provider.generate = AsyncMock()
        provider.embed = AsyncMock()
        return provider
    
    @pytest.fixture
    def mock_reranker_provider(self):
        """Create a mock reranker provider for testing."""
        provider = MagicMock(spec=RerankerInterface)
        provider.rerank = AsyncMock()
        return provider
    
    @pytest.fixture
    def sample_query_context(self):
        """Sample query context for testing."""
        return QueryContext(
            query="What is machine learning?",
            query_type=QueryType.FACTUAL,
            search_strategy=SearchStrategy.HYBRID,
            context_limit=10,
            use_reranking=True,
            llm_config={"temperature": 0.7, "max_tokens": 2048}
        )
    
    @pytest.fixture
    def query_orchestrator_config(self):
        """Configuration for query orchestrator."""
        return {
            "default_search_strategy": "hybrid",
            "context_limit": 10,
            "use_reranking": True,
            "llm_config": {
                "temperature": 0.7,
                "max_tokens": 2048
            }
        }
    
    @pytest.mark.asyncio
    async def test_query_orchestrator_implements_interface(self):
        """Test that QueryOrchestrator implements the correct interface."""
        from src.orchestration.query_orchestrator import QueryOrchestrator
        
        orchestrator = QueryOrchestrator()
        assert isinstance(orchestrator, QueryOrchestratorInterface)
    
    @pytest.mark.asyncio
    async def test_initialize_with_providers(self, mock_search_orchestrator, mock_llm_provider, mock_reranker_provider, query_orchestrator_config):
        """Test initialization with provider dependencies."""
        from src.orchestration.query_orchestrator import QueryOrchestrator
        
        orchestrator = QueryOrchestrator()
        orchestrator.search_orchestrator = mock_search_orchestrator
        orchestrator.llm_provider = mock_llm_provider
        orchestrator.reranker_provider = mock_reranker_provider
        
        await orchestrator.initialize(query_orchestrator_config)
        
        assert orchestrator.config == query_orchestrator_config
        assert orchestrator.default_search_strategy == "hybrid"
        assert orchestrator.context_limit == 10
        assert orchestrator.use_reranking is True
    
    @pytest.mark.asyncio
    async def test_analyze_query_factual(self, mock_search_orchestrator, mock_llm_provider, mock_reranker_provider, query_orchestrator_config):
        """Test query analysis for factual queries."""
        from src.orchestration.query_orchestrator import QueryOrchestrator
        
        orchestrator = QueryOrchestrator()
        orchestrator.search_orchestrator = mock_search_orchestrator
        orchestrator.llm_provider = mock_llm_provider
        orchestrator.reranker_provider = mock_reranker_provider
        await orchestrator.initialize(query_orchestrator_config)
        
        query_type = await orchestrator.analyze_query("What is the capital of France?")
        assert query_type in [QueryType.FACTUAL, QueryType.SEARCH]
    
    @pytest.mark.asyncio
    async def test_analyze_query_analytical(self, mock_search_orchestrator, mock_llm_provider, mock_reranker_provider, query_orchestrator_config):
        """Test query analysis for analytical queries."""
        from src.orchestration.query_orchestrator import QueryOrchestrator
        
        orchestrator = QueryOrchestrator()
        orchestrator.search_orchestrator = mock_search_orchestrator
        orchestrator.llm_provider = mock_llm_provider
        orchestrator.reranker_provider = mock_reranker_provider
        await orchestrator.initialize(query_orchestrator_config)
        
        query_type = await orchestrator.analyze_query("Compare and contrast machine learning vs deep learning")
        assert query_type in [QueryType.ANALYTICAL, QueryType.CREATIVE]
    
    @pytest.mark.asyncio
    async def test_analyze_query_conversational(self, mock_search_orchestrator, mock_llm_provider, mock_reranker_provider, query_orchestrator_config):
        """Test query analysis for conversational queries."""
        from src.orchestration.query_orchestrator import QueryOrchestrator
        
        orchestrator = QueryOrchestrator()
        orchestrator.search_orchestrator = mock_search_orchestrator
        orchestrator.llm_provider = mock_llm_provider
        orchestrator.reranker_provider = mock_reranker_provider
        await orchestrator.initialize(query_orchestrator_config)
        
        query_type = await orchestrator.analyze_query("Can you help me understand this topic?")
        assert query_type in [QueryType.CONVERSATIONAL, QueryType.CREATIVE]
    
    @pytest.mark.asyncio
    async def test_determine_search_strategy(self, mock_search_orchestrator, mock_llm_provider, mock_reranker_provider, query_orchestrator_config):
        """Test search strategy determination based on query type."""
        from src.orchestration.query_orchestrator import QueryOrchestrator
        
        orchestrator = QueryOrchestrator()
        orchestrator.search_orchestrator = mock_search_orchestrator
        orchestrator.llm_provider = mock_llm_provider
        orchestrator.reranker_provider = mock_reranker_provider
        await orchestrator.initialize(query_orchestrator_config)
        
        # Test different query types
        strategies = {
            QueryType.FACTUAL: SearchStrategy.HYBRID,
            QueryType.ANALYTICAL: SearchStrategy.HYBRID,
            QueryType.CREATIVE: SearchStrategy.VECTOR_ONLY,
            QueryType.SEARCH: SearchStrategy.KEYWORD_ONLY,
            QueryType.CONVERSATIONAL: SearchStrategy.VECTOR_ONLY
        }
        
        for query_type, expected_strategy in strategies.items():
            strategy = await orchestrator.determine_search_strategy(query_type)
            assert strategy == expected_strategy
    
    @pytest.mark.asyncio
    async def test_execute_search(self, mock_search_orchestrator, mock_llm_provider, mock_reranker_provider, query_orchestrator_config, sample_query_context):
        """Test search execution with different strategies."""
        from src.orchestration.query_orchestrator import QueryOrchestrator
        
        # Mock search results
        mock_search_results = MagicMock()
        mock_search_results.fused_results = [
            {"id": "doc1", "content": "Machine learning is a subset of AI", "score": 0.9},
            {"id": "doc2", "content": "ML algorithms learn from data", "score": 0.8}
        ]
        mock_search_orchestrator.search.return_value = mock_search_results
        
        orchestrator = QueryOrchestrator()
        orchestrator.search_orchestrator = mock_search_orchestrator
        orchestrator.llm_provider = mock_llm_provider
        orchestrator.reranker_provider = mock_reranker_provider
        await orchestrator.initialize(query_orchestrator_config)
        
        results = await orchestrator.execute_search(sample_query_context)
        
        assert results is not None
        assert len(results) > 0
        mock_search_orchestrator.search.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_rerank_results(self, mock_search_orchestrator, mock_llm_provider, mock_reranker_provider, query_orchestrator_config):
        """Test result reranking functionality."""
        from src.orchestration.query_orchestrator import QueryOrchestrator
        
        # Mock reranked results
        mock_reranker_provider.rerank.return_value = [
            {"id": "doc1", "content": "Machine learning is a subset of AI", "score": 0.95},
            {"id": "doc2", "content": "ML algorithms learn from data", "score": 0.85}
        ]
        
        orchestrator = QueryOrchestrator()
        orchestrator.search_orchestrator = mock_search_orchestrator
        orchestrator.llm_provider = mock_llm_provider
        orchestrator.reranker_provider = mock_reranker_provider
        await orchestrator.initialize(query_orchestrator_config)
        
        original_results = [
            {"id": "doc1", "content": "Machine learning is a subset of AI", "score": 0.9},
            {"id": "doc2", "content": "ML algorithms learn from data", "score": 0.8}
        ]
        
        reranked_results = await orchestrator.rerank_results("What is machine learning?", original_results)
        
        assert reranked_results is not None
        assert len(reranked_results) == len(original_results)
        mock_reranker_provider.rerank.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_prepare_context(self, mock_search_orchestrator, mock_llm_provider, mock_reranker_provider, query_orchestrator_config):
        """Test context preparation for LLM generation."""
        from src.orchestration.query_orchestrator import QueryOrchestrator
        
        orchestrator = QueryOrchestrator()
        orchestrator.search_orchestrator = mock_search_orchestrator
        orchestrator.llm_provider = mock_llm_provider
        orchestrator.reranker_provider = mock_reranker_provider
        await orchestrator.initialize(query_orchestrator_config)
        
        search_results = [
            {"id": "doc1", "content": "Machine learning is a subset of AI", "score": 0.9},
            {"id": "doc2", "content": "ML algorithms learn from data", "score": 0.8}
        ]
        
        context = await orchestrator.prepare_context("What is machine learning?", search_results)
        
        assert context is not None
        assert "Machine learning" in context
        assert len(context) > 0
    
    @pytest.mark.asyncio
    async def test_generate_response(self, mock_search_orchestrator, mock_llm_provider, mock_reranker_provider, query_orchestrator_config):
        """Test LLM response generation."""
        from src.orchestration.query_orchestrator import QueryOrchestrator
        
        # Mock LLM response
        mock_llm_provider.generate.return_value = "Machine learning is a subset of artificial intelligence that enables computers to learn and improve from experience without being explicitly programmed."
        
        orchestrator = QueryOrchestrator()
        orchestrator.search_orchestrator = mock_search_orchestrator
        orchestrator.llm_provider = mock_llm_provider
        orchestrator.reranker_provider = mock_reranker_provider
        await orchestrator.initialize(query_orchestrator_config)
        
        context = "Machine learning is a subset of AI. ML algorithms learn from data."
        response = await orchestrator.generate_response("What is machine learning?", context)
        
        assert response is not None
        assert "Machine learning" in response
        mock_llm_provider.generate.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_process_query_complete_workflow(self, mock_search_orchestrator, mock_llm_provider, mock_reranker_provider, query_orchestrator_config, sample_query_context):
        """Test complete query processing workflow."""
        from src.orchestration.query_orchestrator import QueryOrchestrator
        
        # Mock all dependencies
        mock_search_results = MagicMock()
        mock_search_results.fused_results = [
            {"id": "doc1", "content": "Machine learning is a subset of AI", "score": 0.9},
            {"id": "doc2", "content": "ML algorithms learn from data", "score": 0.8}
        ]
        mock_search_orchestrator.search.return_value = mock_search_results
        
        mock_reranker_provider.rerank.return_value = [
            {"id": "doc1", "content": "Machine learning is a subset of AI", "score": 0.95},
            {"id": "doc2", "content": "ML algorithms learn from data", "score": 0.85}
        ]
        
        mock_llm_provider.generate.return_value = "Machine learning is a subset of artificial intelligence that enables computers to learn and improve from experience without being explicitly programmed."
        
        orchestrator = QueryOrchestrator()
        orchestrator.search_orchestrator = mock_search_orchestrator
        orchestrator.llm_provider = mock_llm_provider
        orchestrator.reranker_provider = mock_reranker_provider
        await orchestrator.initialize(query_orchestrator_config)
        
        result = await orchestrator.process_query(sample_query_context)
        
        assert isinstance(result, QueryResult)
        assert result.original_query == sample_query_context.query
        assert result.llm_response is not None
        assert result.search_strategy_used is not None
        assert result.timing_info is not None
        assert result.context_documents is not None
    
    @pytest.mark.asyncio
    async def test_process_query_error_handling(self, mock_search_orchestrator, mock_llm_provider, mock_reranker_provider, query_orchestrator_config, sample_query_context):
        """Test error handling in query processing."""
        from src.orchestration.query_orchestrator import QueryOrchestrator
        
        # Mock LLM to fail
        mock_llm_provider.generate.side_effect = Exception("LLM generation failed")
        
        orchestrator = QueryOrchestrator()
        orchestrator.search_orchestrator = mock_search_orchestrator
        orchestrator.llm_provider = mock_llm_provider
        orchestrator.reranker_provider = mock_reranker_provider
        await orchestrator.initialize(query_orchestrator_config)
        
        result = await orchestrator.process_query(sample_query_context)
        
        assert isinstance(result, QueryResult)
        assert "Error processing query" in result.llm_response
        assert result.metadata.get("error_occurred", False) is True
    
    @pytest.mark.asyncio
    async def test_health_check(self, mock_search_orchestrator, mock_llm_provider, mock_reranker_provider, query_orchestrator_config):
        """Test health check functionality."""
        from src.orchestration.query_orchestrator import QueryOrchestrator
        
        # Mock healthy providers
        mock_search_orchestrator.health_check.return_value = {"overall_health": True}
        mock_llm_provider.health_check.return_value = True
        mock_reranker_provider.health_check.return_value = True
        
        orchestrator = QueryOrchestrator()
        orchestrator.search_orchestrator = mock_search_orchestrator
        orchestrator.llm_provider = mock_llm_provider
        orchestrator.reranker_provider = mock_reranker_provider
        await orchestrator.initialize(query_orchestrator_config)
        
        health_status = await orchestrator.health_check()
        
        assert isinstance(health_status, dict)
        assert "overall_health" in health_status
        assert health_status["overall_health"] is True
    
    def test_get_service_info(self):
        """Test service info retrieval."""
        from src.orchestration.query_orchestrator import QueryOrchestrator
        
        orchestrator = QueryOrchestrator()
        service_info = orchestrator.get_service_info()
        
        assert isinstance(service_info, dict)
        assert "service_name" in service_info
        assert "version" in service_info
        assert "capabilities" in service_info 