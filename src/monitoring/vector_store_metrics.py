"""
Vector Store Metrics Collection

Collects and manages metrics for vector store providers including:
- Search duration
- Index size
- Operations count
- Vectors stored
- Search queries
"""

from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry
from typing import Optional


class VectorStoreMetrics:
    """Metrics collection for vector store providers"""
    
    def __init__(self, registry: CollectorRegistry = None):
        """Initialize vector store metrics"""
        self.registry = registry or CollectorRegistry()
        
        # Search duration histogram
        self.search_duration = Histogram(
            'vector_search_duration_seconds',
            'Vector search duration in seconds',
            labelnames=['provider'],
            registry=self.registry
        )
        
        # Index size gauge
        self.index_size = Gauge(
            'vector_index_size_bytes',
            'Vector index size in bytes',
            labelnames=['provider'],
            registry=self.registry
        )
        
        # Operations total counter
        self.operations_total = Counter(
            'vector_operations_total',
            'Total vector operations',
            labelnames=['provider', 'operation_type'],
            registry=self.registry
        )
        
        # Vectors stored total counter
        self.vectors_stored_total = Counter(
            'vector_vectors_stored_total',
            'Total vectors stored',
            labelnames=['provider'],
            registry=self.registry
        )
        
        # Search queries total counter
        self.search_queries_total = Counter(
            'vector_search_queries_total',
            'Total search queries',
            labelnames=['provider'],
            registry=self.registry
        )
    
    def record_search(self, provider: str, duration: float, results_count: int):
        """Record a vector search operation"""
        self.search_duration.labels(provider=provider).observe(duration)
        self.search_queries_total.labels(provider=provider).inc()
    
    def record_operation(self, provider: str, operation_type: str, vectors_count: int = 0):
        """Record a vector store operation"""
        self.operations_total.labels(provider=provider, operation_type=operation_type).inc()
        
        if operation_type == 'store' and vectors_count > 0:
            self.vectors_stored_total.labels(provider=provider).inc(vectors_count)
    
    def update_index_size(self, provider: str, size_bytes: int):
        """Update vector index size"""
        self.index_size.labels(provider=provider).set(size_bytes)
    
    def record_batch_operation(self, provider: str, operation_type: str, batch_size: int):
        """Record a batch vector operation"""
        self.operations_total.labels(provider=provider, operation_type=operation_type).inc()
        
        if operation_type == 'store':
            self.vectors_stored_total.labels(provider=provider).inc(batch_size) 