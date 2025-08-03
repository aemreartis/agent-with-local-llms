import pytest
from unittest.mock import MagicMock, AsyncMock
from typing import Dict, Any, List

from src.interfaces.document_interface import (
    DocumentType, ChunkingStrategy, Document, DocumentChunk,
    DocumentLoaderInterface, DocumentChunkerInterface, 
    DocumentProcessorInterface, DocumentPipelineInterface
)


class TestDocumentTypes:
    """Test document type enums."""
    
    def test_document_type_values(self):
        """Test that document types have correct values."""
        assert DocumentType.PDF.value == "pdf"
        assert DocumentType.DOCX.value == "docx"
        assert DocumentType.TXT.value == "txt"
        assert DocumentType.HTML.value == "html"
        assert DocumentType.MD.value == "markdown"
        assert DocumentType.JSON.value == "json"
        assert DocumentType.CSV.value == "csv"
    
    def test_document_type_from_value(self):
        """Test creating document type from value."""
        assert DocumentType("pdf") == DocumentType.PDF
        assert DocumentType("docx") == DocumentType.DOCX
        assert DocumentType("txt") == DocumentType.TXT


class TestChunkingStrategies:
    """Test chunking strategy enums."""
    
    def test_chunking_strategy_values(self):
        """Test that chunking strategies have correct values."""
        assert ChunkingStrategy.FIXED_SIZE.value == "fixed_size"
        assert ChunkingStrategy.SEMANTIC.value == "semantic"
        assert ChunkingStrategy.SENTENCE.value == "sentence"
        assert ChunkingStrategy.PARAGRAPH.value == "paragraph"
        assert ChunkingStrategy.RECURSIVE.value == "recursive"
    
    def test_chunking_strategy_from_value(self):
        """Test creating chunking strategy from value."""
        assert ChunkingStrategy("fixed_size") == ChunkingStrategy.FIXED_SIZE
        assert ChunkingStrategy("semantic") == ChunkingStrategy.SEMANTIC
        assert ChunkingStrategy("sentence") == ChunkingStrategy.SENTENCE


class TestDocumentChunk:
    """Test DocumentChunk class."""
    
    def test_document_chunk_creation(self):
        """Test creating a document chunk."""
        chunk = DocumentChunk(
            content="This is a test chunk",
            chunk_id="chunk_1",
            document_id="doc_1",
            metadata={"page": 1, "section": "intro"},
            start_index=0,
            end_index=20
        )
        
        assert chunk.content == "This is a test chunk"
        assert chunk.chunk_id == "chunk_1"
        assert chunk.document_id == "doc_1"
        assert chunk.metadata["page"] == 1
        assert chunk.start_index == 0
        assert chunk.end_index == 20
    
    def test_document_chunk_to_dict(self):
        """Test converting chunk to dictionary."""
        chunk = DocumentChunk(
            content="Test content",
            chunk_id="chunk_1",
            document_id="doc_1",
            metadata={"page": 1},
            start_index=0,
            end_index=12
        )
        
        chunk_dict = chunk.to_dict()
        
        assert chunk_dict["content"] == "Test content"
        assert chunk_dict["chunk_id"] == "chunk_1"
        assert chunk_dict["document_id"] == "doc_1"
        assert chunk_dict["metadata"]["page"] == 1
        assert chunk_dict["start_index"] == 0
        assert chunk_dict["end_index"] == 12


