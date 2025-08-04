"""
Business Metrics

Collects and aggregates business-related metrics for monitoring and analysis.
"""

from typing import Dict, List, Any
from .quality_scorer import QualityScorer
from .user_satisfaction import UserSatisfactionTracker
from .cost_analyzer import CostAnalyzer
from .metrics_collector import MetricsCollector


class BusinessMetrics:
    """Collects and manages business metrics"""
    
    def __init__(self):
        """Initialize business metrics with components"""
        self.quality_scorer = QualityScorer()
        self.satisfaction_tracker = UserSatisfactionTracker()
        self.cost_analyzer = CostAnalyzer()
        self.metrics_collector = MetricsCollector()
    
    def collect_response_quality_metrics(self, response_data: Dict[str, Any]) -> Dict[str, Any]:
        """Collect response quality metrics
        
        Args:
            response_data: Response data including query, response, sources, user_feedback
            
        Returns:
            Quality metrics dictionary
        """
        query = response_data.get('query', '')
        response = response_data.get('response', '')
        sources = response_data.get('sources', [])
        user_feedback = response_data.get('user_feedback', 0.0)
        
        # Calculate quality scores
        relevance_score = self.quality_scorer.calculate_relevance_score(query, response)
        accuracy_score = self.quality_scorer.calculate_accuracy_score(response, sources)
        completeness_score = self.quality_scorer.calculate_completeness_score(query, response)
        hallucination_score = self.quality_scorer.detect_hallucinations(response, sources)
        
        # Calculate overall quality score
        quality_scores = {
            'relevance': relevance_score,
            'accuracy': accuracy_score,
            'completeness': completeness_score
        }
        overall_quality = self.quality_scorer.calculate_overall_quality_score(quality_scores)
        
        # Normalize user feedback to 0-1 scale
        normalized_feedback = user_feedback / 5.0 if user_feedback > 0 else 0.5
        
        return {
            'quality_score': overall_quality,
            'relevance_score': relevance_score,
            'accuracy_score': accuracy_score,
            'completeness_score': completeness_score,
            'hallucination_score': hallucination_score,
            'user_satisfaction': normalized_feedback,
            'has_sources': len(sources) > 0,
            'source_count': len(sources)
        }
    
    def collect_user_satisfaction_metrics(self, session_data: Dict[str, Any]) -> Dict[str, Any]:
        """Collect user satisfaction metrics
        
        Args:
            session_data: Session data including queries, ratings, completion_rate, time_spent
            
        Returns:
            Satisfaction metrics dictionary
        """
        session_id = session_data.get('session_id', 'unknown')
        queries = session_data.get('queries', [])
        ratings = session_data.get('ratings', [])
        completion_rate = session_data.get('completion_rate', 0.0)
        time_spent = session_data.get('time_spent', 0)
        
        # Calculate average rating
        average_rating = sum(ratings) / len(ratings) if ratings else 0.0
        
        # Calculate engagement score
        engagement_data = {
            'queries_count': len(queries),
            'time_spent': time_spent,
            'completion_rate': completion_rate,
            'return_visits': 0  # Would need additional tracking
        }
        engagement_score = self.satisfaction_tracker.calculate_engagement_score(engagement_data)
        
        # Calculate session satisfaction
        session_satisfaction = self.satisfaction_tracker.calculate_session_satisfaction(session_id)
        
        return {
            'average_rating': average_rating,
            'completion_rate': completion_rate,
            'engagement_score': engagement_score,
            'session_satisfaction': session_satisfaction,
            'query_count': len(queries),
            'time_spent': time_spent,
            'rating_count': len(ratings)
        }
    
    def collect_cost_efficiency_metrics(self, cost_data: Dict[str, Any]) -> Dict[str, Any]:
        """Collect cost efficiency metrics
        
        Args:
            cost_data: Cost data including tokens, queries, API calls, processing time, total cost
            
        Returns:
            Cost efficiency metrics dictionary
        """
        llm_tokens_used = cost_data.get('llm_tokens_used', 0)
        vector_search_queries = cost_data.get('vector_search_queries', 0)
        api_calls = cost_data.get('api_calls', 0)
        processing_time = cost_data.get('processing_time', 0.0)
        total_cost = cost_data.get('total_cost', 0.0)
        
        # Calculate cost per query
        query_count = max(1, api_calls)  # Assume at least 1 query
        cost_per_query = total_cost / query_count
        
        # Calculate tokens per response
        tokens_per_response = llm_tokens_used / query_count if query_count > 0 else 0
        
        # Calculate efficiency score
        efficiency_data = {
            'total_cost': total_cost,
            'queries_processed': query_count,
            'quality_score': 0.8,  # Default quality score
            'user_satisfaction': 4.0  # Default satisfaction score
        }
        efficiency_score = self.cost_analyzer.calculate_cost_efficiency(efficiency_data)
        
        # Analyze cost trends
        cost_trends = self.cost_analyzer.analyze_cost_trends()
        
        return {
            'cost_per_query': cost_per_query,
            'tokens_per_response': tokens_per_response,
            'efficiency_score': efficiency_score,
            'cost_trend': cost_trends.get('cost_trend', 'stable'),
            'total_cost': total_cost,
            'llm_tokens_used': llm_tokens_used,
            'vector_queries': vector_search_queries,
            'api_calls': api_calls,
            'processing_time': processing_time
        }
    
    def collect_business_impact_metrics(self, impact_data: Dict[str, Any]) -> Dict[str, Any]:
        """Collect business impact metrics
        
        Args:
            impact_data: Impact data including queries processed, successful responses, retention, time saved, revenue
            
        Returns:
            Business impact metrics dictionary
        """
        queries_processed = impact_data.get('queries_processed', 0)
        successful_responses = impact_data.get('successful_responses', 0)
        user_retention_rate = impact_data.get('user_retention_rate', 0.0)
        time_saved_per_query = impact_data.get('time_saved_per_query', 0)
        revenue_impact = impact_data.get('revenue_impact', 0.0)
        
        # Calculate success rate
        success_rate = successful_responses / queries_processed if queries_processed > 0 else 0.0
        
        # Calculate total time savings
        total_time_savings = time_saved_per_query * queries_processed
        
        # Calculate ROI score (simplified)
        # Assume baseline cost per query is $0.01
        baseline_cost = queries_processed * 0.01
        roi_score = (revenue_impact - baseline_cost) / baseline_cost if baseline_cost > 0 else 0.0
        
        # Calculate productivity improvement
        productivity_improvement = (time_saved_per_query * queries_processed) / (queries_processed * 60)  # Assume 1 minute baseline
        
        return {
            'success_rate': success_rate,
            'retention_rate': user_retention_rate,
            'time_savings': total_time_savings,
            'roi_score': roi_score,
            'productivity_improvement': productivity_improvement,
            'revenue_impact': revenue_impact,
            'queries_processed': queries_processed,
            'successful_responses': successful_responses
        }
    
    def collect_all_metrics(self, test_data: Dict[str, Any]) -> Dict[str, Any]:
        """Collect all business metrics
        
        Args:
            test_data: Dictionary containing response_data, session_data, cost_data, impact_data
            
        Returns:
            Complete business metrics dictionary
        """
        all_metrics = {}
        
        # Collect response quality metrics
        if 'response_data' in test_data:
            all_metrics['response_quality'] = self.collect_response_quality_metrics(test_data['response_data'])
        
        # Collect user satisfaction metrics
        if 'session_data' in test_data:
            all_metrics['user_satisfaction'] = self.collect_user_satisfaction_metrics(test_data['session_data'])
        
        # Collect cost efficiency metrics
        if 'cost_data' in test_data:
            all_metrics['cost_efficiency'] = self.collect_cost_efficiency_metrics(test_data['cost_data'])
        
        # Collect business impact metrics
        if 'impact_data' in test_data:
            all_metrics['business_impact'] = self.collect_business_impact_metrics(test_data['impact_data'])
        
        # Calculate overall score
        overall_score = self._calculate_overall_score(all_metrics)
        all_metrics['overall_score'] = overall_score
        
        return all_metrics
    
    def _calculate_overall_score(self, metrics: Dict[str, Any]) -> float:
        """Calculate overall business score
        
        Args:
            metrics: Dictionary of all metrics
            
        Returns:
            Overall score between 0 and 1
        """
        scores = []
        weights = []
        
        # Response quality (30% weight)
        if 'response_quality' in metrics:
            quality_score = metrics['response_quality'].get('quality_score', 0.0)
            scores.append(quality_score)
            weights.append(0.3)
        
        # User satisfaction (25% weight)
        if 'user_satisfaction' in metrics:
            satisfaction_score = metrics['user_satisfaction'].get('average_rating', 0.0) / 5.0
            scores.append(satisfaction_score)
            weights.append(0.25)
        
        # Cost efficiency (25% weight)
        if 'cost_efficiency' in metrics:
            efficiency_score = metrics['cost_efficiency'].get('efficiency_score', 0.0)
            scores.append(efficiency_score)
            weights.append(0.25)
        
        # Business impact (20% weight)
        if 'business_impact' in metrics:
            success_rate = metrics['business_impact'].get('success_rate', 0.0)
            retention_rate = metrics['business_impact'].get('retention_rate', 0.0)
            impact_score = (success_rate + retention_rate) / 2.0
            scores.append(impact_score)
            weights.append(0.2)
        
        # Calculate weighted average
        if scores and weights:
            total_weight = sum(weights)
            weighted_sum = sum(score * weight for score, weight in zip(scores, weights))
            return weighted_sum / total_weight
        
        return 0.0
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get summary of all collected metrics
        
        Returns:
            Metrics summary dictionary
        """
        # Get satisfaction trends
        satisfaction_trends = self.satisfaction_tracker.get_satisfaction_trends()
        
        # Get cost trends
        cost_trends = self.cost_analyzer.analyze_cost_trends()
        
        # Get cost breakdown
        cost_breakdown = self.cost_analyzer.get_cost_breakdown('24h')
        
        return {
            'satisfaction_trends': satisfaction_trends,
            'cost_trends': cost_trends,
            'cost_breakdown': cost_breakdown,
            'total_sessions': len(self.satisfaction_tracker.session_data),
            'total_queries': len(self.cost_analyzer.cost_history)
        } 