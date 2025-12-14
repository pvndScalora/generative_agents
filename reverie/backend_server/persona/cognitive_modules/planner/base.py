from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, TYPE_CHECKING
from reverie.backend_server.models import Memory

if TYPE_CHECKING:
    from reverie.backend_server.maze import Maze
    from persona.persona import Persona

class AbstractPlanner(ABC):
    """
    Abstract base class for the Planning cognitive module.
    
    The Planner is responsible for generating the agent's daily schedule and 
    determining the next immediate action based on the current state and retrieved memories.
    """

    @abstractmethod
    def plan(self, maze: "Maze", personas: Dict[str, "Persona"], new_day: Any, retrieved: Dict[str, Dict[str, Any]]) -> str:
        """
        Main cognitive function for planning.

        Args:
            maze: The Maze instance of the current world.
            personas: A dictionary of all Persona instances in the world.
            new_day: Indicates if it is a new day cycle (False, "First day", or "New day").
            retrieved: A dictionary of relevant memories (output from the Retriever).

        Returns:
            The target action address of the persona (e.g., "world:sector:arena:game_object").
        """
        pass
