from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from reverie.backend_server.models import AgentContext, ReflectionResult
    from persona.memory_structures.associative_memory import AssociativeMemory
    from persona.cognitive_modules.retriever.base import AbstractRetriever


class AbstractReflector(ABC):
    """
    Abstract base class for the Reflection cognitive module.
    
    Responsibility: Generate insights from accumulated experiences.
    
    Does NOT: Plan actions, perceive world, modify action state directly.
    All new thoughts are returned as ReflectionResult and stored by Persona.
    """

    @abstractmethod
    def reflect(self,
                agent: "AgentContext",
                memory_store: "AssociativeMemory",
                retriever: "AbstractRetriever"
    ) -> "ReflectionResult":
        """
        Generate reflections/insights based on accumulated experiences.
        
        This method checks if reflection should be triggered based on
        the agent's importance counter and generates new thoughts if so.

        Args:
            agent: Immutable snapshot of the agent's current state.
            memory_store: The agent's associative memory for reading experiences.
            retriever: The retriever module for finding relevant memories.

        Returns:
            ReflectionResult containing new thoughts and counter update info.
        """
        pass

    @abstractmethod
    def reflect_on_conversation(self,
                                 agent: "AgentContext",
                                 conversation: list,
                                 memory_store: "AssociativeMemory"
    ) -> "ReflectionResult":
        """
        Generate reflections specifically about a recent conversation.

        Args:
            agent: Immutable snapshot of the agent's current state.
            conversation: List of [speaker, utterance] pairs from the conversation.
            memory_store: The agent's associative memory.

        Returns:
            ReflectionResult containing planning thoughts and memos from the conversation.
        """
        pass
