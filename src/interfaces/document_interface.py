from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, BinaryIO
from enum import Enum
import asyncio


class DocumentType(Enum):
    """Supported document types."""
    PDF = "pdf"
    DOCX = "docx"
    TXT = "txt"
    HTML = "html"
    MD = "markdown"
    JSON = "json"
    CSV = "csv"


class ChunkingStrategy(Enum):
    """Available chunking strategies."""
    FIXED_SIZE = "fixed_size"
    SEMANTIC = "semantic"
    SENTENCE = "sentence"
    PARAGRAPH = "paragraph"
    RECURSIVE = "recursive"


class DocumentChunk:
    """Represents a chunk of a document."""
    
    def __init__(self, 
                 content: str,
                 chunk_id: str,
                 document_id: str,
                 metadata: Dict[str, Any],
                 start_index: int = 0,
                 end_index: int = 0):
        self.content = content
        self.chunk_id = chunk_id
        self.document_id = document_id
        self.metadata = metadata
        self.start_index = start_index
        self.end_index = end_index
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert chunk to dictionary representation."""
        return {
            "content": self.content,
            "chunk_id": self.chunk_id,
            "document_id": self.document_id,
            "metadata": self.metadata,
            "start_index": self.start_index,
            "end_index": self.end_index
        }


class Document:
    """Represents a processed document."""
    
    def __init__(self,
                 document_id: str,
                 content: str,
                 document_type: DocumentType,
                 metadata: Dict[str, Any],
                 chunks: Optional[List[DocumentChunk]] = None):
        self.document_id = document_id
        self.content = content
        self.document_type = document_type
        self.metadata = metadata
        self.chunks = chunks or []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert document to dictionary representation."""
        return {
            "document_id": self.document_id,
            "content": self.content,
            "document_type": self.document_type.value,
            "metadata": self.metadata,
            "chunks": [chunk.to_dict() for chunk in self.chunks]
        }


class DocumentLoaderInterface(ABC):
    """Interface for document loaders."""
    
    @abstractmethod
    async def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize the document loader with configuration."""
        pass
    
    @abstractmethod
    async def load_document(self, file_path: str, document_type: DocumentType) -> Document:
        """Load a document from file path."""
        pass
    
    @abstractmethod
    async def load_document_from_bytes(self, content: bytes, document_type: DocumentType, filename: str) -> Document:
        """Load a document from bytes content."""
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """Check if the document loader is healthy."""
        pass
    
    @abstractmethod
    def get_supported_types(self) -> List[DocumentType]:
        """Get list of supported document types."""
        pass
    
    @abstractmethod
    def get_loader_info(self) -> Dict[str, Any]:
        """Get information about the document loader."""
        pass


class DocumentChunkerInterface(ABC):
    """Interface for document chunkers."""
    
    @abstractmethod
    async def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize the document chunker with configuration."""
        pass
    
    @abstractmethod
    async def chunk_document(self, document: Document, strategy: ChunkingStrategy) -> List[DocumentChunk]:
        """Chunk a document using the specified strategy."""
        pass
    
    @abstractmethod
    async def chunk_text(self, text: str, strategy: ChunkingStrategy, metadata: Dict[str, Any]) -> List[DocumentChunk]:
        """Chunk text content using the specified strategy."""
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """Check if the document chunker is healthy."""
        pass
    
    @abstractmethod
    def get_supported_strategies(self) -> List[ChunkingStrategy]:
        """Get list of supported chunking strategies."""
        pass
    
    @abstractmethod
    def get_chunker_info(self) -> Dict[str, Any]:
        """Get information about the document chunker."""
        pass


class DocumentProcessorInterface(ABC):
    """Interface for document processors."""
    
    @abstractmethod
    async def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize the document processor with configuration."""
        pass
    
    @abstractmethod
    async def process_document(self, document: Document) -> Document:
        """Process a document (extract metadata, clean content, etc.)."""
        pass
    
    @abstractmethod
    async def extract_metadata(self, document: Document) -> Dict[str, Any]:
        """Extract metadata from a document."""
        pass
    
    @abstractmethod
    async def clean_content(self, content: str) -> str:
        """Clean and normalize document content."""
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """Check if the document processor is healthy."""
        pass
    
    @abstractmethod
    def get_processor_info(self) -> Dict[str, Any]:
        """Get information about the document processor."""
        pass


class DocumentPipelineInterface(ABC):
    """Interface for document processing pipeline."""
    
    @abstractmethod
    async def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize the document pipeline with configuration."""
        pass
    
    @abstractmethod
    async def process_file(self, file_path: str, chunking_strategy: ChunkingStrategy) -> Document:
        """Process a file through the complete pipeline."""
        pass
    
    @abstractmethod
    async def process_bytes(self, content: bytes, document_type: DocumentType, filename: str, chunking_strategy: ChunkingStrategy) -> Document:
        """Process bytes content through the complete pipeline."""
        pass
    
    @abstractmethod
    async def batch_process(self, file_paths: List[str], chunking_strategy: ChunkingStrategy) -> List[Document]:
        """Process multiple files in batch."""
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """Check if the document pipeline is healthy."""
        pass
    
    @abstractmethod
    def get_pipeline_info(self) -> Dict[str, Any]:
        """Get information about the document pipeline."""
        pass 