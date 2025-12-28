from abc import ABC, abstractmethod
from typing import List, Tuple, Dict, TYPE_CHECKING

if TYPE_CHECKING:
    from maze import Maze
    from models import (
        AgentContext, RetrievalResult, ConversationResult
    )
    from persona.memory_structures.associative_memory import AssociativeMemory
    from persona.cognitive_modules.retriever.base import AbstractRetriever


class AbstractConverser(ABC):
    """
    Abstract base class for the Conversation cognitive module.
    
    Responsibility: Manage conversational interactions for an agent.
    
    Does NOT: Modify agent state directly, plan actions outside conversation.
    Conversation effects are returned as ConversationResult and applied by Persona.
    """
    
    @abstractmethod
    def open_session(self, convo_mode: str):
        """
        Open an interactive conversation session (for debugging/analysis).
        
        Args:
            convo_mode: The type of session ("analysis" or "whisper").
        """
        pass

    @abstractmethod
    def generate_utterance(self,
                           agent: "AgentContext",
                           other_agent: "AgentContext",
                           conversation_history: List[Tuple[str, str]],
                           retrieved: Dict[str, "RetrievalResult"],
                           memory_store: "AssociativeMemory"
    ) -> "ConversationResult":
        """
        Generate the next utterance in a conversation.

        Args:
            agent: This agent's context (the speaker).
            other_agent: The other participant's context.
            conversation_history: List of (speaker_name, utterance) tuples.
            retrieved: Retrieved memories relevant to the conversation.
            memory_store: The agent's associative memory.

        Returns:
            ConversationResult with the utterance and conversation state.
        """
        pass

    @abstractmethod
    def decide_to_talk(self,
                       agent: "AgentContext",
                       other_agent: "AgentContext",
                       retrieved: Dict[str, "RetrievalResult"]
    ) -> Tuple[bool, str]:
        """
        Decide whether to initiate conversation with another agent.

        Args:
            agent: This agent's context.
            other_agent: The potential conversation partner's context.
            retrieved: Retrieved memories about the other agent.

        Returns:
            Tuple of (should_talk: bool, reason: str)
        """
        pass
