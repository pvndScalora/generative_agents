from dataclasses import dataclass, field
from typing import List, Optional, Set, Dict, Any
from datetime import datetime
from enum import Enum

@dataclass
class Coordinate:
    """
    Represents a location on the 2D grid map.
    
    Example:
        loc = Coordinate(x=58, y=39)
    """
    x: int
    y: int
    
    def as_tuple(self):
        return (self.x, self.y)

@dataclass
class Action:
    """
    Represents a single unit of activity in the agent's schedule.
    
    Example:
        # "sleeping" for 360 minutes (6 hours)
        act = Action(description="sleeping", duration=360)
        
        # "making coffee" for 10 minutes
        act = Action(description="making coffee", duration=10)
    """
    description: str
    duration: int # in minutes
    
    @property
    def is_decomposed(self) -> bool:
        # Logic to check if this action needs further breakdown
        # Currently inferred from context in the original code
        return False

class MemoryType(Enum):
    """
    Categorizes the type of memory node.
    """
    EVENT = "event"     # Raw observation (e.g., "Isabella saw the bed")
    THOUGHT = "thought" # Generated insight (e.g., "Isabella thinks the bed is messy")
    CHAT = "chat"       # Conversation log (e.g., "Isabella talked to Klaus")

@dataclass
class Memory:
    """
    Represents a node in the Associative Memory graph (ConceptNode).
    
    Example:
        mem = Memory(
            id="node_45",
            type=MemoryType.EVENT,
            description="Klaus is reading a book",
            created=datetime(2023, 1, 1, 10, 0),
            last_accessed=datetime(2023, 1, 1, 10, 0),
            subject="Klaus",
            predicate="is",
            object="reading a book",
            poignancy=5,
            keywords={"klaus", "reading", "book"},
            embedding_key="Klaus is reading a book"
        )
    """
    id: str
    type: MemoryType
    description: str
    created: datetime
    last_accessed: datetime
    
    # The "Subject, Predicate, Object" triple
    # Used for semantic searching and summary
    subject: str
    predicate: str
    object: str
    
    # Retrieval scoring
    poignancy: int # 1-10 score of how emotionally important this memory is
    keywords: Set[str] # Searchable keywords
    
    # Embedding
    # embedding_key: The text string used to generate the vector
    embedding_key: str
    embedding: Optional[List[float]] = None # Vector representation (e.g., 1536 floats from OpenAI)
    
    # For thoughts/reflections
    # filling: List of node_ids that served as evidence for this thought
    filling: List[Any] = field(default_factory=list) 
    expiration: Optional[datetime] = None

@dataclass
class PersonaIdentity:
    """
    Encapsulates the core identity traits of a persona.
    
    Example:
        identity = PersonaIdentity(
            name="Isabella Rodriguez",
            innate="friendly, outgoing, hospitable",
            learned="Isabella is a cafe owner who loves to make people feel welcome.",
            currently="Isabella is planning a Valentine's Day party.",
            lifestyle="Isabella goes to bed around 11pm and wakes up at 6am.",
            living_area="the Ville:Isabella's Apartment:Main Room"
        )
    """
    name: str
    innate: str # L0 traits (Core personality)
    learned: str # L1 traits (Backstory/Occupation)
    currently: str # L2 status (Current goal/Context)
    lifestyle: str # Daily routine description
    living_area: str # Home address string

@dataclass
class CognitiveParams:
    """
    Hyperparameters controlling the agent's cognitive processes.
    
    Example:
        params = CognitiveParams(
            recency_weight=0.5,
            relevance_weight=3.0, # Highly focused on relevance
            importance_trigger_max=200 # Reflect less often
        )
    """
    # Retrieval Weights (Score = w1*Recency + w2*Relevance + w3*Importance)
    recency_weight: float = 1.0
    relevance_weight: float = 1.0
    importance_weight: float = 1.0
    recency_decay: float = 0.99 # Exponential decay factor
    
    # Reflection Triggers
    importance_trigger_max: int = 150 # Threshold to trigger reflection
    importance_trigger_curr: int = 150 # Current counter
    
    # Planning
    daily_reflection_size: int = 5 # Number of focal points to generate
