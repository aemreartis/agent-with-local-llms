"""Integration tests for document processing components.

Tests the integration of document processing components with the existing
provider registry and orchestration system.
"""

import pytest
import asyncio
import tempfile
import os
from unittest.mock import Mock, patch, AsyncMock
from typing import Dict, Any

from src.registry.provider_registry import ProviderRegistry
from src.interfaces.document_interface import DocumentType, ChunkingStrategy
from src.providers.document.text_loader import TextDocumentLoader
from src.providers.document.text_chunker import TextChunker
from src.providers.document.text_processor import TextProcessor
from src.providers.document.document_pipeline import DocumentPipeline


pytestmark = pytest.mark.asyncio


class TestDocumentProcessingIntegration:
    """Test integration of document processing components with provider registry."""
    
    @pytest.fixture
    def provider_registry(self):
        """Create a provider registry with document processing components."""
        registry = ProviderRegistry()
        
        # Register document processing providers
        registry.register_provider("document_loader", "text", TextDocumentLoader)
        registry.register_provider("document_chunker", "text", TextChunker)
        registry.register_provider("document_processor", "text", TextProcessor)
        registry.register_provider("document_pipeline", "text", DocumentPipeline)
        
        return registry
    
    @pytest.fixture
    def sample_text_file(self):
        """Create a temporary text file for testing."""
        content = """This is a sample document for testing.
        
        It contains multiple paragraphs with different content.
        
        This paragraph has some technical terms like API, HTTP, and JSON.
        
        The document should be processed and chunked properly."""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(content)
            temp_file = f.name
        
        yield temp_file
        
        # Cleanup
        os.unlink(temp_file)
    
    async def test_document_loader_registration_and_retrieval(self, provider_registry):
        """Test that document loader can be registered and retrieved from registry."""
        # Get document loader from registry
        loader = await provider_registry.get_provider(
            "document_loader", 
            "text",
            config={"max_file_size": 1024 * 1024}
        )
        
        assert loader is not None
        assert isinstance(loader, TextDocumentLoader)
        assert await loader.health_check()
    
    async def test_document_chunker_registration_and_retrieval(self, provider_registry):
        """Test that document chunker can be registered and retrieved from registry."""
        # Get document chunker from registry
        chunker = await provider_registry.get_provider(
            "document_chunker",
            "text", 
            config={"chunk_size": 100, "chunk_overlap": 20}
        )
        
        assert chunker is not None
        assert isinstance(chunker, TextChunker)
        assert await chunker.health_check()
    
    async def test_document_processor_registration_and_retrieval(self, provider_registry):
        """Test that document processor can be registered and retrieved from registry."""
        # Get document processor from registry
        processor = await provider_registry.get_provider(
            "document_processor",
            "text",
            config={"normalize_whitespace": True, "remove_html": True, "extract_metadata": True}
        )
        
        assert processor is not None
        assert isinstance(processor, TextProcessor)
        assert await processor.health_check()
    
    async def test_document_pipeline_registration_and_retrieval(self, provider_registry):
        """Test that document pipeline can be registered and retrieved from registry."""
        # Get document pipeline from registry
        pipeline = await provider_registry.get_provider(
            "document_pipeline",
            "text",
            config={
                "loader": {"max_file_size": 1024 * 1024},
                "processor": {"normalize_whitespace": True, "extract_metadata": True},
                "chunker": {"chunk_size": 100, "chunk_overlap": 20}
            }
        )
        
        assert pipeline is not None
        assert isinstance(pipeline, DocumentPipeline)
        assert await pipeline.health_check()
    
    async def test_complete_document_processing_workflow(self, provider_registry, sample_text_file):
        """Test complete document processing workflow through registry."""
        # Get document pipeline from registry
        pipeline = await provider_registry.get_provider(
            "document_pipeline",
            "text",
            config={
                "loader": {"max_file_size": 1024 * 1024},
                "processor": {"normalize_whitespace": True, "extract_metadata": True},
                "chunker": {"chunk_size": 100, "chunk_overlap": 20}
            }
        )
        
        # Process document
        result = await pipeline.process_file(sample_text_file, ChunkingStrategy.FIXED_SIZE)
        
        assert result is not None
        assert result.document_id is not None
        assert result.content is not None
        assert len(result.chunks) > 0
        
        # Verify chunks have proper metadata
        for chunk in result.chunks:
            assert chunk.chunk_id is not None
            assert chunk.document_id == result.document_id
            assert chunk.content is not None
            assert len(chunk.content) > 0
    
    async def test_document_processing_with_different_strategies(self, provider_registry, sample_text_file):
        """Test document processing with different chunking strategies."""
        pipeline = await provider_registry.get_provider(
            "document_pipeline",
            "text",
            config={
                "loader": {"max_file_size": 1024 * 1024},
                "processor": {"normalize_whitespace": True, "extract_metadata": True},
                "chunker": {"chunk_size": 50, "chunk_overlap": 10}
            }
        )
        
        # Test fixed size strategy
        fixed_result = await pipeline.process_file(sample_text_file, ChunkingStrategy.FIXED_SIZE)
        assert len(fixed_result.chunks) > 0
        
        # Test sentence strategy
        sentence_result = await pipeline.process_file(sample_text_file, ChunkingStrategy.SENTENCE)
        assert len(sentence_result.chunks) > 0
        
        # Test paragraph strategy
        paragraph_result = await pipeline.process_file(sample_text_file, ChunkingStrategy.PARAGRAPH)
        assert len(paragraph_result.chunks) > 0
    
    async def test_document_processing_error_handling(self, provider_registry):
        """Test error handling in document processing integration."""
        pipeline = await provider_registry.get_provider(
            "document_pipeline",
            "text",
            config={
                "loader": {"max_file_size": 1024 * 1024},
                "processor": {"normalize_whitespace": True, "extract_metadata": True},
                "chunker": {"chunk_size": 100, "chunk_overlap": 20}
            }
        )
        
        # Test with non-existent file
        with pytest.raises(Exception):
            await pipeline.process_file("non_existent_file.txt", ChunkingStrategy.FIXED_SIZE)
    
    async def test_document_processing_health_checks(self, provider_registry):
        """Test health checks for all document processing components."""
        # Test loader health check
        loader = await provider_registry.get_provider("document_loader", "text")
        assert await loader.health_check()
        
        # Test chunker health check
        chunker = await provider_registry.get_provider("document_chunker", "text")
        assert await chunker.health_check()
        
        # Test processor health check
        processor = await provider_registry.get_provider("document_processor", "text")
        assert await processor.health_check()
        
        # Test pipeline health check (needs configuration to initialize components)
        pipeline = await provider_registry.get_provider(
            "document_pipeline",
            "text",
            config={
                "loader": {"max_file_size": 1024 * 1024},
                "processor": {"normalize_whitespace": True, "extract_metadata": True},
                "chunker": {"chunk_size": 100, "chunk_overlap": 20}
            }
        )
        assert await pipeline.health_check()
    
    async def test_document_processing_provider_info(self, provider_registry):
        """Test that document processing providers return proper info."""
        # Test loader info
        loader = await provider_registry.get_provider("document_loader", "text")
        info = loader.get_loader_info()
        assert "name" in info
        assert "supported_types" in info
        
        # Test chunker info
        chunker = await provider_registry.get_provider("document_chunker", "text")
        info = chunker.get_chunker_info()
        assert "name" in info
        assert "supported_strategies" in info
        
        # Test processor info
        processor = await provider_registry.get_provider("document_processor", "text")
        info = processor.get_processor_info()
        assert "name" in info
        assert "capabilities" in info
        
        # Test pipeline info
        pipeline = await provider_registry.get_provider("document_pipeline", "text")
        info = pipeline.get_pipeline_info()
        assert "name" in info
        assert "components" in info
    
    async def test_document_processing_batch_operations(self, provider_registry):
        """Test batch document processing operations."""
        pipeline = await provider_registry.get_provider(
            "document_pipeline",
            "text",
            config={
                "loader": {"max_file_size": 1024 * 1024},
                "processor": {"normalize_whitespace": True, "extract_metadata": True},
                "chunker": {"chunk_size": 100, "chunk_overlap": 20}
            }
        )
        
        # Create multiple temporary files
        files = []
        for i in range(3):
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                f.write(f"Document {i} content for batch processing.")
                files.append(f.name)
        
        try:
            # Process batch
            results = await pipeline.batch_process(files, ChunkingStrategy.FIXED_SIZE)
            
            assert len(results) == 3
            for result in results:
                assert result is not None
                assert result.document_id is not None
                assert len(result.chunks) > 0
        finally:
            # Cleanup
            for file in files:
                os.unlink(file)
    
    async def test_document_processing_with_bytes_content(self, provider_registry):
        """Test document processing with bytes content instead of file."""
        pipeline = await provider_registry.get_provider(
            "document_pipeline",
            "text",
            config={
                "loader": {"max_file_size": 1024 * 1024},
                "processor": {"normalize_whitespace": True, "extract_metadata": True},
                "chunker": {"chunk_size": 100, "chunk_overlap": 20}
            }
        )
        
        content = b"This is sample content for bytes processing.\n\nIt has multiple lines and paragraphs."
        
        # Process bytes content
        result = await pipeline.process_bytes(content, DocumentType.TXT, "test.txt", ChunkingStrategy.FIXED_SIZE)
        
        assert result is not None
        assert result.document_id is not None
        assert result.content is not None
        assert len(result.chunks) > 0 