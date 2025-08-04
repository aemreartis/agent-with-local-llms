"""
Cost Analyzer

Analyzes costs, calculates efficiency metrics, and provides optimization suggestions.
"""

import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional


class CostAnalyzer:
    """Analyzes costs and provides optimization insights"""
    
    def __init__(self):
        """Initialize cost analyzer"""
        self.cost_history = []  # List of cost records
        self.cost_rates = {
            'llm_token': 0.0001,  # Cost per token
            'vector_query': 0.001,  # Cost per vector search
            'api_call': 0.01,     # Cost per API call
            'processing_time': 0.001  # Cost per second of processing
        }
    
    def calculate_query_cost(self, query_data: Dict[str, Any]) -> float:
        """Calculate cost for a single query
        
        Args:
            query_data: Query cost components
            
        Returns:
            Total cost for the query
        """
        total_cost = 0.0
        
        # LLM token cost
        llm_tokens = query_data.get('llm_tokens', 0)
        total_cost += llm_tokens * self.cost_rates['llm_token']
        
        # Vector query cost
        vector_queries = query_data.get('vector_queries', 0)
        total_cost += vector_queries * self.cost_rates['vector_query']
        
        # API call cost
        api_calls = query_data.get('api_calls', 0)
        total_cost += api_calls * self.cost_rates['api_call']
        
        # Processing time cost
        processing_time = query_data.get('processing_time', 0)
        total_cost += processing_time * self.cost_rates['processing_time']
        
        return total_cost
    
    def record_cost(self, query_id: str, cost: float, metadata: Dict[str, Any] = None):
        """Record cost for a query
        
        Args:
            query_id: Query identifier
            cost: Total cost
            metadata: Additional cost metadata
        """
        cost_record = {
            'query_id': query_id,
            'cost': cost,
            'timestamp': datetime.now(),
            'metadata': metadata or {}
        }
        
        self.cost_history.append(cost_record)
    
    def calculate_cost_efficiency(self, cost_data: Dict[str, Any]) -> float:
        """Calculate cost efficiency score
        
        Args:
            cost_data: Cost and performance data
            
        Returns:
            Efficiency score between 0 and 1 (higher = more efficient)
        """
        total_cost = cost_data.get('total_cost', 0)
        queries_processed = cost_data.get('queries_processed', 1)
        quality_score = cost_data.get('quality_score', 0.5)
        user_satisfaction = cost_data.get('user_satisfaction', 2.5)
        
        if total_cost == 0 or queries_processed == 0:
            return 0.0
        
        # Calculate cost per query
        cost_per_query = total_cost / queries_processed
        
        # Normalize cost per query (assume $0.01 is baseline)
        normalized_cost = min(1.0, cost_per_query / 0.01)
        
        # Calculate efficiency components
        cost_efficiency = 1.0 - normalized_cost
        quality_efficiency = quality_score
        satisfaction_efficiency = user_satisfaction / 5.0
        
        # Weighted average
        efficiency_score = (
            cost_efficiency * 0.4 +
            quality_efficiency * 0.4 +
            satisfaction_efficiency * 0.2
        )
        
        return min(1.0, max(0.0, efficiency_score))
    
    def analyze_cost_trends(self) -> Dict[str, Any]:
        """Analyze cost trends over time
        
        Returns:
            Dictionary with trend analysis
        """
        if not self.cost_history:
            return {
                'average_cost': 0.0,
                'cost_trend': 'stable',
                'cost_variance': 0.0,
                'total_queries': 0
            }
        
        costs = [record['cost'] for record in self.cost_history]
        
        average_cost = statistics.mean(costs)
        cost_variance = statistics.variance(costs) if len(costs) > 1 else 0.0
        
        # Calculate trend
        if len(costs) >= 2:
            recent_costs = costs[-10:]  # Last 10 costs
            older_costs = costs[:-10] if len(costs) > 10 else costs
            
            if len(older_costs) > 0:
                recent_avg = statistics.mean(recent_costs)
                older_avg = statistics.mean(older_costs)
                
                if recent_avg > older_avg * 1.2:
                    cost_trend = 'increasing'
                elif recent_avg < older_avg * 0.8:
                    cost_trend = 'decreasing'
                else:
                    cost_trend = 'stable'
            else:
                cost_trend = 'stable'
        else:
            cost_trend = 'stable'
        
        return {
            'average_cost': average_cost,
            'cost_trend': cost_trend,
            'cost_variance': cost_variance,
            'total_queries': len(costs)
        }
    
    def optimize_costs(self, current_config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate cost optimization suggestions
        
        Args:
            current_config: Current system configuration
            
        Returns:
            List of optimization suggestions
        """
        suggestions = []
        
        # Analyze current configuration
        llm_model = current_config.get('llm_model', 'unknown')
        vector_search_limit = current_config.get('vector_search_limit', 10)
        reranking_enabled = current_config.get('reranking_enabled', True)
        
        # LLM model optimization
        if 'llama-2-7b' in llm_model.lower():
            suggestions.append({
                'category': 'llm_model',
                'suggestion': 'Consider using a smaller model like llama-2-3b for cost reduction',
                'potential_savings': '30-50%',
                'impact': 'medium'
            })
        elif 'gpt' in llm_model.lower():
            suggestions.append({
                'category': 'llm_model',
                'suggestion': 'Consider switching to local models for cost reduction',
                'potential_savings': '70-90%',
                'impact': 'high'
            })
        
        # Vector search optimization
        if vector_search_limit > 5:
            suggestions.append({
                'category': 'vector_search',
                'suggestion': f'Reduce vector search limit from {vector_search_limit} to 5',
                'potential_savings': '20-30%',
                'impact': 'low'
            })
        
        # Reranking optimization
        if reranking_enabled:
            suggestions.append({
                'category': 'reranking',
                'suggestion': 'Disable reranking for non-critical queries',
                'potential_savings': '15-25%',
                'impact': 'medium'
            })
        
        # General suggestions
        suggestions.append({
            'category': 'caching',
            'suggestion': 'Implement response caching for repeated queries',
            'potential_savings': '40-60%',
            'impact': 'high'
        })
        
        suggestions.append({
            'category': 'batching',
            'suggestion': 'Batch similar queries together',
            'potential_savings': '20-30%',
            'impact': 'medium'
        })
        
        return suggestions
    
    def get_cost_breakdown(self, time_period: str = '24h') -> Dict[str, Any]:
        """Get cost breakdown for a time period
        
        Args:
            time_period: Time period to analyze ('1h', '24h', '7d', '30d')
            
        Returns:
            Cost breakdown dictionary
        """
        if not self.cost_history:
            return {
                'total_cost': 0.0,
                'query_count': 0,
                'cost_by_component': {},
                'cost_by_time': {}
            }
        
        # Calculate time threshold
        now = datetime.now()
        if time_period == '1h':
            threshold = now - timedelta(hours=1)
        elif time_period == '24h':
            threshold = now - timedelta(days=1)
        elif time_period == '7d':
            threshold = now - timedelta(days=7)
        elif time_period == '30d':
            threshold = now - timedelta(days=30)
        else:
            threshold = now - timedelta(days=1)  # Default to 24h
        
        # Filter records by time
        recent_records = [
            record for record in self.cost_history
            if record['timestamp'] >= threshold
        ]
        
        if not recent_records:
            return {
                'total_cost': 0.0,
                'query_count': 0,
                'cost_by_component': {},
                'cost_by_time': {}
            }
        
        # Calculate totals
        total_cost = sum(record['cost'] for record in recent_records)
        query_count = len(recent_records)
        
        # Cost by component
        cost_by_component = {
            'llm_tokens': 0.0,
            'vector_queries': 0.0,
            'api_calls': 0.0,
            'processing_time': 0.0
        }
        
        for record in recent_records:
            metadata = record.get('metadata', {})
            cost_by_component['llm_tokens'] += metadata.get('llm_token_cost', 0)
            cost_by_component['vector_queries'] += metadata.get('vector_query_cost', 0)
            cost_by_component['api_calls'] += metadata.get('api_call_cost', 0)
            cost_by_component['processing_time'] += metadata.get('processing_cost', 0)
        
        # Cost by time (hourly breakdown for 24h)
        cost_by_time = {}
        if time_period == '24h':
            for i in range(24):
                hour_start = now - timedelta(hours=i+1)
                hour_end = now - timedelta(hours=i)
                
                hour_records = [
                    record for record in recent_records
                    if hour_start <= record['timestamp'] < hour_end
                ]
                
                hour_cost = sum(record['cost'] for record in hour_records)
                cost_by_time[f'hour_{i}'] = hour_cost
        
        return {
            'total_cost': total_cost,
            'query_count': query_count,
            'average_cost_per_query': total_cost / query_count if query_count > 0 else 0.0,
            'cost_by_component': cost_by_component,
            'cost_by_time': cost_by_time
        }
    
    def predict_costs(self, query_volume: int, time_period: str = '24h') -> Dict[str, Any]:
        """Predict costs for future query volume
        
        Args:
            query_volume: Expected number of queries
            time_period: Time period for prediction
            
        Returns:
            Cost prediction dictionary
        """
        if not self.cost_history:
            return {
                'predicted_cost': 0.0,
                'confidence': 'low',
                'assumptions': ['No historical data available']
            }
        
        # Calculate average cost per query
        costs = [record['cost'] for record in self.cost_history]
        avg_cost_per_query = statistics.mean(costs)
        
        # Calculate confidence based on variance
        if len(costs) > 1:
            variance = statistics.variance(costs)
            confidence = 'high' if variance < 0.001 else 'medium' if variance < 0.01 else 'low'
        else:
            confidence = 'low'
        
        # Predict total cost
        predicted_cost = avg_cost_per_query * query_volume
        
        # Calculate range based on variance
        if len(costs) > 1:
            std_dev = statistics.stdev(costs)
            cost_range = (predicted_cost - std_dev, predicted_cost + std_dev)
        else:
            cost_range = (predicted_cost * 0.5, predicted_cost * 1.5)
        
        return {
            'predicted_cost': predicted_cost,
            'cost_range': cost_range,
            'confidence': confidence,
            'avg_cost_per_query': avg_cost_per_query,
            'assumptions': [
                'Query patterns remain similar',
                'No major configuration changes',
                'System performance remains stable'
            ]
        } 