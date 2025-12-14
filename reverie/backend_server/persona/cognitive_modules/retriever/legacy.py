from typing import List, Dict, Any, TYPE_CHECKING
from numpy import dot
from numpy.linalg import norm

from reverie.backend_server.models import Memory
from reverie.backend_server.persona.prompt_template.gpt_structure import get_embedding
from .base import AbstractRetriever

if TYPE_CHECKING:
    from persona.persona import Persona

class LegacyRetriever(AbstractRetriever):
    """
    The legacy implementation of the retrieval module.
    Uses a weighted score of Recency, Importance, and Relevance.
    """

    def __init__(self, persona: "Persona"):
        self.persona = persona

    def retrieve(self, perceived: List[Memory]) -> Dict[str, Dict[str, Any]]:
        """
        Takes a list of perceived events and returns a dictionary of relevant memories.
        """
        retrieved = dict()
        for event in perceived: 
            retrieved[event.description] = dict()
            retrieved[event.description]["curr_event"] = event
            
            # We need to access the persona's associative memory to retrieve relevant events/thoughts
            # The original code called persona.a_mem.retrieve_relevant_events which likely calls new_retrieve internally
            # But wait, retrieve_relevant_events is a method on AssociativeMemory?
            # Let's check AssociativeMemory.retrieve_relevant_events implementation.
            # If it calls `new_retrieve` from the global scope, we need to be careful.
            
            # Looking at the original retrieve.py:
            # relevant_events = persona.a_mem.retrieve_relevant_events(event.subject, event.predicate, event.object)
            # relevant_thoughts = persona.a_mem.retrieve_relevant_thoughts(event.subject, event.predicate, event.object)
            
            # If AssociativeMemory methods are just wrappers around `new_retrieve` (which is in retrieve.py),
            # then we should implement `new_retrieve` logic here and update AssociativeMemory to use THIS class.
            
            # However, for this refactoring step, we want to encapsulate the logic that was in `retrieve.py`.
            # The `retrieve` function in `retrieve.py` calls `persona.a_mem.retrieve_relevant_events`.
            # The `new_retrieve` function in `retrieve.py` implements the scoring logic.
            
            # It seems `AssociativeMemory` depends on `retrieve.py`'s `new_retrieve`.
            # This is a circular dependency or tight coupling we need to break.
            
            # For now, let's implement the `retrieve` method as it was, but we might need to move `new_retrieve` logic 
            # into this class as well, and expose it.
            
            relevant_events = self.persona.a_mem.retrieve_relevant_events(
                                event.subject, event.predicate, event.object)
            retrieved[event.description]["events"] = list(relevant_events)

            relevant_thoughts = self.persona.a_mem.retrieve_relevant_thoughts(
                                event.subject, event.predicate, event.object)
            retrieved[event.description]["thoughts"] = list(relevant_thoughts)
            
        return retrieved

    def retrieve_weighted(self, focal_points: List[str], n_count: int = 30) -> Dict[str, List[Memory]]:
        """
        This corresponds to the `new_retrieve` function in the original file.
        Given focal points, retrieves a set of nodes based on weighted scoring.
        """
        retrieved = dict() 
        for focal_pt in focal_points: 
            # Getting all nodes from the agent's memory (both thoughts and events)
            nodes = [[i.last_accessed, i]
                    for i in self.persona.a_mem.seq_event + self.persona.a_mem.seq_thought
                    if "idle" not in i.embedding_key]
            nodes = sorted(nodes, key=lambda x: x[0])
            nodes = [i for created, i in nodes]

            # Calculating the component dictionaries and normalizing them.
            recency_out = self._extract_recency(nodes)
            recency_out = self._normalize_dict_floats(recency_out, 0, 1)
            importance_out = self._extract_importance(nodes)
            importance_out = self._normalize_dict_floats(importance_out, 0, 1)  
            relevance_out = self._extract_relevance(nodes, focal_pt)
            relevance_out = self._normalize_dict_floats(relevance_out, 0, 1)

            # Computing the final scores
            gw = [0.5, 3, 2]
            master_out = dict()
            for key in recency_out.keys(): 
                master_out[key] = (self.persona.scratch.recency_w * recency_out[key] * gw[0] 
                                + self.persona.scratch.relevance_w * relevance_out[key] * gw[1] 
                                + self.persona.scratch.importance_w * importance_out[key] * gw[2])

            # Extracting the highest x values.
            master_out = self._top_highest_x_values(master_out, n_count)
            master_nodes = [self.persona.a_mem.id_to_node[key] 
                            for key in list(master_out.keys())]

            for n in master_nodes: 
                n.last_accessed = self.persona.scratch.curr_time
            
            retrieved[focal_pt] = master_nodes

        return retrieved

    def _extract_recency(self, nodes: List[Memory]) -> Dict[str, float]:
        recency_vals = [self.persona.scratch.recency_decay ** i 
                        for i in range(1, len(nodes) + 1)]
        
        recency_out = dict()
        for count, node in enumerate(nodes): 
            recency_out[node.id] = recency_vals[count]

        return recency_out

    def _extract_importance(self, nodes: List[Memory]) -> Dict[str, float]:
        importance_out = dict()
        for count, node in enumerate(nodes): 
            importance_out[node.id] = node.poignancy

        return importance_out

    def _extract_relevance(self, nodes: List[Memory], focal_pt: str) -> Dict[str, float]:
        focal_embedding = get_embedding(focal_pt)

        relevance_out = dict()
        for count, node in enumerate(nodes): 
            node_embedding = self.persona.a_mem.embeddings[node.embedding_key]
            relevance_out[node.id] = self._cos_sim(node_embedding, focal_embedding)

        return relevance_out

    @staticmethod
    def _cos_sim(a, b): 
        return dot(a, b)/(norm(a)*norm(b))

    @staticmethod
    def _normalize_dict_floats(d, target_min, target_max):
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
        top_v = dict(sorted(d.items(), 
                            key=lambda item: item[1], 
                            reverse=True)[:x])
        return top_v
