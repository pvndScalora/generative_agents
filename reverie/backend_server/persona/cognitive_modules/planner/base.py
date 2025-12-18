from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Union, TYPE_CHECKING

if TYPE_CHECKING:
    from reverie.backend_server.maze import Maze
    from reverie.backend_server.models import (
        AgentContext, WorldContext, RetrievalResult, PlanResult
    )


class AbstractPlanner(ABC):
    """
    Abstract base class for the Planning cognitive module.
    
    Responsibility: Decide what the agent should do next.
    
    Does NOT: Execute actions, modify state directly, handle conversations.
    All decisions are returned as PlanResult and applied by Persona.
    """

    @abstractmethod
    def plan(self,
             agent: "AgentContext",
             world: "WorldContext",
             maze: "Maze",
             retrieved: Dict[str, "RetrievalResult"],
             other_agents: Dict[str, "AgentContext"],
             is_new_day: Union[bool, str]
    ) -> "PlanResult":
        """
        Main cognitive function for planning.

        Args:
            agent: Immutable snapshot of this agent's current state.
            world: Immutable snapshot of the visible world.
            maze: The Maze instance for spatial reasoning.
            retrieved: Dictionary of relevant memories from the Retriever.
            other_agents: Dictionary of other agents' contexts (name -> AgentContext).
                         NOT full Persona objects to prevent tight coupling.
            is_new_day: False, "First day", or "New day" indicating day transitions.

        Returns:
            PlanResult containing the decided action and any schedule updates.
        """
        pass