class TestDocument:
    """Test Document class."""
    
    def test_document_creation(self):
        """Test creating a document."""
        document = Document(
            document_id="doc_1",
            content="This is a test document",
            document_type=DocumentType.TXT,
            metadata={"title": "Test Document", "author": "Test Author"}
        )
        
        assert document.document_id == "doc_1"
        assert document.content == "This is a test document"
        assert document.document_type == DocumentType.TXT
        assert document.metadata["title"] == "Test Document"
        assert document.chunks == []
    
    def test_document_with_chunks(self):
        """Test creating a document with chunks."""
        chunk = DocumentChunk(
            content="Chunk 1",
            chunk_id="chunk_1",
            document_id="doc_1",
            metadata={}
        )
        
        document = Document(
            document_id="doc_1",
            content="This is a test document",
            document_type=DocumentType.TXT,
            metadata={"title": "Test Document"},
            chunks=[chunk]
        )
        
        assert len(document.chunks) == 1
        assert document.chunks[0].content == "Chunk 1"
    
    def test_document_to_dict(self):
        """Test converting document to dictionary."""
        chunk = DocumentChunk(
            content="Chunk 1",
            chunk_id="chunk_1",
            document_id="doc_1",
            metadata={"page": 1}
        )
        
        document = Document(
            document_id="doc_1",
            content="Test document",
            document_type=DocumentType.PDF,
            metadata={"title": "Test"},
            chunks=[chunk]
        )
        
        doc_dict = document.to_dict()
        
        assert doc_dict["document_id"] == "doc_1"
        assert doc_dict["content"] == "Test document"
        assert doc_dict["document_type"] == "pdf"
        assert doc_dict["metadata"]["title"] == "Test"
        assert len(doc_dict["chunks"]) == 1
        assert doc_dict["chunks"][0]["content"] == "Chunk 1"


class TestDocumentLoaderInterface:
    """Test DocumentLoaderInterface contract."""
    
    def test_loader_interface_methods_exist(self):
        """Test that loader interface has required methods."""
        # Create a mock implementation
        class MockLoader(DocumentLoaderInterface):
            async def initialize(self, config: Dict[str, Any]) -> None:
                pass
            
            async def load_document(self, file_path: str, document_type: DocumentType) -> Document:
                pass
            
            async def load_document_from_bytes(self, content: bytes, document_type: DocumentType, filename: str) -> Document:
                pass
            
            async def health_check(self) -> bool:
                return True
            
            def get_supported_types(self) -> List[DocumentType]:
                return [DocumentType.TXT, DocumentType.PDF]
            
            def get_loader_info(self) -> Dict[str, Any]:
                return {"name": "mock_loader"}
        
        loader = MockLoader()
        
        # Test that all required methods exist
        assert hasattr(loader, 'initialize')
        assert hasattr(loader, 'load_document')
        assert hasattr(loader, 'load_document_from_bytes')
        assert hasattr(loader, 'health_check')
        assert hasattr(loader, 'get_supported_types')
        assert hasattr(loader, 'get_loader_info')
    
    @pytest.mark.asyncio
    async def test_loader_interface_contract(self):
        """Test loader interface contract compliance."""
        class MockLoader(DocumentLoaderInterface):
            async def initialize(self, config: Dict[str, Any]) -> None:
                self.config = config
            
            async def load_document(self, file_path: str, document_type: DocumentType) -> Document:
                return Document(
                    document_id="test_doc",
                    content="Test content",
                    document_type=document_type,
                    metadata={"source": file_path}
                )
            
            async def load_document_from_bytes(self, content: bytes, document_type: DocumentType, filename: str) -> Document:
                return Document(
                    document_id="test_doc",
                    content=content.decode('utf-8'),
                    document_type=document_type,
                    metadata={"filename": filename}
                )
            
            async def health_check(self) -> bool:
                return True
            
            def get_supported_types(self) -> List[DocumentType]:
                return [DocumentType.TXT, DocumentType.PDF]
            
            def get_loader_info(self) -> Dict[str, Any]:
                return {"name": "mock_loader", "version": "1.0.0"}
        
        loader = MockLoader()
        
        # Test initialization
        await loader.initialize({"test": "config"})
        assert loader.config["test"] == "config"
        
        # Test loading document
        doc = await loader.load_document("test.txt", DocumentType.TXT)
        assert doc.document_id == "test_doc"
        assert doc.content == "Test content"
        assert doc.document_type == DocumentType.TXT
        
        # Test loading from bytes
        doc = await loader.load_document_from_bytes(b"Test bytes", DocumentType.PDF, "test.pdf")
        assert doc.content == "Test bytes"
        assert doc.document_type == DocumentType.PDF
        
        # Test health check
        assert await loader.health_check() is True
        
        # Test supported types
        types = loader.get_supported_types()
        assert DocumentType.TXT in types
        assert DocumentType.PDF in types
        
        # Test loader info
        info = loader.get_loader_info()
        assert info["name"] == "mock_loader"
        assert info["version"] == "1.0.0"


