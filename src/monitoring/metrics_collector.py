"""
Main Metrics Collector

Integrates all metrics collection components and provides a unified interface
for collecting and retrieving Prometheus metrics.
"""

from prometheus_client import CollectorRegistry, generate_latest
from .llm_metrics import LLMMetrics
from .vector_store_metrics import VectorStoreMetrics
from .memory_metrics import MemoryMetrics
from .api_metrics import APIMetrics
from .system_metrics import SystemMetrics


class MetricsCollector:
    """Main metrics collector that integrates all metrics components"""
    
    def __init__(self):
        """Initialize the metrics collector with all components"""
        # Create a custom registry for our metrics
        self.registry = CollectorRegistry()
        
        # Initialize all metrics components with the shared registry
        self.llm_metrics = LLMMetrics(self.registry)
        self.vector_store_metrics = VectorStoreMetrics(self.registry)
        self.memory_metrics = MemoryMetrics(self.registry)
        self.api_metrics = APIMetrics(self.registry)
        self.system_metrics = SystemMetrics(self.registry)
        
        # Register all metrics with the registry
        self._register_metrics()
    
    def _register_metrics(self):
        """Register all metrics with the Prometheus registry"""
        # Note: Metrics are automatically registered when created with the registry
        # This method is kept for potential future use or explicit registration needs
        pass
    
    def get_metrics(self) -> str:
        """Generate Prometheus metrics output"""
        return generate_latest(self.registry).decode('utf-8')
    
    def get_registry(self) -> CollectorRegistry:
        """Get the Prometheus registry"""
        return self.registry
    
    def record_llm_request(self, provider: str, duration: float, tokens: int):
        """Record an LLM request"""
        self.llm_metrics.record_request(provider, duration, tokens)
    
    def record_llm_error(self, provider: str, error_type: str):
        """Record an LLM error"""
        self.llm_metrics.record_error(provider, error_type)
    
    def record_vector_search(self, provider: str, duration: float, results_count: int):
        """Record a vector search operation"""
        self.vector_store_metrics.record_search(provider, duration, results_count)
    
    def record_vector_operation(self, provider: str, operation_type: str, vectors_count: int = 0):
        """Record a vector store operation"""
        self.vector_store_metrics.record_operation(provider, operation_type, vectors_count)
    
    def record_memory_operation(self, provider: str, operation_type: str, data_size: int = 0):
        """Record a memory operation"""
        self.memory_metrics.record_operation(provider, operation_type, data_size)
    
    def record_api_request(self, endpoint: str, method: str, duration: float):
        """Record an API request"""
        self.api_metrics.record_request(endpoint, method, duration)
    
    def record_api_error(self, endpoint: str, method: str, error_type: str):
        """Record an API error"""
        self.api_metrics.record_error(endpoint, method, error_type)
    
    def update_system_metrics(self, cpu_percent: float, memory_bytes: int, disk_bytes: int, process_count: int):
        """Update system metrics"""
        self.system_metrics.update_cpu_usage(cpu_percent)
        self.system_metrics.update_memory_usage(memory_bytes)
        self.system_metrics.update_disk_usage(disk_bytes)
        self.system_metrics.update_process_count(process_count)
    
    def record_network_io(self, direction: str, bytes_transferred: int):
        """Record network I/O"""
        self.system_metrics.record_network_io(direction, bytes_transferred) 