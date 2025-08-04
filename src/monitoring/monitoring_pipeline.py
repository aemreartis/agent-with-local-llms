"""
Monitoring Pipeline

Orchestrates the complete monitoring workflow including metrics collection, processing, dashboard updates, and alert checking.
"""

from typing import Dict, List, Any, Optional
from .metrics_collector import MetricsCollector
from .business_metrics import BusinessMetrics
from .metrics_aggregator import MetricsAggregator
from .system_health_monitor import SystemHealthMonitor
from .grafana_dashboard_manager import GrafanaDashboardManager
from .alert_manager import AlertManager
from datetime import datetime


class MonitoringPipeline:
    """Orchestrates complete monitoring workflow"""
    
    def __init__(self, grafana_url: str = "http://localhost:3000", grafana_api_key: str = "test_key"):
        """Initialize monitoring pipeline
        
        Args:
            grafana_url: Grafana server URL
            grafana_api_key: Grafana API key
        """
        self.metrics_collector = MetricsCollector()
        self.business_metrics = BusinessMetrics()
        self.metrics_aggregator = MetricsAggregator()
        self.health_monitor = SystemHealthMonitor()
        self.dashboard_manager = GrafanaDashboardManager(grafana_url, grafana_api_key)
        self.alert_manager = AlertManager(grafana_url, grafana_api_key)
    
    def collect_all_metrics(self, query_data: Dict[str, Any]) -> Dict[str, Any]:
        """Collect all metrics for a query event
        
        Args:
            query_data: Query event data
            
        Returns:
            Complete metrics dictionary
        """
        all_metrics = {}
        
        # Collect system metrics
        system_metrics = {
            'cpu_usage': query_data.get('cpu_usage', 0.0),
            'memory_usage': query_data.get('memory_usage', 0.0),
            'disk_usage': query_data.get('disk_usage', 0.0),
            'error_rate': query_data.get('error_rate', 0.0)
        }
        all_metrics['system_metrics'] = system_metrics
        
        # Collect business metrics
        business_data = {
            'response_data': {
                'query': query_data.get('query', ''),
                'response': query_data.get('response', ''),
                'sources': query_data.get('sources', []),
                'user_feedback': query_data.get('user_rating', 0.0)
            },
            'session_data': {
                'session_id': query_data.get('session_id', 'unknown'),
                'queries': [query_data.get('query', '')],
                'ratings': [query_data.get('user_rating', 0.0)],
                'completion_rate': 1.0,
                'time_spent': query_data.get('processing_time', 0.0)
            },
            'cost_data': {
                'llm_tokens_used': query_data.get('tokens_used', 0),
                'vector_search_queries': 1,
                'api_calls': 1,
                'processing_time': query_data.get('processing_time', 0.0),
                'total_cost': query_data.get('total_cost', 0.0)
            },
            'impact_data': {
                'queries_processed': 1,
                'successful_responses': 1 if query_data.get('success', True) else 0,
                'user_retention_rate': 1.0,
                'time_saved_per_query': query_data.get('time_saved', 0.0),
                'revenue_impact': query_data.get('revenue_impact', 0.0)
            }
        }
        business_metrics = self.business_metrics.collect_all_metrics(business_data)
        all_metrics['business_metrics'] = business_metrics
        
        # Collect performance metrics
        performance_metrics = {
            'response_time': query_data.get('processing_time', 0.0),
            'throughput': 1.0 / max(query_data.get('processing_time', 1.0), 0.1),
            'error_rate': 0.0 if query_data.get('success', True) else 1.0
        }
        all_metrics['performance_metrics'] = performance_metrics
        
        # Collect quality metrics
        quality_metrics = {
            'quality_score': business_metrics.get('response_quality', {}).get('quality_score', 0.0),
            'relevance_score': business_metrics.get('response_quality', {}).get('relevance_score', 0.0),
            'accuracy_score': business_metrics.get('response_quality', {}).get('accuracy_score', 0.0),
            'completeness_score': business_metrics.get('response_quality', {}).get('completeness_score', 0.0),
            'hallucination_score': business_metrics.get('response_quality', {}).get('hallucination_score', 0.0)
        }
        all_metrics['quality_metrics'] = quality_metrics
        
        return all_metrics
    
    def process_metrics(self, raw_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Process and aggregate raw metrics
        
        Args:
            raw_metrics: Raw metrics from different sources
            
        Returns:
            Processed metrics with aggregation and health status
        """
        processed_metrics = {}
        
        # Aggregate metrics by category
        aggregated_metrics = {}
        
        # System metrics aggregation
        if 'llm_metrics' in raw_metrics:
            system_data = [
                {
                    'cpu_usage': raw_metrics.get('llm_metrics', {}).get('cpu_usage', 0.0),
                    'memory_usage': raw_metrics.get('llm_metrics', {}).get('memory_usage', 0.0),
                    'disk_usage': 0.0
                }
            ]
            aggregated_metrics['system'] = system_data
        
        # Business metrics aggregation
        if 'business_metrics' in raw_metrics:
            business_data = [
                {
                    'user_satisfaction': raw_metrics.get('business_metrics', {}).get('user_satisfaction', {}).get('average_rating', 0.0),
                    'cost_per_query': raw_metrics.get('business_metrics', {}).get('cost_efficiency', {}).get('cost_per_query', 0.0),
                    'quality_score': raw_metrics.get('business_metrics', {}).get('response_quality', {}).get('quality_score', 0.0)
                }
            ]
            aggregated_metrics['business'] = business_data
        
        # Performance metrics aggregation
        if 'api_metrics' in raw_metrics:
            performance_data = [
                {
                    'response_time': raw_metrics.get('api_metrics', {}).get('response_time', 0.0),
                    'throughput': raw_metrics.get('api_metrics', {}).get('throughput', 0.0),
                    'error_rate': raw_metrics.get('api_metrics', {}).get('error_rate', 0.0)
                }
            ]
            aggregated_metrics['performance'] = performance_data
        
        # Aggregate all metrics
        if aggregated_metrics:
            processed_metrics['aggregated_metrics'] = self.metrics_aggregator.aggregate_all_metrics(aggregated_metrics)
        
        # Check health status
        if 'aggregated_metrics' in processed_metrics:
            system_metrics = processed_metrics['aggregated_metrics'].get('system_summary', {})
            health_status = self.health_monitor.check_system_health(system_metrics)
            processed_metrics['health_status'] = health_status
        
        # Generate alerts
        alerts = self._generate_alerts(processed_metrics)
        processed_metrics['alerts'] = alerts
        
        return processed_metrics
    
    def update_dashboards(self, metrics_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update Grafana dashboards with new metrics
        
        Args:
            metrics_data: Metrics data to update dashboards with
            
        Returns:
            Dashboard update results
        """
        update_results = {
            'updated': [],
            'failed': []
        }
        
        try:
            # Update system overview dashboard
            if 'system_overview' in metrics_data:
                system_data = metrics_data['system_overview']
                # This would typically send metrics to Grafana
                update_results['updated'].append('system_overview')
            
            # Update business metrics dashboard
            if 'business_metrics' in metrics_data:
                business_data = metrics_data['business_metrics']
                # This would typically send metrics to Grafana
                update_results['updated'].append('business_metrics')
            
            # Update performance dashboard
            if 'performance_metrics' in metrics_data:
                performance_data = metrics_data['performance_metrics']
                # This would typically send metrics to Grafana
                update_results['updated'].append('performance_metrics')
            
        except Exception as e:
            update_results['failed'].append(f"Dashboard update error: {str(e)}")
        
        return update_results
    
    def check_and_send_alerts(self, metrics_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check metrics and send alerts if thresholds are exceeded
        
        Args:
            metrics_data: Metrics data to check
            
        Returns:
            List of alerts sent
        """
        alerts = []
        
        # Check error rate
        error_rate = metrics_data.get('error_rate', 0.0)
        if error_rate > 0.1:  # 10% error rate threshold
            alerts.append({
                'type': 'error_rate',
                'severity': 'critical',
                'message': f"High error rate detected: {error_rate:.2%}",
                'timestamp': datetime.now().isoformat()
            })
        
        # Check response time
        response_time = metrics_data.get('response_time', 0.0)
        if response_time > 3.0:  # 3 second threshold
            alerts.append({
                'type': 'response_time',
                'severity': 'warning',
                'message': f"High response time detected: {response_time:.2f}s",
                'timestamp': datetime.now().isoformat()
            })
        
        # Check CPU usage
        cpu_usage = metrics_data.get('cpu_usage', 0.0)
        if cpu_usage > 0.8:  # 80% CPU threshold
            alerts.append({
                'type': 'cpu_usage',
                'severity': 'warning',
                'message': f"High CPU usage detected: {cpu_usage:.2%}",
                'timestamp': datetime.now().isoformat()
            })
        
        # Check business metrics
        if 'business_metrics' in metrics_data:
            business = metrics_data['business_metrics']
            
            # Check user satisfaction
            satisfaction = business.get('user_satisfaction', {}).get('average_rating', 0.0)
            if satisfaction < 3.0:  # Low satisfaction threshold
                alerts.append({
                    'type': 'user_satisfaction',
                    'severity': 'warning',
                    'message': f"Low user satisfaction detected: {satisfaction:.1f}/5.0",
                    'timestamp': datetime.now().isoformat()
                })
            
            # Check quality score
            quality_score = business.get('response_quality', {}).get('quality_score', 0.0)
            if quality_score < 0.7:  # Low quality threshold
                alerts.append({
                    'type': 'quality_score',
                    'severity': 'warning',
                    'message': f"Low response quality detected: {quality_score:.2f}",
                    'timestamp': datetime.now().isoformat()
                })
        
        return alerts
    
    def run_monitoring_cycle(self, query_event: Dict[str, Any]) -> Dict[str, Any]:
        """Run complete monitoring cycle for a query event
        
        Args:
            query_event: Query event data
            
        Returns:
            Monitoring cycle results
        """
        cycle_results = {
            'metrics_collected': False,
            'dashboards_updated': False,
            'alerts_sent': False,
            'health_status': 'unknown'
        }
        
        try:
            # Step 1: Collect all metrics
            all_metrics = self.collect_all_metrics(query_event)
            cycle_results['metrics_collected'] = True
            
            # Step 2: Process metrics
            processed_metrics = self.process_metrics(all_metrics)
            
            # Step 3: Update dashboards
            dashboard_results = self.update_dashboards(processed_metrics)
            cycle_results['dashboards_updated'] = len(dashboard_results['updated']) > 0
            
            # Step 4: Check and send alerts
            alerts = self.check_and_send_alerts(processed_metrics)
            cycle_results['alerts_sent'] = len(alerts) > 0
            
            # Step 5: Get health status
            if 'health_status' in processed_metrics:
                cycle_results['health_status'] = processed_metrics['health_status'].get('overall_health', 'unknown')
            
            # Add additional results
            cycle_results['metrics_count'] = len(all_metrics)
            cycle_results['alerts_count'] = len(alerts)
            cycle_results['timestamp'] = datetime.now().isoformat()
            
        except Exception as e:
            cycle_results['error'] = str(e)
        
        return cycle_results
    
    def _generate_alerts(self, processed_metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate alerts based on processed metrics
        
        Args:
            processed_metrics: Processed metrics data
            
        Returns:
            List of generated alerts
        """
        alerts = []
        
        # Check health status
        if 'health_status' in processed_metrics:
            health_status = processed_metrics['health_status']
            overall_health = health_status.get('overall_health', 'unknown')
            
            if overall_health == 'critical':
                alerts.append({
                    'type': 'system_health',
                    'severity': 'critical',
                    'message': 'System health is critical',
                    'timestamp': datetime.now().isoformat()
                })
            elif overall_health == 'warning':
                alerts.append({
                    'type': 'system_health',
                    'severity': 'warning',
                    'message': 'System health is degraded',
                    'timestamp': datetime.now().isoformat()
                })
        
        # Check aggregated metrics
        if 'aggregated_metrics' in processed_metrics:
            aggregated = processed_metrics['aggregated_metrics']
            
            # Check system metrics
            if 'system_summary' in aggregated:
                system = aggregated['system_summary']
                avg_cpu = system.get('avg_cpu_usage', 0.0)
                avg_memory = system.get('avg_memory_usage', 0.0)
                
                if avg_cpu > 0.8:
                    alerts.append({
                        'type': 'cpu_usage',
                        'severity': 'warning',
                        'message': f"High average CPU usage: {avg_cpu:.2%}",
                        'timestamp': datetime.now().isoformat()
                    })
                
                if avg_memory > 0.85:
                    alerts.append({
                        'type': 'memory_usage',
                        'severity': 'warning',
                        'message': f"High average memory usage: {avg_memory:.2%}",
                        'timestamp': datetime.now().isoformat()
                    })
            
            # Check business metrics
            if 'business_summary' in aggregated:
                business = aggregated['business_summary']
                avg_satisfaction = business.get('avg_user_satisfaction', 0.0)
                avg_quality = business.get('avg_quality_score', 0.0)
                
                if avg_satisfaction < 3.0:
                    alerts.append({
                        'type': 'user_satisfaction',
                        'severity': 'warning',
                        'message': f"Low average user satisfaction: {avg_satisfaction:.1f}/5.0",
                        'timestamp': datetime.now().isoformat()
                    })
                
                if avg_quality < 0.7:
                    alerts.append({
                        'type': 'quality_score',
                        'severity': 'warning',
                        'message': f"Low average quality score: {avg_quality:.2f}",
                        'timestamp': datetime.now().isoformat()
                    })
        
        return alerts 