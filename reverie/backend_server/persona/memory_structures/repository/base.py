from abc import ABC, abstractmethod
from persona.memory_structures.spatial_memory import MemoryTree
from persona.memory_structures.associative_memory import AssociativeMemory
from persona.memory_structures.scratch import Scratch

class MemoryRepository(ABC):
    @abstractmethod
    def load_spatial_memory(self) -> MemoryTree:
        pass

    @abstractmethod
    def save_spatial_memory(self, memory: MemoryTree, save_folder: str):
        pass

    @abstractmethod
    def load_associative_memory(self) -> AssociativeMemory:
        pass

    @abstractmethod
    def save_associative_memory(self, memory: AssociativeMemory, save_folder: str):
        pass

    @abstractmethod
    def load_scratch(self) -> Scratch:
        pass

    @abstractmethod
    def save_scratch(self, scratch: Scratch, save_folder: str):
        pass
