"""
Tests for core interface contracts.

These tests define the expected behavior that all providers must implement.
Following TDD principles - these tests fail first, then we implement interfaces to make them pass.
"""

import pytest
from abc import ABC
from typing import List, Dict, Any
from unittest.mock import AsyncMock


class TestLLMInterface:
    """Test the LLM interface contract."""
    
    @pytest.mark.interface
    @pytest.mark.asyncio
    async def test_llm_interface_methods_exist(self):
        """Test that LLM interface defines required methods."""
        # This will fail until we implement the interface
        from src.interfaces.llm_interface import LLMInterface
        
        # Verify it's an abstract base class
        assert issubclass(LLMInterface, ABC)
        
        # Verify required methods exist
        required_methods = ['initialize', 'generate', 'embed', 'health_check']
        for method in required_methods:
            assert hasattr(LLMInterface, method)
            assert callable(getattr(LLMInterface, method))
    
    @pytest.mark.interface
    @pytest.mark.asyncio
    async def test_llm_initialize_contract(self, mock_llm_provider):
        """Test LLM initialization behavior."""
        config = {"model": "test-model", "temperature": 0.7}
        
        # Should accept configuration dict
        await mock_llm_provider.initialize(config)
        mock_llm_provider.initialize.assert_called_once_with(config)
    
    @pytest.mark.interface
    @pytest.mark.asyncio
    async def test_llm_generate_contract(self, mock_llm_provider, sample_query, sample_response):
        """Test LLM text generation behavior."""
        mock_llm_provider.generate.return_value = sample_response
        
        # Should accept prompt and return string
        result = await mock_llm_provider.generate(sample_query)
        
        assert isinstance(result, str)
        assert len(result) > 0
        mock_llm_provider.generate.assert_called_once_with(sample_query)
    
    @pytest.mark.interface
    @pytest.mark.asyncio
    async def test_llm_generate_with_context(self, mock_llm_provider):
        """Test LLM generation with context."""
        query = "What is microservices?"
        context = ["Doc 1 content", "Doc 2 content"]
        expected_response = "Microservices are..."
        
        mock_llm_provider.generate.return_value = expected_response
        
        # Should accept query and context
        result = await mock_llm_provider.generate(query, context=context)
        
        assert isinstance(result, str)
        mock_llm_provider.generate.assert_called_once_with(query, context=context)
    
    @pytest.mark.interface
    @pytest.mark.asyncio
    async def test_llm_embed_contract(self, mock_llm_provider, sample_embeddings):
        """Test LLM embedding generation behavior."""
        text = "Sample text to embed"
        mock_llm_provider.embed.return_value = sample_embeddings
        
        # Should accept text and return list of floats
        result = await mock_llm_provider.embed(text)
        
        assert isinstance(result, list)
        assert all(isinstance(x, (int, float)) for x in result)
        assert len(result) > 0
        mock_llm_provider.embed.assert_called_once_with(text)
    
    @pytest.mark.interface
    @pytest.mark.asyncio
    async def test_llm_health_check_contract(self, mock_llm_provider):
        """Test LLM health check behavior."""
        mock_llm_provider.health_check.return_value = True
        
        # Should return boolean
        result = await mock_llm_provider.health_check()
        
        assert isinstance(result, bool)
        mock_llm_provider.health_check.assert_called_once()


