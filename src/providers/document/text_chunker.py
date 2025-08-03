import re
import uuid
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List

from src.interfaces.document_interface import DocumentChunkerInterface, ChunkingStrategy, Document, DocumentChunk

logger = logging.getLogger(__name__)


class TextChunker(DocumentChunkerInterface):
    """Text document chunker for splitting documents into smaller pieces."""
    
    def __init__(self):
        """Initialize the text chunker."""
        self.chunk_size = 1000
        self.chunk_overlap = 200
        self.min_chunk_size = 100
        self.separators = ["\n\n", "\n", ". ", "! ", "? "]
        self._chunk_counter = 0
    
    async def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize the text chunker with configuration."""
        self.chunk_size = config.get("chunk_size", 1000)
        self.chunk_overlap = config.get("chunk_overlap", 200)
        self.min_chunk_size = config.get("min_chunk_size", 100)
        self.separators = config.get("separators", ["\n\n", "\n", ". ", "! ", "? "])
        
        logger.info(f"Text chunker initialized with chunk_size: {self.chunk_size}, overlap: {self.chunk_overlap}")
    
    async def chunk_document(self, document: Document, strategy: ChunkingStrategy) -> List[DocumentChunk]:
        """Chunk a document using the specified strategy."""
        try:
            # Validate strategy
            if strategy not in self.get_supported_strategies():
                raise ValueError(f"Unsupported chunking strategy: {strategy}")
            
            # Add document_id to metadata
            metadata = {**document.metadata, "document_id": document.document_id}
            
            # Chunk the text content
            chunks = await self.chunk_text(document.content, strategy, metadata)
            
            # Update document with chunks
            document.chunks = chunks
            
            logger.info(f"Successfully chunked document {document.document_id} into {len(chunks)} chunks")
            return chunks
            
        except Exception as e:
            logger.error(f"Failed to chunk document {document.document_id}: {str(e)}")
            raise
    
    async def chunk_text(self, text: str, strategy: ChunkingStrategy, metadata: Dict[str, Any]) -> List[DocumentChunk]:
        """Chunk text content using the specified strategy."""
        try:
            if not text.strip():
                return []
            
            document_id = metadata.get("document_id", "unknown")
            
            if strategy == ChunkingStrategy.FIXED_SIZE:
                return self._chunk_fixed_size(text, document_id, metadata)
            elif strategy == ChunkingStrategy.SENTENCE:
                return self._chunk_by_sentences(text, document_id, metadata)
            elif strategy == ChunkingStrategy.PARAGRAPH:
                return self._chunk_by_paragraphs(text, document_id, metadata)
            else:
                raise ValueError(f"Unsupported chunking strategy: {strategy}")
                
        except Exception as e:
            logger.error(f"Failed to chunk text: {str(e)}")
            raise
    
    async def health_check(self) -> bool:
        """Check if the text chunker is healthy."""
        try:
            # Basic health check - verify configuration is valid
            if self.chunk_size <= 0:
                return False
            
            if self.chunk_overlap < 0:
                return False
            
            if self.min_chunk_size <= 0:
                return False
            
            if not self.separators:
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return False
    
    def get_supported_strategies(self) -> List[ChunkingStrategy]:
        """Get list of supported chunking strategies."""
        return [
            ChunkingStrategy.FIXED_SIZE,
            ChunkingStrategy.SENTENCE,
            ChunkingStrategy.PARAGRAPH
        ]
    
    def get_chunker_info(self) -> Dict[str, Any]:
        """Get information about the text chunker."""
        return {
            "name": "text_chunker",
            "type": "document_chunker",
            "version": "1.0.0",
            "description": "Text document chunker for splitting documents into smaller pieces",
            "supported_strategies": [strategy.value for strategy in self.get_supported_strategies()],
            "chunk_size": self.chunk_size,
            "chunk_overlap": self.chunk_overlap,
            "min_chunk_size": self.min_chunk_size,
            "separators": self.separators
        }
    
    def _chunk_fixed_size(self, text: str, document_id: str, metadata: Dict[str, Any]) -> List[DocumentChunk]:
        """Chunk text by fixed size with overlap."""
        chunks = []
        start = 0
        
        while start < len(text):
            # Determine chunk end
            end = min(start + self.chunk_size, len(text))
            
            # If this isn't the last chunk, try to break at a separator
            if end < len(text):
                # Find the best break point
                best_break = end
                for separator in self.separators:
                    # Look for separator before the end
                    pos = text.rfind(separator, start, end)
                    if pos > start and pos > best_break - 100:  # Within 100 chars of end
                        best_break = pos + len(separator)
                        break
                
                end = best_break
            
            chunk_content = text[start:end].strip()
            
            # Skip chunks that are too small (unless it's the only chunk)
            if len(chunk_content) < self.min_chunk_size and len(chunks) > 0:
                # Merge with previous chunk if possible
                if chunks:
                    chunks[-1].content += " " + chunk_content
                    chunks[-1].end_index = end
                start = end
                continue
            
            # Create chunk
            chunk = DocumentChunk(
                content=chunk_content,
                chunk_id=self._generate_chunk_id(document_id),
                document_id=document_id,
                metadata={
                    **metadata,
                    "strategy": "fixed_size",
                    "chunk_index": len(chunks),
                    "start_index": start,
                    "end_index": end,
                    "chunk_size": len(chunk_content)
                },
                start_index=start,
                end_index=end
            )
            
            chunks.append(chunk)
            
            # Move start position with overlap
            if end < len(text):
                start = max(start + 1, end - self.chunk_overlap)
            else:
                break
        
        return chunks
    
    def _chunk_by_sentences(self, text: str, document_id: str, metadata: Dict[str, Any]) -> List[DocumentChunk]:
        """Chunk text by sentences."""
        # Split text into sentences
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        chunks = []
        current_chunk = ""
        start_index = 0
        
        for i, sentence in enumerate(sentences):
            sentence = sentence.strip()
            if not sentence:
                continue
            
            # Check if adding this sentence would exceed chunk size
            if len(current_chunk) + len(sentence) > self.chunk_size and current_chunk:
                # Create chunk from current content
                chunk = DocumentChunk(
                    content=current_chunk.strip(),
                    chunk_id=self._generate_chunk_id(document_id),
                    document_id=document_id,
                    metadata={
                        **metadata,
                        "strategy": "sentence",
                        "chunk_index": len(chunks),
                        "start_index": start_index,
                        "end_index": start_index + len(current_chunk),
                        "sentence_count": len(current_chunk.split('. '))
                    },
                    start_index=start_index,
                    end_index=start_index + len(current_chunk)
                )
                chunks.append(chunk)
                
                # Start new chunk
                current_chunk = sentence
                start_index = text.find(sentence, start_index)
            else:
                # Add sentence to current chunk
                if current_chunk:
                    current_chunk += " " + sentence
                else:
                    current_chunk = sentence
                    start_index = text.find(sentence, start_index)
        
        # Add final chunk
        if current_chunk:
            chunk = DocumentChunk(
                content=current_chunk.strip(),
                chunk_id=self._generate_chunk_id(document_id),
                document_id=document_id,
                metadata={
                    **metadata,
                    "strategy": "sentence",
                    "chunk_index": len(chunks),
                    "start_index": start_index,
                    "end_index": start_index + len(current_chunk),
                    "sentence_count": len(current_chunk.split('. '))
                },
                start_index=start_index,
                end_index=start_index + len(current_chunk)
            )
            chunks.append(chunk)
        
        return chunks
    
    def _chunk_by_paragraphs(self, text: str, document_id: str, metadata: Dict[str, Any]) -> List[DocumentChunk]:
        """Chunk text by paragraphs."""
        # Split text into paragraphs
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        
        chunks = []
        
        for i, paragraph in enumerate(paragraphs):
            # Find paragraph position in original text
            start_index = text.find(paragraph)
            end_index = start_index + len(paragraph)
            
            chunk = DocumentChunk(
                content=paragraph,
                chunk_id=self._generate_chunk_id(document_id),
                document_id=document_id,
                metadata={
                    **metadata,
                    "strategy": "paragraph",
                    "chunk_index": i,
                    "paragraph_index": i,
                    "start_index": start_index,
                    "end_index": end_index,
                    "paragraph_count": len(paragraphs)
                },
                start_index=start_index,
                end_index=end_index
            )
            chunks.append(chunk)
        
        return chunks
    
    def _generate_chunk_id(self, document_id: str) -> str:
        """Generate a unique chunk ID."""
        self._chunk_counter += 1
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        return f"chunk_{document_id}_{timestamp}_{unique_id}_{self._chunk_counter}" 