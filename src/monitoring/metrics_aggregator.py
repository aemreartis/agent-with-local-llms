"""
Metrics Aggregator

Aggregates metrics from different sources and calculates trends and summaries.
"""

import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional


class MetricsAggregator:
    """Aggregates and analyzes metrics from multiple sources"""
    
    def __init__(self):
        """Initialize metrics aggregator"""
        self.aggregation_rules = {
            'system': ['cpu_usage', 'memory_usage', 'disk_usage'],
            'business': ['user_satisfaction', 'cost_per_query', 'quality_score'],
            'performance': ['response_time', 'throughput', 'error_rate']
        }
        self.time_windows = {
            '1h': timedelta(hours=1),
            '24h': timedelta(days=1),
            '7d': timedelta(days=7),
            '30d': timedelta(days=30)
        }
    
    def aggregate_system_metrics(self, system_metrics: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Aggregate system metrics
        
        Args:
            system_metrics: List of system metric records
            
        Returns:
            Aggregated system metrics
        """
        if not system_metrics:
            return {
                'avg_cpu_usage': 0.0,
                'avg_memory_usage': 0.0,
                'max_cpu_usage': 0.0,
                'max_memory_usage': 0.0,
                'min_cpu_usage': 0.0,
                'min_memory_usage': 0.0
            }
        
        # Extract metrics
        cpu_usages = [m.get('cpu_usage', 0.0) for m in system_metrics]
        memory_usages = [m.get('memory_usage', 0.0) for m in system_metrics]
        disk_usages = [m.get('disk_usage', 0.0) for m in system_metrics]
        
        return {
            'avg_cpu_usage': statistics.mean(cpu_usages),
            'avg_memory_usage': statistics.mean(memory_usages),
            'avg_disk_usage': statistics.mean(disk_usages),
            'max_cpu_usage': max(cpu_usages),
            'max_memory_usage': max(memory_usages),
            'max_disk_usage': max(disk_usages),
            'min_cpu_usage': min(cpu_usages),
            'min_memory_usage': min(memory_usages),
            'min_disk_usage': min(disk_usages),
            'cpu_variance': statistics.variance(cpu_usages) if len(cpu_usages) > 1 else 0.0,
            'memory_variance': statistics.variance(memory_usages) if len(memory_usages) > 1 else 0.0,
            'disk_variance': statistics.variance(disk_usages) if len(disk_usages) > 1 else 0.0
        }
    
    def aggregate_business_metrics(self, business_metrics: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Aggregate business metrics
        
        Args:
            business_metrics: List of business metric records
            
        Returns:
            Aggregated business metrics
        """
        if not business_metrics:
            return {
                'avg_user_satisfaction': 0.0,
                'avg_cost_per_query': 0.0,
                'satisfaction_trend': 'stable',
                'cost_trend': 'stable'
            }
        
        # Extract metrics
        user_satisfactions = [m.get('user_satisfaction', 0.0) for m in business_metrics]
        cost_per_queries = [m.get('cost_per_query', 0.0) for m in business_metrics]
        quality_scores = [m.get('quality_score', 0.0) for m in business_metrics]
        
        # Calculate trends
        satisfaction_trend = self.calculate_trend(user_satisfactions)
        cost_trend = self.calculate_trend(cost_per_queries)
        quality_trend = self.calculate_trend(quality_scores)
        
        return {
            'avg_user_satisfaction': statistics.mean(user_satisfactions),
            'avg_cost_per_query': statistics.mean(cost_per_queries),
            'avg_quality_score': statistics.mean(quality_scores),
            'satisfaction_trend': satisfaction_trend,
            'cost_trend': cost_trend,
            'quality_trend': quality_trend,
            'satisfaction_variance': statistics.variance(user_satisfactions) if len(user_satisfactions) > 1 else 0.0,
            'cost_variance': statistics.variance(cost_per_queries) if len(cost_per_queries) > 1 else 0.0,
            'quality_variance': statistics.variance(quality_scores) if len(quality_scores) > 1 else 0.0
        }
    
    def aggregate_performance_metrics(self, performance_metrics: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Aggregate performance metrics
        
        Args:
            performance_metrics: List of performance metric records
            
        Returns:
            Aggregated performance metrics
        """
        if not performance_metrics:
            return {
                'avg_response_time': 0.0,
                'avg_throughput': 0.0,
                'p95_response_time': 0.0,
                'performance_trend': 'stable'
            }
        
        # Extract metrics
        response_times = [m.get('response_time', 0.0) for m in performance_metrics]
        throughputs = [m.get('throughput', 0.0) for m in performance_metrics]
        error_rates = [m.get('error_rate', 0.0) for m in performance_metrics]
        
        # Calculate percentiles
        response_times_sorted = sorted(response_times)
        p95_index = int(len(response_times_sorted) * 0.95)
        p95_response_time = response_times_sorted[p95_index] if response_times_sorted else 0.0
        
        # Calculate trends
        response_time_trend = self.calculate_trend(response_times)
        throughput_trend = self.calculate_trend(throughputs)
        error_rate_trend = self.calculate_trend(error_rates)
        
        return {
            'avg_response_time': statistics.mean(response_times),
            'avg_throughput': statistics.mean(throughputs),
            'avg_error_rate': statistics.mean(error_rates),
            'p95_response_time': p95_response_time,
            'p99_response_time': response_times_sorted[int(len(response_times_sorted) * 0.99)] if response_times_sorted else 0.0,
            'performance_trend': response_time_trend,
            'response_time_trend': response_time_trend,
            'throughput_trend': throughput_trend,
            'error_rate_trend': error_rate_trend,
            'response_time_variance': statistics.variance(response_times) if len(response_times) > 1 else 0.0,
            'throughput_variance': statistics.variance(throughputs) if len(throughputs) > 1 else 0.0,
            'error_rate_variance': statistics.variance(error_rates) if len(error_rates) > 1 else 0.0
        }
    
    def calculate_trend(self, time_series_data: List[float]) -> Dict[str, Any]:
        """Calculate trend for a time series
        
        Args:
            time_series_data: List of numeric values
            
        Returns:
            Trend analysis dictionary
        """
        if len(time_series_data) < 2:
            return {
                'direction': 'stable',
                'slope': 0.0,
                'confidence': 'low'
            }
        
        # Simple linear trend calculation
        n = len(time_series_data)
        x_values = list(range(n))
        
        # Calculate slope using least squares
        sum_x = sum(x_values)
        sum_y = sum(time_series_data)
        sum_xy = sum(x * y for x, y in zip(x_values, time_series_data))
        sum_x2 = sum(x * x for x in x_values)
        
        if n * sum_x2 - sum_x * sum_x == 0:
            slope = 0.0
        else:
            slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
        
        # Determine direction
        if abs(slope) < 0.01:
            direction = 'stable'
        elif slope > 0:
            direction = 'increasing'
        else:
            direction = 'decreasing'
        
        # Calculate confidence based on variance
        variance = statistics.variance(time_series_data) if len(time_series_data) > 1 else 0.0
        if variance < 0.01:
            confidence = 'high'
        elif variance < 0.1:
            confidence = 'medium'
        else:
            confidence = 'low'
        
        return {
            'direction': direction,
            'slope': slope,
            'confidence': confidence,
            'variance': variance
        }
    
    def aggregate_all_metrics(self, all_metrics: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
        """Aggregate all metrics from different sources
        
        Args:
            all_metrics: Dictionary with metrics by category
            
        Returns:
            Complete aggregated metrics
        """
        aggregated = {}
        
        # Aggregate system metrics
        if 'system' in all_metrics:
            aggregated['system_summary'] = self.aggregate_system_metrics(all_metrics['system'])
        
        # Aggregate business metrics
        if 'business' in all_metrics:
            aggregated['business_summary'] = self.aggregate_business_metrics(all_metrics['business'])
        
        # Aggregate performance metrics
        if 'performance' in all_metrics:
            aggregated['performance_summary'] = self.aggregate_performance_metrics(all_metrics['performance'])
        
        # Calculate overall health score
        overall_health = self._calculate_overall_health(aggregated)
        aggregated['overall_health'] = overall_health
        
        return aggregated
    
    def _calculate_overall_health(self, aggregated_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate overall system health
        
        Args:
            aggregated_metrics: Aggregated metrics from all sources
            
        Returns:
            Overall health assessment
        """
        health_scores = []
        health_factors = []
        
        # System health (30% weight)
        if 'system_summary' in aggregated_metrics:
            system = aggregated_metrics['system_summary']
            cpu_health = 1.0 - min(1.0, system.get('avg_cpu_usage', 0.0))
            memory_health = 1.0 - min(1.0, system.get('avg_memory_usage', 0.0))
            system_health = (cpu_health + memory_health) / 2.0
            health_scores.append(system_health * 0.3)
            health_factors.append(f"System: {system_health:.2f}")
        
        # Business health (40% weight)
        if 'business_summary' in aggregated_metrics:
            business = aggregated_metrics['business_summary']
            satisfaction_health = min(1.0, business.get('avg_user_satisfaction', 0.0) / 5.0)
            quality_health = business.get('avg_quality_score', 0.0)
            business_health = (satisfaction_health + quality_health) / 2.0
            health_scores.append(business_health * 0.4)
            health_factors.append(f"Business: {business_health:.2f}")
        
        # Performance health (30% weight)
        if 'performance_summary' in aggregated_metrics:
            performance = aggregated_metrics['performance_summary']
            response_time_health = max(0.0, 1.0 - min(1.0, performance.get('avg_response_time', 0.0) / 5.0))
            error_rate_health = max(0.0, 1.0 - min(1.0, performance.get('avg_error_rate', 0.0) / 0.1))
            performance_health = (response_time_health + error_rate_health) / 2.0
            health_scores.append(performance_health * 0.3)
            health_factors.append(f"Performance: {performance_health:.2f}")
        
        # Calculate overall health score
        overall_score = sum(health_scores) if health_scores else 0.0
        
        # Determine health status
        if overall_score >= 0.8:
            status = 'excellent'
        elif overall_score >= 0.6:
            status = 'good'
        elif overall_score >= 0.4:
            status = 'fair'
        else:
            status = 'poor'
        
        return {
            'score': overall_score,
            'status': status,
            'factors': health_factors,
            'timestamp': datetime.now().isoformat()
        }
    
    def get_metrics_summary(self, time_window: str = '24h') -> Dict[str, Any]:
        """Get summary of metrics for a time window
        
        Args:
            time_window: Time window for summary ('1h', '24h', '7d', '30d')
            
        Returns:
            Metrics summary
        """
        # This would typically query actual metrics data
        # For now, return a mock summary
        return {
            'time_window': time_window,
            'total_metrics': 0,
            'system_metrics_count': 0,
            'business_metrics_count': 0,
            'performance_metrics_count': 0,
            'last_updated': datetime.now().isoformat()
        } 