from abc import ABC, abstractmethod

class AbstractConverser(ABC):
    @abstractmethod
    def open_session(self, convo_mode):
        pass

    @abstractmethod
    def chat(self, maze, target_persona):
        pass
