import pytest
import pytest_asyncio
from unittest.mock import patch, Mock, AsyncMock
from typing import List, Dict, Any, Optional
import sys

# Mock the external libraries before importing our provider
@pytest.fixture(autouse=True)
def mock_external_libs():
    """Mock external libraries that BGE provider depends on."""
    mock_modules = {
        'FlagEmbedding': Mock(),
        'FlagEmbedding.FlagReranker': Mock(),
        'sentence_transformers': Mock(),
        'torch': Mock(),
        'transformers': Mock()
    }
    
    with patch.dict('sys.modules', mock_modules):
        yield


class TestBGEProvider:
    """Test suite for BGE Reranker Provider implementation."""
    
    @pytest.fixture
    def mock_reranker_model(self):
        """Mock BGE reranker model for testing."""
        mock_model = Mock()
        # Return actual numeric values instead of Mock objects
        mock_model.compute_score = Mock(return_value=[0.95, 0.87, 0.65, 0.42])
        return mock_model
    
    @pytest.mark.asyncio
    @pytest.mark.provider
    async def test_bge_provider_basic_interface(self):
        """Test that BGE provider properly implements RerankerInterface."""
        from src.providers.rerankers.bge_provider import BGEProvider
        from src.interfaces.reranker_interface import RerankerInterface
        
        provider = BGEProvider()
        assert isinstance(provider, RerankerInterface)
        
        # Check all required methods exist
        assert hasattr(provider, 'initialize')
        assert hasattr(provider, 'rerank')
        assert hasattr(provider, 'health_check')
        assert hasattr(provider, 'get_provider_info')
    
    @pytest.mark.asyncio
    @pytest.mark.provider
    async def test_initialization_validation(self, mock_reranker_model):
        """Test BGE provider initialization with various configurations.""" 
        from src.providers.rerankers.bge_provider import BGEProvider
        
        provider = BGEProvider()
        
        # Test successful initialization
        with patch('src.providers.rerankers.bge_provider.FlagReranker', return_value=mock_reranker_model):
            config = {
                "model_name": "BAAI/bge-reranker-large",
                "device": "cpu",
                "batch_size": 32,
                "max_length": 512
            }
            await provider.initialize(config)
            assert provider.model is not None
            assert provider.model_name == "BAAI/bge-reranker-large"
            assert provider.device == "cpu"
            assert provider.batch_size == 32
    
    @pytest.mark.asyncio 
    @pytest.mark.provider
    async def test_initialization_with_defaults(self, mock_reranker_model):
        """Test BGE provider initialization with default values."""
        from src.providers.rerankers.bge_provider import BGEProvider
        
        provider = BGEProvider()
        
        with patch('src.providers.rerankers.bge_provider.FlagReranker', return_value=mock_reranker_model):
            config = {}  # Empty config should use defaults
            await provider.initialize(config)
            
            assert provider.model_name == "BAAI/bge-reranker-base"  # Default model
            assert provider.device == "cpu"  # Default device
            assert provider.batch_size == 16  # Default batch size
    
    @pytest.mark.asyncio
    @pytest.mark.provider
    async def test_rerank_functionality(self, mock_reranker_model):
        """Test document reranking functionality."""
        from src.providers.rerankers.bge_provider import BGEProvider
        
        provider = BGEProvider()
        
        with patch('src.providers.rerankers.bge_provider.FlagReranker', return_value=mock_reranker_model):
            await provider.initialize({"model_name": "BAAI/bge-reranker-base"})
            
            query = "What is machine learning?"
            documents = [
                {"id": "doc1", "content": "Machine learning is a subset of AI", "metadata": {"score": 0.8}},
                {"id": "doc2", "content": "Deep learning uses neural networks", "metadata": {"score": 0.7}},
                {"id": "doc3", "content": "Python is a programming language", "metadata": {"score": 0.6}},
                {"id": "doc4", "content": "Data science involves statistics", "metadata": {"score": 0.5}}
            ]
            
            # Mock the compute_score to return descending scores (as floats, not Mocks)
            mock_reranker_model.compute_score.return_value = [0.95, 0.87, 0.65, 0.42]
            
            reranked = await provider.rerank(query, documents, top_k=3)
            
            # Should return top 3 documents reordered by BGE scores
            assert len(reranked) == 3
            assert reranked[0]["id"] == "doc1"  # Highest BGE score (0.95)
            assert reranked[1]["id"] == "doc2"  # Second highest (0.87)
            assert reranked[2]["id"] == "doc3"  # Third highest (0.65)
            
            # Verify BGE scores were added to metadata
            assert reranked[0]["metadata"]["bge_score"] == 0.95
            assert reranked[1]["metadata"]["bge_score"] == 0.87
            assert reranked[2]["metadata"]["bge_score"] == 0.65
    
    @pytest.mark.asyncio
    @pytest.mark.provider  
    async def test_rerank_with_no_top_k(self, mock_reranker_model):
        """Test reranking without top_k limit (return all documents)."""
        from src.providers.rerankers.bge_provider import BGEProvider
        
        provider = BGEProvider()
        
        with patch('src.providers.rerankers.bge_provider.FlagReranker', return_value=mock_reranker_model):
            await provider.initialize({})
            
            query = "Test query"
            documents = [
                {"id": "doc1", "content": "Content 1"},
                {"id": "doc2", "content": "Content 2"}
            ]
            
            mock_reranker_model.compute_score.return_value = [0.9, 0.7]
            
            reranked = await provider.rerank(query, documents)  # No top_k
            
            assert len(reranked) == 2  # All documents returned
            assert reranked[0]["id"] == "doc1"  # Higher score first
            assert reranked[1]["id"] == "doc2"  # Lower score second
    
    @pytest.mark.asyncio
    @pytest.mark.provider
    async def test_rerank_empty_documents(self, mock_reranker_model):
        """Test reranking with empty document list."""
        from src.providers.rerankers.bge_provider import BGEProvider
        
        provider = BGEProvider()
        
        with patch('src.providers.rerankers.bge_provider.FlagReranker', return_value=mock_reranker_model):
            await provider.initialize({})
            
            query = "Test query"
            documents = []
            
            reranked = await provider.rerank(query, documents)
            
            assert reranked == []
            mock_reranker_model.compute_score.assert_not_called()
    
    @pytest.mark.asyncio
    @pytest.mark.provider
    async def test_rerank_batch_processing(self, mock_reranker_model):
        """Test reranking with batch processing for large document sets."""
        from src.providers.rerankers.bge_provider import BGEProvider
        
        provider = BGEProvider()
        
        with patch('src.providers.rerankers.bge_provider.FlagReranker', return_value=mock_reranker_model):
            await provider.initialize({"batch_size": 2})  # Small batch for testing
            
            query = "Test query"
            documents = [
                {"id": f"doc{i}", "content": f"Content {i}"} 
                for i in range(5)  # 5 documents, batch_size=2
            ]
            
            # Mock compute_score to be called multiple times for batches
            mock_reranker_model.compute_score.side_effect = [
                [0.9, 0.8],    # First batch (2 docs)
                [0.7, 0.6],    # Second batch (2 docs)  
                [0.5]          # Third batch (1 doc)
            ]
            
            reranked = await provider.rerank(query, documents)
            
            assert len(reranked) == 5
            # Should be sorted by BGE scores in descending order
            scores = [doc["metadata"]["bge_score"] for doc in reranked]
            assert scores == [0.9, 0.8, 0.7, 0.6, 0.5]
    
    @pytest.mark.asyncio
    @pytest.mark.provider
    async def test_health_check(self, mock_reranker_model):
        """Test BGE provider health check functionality."""
        from src.providers.rerankers.bge_provider import BGEProvider
        
        provider = BGEProvider()
        
        # Health check should fail before initialization
        assert await provider.health_check() == False
        
        # Health check should pass after successful initialization
        with patch('src.providers.rerankers.bge_provider.FlagReranker', return_value=mock_reranker_model):
            await provider.initialize({})
            assert await provider.health_check() == True
    
    @pytest.mark.asyncio
    @pytest.mark.provider
    async def test_get_provider_info(self):
        """Test BGE provider info method."""
        from src.providers.rerankers.bge_provider import BGEProvider
        
        provider = BGEProvider()
        info = provider.get_provider_info()
        
        assert isinstance(info, dict)
        assert info["name"] == "BGEProvider"
        assert info["type"] == "reranker"
        assert "version" in info
        assert "capabilities" in info
        assert "semantic_reranking" in info["capabilities"]
        assert "relevance_scoring" in info["capabilities"]
        assert "result_optimization" in info["capabilities"]
    
    @pytest.mark.asyncio
    @pytest.mark.provider
    async def test_model_loading_error_handling(self):
        """Test BGE provider handling of model loading errors."""
        from src.providers.rerankers.bge_provider import BGEProvider
        
        provider = BGEProvider()
        
        # Test initialization failure when model loading fails
        with patch('src.providers.rerankers.bge_provider.FlagReranker', side_effect=Exception("Model loading failed")):
            config = {"model_name": "invalid-model"}
            
            with pytest.raises(Exception):
                await provider.initialize(config)
    
    @pytest.mark.asyncio
    @pytest.mark.provider
    async def test_reranking_error_handling(self, mock_reranker_model):
        """Test BGE provider error handling during reranking."""
        from src.providers.rerankers.bge_provider import BGEProvider
        
        provider = BGEProvider()
        
        with patch('src.providers.rerankers.bge_provider.FlagReranker', return_value=mock_reranker_model):
            await provider.initialize({})
            
            # Test error when compute_score fails
            mock_reranker_model.compute_score.side_effect = Exception("Reranking failed")
            
            query = "Test query"
            documents = [{"id": "doc1", "content": "Content 1"}]
            
            with pytest.raises(Exception):
                await provider.rerank(query, documents) 