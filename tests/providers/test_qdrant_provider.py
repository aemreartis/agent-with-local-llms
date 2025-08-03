import pytest
from unittest.mock import AsyncMock, Mock, patch
from typing import List, Dict, Any


class TestQdrantProvider:
    """Test suite for Qdrant Provider implementation."""
    
    @pytest.fixture
    def qdrant_config(self):
        """Configuration for Qdrant provider."""
        return {
            "url": "http://localhost:6333",
            "collection_name": "test_documents",
            "vector_size": 768,
            "distance": "Cosine",
            "api_key": None,
            "timeout": 30.0,
        }
    
    @pytest.fixture
    def sample_vector(self):
        """Sample embedding vector for testing."""
        return [0.1, 0.2, 0.3, 0.4, 0.5] * 153 + [0.1, 0.2, 0.3]  # 768 dimensions
    
    @pytest.fixture
    def sample_metadata(self):
        """Sample metadata for testing."""
        return {
            "document_id": "doc_123",
            "source": "test_document.pdf",
            "content": "This is test content for the document."
        }
    
    @pytest.mark.provider
    @pytest.mark.asyncio  
    async def test_qdrant_provider_basic_interface(self):
        """Test that QdrantProvider can be imported and has required methods."""
        # Mock the qdrant imports
        with patch.dict('sys.modules', {
            'qdrant_client': Mock(),
            'qdrant_client.models': Mock()
        }):
            from src.providers.vector_stores.qdrant_provider import QdrantProvider
            from src.interfaces.vector_store_interface import VectorStoreInterface
            
            provider = QdrantProvider()
            assert isinstance(provider, VectorStoreInterface)
            
            # Check all required methods exist
            assert hasattr(provider, 'initialize')
            assert hasattr(provider, 'store')
            assert hasattr(provider, 'retrieve')
            assert hasattr(provider, 'delete')
            assert hasattr(provider, 'health_check')
            assert hasattr(provider, 'get_provider_info')
    
    @pytest.mark.provider
    @pytest.mark.asyncio
    async def test_initialization_validation(self, qdrant_config):
        """Test initialization parameter validation."""
        with patch.dict('sys.modules', {
            'qdrant_client': Mock(),
            'qdrant_client.models': Mock()
        }):
            from src.providers.vector_stores.qdrant_provider import QdrantProvider
            
            provider = QdrantProvider()
            
            # Test missing URL
            config_no_url = {"collection_name": "test"}
            with pytest.raises(ValueError, match="url is required"):
                await provider.initialize(config_no_url)
            
            # Test that initialization sets properties correctly
            with patch('src.providers.vector_stores.qdrant_provider.AsyncQdrantClient') as mock_client_class:
                mock_client = AsyncMock()
                mock_client_class.return_value = mock_client
                mock_client.collection_exists.return_value = True
                
                await provider.initialize(qdrant_config)
                
                assert provider.url == "http://localhost:6333"
                assert provider.collection_name == "test_documents"
                assert provider.vector_size == 768
                assert provider._initialized is True
    
    @pytest.mark.provider
    @pytest.mark.asyncio
    async def test_store_functionality(self, qdrant_config, sample_vector, sample_metadata):
        """Test basic store functionality."""
        with patch.dict('sys.modules', {
            'qdrant_client': Mock(),
            'qdrant_client.models': Mock()
        }):
            from src.providers.vector_stores.qdrant_provider import QdrantProvider
            
            provider = QdrantProvider()
            
            with patch('src.providers.vector_stores.qdrant_provider.AsyncQdrantClient') as mock_client_class:
                with patch('src.providers.vector_stores.qdrant_provider.PointStruct'):
                    mock_client = AsyncMock()
                    mock_client_class.return_value = mock_client
                    mock_client.collection_exists.return_value = True
                    mock_client.upsert.return_value = Mock(operation_id=123)
                    
                    await provider.initialize(qdrant_config)
                    
                    # Test store with provided ID
                    result = await provider.store(sample_vector, sample_metadata, "doc_123")
                    assert result == "doc_123"
                    mock_client.upsert.assert_called_once()
                    
                    # Test store with auto-generated ID
                    mock_client.upsert.reset_mock()
                    result = await provider.store(sample_vector, sample_metadata)
                    assert result is not None
                    assert len(result) == 36  # UUID format
                    mock_client.upsert.assert_called_once()
    
    @pytest.mark.provider
    @pytest.mark.asyncio
    async def test_retrieve_functionality(self, qdrant_config, sample_vector):
        """Test basic retrieve functionality."""
        with patch.dict('sys.modules', {
            'qdrant_client': Mock(),
            'qdrant_client.models': Mock()
        }):
            from src.providers.vector_stores.qdrant_provider import QdrantProvider
            
            provider = QdrantProvider()
            
            with patch('src.providers.vector_stores.qdrant_provider.AsyncQdrantClient') as mock_client_class:
                mock_client = AsyncMock()
                mock_client_class.return_value = mock_client
                mock_client.collection_exists.return_value = True
                
                # Mock search results
                mock_result1 = Mock()
                mock_result1.id = "point_1"
                mock_result1.score = 0.95
                mock_result1.payload = {"document_id": "doc_1", "content": "Test content"}
                
                mock_result2 = Mock()
                mock_result2.id = "point_2"
                mock_result2.score = 0.87
                mock_result2.payload = {"document_id": "doc_2", "content": "More content"}
                
                mock_client.search.return_value = [mock_result1, mock_result2]
                
                await provider.initialize(qdrant_config)
                
                results = await provider.retrieve(sample_vector, top_k=5)
                
                assert len(results) == 2
                assert results[0]["id"] == "point_1"
                assert results[0]["score"] == 0.95
                assert results[0]["metadata"]["document_id"] == "doc_1"
                
                mock_client.search.assert_called_once()
    
    @pytest.mark.provider
    @pytest.mark.asyncio
    async def test_delete_functionality(self, qdrant_config):
        """Test basic delete functionality."""
        with patch.dict('sys.modules', {
            'qdrant_client': Mock(),
            'qdrant_client.models': Mock()
        }):
            from src.providers.vector_stores.qdrant_provider import QdrantProvider
            
            provider = QdrantProvider()
            
            with patch('src.providers.vector_stores.qdrant_provider.AsyncQdrantClient') as mock_client_class:
                with patch('src.providers.vector_stores.qdrant_provider.PointIdsList'):
                    mock_client = AsyncMock()
                    mock_client_class.return_value = mock_client
                    mock_client.collection_exists.return_value = True
                    mock_client.delete.return_value = Mock(operation_id=456)
                    
                    await provider.initialize(qdrant_config)
                    
                    # Test successful deletion
                    result = await provider.delete("doc_123")
                    assert result is True
                    mock_client.delete.assert_called_once()
                    
                    # Test deletion failure
                    mock_client.delete.side_effect = Exception("Delete failed")
                    result = await provider.delete("doc_456")
                    assert result is False
    
    @pytest.mark.provider
    @pytest.mark.asyncio
    async def test_health_check(self, qdrant_config):
        """Test health check functionality."""
        with patch.dict('sys.modules', {
            'qdrant_client': Mock(),
            'qdrant_client.models': Mock()
        }):
            from src.providers.vector_stores.qdrant_provider import QdrantProvider
            
            provider = QdrantProvider()
            
            with patch('src.providers.vector_stores.qdrant_provider.AsyncQdrantClient') as mock_client_class:
                mock_client = AsyncMock()
                mock_client_class.return_value = mock_client
                mock_client.collection_exists.return_value = True
                
                await provider.initialize(qdrant_config)
                
                # Test successful health check
                mock_client.get_collections.return_value = Mock()
                result = await provider.health_check()
                assert result is True
                
                # Test health check failure
                mock_client.get_collections.side_effect = Exception("Connection failed")
                result = await provider.health_check()
                assert result is False
    
    @pytest.mark.provider
    def test_get_provider_info(self):
        """Test provider info retrieval."""
        with patch.dict('sys.modules', {
            'qdrant_client': Mock(),
            'qdrant_client.models': Mock()
        }):
            from src.providers.vector_stores.qdrant_provider import QdrantProvider
            
            provider = QdrantProvider()
            info = provider.get_provider_info()
            
            assert info["name"] == "QdrantProvider"
            assert info["type"] == "vector_store"
            assert "storage" in info["capabilities"]
            assert "retrieval" in info["capabilities"]
            assert "version" in info 