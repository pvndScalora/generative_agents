from abc import ABC, abstractmethod
from typing import Dict, Any, TYPE_CHECKING
from reverie.backend_server.models import PlanExecution

if TYPE_CHECKING:
    from reverie.backend_server.maze import Maze
    from persona.persona import Persona

class AbstractExecutor(ABC):
    @abstractmethod
    def execute(self, maze: "Maze", personas: Dict[str, "Persona"], plan: str) -> PlanExecution:
        pass
