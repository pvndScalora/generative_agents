from abc import ABC, abstractmethod

class AbstractReflector(ABC):
    @abstractmethod
    def reflect(self):
        pass
