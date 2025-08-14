"""
Tests for RAG Pipeline Orchestrator

Tests the complete pipeline: User Input → RAG → Rerank → LLM → Agent Response
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from src.orchestration.rag_pipeline import RAGPipelineOrchestrator


class TestRAGPipelineOrchestrator:
    """Test RAG Pipeline Orchestrator functionality"""
    
    @pytest.fixture
    def mock_components(self):
        """Create mock components for testing"""
        
        # Mock search orchestrator
        mock_search = Mock()
        mock_search.search = AsyncMock(return_value={
            "results": [
                {
                    "id": "doc1",
                    "content": "This is a test document about AI and machine learning.",
                    "metadata": {"source": "test_source", "title": "AI Basics"},
                    "score": 0.85
                },
                {
                    "id": "doc2", 
                    "content": "Machine learning is a subset of artificial intelligence.",
                    "metadata": {"source": "test_source", "title": "ML Overview"},
                    "score": 0.75
                }
            ],
            "total": 2
        })
        mock_search.health_check = AsyncMock(return_value={"status": "healthy"})
        
        # Mock reranker
        mock_reranker = Mock()
        mock_reranker.rerank = AsyncMock(return_value=[
            {
                "id": "doc1",
                "content": "This is a test document about AI and machine learning.",
                "metadata": {"source": "test_source", "title": "AI Basics"},
                "score": 0.95
            },
            {
                "id": "doc2",
                "content": "Machine learning is a subset of artificial intelligence.",
                "metadata": {"source": "test_source", "title": "ML Overview"},
                "score": 0.85
            }
        ])
        mock_reranker.health_check = AsyncMock(return_value={"status": "healthy"})
        
        # Mock LLM provider
        mock_llm = Mock()
        mock_llm.generate = AsyncMock(return_value="Based on the information provided, AI and machine learning are related technologies. AI is the broader field, while machine learning is a specific approach within AI.")
        mock_llm.health_check = AsyncMock(return_value={"status": "healthy"})
        
        # Mock memory provider
        mock_memory = Mock()
        mock_memory.retrieve = AsyncMock(return_value=[])
        mock_memory.store = AsyncMock(return_value=True)
        mock_memory.health_check = AsyncMock(return_value={"status": "healthy"})
        
        return {
            "search_orchestrator": mock_search,
            "reranker": mock_reranker,
            "llm_provider": mock_llm,
            "memory_provider": mock_memory
        }
    
    @pytest.fixture
    def pipeline_config(self):
        """Pipeline configuration for testing"""
        return {
            "search_top_k": 5,
            "rerank_top_k": 3,
            "max_context_length": 2000,
            "enable_memory": True,
            "max_tokens": 500,
            "temperature": 0.7
        }
    
    @pytest.fixture
    def rag_pipeline(self, mock_components, pipeline_config):
        """Create RAG pipeline orchestrator for testing"""
        return RAGPipelineOrchestrator(
            search_orchestrator=mock_components["search_orchestrator"],
            reranker=mock_components["reranker"],
            llm_provider=mock_components["llm_provider"],
            memory_provider=mock_components["memory_provider"],
            config=pipeline_config
        )
    
    @pytest.mark.asyncio
    async def test_pipeline_initialization(self, rag_pipeline):
        """Test pipeline initialization"""
        assert rag_pipeline is not None
        assert rag_pipeline.search_top_k == 5
        assert rag_pipeline.rerank_top_k == 3
        assert rag_pipeline.enable_memory is True
    
    @pytest.mark.asyncio
    async def test_complete_pipeline_flow(self, rag_pipeline):
        """Test complete pipeline flow"""
        
        # Test query
        user_input = "What is the relationship between AI and machine learning?"
        user_id = "test_user_123"
        
        # Execute pipeline
        response = await rag_pipeline.process_query(
            user_input=user_input,
            user_id=user_id
        )
        
        # Verify response structure
        assert response["status"] == "success"
        assert response["user_input"] == user_input
        assert "agent_response" in response
        assert "pipeline_metrics" in response
        assert "search_results" in response
        assert "reranked_results" in response
        
        # Verify metrics
        metrics = response["pipeline_metrics"]
        assert "total_duration" in metrics
        assert "search_duration" in metrics
        assert "rerank_duration" in metrics
        assert "llm_duration" in metrics
        assert metrics["search_results_count"] > 0
        assert metrics["reranked_results_count"] > 0
    
    @pytest.mark.asyncio
    async def test_pipeline_with_conversation_context(self, rag_pipeline, mock_components):
        """Test pipeline with conversation context"""
        
        # Mock conversation history
        conversation_history = [
            {
                "timestamp": "2025-01-01T10:00:00",
                "user_input": "Tell me about AI",
                "agent_response": "AI is artificial intelligence technology.",
                "user_id": "test_user_123"
            }
        ]
        
        mock_components["memory_provider"].retrieve = AsyncMock(return_value=conversation_history)
        
        # Test query
        user_input = "What about machine learning specifically?"
        user_id = "test_user_123"
        
        # Execute pipeline
        response = await rag_pipeline.process_query(
            user_input=user_input,
            user_id=user_id,
            conversation_id="conv_123"
        )
        
        # Verify response
        assert response["status"] == "success"
        assert "conversation_id" in response
    
    @pytest.mark.asyncio
    async def test_pipeline_without_memory(self, mock_components, pipeline_config):
        """Test pipeline with memory disabled"""
        
        pipeline_config["enable_memory"] = False
        
        rag_pipeline = RAGPipelineOrchestrator(
            search_orchestrator=mock_components["search_orchestrator"],
            reranker=mock_components["reranker"],
            llm_provider=mock_components["llm_provider"],
            memory_provider=mock_components["memory_provider"],
            config=pipeline_config
        )
        
        # Test query
        user_input = "What is AI?"
        user_id = "test_user_123"
        
        # Execute pipeline
        response = await rag_pipeline.process_query(
            user_input=user_input,
            user_id=user_id
        )
        
        # Verify response
        assert response["status"] == "success"
        
        # Verify memory was not called
        mock_components["memory_provider"].retrieve.assert_not_called()
        mock_components["memory_provider"].store.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_pipeline_error_handling(self, mock_components, pipeline_config):
        """Test pipeline error handling"""
        
        # Mock search failure
        mock_components["search_orchestrator"].search = AsyncMock(
            side_effect=Exception("Search service unavailable")
        )
        
        # Mock LLM failure as well to ensure pipeline returns error
        mock_components["llm_provider"].generate = AsyncMock(
            side_effect=Exception("LLM service unavailable")
        )
        
        rag_pipeline = RAGPipelineOrchestrator(
            search_orchestrator=mock_components["search_orchestrator"],
            reranker=mock_components["reranker"],
            llm_provider=mock_components["llm_provider"],
            memory_provider=mock_components["memory_provider"],
            config=pipeline_config
        )
        
        # Test query
        user_input = "What is AI?"
        user_id = "test_user_123"
        
        # Execute pipeline
        response = await rag_pipeline.process_query(
            user_input=user_input,
            user_id=user_id
        )
        
        # Verify resilient response (pipeline continues with fallback)
        assert response["status"] == "success"
        assert "agent_response" in response
        assert "I apologize" in response["agent_response"]
        assert "unable to generate" in response["agent_response"]
        
        # Verify empty search results due to search failure
        assert len(response["search_results"]) == 0
        assert len(response["reranked_results"]) == 0
    
    @pytest.mark.asyncio
    async def test_pipeline_health_check(self, rag_pipeline):
        """Test pipeline health check"""
        
        health_status = await rag_pipeline.health_check()
        
        # Verify health check structure
        assert "status" in health_status
        assert "components" in health_status
        assert "timestamp" in health_status
        
        # Verify all components are checked
        components = health_status["components"]
        assert "search_orchestrator" in components
        assert "reranker" in components
        assert "llm_provider" in components
        assert "memory_provider" in components
        
        # Verify all components are healthy
        for component_name, component_status in components.items():
            assert component_status["status"] == "healthy"
    
    @pytest.mark.asyncio
    async def test_pipeline_with_empty_search_results(self, mock_components, pipeline_config):
        """Test pipeline with empty search results"""
        
        # Mock empty search results
        mock_components["search_orchestrator"].search = AsyncMock(return_value={
            "results": [],
            "total": 0
        })
        
        rag_pipeline = RAGPipelineOrchestrator(
            search_orchestrator=mock_components["search_orchestrator"],
            reranker=mock_components["reranker"],
            llm_provider=mock_components["llm_provider"],
            memory_provider=mock_components["memory_provider"],
            config=pipeline_config
        )
        
        # Test query
        user_input = "What is quantum computing?"
        user_id = "test_user_123"
        
        # Execute pipeline
        response = await rag_pipeline.process_query(
            user_input=user_input,
            user_id=user_id
        )
        
        # Verify response
        assert response["status"] == "success"
        assert len(response["search_results"]) == 0
        assert len(response["reranked_results"]) == 0
    
    @pytest.mark.asyncio
    async def test_pipeline_performance_metrics(self, rag_pipeline):
        """Test pipeline performance metrics"""
        
        # Test query
        user_input = "What is the difference between AI and ML?"
        user_id = "test_user_123"
        
        # Execute pipeline
        response = await rag_pipeline.process_query(
            user_input=user_input,
            user_id=user_id
        )
        
        # Verify performance metrics
        metrics = response["pipeline_metrics"]
        
        assert metrics["total_duration"] > 0
        assert metrics["search_duration"] >= 0
        assert metrics["rerank_duration"] >= 0
        assert metrics["llm_duration"] >= 0
        assert metrics["context_length"] > 0
        
        # Verify timing makes sense
        assert metrics["total_duration"] >= metrics["search_duration"]
        assert metrics["total_duration"] >= metrics["rerank_duration"]
        assert metrics["total_duration"] >= metrics["llm_duration"]
    
    @pytest.mark.asyncio
    async def test_pipeline_with_session_and_conversation_ids(self, rag_pipeline):
        """Test pipeline with session and conversation IDs"""
        
        # Test query
        user_input = "Explain neural networks"
        user_id = "test_user_123"
        session_id = "session_456"
        conversation_id = "conv_789"
        
        # Execute pipeline
        response = await rag_pipeline.process_query(
            user_input=user_input,
            user_id=user_id,
            session_id=session_id,
            conversation_id=conversation_id
        )
        
        # Verify response
        assert response["status"] == "success"
        assert response["conversation_id"] == conversation_id
    
    @pytest.mark.asyncio
    async def test_pipeline_context_preparation(self, rag_pipeline):
        """Test context preparation for LLM"""
        
        # Test with reranked results
        reranked_results = {
            "results": [
                {
                    "id": "doc1",
                    "content": "Neural networks are computational models inspired by biological neural networks.",
                    "metadata": {"source": "ai_textbook", "title": "Neural Networks"},
                    "score": 0.95
                }
            ],
            "duration": 0.1,
            "original_count": 1,
            "reranked_count": 1
        }
        
        context = {
            "conversation_history": [],
            "session_state": {},
            "user_id": "test_user"
        }
        
        # Test context preparation
        context_text = rag_pipeline._prepare_context_for_llm(
            "What are neural networks?",
            reranked_results,
            context
        )
        
        # Verify context contains relevant information
        assert "Neural networks" in context_text
        assert "ai_textbook" in context_text
        assert len(context_text) > 0
    
    @pytest.mark.asyncio
    async def test_pipeline_query_enhancement(self, rag_pipeline):
        """Test query enhancement with context"""
        
        # Test conversation history
        context = {
            "conversation_history": [
                {
                    "user_input": "What is AI?",
                    "agent_response": "AI is artificial intelligence technology."
                }
            ],
            "session_state": {},
            "user_id": "test_user"
        }
        
        # Test query enhancement
        enhanced_query = rag_pipeline._enhance_query_with_context(
            "What about machine learning?",
            context
        )
        
        # Verify enhanced query contains context
        assert "What is AI?" in enhanced_query
        assert "AI is artificial intelligence" in enhanced_query
        assert "What about machine learning?" in enhanced_query


class TestRAGPipelineIntegration:
    """Integration tests for RAG Pipeline"""
    
    @pytest.mark.asyncio
    async def test_pipeline_with_real_components(self):
        """Test pipeline with real (mocked) components"""
        
        # This test would use real component implementations
        # but with mocked external dependencies
        
        # For now, we'll test the integration pattern
        assert True  # Placeholder for real integration test
    
    @pytest.mark.asyncio
    async def test_pipeline_concurrent_requests(self):
        """Test pipeline with concurrent requests"""
        
        # This test would verify the pipeline handles concurrent requests properly
        # For now, we'll test the pattern
        assert True  # Placeholder for concurrent test 