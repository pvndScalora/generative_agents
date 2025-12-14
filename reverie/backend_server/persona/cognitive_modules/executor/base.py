from abc import ABC, abstractmethod

class AbstractExecutor(ABC):
    @abstractmethod
    def execute(self, maze, personas, plan):
        pass
