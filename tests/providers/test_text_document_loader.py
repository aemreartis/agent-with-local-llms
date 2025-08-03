import pytest
import tempfile
import os
from unittest.mock import AsyncMock, patch, MagicMock
from typing import Dict, Any

from src.interfaces.document_interface import DocumentType, Document


class TestTextDocumentLoader:
    """Test suite for Text Document Loader implementation."""
    
    @pytest.fixture
    def sample_config(self):
        """Sample configuration for text document loader."""
        return {
            "encoding": "utf-8",
            "max_file_size": 10485760,  # 10MB
            "allowed_extensions": [".txt", ".md", ".csv"]
        }
    
    @pytest.fixture
    def sample_text_content(self):
        """Sample text content for testing."""
        return """This is a sample text document.
It contains multiple lines of content.
This is the third line.
And this is the fourth line."""
    
    @pytest.fixture
    def temp_text_file(self, sample_text_content):
        """Create a temporary text file for testing."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(sample_text_content)
            temp_file = f.name
        
        yield temp_file
        
        # Cleanup
        os.unlink(temp_file)
    
    @pytest.mark.asyncio
    async def test_text_loader_initialization(self, sample_config):
        """Test text document loader initialization."""
        from src.providers.document.text_loader import TextDocumentLoader
        
        loader = TextDocumentLoader()
        await loader.initialize(sample_config)
        
        assert loader.encoding == "utf-8"
        assert loader.max_file_size == 10485760
        assert ".txt" in loader.allowed_extensions
        assert ".md" in loader.allowed_extensions
    
    @pytest.mark.asyncio
    async def test_text_loader_load_document_success(self, temp_text_file, sample_config):
        """Test successful document loading from file."""
        from src.providers.document.text_loader import TextDocumentLoader
        
        loader = TextDocumentLoader()
        await loader.initialize(sample_config)
        
        document = await loader.load_document(temp_text_file, DocumentType.TXT)
        
        assert document.document_id is not None
        assert "This is a sample text document" in document.content
        assert document.document_type == DocumentType.TXT
        assert document.metadata["source"] == temp_text_file
        assert document.metadata["file_size"] > 0
        assert document.metadata["encoding"] == "utf-8"
    
    @pytest.mark.asyncio
    async def test_text_loader_load_document_from_bytes_success(self, sample_config):
        """Test successful document loading from bytes."""
        from src.providers.document.text_loader import TextDocumentLoader
        
        loader = TextDocumentLoader()
        await loader.initialize(sample_config)
        
        content = b"This is test content from bytes"
        document = await loader.load_document_from_bytes(content, DocumentType.TXT, "test.txt")
        
        assert document.document_id is not None
        assert document.content == "This is test content from bytes"
        assert document.document_type == DocumentType.TXT
        assert document.metadata["filename"] == "test.txt"
        assert document.metadata["encoding"] == "utf-8"
    
    @pytest.mark.asyncio
    async def test_text_loader_load_document_file_not_found(self, sample_config):
        """Test document loading with non-existent file."""
        from src.providers.document.text_loader import TextDocumentLoader
        
        loader = TextDocumentLoader()
        await loader.initialize(sample_config)
        
        with pytest.raises(FileNotFoundError):
            await loader.load_document("nonexistent.txt", DocumentType.TXT)
    
    @pytest.mark.asyncio
    async def test_text_loader_load_document_file_too_large(self, sample_config):
        """Test document loading with file exceeding size limit."""
        from src.providers.document.text_loader import TextDocumentLoader
        
        # Create config with very small max file size
        small_config = {**sample_config, "max_file_size": 10}
        
        loader = TextDocumentLoader()
        await loader.initialize(small_config)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("This content is longer than 10 bytes")
            temp_file = f.name
        
        try:
            with pytest.raises(ValueError, match="File size.*exceeds maximum allowed"):
                await loader.load_document(temp_file, DocumentType.TXT)
        finally:
            os.unlink(temp_file)
    
    @pytest.mark.asyncio
    async def test_text_loader_load_document_unsupported_extension(self, sample_config):
        """Test document loading with unsupported file extension."""
        from src.providers.document.text_loader import TextDocumentLoader
        
        loader = TextDocumentLoader()
        await loader.initialize(sample_config)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.pdf', delete=False) as f:
            f.write("Test content")
            temp_file = f.name
        
        try:
            with pytest.raises(ValueError, match="Unsupported file extension"):
                await loader.load_document(temp_file, DocumentType.TXT)
        finally:
            os.unlink(temp_file)
    
    @pytest.mark.asyncio
    async def test_text_loader_load_document_encoding_error(self, sample_config):
        """Test document loading with encoding error."""
        from src.providers.document.text_loader import TextDocumentLoader
        
        loader = TextDocumentLoader()
        await loader.initialize(sample_config)
        
        # Create file with invalid UTF-8 content
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.txt', delete=False) as f:
            f.write(b"This is valid content\xff\xfe\xfd")  # Invalid UTF-8
            temp_file = f.name
        
        try:
            with pytest.raises(UnicodeDecodeError):
                await loader.load_document(temp_file, DocumentType.TXT)
        finally:
            os.unlink(temp_file)
    
    @pytest.mark.asyncio
    async def test_text_loader_health_check_success(self, sample_config):
        """Test successful health check."""
        from src.providers.document.text_loader import TextDocumentLoader
        
        loader = TextDocumentLoader()
        await loader.initialize(sample_config)
        
        assert await loader.health_check() is True
    
    def test_text_loader_get_supported_types(self, sample_config):
        """Test getting supported document types."""
        from src.providers.document.text_loader import TextDocumentLoader
        
        loader = TextDocumentLoader()
        
        supported_types = loader.get_supported_types()
        
        assert DocumentType.TXT in supported_types
        assert DocumentType.MD in supported_types
        assert DocumentType.CSV in supported_types
        assert DocumentType.PDF not in supported_types  # Should not support PDF
    
    def test_text_loader_get_loader_info(self, sample_config):
        """Test getting loader information."""
        from src.providers.document.text_loader import TextDocumentLoader
        
        loader = TextDocumentLoader()
        
        info = loader.get_loader_info()
        
        assert info["name"] == "text_loader"
        assert info["type"] == "document_loader"
        assert "version" in info
        assert "description" in info
        assert "supported_types" in info
    
    @pytest.mark.asyncio
    async def test_text_loader_interface_compliance(self, sample_config):
        """Test that text loader implements DocumentLoaderInterface correctly."""
        from src.interfaces.document_interface import DocumentLoaderInterface
        from src.providers.document.text_loader import TextDocumentLoader
        
        loader = TextDocumentLoader()
        await loader.initialize(sample_config)
        
        # Check that all required methods exist
        assert hasattr(loader, 'initialize')
        assert hasattr(loader, 'load_document')
        assert hasattr(loader, 'load_document_from_bytes')
        assert hasattr(loader, 'health_check')
        assert hasattr(loader, 'get_supported_types')
        assert hasattr(loader, 'get_loader_info')
        
        # Check that it's an instance of the interface
        assert isinstance(loader, DocumentLoaderInterface)
    
    @pytest.mark.asyncio
    async def test_text_loader_document_id_generation(self, temp_text_file, sample_config):
        """Test that document IDs are generated correctly."""
        from src.providers.document.text_loader import TextDocumentLoader
        
        loader = TextDocumentLoader()
        await loader.initialize(sample_config)
        
        document1 = await loader.load_document(temp_text_file, DocumentType.TXT)
        document2 = await loader.load_document(temp_text_file, DocumentType.TXT)
        
        # Document IDs should be unique
        assert document1.document_id != document2.document_id
        assert document1.document_id.startswith("doc_")
        assert document2.document_id.startswith("doc_")
    
    @pytest.mark.asyncio
    async def test_text_loader_metadata_extraction(self, temp_text_file, sample_config):
        """Test that metadata is extracted correctly."""
        from src.providers.document.text_loader import TextDocumentLoader
        
        loader = TextDocumentLoader()
        await loader.initialize(sample_config)
        
        document = await loader.load_document(temp_text_file, DocumentType.TXT)
        
        # Check required metadata fields
        assert "source" in document.metadata
        assert "file_size" in document.metadata
        assert "encoding" in document.metadata
        assert "created_at" in document.metadata
        assert "document_type" in document.metadata
        
        # Check metadata values
        assert document.metadata["source"] == temp_text_file
        assert document.metadata["encoding"] == "utf-8"
        assert document.metadata["document_type"] == "txt"
        assert document.metadata["file_size"] > 0 