class TestDocumentChunkerInterface:
    """Test DocumentChunkerInterface contract."""
    
    def test_chunker_interface_methods_exist(self):
        """Test that chunker interface has required methods."""
        class MockChunker(DocumentChunkerInterface):
            async def initialize(self, config: Dict[str, Any]) -> None:
                pass
            
            async def chunk_document(self, document: Document, strategy: ChunkingStrategy) -> List[DocumentChunk]:
                pass
            
            async def chunk_text(self, text: str, strategy: ChunkingStrategy, metadata: Dict[str, Any]) -> List[DocumentChunk]:
                pass
            
            async def health_check(self) -> bool:
                return True
            
            def get_supported_strategies(self) -> List[ChunkingStrategy]:
                return [ChunkingStrategy.FIXED_SIZE]
            
            def get_chunker_info(self) -> Dict[str, Any]:
                return {"name": "mock_chunker"}
        
        chunker = MockChunker()
        
        # Test that all required methods exist
        assert hasattr(chunker, 'initialize')
        assert hasattr(chunker, 'chunk_document')
        assert hasattr(chunker, 'chunk_text')
        assert hasattr(chunker, 'health_check')
        assert hasattr(chunker, 'get_supported_strategies')
        assert hasattr(chunker, 'get_chunker_info')
    
    @pytest.mark.asyncio
    async def test_chunker_interface_contract(self):
        """Test chunker interface contract compliance."""
        class MockChunker(DocumentChunkerInterface):
            async def initialize(self, config: Dict[str, Any]) -> None:
                self.config = config
            
            async def chunk_document(self, document: Document, strategy: ChunkingStrategy) -> List[DocumentChunk]:
                chunk = DocumentChunk(
                    content=document.content,
                    chunk_id=f"{document.document_id}_chunk_1",
                    document_id=document.document_id,
                    metadata=document.metadata
                )
                return [chunk]
            
            async def chunk_text(self, text: str, strategy: ChunkingStrategy, metadata: Dict[str, Any]) -> List[DocumentChunk]:
                chunk = DocumentChunk(
                    content=text,
                    chunk_id="text_chunk_1",
                    document_id=metadata.get("document_id", "unknown"),
                    metadata=metadata
                )
                return [chunk]
            
            async def health_check(self) -> bool:
                return True
            
            def get_supported_strategies(self) -> List[ChunkingStrategy]:
                return [ChunkingStrategy.FIXED_SIZE, ChunkingStrategy.SENTENCE]
            
            def get_chunker_info(self) -> Dict[str, Any]:
                return {"name": "mock_chunker", "version": "1.0.0"}
        
        chunker = MockChunker()
        
        # Test initialization
        await chunker.initialize({"chunk_size": 1000})
        assert chunker.config["chunk_size"] == 1000
        
        # Test chunking document
        doc = Document(
            document_id="test_doc",
            content="Test document content",
            document_type=DocumentType.TXT,
            metadata={"title": "Test"}
        )
        
        chunks = await chunker.chunk_document(doc, ChunkingStrategy.FIXED_SIZE)
        assert len(chunks) == 1
        assert chunks[0].content == "Test document content"
        assert chunks[0].document_id == "test_doc"
        
        # Test chunking text
        chunks = await chunker.chunk_text("Test text", ChunkingStrategy.SENTENCE, {"document_id": "test"})
        assert len(chunks) == 1
        assert chunks[0].content == "Test text"
        
        # Test health check
        assert await chunker.health_check() is True
        
        # Test supported strategies
        strategies = chunker.get_supported_strategies()
        assert ChunkingStrategy.FIXED_SIZE in strategies
        assert ChunkingStrategy.SENTENCE in strategies
        
        # Test chunker info
        info = chunker.get_chunker_info()
        assert info["name"] == "mock_chunker"
        assert info["version"] == "1.0.0"


