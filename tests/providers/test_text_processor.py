import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from typing import Dict, Any

from src.interfaces.document_interface import DocumentType, Document


class TestTextProcessor:
    """Test suite for Text Document Processor implementation."""
    
    @pytest.fixture
    def sample_config(self):
        """Sample configuration for text processor."""
        return {
            "remove_extra_whitespace": True,
            "normalize_unicode": True,
            "remove_html_tags": True,
            "extract_metadata": True,
            "language_detection": True
        }
    
    @pytest.fixture
    def sample_document(self):
        """Sample document for testing."""
        return Document(
            document_id="test_doc",
            content="""This is a test document with some formatting issues.

It has multiple spaces    and newlines.

It also contains some HTML tags like <b>bold</b> and <i>italic</i> text.

The document has 5 paragraphs and contains various punctuation marks!""",
            document_type=DocumentType.TXT,
            metadata={"title": "Test Document", "author": "Test Author"}
        )
    
    @pytest.fixture
    def html_document(self):
        """Sample HTML document for testing."""
        return Document(
            document_id="html_doc",
            content="""<html>
<head><title>Test HTML Document</title></head>
<body>
<h1>Main Title</h1>
<p>This is a paragraph with <b>bold</b> and <i>italic</i> text.</p>
<p>Another paragraph with <a href="http://example.com">a link</a>.</p>
<div>Some div content with <span>inline elements</span>.</div>
</body>
</html>""",
            document_type=DocumentType.HTML,
            metadata={"title": "Test HTML Document"}
        )
    
    @pytest.mark.asyncio
    async def test_text_processor_initialization(self, sample_config):
        """Test text processor initialization."""
        from src.providers.document.text_processor import TextProcessor
        
        processor = TextProcessor()
        await processor.initialize(sample_config)
        
        assert processor.remove_extra_whitespace is True
        assert processor.normalize_unicode is True
        assert processor.remove_html_tags is True
        assert processor.extract_metadata_flag is True
        assert processor.language_detection is True
    
    @pytest.mark.asyncio
    async def test_text_processor_process_document_success(self, sample_config, sample_document):
        """Test successful document processing."""
        from src.providers.document.text_processor import TextProcessor
        
        processor = TextProcessor()
        await processor.initialize(sample_config)
        
        processed_doc = await processor.process_document(sample_document)
        
        assert processed_doc.document_id == "test_doc"
        assert processed_doc.document_type == DocumentType.TXT
        assert "processed" in processed_doc.metadata
        assert processed_doc.metadata["processed"] is True
        assert "processor" in processed_doc.metadata
        assert processed_doc.metadata["processor"] == "text_processor"
        assert "processing_timestamp" in processed_doc.metadata
    
    @pytest.mark.asyncio
    async def test_text_processor_clean_content_whitespace(self, sample_config):
        """Test content cleaning with whitespace normalization."""
        from src.providers.document.text_processor import TextProcessor
        
        processor = TextProcessor()
        await processor.initialize(sample_config)
        
        dirty_content = "This   has    multiple    spaces\n\nand\n\nnewlines."
        cleaned_content = await processor.clean_content(dirty_content)
        
        # Should normalize whitespace
        assert "   " not in cleaned_content  # No multiple spaces
        assert "\n\n" not in cleaned_content  # No multiple newlines
        assert cleaned_content == "This has multiple spaces and newlines."
    
    @pytest.mark.asyncio
    async def test_text_processor_clean_content_html_tags(self, sample_config):
        """Test content cleaning with HTML tag removal."""
        from src.providers.document.text_processor import TextProcessor
        
        processor = TextProcessor()
        await processor.initialize(sample_config)
        
        html_content = "This is <b>bold</b> and <i>italic</i> text with <a href='#'>link</a>."
        cleaned_content = await processor.clean_content(html_content)
        
        # Should remove HTML tags
        assert "<b>" not in cleaned_content
        assert "</b>" not in cleaned_content
        assert "<i>" not in cleaned_content
        assert "</i>" not in cleaned_content
        assert "<a" not in cleaned_content
        assert "href" not in cleaned_content
        assert cleaned_content == "This is bold and italic text with link."
    
    @pytest.mark.asyncio
    async def test_text_processor_clean_content_unicode(self, sample_config):
        """Test content cleaning with unicode normalization."""
        from src.providers.document.text_processor import TextProcessor
        
        processor = TextProcessor()
        await processor.initialize(sample_config)
        
        # Test with unicode characters
        unicode_content = "café résumé naïve"
        cleaned_content = await processor.clean_content(unicode_content)
        
        # Should normalize unicode
        assert cleaned_content == "café résumé naïve"
    
    @pytest.mark.asyncio
    async def test_text_processor_extract_metadata_success(self, sample_config, sample_document):
        """Test successful metadata extraction."""
        from src.providers.document.text_processor import TextProcessor
        
        processor = TextProcessor()
        await processor.initialize(sample_config)
        
        metadata = await processor.extract_metadata(sample_document)
        
        # Check basic metadata
        assert "word_count" in metadata
        assert "char_count" in metadata
        assert "document_type" in metadata
        assert "paragraph_count" in metadata
        assert "sentence_count" in metadata
        
        # Check values
        assert metadata["document_type"] == "txt"
        assert metadata["word_count"] > 0
        assert metadata["char_count"] > 0
        assert metadata["paragraph_count"] == 4  # Based on sample document (after cleaning)
        assert metadata["sentence_count"] > 0
    
    @pytest.mark.asyncio
    async def test_text_processor_extract_metadata_html(self, sample_config, html_document):
        """Test metadata extraction from HTML document."""
        from src.providers.document.text_processor import TextProcessor
        
        processor = TextProcessor()
        await processor.initialize(sample_config)
        
        metadata = await processor.extract_metadata(html_document)
        
        # Check HTML-specific metadata
        assert "html_tags" in metadata
        assert "title" in metadata
        assert metadata["document_type"] == "html"
        assert metadata["title"] == "Test HTML Document"
        assert len(metadata["html_tags"]) > 0
    
    @pytest.mark.asyncio
    async def test_text_processor_health_check_success(self, sample_config):
        """Test successful health check."""
        from src.providers.document.text_processor import TextProcessor
        
        processor = TextProcessor()
        await processor.initialize(sample_config)
        
        assert await processor.health_check() is True
    
    def test_text_processor_get_processor_info(self, sample_config):
        """Test getting processor information."""
        from src.providers.document.text_processor import TextProcessor
        
        processor = TextProcessor()
        
        info = processor.get_processor_info()
        
        assert info["name"] == "text_processor"
        assert info["type"] == "document_processor"
        assert "version" in info
        assert "description" in info
        assert "capabilities" in info
    
    @pytest.mark.asyncio
    async def test_text_processor_interface_compliance(self, sample_config):
        """Test that text processor implements DocumentProcessorInterface correctly."""
        from src.interfaces.document_interface import DocumentProcessorInterface
        from src.providers.document.text_processor import TextProcessor
        
        processor = TextProcessor()
        await processor.initialize(sample_config)
        
        # Check that all required methods exist
        assert hasattr(processor, 'initialize')
        assert hasattr(processor, 'process_document')
        assert hasattr(processor, 'extract_metadata')
        assert hasattr(processor, 'clean_content')
        assert hasattr(processor, 'health_check')
        assert hasattr(processor, 'get_processor_info')
        
        # Check that it's an instance of the interface
        assert isinstance(processor, DocumentProcessorInterface)
    
    @pytest.mark.asyncio
    async def test_text_processor_empty_document(self, sample_config):
        """Test processing empty document."""
        from src.providers.document.text_processor import TextProcessor
        
        processor = TextProcessor()
        await processor.initialize(sample_config)
        
        empty_doc = Document(
            document_id="empty_doc",
            content="",
            document_type=DocumentType.TXT,
            metadata={}
        )
        
        processed_doc = await processor.process_document(empty_doc)
        
        assert processed_doc.content == ""
        assert processed_doc.metadata["processed"] is True
        assert processed_doc.metadata["word_count"] == 0
        assert processed_doc.metadata["char_count"] == 0
    
    @pytest.mark.asyncio
    async def test_text_processor_content_preservation(self, sample_config, sample_document):
        """Test that important content is preserved during processing."""
        from src.providers.document.text_processor import TextProcessor
        
        processor = TextProcessor()
        await processor.initialize(sample_config)
        
        processed_doc = await processor.process_document(sample_document)
        
        # Check that key content is preserved
        assert "test document" in processed_doc.content.lower()
        assert "paragraphs" in processed_doc.content.lower()
        assert "html tags" in processed_doc.content.lower()  # Text about HTML tags, not actual tags
        
        # Check that original metadata is preserved
        assert processed_doc.metadata["title"] == "Test Document"
        assert processed_doc.metadata["author"] == "Test Author"
    
    @pytest.mark.asyncio
    async def test_text_processor_metadata_enhancement(self, sample_config, sample_document):
        """Test that metadata is enhanced during processing."""
        from src.providers.document.text_processor import TextProcessor
        
        processor = TextProcessor()
        await processor.initialize(sample_config)
        
        processed_doc = await processor.process_document(sample_document)
        
        # Check that processing metadata is added
        assert "processed" in processed_doc.metadata
        assert "processor" in processed_doc.metadata
        assert "processing_timestamp" in processed_doc.metadata
        assert "processing_duration" in processed_doc.metadata
        
        # Check that extracted metadata is added
        assert "word_count" in processed_doc.metadata
        assert "char_count" in processed_doc.metadata
        assert "paragraph_count" in processed_doc.metadata
        assert "sentence_count" in processed_doc.metadata
    
    @pytest.mark.asyncio
    async def test_text_processor_clean_content_edge_cases(self, sample_config):
        """Test content cleaning with edge cases."""
        from src.providers.document.text_processor import TextProcessor
        
        processor = TextProcessor()
        await processor.initialize(sample_config)
        
        # Test with only whitespace
        whitespace_content = "   \n\n\t\t   "
        cleaned_content = await processor.clean_content(whitespace_content)
        assert cleaned_content == ""
        
        # Test with special characters
        special_content = "Text with &amp; &lt; &gt; entities"
        cleaned_content = await processor.clean_content(special_content)
        assert "&amp;" not in cleaned_content
        assert "&lt;" not in cleaned_content
        assert "&gt;" not in cleaned_content
    
    @pytest.mark.asyncio
    async def test_text_processor_config_disabled_features(self):
        """Test processor with disabled features."""
        config = {
            "remove_extra_whitespace": False,
            "normalize_unicode": False,
            "remove_html_tags": False,
            "extract_metadata": False,
            "language_detection": False
        }
        
        from src.providers.document.text_processor import TextProcessor
        
        processor = TextProcessor()
        await processor.initialize(config)
        
        # Test that features are disabled
        dirty_content = "This   has    spaces\n\nand\n\nnewlines."
        cleaned_content = await processor.clean_content(dirty_content)
        
        # Should preserve original formatting when disabled
        assert "   " in cleaned_content  # Multiple spaces preserved
        assert "\n\n" in cleaned_content  # Multiple newlines preserved 