"""
Monitoring Orchestrator

Manages the complete monitoring system lifecycle including starting, stopping, configuring, and running monitoring cycles.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from .monitoring_pipeline import MonitoringPipeline
from .metrics_aggregator import MetricsAggregator
from .system_health_monitor import SystemHealthMonitor


class MonitoringOrchestrator:
    """Orchestrates the complete monitoring system"""
    
    def __init__(self, grafana_url: str = "http://localhost:3000", grafana_api_key: str = "test_key"):
        """Initialize monitoring orchestrator
        
        Args:
            grafana_url: Grafana server URL
            grafana_api_key: Grafana API key
        """
        self.pipeline = MonitoringPipeline(grafana_url, grafana_api_key)
        self.aggregator = MetricsAggregator()
        self.health_monitor = SystemHealthMonitor()
        
        # Monitoring state
        self.monitoring_active = False
        self.monitoring_config = {}
        self.last_update = None
        self.metrics_collected = 0
        self.cycle_count = 0
        
        # Performance tracking
        self.cycle_times = []
        self.error_count = 0
        self.success_count = 0
    
    def start_monitoring(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Start the monitoring system
        
        Args:
            config: Monitoring configuration
            
        Returns:
            Start result dictionary
        """
        try:
            # Validate configuration
            if not self._validate_config(config):
                return {
                    'status': 'failed',
                    'monitoring_active': False,
                    'error': 'Invalid configuration'
                }
            
            # Store configuration
            self.monitoring_config = config.copy()
            
            # Initialize monitoring state
            self.monitoring_active = True
            self.last_update = datetime.now()
            self.metrics_collected = 0
            self.cycle_count = 0
            self.cycle_times = []
            self.error_count = 0
            self.success_count = 0
            
            return {
                'status': 'success',
                'monitoring_active': True,
                'config': self.monitoring_config,
                'start_time': self.last_update.isoformat()
            }
            
        except Exception as e:
            return {
                'status': 'failed',
                'monitoring_active': False,
                'error': str(e)
            }
    
    def stop_monitoring(self) -> Dict[str, Any]:
        """Stop the monitoring system
        
        Returns:
            Stop result dictionary
        """
        try:
            # Stop monitoring
            self.monitoring_active = False
            
            # Calculate performance metrics
            performance_metrics = self._calculate_performance_metrics()
            
            return {
                'status': 'success',
                'monitoring_active': False,
                'stop_time': datetime.now().isoformat(),
                'performance_metrics': performance_metrics
            }
            
        except Exception as e:
            return {
                'status': 'failed',
                'monitoring_active': False,
                'error': str(e)
            }
    
    def get_monitoring_status(self) -> Dict[str, Any]:
        """Get current monitoring status
        
        Returns:
            Status dictionary
        """
        return {
            'active': self.monitoring_active,
            'last_update': self.last_update.isoformat() if self.last_update else None,
            'metrics_collected': self.metrics_collected,
            'cycle_count': self.cycle_count,
            'error_count': self.error_count,
            'success_count': self.success_count,
            'config': self.monitoring_config,
            'uptime': self._calculate_uptime()
        }
    
    def configure_monitoring(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Configure monitoring settings
        
        Args:
            config: New monitoring configuration
            
        Returns:
            Configuration result dictionary
        """
        try:
            # Validate configuration
            if not self._validate_config(config):
                return {
                    'configured': False,
                    'error': 'Invalid configuration'
                }
            
            # Update configuration
            self.monitoring_config.update(config)
            
            # Determine active components
            active_components = []
            if config.get('metrics_collection', {}).get('enabled', True):
                active_components.append('metrics_collection')
            if config.get('dashboard_updates', {}).get('enabled', True):
                active_components.append('dashboard_updates')
            if config.get('alerting', {}).get('enabled', True):
                active_components.append('alerting')
            
            return {
                'configured': True,
                'active_components': active_components,
                'config': self.monitoring_config
            }
            
        except Exception as e:
            return {
                'configured': False,
                'error': str(e)
            }
    
    def run_monitoring_cycle(self) -> Dict[str, Any]:
        """Run a single monitoring cycle
        
        Returns:
            Cycle result dictionary
        """
        if not self.monitoring_active:
            return {
                'status': 'failed',
                'error': 'Monitoring is not active'
            }
        
        cycle_start = datetime.now()
        
        try:
            # Create mock query event for testing
            query_event = self._create_mock_query_event()
            
            # Run monitoring cycle
            cycle_result = self.pipeline.run_monitoring_cycle(query_event)
            
            # Update tracking metrics
            self.cycle_count += 1
            self.success_count += 1
            self.last_update = datetime.now()
            
            if cycle_result.get('metrics_collected'):
                self.metrics_collected += cycle_result.get('metrics_count', 1)
            
            # Record cycle time
            cycle_time = (datetime.now() - cycle_start).total_seconds()
            self.cycle_times.append(cycle_time)
            
            # Add cycle metadata
            cycle_result['cycle_number'] = self.cycle_count
            cycle_result['cycle_time'] = cycle_time
            cycle_result['timestamp'] = self.last_update.isoformat()
            
            return cycle_result
            
        except Exception as e:
            self.error_count += 1
            self.last_update = datetime.now()
            
            return {
                'status': 'failed',
                'error': str(e),
                'cycle_number': self.cycle_count + 1,
                'timestamp': self.last_update.isoformat()
            }
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Get performance report for monitoring system
        
        Returns:
            Performance report dictionary
        """
        if not self.cycle_times:
            return {
                'total_cycles': 0,
                'average_cycle_time': 0.0,
                'success_rate': 0.0,
                'error_rate': 0.0
            }
        
        total_cycles = len(self.cycle_times)
        average_cycle_time = sum(self.cycle_times) / total_cycles
        success_rate = self.success_count / (self.success_count + self.error_count) if (self.success_count + self.error_count) > 0 else 0.0
        error_rate = self.error_count / (self.success_count + self.error_count) if (self.success_count + self.error_count) > 0 else 0.0
        
        return {
            'total_cycles': total_cycles,
            'average_cycle_time': average_cycle_time,
            'min_cycle_time': min(self.cycle_times),
            'max_cycle_time': max(self.cycle_times),
            'success_rate': success_rate,
            'error_rate': error_rate,
            'success_count': self.success_count,
            'error_count': self.error_count,
            'metrics_collected': self.metrics_collected,
            'uptime': self._calculate_uptime()
        }
    
    def _validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate monitoring configuration
        
        Args:
            config: Configuration to validate
            
        Returns:
            True if valid, False otherwise
        """
        required_sections = ['metrics_collection', 'dashboard_updates', 'alerting']
        
        for section in required_sections:
            if section not in config:
                return False
            
            section_config = config[section]
            if not isinstance(section_config, dict):
                return False
            
            if 'enabled' not in section_config:
                return False
            
            if section_config.get('enabled') and 'interval' not in section_config:
                return False
        
        return True
    
    def _calculate_performance_metrics(self) -> Dict[str, Any]:
        """Calculate performance metrics
        
        Returns:
            Performance metrics dictionary
        """
        if not self.cycle_times:
            return {
                'total_cycles': 0,
                'average_cycle_time': 0.0,
                'success_rate': 0.0
            }
        
        total_cycles = len(self.cycle_times)
        average_cycle_time = sum(self.cycle_times) / total_cycles
        success_rate = self.success_count / (self.success_count + self.error_count) if (self.success_count + self.error_count) > 0 else 0.0
        
        return {
            'total_cycles': total_cycles,
            'average_cycle_time': average_cycle_time,
            'success_rate': success_rate,
            'metrics_collected': self.metrics_collected
        }
    
    def _calculate_uptime(self) -> Optional[float]:
        """Calculate monitoring uptime in seconds
        
        Returns:
            Uptime in seconds or None if not started
        """
        if not self.last_update:
            return None
        
        # For simplicity, assume monitoring started when first cycle was run
        # In a real implementation, you'd track the actual start time
        return (datetime.now() - self.last_update).total_seconds()
    
    def _create_mock_query_event(self) -> Dict[str, Any]:
        """Create a mock query event for testing
        
        Returns:
            Mock query event dictionary
        """
        import random
        
        return {
            'query': 'What is machine learning?',
            'response': 'Machine learning is a subset of artificial intelligence that enables computers to learn from data.',
            'sources': ['ml_guide.pdf', 'ai_basics.pdf'],
            'user_rating': random.uniform(3.5, 5.0),
            'processing_time': random.uniform(0.5, 2.0),
            'tokens_used': random.randint(50, 200),
            'total_cost': random.uniform(0.001, 0.01),
            'cpu_usage': random.uniform(0.3, 0.7),
            'memory_usage': random.uniform(0.4, 0.8),
            'disk_usage': random.uniform(0.2, 0.6),
            'error_rate': random.uniform(0.0, 0.05),
            'success': True,
            'time_saved': random.uniform(30, 120),
            'revenue_impact': random.uniform(0.1, 1.0),
            'session_id': f'session_{random.randint(1000, 9999)}'
        } 