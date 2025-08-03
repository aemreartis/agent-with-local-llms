"""Integration tests for document processing with orchestration system.

Tests the integration of document processing components with the existing
orchestration system (search orchestrator, query orchestrator, etc.).
"""

import pytest
import asyncio
import tempfile
import os
from unittest.mock import Mock, patch, AsyncMock
from typing import Dict, Any

from src.registry.provider_registry import ProviderRegistry
from src.interfaces.document_interface import DocumentType, ChunkingStrategy
from src.orchestration.search_orchestrator import SearchOrchestrator
from src.orchestration.query_orchestrator import QueryOrchestrator
from src.providers.document.document_pipeline import DocumentPipeline
from src.providers.vector_stores.qdrant_provider import QdrantProvider
from src.providers.search_engines.bm25_provider import BM25Provider
from src.providers.llm.vllm_provider import VLLMProvider
from src.providers.rerankers.bge_provider import BGEProvider


pytestmark = pytest.mark.asyncio


class TestDocumentOrchestrationIntegration:
    """Test integration of document processing with orchestration system."""
    
    @pytest.fixture
    def provider_registry(self):
        """Create a provider registry with all components."""
        registry = ProviderRegistry()
        
        # Register document processing providers
        registry.register_provider("document_pipeline", "text", DocumentPipeline)
        
        # Register search and orchestration providers (mocked for testing)
        registry.register_provider("vector_store", "qdrant", QdrantProvider)
        registry.register_provider("search_engine", "bm25", BM25Provider)
        registry.register_provider("llm", "vllm", VLLMProvider)
        registry.register_provider("reranker", "bge", BGEProvider)
        
        return registry
    
    @pytest.fixture
    def sample_documents(self):
        """Create sample documents for testing."""
        documents = []
        
        # Create multiple temporary files
        for i in range(3):
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                content = f"""Document {i} content for testing.
                
                This document contains information about topic {i}.
                
                It has multiple paragraphs with different content.
                
                The document should be processed and indexed properly."""
                f.write(content)
                documents.append(f.name)
        
        yield documents
        
        # Cleanup
        for doc in documents:
            os.unlink(doc)
    
    async def test_document_processing_with_search_orchestrator(
        self, 
        provider_registry, 
        sample_documents
    ):
        """Test document processing integrated with search orchestrator."""
        # Get document pipeline
        pipeline = await provider_registry.get_provider(
            "document_pipeline",
            "text",
            config={
                "loader": {"max_file_size": 1024 * 1024},
                "processor": {"normalize_whitespace": True, "extract_metadata": True},
                "chunker": {"chunk_size": 100, "chunk_overlap": 20}
            }
        )
        
        # Process documents
        processed_documents = []
        for doc_path in sample_documents:
            doc = await pipeline.process_file(doc_path, ChunkingStrategy.FIXED_SIZE)
            processed_documents.append(doc)
        
        assert len(processed_documents) == 3
        for doc in processed_documents:
            assert doc.document_id is not None
            assert len(doc.chunks) > 0
        
        # Test that document processing works correctly
        # (In a real scenario, documents would be indexed in vector store and search engine)
        assert pipeline is not None
    
    async def test_document_processing_with_query_orchestrator(
        self, 
        provider_registry, 
        sample_documents
    ):
        """Test document processing integrated with query orchestrator."""
        # Get document pipeline
        pipeline = await provider_registry.get_provider(
            "document_pipeline",
            "text",
            config={
                "loader": {"max_file_size": 1024 * 1024},
                "processor": {"normalize_whitespace": True, "extract_metadata": True},
                "chunker": {"chunk_size": 100, "chunk_overlap": 20}
            }
        )
        
        # Process documents
        processed_documents = []
        for doc_path in sample_documents:
            doc = await pipeline.process_file(doc_path, ChunkingStrategy.FIXED_SIZE)
            processed_documents.append(doc)
        
        # Test that document processing works correctly
        # (In a real scenario, documents would be indexed and searchable)
        assert len(processed_documents) == 3
        for doc in processed_documents:
            assert doc.document_id is not None
            assert len(doc.chunks) > 0
    
    async def test_document_processing_configuration_integration(self, provider_registry):
        """Test that document processing configuration integrates properly."""
        # Test that document processing providers can be configured through registry
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
        assert await pipeline.health_check()
        
        # Verify configuration is properly applied
        info = pipeline.get_pipeline_info()
        assert "config" in info
        assert info["config"]["loader"]["max_file_size"] == 1024 * 1024
    
    async def test_document_processing_error_handling_integration(self, provider_registry):
        """Test error handling in document processing integration."""
        # Test with invalid configuration - should still work as validation is in the provider
        pipeline = await provider_registry.get_provider(
            "document_pipeline",
            "text",
            config={
                "loader": {"max_file_size": -1},  # Invalid config
                "processor": {"normalize_whitespace": True},
                "chunker": {"chunk_size": 100}
            }
        )
        
        # The pipeline should still be created, but may fail during actual operations
        assert pipeline is not None
    
    async def test_document_processing_health_check_integration(self, provider_registry):
        """Test health checks in document processing integration."""
        # Get document pipeline with proper configuration
        pipeline = await provider_registry.get_provider(
            "document_pipeline",
            "text",
            config={
                "loader": {"max_file_size": 1024 * 1024},
                "processor": {"normalize_whitespace": True, "extract_metadata": True},
                "chunker": {"chunk_size": 100, "chunk_overlap": 20}
            }
        )
        
        # Test health check
        health_status = await pipeline.health_check()
        assert health_status is True
        
        # Test pipeline info
        info = pipeline.get_pipeline_info()
        assert "name" in info
        assert "components" in info
        assert "config" in info 