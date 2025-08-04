"""
Alert Rules Definitions

Defines various alert rules for monitoring system health, performance, and business metrics.
"""

from typing import Dict, List, Any


class AlertRules:
    """Alert rule definitions for Grafana"""
    
    def get_high_error_rate_rule(self) -> Dict[str, Any]:
        """Get high error rate alert rule"""
        return {
            'name': 'High Error Rate',
            'condition': 'rate(api_errors_total[5m]) > 0.1',
            'threshold': 0.1,
            'duration': '5m',
            'severity': 'warning',
            'description': 'API error rate is above threshold',
            'annotations': {
                'summary': 'High error rate detected',
                'description': 'Error rate is {{ $value }} errors per second'
            }
        }
    
    def get_performance_degradation_rule(self) -> Dict[str, Any]:
        """Get performance degradation alert rule"""
        return {
            'name': 'Performance Degradation',
            'condition': 'histogram_quantile(0.95, rate(api_response_time_seconds_bucket[5m])) > 2',
            'threshold': 2.0,
            'duration': '5m',
            'severity': 'warning',
            'description': 'API response time is degraded',
            'annotations': {
                'summary': 'Performance degradation detected',
                'description': '95th percentile response time is {{ $value }} seconds'
            }
        }
    
    def get_resource_usage_rule(self) -> Dict[str, Any]:
        """Get high resource usage alert rule"""
        return {
            'name': 'High Resource Usage',
            'condition': 'system_cpu_usage_percent > 80 or system_memory_usage_bytes > 12884901888',
            'threshold': 80,
            'duration': '5m',
            'severity': 'warning',
            'description': 'System resource usage is high',
            'annotations': {
                'summary': 'High resource usage detected',
                'description': 'CPU: {{ $value }}% or Memory: {{ $value }} bytes'
            }
        }
    
    def get_business_metric_rule(self) -> Dict[str, Any]:
        """Get business metric alert rule"""
        return {
            'name': 'Business Metric Alert',
            'condition': 'user_satisfaction_score < 0.8 or response_quality_score < 0.8',
            'threshold': 0.8,
            'duration': '10m',
            'severity': 'critical',
            'description': 'Business metrics are below acceptable levels',
            'annotations': {
                'summary': 'Business metrics degraded',
                'description': 'User satisfaction: {{ $value }} or Quality score: {{ $value }}'
            }
        }
    
    def get_llm_provider_rule(self) -> Dict[str, Any]:
        """Get LLM provider alert rule"""
        return {
            'name': 'LLM Provider Issues',
            'condition': 'rate(llm_errors_total[5m]) > 0.05 or rate(llm_request_duration_seconds_sum[5m]) / rate(llm_request_duration_seconds_count[5m]) > 10',
            'threshold': 0.05,
            'duration': '5m',
            'severity': 'warning',
            'description': 'LLM provider is experiencing issues',
            'annotations': {
                'summary': 'LLM provider issues detected',
                'description': 'Error rate: {{ $value }} or Response time: {{ $value }} seconds'
            }
        }
    
    def get_vector_store_rule(self) -> Dict[str, Any]:
        """Get vector store alert rule"""
        return {
            'name': 'Vector Store Issues',
            'condition': 'rate(vector_search_duration_seconds_sum[5m]) / rate(vector_search_duration_seconds_count[5m]) > 1 or vector_index_size_bytes > 10737418240',
            'threshold': 1.0,
            'duration': '5m',
            'severity': 'warning',
            'description': 'Vector store is experiencing issues',
            'annotations': {
                'summary': 'Vector store issues detected',
                'description': 'Search time: {{ $value }} seconds or Index size: {{ $value }} bytes'
            }
        }
    
    def get_memory_provider_rule(self) -> Dict[str, Any]:
        """Get memory provider alert rule"""
        return {
            'name': 'Memory Provider Issues',
            'condition': 'memory_cache_hit_rate < 0.7 or memory_storage_usage_bytes > 8589934592',
            'threshold': 0.7,
            'duration': '5m',
            'severity': 'warning',
            'description': 'Memory provider is experiencing issues',
            'annotations': {
                'summary': 'Memory provider issues detected',
                'description': 'Cache hit rate: {{ $value }} or Storage usage: {{ $value }} bytes'
            }
        }
    
    def get_cost_alert_rule(self) -> Dict[str, Any]:
        """Get cost alert rule"""
        return {
            'name': 'High Cost Alert',
            'condition': 'increase(total_cost_dollars[1h]) > 10 or cost_per_query_dollars > 0.05',
            'threshold': 10.0,
            'duration': '1h',
            'severity': 'warning',
            'description': 'System costs are above threshold',
            'annotations': {
                'summary': 'High cost detected',
                'description': 'Hourly cost: ${{ $value }} or Cost per query: ${{ $value }}'
            }
        }
    
    def get_availability_rule(self) -> Dict[str, Any]:
        """Get availability alert rule"""
        return {
            'name': 'Service Availability',
            'condition': 'up == 0 or rate(api_requests_total[5m]) == 0',
            'threshold': 0,
            'duration': '2m',
            'severity': 'critical',
            'description': 'Service is not available',
            'annotations': {
                'summary': 'Service unavailable',
                'description': 'Service is down or not receiving requests'
            }
        }
    
    def get_all_rules(self) -> Dict[str, Dict[str, Any]]:
        """Get all alert rules"""
        return {
            'high_error_rate': self.get_high_error_rate_rule(),
            'performance_degradation': self.get_performance_degradation_rule(),
            'resource_usage': self.get_resource_usage_rule(),
            'business_metric': self.get_business_metric_rule(),
            'llm_provider': self.get_llm_provider_rule(),
            'vector_store': self.get_vector_store_rule(),
            'memory_provider': self.get_memory_provider_rule(),
            'cost_alert': self.get_cost_alert_rule(),
            'availability': self.get_availability_rule()
        } 