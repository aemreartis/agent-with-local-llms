"""
System Health Monitor

Monitors system health, component health, and predicts potential issues.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional


class SystemHealthMonitor:
    """Monitors system and component health"""
    
    def __init__(self):
        """Initialize health monitor"""
        self.health_thresholds = {
            'cpu_usage': 0.8,
            'memory_usage': 0.85,
            'disk_usage': 0.9,
            'error_rate': 0.05,
            'response_time': 5.0
        }
        self.health_history = []
    
    def check_system_health(self, system_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Check overall system health
        
        Args:
            system_metrics: System metrics dictionary
            
        Returns:
            Health status dictionary
        """
        health_checks = {}
        alerts = []
        
        # Check CPU usage
        cpu_usage = system_metrics.get('cpu_usage', 0.0)
        if cpu_usage > self.health_thresholds['cpu_usage']:
            health_checks['cpu'] = 'warning'
            alerts.append(f"High CPU usage: {cpu_usage:.2%}")
        elif cpu_usage > self.health_thresholds['cpu_usage'] * 0.8:
            health_checks['cpu'] = 'monitoring'
        else:
            health_checks['cpu'] = 'healthy'
        
        # Check memory usage
        memory_usage = system_metrics.get('memory_usage', 0.0)
        if memory_usage > self.health_thresholds['memory_usage']:
            health_checks['memory'] = 'warning'
            alerts.append(f"High memory usage: {memory_usage:.2%}")
        elif memory_usage > self.health_thresholds['memory_usage'] * 0.8:
            health_checks['memory'] = 'monitoring'
        else:
            health_checks['memory'] = 'healthy'
        
        # Check disk usage
        disk_usage = system_metrics.get('disk_usage', 0.0)
        if disk_usage > self.health_thresholds['disk_usage']:
            health_checks['disk'] = 'warning'
            alerts.append(f"High disk usage: {disk_usage:.2%}")
        elif disk_usage > self.health_thresholds['disk_usage'] * 0.8:
            health_checks['disk'] = 'monitoring'
        else:
            health_checks['disk'] = 'healthy'
        
        # Check error rate
        error_rate = system_metrics.get('error_rate', 0.0)
        if error_rate > self.health_thresholds['error_rate']:
            health_checks['errors'] = 'critical'
            alerts.append(f"High error rate: {error_rate:.2%}")
        elif error_rate > self.health_thresholds['error_rate'] * 0.5:
            health_checks['errors'] = 'warning'
        else:
            health_checks['errors'] = 'healthy'
        
        # Determine overall health
        overall_health = self._determine_overall_health(health_checks)
        
        # Record health check
        health_record = {
            'timestamp': datetime.now(),
            'overall_health': overall_health,
            'component_health': health_checks,
            'alerts': alerts,
            'metrics': system_metrics
        }
        self.health_history.append(health_record)
        
        return {
            'overall_health': overall_health,
            'component_health': health_checks,
            'alerts': alerts,
            'timestamp': datetime.now().isoformat()
        }
    
    def check_component_health(self, component_metrics: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Check health of individual components
        
        Args:
            component_metrics: Dictionary of component metrics
            
        Returns:
            Component health status dictionary
        """
        component_health = {}
        alerts = []
        
        for component_name, metrics in component_metrics.items():
            component_status = 'healthy'
            component_alerts = []
            
            # Check error rate
            error_rate = metrics.get('error_rate', 0.0)
            if error_rate > self.health_thresholds['error_rate']:
                component_status = 'critical'
                component_alerts.append(f"High error rate: {error_rate:.2%}")
            elif error_rate > self.health_thresholds['error_rate'] * 0.5:
                component_status = 'warning'
            
            # Check response time
            response_time = metrics.get('response_time', 0.0)
            if response_time > self.health_thresholds['response_time']:
                component_status = 'warning'
                component_alerts.append(f"High response time: {response_time:.2f}s")
            
            # Check component-specific metrics
            if component_name == 'llm_provider':
                # Check LLM-specific metrics
                if 'model_loading_time' in metrics and metrics['model_loading_time'] > 30:
                    component_alerts.append("Slow model loading")
            
            elif component_name == 'vector_store':
                # Check vector store-specific metrics
                if 'index_size' in metrics and metrics['index_size'] > 10**9:  # 1GB
                    component_alerts.append("Large index size")
            
            elif component_name == 'memory_provider':
                # Check memory provider-specific metrics
                cache_hit_rate = metrics.get('cache_hit_rate', 1.0)
                if cache_hit_rate < 0.7:
                    component_alerts.append(f"Low cache hit rate: {cache_hit_rate:.2%}")
            
            component_health[component_name] = {
                'status': component_status,
                'alerts': component_alerts
            }
            
            if component_alerts:
                alerts.extend([f"{component_name}: {alert}" for alert in component_alerts])
        
        return {
            'component_health': component_health,
            'alerts': alerts,
            'timestamp': datetime.now().isoformat()
        }
    
    def generate_health_report(self, health_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive health report
        
        Args:
            health_data: Health status data
            
        Returns:
            Health report dictionary
        """
        overall_health = health_data.get('system_health', 'unknown')
        component_health = health_data.get('component_health', {})
        alerts = health_data.get('alerts', [])
        
        # Generate summary
        healthy_components = sum(1 for status in component_health.values() if status == 'healthy')
        total_components = len(component_health) if component_health else 1
        health_percentage = (healthy_components / total_components) * 100
        
        # Generate recommendations
        recommendations = self._generate_recommendations(health_data)
        
        # Calculate trend
        trend = self._calculate_health_trend()
        
        return {
            'summary': {
                'overall_health': overall_health,
                'health_percentage': health_percentage,
                'healthy_components': healthy_components,
                'total_components': total_components,
                'alert_count': len(alerts)
            },
            'details': {
                'component_health': component_health,
                'alerts': alerts,
                'trend': trend
            },
            'recommendations': recommendations,
            'timestamp': datetime.now().isoformat()
        }
    
    def predict_health_issues(self, historical_metrics: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Predict potential health issues based on historical data
        
        Args:
            historical_metrics: List of historical metric records
            
        Returns:
            Prediction results dictionary
        """
        if len(historical_metrics) < 3:
            return {
                'predicted_issues': [],
                'confidence': 'low',
                'timeframe': 'unknown',
                'reason': 'Insufficient historical data'
            }
        
        predictions = []
        confidence_factors = []
        
        # Analyze CPU trends
        cpu_trend = self._analyze_metric_trend(historical_metrics, 'cpu_usage')
        if cpu_trend['direction'] == 'increasing' and cpu_trend['slope'] > 0.1:
            predictions.append({
                'component': 'cpu',
                'issue': 'CPU usage trending upward',
                'severity': 'medium',
                'timeframe': '24-48 hours',
                'confidence': cpu_trend['confidence']
            })
            confidence_factors.append(cpu_trend['confidence'])
        
        # Analyze memory trends
        memory_trend = self._analyze_metric_trend(historical_metrics, 'memory_usage')
        if memory_trend['direction'] == 'increasing' and memory_trend['slope'] > 0.05:
            predictions.append({
                'component': 'memory',
                'issue': 'Memory usage trending upward',
                'severity': 'high',
                'timeframe': '12-24 hours',
                'confidence': memory_trend['confidence']
            })
            confidence_factors.append(memory_trend['confidence'])
        
        # Analyze error rate trends
        error_trend = self._analyze_metric_trend(historical_metrics, 'error_rate')
        if error_trend['direction'] == 'increasing' and error_trend['slope'] > 0.01:
            predictions.append({
                'component': 'errors',
                'issue': 'Error rate trending upward',
                'severity': 'critical',
                'timeframe': '6-12 hours',
                'confidence': error_trend['confidence']
            })
            confidence_factors.append(error_trend['confidence'])
        
        # Calculate overall confidence
        overall_confidence = 'low'
        if confidence_factors:
            avg_confidence = sum(1 if c == 'high' else 0.5 if c == 'medium' else 0 for c in confidence_factors) / len(confidence_factors)
            if avg_confidence > 0.7:
                overall_confidence = 'high'
            elif avg_confidence > 0.4:
                overall_confidence = 'medium'
        
        return {
            'predicted_issues': predictions,
            'confidence': overall_confidence,
            'timeframe': '6-48 hours',
            'analysis_timestamp': datetime.now().isoformat()
        }
    
    def _determine_overall_health(self, component_health: Dict[str, str]) -> str:
        """Determine overall health based on component health
        
        Args:
            component_health: Dictionary of component health statuses
            
        Returns:
            Overall health status
        """
        if not component_health:
            return 'unknown'
        
        status_counts = {}
        for status in component_health.values():
            status_counts[status] = status_counts.get(status, 0) + 1
        
        # Priority: critical > warning > monitoring > healthy
        if status_counts.get('critical', 0) > 0:
            return 'critical'
        elif status_counts.get('warning', 0) > 0:
            return 'warning'
        elif status_counts.get('monitoring', 0) > 0:
            return 'monitoring'
        else:
            return 'healthy'
    
    def _generate_recommendations(self, health_data: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on health data
        
        Args:
            health_data: Health status data
            
        Returns:
            List of recommendations
        """
        recommendations = []
        component_health = health_data.get('component_health', {})
        alerts = health_data.get('alerts', [])
        
        # CPU recommendations
        if any('CPU' in alert for alert in alerts):
            recommendations.append("Consider scaling up CPU resources or optimizing workload distribution")
        
        # Memory recommendations
        if any('memory' in alert.lower() for alert in alerts):
            recommendations.append("Consider increasing memory allocation or implementing memory optimization")
        
        # Disk recommendations
        if any('disk' in alert.lower() for alert in alerts):
            recommendations.append("Consider disk cleanup or storage expansion")
        
        # Error rate recommendations
        if any('error' in alert.lower() for alert in alerts):
            recommendations.append("Investigate error sources and implement error handling improvements")
        
        # General recommendations
        if len(alerts) > 3:
            recommendations.append("Consider comprehensive system review and optimization")
        
        if not recommendations:
            recommendations.append("System is healthy - continue monitoring")
        
        return recommendations
    
    def _calculate_health_trend(self) -> Dict[str, Any]:
        """Calculate health trend over time
        
        Returns:
            Health trend analysis
        """
        if len(self.health_history) < 2:
            return {
                'direction': 'stable',
                'confidence': 'low',
                'data_points': len(self.health_history)
            }
        
        # Analyze recent health history
        recent_health = self.health_history[-10:]  # Last 10 health checks
        
        health_scores = []
        for record in recent_health:
            health = record['overall_health']
            if health == 'healthy':
                score = 1.0
            elif health == 'monitoring':
                score = 0.7
            elif health == 'warning':
                score = 0.4
            else:  # critical
                score = 0.1
            health_scores.append(score)
        
        # Calculate trend
        if len(health_scores) >= 2:
            recent_avg = sum(health_scores[-3:]) / min(3, len(health_scores))
            older_avg = sum(health_scores[:-3]) / max(1, len(health_scores) - 3)
            
            if recent_avg > older_avg + 0.2:
                direction = 'improving'
            elif recent_avg < older_avg - 0.2:
                direction = 'declining'
            else:
                direction = 'stable'
        else:
            direction = 'stable'
        
        return {
            'direction': direction,
            'confidence': 'medium' if len(health_scores) >= 5 else 'low',
            'data_points': len(health_scores)
        }
    
    def _analyze_metric_trend(self, historical_metrics: List[Dict[str, Any]], metric_name: str) -> Dict[str, Any]:
        """Analyze trend for a specific metric
        
        Args:
            historical_metrics: List of historical metric records
            metric_name: Name of the metric to analyze
            
        Returns:
            Trend analysis dictionary
        """
        values = [m.get(metric_name, 0.0) for m in historical_metrics if metric_name in m]
        
        if len(values) < 2:
            return {
                'direction': 'stable',
                'slope': 0.0,
                'confidence': 'low'
            }
        
        # Simple linear trend calculation
        n = len(values)
        x_values = list(range(n))
        
        # Calculate slope
        sum_x = sum(x_values)
        sum_y = sum(values)
        sum_xy = sum(x * y for x, y in zip(x_values, values))
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
        
        # Calculate confidence
        variance = sum((v - sum_y/n) ** 2 for v in values) / n if n > 1 else 0.0
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