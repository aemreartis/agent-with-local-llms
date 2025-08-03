import logging
from typing import Dict, Any, List

from src.interfaces.document_interface import DocumentPipelineInterface, DocumentType, ChunkingStrategy, Document
from src.providers.document.text_loader import TextDocumentLoader
from src.providers.document.text_processor import TextProcessor
from src.providers.document.text_chunker import TextChunker

logger = logging.getLogger(__name__)


class DocumentPipeline(DocumentPipelineInterface):
    """Document processing pipeline that orchestrates loader, processor, and chunker."""
    
    def __init__(self):
        """Initialize the document pipeline."""
        self.loader = None
        self.processor = None
        self.chunker = None
        self.config = None
    
    async def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize the document pipeline with configuration."""
        try:
            self.config = config
            
            # Initialize loader
            loader_config = config.get("loader", {})
            loader_type = loader_config.get("type", "text")
            
            if loader_type == "text":
                self.loader = TextDocumentLoader()
                await self.loader.initialize(loader_config.get("config", {}))
            else:
                raise ValueError(f"Unsupported loader type: {loader_type}")
            
            # Initialize processor
            processor_config = config.get("processor", {})
            processor_type = processor_config.get("type", "text")
            
            if processor_type == "text":
                self.processor = TextProcessor()
                await self.processor.initialize(processor_config.get("config", {}))
            else:
                raise ValueError(f"Unsupported processor type: {processor_type}")
            
            # Initialize chunker
            chunker_config = config.get("chunker", {})
            chunker_type = chunker_config.get("type", "text")
            
            if chunker_type == "text":
                self.chunker = TextChunker()
                await self.chunker.initialize(chunker_config.get("config", {}))
            else:
                raise ValueError(f"Unsupported chunker type: {chunker_type}")
            
            logger.info("Document pipeline initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize document pipeline: {str(e)}")
            raise
    
    async def process_file(self, file_path: str, chunking_strategy: ChunkingStrategy) -> Document:
        """Process a file through the complete pipeline."""
        try:
            # Step 1: Load document
            document_type = self._detect_document_type(file_path)
            document = await self.loader.load_document(file_path, document_type)
            
            # Step 2: Process document
            document = await self.processor.process_document(document)
            
            # Step 3: Chunk document
            await self.chunker.chunk_document(document, chunking_strategy)
            
            logger.info(f"Successfully processed file {file_path} through pipeline")
            return document
            
        except Exception as e:
            logger.error(f"Failed to process file {file_path}: {str(e)}")
            raise
    
    async def process_bytes(self, content: bytes, document_type: DocumentType, filename: str, chunking_strategy: ChunkingStrategy) -> Document:
        """Process bytes content through the complete pipeline."""
        try:
            # Step 1: Load document from bytes
            document = await self.loader.load_document_from_bytes(content, document_type, filename)
            
            # Step 2: Process document
            document = await self.processor.process_document(document)
            
            # Step 3: Chunk document
            await self.chunker.chunk_document(document, chunking_strategy)
            
            logger.info(f"Successfully processed bytes content through pipeline")
            return document
            
        except Exception as e:
            logger.error(f"Failed to process bytes content: {str(e)}")
            raise
    
    async def batch_process(self, file_paths: List[str], chunking_strategy: ChunkingStrategy) -> List[Document]:
        """Process multiple files in batch."""
        try:
            documents = []
            
            for file_path in file_paths:
                try:
                    document = await self.process_file(file_path, chunking_strategy)
                    documents.append(document)
                except Exception as e:
                    logger.error(f"Failed to process file {file_path} in batch: {str(e)}")
                    # Continue with other files instead of failing the entire batch
                    continue
            
            logger.info(f"Successfully processed {len(documents)} out of {len(file_paths)} files in batch")
            return documents
            
        except Exception as e:
            logger.error(f"Failed to process batch: {str(e)}")
            raise
    
    async def health_check(self) -> bool:
        """Check if the document pipeline is healthy."""
        try:
            # Check if components are initialized
            if not self.loader or not self.processor or not self.chunker:
                return False
            
            # Check component health
            loader_healthy = await self.loader.health_check()
            processor_healthy = await self.processor.health_check()
            chunker_healthy = await self.chunker.health_check()
            
            return loader_healthy and processor_healthy and chunker_healthy
            
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return False
    
    def get_pipeline_info(self) -> Dict[str, Any]:
        """Get information about the document pipeline."""
        return {
            "name": "document_pipeline",
            "type": "document_pipeline",
            "version": "1.0.0",
            "description": "Document processing pipeline that orchestrates loader, processor, and chunker",
            "components": {
                "loader": self.loader.get_loader_info() if self.loader else None,
                "processor": self.processor.get_processor_info() if self.processor else None,
                "chunker": self.chunker.get_chunker_info() if self.chunker else None
            },
            "config": self.config
        }
    
    def _detect_document_type(self, file_path: str) -> DocumentType:
        """Detect document type from file extension."""
        import os
        
        _, ext = os.path.splitext(file_path.lower())
        
        if ext == ".txt":
            return DocumentType.TXT
        elif ext == ".md":
            return DocumentType.MD
        elif ext == ".csv":
            return DocumentType.CSV
        elif ext == ".html" or ext == ".htm":
            return DocumentType.HTML
        elif ext == ".json":
            return DocumentType.JSON
        elif ext == ".pdf":
            return DocumentType.PDF
        elif ext == ".docx":
            return DocumentType.DOCX
        else:
            # Default to text for unknown extensions
            return DocumentType.TXT 