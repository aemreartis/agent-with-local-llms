"""
Quality Scorer

Evaluates response quality, relevance, accuracy, completeness, and detects hallucinations.
"""

import re
from typing import Dict, List, Any, Tuple
from difflib import SequenceMatcher


class QualityScorer:
    """Evaluates response quality and detects issues"""
    
    def __init__(self):
        """Initialize quality scorer with thresholds"""
        self.relevance_threshold = 0.7
        self.accuracy_threshold = 0.8
        self.completeness_threshold = 0.6
        self.hallucination_threshold = 0.3
    
    def calculate_relevance_score(self, query: str, response: str) -> float:
        """Calculate relevance score between query and response
        
        Args:
            query: User query
            response: Generated response
            
        Returns:
            Relevance score between 0 and 1
        """
        # Simple keyword matching approach
        query_words = set(re.findall(r'\b\w+\b', query.lower()))
        response_words = set(re.findall(r'\b\w+\b', response.lower()))
        
        if not query_words:
            return 0.0
        
        # Calculate word overlap
        overlap = len(query_words.intersection(response_words))
        relevance_score = overlap / len(query_words)
        
        # Boost score for longer, more detailed responses
        if len(response_words) > len(query_words) * 2:
            relevance_score = min(1.0, relevance_score * 1.2)
        
        return min(1.0, max(0.0, relevance_score))
    
    def calculate_accuracy_score(self, response: str, sources: List[str]) -> float:
        """Calculate accuracy score based on source citations
        
        Args:
            response: Generated response
            sources: List of source documents
            
        Returns:
            Accuracy score between 0 and 1
        """
        if not sources:
            return 0.5  # Neutral score when no sources provided
        
        # Check for source citations in response
        source_mentions = 0
        for source in sources:
            if source.lower() in response.lower():
                source_mentions += 1
        
        # Calculate accuracy based on source citations
        citation_ratio = source_mentions / len(sources)
        
        # Base accuracy score
        accuracy_score = 0.5 + (citation_ratio * 0.5)
        
        # Penalize responses that are too generic
        if len(response.split()) < 10:
            accuracy_score *= 0.8
        
        return min(1.0, max(0.0, accuracy_score))
    
    def calculate_completeness_score(self, query: str, response: str) -> float:
        """Calculate completeness score based on query requirements
        
        Args:
            query: User query
            response: Generated response
            
        Returns:
            Completeness score between 0 and 1
        """
        # Analyze query complexity
        query_complexity = self._analyze_query_complexity(query)
        
        # Analyze response depth
        response_depth = self._analyze_response_depth(response)
        
        # Calculate completeness ratio
        completeness_score = min(1.0, response_depth / query_complexity)
        
        # Boost score for detailed responses
        if len(response.split()) > 50:
            completeness_score = min(1.0, completeness_score * 1.1)
        
        return min(1.0, max(0.0, completeness_score))
    
    def calculate_overall_quality_score(self, scores: Dict[str, float]) -> float:
        """Calculate overall quality score from individual scores
        
        Args:
            scores: Dictionary of individual quality scores
            
        Returns:
            Overall quality score between 0 and 1
        """
        weights = {
            'relevance': 0.3,
            'accuracy': 0.4,
            'completeness': 0.3
        }
        
        overall_score = 0.0
        total_weight = 0.0
        
        for metric, weight in weights.items():
            if metric in scores:
                overall_score += scores[metric] * weight
                total_weight += weight
        
        if total_weight == 0:
            return 0.0
        
        return overall_score / total_weight
    
    def detect_hallucinations(self, response: str, sources: List[str]) -> float:
        """Detect potential hallucinations in response
        
        Args:
            response: Generated response
            sources: List of source documents
            
        Returns:
            Hallucination score between 0 and 1 (higher = more likely hallucination)
        """
        if not sources:
            return 0.5  # Uncertain without sources
        
        # Check for specific claims without citations
        specific_claims = self._extract_specific_claims(response)
        
        hallucination_score = 0.0
        total_claims = len(specific_claims)
        
        if total_claims == 0:
            return 0.1  # Low hallucination risk for general responses
        
        for claim in specific_claims:
            # Check if claim is supported by sources
            if not self._is_claim_supported(claim, sources):
                hallucination_score += 1.0
        
        return min(1.0, hallucination_score / total_claims)
    
    def _analyze_query_complexity(self, query: str) -> float:
        """Analyze query complexity
        
        Args:
            query: User query
            
        Returns:
            Complexity score
        """
        # Simple complexity metrics
        word_count = len(query.split())
        question_words = ['what', 'how', 'why', 'when', 'where', 'who', 'which']
        question_count = sum(1 for word in question_words if word in query.lower())
        
        complexity = word_count * 0.1 + question_count * 0.2
        return max(1.0, complexity)
    
    def _analyze_response_depth(self, response: str) -> float:
        """Analyze response depth and detail
        
        Args:
            response: Generated response
            
        Returns:
            Depth score
        """
        # Simple depth metrics
        word_count = len(response.split())
        sentence_count = len(response.split('.'))
        paragraph_count = len(response.split('\n\n'))
        
        depth = word_count * 0.05 + sentence_count * 0.1 + paragraph_count * 0.2
        return max(1.0, depth)
    
    def _extract_specific_claims(self, response: str) -> List[str]:
        """Extract specific factual claims from response
        
        Args:
            response: Generated response
            
        Returns:
            List of specific claims
        """
        # Simple claim extraction
        sentences = response.split('.')
        claims = []
        
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) > 10 and any(word in sentence.lower() for word in ['is', 'are', 'was', 'were', 'has', 'have', 'had']):
                claims.append(sentence)
        
        return claims
    
    def _is_claim_supported(self, claim: str, sources: List[str]) -> bool:
        """Check if a claim is supported by sources
        
        Args:
            claim: Specific claim
            sources: List of source documents
            
        Returns:
            True if claim appears to be supported
        """
        # Simple keyword matching
        claim_words = set(re.findall(r'\b\w+\b', claim.lower()))
        
        for source in sources:
            source_words = set(re.findall(r'\b\w+\b', source.lower()))
            overlap = len(claim_words.intersection(source_words))
            
            if overlap > len(claim_words) * 0.3:  # 30% word overlap
                return True
        
        return False 