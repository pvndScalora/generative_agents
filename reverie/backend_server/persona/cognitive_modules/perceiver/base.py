from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from reverie.backend_server.maze import Maze

class AbstractPerceiver(ABC):
    @abstractmethod
    def perceive(self, maze: "Maze"):
        pass
