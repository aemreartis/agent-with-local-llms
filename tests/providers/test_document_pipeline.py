import pytest
import tempfile
import os
from unittest.mock import AsyncMock, patch, MagicMock
from typing import Dict, Any

from src.interfaces.document_interface import DocumentType, ChunkingStrategy, Document


class TestDocumentPipeline:
    """Test suite for Document Pipeline implementation."""
    
    @pytest.fixture
    def sample_config(self):
        """Sample configuration for document pipeline."""
        return {
            "loader": {
                "type": "text",
                "config": {
                    "encoding": "utf-8",
                    "max_file_size": 10485760,
                    "allowed_extensions": [".txt", ".md", ".csv"]
                }
            },
            "processor": {
                "type": "text",
                "config": {
                    "remove_extra_whitespace": True,
                    "normalize_unicode": True,
                    "remove_html_tags": True,
                    "extract_metadata": True,
                    "language_detection": True
                }
            },
            "chunker": {
                "type": "text",
                "config": {
                    "chunk_size": 1000,
                    "chunk_overlap": 200,
                    "min_chunk_size": 100,
                    "separators": ["\n\n", "\n", ". ", "! ", "? "]
                }
            }
        }
    
    @pytest.fixture
    def sample_text_content(self):
        """Sample text content for testing."""
        return """This is a sample document for testing the document pipeline.

It contains multiple paragraphs that should be processed and chunked appropriately.

The pipeline should load this document, process it to clean the content and extract metadata, and then chunk it into smaller pieces for further processing.

This is the fourth paragraph to ensure we have enough content for meaningful chunking."""
    
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
    async def test_document_pipeline_initialization(self, sample_config):
        """Test document pipeline initialization."""
        from src.providers.document.document_pipeline import DocumentPipeline
        
        pipeline = DocumentPipeline()
        await pipeline.initialize(sample_config)
        
        assert pipeline.loader is not None
        assert pipeline.processor is not None
        assert pipeline.chunker is not None
        assert pipeline.config == sample_config
    
    @pytest.mark.asyncio
    async def test_document_pipeline_process_file_success(self, sample_config, temp_text_file):
        """Test successful file processing through the pipeline."""
        from src.providers.document.document_pipeline import DocumentPipeline
        
        pipeline = DocumentPipeline()
        await pipeline.initialize(sample_config)
        
        document = await pipeline.process_file(temp_text_file, ChunkingStrategy.PARAGRAPH)
        
        # Check document properties
        assert document.document_id is not None
        assert document.document_type == DocumentType.TXT
        assert "sample document" in document.content.lower()
        
        # Check that document was processed
        assert document.metadata["processed"] is True
        assert document.metadata["processor"] == "text_processor"
        
        # Check that document was chunked
        assert len(document.chunks) > 0
        for chunk in document.chunks:
            assert chunk.document_id == document.document_id
            assert chunk.metadata["strategy"] == "paragraph"
    
    @pytest.mark.asyncio
    async def test_document_pipeline_process_bytes_success(self, sample_config):
        """Test successful bytes processing through the pipeline."""
        from src.providers.document.document_pipeline import DocumentPipeline
        
        pipeline = DocumentPipeline()
        await pipeline.initialize(sample_config)
        
        content = b"This is test content from bytes that should be processed and chunked."
        document = await pipeline.process_bytes(content, DocumentType.TXT, "test.txt", ChunkingStrategy.FIXED_SIZE)
        
        # Check document properties
        assert document.document_id is not None
        assert document.document_type == DocumentType.TXT
        assert "test content" in document.content.lower()
        
        # Check that document was processed
        assert document.metadata["processed"] is True
        assert document.metadata["processor"] == "text_processor"
        
        # Check that document was chunked
        assert len(document.chunks) > 0
        for chunk in document.chunks:
            assert chunk.document_id == document.document_id
            assert chunk.metadata["strategy"] == "fixed_size"
    
    @pytest.mark.asyncio
    async def test_document_pipeline_batch_process_success(self, sample_config):
        """Test successful batch processing through the pipeline."""
        from src.providers.document.document_pipeline import DocumentPipeline
        
        pipeline = DocumentPipeline()
        await pipeline.initialize(sample_config)
        
        # Create temporary files for batch processing
        temp_files = []
        try:
            for i in range(3):
                with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                    f.write(f"This is test document {i} for batch processing.")
                    temp_files.append(f.name)
            
            documents = await pipeline.batch_process(temp_files, ChunkingStrategy.SENTENCE)
            
            # Check that all documents were processed
            assert len(documents) == 3
            
            for i, document in enumerate(documents):
                assert document.document_id is not None
                assert document.document_type == DocumentType.TXT
                assert f"test document {i}" in document.content.lower()
                assert document.metadata["processed"] is True
                assert len(document.chunks) > 0
                
        finally:
            # Cleanup
            for temp_file in temp_files:
                os.unlink(temp_file)
    
    @pytest.mark.asyncio
    async def test_document_pipeline_different_chunking_strategies(self, sample_config, temp_text_file):
        """Test pipeline with different chunking strategies."""
        from src.providers.document.document_pipeline import DocumentPipeline
        
        pipeline = DocumentPipeline()
        await pipeline.initialize(sample_config)
        
        # Test fixed size strategy
        doc1 = await pipeline.process_file(temp_text_file, ChunkingStrategy.FIXED_SIZE)
        assert doc1.chunks[0].metadata["strategy"] == "fixed_size"
        
        # Test sentence strategy
        doc2 = await pipeline.process_file(temp_text_file, ChunkingStrategy.SENTENCE)
        assert doc2.chunks[0].metadata["strategy"] == "sentence"
        
        # Test paragraph strategy
        doc3 = await pipeline.process_file(temp_text_file, ChunkingStrategy.PARAGRAPH)
        assert doc3.chunks[0].metadata["strategy"] == "paragraph"
    
    @pytest.mark.asyncio
    async def test_document_pipeline_health_check_success(self, sample_config):
        """Test successful health check."""
        from src.providers.document.document_pipeline import DocumentPipeline
        
        pipeline = DocumentPipeline()
        await pipeline.initialize(sample_config)
        
        assert await pipeline.health_check() is True
    
    @pytest.mark.asyncio
    async def test_document_pipeline_health_check_failure(self):
        """Test health check failure when components are not initialized."""
        from src.providers.document.document_pipeline import DocumentPipeline
        
        pipeline = DocumentPipeline()
        
        # Should fail when not initialized
        assert await pipeline.health_check() is False
    
    def test_document_pipeline_get_pipeline_info(self, sample_config):
        """Test getting pipeline information."""
        from src.providers.document.document_pipeline import DocumentPipeline
        
        pipeline = DocumentPipeline()
        
        info = pipeline.get_pipeline_info()
        
        assert info["name"] == "document_pipeline"
        assert info["type"] == "document_pipeline"
        assert "version" in info
        assert "description" in info
        assert "components" in info
    
    @pytest.mark.asyncio
    async def test_document_pipeline_interface_compliance(self, sample_config):
        """Test that document pipeline implements DocumentPipelineInterface correctly."""
        from src.interfaces.document_interface import DocumentPipelineInterface
        from src.providers.document.document_pipeline import DocumentPipeline
        
        pipeline = DocumentPipeline()
        await pipeline.initialize(sample_config)
        
        # Check that all required methods exist
        assert hasattr(pipeline, 'initialize')
        assert hasattr(pipeline, 'process_file')
        assert hasattr(pipeline, 'process_bytes')
        assert hasattr(pipeline, 'batch_process')
        assert hasattr(pipeline, 'health_check')
        assert hasattr(pipeline, 'get_pipeline_info')
        
        # Check that it's an instance of the interface
        assert isinstance(pipeline, DocumentPipelineInterface)
    
    @pytest.mark.asyncio
    async def test_document_pipeline_error_handling(self, sample_config):
        """Test error handling in the pipeline."""
        from src.providers.document.document_pipeline import DocumentPipeline
        
        pipeline = DocumentPipeline()
        await pipeline.initialize(sample_config)
        
        # Test with non-existent file
        with pytest.raises(FileNotFoundError):
            await pipeline.process_file("nonexistent.txt", ChunkingStrategy.FIXED_SIZE)
    
    @pytest.mark.asyncio
    async def test_document_pipeline_metadata_preservation(self, sample_config, temp_text_file):
        """Test that metadata is preserved through the pipeline."""
        from src.providers.document.document_pipeline import DocumentPipeline
        
        pipeline = DocumentPipeline()
        await pipeline.initialize(sample_config)
        
        document = await pipeline.process_file(temp_text_file, ChunkingStrategy.PARAGRAPH)
        
        # Check that source metadata is preserved
        assert "source" in document.metadata
        assert document.metadata["source"] == temp_text_file
        
        # Check that processing metadata is added
        assert "processed" in document.metadata
        assert "processing_timestamp" in document.metadata
        assert "processing_duration" in document.metadata
        
        # Check that extracted metadata is present
        assert "word_count" in document.metadata
        assert "char_count" in document.metadata
        assert "paragraph_count" in document.metadata
    
    @pytest.mark.asyncio
    async def test_document_pipeline_component_initialization(self, sample_config):
        """Test that all components are properly initialized."""
        from src.providers.document.document_pipeline import DocumentPipeline
        
        pipeline = DocumentPipeline()
        await pipeline.initialize(sample_config)
        
        # Check that components are initialized
        assert pipeline.loader is not None
        assert pipeline.processor is not None
        assert pipeline.chunker is not None
        
        # Check that components are healthy
        assert await pipeline.loader.health_check() is True
        assert await pipeline.processor.health_check() is True
        assert await pipeline.chunker.health_check() is True
    
    @pytest.mark.asyncio
    async def test_document_pipeline_empty_batch(self, sample_config):
        """Test batch processing with empty file list."""
        from src.providers.document.document_pipeline import DocumentPipeline
        
        pipeline = DocumentPipeline()
        await pipeline.initialize(sample_config)
        
        documents = await pipeline.batch_process([], ChunkingStrategy.FIXED_SIZE)
        
        assert len(documents) == 0
    
    @pytest.mark.asyncio
    async def test_document_pipeline_unsupported_strategy(self, sample_config, temp_text_file):
        """Test pipeline with unsupported chunking strategy."""
        from src.providers.document.document_pipeline import DocumentPipeline
        
        pipeline = DocumentPipeline()
        await pipeline.initialize(sample_config)
        
        with pytest.raises(ValueError, match="Unsupported chunking strategy"):
            await pipeline.process_file(temp_text_file, ChunkingStrategy.SEMANTIC)
    
    @pytest.mark.asyncio
    async def test_document_pipeline_processing_order(self, sample_config, temp_text_file):
        """Test that processing happens in the correct order."""
        from src.providers.document.document_pipeline import DocumentPipeline
        
        pipeline = DocumentPipeline()
        await pipeline.initialize(sample_config)
        
        document = await pipeline.process_file(temp_text_file, ChunkingStrategy.PARAGRAPH)
        
        # Check processing order: load -> process -> chunk
        assert "source" in document.metadata  # From loader
        assert "processed" in document.metadata  # From processor
        assert len(document.chunks) > 0  # From chunker
        
        # Check that chunks have processed metadata
        for chunk in document.chunks:
            assert "strategy" in chunk.metadata  # From chunker
            assert chunk.document_id == document.document_id  # Link to original document 