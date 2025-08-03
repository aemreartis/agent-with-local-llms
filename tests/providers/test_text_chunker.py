import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from typing import Dict, Any

from src.interfaces.document_interface import (
    DocumentType, ChunkingStrategy, Document, DocumentChunk
)


class TestTextChunker:
    """Test suite for Text Document Chunker implementation."""
    
    @pytest.fixture
    def sample_config(self):
        """Sample configuration for text chunker."""
        return {
            "chunk_size": 1000,
            "chunk_overlap": 200,
            "min_chunk_size": 100,
            "separators": ["\n\n", "\n", ". ", "! ", "? "]
        }
    
    @pytest.fixture
    def sample_document(self):
        """Sample document for testing."""
        return Document(
            document_id="test_doc",
            content="""This is the first paragraph. It contains multiple sentences. This is the end of the first paragraph.

This is the second paragraph. It also has multiple sentences. This is the end of the second paragraph.

This is the third paragraph. It is shorter than the others. End of third paragraph.""",
            document_type=DocumentType.TXT,
            metadata={"title": "Test Document", "author": "Test Author"}
        )
    
    @pytest.fixture
    def long_text(self):
        """Long text for testing chunking strategies."""
        return """This is a very long text that needs to be chunked into smaller pieces. It contains multiple sentences and paragraphs that should be split appropriately. The chunker should respect natural boundaries like sentence endings and paragraph breaks. This text is designed to test various chunking strategies including fixed size, sentence-based, and paragraph-based approaches. Each chunk should maintain semantic coherence while staying within size limits. The chunker should also handle edge cases like very short or very long sentences. It should preserve the original meaning and structure as much as possible. This is the end of our test text. This is additional content to make the text longer. We need to ensure that the text is long enough to be split into multiple chunks when using the fixed size strategy. The chunker should create multiple chunks when the text exceeds the configured chunk size. This is more content to ensure we have enough text for testing. The fixed size chunking should split this text into multiple pieces. Each piece should be within the specified chunk size limit. The overlap should ensure that consecutive chunks share some content. This helps maintain context between chunks. The sentence-based chunking should split at sentence boundaries. The paragraph-based chunking should split at paragraph boundaries. This text should be long enough to test all chunking strategies effectively."""
    
    @pytest.mark.asyncio
    async def test_text_chunker_initialization(self, sample_config):
        """Test text chunker initialization."""
        from src.providers.document.text_chunker import TextChunker
        
        chunker = TextChunker()
        await chunker.initialize(sample_config)
        
        assert chunker.chunk_size == 1000
        assert chunker.chunk_overlap == 200
        assert chunker.min_chunk_size == 100
        assert "\n\n" in chunker.separators
        assert "\n" in chunker.separators
    
    @pytest.mark.asyncio
    async def test_text_chunker_fixed_size_strategy(self, sample_config, long_text):
        """Test fixed size chunking strategy."""
        from src.providers.document.text_chunker import TextChunker
        
        chunker = TextChunker()
        await chunker.initialize(sample_config)
        
        chunks = await chunker.chunk_text(long_text, ChunkingStrategy.FIXED_SIZE, {"document_id": "test_doc"})
        
        assert len(chunks) > 1  # Should create multiple chunks
        for chunk in chunks:
            assert len(chunk.content) <= 1000  # Should respect chunk size
            assert chunk.document_id == "test_doc"
            assert chunk.chunk_id.startswith("chunk_")
            assert "strategy" in chunk.metadata
            assert chunk.metadata["strategy"] == "fixed_size"
    
    @pytest.mark.asyncio
    async def test_text_chunker_sentence_strategy(self, sample_config, long_text):
        """Test sentence-based chunking strategy."""
        from src.providers.document.text_chunker import TextChunker
        
        chunker = TextChunker()
        await chunker.initialize(sample_config)
        
        chunks = await chunker.chunk_text(long_text, ChunkingStrategy.SENTENCE, {"document_id": "test_doc"})
        
        assert len(chunks) > 1  # Should create multiple chunks
        for chunk in chunks:
            assert chunk.document_id == "test_doc"
            assert chunk.metadata["strategy"] == "sentence"
            # Each chunk should end with sentence-ending punctuation
            assert chunk.content.strip().endswith(('.', '!', '?'))
    
    @pytest.mark.asyncio
    async def test_text_chunker_paragraph_strategy(self, sample_config, sample_document):
        """Test paragraph-based chunking strategy."""
        from src.providers.document.text_chunker import TextChunker
        
        chunker = TextChunker()
        await chunker.initialize(sample_config)
        
        chunks = await chunker.chunk_document(sample_document, ChunkingStrategy.PARAGRAPH)
        
        assert len(chunks) == 3  # Should create 3 chunks for 3 paragraphs
        for i, chunk in enumerate(chunks):
            assert chunk.document_id == "test_doc"
            assert chunk.metadata["strategy"] == "paragraph"
            assert chunk.metadata["paragraph_index"] == i
            assert "This is the" in chunk.content  # Each paragraph starts with this
    
    @pytest.mark.asyncio
    async def test_text_chunker_document_chunking(self, sample_config, sample_document):
        """Test chunking a document object."""
        from src.providers.document.text_chunker import TextChunker
        
        chunker = TextChunker()
        await chunker.initialize(sample_config)
        
        chunks = await chunker.chunk_document(sample_document, ChunkingStrategy.FIXED_SIZE)
        
        assert len(chunks) > 0
        for chunk in chunks:
            assert chunk.document_id == "test_doc"
            assert chunk.metadata["title"] == "Test Document"
            assert chunk.metadata["author"] == "Test Author"
            assert chunk.metadata["strategy"] == "fixed_size"
    
    @pytest.mark.asyncio
    async def test_text_chunker_min_chunk_size(self, sample_config):
        """Test that chunks respect minimum size."""
        from src.providers.document.text_chunker import TextChunker
        
        # Create config with larger min chunk size
        config = {**sample_config, "min_chunk_size": 50}
        chunker = TextChunker()
        await chunker.initialize(config)
        
        short_text = "This is a short text."
        chunks = await chunker.chunk_text(short_text, ChunkingStrategy.FIXED_SIZE, {"document_id": "test_doc"})
        
        # Should create one chunk since text is shorter than min_chunk_size
        assert len(chunks) == 1
        assert chunks[0].content == short_text
    
    @pytest.mark.asyncio
    async def test_text_chunker_overlap(self, sample_config, long_text):
        """Test that chunks have proper overlap."""
        from src.providers.document.text_chunker import TextChunker
        
        chunker = TextChunker()
        await chunker.initialize(sample_config)
        
        chunks = await chunker.chunk_text(long_text, ChunkingStrategy.FIXED_SIZE, {"document_id": "test_doc"})
        
        if len(chunks) > 1:
            # Check that consecutive chunks have overlap
            for i in range(len(chunks) - 1):
                current_chunk = chunks[i].content
                next_chunk = chunks[i + 1].content
                
                # Find overlap by checking if end of current chunk appears in start of next chunk
                overlap_found = False
                for j in range(1, min(len(current_chunk), len(next_chunk))):
                    if current_chunk[-j:] == next_chunk[:j]:
                        overlap_found = True
                        break
                
                assert overlap_found, f"Chunks {i} and {i+1} should have overlap"
    
    @pytest.mark.asyncio
    async def test_text_chunker_unsupported_strategy(self, sample_config, sample_document):
        """Test chunking with unsupported strategy."""
        from src.providers.document.text_chunker import TextChunker
        
        chunker = TextChunker()
        await chunker.initialize(sample_config)
        
        with pytest.raises(ValueError, match="Unsupported chunking strategy"):
            await chunker.chunk_document(sample_document, ChunkingStrategy.SEMANTIC)
    
    @pytest.mark.asyncio
    async def test_text_chunker_empty_text(self, sample_config):
        """Test chunking empty text."""
        from src.providers.document.text_chunker import TextChunker
        
        chunker = TextChunker()
        await chunker.initialize(sample_config)
        
        chunks = await chunker.chunk_text("", ChunkingStrategy.FIXED_SIZE, {"document_id": "test_doc"})
        
        assert len(chunks) == 0  # Should return empty list for empty text
    
    @pytest.mark.asyncio
    async def test_text_chunker_health_check_success(self, sample_config):
        """Test successful health check."""
        from src.providers.document.text_chunker import TextChunker
        
        chunker = TextChunker()
        await chunker.initialize(sample_config)
        
        assert await chunker.health_check() is True
    
    def test_text_chunker_get_supported_strategies(self, sample_config):
        """Test getting supported chunking strategies."""
        from src.providers.document.text_chunker import TextChunker
        
        chunker = TextChunker()
        
        strategies = chunker.get_supported_strategies()
        
        assert ChunkingStrategy.FIXED_SIZE in strategies
        assert ChunkingStrategy.SENTENCE in strategies
        assert ChunkingStrategy.PARAGRAPH in strategies
        assert ChunkingStrategy.SEMANTIC not in strategies  # Should not support semantic
    
    def test_text_chunker_get_chunker_info(self, sample_config):
        """Test getting chunker information."""
        from src.providers.document.text_chunker import TextChunker
        
        chunker = TextChunker()
        
        info = chunker.get_chunker_info()
        
        assert info["name"] == "text_chunker"
        assert info["type"] == "document_chunker"
        assert "version" in info
        assert "description" in info
        assert "supported_strategies" in info
    
    @pytest.mark.asyncio
    async def test_text_chunker_interface_compliance(self, sample_config):
        """Test that text chunker implements DocumentChunkerInterface correctly."""
        from src.interfaces.document_interface import DocumentChunkerInterface
        from src.providers.document.text_chunker import TextChunker
        
        chunker = TextChunker()
        await chunker.initialize(sample_config)
        
        # Check that all required methods exist
        assert hasattr(chunker, 'initialize')
        assert hasattr(chunker, 'chunk_document')
        assert hasattr(chunker, 'chunk_text')
        assert hasattr(chunker, 'health_check')
        assert hasattr(chunker, 'get_supported_strategies')
        assert hasattr(chunker, 'get_chunker_info')
        
        # Check that it's an instance of the interface
        assert isinstance(chunker, DocumentChunkerInterface)
    
    @pytest.mark.asyncio
    async def test_text_chunker_chunk_id_generation(self, sample_config, long_text):
        """Test that chunk IDs are generated correctly."""
        from src.providers.document.text_chunker import TextChunker
        
        chunker = TextChunker()
        await chunker.initialize(sample_config)
        
        chunks = await chunker.chunk_text(long_text, ChunkingStrategy.FIXED_SIZE, {"document_id": "test_doc"})
        
        # Check that chunk IDs are unique and properly formatted
        chunk_ids = [chunk.chunk_id for chunk in chunks]
        assert len(chunk_ids) == len(set(chunk_ids))  # All IDs should be unique
        
        for chunk_id in chunk_ids:
            assert chunk_id.startswith("chunk_")
            assert "test_doc" in chunk_id
    
    @pytest.mark.asyncio
    async def test_text_chunker_metadata_preservation(self, sample_config, sample_document):
        """Test that document metadata is preserved in chunks."""
        from src.providers.document.text_chunker import TextChunker
        
        chunker = TextChunker()
        await chunker.initialize(sample_config)
        
        chunks = await chunker.chunk_document(sample_document, ChunkingStrategy.PARAGRAPH)
        
        for chunk in chunks:
            # Original document metadata should be preserved
            assert chunk.metadata["title"] == "Test Document"
            assert chunk.metadata["author"] == "Test Author"
            # Chunk-specific metadata should be added
            assert "strategy" in chunk.metadata
            assert "chunk_index" in chunk.metadata
            assert "paragraph_index" in chunk.metadata 