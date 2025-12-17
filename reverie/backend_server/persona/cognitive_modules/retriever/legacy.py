from typing import List, Dict, Any, TYPE_CHECKING, Optional
from numpy import dot
from numpy.linalg import norm

from reverie.backend_server.models import Memory, RetrievalResult
from reverie.backend_server.persona.prompt_template.gpt_structure import get_embedding
from .scoring import (
    MemoryScoringStrategy,
    LinearWeightedScoring,
    ScoringContext,
)
from .base import AbstractRetriever

if TYPE_CHECKING:
    from persona.memory_structures.scratch import Scratch
    from persona.memory_structures.associative_memory import AssociativeMemory
    from reverie.backend_server.models import AgentContext


class LegacyRetriever(AbstractRetriever):
    """
    Legacy implementation of the Retrieval cognitive module.
    
    Uses a weighted score of Recency, Importance, and Relevance.
    Supports both scratch-based and contract-based interfaces.
    
    Now supports pluggable scoring strategies for experimental flexibility:
        retriever = LegacyRetriever(scratch)
        retriever.scoring_strategy = AttentionBasedScoring(temperature=0.5)
    """

    def __init__(self, 
                 scratch: "Scratch",
                 scoring_strategy: Optional[MemoryScoringStrategy] = None):
        """
        Args:
            scratch: Scratch state for legacy compatibility.
            scoring_strategy: Optional custom scoring strategy. 
                              Defaults to LinearWeightedScoring (original paper).
        """
        self.scratch = scratch
        self.scoring_strategy = scoring_strategy or LinearWeightedScoring()

    def retrieve(self, 
                 perceived_or_queries: List[Memory],
                 agent: Optional["AgentContext"] = None,
                 memory_store: Optional["AssociativeMemory"] = None
    ) -> Dict[str, Any]:
        """
        Retrieve relevant memories for perceived events.
        
        Supports both interfaces:
        - Legacy: retrieve(perceived) - uses self.scratch for memory access
        - New: retrieve(queries, agent, memory_store) - explicit dependencies
        
        Returns:
            Dictionary mapping event descriptions to RetrievalResult or legacy dict format.
        """
        # Use scratch's memory if not explicitly provided
        a_mem = memory_store if memory_store else self.scratch.a_mem
        
        retrieved = dict()
        for event in perceived_or_queries: 
            retrieved[event.description] = dict()
            retrieved[event.description]["curr_event"] = event
            
            relevant_events = a_mem.retrieve_relevant_events(
                                event.subject, event.predicate, event.object)
            retrieved[event.description]["events"] = list(relevant_events)

            relevant_thoughts = a_mem.retrieve_relevant_thoughts(
                                event.subject, event.predicate, event.object)
            retrieved[event.description]["thoughts"] = list(relevant_thoughts)
            
        return retrieved

    def retrieve_by_focal_points(self,
                                  focal_points: List[str],
                                  agent: Optional["AgentContext"] = None,
                                  memory_store: Optional["AssociativeMemory"] = None,
                                  n_count: int = 30
    ) -> Dict[str, "RetrievalResult"]:
        """
        Retrieve memories based on focal point strings (for reflection).
        
        New contract-based interface that wraps retrieve_weighted.
        """
        # Use scratch's memory if not explicitly provided
        a_mem = memory_store if memory_store else self.scratch.a_mem
        
        raw_results = self._retrieve_weighted_internal(focal_points, a_mem, n_count)
        
        # Convert to RetrievalResult format
        results = {}
        for focal_pt, nodes in raw_results.items():
            results[focal_pt] = RetrievalResult(
                query_event=None,
                relevant_events=[n for n in nodes if n.type.value == "event"],
                relevant_thoughts=[n for n in nodes if n.type.value == "thought"],
            )
        return results

    def retrieve_weighted(self, focal_points: List[str], n_count: int = 30) -> Dict[str, List[Memory]]:
        """
        Legacy interface: Given focal points, retrieves nodes based on weighted scoring.
        """
        return self._retrieve_weighted_internal(focal_points, self.scratch.a_mem, n_count)

    def _retrieve_weighted_internal(self, 
                                     focal_points: List[str], 
                                     a_mem: "AssociativeMemory",
                                     n_count: int = 30) -> Dict[str, List[Memory]]:
        """
        Internal implementation of weighted retrieval.
        
        Uses the configured scoring_strategy for flexible experimentation.
        """
        retrieved = dict() 
        for focal_pt in focal_points: 
            # Getting all nodes from the agent's memory (both thoughts and events)
            nodes = [[i.last_accessed, i]
                    for i in a_mem.seq_event + a_mem.seq_thought
                    if "idle" not in i.embedding_key]
            nodes = sorted(nodes, key=lambda x: x[0])
            nodes = [i for created, i in nodes]

            if not nodes:
                retrieved[focal_pt] = []
                continue

            # Use the scoring strategy for experimental flexibility
            query_embedding = get_embedding(focal_pt)
            context = ScoringContext(
                recency_weight=self.scratch.recency_w,
                relevance_weight=self.scratch.relevance_w,
                importance_weight=self.scratch.importance_w,
                recency_decay=self.scratch.recency_decay,
                current_time_index=len(nodes),
            )
            
            # Compute scores using the strategy
            master_out = self.scoring_strategy.compute_scores(
                memories=nodes,
                query_embedding=query_embedding,
                embeddings=a_mem.embeddings,
                context=context
            )

            # Select top N using the strategy
            master_out = self.scoring_strategy.select_top(master_out, n_count)
            master_nodes = [a_mem.id_to_node[key] 
                            for key in list(master_out.keys())]

            for n in master_nodes: 
                n.last_accessed = self.scratch.curr_time
            
            retrieved[focal_pt] = master_nodes

        return retrieved

    # Legacy helper methods - kept for backward compatibility
    # These are now superseded by the MemoryScoringStrategy interface
    
    def _extract_recency(self, nodes: List[Memory]) -> Dict[str, float]:
        """Deprecated: Use scoring_strategy.compute_recency_scores instead."""
        recency_vals = [self.scratch.recency_decay ** i 
                        for i in range(1, len(nodes) + 1)]
        
        recency_out = dict()
        for count, node in enumerate(nodes): 
            recency_out[node.id] = recency_vals[count]

        return recency_out

    def _extract_importance(self, nodes: List[Memory]) -> Dict[str, float]:
        """Deprecated: Use scoring_strategy.compute_importance_scores instead."""
        importance_out = dict()
        for count, node in enumerate(nodes): 
            importance_out[node.id] = node.poignancy

        return importance_out

    def _extract_relevance(self, nodes: List[Memory], focal_pt: str, 
                           a_mem: Optional["AssociativeMemory"] = None) -> Dict[str, float]:
        """Deprecated: Use scoring_strategy.compute_relevance_scores instead."""
        focal_embedding = get_embedding(focal_pt)
        memory = a_mem if a_mem else self.scratch.a_mem

        relevance_out = dict()
        for count, node in enumerate(nodes): 
            node_embedding = memory.embeddings[node.embedding_key]
            relevance_out[node.id] = self._cos_sim(node_embedding, focal_embedding)

        return relevance_out

    @staticmethod
    def _cos_sim(a, b): 
        """Deprecated: Use MemoryScoringStrategy._cos_sim instead."""
        return dot(a, b)/(norm(a)*norm(b))

    @staticmethod
    def _normalize_dict_floats(d, target_min, target_max):
        """Deprecated: Use MemoryScoringStrategy.normalize instead."""
        if not d: return d
        min_val = min(val for val in d.values())
        max_val = max(val for val in d.values())
        range_val = max_val - min_val

        if range_val == 0: 
            for key, val in d.items(): 
                d[key] = (target_max - target_min)/2
        else: 
            for key, val in d.items():
                d[key] = ((val - min_val) * (target_max - target_min) 
                            / range_val + target_min)
        return d

    @staticmethod
    def _top_highest_x_values(d, x):
        """Deprecated: Use scoring_strategy.select_top instead."""