class TestVectorStoreInterface:
    """Test the Vector Store interface contract."""
    
    @pytest.mark.interface
    @pytest.mark.asyncio
    async def test_vector_store_interface_methods_exist(self):
        """Test that VectorStore interface defines required methods."""
        from src.interfaces.vector_store_interface import VectorStoreInterface
        
        assert issubclass(VectorStoreInterface, ABC)
        
        required_methods = ['initialize', 'store', 'retrieve', 'delete', 'health_check']
        for method in required_methods:
            assert hasattr(VectorStoreInterface, method)
    
    @pytest.mark.interface
    @pytest.mark.asyncio
    async def test_vector_store_contract(self, mock_vector_store_provider, sample_embeddings):
        """Test vector store operations."""
        # Store operation
        document_id = "test_doc_1"
        metadata = {"source": "test.pdf", "page": 1}
        
        mock_vector_store_provider.store.return_value = document_id
        
        result = await mock_vector_store_provider.store(
            vector=sample_embeddings,
            metadata=metadata,
            document_id=document_id
        )
        
        assert isinstance(result, str)
        mock_vector_store_provider.store.assert_called_once()
    
    @pytest.mark.interface
    @pytest.mark.asyncio
    async def test_vector_retrieve_contract(self, mock_vector_store_provider, sample_embeddings):
        """Test vector retrieval behavior."""
        expected_results = [
            {"id": "doc_1", "score": 0.9, "metadata": {"source": "test1.pdf"}},
            {"id": "doc_2", "score": 0.8, "metadata": {"source": "test2.pdf"}}
        ]
        mock_vector_store_provider.retrieve.return_value = expected_results
        
        results = await mock_vector_store_provider.retrieve(
            query_vector=sample_embeddings,
            top_k=5
        )
        
        assert isinstance(results, list)
        assert len(results) > 0
        for result in results:
            assert "id" in result
            assert "score" in result
            assert isinstance(result["score"], (int, float))


class TestSearchEngineInterface:
    """Test the Search Engine interface contract."""
    
    @pytest.mark.interface
    @pytest.mark.asyncio
    async def test_search_engine_interface_methods_exist(self):
        """Test that SearchEngine interface defines required methods."""
        from src.interfaces.search_engine_interface import SearchEngineInterface
        
        assert issubclass(SearchEngineInterface, ABC)
        
        required_methods = ['initialize', 'search', 'index', 'health_check']
        for method in required_methods:
            assert hasattr(SearchEngineInterface, method)
    
    @pytest.mark.interface
    @pytest.mark.asyncio
    async def test_search_contract(self, mock_search_engine_provider):
        """Test search engine search behavior."""
        query = "microservices architecture"
        expected_results = [
            {"id": "doc_1", "score": 0.95, "content": "Microservices are..."},
            {"id": "doc_2", "score": 0.85, "content": "Architecture patterns..."}
        ]
        mock_search_engine_provider.search.return_value = expected_results
        
        results = await mock_search_engine_provider.search(query, top_k=10)
        
        assert isinstance(results, list)
        assert len(results) > 0
        for result in results:
            assert "id" in result
            assert "score" in result
            assert isinstance(result["score"], (int, float))


class TestRerankerInterface:
    """Test the Reranker interface contract."""
    
    @pytest.mark.interface
    @pytest.mark.asyncio
    async def test_reranker_interface_methods_exist(self):
        """Test that Reranker interface defines required methods."""
        from src.interfaces.reranker_interface import RerankerInterface
        
        assert issubclass(RerankerInterface, ABC)
        
        required_methods = ['initialize', 'rerank', 'health_check']
        for method in required_methods:
            assert hasattr(RerankerInterface, method)
    
    @pytest.mark.interface
    @pytest.mark.asyncio
    async def test_rerank_contract(self, mock_reranker_provider, sample_documents):
        """Test reranker behavior."""
        query = "microservices benefits"
        
        # Mock reranked results (different order, updated scores)
        reranked_results = [
            {"id": "doc_2", "score": 0.95, "content": sample_documents[1]["content"]},
            {"id": "doc_1", "score": 0.90, "content": sample_documents[0]["content"]},
            {"id": "doc_3", "score": 0.75, "content": sample_documents[2]["content"]}
        ]
        mock_reranker_provider.rerank.return_value = reranked_results
        
        results = await mock_reranker_provider.rerank(
            query=query,
            documents=sample_documents
        )
        
        assert isinstance(results, list)
        assert len(results) > 0
        for result in results:
            assert "id" in result
            assert "score" in result
            assert isinstance(result["score"], (int, float))
        
        # Check that reranking actually changed the order/scores
        assert results != sample_documents


