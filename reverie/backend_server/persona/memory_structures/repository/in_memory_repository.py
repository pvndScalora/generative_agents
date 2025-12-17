"""
In-memory repository for testing purposes.

This repository keeps all data in memory without persistence,
useful for unit testing and experimentation.
"""
from typing import Optional
from .base import MemoryRepository
from reverie.backend_server.persona.memory_structures.spatial_memory import MemoryTree
from reverie.backend_server.persona.memory_structures.associative_memory import AssociativeMemory
from reverie.backend_server.persona.memory_structures.scratch import Scratch
from reverie.backend_server.persona.memory_structures.state import (
    PersonaState, IdentityProfile, WorldContext, ExecutiveState,
    ActionState, SocialContext
)
from reverie.backend_server.models import PersonaIdentity, CognitiveParams


def _create_empty_persona_state() -> PersonaState:
    """Create an empty PersonaState with default values."""
    identity = PersonaIdentity(
        name="Test Agent",
        age=25,
        innate="curious, helpful",
        learned="",
        currently="",
        lifestyle="",
        living_area=""
    )
    return PersonaState(
        identity_profile=IdentityProfile(identity, CognitiveParams()),
        world_context=WorldContext(),
        executive_state=ExecutiveState(),
        action_state=ActionState(),
        social_context=SocialContext()
    )


class InMemoryRepository(MemoryRepository):
    """
    In-memory implementation of MemoryRepository for testing.
    
    All data is stored in memory and lost when the object is destroyed.
    Useful for unit tests where persistence is not needed.
    """
    
    def __init__(self):
        self._spatial_memory: Optional[MemoryTree] = None
        self._associative_memory: Optional[AssociativeMemory] = None
        self._scratch: Optional[Scratch] = None
    
    def load_spatial_memory(self) -> MemoryTree:
        """Load or create empty spatial memory."""
        if self._spatial_memory is None:
            self._spatial_memory = MemoryTree({})
        return self._spatial_memory
    
    def save_spatial_memory(self, memory: MemoryTree, save_folder: str):
        """Store spatial memory in memory (folder is ignored)."""
        self._spatial_memory = memory
    
    def load_associative_memory(self) -> AssociativeMemory:
        """Load or create empty associative memory."""
        if self._associative_memory is None:
            self._associative_memory = AssociativeMemory()
        return self._associative_memory
    
    def save_associative_memory(self, memory: AssociativeMemory, save_folder: str):
        """Store associative memory in memory (folder is ignored)."""
        self._associative_memory = memory
    
    def load_scratch(self) -> Scratch:
        """Load or create empty scratch with PersonaState."""
        if self._scratch is None:
            # Create Scratch with an empty PersonaState (new way)
            state = _create_empty_persona_state()
            self._scratch = Scratch(state)
        return self._scratch
    
    def save_scratch(self, scratch: Scratch, save_folder: str):
        """Store scratch in memory (folder is ignored)."""
        self._scratch = scratch
