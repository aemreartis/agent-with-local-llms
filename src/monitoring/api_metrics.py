"""
API Metrics Collection

Collects and manages metrics for API endpoints including:
- Request rate
- Response time
- Error rate
- Request counts
- Active connections
"""

from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry
from typing import Optional


class APIMetrics:
    """Metrics collection for API endpoints"""
    
    def __init__(self, registry: CollectorRegistry = None):
        """Initialize API metrics"""
        self.registry = registry or CollectorRegistry()
        
        # Request rate counter
        self.request_rate = Counter(
            'api_requests_total',
            'Total API requests',
            labelnames=['endpoint', 'method'],
            registry=self.registry
        )
        
        # Response time histogram
        self.response_time = Histogram(
            'api_response_time_seconds',
            'API response time in seconds',
            labelnames=['endpoint', 'method'],
            registry=self.registry
        )
        
        # Error rate counter
        self.error_rate = Counter(
            'api_errors_total',
            'Total API errors',
            labelnames=['endpoint', 'error_type'],
            registry=self.registry
        )
        
        # Requests total counter (alias for request_rate)
        self.requests_total = self.request_rate
        
        # Active connections gauge
        self.active_connections = Gauge(
            'api_active_connections',
            'Number of active API connections',
            registry=self.registry
        )
    
    def record_request(self, endpoint: str, method: str, duration: float):
        """Record an API request"""
        self.request_rate.labels(endpoint=endpoint, method=method).inc()
        self.response_time.labels(endpoint=endpoint, method=method).observe(duration)
    
    def record_error(self, endpoint: str, method: str, error_type: str):
        """Record an API error"""
        self.error_rate.labels(endpoint=endpoint, error_type=error_type).inc()
    
    def update_active_connections(self, count: int):
        """Update active connections count"""
        self.active_connections.set(count)
    
    def increment_active_connections(self):
        """Increment active connections count"""
        self.active_connections.inc()
    
    def decrement_active_connections(self):
        """Decrement active connections count"""
        self.active_connections.dec()
    
    def record_request_with_error(self, endpoint: str, method: str, duration: float, error_type: str):
        """Record an API request that resulted in an error"""
        self.record_request(endpoint, method, duration)
        self.record_error(endpoint, method, error_type) 