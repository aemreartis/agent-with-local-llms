from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


@dataclass
class ScoredResult:
    """A search result with normalized scoring information."""
    document_id: str
    content: str
    original_score: float
    normalized_score: float
    rank: int
    provider_name: str
    metadata: Dict[str, Any] = None


@dataclass  
class FusionWeights:
    """Weight configuration for fusion strategies."""
    provider_weights: Dict[str, float]  # Weight by provider
    score_weights: Dict[str, float]     # Weight by score type
    rank_decay_factor: float = 0.6      # For rank-based fusion
    diversity_factor: float = 0.1       # For promoting result diversity


@dataclass
class FusionResult:
    """Result from fusion process with detailed metadata."""
    fused_results: List[ScoredResult]
    fusion_metadata: Dict[str, Any]
    provider_contributions: Dict[str, int]  # How many results from each provider
    fusion_scores: Dict[str, float]         # Final fusion scores
    diversity_score: float = 0.0
    processing_time_ms: float = 0.0


class ResultFusionInterface(ABC):
    """Interface for implementing result fusion algorithms and strategies."""
    
    @abstractmethod
    async def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize the result fusion service with configuration."""
        pass
    
    @abstractmethod
    async def fuse_ranked_results(self, provider_results: List[List[ScoredResult]], weights: Optional[FusionWeights] = None) -> FusionResult:
        """
        Fuse results using rank-based fusion algorithms.
        Implements Reciprocal Rank Fusion (RRF) and weighted variants.
        """
        pass
    
    @abstractmethod
    async def fuse_scored_results(self, provider_results: List[List[ScoredResult]], weights: Optional[FusionWeights] = None) -> FusionResult:
        """
        Fuse results using score-based fusion algorithms.
        Combines normalized scores with configurable weights.
        """
        pass
    
    @abstractmethod
    async def interleave_results(self, provider_results: List[List[ScoredResult]], pattern: Optional[List[int]] = None) -> FusionResult:
        """
        Interleave results from multiple providers in a specified pattern.
        Default pattern alternates between providers.
        """
        pass
    
    @abstractmethod
    async def adaptive_fusion(self, provider_results: List[List[ScoredResult]], query_context: Dict[str, Any]) -> FusionResult:
        """
        Choose and apply the best fusion strategy based on query context and result characteristics.
        """
        pass
    
    @abstractmethod
    async def normalize_scores(self, results: List[ScoredResult], method: str = "min_max") -> List[ScoredResult]:
        """
        Normalize scores from different providers to a common scale.
        Methods: min_max, z_score, rank_based, sigmoid
        """
        pass
    
    @abstractmethod
    async def calculate_diversity(self, results: List[ScoredResult]) -> float:
        """Calculate diversity score for a set of results."""
        pass
    
    @abstractmethod
    async def apply_diversity_promotion(self, results: List[ScoredResult], diversity_factor: float = 0.1) -> List[ScoredResult]:
        """Apply diversity promotion to reduce result redundancy."""
        pass
    
    @abstractmethod
    async def reciprocal_rank_fusion(self, provider_results: List[List[ScoredResult]], k: float = 60.0) -> FusionResult:
        """
        Apply Reciprocal Rank Fusion algorithm.
        RRF score = sum(1 / (k + rank)) for each provider
        """
        pass
    
    @abstractmethod
    async def weighted_score_fusion(self, provider_results: List[List[ScoredResult]], weights: Dict[str, float]) -> FusionResult:
        """Apply weighted score fusion with provider-specific weights."""
        pass
    
    @abstractmethod
    async def borda_count_fusion(self, provider_results: List[List[ScoredResult]]) -> FusionResult:
        """Apply Borda count fusion based on result rankings."""
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """Check if the fusion service is healthy and operational."""
        pass
    
    def get_service_info(self) -> Dict[str, Any]:
        """Get information about the result fusion service."""
        return {
            "name": self.__class__.__name__,
            "version": "1.0",
            "capabilities": [
                "rank_based_fusion",
                "score_based_fusion", 
                "interleaving",
                "adaptive_fusion",
                "diversity_promotion",
                "score_normalization",
                "reciprocal_rank_fusion",
                "weighted_fusion",
                "borda_count"
            ],
            "type": "result_fusion_service",
            "supported_normalization_methods": ["min_max", "z_score", "rank_based", "sigmoid"],
            "supported_fusion_algorithms": ["rrf", "weighted_score", "borda_count", "interleave", "adaptive"]
        } 