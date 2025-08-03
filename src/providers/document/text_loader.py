import os
import uuid
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List
from pathlib import Path

from src.interfaces.document_interface import DocumentLoaderInterface, DocumentType, Document

logger = logging.getLogger(__name__)


class TextDocumentLoader(DocumentLoaderInterface):
    """Text document loader for plain text files."""
    
    def __init__(self):
        """Initialize the text document loader."""
        self.encoding = "utf-8"
        self.max_file_size = 10485760  # 10MB default
        self.allowed_extensions = [".txt", ".md", ".csv"]
        self._document_counter = 0
    
    async def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize the text document loader with configuration."""
        self.encoding = config.get("encoding", "utf-8")
        self.max_file_size = config.get("max_file_size", 10485760)
        self.allowed_extensions = config.get("allowed_extensions", [".txt", ".md", ".csv"])
        
        logger.info(f"Text document loader initialized with encoding: {self.encoding}, max size: {self.max_file_size}")
    
    async def load_document(self, file_path: str, document_type: DocumentType) -> Document:
        """Load a document from file path."""
        try:
            # Validate file exists
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"File not found: {file_path}")
            
            # Validate file extension
            file_ext = Path(file_path).suffix.lower()
            if file_ext not in self.allowed_extensions:
                raise ValueError(f"Unsupported file extension: {file_ext}")
            
            # Check file size
            file_size = os.path.getsize(file_path)
            if file_size > self.max_file_size:
                raise ValueError(f"File size ({file_size}) exceeds maximum allowed ({self.max_file_size})")
            
            # Read file content
            with open(file_path, 'r', encoding=self.encoding) as f:
                content = f.read()
            
            # Generate document ID
            document_id = self._generate_document_id()
            
            # Extract metadata
            metadata = self._extract_metadata(file_path, file_size, document_type)
            
            # Create document
            document = Document(
                document_id=document_id,
                content=content,
                document_type=document_type,
                metadata=metadata
            )
            
            logger.info(f"Successfully loaded document {document_id} from {file_path}")
            return document
            
        except Exception as e:
            logger.error(f"Failed to load document from {file_path}: {str(e)}")
            raise
    
    async def load_document_from_bytes(self, content: bytes, document_type: DocumentType, filename: str) -> Document:
        """Load a document from bytes content."""
        try:
            # Decode content
            text_content = content.decode(self.encoding)
            
            # Generate document ID
            document_id = self._generate_document_id()
            
            # Extract metadata
            metadata = {
                "filename": filename,
                "encoding": self.encoding,
                "content_size": len(content),
                "created_at": datetime.now(timezone.utc).isoformat(),
                "document_type": document_type.value,
                "source": "bytes"
            }
            
            # Create document
            document = Document(
                document_id=document_id,
                content=text_content,
                document_type=document_type,
                metadata=metadata
            )
            
            logger.info(f"Successfully loaded document {document_id} from bytes")
            return document
            
        except Exception as e:
            logger.error(f"Failed to load document from bytes: {str(e)}")
            raise
    
    async def health_check(self) -> bool:
        """Check if the text document loader is healthy."""
        try:
            # Basic health check - verify configuration is valid
            if not self.allowed_extensions:
                return False
            
            if self.max_file_size <= 0:
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return False
    
    def get_supported_types(self) -> List[DocumentType]:
        """Get list of supported document types."""
        supported_types = []
        
        if ".txt" in self.allowed_extensions:
            supported_types.append(DocumentType.TXT)
        
        if ".md" in self.allowed_extensions:
            supported_types.append(DocumentType.MD)
        
        if ".csv" in self.allowed_extensions:
            supported_types.append(DocumentType.CSV)
        
        return supported_types
    
    def get_loader_info(self) -> Dict[str, Any]:
        """Get information about the text document loader."""
        return {
            "name": "text_loader",
            "type": "document_loader",
            "version": "1.0.0",
            "description": "Text document loader for plain text files",
            "supported_types": [dt.value for dt in self.get_supported_types()],
            "encoding": self.encoding,
            "max_file_size": self.max_file_size,
            "allowed_extensions": self.allowed_extensions
        }
    
    def _generate_document_id(self) -> str:
        """Generate a unique document ID."""
        self._document_counter += 1
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        return f"doc_{timestamp}_{unique_id}_{self._document_counter}"
    
    def _extract_metadata(self, file_path: str, file_size: int, document_type: DocumentType) -> Dict[str, Any]:
        """Extract metadata from file."""
        return {
            "source": file_path,
            "file_size": file_size,
            "encoding": self.encoding,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "document_type": document_type.value,
            "filename": Path(file_path).name,
            "file_extension": Path(file_path).suffix.lower()
        } 