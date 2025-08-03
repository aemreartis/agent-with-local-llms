import re
import time
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List
from html import unescape
import unicodedata

from src.interfaces.document_interface import DocumentProcessorInterface, Document

logger = logging.getLogger(__name__)


class TextProcessor(DocumentProcessorInterface):
    """Text document processor for cleaning and extracting metadata from documents."""
    
    def __init__(self):
        """Initialize the text processor."""
        self.remove_extra_whitespace = True
        self.normalize_unicode = True
        self.remove_html_tags = True
        self.extract_metadata_flag = True
        self.language_detection = True
    
    async def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize the text processor with configuration."""
        self.remove_extra_whitespace = config.get("remove_extra_whitespace", True)
        self.normalize_unicode = config.get("normalize_unicode", True)
        self.remove_html_tags = config.get("remove_html_tags", True)
        self.extract_metadata_flag = config.get("extract_metadata", True)
        self.language_detection = config.get("language_detection", True)
        
        logger.info(f"Text processor initialized with features: whitespace={self.remove_extra_whitespace}, unicode={self.normalize_unicode}, html={self.remove_html_tags}")
    
    async def process_document(self, document: Document) -> Document:
        """Process a document (extract metadata, clean content, etc.)."""
        try:
            start_time = time.time()
            
            # Clean content
            if self.remove_extra_whitespace or self.normalize_unicode or self.remove_html_tags:
                document.content = await self.clean_content(document.content)
            
            # Extract metadata
            if self.extract_metadata_flag:
                extracted_metadata = await self.extract_metadata(document)
                document.metadata.update(extracted_metadata)
            
            # Add processing metadata
            processing_time = time.time() - start_time
            document.metadata.update({
                "processed": True,
                "processor": "text_processor",
                "processing_timestamp": datetime.now(timezone.utc).isoformat(),
                "processing_duration": processing_time
            })
            
            logger.info(f"Successfully processed document {document.document_id} in {processing_time:.3f}s")
            return document
            
        except Exception as e:
            logger.error(f"Failed to process document {document.document_id}: {str(e)}")
            raise
    
    async def extract_metadata(self, document: Document) -> Dict[str, Any]:
        """Extract metadata from a document."""
        try:
            metadata = {
                "word_count": len(document.content.split()),
                "char_count": len(document.content),
                "document_type": document.document_type.value,
                "paragraph_count": len([p for p in document.content.split('\n\n') if p.strip()]),
                "sentence_count": len(re.split(r'[.!?]+', document.content))
            }
            
            # Extract HTML-specific metadata
            if document.document_type.value == "html":
                html_metadata = self._extract_html_metadata(document.content)
                metadata.update(html_metadata)
            
            # Extract title if available
            if "title" in document.metadata:
                metadata["title"] = document.metadata["title"]
            
            # Basic language detection (simplified)
            if self.language_detection:
                metadata["detected_language"] = self._detect_language(document.content)
            
            return metadata
            
        except Exception as e:
            logger.error(f"Failed to extract metadata from document {document.document_id}: {str(e)}")
            return {}
    
    async def clean_content(self, content: str) -> str:
        """Clean and normalize document content."""
        try:
            if not content:
                return ""
            
            cleaned_content = content
            
            # Remove HTML tags
            if self.remove_html_tags:
                cleaned_content = self._remove_html_tags(cleaned_content)
            
            # Normalize unicode
            if self.normalize_unicode:
                cleaned_content = self._normalize_unicode(cleaned_content)
            
            # Remove extra whitespace
            if self.remove_extra_whitespace:
                cleaned_content = self._normalize_whitespace(cleaned_content)
            
            return cleaned_content
            
        except Exception as e:
            logger.error(f"Failed to clean content: {str(e)}")
            return content
    
    async def health_check(self) -> bool:
        """Check if the text processor is healthy."""
        try:
            # Basic health check - verify configuration is valid
            if not isinstance(self.remove_extra_whitespace, bool):
                return False
            
            if not isinstance(self.normalize_unicode, bool):
                return False
            
            if not isinstance(self.remove_html_tags, bool):
                return False
            
            if not isinstance(self.extract_metadata_flag, bool):
                return False
            
            if not isinstance(self.language_detection, bool):
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return False
    
    def get_processor_info(self) -> Dict[str, Any]:
        """Get information about the text processor."""
        return {
            "name": "text_processor",
            "type": "document_processor",
            "version": "1.0.0",
            "description": "Text document processor for cleaning and extracting metadata",
            "capabilities": {
                "remove_extra_whitespace": self.remove_extra_whitespace,
                "normalize_unicode": self.normalize_unicode,
                "remove_html_tags": self.remove_html_tags,
                "extract_metadata": self.extract_metadata_flag,
                "language_detection": self.language_detection
            }
        }
    
    def _remove_html_tags(self, content: str) -> str:
        """Remove HTML tags from content."""
        # Remove HTML tags
        content = re.sub(r'<[^>]+>', '', content)
        
        # Decode HTML entities
        content = unescape(content)
        
        return content
    
    def _normalize_unicode(self, content: str) -> str:
        """Normalize unicode characters."""
        # Normalize unicode to NFC form
        content = unicodedata.normalize('NFC', content)
        return content
    
    def _normalize_whitespace(self, content: str) -> str:
        """Normalize whitespace in content."""
        # Replace multiple spaces with single space
        content = re.sub(r' +', ' ', content)
        
        # Replace multiple newlines with single space
        content = re.sub(r'\n+', ' ', content)
        
        # Replace multiple tabs with single space
        content = re.sub(r'\t+', ' ', content)
        
        # Strip leading/trailing whitespace
        content = content.strip()
        
        return content
    
    def _extract_html_metadata(self, content: str) -> Dict[str, Any]:
        """Extract metadata from HTML content."""
        metadata = {
            "html_tags": [],
            "title": None
        }
        
        # Extract HTML tags
        tags = re.findall(r'<([^>]+)>', content)
        metadata["html_tags"] = list(set(tags))
        
        # Extract title
        title_match = re.search(r'<title[^>]*>(.*?)</title>', content, re.IGNORECASE | re.DOTALL)
        if title_match:
            metadata["title"] = title_match.group(1).strip()
        
        return metadata
    
    def _detect_language(self, content: str) -> str:
        """Simple language detection (basic implementation)."""
        # This is a very basic implementation
        # In a real system, you would use a proper language detection library
        
        # Count common English words
        english_words = ['the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by']
        content_lower = content.lower()
        
        english_count = sum(1 for word in english_words if word in content_lower.split())
        
        # Simple heuristic: if more than 3 English words found, assume English
        if english_count > 3:
            return "en"
        else:
            return "unknown" 