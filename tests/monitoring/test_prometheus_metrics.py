"""
Prometheus Metrics Collection Tests

Tests for comprehensive metrics collection across all system components.
Following TDD methodology: Tests first, then implementation.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry
import time
import asyncio

from src.monitoring.metrics_collector import MetricsCollector
from src.monitoring.llm_metrics import LLMMetrics
from src.monitoring.vector_store_metrics import VectorStoreMetrics
from src.monitoring.memory_metrics import MemoryMetrics
from src.monitoring.api_metrics import APIMetrics
from src.monitoring.system_metrics import SystemMetrics


class TestLLMMetrics:
    """Test LLM provider metrics collection"""
    
    @pytest.fixture
    def llm_metrics(self):
        """Create LLM metrics instance"""
        return LLMMetrics()
    
    def test_llm_metrics_initialization(self, llm_metrics):
        """Test LLM metrics are properly initialized"""
        assert hasattr(llm_metrics, 'request_duration')
        assert hasattr(llm_metrics, 'token_generation_rate')
        assert hasattr(llm_metrics, 'error_rate')
        assert hasattr(llm_metrics, 'requests_total')
        assert hasattr(llm_metrics, 'tokens_generated_total')
    
    def test_llm_request_duration_histogram(self, llm_metrics):
        """Test LLM request duration histogram"""
        assert isinstance(llm_metrics.request_duration, Histogram)
        assert llm_metrics.request_duration._name == 'llm_request_duration_seconds'
        assert 'provider' in llm_metrics.request_duration._labelnames
    
    def test_llm_token_generation_rate_gauge(self, llm_metrics):
        """Test LLM token generation rate gauge"""
        assert isinstance(llm_metrics.token_generation_rate, Gauge)
        assert llm_metrics.token_generation_rate._name == 'llm_token_generation_rate'
        assert 'provider' in llm_metrics.token_generation_rate._labelnames
    
    def test_llm_error_rate_counter(self, llm_metrics):
        """Test LLM error rate counter"""
        assert isinstance(llm_metrics.error_rate, Counter)
        assert llm_metrics.error_rate._name == 'llm_errors'
        assert 'provider' in llm_metrics.error_rate._labelnames
        assert 'error_type' in llm_metrics.error_rate._labelnames
    
    def test_llm_requests_total_counter(self, llm_metrics):
        """Test LLM requests total counter"""
        assert isinstance(llm_metrics.requests_total, Counter)
        assert llm_metrics.requests_total._name == 'llm_requests'
        assert 'provider' in llm_metrics.requests_total._labelnames
    
    def test_llm_tokens_generated_total_counter(self, llm_metrics):
        """Test LLM tokens generated total counter"""
        assert isinstance(llm_metrics.tokens_generated_total, Counter)
        assert llm_metrics.tokens_generated_total._name == 'llm_tokens_generated'
        assert 'provider' in llm_metrics.tokens_generated_total._labelnames
    
    def test_llm_metrics_record_request(self, llm_metrics):
        """Test recording LLM request metrics"""
        # Record a request
        llm_metrics.record_request('vllm', duration=1.5, tokens=100)
        
        # Verify metrics were recorded by checking the registry
        metrics_output = llm_metrics.registry.get_sample_value('llm_requests_total', {'provider': 'vllm'})
        assert metrics_output is not None
        assert metrics_output > 0
    
    def test_llm_metrics_record_error(self, llm_metrics):
        """Test recording LLM error metrics"""
        # Record an error
        llm_metrics.record_error('vllm', 'timeout')
        
        # Verify error was recorded by checking the registry
        metrics_output = llm_metrics.registry.get_sample_value('llm_errors_total', {'provider': 'vllm', 'error_type': 'timeout'})
        assert metrics_output is not None
        assert metrics_output > 0


class TestVectorStoreMetrics:
    """Test vector store metrics collection"""
    
    @pytest.fixture
    def vector_store_metrics(self):
        """Create vector store metrics instance"""
        return VectorStoreMetrics()
    
    def test_vector_store_metrics_initialization(self, vector_store_metrics):
        """Test vector store metrics are properly initialized"""
        assert hasattr(vector_store_metrics, 'search_duration')
        assert hasattr(vector_store_metrics, 'index_size')
        assert hasattr(vector_store_metrics, 'operations_total')
        assert hasattr(vector_store_metrics, 'vectors_stored_total')
        assert hasattr(vector_store_metrics, 'search_queries_total')
    
    def test_vector_store_search_duration_histogram(self, vector_store_metrics):
        """Test vector store search duration histogram"""
        assert isinstance(vector_store_metrics.search_duration, Histogram)
        assert vector_store_metrics.search_duration._name == 'vector_search_duration_seconds'
        assert 'provider' in vector_store_metrics.search_duration._labelnames
    
    def test_vector_store_index_size_gauge(self, vector_store_metrics):
        """Test vector store index size gauge"""
        assert isinstance(vector_store_metrics.index_size, Gauge)
        assert vector_store_metrics.index_size._name == 'vector_index_size_bytes'
        assert 'provider' in vector_store_metrics.index_size._labelnames
    
    def test_vector_store_operations_total_counter(self, vector_store_metrics):
        """Test vector store operations total counter"""
        assert isinstance(vector_store_metrics.operations_total, Counter)
        assert vector_store_metrics.operations_total._name == 'vector_operations'
        assert 'provider' in vector_store_metrics.operations_total._labelnames
        assert 'operation_type' in vector_store_metrics.operations_total._labelnames
    
    def test_vector_store_vectors_stored_total_counter(self, vector_store_metrics):
        """Test vector store vectors stored total counter"""
        assert isinstance(vector_store_metrics.vectors_stored_total, Counter)
        assert vector_store_metrics.vectors_stored_total._name == 'vector_vectors_stored'
        assert 'provider' in vector_store_metrics.vectors_stored_total._labelnames
    
    def test_vector_store_search_queries_total_counter(self, vector_store_metrics):
        """Test vector store search queries total counter"""
        assert isinstance(vector_store_metrics.search_queries_total, Counter)
        assert vector_store_metrics.search_queries_total._name == 'vector_search_queries'
        assert 'provider' in vector_store_metrics.search_queries_total._labelnames
    
    def test_vector_store_metrics_record_search(self, vector_store_metrics):
        """Test recording vector store search metrics"""
        # Record a search operation
        vector_store_metrics.record_search('qdrant', duration=0.5, results_count=10)
        
        # Verify metrics were recorded by checking the registry
        metrics_output = vector_store_metrics.registry.get_sample_value('vector_search_queries_total', {'provider': 'qdrant'})
        assert metrics_output is not None
        assert metrics_output > 0
    
    def test_vector_store_metrics_record_operation(self, vector_store_metrics):
        """Test recording vector store operation metrics"""
        # Record an operation
        vector_store_metrics.record_operation('qdrant', 'store', vectors_count=5)
        
        # Verify metrics were recorded by checking the registry
        metrics_output = vector_store_metrics.registry.get_sample_value('vector_operations_total', {'provider': 'qdrant', 'operation_type': 'store'})
        assert metrics_output is not None
        assert metrics_output > 0


class TestMemoryMetrics:
    """Test memory provider metrics collection"""
    
    @pytest.fixture
    def memory_metrics(self):
        """Create memory metrics instance"""
        return MemoryMetrics()
    
    def test_memory_metrics_initialization(self, memory_metrics):
        """Test memory metrics are properly initialized"""
        assert hasattr(memory_metrics, 'cache_hit_rate')
        assert hasattr(memory_metrics, 'storage_usage')
        assert hasattr(memory_metrics, 'session_count')
        assert hasattr(memory_metrics, 'operations_total')
        assert hasattr(memory_metrics, 'data_size_bytes')
    
    def test_memory_cache_hit_rate_gauge(self, memory_metrics):
        """Test memory cache hit rate gauge"""
        assert isinstance(memory_metrics.cache_hit_rate, Gauge)
        assert memory_metrics.cache_hit_rate._name == 'memory_cache_hit_rate'
        assert 'provider' in memory_metrics.cache_hit_rate._labelnames
    
    def test_memory_storage_usage_gauge(self, memory_metrics):
        """Test memory storage usage gauge"""
        assert isinstance(memory_metrics.storage_usage, Gauge)
        assert memory_metrics.storage_usage._name == 'memory_storage_usage_bytes'
        assert 'provider' in memory_metrics.storage_usage._labelnames
    
    def test_memory_session_count_gauge(self, memory_metrics):
        """Test memory session count gauge"""
        assert isinstance(memory_metrics.session_count, Gauge)
        assert memory_metrics.session_count._name == 'memory_session_count'
        assert 'provider' in memory_metrics.session_count._labelnames
    
    def test_memory_operations_total_counter(self, memory_metrics):
        """Test memory operations total counter"""
        assert isinstance(memory_metrics.operations_total, Counter)
        assert memory_metrics.operations_total._name == 'memory_operations'
        assert 'provider' in memory_metrics.operations_total._labelnames
        assert 'operation_type' in memory_metrics.operations_total._labelnames
    
    def test_memory_data_size_bytes_gauge(self, memory_metrics):
        """Test memory data size bytes gauge"""
        assert isinstance(memory_metrics.data_size_bytes, Gauge)
        assert memory_metrics.data_size_bytes._name == 'memory_data_size_bytes'
        assert 'provider' in memory_metrics.data_size_bytes._labelnames
    
    def test_memory_metrics_record_operation(self, memory_metrics):
        """Test recording memory operation metrics"""
        # Record an operation
        memory_metrics.record_operation('redis', 'store', data_size=1024)
        
        # Verify metrics were recorded by checking the registry
        metrics_output = memory_metrics.registry.get_sample_value('memory_operations_total', {'provider': 'redis', 'operation_type': 'store'})
        assert metrics_output is not None
        assert metrics_output > 0
    
    def test_memory_metrics_update_cache_hit_rate(self, memory_metrics):
        """Test updating memory cache hit rate"""
        # Update cache hit rate
        memory_metrics.update_cache_hit_rate('redis', 0.85)
        
        # Verify rate was updated by checking the registry
        metrics_output = memory_metrics.registry.get_sample_value('memory_cache_hit_rate', {'provider': 'redis'})
        assert metrics_output is not None
        assert metrics_output == 0.85


class TestAPIMetrics:
    """Test API metrics collection"""
    
    @pytest.fixture
    def api_metrics(self):
        """Create API metrics instance"""
        return APIMetrics()
    
    def test_api_metrics_initialization(self, api_metrics):
        """Test API metrics are properly initialized"""
        assert hasattr(api_metrics, 'request_rate')
        assert hasattr(api_metrics, 'response_time')
        assert hasattr(api_metrics, 'error_rate')
        assert hasattr(api_metrics, 'requests_total')
        assert hasattr(api_metrics, 'active_connections')
    
    def test_api_request_rate_counter(self, api_metrics):
        """Test API request rate counter"""
        assert isinstance(api_metrics.request_rate, Counter)
        assert api_metrics.request_rate._name == 'api_requests'
        assert 'endpoint' in api_metrics.request_rate._labelnames
        assert 'method' in api_metrics.request_rate._labelnames
    
    def test_api_response_time_histogram(self, api_metrics):
        """Test API response time histogram"""
        assert isinstance(api_metrics.response_time, Histogram)
        assert api_metrics.response_time._name == 'api_response_time_seconds'
        assert 'endpoint' in api_metrics.response_time._labelnames
        assert 'method' in api_metrics.response_time._labelnames
    
    def test_api_error_rate_counter(self, api_metrics):
        """Test API error rate counter"""
        assert isinstance(api_metrics.error_rate, Counter)
        assert api_metrics.error_rate._name == 'api_errors'
        assert 'endpoint' in api_metrics.error_rate._labelnames
        assert 'error_type' in api_metrics.error_rate._labelnames
    
    def test_api_requests_total_counter(self, api_metrics):
        """Test API requests total counter"""
        assert isinstance(api_metrics.requests_total, Counter)
        assert api_metrics.requests_total._name == 'api_requests'
        assert 'endpoint' in api_metrics.requests_total._labelnames
        assert 'method' in api_metrics.requests_total._labelnames
    
    def test_api_active_connections_gauge(self, api_metrics):
        """Test API active connections gauge"""
        assert isinstance(api_metrics.active_connections, Gauge)
        assert api_metrics.active_connections._name == 'api_active_connections'
    
    def test_api_metrics_record_request(self, api_metrics):
        """Test recording API request metrics"""
        # Record a request
        api_metrics.record_request('/chat', 'POST', duration=0.5)
        
        # Verify metrics were recorded by checking the registry
        metrics_output = api_metrics.registry.get_sample_value('api_requests_total', {'endpoint': '/chat', 'method': 'POST'})
        assert metrics_output is not None
        assert metrics_output > 0
    
    def test_api_metrics_record_error(self, api_metrics):
        """Test recording API error metrics"""
        # Record an error
        api_metrics.record_error('/chat', 'POST', 'validation_error')
        
        # Verify error was recorded by checking the registry
        metrics_output = api_metrics.registry.get_sample_value('api_errors_total', {'endpoint': '/chat', 'error_type': 'validation_error'})
        assert metrics_output is not None
        assert metrics_output > 0


class TestSystemMetrics:
    """Test system metrics collection"""
    
    @pytest.fixture
    def system_metrics(self):
        """Create system metrics instance"""
        return SystemMetrics()
    
    def test_system_metrics_initialization(self, system_metrics):
        """Test system metrics are properly initialized"""
        assert hasattr(system_metrics, 'cpu_usage')
        assert hasattr(system_metrics, 'memory_usage')
        assert hasattr(system_metrics, 'disk_usage')
        assert hasattr(system_metrics, 'network_io')
        assert hasattr(system_metrics, 'process_count')
    
    def test_system_cpu_usage_gauge(self, system_metrics):
        """Test system CPU usage gauge"""
        assert isinstance(system_metrics.cpu_usage, Gauge)
        assert system_metrics.cpu_usage._name == 'system_cpu_usage_percent'
    
    def test_system_memory_usage_gauge(self, system_metrics):
        """Test system memory usage gauge"""
        assert isinstance(system_metrics.memory_usage, Gauge)
        assert system_metrics.memory_usage._name == 'system_memory_usage_bytes'
    
    def test_system_disk_usage_gauge(self, system_metrics):
        """Test system disk usage gauge"""
        assert isinstance(system_metrics.disk_usage, Gauge)
        assert system_metrics.disk_usage._name == 'system_disk_usage_bytes'
    
    def test_system_network_io_counter(self, system_metrics):
        """Test system network I/O counter"""
        assert isinstance(system_metrics.network_io, Counter)
        assert system_metrics.network_io._name == 'system_network_io_bytes'
        assert 'direction' in system_metrics.network_io._labelnames
    
    def test_system_process_count_gauge(self, system_metrics):
        """Test system process count gauge"""
        assert isinstance(system_metrics.process_count, Gauge)
        assert system_metrics.process_count._name == 'system_process_count'
    
    def test_system_metrics_update_cpu_usage(self, system_metrics):
        """Test updating system CPU usage"""
        # Update CPU usage
        system_metrics.update_cpu_usage(45.5)
        
        # Verify usage was updated by checking the registry
        metrics_output = system_metrics.registry.get_sample_value('system_cpu_usage_percent')
        assert metrics_output is not None
        assert metrics_output == 45.5
    
    def test_system_metrics_update_memory_usage(self, system_metrics):
        """Test updating system memory usage"""
        # Update memory usage
        system_metrics.update_memory_usage(8589934592)  # 8GB
        
        # Verify usage was updated by checking the registry
        metrics_output = system_metrics.registry.get_sample_value('system_memory_usage_bytes')
        assert metrics_output is not None
        assert metrics_output == 8589934592


class TestMetricsCollector:
    """Test main metrics collector integration"""
    
    @pytest.fixture
    def metrics_collector(self):
        """Create metrics collector instance"""
        return MetricsCollector()
    
    def test_metrics_collector_initialization(self, metrics_collector):
        """Test metrics collector is properly initialized"""
        assert hasattr(metrics_collector, 'llm_metrics')
        assert hasattr(metrics_collector, 'vector_store_metrics')
        assert hasattr(metrics_collector, 'memory_metrics')
        assert hasattr(metrics_collector, 'api_metrics')
        assert hasattr(metrics_collector, 'system_metrics')
    
    def test_metrics_collector_registry(self, metrics_collector):
        """Test metrics collector has Prometheus registry"""
        assert hasattr(metrics_collector, 'registry')
        assert isinstance(metrics_collector.registry, CollectorRegistry)
    
    def test_metrics_collector_get_metrics(self, metrics_collector):
        """Test metrics collector can generate metrics output"""
        # Get metrics output
        metrics_output = metrics_collector.get_metrics()
        
        # Verify output is not empty
        assert metrics_output is not None
        assert len(metrics_output) > 0
    
    def test_metrics_collector_integration(self, metrics_collector):
        """Test metrics collector integration with all components"""
        # Record metrics from different components
        metrics_collector.llm_metrics.record_request('vllm', duration=1.0, tokens=50)
        metrics_collector.vector_store_metrics.record_search('qdrant', duration=0.3, results_count=5)
        metrics_collector.memory_metrics.record_operation('redis', 'store', data_size=512)
        metrics_collector.api_metrics.record_request('/chat', 'POST', duration=0.8)
        metrics_collector.system_metrics.update_cpu_usage(30.0)
        
        # Get metrics output
        metrics_output = metrics_collector.get_metrics()
        
        # Verify all metrics are present
        assert 'llm_request_duration_seconds' in metrics_output
        assert 'vector_search_duration_seconds' in metrics_output
        assert 'memory_operations_total' in metrics_output
        assert 'api_requests_total' in metrics_output
        assert 'system_cpu_usage_percent' in metrics_output 