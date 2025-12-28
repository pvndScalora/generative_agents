from abc import ABC, abstractmethod
from typing import Dict, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from maze import Maze
    from models import (
        AgentContext, PlanResult, ExecutionResult
    )


class AbstractExecutor(ABC):
    """
    Abstract base class for the Execution cognitive module.
    
    Responsibility: Convert a plan into concrete movement/action.
    
    Does NOT: Decide what to do, access memories, call LLMs.
    This is primarily pathfinding and action translation.
    """

    @abstractmethod
    def execute(self,
                agent: "AgentContext",
                plan: "PlanResult",
                maze: "Maze",
                other_agents: Dict[str, "AgentContext"]
    ) -> "ExecutionResult":
        """
        Convert a plan into concrete tile movement and action output.

        Args:
            agent: Immutable snapshot of the agent's current state.
            plan: The PlanResult from the Planner containing action details.
            maze: The Maze instance for pathfinding.
            other_agents: Other agents' contexts for collision avoidance.

        Returns:
            ExecutionResult with next_tile, pronunciatio, and description.
        """
        pass