class TestDocumentProcessorInterface:
    """Test DocumentProcessorInterface contract."""
    
    def test_processor_interface_methods_exist(self):
        """Test that processor interface has required methods."""
        class MockProcessor(DocumentProcessorInterface):
            async def initialize(self, config: Dict[str, Any]) -> None:
                pass
            
            async def process_document(self, document: Document) -> Document:
                pass
            
            async def extract_metadata(self, document: Document) -> Dict[str, Any]:
                pass
            
            async def clean_content(self, content: str) -> str:
                pass
            
            async def health_check(self) -> bool:
                return True
            
            def get_processor_info(self) -> Dict[str, Any]:
                return {"name": "mock_processor"}
        
        processor = MockProcessor()
        
        # Test that all required methods exist
        assert hasattr(processor, 'initialize')
        assert hasattr(processor, 'process_document')
        assert hasattr(processor, 'extract_metadata')
        assert hasattr(processor, 'clean_content')
        assert hasattr(processor, 'health_check')
        assert hasattr(processor, 'get_processor_info')
    
    @pytest.mark.asyncio
    async def test_processor_interface_contract(self):
        """Test processor interface contract compliance."""
        class MockProcessor(DocumentProcessorInterface):
            async def initialize(self, config: Dict[str, Any]) -> None:
                self.config = config
            
            async def process_document(self, document: Document) -> Document:
                # Add processing metadata
                document.metadata["processed"] = True
                document.metadata["processor"] = "mock_processor"
                return document
            
            async def extract_metadata(self, document: Document) -> Dict[str, Any]:
                return {
                    "word_count": len(document.content.split()),
                    "char_count": len(document.content),
                    "document_type": document.document_type.value
                }
            
            async def clean_content(self, content: str) -> str:
                return content.strip().replace('\n', ' ')
            
            async def health_check(self) -> bool:
                return True
            
            def get_processor_info(self) -> Dict[str, Any]:
                return {"name": "mock_processor", "version": "1.0.0"}
        
        processor = MockProcessor()
        
        # Test initialization
        await processor.initialize({"clean_html": True})
        assert processor.config["clean_html"] is True
        
        # Test processing document
        doc = Document(
            document_id="test_doc",
            content="Test document",
            document_type=DocumentType.TXT,
            metadata={"title": "Test"}
        )
        
        processed_doc = await processor.process_document(doc)
        assert processed_doc.metadata["processed"] is True
        assert processed_doc.metadata["processor"] == "mock_processor"
        
        # Test extracting metadata
        metadata = await processor.extract_metadata(doc)
        assert metadata["word_count"] == 2
        assert metadata["char_count"] == 13
        assert metadata["document_type"] == "txt"
        
        # Test cleaning content
        cleaned = await processor.clean_content("  Test\ncontent  ")
        assert cleaned == "Test content"
        
        # Test health check
        assert await processor.health_check() is True
        
        # Test processor info
        info = processor.get_processor_info()
        assert info["name"] == "mock_processor"
        assert info["version"] == "1.0.0"


