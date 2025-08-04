"""
Advanced Integration Tests: Production Load & Error Testing

Tests production load scenarios, concurrent user simulation, stress testing,
and real-world error scenarios following TDD methodology.
"""

import pytest
import asyncio
import time
import random
import tempfile
import os
from typing import Dict, List, Any, Optional
from unittest.mock import patch, MagicMock
from concurrent.futures import ThreadPoolExecutor
import statistics

pytestmark = pytest.mark.asyncio

from src.orchestration.document_pipeline import DocumentPipeline
from src.orchestration.search_orchestrator import SearchOrchestrator
from src.orchestration.query_orchestrator import QueryOrchestrator
from src.orchestration.chat_service import ChatService
from src.registry.provider_registry import ProviderRegistry
from src.config.config_loader import ConfigLoader


class TestProductionLoadScenarios:
    """Test production load scenarios with concurrent users and high throughput"""
    
    @pytest.fixture
    async def setup_load_test_components(self):
        """Set up components for load testing"""
        # Initialize registry and config
        registry = ProviderRegistry()
        config_loader = ConfigLoader()
        
        # Use a default config for testing
        config = {
            "app": {
                "name": "agentic-rag-load-test",
                "version": "1.0.0"
            },
            "providers": {
                "llm": {
                    "default": "vllm",
                    "providers": {
                        "vllm": {
                            "class": "src.providers.llm.vllm_provider.VLLMProvider",
                            "config": {
                                "base_url": "http://localhost:8001"
                            }
                        }
                    }
                },
                "vector_store": {
                    "default": "qdrant",
                    "providers": {
                        "qdrant": {
                            "class": "src.providers.vector_stores.qdrant_provider.QdrantProvider",
                            "config": {
                                "url": "http://localhost:6333"
                            }
                        }
                    }
                },
                "search_engine": {
                    "default": "bm25",
                    "providers": {
                        "bm25": {
                            "class": "src.providers.search_engines.bm25_provider.BM25Provider",
                            "config": {}
                        }
                    }
                },
                "memory": {
                    "default": "redis",
                    "providers": {
                        "redis": {
                            "class": "src.providers.memory.redis_provider.RedisMemoryProvider",
                            "config": {
                                "host": "localhost",
                                "port": 6379
                            }
                        }
                    }
                }
            },
            "document_pipeline": {
                "loader": {
                    "type": "text",
                    "config": {}
                },
                "processor": {
                    "type": "text",
                    "config": {}
                },
                "chunker": {
                    "type": "text",
                    "config": {}
                }
            }
        }
        
        # For testing purposes, we'll use mock providers to avoid external dependencies
        class MockLLMProvider:
            async def initialize(self, config):
                pass
            async def embed(self, text):
                # Simulate some processing time
                await asyncio.sleep(0.01)
                return [0.1] * 384
            async def generate(self, prompt, **kwargs):
                await asyncio.sleep(0.05)  # Simulate LLM generation time
                return f"Mock response to: {prompt[:50]}..."
            async def health_check(self):
                return True
        
        class MockVectorStoreProvider:
            def __init__(self):
                self.stored_vectors = {}
                self.operation_count = 0
            
            async def initialize(self, config):
                pass
            async def store(self, embedding, metadata):
                self.operation_count += 1
                vector_id = f"mock_vector_{self.operation_count}"
                self.stored_vectors[vector_id] = {"embedding": embedding, "metadata": metadata}
                await asyncio.sleep(0.02)  # Simulate storage time
                return vector_id
            async def delete(self, vector_id):
                if vector_id in self.stored_vectors:
                    del self.stored_vectors[vector_id]
                return True
            async def health_check(self):
                return True
        
        class MockSearchEngineProvider:
            def __init__(self):
                self.search_count = 0
            
            async def initialize(self, config):
                pass
            async def search(self, query, top_k=10):
                self.search_count += 1
                await asyncio.sleep(0.03)  # Simulate search time
                return [
                    {"content": f"Result {i} for {query}", "score": 0.9 - i * 0.1}
                    for i in range(min(top_k, 5))
                ]
            async def health_check(self):
                return True
        
        class MockMemoryProvider:
            def __init__(self):
                self.stored_data = {}
                self.operation_count = 0
            
            async def initialize(self, config):
                pass
            async def store(self, key, data, metadata=None):
                self.operation_count += 1
                self.stored_data[key] = data
                await asyncio.sleep(0.01)  # Simulate storage time
                return True
            async def retrieve(self, key):
                await asyncio.sleep(0.01)  # Simulate retrieval time
                return self.stored_data.get(key, [])
            async def delete(self, key):
                if key in self.stored_data:
                    del self.stored_data[key]
                return True
            async def health_check(self):
                return True
        
        registry.register_provider("llm", "vllm", MockLLMProvider)
        registry.register_provider("vector_store", "qdrant", MockVectorStoreProvider)
        registry.register_provider("search_engine", "bm25", MockSearchEngineProvider)
        registry.register_provider("memory", "redis", MockMemoryProvider)
        
        # Initialize providers with correct config structure
        provider_configs = {}
        for category, category_config in config["providers"].items():
            provider_configs[category] = {}
            for provider_name, provider_config in category_config["providers"].items():
                provider_configs[category][provider_name] = provider_config["config"]
        
        await registry.initialize_providers(provider_configs)
        
        # Initialize components
        document_pipeline = DocumentPipeline(registry)
        search_orchestrator = SearchOrchestrator()
        query_orchestrator = QueryOrchestrator()
        chat_service = ChatService()
        
        # Initialize components with config
        await document_pipeline.initialize(config)
        await search_orchestrator.initialize(config)
        await query_orchestrator.initialize(config)
        await chat_service.initialize(config)
        
        return {
            'registry': registry,
            'config': config,
            'document_pipeline': document_pipeline,
            'search_orchestrator': search_orchestrator,
            'query_orchestrator': query_orchestrator,
            'chat_service': chat_service
        }
    
    @pytest.fixture
    def load_test_documents(self):
        """Create test documents for load testing"""
        documents = []
        for i in range(10):
            content = f"""
            # Test Document {i}
            
            This is test document {i} for load testing purposes.
            
            ## Section 1
            This document contains various sections with different content.
            
            ## Section 2
            More content for testing search and retrieval functionality.
            
            ## Section 3
            Additional content to make the document more substantial.
            
            Key terms: testing, load, performance, document {i}, section
            """
            
            documents.append({
                'content': content,
                'metadata': {
                    'title': f'Test Document {i}',
                    'type': 'test',
                    'language': 'en',
                    'document_id': f'doc_{i}'
                }
            })
        
        return documents
    
    async def test_concurrent_document_processing(self, setup_load_test_components, load_test_documents):
        """Test concurrent processing of multiple documents"""
        components = await setup_load_test_components
        
        # Create temporary files for all documents
        temp_files = []
        for i, doc_data in enumerate(load_test_documents):
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                f.write(doc_data['content'])
                temp_files.append((f.name, doc_data['metadata']))
        
        try:
            # Process documents concurrently
            start_time = time.time()
            
            tasks = []
            for file_path, metadata in temp_files:
                task = components['document_pipeline'].process_document(
                    file_path=file_path,
                    metadata=metadata
                )
                tasks.append(task)
            
            results = await asyncio.gather(*tasks)
            end_time = time.time()
            
            total_time = end_time - start_time
            
            # Assertions
            assert len(results) == len(temp_files)
            for result in results:
                assert result['success'] is True
                assert 'document_id' in result
                assert 'chunks' in result
                assert len(result['chunks']) > 0
            
            # Performance assertions
            assert total_time < len(temp_files) * 2.0  # Should be much faster than sequential
            avg_time_per_doc = total_time / len(temp_files)
            assert avg_time_per_doc < 1.0  # Each document should process in under 1 second
            
            print(f"Processed {len(temp_files)} documents concurrently in {total_time:.2f}s")
            print(f"Average time per document: {avg_time_per_doc:.2f}s")
            
        finally:
            # Cleanup
            for file_path, _ in temp_files:
                os.unlink(file_path)
    
    async def test_concurrent_search_operations(self, setup_load_test_components, load_test_documents):
        """Test concurrent search operations"""
        components = await setup_load_test_components
        
        # First, ingest documents
        temp_files = []
        for doc_data in load_test_documents[:5]:  # Use first 5 documents
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                f.write(doc_data['content'])
                temp_files.append((f.name, doc_data['metadata']))
        
        try:
            # Ingest documents
            for file_path, metadata in temp_files:
                await components['document_pipeline'].process_document(
                    file_path=file_path,
                    metadata=metadata
                )
            
            # Define search queries
            search_queries = [
                "testing",
                "performance",
                "document",
                "section",
                "content",
                "load",
                "concurrent",
                "search",
                "retrieval",
                "functionality"
            ]
            
            # Perform concurrent searches
            start_time = time.time()
            
            search_tasks = []
            for query in search_queries:
                # Create search request
                from src.interfaces.search_orchestrator_interface import SearchRequest, FusionStrategy
                search_request = SearchRequest(
                    query=query,
                    providers=["vector", "bm25"],
                    fusion_strategy=FusionStrategy.RANK_FUSION,
                    top_k=5
                )
                task = components['search_orchestrator'].search(search_request)
                search_tasks.append(task)
            
            search_results = await asyncio.gather(*search_tasks)
            end_time = time.time()
            
            total_time = end_time - start_time
            
            # Assertions
            assert len(search_results) == len(search_queries)
            for result in search_results:
                assert hasattr(result, 'fused_results') or isinstance(result, dict)
            
            # Performance assertions
            assert total_time < len(search_queries) * 1.0  # Should be faster than sequential
            avg_time_per_search = total_time / len(search_queries)
            assert avg_time_per_search < 0.5  # Each search should complete in under 0.5 seconds
            
            print(f"Performed {len(search_queries)} concurrent searches in {total_time:.2f}s")
            print(f"Average time per search: {avg_time_per_search:.2f}s")
            
        finally:
            # Cleanup
            for file_path, _ in temp_files:
                os.unlink(file_path)
    
    async def test_high_throughput_document_ingestion(self, setup_load_test_components):
        """Test high throughput document ingestion"""
        components = await setup_load_test_components
        
        # Create many small documents for high throughput testing
        num_documents = 50
        documents = []
        
        for i in range(num_documents):
            content = f"Document {i}: This is a test document for high throughput testing. "
            content += "It contains some key terms and phrases for search testing. " * 5
            
            documents.append({
                'content': content,
                'metadata': {
                    'title': f'High Throughput Doc {i}',
                    'type': 'throughput_test',
                    'language': 'en'
                }
            })
        
        # Create temporary files
        temp_files = []
        for doc_data in documents:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                f.write(doc_data['content'])
                temp_files.append((f.name, doc_data['metadata']))
        
        try:
            # Process documents in batches
            batch_size = 10
            total_start_time = time.time()
            
            successful_ingestions = 0
            failed_ingestions = 0
            
            for i in range(0, len(temp_files), batch_size):
                batch = temp_files[i:i + batch_size]
                
                batch_start_time = time.time()
                tasks = []
                for file_path, metadata in batch:
                    task = components['document_pipeline'].process_document(
                        file_path=file_path,
                        metadata=metadata
                    )
                    tasks.append(task)
                
                batch_results = await asyncio.gather(*tasks, return_exceptions=True)
                batch_end_time = time.time()
                
                # Count successes and failures
                for result in batch_results:
                    if isinstance(result, Exception):
                        failed_ingestions += 1
                    elif result.get('success'):
                        successful_ingestions += 1
                    else:
                        failed_ingestions += 1
                
                batch_time = batch_end_time - batch_start_time
                print(f"Batch {i//batch_size + 1}: {len(batch)} documents in {batch_time:.2f}s")
            
            total_end_time = time.time()
            total_time = total_end_time - total_start_time
            
            # Assertions
            success_rate = successful_ingestions / num_documents
            assert success_rate > 0.9  # 90% success rate minimum
            
            throughput = successful_ingestions / total_time
            assert throughput > 5.0  # At least 5 documents per second
            
            print(f"High throughput test: {successful_ingestions}/{num_documents} successful")
            print(f"Success rate: {success_rate:.2%}")
            print(f"Throughput: {throughput:.2f} documents/second")
            print(f"Total time: {total_time:.2f}s")
            
        finally:
            # Cleanup
            for file_path, _ in temp_files:
                os.unlink(file_path)
    
    async def test_memory_usage_under_load(self, setup_load_test_components, load_test_documents):
        """Test memory usage under load"""
        components = await setup_load_test_components
        
        # Monitor memory usage during load testing
        import psutil
        import gc
        
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Create and process documents
        temp_files = []
        for doc_data in load_test_documents:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                f.write(doc_data['content'])
                temp_files.append((f.name, doc_data['metadata']))
        
        try:
            # Process documents
            for file_path, metadata in temp_files:
                await components['document_pipeline'].process_document(
                    file_path=file_path,
                    metadata=metadata
                )
            
            # Force garbage collection
            gc.collect()
            
            # Check memory usage
            final_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_increase = final_memory - initial_memory
            
            print(f"Initial memory: {initial_memory:.2f} MB")
            print(f"Final memory: {final_memory:.2f} MB")
            print(f"Memory increase: {memory_increase:.2f} MB")
            
            # Assertions
            assert memory_increase < 100  # Should not increase by more than 100MB
            assert final_memory < 500  # Should not exceed 500MB total
            
        finally:
            # Cleanup
            for file_path, _ in temp_files:
                os.unlink(file_path)
    
    async def test_concurrent_user_simulation(self, setup_load_test_components):
        """Simulate concurrent users performing various operations"""
        components = await setup_load_test_components
        
        # Define user operations
        async def user_operation(user_id: int, operation_type: str):
            """Simulate a user performing an operation"""
            try:
                if operation_type == "document_upload":
                    # Simulate document upload
                    content = f"User {user_id} document content with some key terms."
                    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                        f.write(content)
                        temp_file_path = f.name
                    
                    try:
                        result = await components['document_pipeline'].process_document(
                            file_path=temp_file_path,
                            metadata={
                                'title': f'User {user_id} Document',
                                'type': 'user_upload',
                                'user_id': user_id
                            }
                        )
                        return {"user_id": user_id, "operation": operation_type, "success": result['success']}
                    finally:
                        os.unlink(temp_file_path)
                
                elif operation_type == "search":
                    # Simulate search operation
                    query = f"user {user_id} search query"
                    from src.interfaces.search_orchestrator_interface import SearchRequest, FusionStrategy
                    search_request = SearchRequest(
                        query=query,
                        providers=["vector", "bm25"],
                        fusion_strategy=FusionStrategy.RANK_FUSION,
                        top_k=5
                    )
                    result = await components['search_orchestrator'].search(search_request)
                    return {"user_id": user_id, "operation": operation_type, "success": True}
                
                elif operation_type == "chat":
                    # Simulate chat operation
                    message = f"User {user_id} chat message"
                    # This would use the chat service in a real scenario
                    return {"user_id": user_id, "operation": operation_type, "success": True}
                
                else:
                    return {"user_id": user_id, "operation": operation_type, "success": False, "error": "Unknown operation"}
            
            except Exception as e:
                return {"user_id": user_id, "operation": operation_type, "success": False, "error": str(e)}
        
        # Simulate concurrent users
        num_users = 20
        operations_per_user = 5
        operation_types = ["document_upload", "search", "chat"]
        
        start_time = time.time()
        
        # Create user tasks
        all_tasks = []
        for user_id in range(num_users):
            for _ in range(operations_per_user):
                operation_type = random.choice(operation_types)
                task = user_operation(user_id, operation_type)
                all_tasks.append(task)
        
        # Execute all user operations concurrently
        results = await asyncio.gather(*all_tasks, return_exceptions=True)
        end_time = time.time()
        
        total_time = end_time - start_time
        total_operations = len(all_tasks)
        
        # Analyze results
        successful_operations = sum(1 for r in results if isinstance(r, dict) and r.get('success'))
        failed_operations = total_operations - successful_operations
        
        success_rate = successful_operations / total_operations
        operations_per_second = total_operations / total_time
        
        print(f"Concurrent user simulation: {num_users} users, {operations_per_user} operations each")
        print(f"Total operations: {total_operations}")
        print(f"Successful operations: {successful_operations}")
        print(f"Failed operations: {failed_operations}")
        print(f"Success rate: {success_rate:.2%}")
        print(f"Operations per second: {operations_per_second:.2f}")
        print(f"Total time: {total_time:.2f}s")
        
        # Assertions
        assert success_rate > 0.8  # 80% success rate minimum
        assert operations_per_second > 10  # At least 10 operations per second
        assert total_time < 30  # Should complete within 30 seconds


