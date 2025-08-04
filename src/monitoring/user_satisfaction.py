"""
User Satisfaction Tracker

Tracks user satisfaction, ratings, and engagement metrics.
"""

import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional


class UserSatisfactionTracker:
    """Tracks user satisfaction and engagement metrics"""
    
    def __init__(self):
        """Initialize satisfaction tracker"""
        self.rating_history = {}  # session_id -> list of ratings
        self.session_data = {}    # session_id -> session metrics
        self.feedback_history = {}  # session_id -> list of feedback
    
    def record_user_rating(self, session_id: str, query: str, rating: float, feedback: str = "") -> bool:
        """Record user rating for a query
        
        Args:
            session_id: User session identifier
            query: User query
            rating: User rating (1-5 scale)
            feedback: Optional user feedback
            
        Returns:
            True if successfully recorded
        """
        try:
            # Validate rating
            if not (1.0 <= rating <= 5.0):
                return False
            
            # Initialize session data if not exists
            if session_id not in self.rating_history:
                self.rating_history[session_id] = []
                self.session_data[session_id] = {
                    'start_time': datetime.now(),
                    'queries': [],
                    'ratings': [],
                    'total_time': 0
                }
                self.feedback_history[session_id] = []
            
            # Record rating
            self.rating_history[session_id].append({
                'query': query,
                'rating': rating,
                'timestamp': datetime.now()
            })
            
            # Update session data
            self.session_data[session_id]['queries'].append(query)
            self.session_data[session_id]['ratings'].append(rating)
            
            # Record feedback if provided
            if feedback:
                self.feedback_history[session_id].append({
                    'query': query,
                    'feedback': feedback,
                    'timestamp': datetime.now()
                })
            
            return True
            
        except Exception:
            return False
    
    def calculate_session_satisfaction(self, session_id: str) -> float:
        """Calculate average satisfaction for a session
        
        Args:
            session_id: User session identifier
            
        Returns:
            Average satisfaction score (1-5 scale)
        """
        if session_id not in self.rating_history:
            return 0.0
        
        ratings = [r['rating'] for r in self.rating_history[session_id]]
        
        if not ratings:
            return 0.0
        
        return statistics.mean(ratings)
    
    def calculate_engagement_score(self, session_data: Dict[str, Any]) -> float:
        """Calculate engagement score based on session data
        
        Args:
            session_data: Session metrics
            
        Returns:
            Engagement score between 0 and 1
        """
        queries_count = session_data.get('queries_count', 0)
        time_spent = session_data.get('time_spent', 0)
        completion_rate = session_data.get('completion_rate', 0.0)
        return_visits = session_data.get('return_visits', 0)
        
        # Calculate engagement components
        query_engagement = min(1.0, queries_count / 10.0)  # Normalize to 10 queries
        time_engagement = min(1.0, time_spent / 600.0)     # Normalize to 10 minutes
        completion_engagement = completion_rate
        return_engagement = min(1.0, return_visits / 3.0)   # Normalize to 3 return visits
        
        # Weighted average
        engagement_score = (
            query_engagement * 0.3 +
            time_engagement * 0.2 +
            completion_engagement * 0.3 +
            return_engagement * 0.2
        )
        
        return min(1.0, max(0.0, engagement_score))
    
    def get_satisfaction_trends(self) -> Dict[str, Any]:
        """Get satisfaction trends across all sessions
        
        Returns:
            Dictionary with trend information
        """
        all_ratings = []
        for session_ratings in self.rating_history.values():
            all_ratings.extend([r['rating'] for r in session_ratings])
        
        if not all_ratings:
            return {
                'average_rating': 0.0,
                'rating_count': 0,
                'trend_direction': 'stable'
            }
        
        average_rating = statistics.mean(all_ratings)
        rating_count = len(all_ratings)
        
        # Calculate trend direction
        if len(all_ratings) >= 2:
            recent_ratings = all_ratings[-10:]  # Last 10 ratings
            older_ratings = all_ratings[:-10] if len(all_ratings) > 10 else all_ratings
            
            if len(older_ratings) > 0:
                recent_avg = statistics.mean(recent_ratings)
                older_avg = statistics.mean(older_ratings)
                
                if recent_avg > older_avg + 0.5:
                    trend_direction = 'improving'
                elif recent_avg < older_avg - 0.5:
                    trend_direction = 'declining'
                else:
                    trend_direction = 'stable'
            else:
                trend_direction = 'stable'
        else:
            trend_direction = 'stable'
        
        return {
            'average_rating': average_rating,
            'rating_count': rating_count,
            'trend_direction': trend_direction
        }
    
    def get_session_metrics(self, session_id: str) -> Dict[str, Any]:
        """Get comprehensive metrics for a session
        
        Args:
            session_id: User session identifier
            
        Returns:
            Session metrics dictionary
        """
        if session_id not in self.session_data:
            return {}
        
        session = self.session_data[session_id]
        ratings = session.get('ratings', [])
        
        metrics = {
            'session_id': session_id,
            'start_time': session.get('start_time'),
            'queries_count': len(session.get('queries', [])),
            'average_rating': statistics.mean(ratings) if ratings else 0.0,
            'rating_count': len(ratings),
            'total_time': session.get('total_time', 0),
            'feedback_count': len(self.feedback_history.get(session_id, []))
        }
        
        # Calculate engagement score
        engagement_data = {
            'queries_count': metrics['queries_count'],
            'time_spent': metrics['total_time'],
            'completion_rate': 1.0 if metrics['queries_count'] > 0 else 0.0,
            'return_visits': 0  # Would need additional tracking
        }
        
        metrics['engagement_score'] = self.calculate_engagement_score(engagement_data)
        
        return metrics
    
    def get_user_feedback_summary(self, session_id: str) -> Dict[str, Any]:
        """Get summary of user feedback for a session
        
        Args:
            session_id: User session identifier
            
        Returns:
            Feedback summary dictionary
        """
        if session_id not in self.feedback_history:
            return {
                'feedback_count': 0,
                'positive_feedback': 0,
                'negative_feedback': 0,
                'common_themes': []
            }
        
        feedback_list = self.feedback_history[session_id]
        
        # Simple sentiment analysis
        positive_words = ['good', 'great', 'excellent', 'helpful', 'useful', 'accurate']
        negative_words = ['bad', 'poor', 'wrong', 'unhelpful', 'useless', 'inaccurate']
        
        positive_count = 0
        negative_count = 0
        
        for feedback_item in feedback_list:
            feedback_text = feedback_item['feedback'].lower()
            
            if any(word in feedback_text for word in positive_words):
                positive_count += 1
            elif any(word in feedback_text for word in negative_words):
                negative_count += 1
        
        return {
            'feedback_count': len(feedback_list),
            'positive_feedback': positive_count,
            'negative_feedback': negative_count,
            'common_themes': self._extract_common_themes(feedback_list)
        }
    
    def _extract_common_themes(self, feedback_list: List[Dict[str, Any]]) -> List[str]:
        """Extract common themes from feedback
        
        Args:
            feedback_list: List of feedback items
            
        Returns:
            List of common themes
        """
        # Simple theme extraction
        themes = []
        all_feedback = ' '.join([f['feedback'] for f in feedback_list])
        
        theme_keywords = {
            'accuracy': ['accurate', 'correct', 'wrong', 'incorrect'],
            'speed': ['fast', 'slow', 'quick', 'delay'],
            'clarity': ['clear', 'confusing', 'understandable'],
            'completeness': ['complete', 'incomplete', 'missing']
        }
        
        for theme, keywords in theme_keywords.items():
            if any(keyword in all_feedback.lower() for keyword in keywords):
                themes.append(theme)
        
        return themes 