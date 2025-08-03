"""
Pytest configuration and shared fixtures for agentic RAG testing.
"""

import asyncio
import pytest
from typing import Dict, Any, List
from unittest.mock import AsyncMock, Mock


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def sample_config():
    """Sample configuration for testing providers."""
    return {
        "llm": {
            "default": "mock_llm",
            "providers": {
                "mock_llm": {
                    "class": "MockLLMProvider",
                    "config": {
                        "model": "test-model",
                        "temperature": 0.7
                    }
                }
            }
        },
        "vector_store": {
            "default": "mock_vector",
            "providers": {
                "mock_vector": {
                    "class": "MockVectorStoreProvider",
                    "config": {
                        "collection": "test_docs",
                        "dimension": 768
                    }
                }
            }
        }
    }


@pytest.fixture
def sample_query():
    """Sample query for testing."""
    return "What are the benefits of using microservices architecture?"


@pytest.fixture
def sample_response():
    """Sample LLM response for testing."""
    return "Microservices architecture provides benefits including scalability, flexibility, and independent deployment capabilities."


@pytest.fixture
def sample_documents():
    """Sample documents for testing retrieval."""
    return [
        {
            "id": "doc_1",
            "content": "Microservices are a software development approach...",
            "metadata": {"source": "architecture_guide.pdf", "page": 1}
        },
        {
            "id": "doc_2", 
            "content": "Benefits of microservices include scalability...",
            "metadata": {"source": "scalability_paper.pdf", "page": 3}
        },
        {
            "id": "doc_3",
            "content": "Distributed systems require careful design...",
            "metadata": {"source": "distributed_systems.pdf", "page": 15}
        }
    ]


@pytest.fixture
def sample_embeddings():
    """Sample embeddings for testing."""
    return [0.1, 0.2, 0.3, 0.4, 0.5] * 153  # 765 dimensions


@pytest.fixture
def mock_llm_provider():
    """Mock LLM provider for testing."""
    mock = AsyncMock()
    mock.initialize = AsyncMock()
    mock.generate = AsyncMock(return_value="Mock response")
    mock.embed = AsyncMock(return_value=[0.1, 0.2, 0.3, 0.4, 0.5] * 153)
    mock.health_check = AsyncMock(return_value=True)
    mock.get_provider_info = Mock(return_value={"name": "mock_llm", "version": "1.0"})
    return mock


@pytest.fixture
def mock_vector_store_provider():
    """Mock vector store provider for testing."""
    mock = AsyncMock()
    mock.initialize = AsyncMock()
    mock.store = AsyncMock(return_value="mock_doc_id")
    mock.retrieve = AsyncMock(return_value=[
        {"id": "doc_1", "score": 0.9, "content": "Mock content 1"},
        {"id": "doc_2", "score": 0.8, "content": "Mock content 2"}
    ])
    mock.delete = AsyncMock(return_value=True)
    mock.health_check = AsyncMock(return_value=True)
    mock.get_provider_info = Mock(return_value={"name": "mock_vector", "version": "1.0"})
    return mock


@pytest.fixture
def mock_search_engine_provider():
    """Mock search engine provider for testing."""
    mock = AsyncMock()
    mock.initialize = AsyncMock()
    mock.search = AsyncMock(return_value=[
        {"id": "doc_1", "score": 0.95, "content": "Mock search result 1"},
        {"id": "doc_2", "score": 0.85, "content": "Mock search result 2"}
    ])
    mock.index = AsyncMock(return_value=True)
    mock.health_check = AsyncMock(return_value=True)
    mock.get_provider_info = Mock(return_value={"name": "mock_search", "version": "1.0"})
    return mock


@pytest.fixture
def mock_reranker_provider():
    """Mock reranker provider for testing."""
    mock = AsyncMock()
    mock.initialize = AsyncMock()
    mock.rerank = AsyncMock(return_value=[
        {"id": "doc_2", "score": 0.95, "content": "Reranked content 2"},
        {"id": "doc_1", "score": 0.90, "content": "Reranked content 1"}
    ])
    mock.health_check = AsyncMock(return_value=True)
    mock.get_provider_info = Mock(return_value={"name": "mock_reranker", "version": "1.0"})
    return mock


@pytest.fixture
def evaluation_query_sample():
    """Sample evaluation query for testing evaluation framework."""
    return {
        "query": "What are microservices?",
        "expected_answer": "Microservices are a software architecture pattern...",
        "relevant_documents": ["doc_1", "doc_2"],
        "category": "technology",
        "difficulty": "medium",
        "metadata": {"domain": "software_architecture"}
    }


class AsyncContextManager:
    """Helper for testing async context managers."""
    
    def __init__(self, async_mock):
        self.async_mock = async_mock
    
    async def __aenter__(self):
        return self.async_mock
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass


@pytest.fixture
def async_context_manager():
    """Factory for creating async context managers in tests."""
    return AsyncContextManager 