class TestErrorScenarios:
    """Test real-world error scenarios and recovery mechanisms"""
    
    @pytest.fixture
    async def setup_error_test_components(self):
        """Set up components for error testing"""
        # Similar setup to load testing but with error-prone mock providers
        registry = ProviderRegistry()
        
        class ErrorProneLLMProvider:
            def __init__(self):
                self.call_count = 0
                self.fail_every_n = 5  # Fail every 5th call
            
            async def initialize(self, config):
                pass
            
            async def embed(self, text):
                self.call_count += 1
                if self.call_count % self.fail_every_n == 0:
                    raise Exception(f"LLM embedding failed on call {self.call_count}")
                await asyncio.sleep(0.01)
                return [0.1] * 384
            
            async def generate(self, prompt, **kwargs):
                self.call_count += 1
                if self.call_count % self.fail_every_n == 0:
                    raise Exception(f"LLM generation failed on call {self.call_count}")
                await asyncio.sleep(0.05)
                return f"Mock response to: {prompt[:50]}..."
            
            async def health_check(self):
                return True
        
        class ErrorProneVectorStoreProvider:
            def __init__(self):
                self.operation_count = 0
                self.fail_every_n = 3  # Fail every 3rd operation
            
            async def initialize(self, config):
                pass
            
            async def store(self, embedding, metadata):
                self.operation_count += 1
                if self.operation_count % self.fail_every_n == 0:
                    raise Exception(f"Vector store failed on operation {self.operation_count}")
                await asyncio.sleep(0.02)
                return f"mock_vector_{self.operation_count}"
            
            async def delete(self, vector_id):
                return True
            
            async def health_check(self):
                return True
        
        registry.register_provider("llm", "vllm", ErrorProneLLMProvider)
        registry.register_provider("vector_store", "qdrant", ErrorProneVectorStoreProvider)
        
        # Add missing providers for error testing
        class ErrorProneSearchEngineProvider:
            def __init__(self):
                self.operation_count = 0
                self.fail_every_n = 4  # Fail every 4th operation
            
            async def initialize(self, config):
                pass
            
            async def search(self, query, top_k=10):
                self.operation_count += 1
                if self.operation_count % self.fail_every_n == 0:
                    raise Exception(f"Search engine failed on operation {self.operation_count}")
                await asyncio.sleep(0.03)
                return [
                    {"content": f"Result {i} for {query}", "score": 0.9 - i * 0.1}
                    for i in range(min(top_k, 5))
                ]
            
            async def health_check(self):
                return True
        
        class ErrorProneMemoryProvider:
            def __init__(self):
                self.operation_count = 0
                self.fail_every_n = 6  # Fail every 6th operation
                self.stored_data = {}
            
            async def initialize(self, config):
                pass
            
            async def store(self, key, data, metadata=None):
                self.operation_count += 1
                if self.operation_count % self.fail_every_n == 0:
                    raise Exception(f"Memory provider failed on operation {self.operation_count}")
                self.stored_data[key] = data
                await asyncio.sleep(0.01)
                return True
            
            async def retrieve(self, key):
                self.operation_count += 1
                if self.operation_count % self.fail_every_n == 0:
                    raise Exception(f"Memory provider failed on operation {self.operation_count}")
                await asyncio.sleep(0.01)
                return self.stored_data.get(key, [])
            
            async def delete(self, key):
                if key in self.stored_data:
                    del self.stored_data[key]
                return True
            
            async def health_check(self):
                return True
        
        registry.register_provider("search_engine", "bm25", ErrorProneSearchEngineProvider)
        registry.register_provider("memory", "redis", ErrorProneMemoryProvider)
        
        # Initialize with minimal config
        config = {
            "app": {"name": "error-test"},
            "providers": {
                "llm": {"vllm": {"config": {}}},
                "vector_store": {"qdrant": {"config": {}}}
            }
        }
        
        await registry.initialize_providers(config)
        
        document_pipeline = DocumentPipeline(registry)
        await document_pipeline.initialize(config)
        
        return {
            'registry': registry,
            'document_pipeline': document_pipeline
        }
    
    async def test_graceful_degradation_on_provider_failure(self, setup_error_test_components):
        """Test system behavior when providers fail"""
        components = await setup_error_test_components
        
        # Create test documents
        documents = []
        for i in range(10):
            content = f"Test document {i} for error testing."
            documents.append({
                'content': content,
                'metadata': {'title': f'Error Test Doc {i}', 'type': 'error_test'}
            })
        
        # Process documents and expect some failures
        temp_files = []
        for doc_data in documents:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                f.write(doc_data['content'])
                temp_files.append((f.name, doc_data['metadata']))
        
        try:
            results = []
            for file_path, metadata in temp_files:
                try:
                    result = await components['document_pipeline'].process_document(
                        file_path=file_path,
                        metadata=metadata
                    )
                    results.append(result)
                except Exception as e:
                    results.append({'success': False, 'error': str(e)})
            
            # Analyze results
            successful = sum(1 for r in results if r.get('success'))
            failed = len(results) - successful
            
            print(f"Error scenario test: {successful} successful, {failed} failed")
            
            # Assertions
            assert successful > 0  # Some operations should succeed
            assert failed > 0  # Some operations should fail due to error-prone providers
            assert successful + failed == len(documents)  # All documents processed
            
        finally:
            # Cleanup
            for file_path, _ in temp_files:
                os.unlink(file_path)
    
    async def test_recovery_after_provider_failure(self, setup_error_test_components):
        """Test system recovery after provider failures"""
        components = await setup_error_test_components
        
        # Test that the system can recover and continue processing
        content = "Test document for recovery testing."
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(content)
            temp_file_path = f.name
        
        try:
            # Process multiple times to trigger failures and recovery
            results = []
            for i in range(5):
                try:
                    result = await components['document_pipeline'].process_document(
                        file_path=temp_file_path,
                        metadata={'title': f'Recovery Test {i}', 'type': 'recovery_test'}
                    )
                    results.append(result)
                except Exception as e:
                    results.append({'success': False, 'error': str(e)})
            
            # Check that some operations succeeded after failures
            successful_after_failure = False
            for i, result in enumerate(results):
                if i > 0 and result.get('success'):
                    # Check if there was a previous failure
                    if any(not r.get('success') for r in results[:i]):
                        successful_after_failure = True
                        break
            
            print(f"Recovery test results: {[r.get('success') for r in results]}")
            
            # Assertions
            assert successful_after_failure, "System should recover after provider failures"
            
        finally:
            os.unlink(temp_file_path) 