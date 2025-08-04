"""
System Metrics Collection

Collects and manages metrics for system resources including:
- CPU usage
- Memory usage
- Disk usage
- Network I/O
- Process count
"""

from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry
from typing import Optional


class SystemMetrics:
    """Metrics collection for system resources"""
    
    def __init__(self, registry: CollectorRegistry = None):
        """Initialize system metrics"""
        self.registry = registry or CollectorRegistry()
        
        # CPU usage gauge
        self.cpu_usage = Gauge(
            'system_cpu_usage_percent',
            'System CPU usage percentage',
            registry=self.registry
        )
        
        # Memory usage gauge
        self.memory_usage = Gauge(
            'system_memory_usage_bytes',
            'System memory usage in bytes',
            registry=self.registry
        )
        
        # Disk usage gauge
        self.disk_usage = Gauge(
            'system_disk_usage_bytes',
            'System disk usage in bytes',
            registry=self.registry
        )
        
        # Network I/O counter
        self.network_io = Counter(
            'system_network_io_bytes',
            'System network I/O in bytes',
            labelnames=['direction'],
            registry=self.registry
        )
        
        # Process count gauge
        self.process_count = Gauge(
            'system_process_count',
            'Number of system processes',
            registry=self.registry
        )
    
    def update_cpu_usage(self, usage_percent: float):
        """Update CPU usage percentage"""
        if 0.0 <= usage_percent <= 100.0:
            self.cpu_usage.set(usage_percent)
    
    def update_memory_usage(self, usage_bytes: int):
        """Update memory usage in bytes"""
        if usage_bytes >= 0:
            self.memory_usage.set(usage_bytes)
    
    def update_disk_usage(self, usage_bytes: int):
        """Update disk usage in bytes"""
        if usage_bytes >= 0:
            self.disk_usage.set(usage_bytes)
    
    def record_network_io(self, direction: str, bytes_transferred: int):
        """Record network I/O"""
        if direction in ['in', 'out'] and bytes_transferred >= 0:
            self.network_io.labels(direction=direction).inc(bytes_transferred)
    
    def update_process_count(self, count: int):
        """Update process count"""
        if count >= 0:
            self.process_count.set(count)
    
    def record_network_input(self, bytes_transferred: int):
        """Record network input"""
        self.record_network_io('in', bytes_transferred)
    
    def record_network_output(self, bytes_transferred: int):
        """Record network output"""
        self.record_network_io('out', bytes_transferred) 