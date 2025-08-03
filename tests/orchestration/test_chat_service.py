import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any, List

from src.interfaces.chat_service_interface import (
    ChatServiceInterface,
    ChatRequest,
    ChatResponse
)
from src.interfaces.query_orchestrator_interface import QueryOrchestratorInterface
from src.interfaces.memory_interface import MemoryInterface


class TestChatService:
    """Test suite for Chat Service implementation."""
    
    @pytest.fixture
    def mock_query_orchestrator(self):
        """Create a mock query orchestrator for testing."""
        orchestrator = MagicMock(spec=QueryOrchestratorInterface)
        orchestrator.process_query = AsyncMock()
        return orchestrator
    
    @pytest.fixture
    def mock_memory_provider(self):
        """Create a mock memory provider for testing."""
        provider = MagicMock(spec=MemoryInterface)
        provider.store = AsyncMock()
        provider.retrieve = AsyncMock()
        provider.clear = AsyncMock()
        return provider
    
    @pytest.fixture
    def sample_chat_request(self):
        """Sample chat request for testing."""
        return ChatRequest(
            query="What is machine learning?",
            conversation_id="test_conv_123",
            use_reranking=True
        )
    
    @pytest.fixture
    def chat_service_config(self):
        """Configuration for chat service."""
        return {
            "max_conversation_length": 50,
            "conversation_ttl": 3600,
            "use_reranking": True,
            "default_llm_config": {
                "temperature": 0.7,
                "max_tokens": 2048
            }
        }
    
    @pytest.mark.asyncio
    async def test_chat_service_implements_interface(self):
        """Test that ChatService implements the correct interface."""
        from src.orchestration.chat_service import ChatService
        
        service = ChatService()
        assert isinstance(service, ChatServiceInterface)
    
    @pytest.mark.asyncio
    async def test_initialize_with_providers(self, mock_query_orchestrator, mock_memory_provider, chat_service_config):
        """Test initialization with provider dependencies."""
        from src.orchestration.chat_service import ChatService
        
        service = ChatService()
        service.query_orchestrator = mock_query_orchestrator
        service.memory_provider = mock_memory_provider
        
        await service.initialize(chat_service_config)
        
        assert service.config == chat_service_config
        assert service.max_conversation_length == 50
        assert service.conversation_ttl == 3600
        assert service.use_reranking is True
    
    @pytest.mark.asyncio
    async def test_generate_conversation_id(self, mock_query_orchestrator, mock_memory_provider, chat_service_config):
        """Test conversation ID generation."""
        from src.orchestration.chat_service import ChatService
        
        service = ChatService()
        service.query_orchestrator = mock_query_orchestrator
        service.memory_provider = mock_memory_provider
        await service.initialize(chat_service_config)
        
        conv_id_1 = service.generate_conversation_id()
        conv_id_2 = service.generate_conversation_id()
        
        assert conv_id_1 != conv_id_2
        assert len(conv_id_1) > 0
        assert conv_id_1.startswith("conv_")
    
    @pytest.mark.asyncio
    async def test_basic_chat_request(self, mock_query_orchestrator, mock_memory_provider, chat_service_config, sample_chat_request):
        """Test basic chat request processing."""
        from src.orchestration.chat_service import ChatService
        from src.interfaces.query_orchestrator_interface import QueryResult, QueryContext, QueryType, SearchStrategy
        
        # Mock query result
        mock_query_result = QueryResult(
            original_query=sample_chat_request.query,
            processed_query=sample_chat_request.query,
            search_results=[{"id": "doc1", "content": "Machine learning is a subset of AI", "score": 0.9}],
            reranked_results=[{"id": "doc1", "content": "Machine learning is a subset of AI", "score": 0.95}],
            context_documents=[{"id": "doc1", "content": "Machine learning is a subset of AI", "score": 0.95}],
            llm_response="Machine learning is a subset of artificial intelligence that enables computers to learn from data.",
            query_type=QueryType.FACTUAL,
            search_strategy_used=SearchStrategy.HYBRID,
            processing_steps=["query_analysis", "search_execution", "reranking", "context_preparation", "llm_generation"],
            timing_info={"total_time_seconds": 0.5},
            metadata={"error_occurred": False}
        )
        
        mock_query_orchestrator.process_query.return_value = mock_query_result
        
        service = ChatService()
        service.query_orchestrator = mock_query_orchestrator
        service.memory_provider = mock_memory_provider
        await service.initialize(chat_service_config)
        
        response = await service.chat(sample_chat_request)
        
        assert isinstance(response, ChatResponse)
        assert response.response == mock_query_result.llm_response
        assert response.conversation_id == sample_chat_request.conversation_id
        assert response.search_results_count == 1
        assert response.reranked_results_count == 1
        assert response.processing_time_ms > 0
    
    @pytest.mark.asyncio
    async def test_chat_with_conversation_history(self, mock_query_orchestrator, mock_memory_provider, chat_service_config):
        """Test chat with conversation history."""
        from src.orchestration.chat_service import ChatService
        from src.interfaces.query_orchestrator_interface import QueryResult, QueryContext, QueryType, SearchStrategy
        
        # Mock conversation history
        mock_memory_provider.retrieve.return_value = [
            {"role": "user", "content": "What is AI?", "timestamp": "2024-01-01T10:00:00Z"},
            {"role": "assistant", "content": "AI is artificial intelligence.", "timestamp": "2024-01-01T10:00:01Z"}
        ]
        
        # Mock query result
        mock_query_result = QueryResult(
            original_query="Tell me more about machine learning",
            processed_query="Tell me more about machine learning",
            search_results=[{"id": "doc1", "content": "Machine learning is a subset of AI", "score": 0.9}],
            reranked_results=[{"id": "doc1", "content": "Machine learning is a subset of AI", "score": 0.95}],
            context_documents=[{"id": "doc1", "content": "Machine learning is a subset of AI", "score": 0.95}],
            llm_response="Machine learning is a subset of artificial intelligence that enables computers to learn from data.",
            query_type=QueryType.FACTUAL,
            search_strategy_used=SearchStrategy.HYBRID,
            processing_steps=["query_analysis", "search_execution", "reranking", "context_preparation", "llm_generation"],
            timing_info={"total_time_seconds": 0.5},
            metadata={"error_occurred": False}
        )
        
        mock_query_orchestrator.process_query.return_value = mock_query_result
        
        service = ChatService()
        service.query_orchestrator = mock_query_orchestrator
        service.memory_provider = mock_memory_provider
        await service.initialize(chat_service_config)
        
        request = ChatRequest(
            query="Tell me more about machine learning",
            conversation_id="test_conv_123",
            use_reranking=True
        )
        
        response = await service.chat(request)
        
        assert isinstance(response, ChatResponse)
        assert response.response == mock_query_result.llm_response
        assert response.conversation_id == request.conversation_id
        
        # Verify history was retrieved
        mock_memory_provider.retrieve.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_chat_without_conversation_id(self, mock_query_orchestrator, mock_memory_provider, chat_service_config):
        """Test chat request without conversation ID (should generate one)."""
        from src.orchestration.chat_service import ChatService
        from src.interfaces.query_orchestrator_interface import QueryResult, QueryContext, QueryType, SearchStrategy
        
        # Mock query result
        mock_query_result = QueryResult(
            original_query="What is machine learning?",
            processed_query="What is machine learning?",
            search_results=[{"id": "doc1", "content": "Machine learning is a subset of AI", "score": 0.9}],
            reranked_results=[{"id": "doc1", "content": "Machine learning is a subset of AI", "score": 0.95}],
            context_documents=[{"id": "doc1", "content": "Machine learning is a subset of AI", "score": 0.95}],
            llm_response="Machine learning is a subset of artificial intelligence that enables computers to learn from data.",
            query_type=QueryType.FACTUAL,
            search_strategy_used=SearchStrategy.HYBRID,
            processing_steps=["query_analysis", "search_execution", "reranking", "context_preparation", "llm_generation"],
            timing_info={"total_time_seconds": 0.5},
            metadata={"error_occurred": False}
        )
        
        mock_query_orchestrator.process_query.return_value = mock_query_result
        
        service = ChatService()
        service.query_orchestrator = mock_query_orchestrator
        service.memory_provider = mock_memory_provider
        await service.initialize(chat_service_config)
        
        request = ChatRequest(
            query="What is machine learning?",
            conversation_id=None,
            use_reranking=True
        )
        
        response = await service.chat(request)
        
        assert isinstance(response, ChatResponse)
        assert response.conversation_id is not None
        assert response.conversation_id.startswith("conv_")
    
    @pytest.mark.asyncio
    async def test_clear_conversation(self, mock_query_orchestrator, mock_memory_provider, chat_service_config):
        """Test clearing conversation history."""
        from src.orchestration.chat_service import ChatService
        
        service = ChatService()
        service.query_orchestrator = mock_query_orchestrator
        service.memory_provider = mock_memory_provider
        await service.initialize(chat_service_config)
        
        conversation_id = "test_conv_123"
        result = await service.clear_conversation(conversation_id)
        
        assert result is True
        mock_memory_provider.clear.assert_called_once_with(conversation_id)
    
    @pytest.mark.asyncio
    async def test_get_conversation_history(self, mock_query_orchestrator, mock_memory_provider, chat_service_config):
        """Test retrieving conversation history."""
        from src.orchestration.chat_service import ChatService
        
        # Mock conversation history
        mock_history = [
            {"role": "user", "content": "What is AI?", "timestamp": "2024-01-01T10:00:00Z"},
            {"role": "assistant", "content": "AI is artificial intelligence.", "timestamp": "2024-01-01T10:00:01Z"},
            {"role": "user", "content": "Tell me more about machine learning", "timestamp": "2024-01-01T10:00:02Z"},
            {"role": "assistant", "content": "Machine learning is a subset of AI.", "timestamp": "2024-01-01T10:00:03Z"}
        ]
        
        mock_memory_provider.retrieve.return_value = mock_history
        
        service = ChatService()
        service.query_orchestrator = mock_query_orchestrator
        service.memory_provider = mock_memory_provider
        await service.initialize(chat_service_config)
        
        conversation_id = "test_conv_123"
        history = await service.get_conversation_history(conversation_id)
        
        assert history == mock_history
        mock_memory_provider.retrieve.assert_called_once_with(conversation_id)
    
    @pytest.mark.asyncio
    async def test_health_check(self, mock_query_orchestrator, mock_memory_provider, chat_service_config):
        """Test health check functionality."""
        from src.orchestration.chat_service import ChatService
        
        # Mock healthy providers
        mock_query_orchestrator.health_check.return_value = {"overall_health": True}
        mock_memory_provider.health_check.return_value = True
        
        service = ChatService()
        service.query_orchestrator = mock_query_orchestrator
        service.memory_provider = mock_memory_provider
        await service.initialize(chat_service_config)
        
        health_status = await service.health_check()
        
        assert isinstance(health_status, dict)
        assert "overall_health" in health_status
        assert health_status["overall_health"] is True
        assert "query_orchestrator" in health_status
        assert "memory_provider" in health_status
    
    @pytest.mark.asyncio
    async def test_get_service_info(self, mock_query_orchestrator, mock_memory_provider, chat_service_config):
        """Test service info retrieval."""
        from src.orchestration.chat_service import ChatService
        
        service = ChatService()
        service.query_orchestrator = mock_query_orchestrator
        service.memory_provider = mock_memory_provider
        await service.initialize(chat_service_config)
        
        service_info = service.get_service_info()
        
        assert isinstance(service_info, dict)
        assert "service_name" in service_info
        assert "version" in service_info
        assert "capabilities" in service_info
        assert "max_conversation_length" in service_info
        assert "conversation_ttl" in service_info
    
    @pytest.mark.asyncio
    async def test_chat_error_handling(self, mock_query_orchestrator, mock_memory_provider, chat_service_config, sample_chat_request):
        """Test error handling in chat processing."""
        from src.orchestration.chat_service import ChatService
        
        # Mock query orchestrator to fail
        mock_query_orchestrator.process_query.side_effect = Exception("Query processing failed")
        
        service = ChatService()
        service.query_orchestrator = mock_query_orchestrator
        service.memory_provider = mock_memory_provider
        await service.initialize(chat_service_config)
        
        response = await service.chat(sample_chat_request)
        
        assert isinstance(response, ChatResponse)
        assert "Error" in response.response
        assert response.conversation_id == sample_chat_request.conversation_id
        assert response.search_results_count == 0
        assert response.reranked_results_count is None
    
    @pytest.mark.asyncio
    async def test_enhanced_query_building(self, mock_query_orchestrator, mock_memory_provider, chat_service_config):
        """Test enhanced query building with conversation context."""
        from src.orchestration.chat_service import ChatService
        from src.interfaces.query_orchestrator_interface import QueryResult, QueryContext, QueryType, SearchStrategy
        
        # Mock conversation history
        mock_memory_provider.retrieve.return_value = [
            {"role": "user", "content": "What is AI?", "timestamp": "2024-01-01T10:00:00Z"},
            {"role": "assistant", "content": "AI is artificial intelligence.", "timestamp": "2024-01-01T10:00:01Z"}
        ]
        
        # Mock query result
        mock_query_result = QueryResult(
            original_query="Tell me more about machine learning",
            processed_query="Tell me more about machine learning",
            search_results=[{"id": "doc1", "content": "Machine learning is a subset of AI", "score": 0.9}],
            reranked_results=[{"id": "doc1", "content": "Machine learning is a subset of AI", "score": 0.95}],
            context_documents=[{"id": "doc1", "content": "Machine learning is a subset of AI", "score": 0.95}],
            llm_response="Machine learning is a subset of artificial intelligence that enables computers to learn from data.",
            query_type=QueryType.FACTUAL,
            search_strategy_used=SearchStrategy.HYBRID,
            processing_steps=["query_analysis", "search_execution", "reranking", "context_preparation", "llm_generation"],
            timing_info={"total_time_seconds": 0.5},
            metadata={"error_occurred": False}
        )
        
        mock_query_orchestrator.process_query.return_value = mock_query_result
        
        service = ChatService()
        service.query_orchestrator = mock_query_orchestrator
        service.memory_provider = mock_memory_provider
        await service.initialize(chat_service_config)
        
        request = ChatRequest(
            query="Tell me more about machine learning",
            conversation_id="test_conv_123",
            use_reranking=True
        )
        
        response = await service.chat(request)
        
        assert isinstance(response, ChatResponse)
        assert response.response == mock_query_result.llm_response
        
        # Verify that process_query was called with enhanced context
        mock_query_orchestrator.process_query.assert_called_once()
        call_args = mock_query_orchestrator.process_query.call_args[0][0]
        assert isinstance(call_args, QueryContext)
        assert "machine learning" in call_args.query.lower()
    
    @pytest.mark.asyncio
    async def test_conversation_length_limit(self, mock_query_orchestrator, mock_memory_provider, chat_service_config):
        """Test conversation length limiting."""
        from src.orchestration.chat_service import ChatService
        
        # Mock long conversation history
        long_history = []
        for i in range(60):  # More than the limit of 50
            long_history.append({
                "role": "user" if i % 2 == 0 else "assistant",
                "content": f"Message {i}",
                "timestamp": f"2024-01-01T10:00:{i:02d}Z"
            })
        
        mock_memory_provider.retrieve.return_value = long_history
        
        service = ChatService()
        service.query_orchestrator = mock_query_orchestrator
        service.memory_provider = mock_memory_provider
        await service.initialize(chat_service_config)
        
        conversation_id = "test_conv_123"
        history = await service.get_conversation_history(conversation_id)
        
        # Should be limited to max_conversation_length
        assert len(history) <= chat_service_config["max_conversation_length"]
    
    @pytest.mark.asyncio
    async def test_metadata_in_response(self, mock_query_orchestrator, mock_memory_provider, chat_service_config, sample_chat_request):
        """Test metadata inclusion in chat response."""
        from src.orchestration.chat_service import ChatService
        from src.interfaces.query_orchestrator_interface import QueryResult, QueryContext, QueryType, SearchStrategy
        
        # Mock query result with metadata
        mock_query_result = QueryResult(
            original_query=sample_chat_request.query,
            processed_query=sample_chat_request.query,
            search_results=[{"id": "doc1", "content": "Machine learning is a subset of AI", "score": 0.9}],
            reranked_results=[{"id": "doc1", "content": "Machine learning is a subset of AI", "score": 0.95}],
            context_documents=[{"id": "doc1", "content": "Machine learning is a subset of AI", "score": 0.95}],
            llm_response="Machine learning is a subset of artificial intelligence that enables computers to learn from data.",
            query_type=QueryType.FACTUAL,
            search_strategy_used=SearchStrategy.HYBRID,
            processing_steps=["query_analysis", "search_execution", "reranking", "context_preparation", "llm_generation"],
            timing_info={"total_time_seconds": 0.5},
            metadata={"error_occurred": False, "sources_used": 1}
        )
        
        mock_query_orchestrator.process_query.return_value = mock_query_result
        
        service = ChatService()
        service.query_orchestrator = mock_query_orchestrator
        service.memory_provider = mock_memory_provider
        await service.initialize(chat_service_config)
        
        response = await service.chat(sample_chat_request)
        
        assert isinstance(response, ChatResponse)
        assert response.metadata is not None
        assert "query_type" in response.metadata
        assert "search_strategy" in response.metadata
        assert "processing_steps" in response.metadata 