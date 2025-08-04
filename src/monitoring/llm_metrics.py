"""
LLM Metrics Collection

Collects and manages metrics for LLM providers including:
- Request duration
- Token generation rate
- Error rates
- Request counts
- Tokens generated
"""

from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry
from typing import Optional


class LLMMetrics:
    """Metrics collection for LLM providers"""
    
    def __init__(self, registry: CollectorRegistry = None):
        """Initialize LLM metrics"""
        self.registry = registry or CollectorRegistry()
        
        # Request duration histogram
        self.request_duration = Histogram(
            'llm_request_duration_seconds',
            'LLM request duration in seconds',
            labelnames=['provider'],
            registry=self.registry
        )
        
        # Token generation rate gauge
        self.token_generation_rate = Gauge(
            'llm_token_generation_rate',
            'Tokens generated per second',
            labelnames=['provider'],
            registry=self.registry
        )
        
        # Error rate counter
        self.error_rate = Counter(
            'llm_errors_total',
            'Total LLM errors',
            labelnames=['provider', 'error_type'],
            registry=self.registry
        )
        
        # Requests total counter
        self.requests_total = Counter(
            'llm_requests_total',
            'Total LLM requests',
            labelnames=['provider'],
            registry=self.registry
        )
        
        # Tokens generated total counter
        self.tokens_generated_total = Counter(
            'llm_tokens_generated_total',
            'Total tokens generated',
            labelnames=['provider'],
            registry=self.registry
        )
    
    def record_request(self, provider: str, duration: float, tokens: int):
        """Record a successful LLM request"""
        self.request_duration.labels(provider=provider).observe(duration)
        self.requests_total.labels(provider=provider).inc()
        self.tokens_generated_total.labels(provider=provider).inc(tokens)
        
        # Calculate and update token generation rate
        if duration > 0:
            rate = tokens / duration
            self.token_generation_rate.labels(provider=provider).set(rate)
    
    def record_error(self, provider: str, error_type: str):
        """Record an LLM error"""
        self.error_rate.labels(provider=provider, error_type=error_type).inc()
    
    def update_token_generation_rate(self, provider: str, rate: float):
        """Update token generation rate directly"""
        self.token_generation_rate.labels(provider=provider).set(rate) 