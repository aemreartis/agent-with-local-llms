"""
Monitoring Integration Tests

Tests for comprehensive monitoring system integration and pipeline.
Following TDD methodology: Tests first, then implementation.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import json
from typing import Dict, List, Any

from src.monitoring.monitoring_pipeline import MonitoringPipeline
from src.monitoring.metrics_aggregator import MetricsAggregator
from src.monitoring.system_health_monitor import SystemHealthMonitor
from src.monitoring.monitoring_orchestrator import MonitoringOrchestrator


class TestMonitoringPipeline:
    """Test monitoring pipeline integration"""
    
    @pytest.fixture
    def monitoring_pipeline(self):
        """Create monitoring pipeline instance"""
        return MonitoringPipeline()
    
    def test_monitoring_pipeline_initialization(self, monitoring_pipeline):
        """Test monitoring pipeline is properly initialized"""
        assert hasattr(monitoring_pipeline, 'metrics_collector')
        assert hasattr(monitoring_pipeline, 'business_metrics')
        assert hasattr(monitoring_pipeline, 'dashboard_manager')
        assert hasattr(monitoring_pipeline, 'alert_manager')
        assert hasattr(monitoring_pipeline, 'health_monitor')
    
    def test_collect_all_metrics(self, monitoring_pipeline):
        """Test collection of all metrics"""
        query_data = {
            'query': 'What is AI?',
            'response': 'AI is artificial intelligence...',
            'processing_time': 1.5,
            'tokens_used': 100,
            'user_rating': 4.5
        }
        
        all_metrics = monitoring_pipeline.collect_all_metrics(query_data)
        
        assert all_metrics is not None
        assert 'system_metrics' in all_metrics
        assert 'business_metrics' in all_metrics
        assert 'performance_metrics' in all_metrics
        assert 'quality_metrics' in all_metrics
    
    def test_process_metrics_pipeline(self, monitoring_pipeline):
        """Test metrics processing pipeline"""
        raw_metrics = {
            'llm_metrics': {'requests': 10, 'errors': 1},
            'vector_metrics': {'searches': 20, 'latency': 0.5},
            'api_metrics': {'requests': 30, 'response_time': 1.2}
        }
        
        processed_metrics = monitoring_pipeline.process_metrics(raw_metrics)
        
        assert processed_metrics is not None
        assert 'aggregated_metrics' in processed_metrics
        assert 'health_status' in processed_metrics
        assert 'alerts' in processed_metrics
    
    def test_update_dashboards(self, monitoring_pipeline):
        """Test dashboard updates"""
        metrics_data = {
            'system_overview': {'cpu_usage': 0.6, 'memory_usage': 0.7},
            'business_metrics': {'user_satisfaction': 4.2, 'cost_per_query': 0.01}
        }
        
        result = monitoring_pipeline.update_dashboards(metrics_data)
        
        assert result is not None
        assert 'updated' in result
        assert 'failed' in result
    
    def test_check_and_send_alerts(self, monitoring_pipeline):
        """Test alert checking and sending"""
        metrics_data = {
            'error_rate': 0.15,
            'response_time': 3.0,
            'cpu_usage': 0.9
        }
        
        alerts = monitoring_pipeline.check_and_send_alerts(metrics_data)
        
        assert alerts is not None
        assert isinstance(alerts, list)
    
    def test_complete_monitoring_cycle(self, monitoring_pipeline):
        """Test complete monitoring cycle"""
        query_event = {
            'query': 'Test query',
            'response': 'Test response',
            'processing_time': 2.0,
            'tokens_used': 150,
            'user_rating': 4.0
        }
        
        cycle_result = monitoring_pipeline.run_monitoring_cycle(query_event)
        
        assert cycle_result is not None
        assert 'metrics_collected' in cycle_result
        assert 'dashboards_updated' in cycle_result
        assert 'alerts_sent' in cycle_result
        assert 'health_status' in cycle_result


class TestMetricsAggregator:
    """Test metrics aggregation functionality"""
    
    @pytest.fixture
    def metrics_aggregator(self):
        """Create metrics aggregator instance"""
        return MetricsAggregator()
    
    def test_metrics_aggregator_initialization(self, metrics_aggregator):
        """Test metrics aggregator is properly initialized"""
        assert hasattr(metrics_aggregator, 'aggregation_rules')
        assert hasattr(metrics_aggregator, 'time_windows')
    
    def test_aggregate_system_metrics(self, metrics_aggregator):
        """Test system metrics aggregation"""
        system_metrics = [
            {'cpu_usage': 0.5, 'memory_usage': 0.6, 'timestamp': '2024-01-01T10:00:00'},
            {'cpu_usage': 0.7, 'memory_usage': 0.8, 'timestamp': '2024-01-01T10:01:00'},
            {'cpu_usage': 0.6, 'memory_usage': 0.7, 'timestamp': '2024-01-01T10:02:00'}
        ]
        
        aggregated = metrics_aggregator.aggregate_system_metrics(system_metrics)
        
        assert aggregated is not None
        assert 'avg_cpu_usage' in aggregated
        assert 'avg_memory_usage' in aggregated
        assert 'max_cpu_usage' in aggregated
        assert 'max_memory_usage' in aggregated
    
    def test_aggregate_business_metrics(self, metrics_aggregator):
        """Test business metrics aggregation"""
        business_metrics = [
            {'user_satisfaction': 4.0, 'cost_per_query': 0.01, 'timestamp': '2024-01-01T10:00:00'},
            {'user_satisfaction': 4.5, 'cost_per_query': 0.015, 'timestamp': '2024-01-01T10:01:00'},
            {'user_satisfaction': 3.8, 'cost_per_query': 0.012, 'timestamp': '2024-01-01T10:02:00'}
        ]
        
        aggregated = metrics_aggregator.aggregate_business_metrics(business_metrics)
        
        assert aggregated is not None
        assert 'avg_user_satisfaction' in aggregated
        assert 'avg_cost_per_query' in aggregated
        assert 'satisfaction_trend' in aggregated
        assert 'cost_trend' in aggregated
    
    def test_aggregate_performance_metrics(self, metrics_aggregator):
        """Test performance metrics aggregation"""
        performance_metrics = [
            {'response_time': 1.0, 'throughput': 100, 'timestamp': '2024-01-01T10:00:00'},
            {'response_time': 1.2, 'throughput': 95, 'timestamp': '2024-01-01T10:01:00'},
            {'response_time': 0.8, 'throughput': 110, 'timestamp': '2024-01-01T10:02:00'}
        ]
        
        aggregated = metrics_aggregator.aggregate_performance_metrics(performance_metrics)
        
        assert aggregated is not None
        assert 'avg_response_time' in aggregated
        assert 'avg_throughput' in aggregated
        assert 'p95_response_time' in aggregated
        assert 'performance_trend' in aggregated
    
    def test_calculate_trends(self, metrics_aggregator):
        """Test trend calculation"""
        time_series_data = [1.0, 1.2, 1.1, 1.3, 1.0, 0.9, 1.1]
        
        trend = metrics_aggregator.calculate_trend(time_series_data)
        
        assert trend is not None
        assert 'direction' in trend
        assert 'slope' in trend
        assert 'confidence' in trend
    
    def test_aggregate_all_metrics(self, metrics_aggregator):
        """Test aggregation of all metrics"""
        all_metrics = {
            'system': [
                {'cpu_usage': 0.5, 'memory_usage': 0.6, 'timestamp': '2024-01-01T10:00:00'}
            ],
            'business': [
                {'user_satisfaction': 4.0, 'cost_per_query': 0.01, 'timestamp': '2024-01-01T10:00:00'}
            ],
            'performance': [
                {'response_time': 1.0, 'throughput': 100, 'timestamp': '2024-01-01T10:00:00'}
            ]
        }
        
        aggregated = metrics_aggregator.aggregate_all_metrics(all_metrics)
        
        assert aggregated is not None
        assert 'system_summary' in aggregated
        assert 'business_summary' in aggregated
        assert 'performance_summary' in aggregated
        assert 'overall_health' in aggregated


class TestSystemHealthMonitor:
    """Test system health monitoring"""
    
    @pytest.fixture
    def health_monitor(self):
        """Create health monitor instance"""
        return SystemHealthMonitor()
    
    def test_health_monitor_initialization(self, health_monitor):
        """Test health monitor is properly initialized"""
        assert hasattr(health_monitor, 'health_thresholds')
        assert hasattr(health_monitor, 'health_history')
    
    def test_check_system_health(self, health_monitor):
        """Test system health checking"""
        system_metrics = {
            'cpu_usage': 0.7,
            'memory_usage': 0.8,
            'disk_usage': 0.6,
            'error_rate': 0.05
        }
        
        health_status = health_monitor.check_system_health(system_metrics)
        
        assert health_status is not None
        assert 'overall_health' in health_status
        assert 'component_health' in health_status
        assert 'alerts' in health_status
    
    def test_check_component_health(self, health_monitor):
        """Test component health checking"""
        component_metrics = {
            'llm_provider': {'error_rate': 0.02, 'response_time': 1.5},
            'vector_store': {'error_rate': 0.01, 'search_time': 0.3},
            'memory_provider': {'error_rate': 0.03, 'cache_hit_rate': 0.8}
        }
        
        component_health = health_monitor.check_component_health(component_metrics)
        
        assert component_health is not None
        assert 'component_health' in component_health
        assert 'llm_provider' in component_health['component_health']
        assert 'vector_store' in component_health['component_health']
        assert 'memory_provider' in component_health['component_health']
    
    def test_generate_health_report(self, health_monitor):
        """Test health report generation"""
        health_data = {
            'system_health': 'healthy',
            'component_health': {
                'llm_provider': 'healthy',
                'vector_store': 'warning',
                'memory_provider': 'healthy'
            },
            'alerts': ['High vector store latency']
        }
        
        report = health_monitor.generate_health_report(health_data)
        
        assert report is not None
        assert 'summary' in report
        assert 'details' in report
        assert 'recommendations' in report
    
    def test_predict_health_issues(self, health_monitor):
        """Test health issue prediction"""
        historical_metrics = [
            {'cpu_usage': 0.5, 'memory_usage': 0.6, 'timestamp': '2024-01-01T10:00:00'},
            {'cpu_usage': 0.6, 'memory_usage': 0.7, 'timestamp': '2024-01-01T10:01:00'},
            {'cpu_usage': 0.7, 'memory_usage': 0.8, 'timestamp': '2024-01-01T10:02:00'}
        ]
        
        predictions = health_monitor.predict_health_issues(historical_metrics)
        
        assert predictions is not None
        assert 'predicted_issues' in predictions
        assert 'confidence' in predictions
        assert 'timeframe' in predictions


class TestMonitoringOrchestrator:
    """Test monitoring orchestrator"""
    
    @pytest.fixture
    def monitoring_orchestrator(self):
        """Create monitoring orchestrator instance"""
        return MonitoringOrchestrator()
    
    def test_monitoring_orchestrator_initialization(self, monitoring_orchestrator):
        """Test monitoring orchestrator is properly initialized"""
        assert hasattr(monitoring_orchestrator, 'pipeline')
        assert hasattr(monitoring_orchestrator, 'aggregator')
        assert hasattr(monitoring_orchestrator, 'health_monitor')
    
    def test_start_monitoring(self, monitoring_orchestrator):
        """Test starting monitoring"""
        config = {
            'collection_interval': 30,
            'dashboard_update_interval': 60,
            'alert_check_interval': 15
        }
        
        result = monitoring_orchestrator.start_monitoring(config)
        
        assert result is not None
        assert 'status' in result
        assert 'monitoring_active' in result
    
    def test_stop_monitoring(self, monitoring_orchestrator):
        """Test stopping monitoring"""
        result = monitoring_orchestrator.stop_monitoring()
        
        assert result is not None
        assert 'status' in result
        assert 'monitoring_active' in result
    
    def test_get_monitoring_status(self, monitoring_orchestrator):
        """Test getting monitoring status"""
        status = monitoring_orchestrator.get_monitoring_status()
        
        assert status is not None
        assert 'active' in status
        assert 'last_update' in status
        assert 'metrics_collected' in status
    
    def test_configure_monitoring(self, monitoring_orchestrator):
        """Test monitoring configuration"""
        config = {
            'metrics_collection': {
                'enabled': True,
                'interval': 30
            },
            'dashboard_updates': {
                'enabled': True,
                'interval': 60
            },
            'alerting': {
                'enabled': True,
                'interval': 15
            }
        }
        
        result = monitoring_orchestrator.configure_monitoring(config)
        
        assert result is not None
        assert 'configured' in result
        assert 'active_components' in result
    
    def test_run_monitoring_cycle(self, monitoring_orchestrator):
        """Test running monitoring cycle"""
        # Start monitoring first
        config = {
            'metrics_collection': {'enabled': True, 'interval': 30},
            'dashboard_updates': {'enabled': True, 'interval': 60},
            'alerting': {'enabled': True, 'interval': 15}
        }
        monitoring_orchestrator.start_monitoring(config)
        
        # Now run monitoring cycle
        cycle_result = monitoring_orchestrator.run_monitoring_cycle()
        
        assert cycle_result is not None
        assert 'metrics_collected' in cycle_result
        assert 'dashboards_updated' in cycle_result
        assert 'alerts_sent' in cycle_result
        assert 'health_status' in cycle_result 