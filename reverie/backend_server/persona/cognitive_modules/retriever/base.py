from abc import ABC, abstractmethod
from typing import List, Dict, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from reverie.backend_server.models import Memory, AgentContext, RetrievalResult
    from persona.memory_structures.associative_memory import AssociativeMemory


class AbstractRetriever(ABC):
    """
    Abstract base class for the Retrieval cognitive module.
    
    Responsibility: Find relevant memories for decision-making.
    
    Does NOT: Modify memories permanently, access scratch, call LLMs for other purposes.
    The retriever may update last_accessed times on memories as a side effect,
    but major state changes are handled by Persona.
    """

    @abstractmethod
    def retrieve(self, 
                 queries: List["Memory"],
                 agent: "AgentContext",
                 memory_store: "AssociativeMemory"
    ) -> Dict[str, "RetrievalResult"]:
        """
        Retrieve relevant memories for a list of perceived events.

        Args:
            queries: List of Memory objects representing events to find context for.
            agent: Immutable snapshot of the agent's current state.
            memory_store: The agent's associative memory (for reading).

        Returns:
            A dictionary where keys are event descriptions and values are 
            RetrievalResult objects containing relevant events and thoughts.
        """
        pass

    @abstractmethod
    def retrieve_by_focal_points(self,
                                  focal_points: List[str],
                                  agent: "AgentContext", 
                                  memory_store: "AssociativeMemory",
                                  n_count: int = 30
    ) -> Dict[str, "RetrievalResult"]:
        """
        Retrieve memories based on focal point strings (for reflection).
        
        This corresponds to the weighted retrieval used in reflection,
        where we search by text queries rather than Memory objects.

        Args:
            focal_points: List of text queries to search for.
            agent: Immutable snapshot of the agent's current state.
            memory_store: The agent's associative memory.
            n_count: Maximum number of memories to retrieve per focal point.

        Returns:
            A dictionary mapping focal points to RetrievalResult objects.
        """
        pass
