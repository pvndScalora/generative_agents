from abc import ABC, abstractmethod
from typing import List, Dict, Any
from reverie.backend_server.models import Memory

class AbstractRetriever(ABC):
    """
    Abstract base class for the Retrieval cognitive module.
    
    The Retriever is responsible for selecting relevant memories (events and thoughts)
    from the agent's associative memory based on the current context (perceived events).
    """

    @abstractmethod
    def retrieve(self, perceived: List[Memory]) -> Dict[str, Dict[str, Any]]:
        """
        Takes a list of perceived events and returns a dictionary of relevant memories.

        Args:
            perceived: A list of Memory objects representing events happening around the persona.

        Returns:
            A dictionary where keys are event descriptions and values are dictionaries containing:
            - "curr_event": The perceived Memory object.
            - "events": A list of relevant event Memory objects retrieved from storage.
            - "thoughts": A list of relevant thought Memory objects retrieved from storage.
        """
        pass
