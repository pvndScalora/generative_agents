"""
Memory Scoring Strategies

Different approaches to scoring memories for retrieval, enabling experimentation
with alternative weighting schemes beyond the original linear combination.

The original paper uses: score = recency_w * R + relevance_w * V + importance_w * I
These strategies allow swapping this formula without changing the retriever.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Optional, TYPE_CHECKING
from numpy import dot, exp
from numpy.linalg import norm

if TYPE_CHECKING:
    from reverie.backend_server.models import Memory


@dataclass(frozen=True)
class ScoringContext:
    """
    Immutable context provided to scoring strategies.
    
    Contains all the information needed to score memories without
    directly accessing scratch or other mutable state.
    """
    recency_weight: float
    relevance_weight: float
    importance_weight: float
    recency_decay: float
    current_time_index: int  # Position in time sequence (for recency calculation)
    
    # Optional global multipliers (paper uses [0.5, 3, 2])
    recency_global: float = 0.5
    relevance_global: float = 3.0
    importance_global: float = 2.0


@dataclass(frozen=True)
class MemoryScores:
    """
    Intermediate scores for a single memory before combination.
    
    All values are normalized to [0, 1] range.
    """
    recency: float      # How recently accessed (exponential decay)
    relevance: float    # Semantic similarity to query
    importance: float   # Poignancy/significance score


class MemoryScoringStrategy(ABC):
    """
    Abstract base class for memory scoring strategies.
    
    Defines the interface for computing final retrieval scores from 
    individual memory attributes. Different implementations can 
    experiment with alternative scoring formulas.
    
    Example usage:
        strategy = LinearWeightedScoring()
        scores = strategy.compute_scores(memories, query_embedding, context)
        top_memories = strategy.select_top(scores, n=30)
    """
    
    @abstractmethod
    def compute_scores(self,
                       memories: List["Memory"],
                       query_embedding: List[float],
                       embeddings: Dict[str, List[float]],
                       context: ScoringContext
    ) -> Dict[str, float]:
        """
        Compute final scores for all memories.
        
        Args:
            memories: List of Memory nodes to score.
            query_embedding: Embedding vector for the query/focal point.
            embeddings: Dictionary mapping embedding_key -> embedding vector.
            context: ScoringContext with weights and parameters.
            
        Returns:
            Dictionary mapping memory.id -> final score.
        """
        pass
    
    def select_top(self, scores: Dict[str, float], n: int) -> Dict[str, float]:
        """
        Select the top N highest scoring memories.
        
        Default implementation simply sorts by score.
        Override for different selection strategies (e.g., diversity-aware).
        """
        return dict(sorted(scores.items(), key=lambda x: x[1], reverse=True)[:n])
    
    # Utility methods for common calculations
    
    @staticmethod
    def compute_recency_scores(memories: List["Memory"], decay: float) -> Dict[str, float]:
        """Compute recency scores using exponential decay by position."""
        # Score based on position in sorted list (most recent last)
        recency_vals = [decay ** i for i in range(1, len(memories) + 1)]
        return {mem.id: recency_vals[i] for i, mem in enumerate(memories)}
    
    @staticmethod
    def compute_importance_scores(memories: List["Memory"]) -> Dict[str, float]:
        """Extract importance scores from memory poignancy."""
        return {mem.id: mem.poignancy for mem in memories}
    
    @staticmethod
    def compute_relevance_scores(memories: List["Memory"],
                                  query_embedding: List[float],
                                  embeddings: Dict[str, List[float]]
    ) -> Dict[str, float]:
        """Compute relevance as cosine similarity to query."""
        relevance = {}
        for mem in memories:
            if mem.embedding_key in embeddings:
                mem_emb = embeddings[mem.embedding_key]
                relevance[mem.id] = MemoryScoringStrategy._cos_sim(mem_emb, query_embedding)
            else:
                relevance[mem.id] = 0.0
        return relevance
    
    @staticmethod
    def _cos_sim(a, b) -> float:
        """Cosine similarity between two vectors."""
        n_a, n_b = norm(a), norm(b)
        if n_a == 0 or n_b == 0:
            return 0.0
        return dot(a, b) / (n_a * n_b)
    
    @staticmethod
    def normalize(scores: Dict[str, float], 
                  target_min: float = 0.0, 
                  target_max: float = 1.0) -> Dict[str, float]:
        """Normalize scores to [target_min, target_max] range."""
        if not scores:
            return scores
            
        min_val = min(scores.values())
        max_val = max(scores.values())
        range_val = max_val - min_val
        
        if range_val == 0:
            mid = (target_max - target_min) / 2
            return {k: mid for k in scores}
        
        return {
            k: ((v - min_val) * (target_max - target_min) / range_val + target_min)
            for k, v in scores.items()
        }


class LinearWeightedScoring(MemoryScoringStrategy):
    """
    Original paper's scoring formula: linear weighted sum.
    
    score = (recency_w * recency * g_r) + (relevance_w * relevance * g_v) + (importance_w * importance * g_i)
    
    Where g_r, g_v, g_i are global multipliers that adjust the base contribution
    of each factor before persona-specific weights are applied.
    """
    
    def compute_scores(self,
                       memories: List["Memory"],
                       query_embedding: List[float],
                       embeddings: Dict[str, List[float]],
                       context: ScoringContext
    ) -> Dict[str, float]:
        # Compute individual components
        recency = self.normalize(self.compute_recency_scores(memories, context.recency_decay))
        importance = self.normalize(self.compute_importance_scores(memories))
        relevance = self.normalize(self.compute_relevance_scores(memories, query_embedding, embeddings))
        
        # Combine with weights and global multipliers
        scores = {}
        for mem_id in recency:
            scores[mem_id] = (
                context.recency_weight * recency[mem_id] * context.recency_global +
                context.relevance_weight * relevance.get(mem_id, 0) * context.relevance_global +
                context.importance_weight * importance.get(mem_id, 0) * context.importance_global
            )
        
        return scores


class AttentionBasedScoring(MemoryScoringStrategy):
    """
    Attention-inspired scoring using softmax weighting.
    
    Instead of linear combination, uses softmax to create attention weights
    over recency/relevance/importance, then combines. This can create more
    dynamic weighting based on the distribution of each factor.
    
    score = softmax(w_r * R, w_v * V, w_i * I) • (R, V, I)
    """
    
    def __init__(self, temperature: float = 1.0):
        """
        Args:
            temperature: Controls sharpness of attention (lower = sharper).
        """
        self.temperature = temperature
    
    def compute_scores(self,
                       memories: List["Memory"],
                       query_embedding: List[float],
                       embeddings: Dict[str, List[float]],
                       context: ScoringContext
    ) -> Dict[str, float]:
        recency = self.normalize(self.compute_recency_scores(memories, context.recency_decay))
        importance = self.normalize(self.compute_importance_scores(memories))
        relevance = self.normalize(self.compute_relevance_scores(memories, query_embedding, embeddings))
        
        scores = {}
        for mem_id in recency:
            r, v, i = recency[mem_id], relevance.get(mem_id, 0), importance.get(mem_id, 0)
            
            # Weighted inputs
            wr = context.recency_weight * r
            wv = context.relevance_weight * v
            wi = context.importance_weight * i
            
            # Softmax attention weights
            factors = [wr / self.temperature, wv / self.temperature, wi / self.temperature]
            max_f = max(factors)  # For numerical stability
            exp_factors = [exp(f - max_f) for f in factors]
            sum_exp = sum(exp_factors)
            attention = [e / sum_exp for e in exp_factors]
            
            # Attention-weighted combination
            scores[mem_id] = attention[0] * r + attention[1] * v + attention[2] * i
        
        return scores


class RecencyOnlyScoring(MemoryScoringStrategy):
    """
    Scores memories purely by recency.
    
    Useful for experiments testing the importance of temporal ordering
    vs semantic relevance.
    """
    
    def compute_scores(self,
                       memories: List["Memory"],
                       query_embedding: List[float],
                       embeddings: Dict[str, List[float]],
                       context: ScoringContext
    ) -> Dict[str, float]:
        return self.normalize(self.compute_recency_scores(memories, context.recency_decay))


class RelevanceOnlyScoring(MemoryScoringStrategy):
    """
    Scores memories purely by semantic relevance.
    
    Useful for experiments testing pure semantic retrieval vs 
    the multi-factor approach.
    """
    
    def compute_scores(self,
                       memories: List["Memory"],
                       query_embedding: List[float],
                       embeddings: Dict[str, List[float]],
                       context: ScoringContext
    ) -> Dict[str, float]:
        return self.normalize(self.compute_relevance_scores(memories, query_embedding, embeddings))


class ImportanceOnlyScoring(MemoryScoringStrategy):
    """
    Scores memories purely by importance/poignancy.
    
    Useful for experiments focusing on emotionally significant memories.
    """
    
    def compute_scores(self,
                       memories: List["Memory"],
                       query_embedding: List[float],
                       embeddings: Dict[str, List[float]],
                       context: ScoringContext
    ) -> Dict[str, float]:
        return self.normalize(self.compute_importance_scores(memories))


class HybridRelevanceRecencyScoring(MemoryScoringStrategy):
    """
    Two-factor scoring: Relevance * Recency.
    
    Multiplicative instead of additive combination, meaning both factors
    must be high for a memory to score well.
    """
    
    def compute_scores(self,
                       memories: List["Memory"],
                       query_embedding: List[float],
                       embeddings: Dict[str, List[float]],
                       context: ScoringContext
    ) -> Dict[str, float]:
        recency = self.normalize(self.compute_recency_scores(memories, context.recency_decay))
        relevance = self.normalize(self.compute_relevance_scores(memories, query_embedding, embeddings))
        
        return {
            mem_id: recency[mem_id] * relevance.get(mem_id, 0)
            for mem_id in recency
        }