class TestDocumentPipelineInterface:
    """Test DocumentPipelineInterface contract."""
    
    def test_pipeline_interface_methods_exist(self):
        """Test that pipeline interface has required methods."""
        class MockPipeline(DocumentPipelineInterface):
            async def initialize(self, config: Dict[str, Any]) -> None:
                pass
            
            async def process_file(self, file_path: str, chunking_strategy: ChunkingStrategy) -> Document:
                pass
            
            async def process_bytes(self, content: bytes, document_type: DocumentType, filename: str, chunking_strategy: ChunkingStrategy) -> Document:
                pass
            
            async def batch_process(self, file_paths: List[str], chunking_strategy: ChunkingStrategy) -> List[Document]:
                pass
            
            async def health_check(self) -> bool:
                return True
            
            def get_pipeline_info(self) -> Dict[str, Any]:
                return {"name": "mock_pipeline"}
        
        pipeline = MockPipeline()
        
        # Test that all required methods exist
        assert hasattr(pipeline, 'initialize')
        assert hasattr(pipeline, 'process_file')
        assert hasattr(pipeline, 'process_bytes')
        assert hasattr(pipeline, 'batch_process')
        assert hasattr(pipeline, 'health_check')
        assert hasattr(pipeline, 'get_pipeline_info')
    
    @pytest.mark.asyncio
    async def test_pipeline_interface_contract(self):
        """Test pipeline interface contract compliance."""
        class MockPipeline(DocumentPipelineInterface):
            async def initialize(self, config: Dict[str, Any]) -> None:
                self.config = config
            
            async def process_file(self, file_path: str, chunking_strategy: ChunkingStrategy) -> Document:
                return Document(
                    document_id="processed_doc",
                    content="Processed content",
                    document_type=DocumentType.TXT,
                    metadata={"source": file_path, "strategy": chunking_strategy.value}
                )
            
            async def process_bytes(self, content: bytes, document_type: DocumentType, filename: str, chunking_strategy: ChunkingStrategy) -> Document:
                return Document(
                    document_id="processed_bytes_doc",
                    content=content.decode('utf-8'),
                    document_type=document_type,
                    metadata={"filename": filename, "strategy": chunking_strategy.value}
                )
            
            async def batch_process(self, file_paths: List[str], chunking_strategy: ChunkingStrategy) -> List[Document]:
                documents = []
                for i, file_path in enumerate(file_paths):
                    doc = Document(
                        document_id=f"batch_doc_{i}",
                        content=f"Content from {file_path}",
                        document_type=DocumentType.TXT,
                        metadata={"source": file_path, "strategy": chunking_strategy.value}
                    )
                    documents.append(doc)
                return documents
            
            async def health_check(self) -> bool:
                return True
            
            def get_pipeline_info(self) -> Dict[str, Any]:
                return {"name": "mock_pipeline", "version": "1.0.0"}
        
        pipeline = MockPipeline()
        
        # Test initialization
        await pipeline.initialize({"batch_size": 10})
        assert pipeline.config["batch_size"] == 10
        
        # Test processing file
        doc = await pipeline.process_file("test.txt", ChunkingStrategy.FIXED_SIZE)
        assert doc.document_id == "processed_doc"
        assert doc.content == "Processed content"
        assert doc.metadata["source"] == "test.txt"
        assert doc.metadata["strategy"] == "fixed_size"
        
        # Test processing bytes
        doc = await pipeline.process_bytes(b"Test bytes", DocumentType.PDF, "test.pdf", ChunkingStrategy.SENTENCE)
        assert doc.document_id == "processed_bytes_doc"
        assert doc.content == "Test bytes"
        assert doc.document_type == DocumentType.PDF
        assert doc.metadata["filename"] == "test.pdf"
        assert doc.metadata["strategy"] == "sentence"
        
        # Test batch processing
        docs = await pipeline.batch_process(["file1.txt", "file2.txt"], ChunkingStrategy.PARAGRAPH)
        assert len(docs) == 2
        assert docs[0].document_id == "batch_doc_0"
        assert docs[1].document_id == "batch_doc_1"
        assert docs[0].metadata["source"] == "file1.txt"
        assert docs[1].metadata["source"] == "file2.txt"
        
        # Test health check
        assert await pipeline.health_check() is True
        
        # Test pipeline info
        info = pipeline.get_pipeline_info()
        assert info["name"] == "mock_pipeline"
        assert info["version"] == "1.0.0" 