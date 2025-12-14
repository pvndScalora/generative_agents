from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from reverie.backend_server.maze import Maze
    from persona.persona import Persona

class AbstractConverser(ABC):
    """
    responsible for managing conversational interactions for a persona.
    """
    @abstractmethod
    def open_session(self, convo_mode: str):
        pass

    @abstractmethod
    def chat(self, maze: "Maze", target_persona: "Persona"):
        pass
