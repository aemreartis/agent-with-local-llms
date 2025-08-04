"""
Memory Metrics Collection

Collects and manages metrics for memory providers including:
- Cache hit rate
- Storage usage
- Session count
- Operations count
- Data size
"""

from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry
from typing import Optional


class MemoryMetrics:
    """Metrics collection for memory providers"""
    
    def __init__(self, registry: CollectorRegistry = None):
        """Initialize memory metrics"""
        self.registry = registry or CollectorRegistry()
        
        # Cache hit rate gauge
        self.cache_hit_rate = Gauge(
            'memory_cache_hit_rate',
            'Memory cache hit rate (0.0 to 1.0)',
            labelnames=['provider'],
            registry=self.registry
        )
        
        # Storage usage gauge
        self.storage_usage = Gauge(
            'memory_storage_usage_bytes',
            'Memory storage usage in bytes',
            labelnames=['provider'],
            registry=self.registry
        )
        
        # Session count gauge
        self.session_count = Gauge(
            'memory_session_count',
            'Number of active sessions',
            labelnames=['provider'],
            registry=self.registry
        )
        
        # Operations total counter
        self.operations_total = Counter(
            'memory_operations_total',
            'Total memory operations',
            labelnames=['provider', 'operation_type'],
            registry=self.registry
        )
        
        # Data size bytes gauge
        self.data_size_bytes = Gauge(
            'memory_data_size_bytes',
            'Total data size in bytes',
            labelnames=['provider'],
            registry=self.registry
        )
    
    def record_operation(self, provider: str, operation_type: str, data_size: int = 0):
        """Record a memory operation"""
        self.operations_total.labels(provider=provider, operation_type=operation_type).inc()
        
        if data_size > 0:
            self.data_size_bytes.labels(provider=provider).inc(data_size)
    
    def update_cache_hit_rate(self, provider: str, hit_rate: float):
        """Update cache hit rate (0.0 to 1.0)"""
        if 0.0 <= hit_rate <= 1.0:
            self.cache_hit_rate.labels(provider=provider).set(hit_rate)
    
    def update_storage_usage(self, provider: str, usage_bytes: int):
        """Update storage usage"""
        self.storage_usage.labels(provider=provider).set(usage_bytes)
    
    def update_session_count(self, provider: str, count: int):
        """Update session count"""
        self.session_count.labels(provider=provider).set(count)
    
    def record_session_operation(self, provider: str, operation_type: str):
        """Record a session-related operation"""
        self.operations_total.labels(provider=provider, operation_type=operation_type).inc()
    
    def update_data_size(self, provider: str, size_bytes: int):
        """Update total data size"""
        self.data_size_bytes.labels(provider=provider).set(size_bytes) 