from abc import ABC, abstractmethod

class AbstractPerceiver(ABC):
    @abstractmethod
    def perceive(self, maze):
        pass
