from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from maze import Maze
    from models import (
        AgentContext, WorldContext, PerceptionResult, Memory
    )
    from persona.memory_structures.spatial_memory import MemoryTree


class AbstractPerceiver(ABC):
    """
    Abstract base class for the Perception cognitive module.
    
    Responsibility: Filter world events into memorable observations.
    
    Does NOT: Modify state directly, access scratch, know about other modules.
    All state changes are returned as PerceptionResult and applied by Persona.
    """

    @abstractmethod
    def perceive(self, 
                 agent: "AgentContext",
                 world: "WorldContext",
                 maze: "Maze",
                 spatial_memory: "MemoryTree",
                 recent_memories: List["Memory"]
    ) -> "PerceptionResult":
        """
        Perceive events around the agent and determine what's worth remembering.
        
        Args:
            agent: Immutable snapshot of the agent's current state.
            world: Immutable snapshot of the visible world.
            maze: The Maze instance for accessing tile details.
            spatial_memory: The agent's spatial memory tree (read-only for decisions).
            recent_memories: Recent memories for retention filtering.
            
        Returns:
            PerceptionResult containing new memories to store and spatial updates.
        """
        pass
