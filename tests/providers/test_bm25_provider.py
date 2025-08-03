import pytest
from unittest.mock import Mock, patch
from typing import List, Dict, Any


class TestBM25Provider:
    """Test suite for BM25 Provider implementation."""
    
    @pytest.fixture
    def bm25_config(self):
        """Configuration for BM25 provider."""
        return {
            "k1": 1.2,
            "b": 0.75,
            "epsilon": 0.25,
            "tokenizer": "simple",
            "lowercase": True,
            "remove_punctuation": True
        }
    
    @pytest.fixture
    def sample_documents(self):
        """Sample documents for testing."""
        return [
            {
                "id": "doc_1",
                "content": "Machine learning is a subset of artificial intelligence",
                "metadata": {"source": "ml_basics.pdf", "page": 1}
            },
            {
                "id": "doc_2", 
                "content": "Deep learning uses neural networks with multiple layers",
                "metadata": {"source": "dl_guide.pdf", "page": 3}
            },
            {
                "id": "doc_3",
                "content": "Natural language processing enables computers to understand text",
                "metadata": {"source": "nlp_intro.pdf", "page": 5}
            }
        ]
    
    @pytest.mark.provider
    @pytest.mark.asyncio
    async def test_bm25_provider_basic_interface(self):
        """Test that BM25Provider can be imported and has required methods."""
        # Mock the rank_bm25 import
        with patch.dict('sys.modules', {
            'rank_bm25': Mock()
        }):
            from src.providers.search_engines.bm25_provider import BM25Provider
            from src.interfaces.search_engine_interface import SearchEngineInterface
            
            provider = BM25Provider()
            assert isinstance(provider, SearchEngineInterface)
            
            # Check all required methods exist
            assert hasattr(provider, 'initialize')
            assert hasattr(provider, 'search')
            assert hasattr(provider, 'index')
            assert hasattr(provider, 'health_check')
            assert hasattr(provider, 'get_provider_info')
    
    @pytest.mark.provider
    @pytest.mark.asyncio
    async def test_initialization_and_config(self, bm25_config):
        """Test initialization and configuration."""
        with patch.dict('sys.modules', {'rank_bm25': Mock()}):
            from src.providers.search_engines.bm25_provider import BM25Provider
            
            provider = BM25Provider()
            
            # Mock BM25Okapi to be available
            with patch('src.providers.search_engines.bm25_provider.BM25Okapi', Mock()):
                await provider.initialize(bm25_config)
                
                assert provider.k1 == 1.2
                assert provider.b == 0.75
                assert provider.epsilon == 0.25
                assert provider.tokenizer == "simple"
                assert provider.lowercase is True
                assert provider._initialized is True
    
    @pytest.mark.provider
    @pytest.mark.asyncio
    async def test_initialization_with_defaults(self):
        """Test initialization with default parameters."""
        with patch.dict('sys.modules', {'rank_bm25': Mock()}):
            from src.providers.search_engines.bm25_provider import BM25Provider
            
            provider = BM25Provider()
            
            with patch('src.providers.search_engines.bm25_provider.BM25Okapi', Mock()):
                await provider.initialize({})
                
                # Should use default values
                assert provider.k1 == 1.2  # BM25 default
                assert provider.b == 0.75  # BM25 default
                assert provider.tokenizer == "simple"
                assert provider._initialized is True
    
    @pytest.mark.provider
    @pytest.mark.asyncio
    async def test_tokenization_functionality(self):
        """Test tokenization functionality."""
        with patch.dict('sys.modules', {'rank_bm25': Mock()}):
            from src.providers.search_engines.bm25_provider import BM25Provider
            
            provider = BM25Provider()
            
            with patch('src.providers.search_engines.bm25_provider.BM25Okapi', Mock()):
                # Test simple tokenization
                config = {"tokenizer": "simple", "lowercase": True, "remove_punctuation": True}
                await provider.initialize(config)
                
                text = "Hello, World! This is a test."
                tokens = provider._tokenize(text)
                
                expected = ["hello", "world", "this", "is", "a", "test"]
                assert tokens == expected
                
                # Test case preservation
                provider.lowercase = False
                text = "Hello, World! This is a Test."
                tokens = provider._tokenize(text)
                
                expected = ["Hello", "World", "This", "is", "a", "Test"]
                assert tokens == expected
    
    @pytest.mark.provider
    @pytest.mark.asyncio
    async def test_index_documents(self, bm25_config, sample_documents):
        """Test document indexing functionality."""
        with patch.dict('sys.modules', {'rank_bm25': Mock()}):
            from src.providers.search_engines.bm25_provider import BM25Provider
            
            provider = BM25Provider()
            
            mock_bm25 = Mock()
            with patch('src.providers.search_engines.bm25_provider.BM25Okapi', return_value=mock_bm25):
                await provider.initialize(bm25_config)
                
                result = await provider.index(sample_documents)
                
                assert result is True
                assert len(provider.documents) == 3
                assert provider.documents[0]["id"] == "doc_1"
                assert provider.bm25_index is not None
    
    @pytest.mark.provider
    @pytest.mark.asyncio
    async def test_search_functionality(self, bm25_config, sample_documents):
        """Test search functionality."""
        with patch.dict('sys.modules', {'rank_bm25': Mock()}):
            from src.providers.search_engines.bm25_provider import BM25Provider
            
            provider = BM25Provider()
            
            mock_bm25 = Mock()
            mock_bm25.get_scores.return_value = [0.85, 0.92, 0.23]
            
            with patch('src.providers.search_engines.bm25_provider.BM25Okapi', return_value=mock_bm25):
                await provider.initialize(bm25_config)
                await provider.index(sample_documents)
                
                results = await provider.search("machine learning", top_k=2)
                
                # Should return top 2 results sorted by score
                assert len(results) == 2
                
                # First result should be highest scoring (doc_2 with score 0.92)
                assert results[0]["score"] == 0.92
                assert results[0]["id"] == "doc_2"
                assert "content" in results[0]
                
                # Second result should be second highest (doc_1 with score 0.85)
                assert results[1]["score"] == 0.85
                assert results[1]["id"] == "doc_1"
                
                mock_bm25.get_scores.assert_called_once()
    
    @pytest.mark.provider
    @pytest.mark.asyncio
    async def test_search_with_filters(self, bm25_config, sample_documents):
        """Test search with metadata filtering."""
        with patch.dict('sys.modules', {'rank_bm25': Mock()}):
            from src.providers.search_engines.bm25_provider import BM25Provider
            
            provider = BM25Provider()
            
            mock_bm25 = Mock()
            mock_bm25.get_scores.return_value = [0.85, 0.92, 0.23]
            
            with patch('src.providers.search_engines.bm25_provider.BM25Okapi', return_value=mock_bm25):
                await provider.initialize(bm25_config)
                await provider.index(sample_documents)
                
                # Search with source filter
                results = await provider.search(
                    "machine learning",
                    top_k=5,
                    filters={"source": "dl_guide.pdf"}
                )
                
                # Should only return documents matching filter
                assert len(results) == 1
                assert results[0]["id"] == "doc_2"
                assert results[0]["metadata"]["source"] == "dl_guide.pdf"
    
    @pytest.mark.provider
    @pytest.mark.asyncio
    async def test_search_empty_index(self, bm25_config):
        """Test search on empty index."""
        with patch.dict('sys.modules', {'rank_bm25': Mock()}):
            from src.providers.search_engines.bm25_provider import BM25Provider
            
            provider = BM25Provider()
            
            with patch('src.providers.search_engines.bm25_provider.BM25Okapi', Mock()):
                await provider.initialize(bm25_config)
                
                results = await provider.search("test query", top_k=5)
                
                assert results == []
    
    @pytest.mark.provider
    @pytest.mark.asyncio
    async def test_health_check(self, bm25_config):
        """Test health check functionality."""
        with patch.dict('sys.modules', {'rank_bm25': Mock()}):
            from src.providers.search_engines.bm25_provider import BM25Provider
            
            provider = BM25Provider()
            
            # Health check should fail when not initialized
            result = await provider.health_check()
            assert result is False
            
            # Health check should pass when initialized
            with patch('src.providers.search_engines.bm25_provider.BM25Okapi', Mock()):
                await provider.initialize(bm25_config)
                result = await provider.health_check()
                assert result is True
    
    @pytest.mark.provider
    def test_get_provider_info(self):
        """Test provider info retrieval."""
        with patch.dict('sys.modules', {'rank_bm25': Mock()}):
            from src.providers.search_engines.bm25_provider import BM25Provider
            
            provider = BM25Provider()
            info = provider.get_provider_info()
            
            assert info["name"] == "BM25Provider"
            assert info["type"] == "search_engine"
            assert "keyword_search" in info["capabilities"]
            assert "full_text_search" in info["capabilities"]
            assert "indexing" in info["capabilities"]
            assert "version" in info
    
    @pytest.mark.provider
    @pytest.mark.asyncio
    async def test_filter_matching(self):
        """Test metadata filter matching functionality."""
        with patch.dict('sys.modules', {'rank_bm25': Mock()}):
            from src.providers.search_engines.bm25_provider import BM25Provider
            
            provider = BM25Provider()
            
            # Test string filter
            metadata = {"source": "test.pdf", "page": 1}
            filters = {"source": "test.pdf"}
            assert provider._matches_filters(metadata, filters) is True
            
            filters = {"source": "other.pdf"}
            assert provider._matches_filters(metadata, filters) is False
            
            # Test numeric filter
            filters = {"page": 1}
            assert provider._matches_filters(metadata, filters) is True
            
            filters = {"page": 2}
            assert provider._matches_filters(metadata, filters) is False
            
            # Test missing key
            filters = {"author": "test"}
            assert provider._matches_filters(metadata, filters) is False 