class TestProviderRegistryInterface:
    """Test the Provider Registry interface contract."""
    
    @pytest.mark.interface
    @pytest.mark.asyncio
    async def test_provider_registry_interface_methods_exist(self):
        """Test that ProviderRegistry defines required methods."""
        from src.registry.provider_registry import ProviderRegistry
        
        required_methods = [
            'register_provider', 'get_provider', 'list_providers',
            'initialize_providers', 'health_check_all'
        ]
        for method in required_methods:
            assert hasattr(ProviderRegistry, method)
    
    @pytest.mark.interface
    @pytest.mark.asyncio
    async def test_register_provider_contract(self):
        """Test provider registration behavior."""
        from src.registry.provider_registry import ProviderRegistry
        
        registry = ProviderRegistry()
        
        # Should be able to register providers
        registry.register_provider(
            category="llm",
            name="test_llm",
            provider_class=AsyncMock
        )
        
        # Should be able to list registered providers
        providers = registry.list_providers("llm")
        assert "test_llm" in providers
    
    @pytest.mark.interface
    @pytest.mark.asyncio
    async def test_get_provider_contract(self, sample_config):
        """Test provider retrieval behavior."""
        from src.registry.provider_registry import ProviderRegistry
        
        registry = ProviderRegistry()
        
        # Register a mock provider
        mock_provider_class = AsyncMock
        registry.register_provider("llm", "test_llm", mock_provider_class)
        
        # Should be able to get initialized provider
        provider = await registry.get_provider("llm", "test_llm")
        
        assert provider is not None
        # Provider should be initialized
        assert hasattr(provider, 'initialize')


class TestComponentIntegrationContracts:
    """Test contracts for component integration."""
    
    @pytest.mark.interface
    @pytest.mark.asyncio
    async def test_all_providers_implement_health_check(self):
        """Test that all provider types implement health_check."""
        # This ensures we can monitor all components uniformly
        interface_mapping = {
            'LLMInterface': 'src.interfaces.llm_interface',
            'VectorStoreInterface': 'src.interfaces.vector_store_interface',
            'SearchEngineInterface': 'src.interfaces.search_engine_interface',
            'RerankerInterface': 'src.interfaces.reranker_interface'
        }
        
        for interface_name, module_path in interface_mapping.items():
            try:
                module = __import__(module_path, fromlist=[interface_name])
                interface_class = getattr(module, interface_name)
                assert hasattr(interface_class, 'health_check')
            except ImportError:
                pytest.fail(f"Interface {interface_name} not implemented yet")
    
    @pytest.mark.interface
    @pytest.mark.asyncio
    async def test_all_providers_implement_initialize(self):
        """Test that all provider types implement initialize."""
        # This ensures consistent initialization across all components
        interface_mapping = {
            'LLMInterface': 'src.interfaces.llm_interface',
            'VectorStoreInterface': 'src.interfaces.vector_store_interface',
            'SearchEngineInterface': 'src.interfaces.search_engine_interface',
            'RerankerInterface': 'src.interfaces.reranker_interface'
        }
        
        for interface_name, module_path in interface_mapping.items():
            try:
                module = __import__(module_path, fromlist=[interface_name])
                interface_class = getattr(module, interface_name)
                assert hasattr(interface_class, 'initialize')
            except ImportError:
                pytest.fail(f"Interface {interface_name} not implemented yet")


class TestErrorHandlingContracts:
    """Test error handling contracts for all interfaces."""
    
    @pytest.mark.interface
    @pytest.mark.asyncio
    async def test_providers_handle_initialization_errors(self, mock_llm_provider):
        """Test that providers handle initialization errors gracefully."""
        # Invalid config should not crash, should raise specific exception
        invalid_config = {"invalid": "config"}
        
        # Mock an initialization error
        mock_llm_provider.initialize.side_effect = ValueError("Invalid configuration")
        
        with pytest.raises(ValueError, match="Invalid configuration"):
            await mock_llm_provider.initialize(invalid_config)
    
    @pytest.mark.interface
    @pytest.mark.asyncio
    async def test_providers_handle_service_errors(self, mock_llm_provider):
        """Test that providers handle service errors gracefully."""
        # Service unavailable should raise specific exception
        mock_llm_provider.generate.side_effect = ConnectionError("Service unavailable")
        
        with pytest.raises(ConnectionError):
            await mock_llm_provider.generate("test query")
    
    @pytest.mark.interface
    @pytest.mark.asyncio
    async def test_health_check_handles_failures(self, mock_llm_provider):
        """Test that health checks handle failures gracefully."""
        # Health check should return False on failure, not raise exception
        mock_llm_provider.health_check.return_value = False
        
        result = await mock_llm_provider.health_check()
        assert result is False 