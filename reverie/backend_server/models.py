from dataclasses import dataclass, field
from typing import List, Optional, Set, Dict, Any, Tuple, Union
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

    def __iter__(self):
        return iter((self.x, self.y))
    
    def __getitem__(self, item):
        return (self.x, self.y)[item]

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

    def __iter__(self):
        return iter((self.description, self.duration))
    
    def __getitem__(self, item):
        return (self.description, self.duration)[item]

@dataclass
class PlanExecution:
    """
    Represents the concrete execution details for a time step.
    """
    next_tile: Tuple[int, int]
    pronunciatio: str
    description: str

    def __iter__(self):
        return iter((self.next_tile, self.pronunciatio, self.description))


@dataclass
class CurrentAction:
    """
    Represents the action currently being executed by the persona.
    Includes execution details like start time, location, and object interactions.
    """
    address: Optional[str] = None
    start_time: Optional[datetime] = None
    duration: Optional[int] = None
    description: Optional[str] = None
    pronunciatio: Optional[str] = None
    event: Tuple[str, Optional[str], Optional[str]] = field(default_factory=lambda: ("", None, None))
    
    # Object interaction details
    obj_description: Optional[str] = None
    obj_pronunciatio: Optional[str] = None
    obj_event: Tuple[str, Optional[str], Optional[str]] = field(default_factory=lambda: ("", None, None))

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
    
    # Legacy fields for compatibility
    depth: int = 0
    node_count: int = 0
    type_count: int = 0

    def spo_summary(self): 
        return (self.subject, self.predicate, self.object)

    def __hash__(self):
        return hash(self.id)
    
    def __eq__(self, other):
        if isinstance(other, Memory):
            return self.id == other.id
        return False

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
    age: int # Age of the persona
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
    importance_ele_n: int = 0
    thought_count: int = 5
    
    # Reflection Tuning
    concept_forget: int = 100
    daily_reflection_time: int = 60 * 3
    overlap_reflect_th: int = 2
    kw_strg_event_reflect_th: int = 4
    kw_strg_thought_reflect_th: int = 4

    # Planning
    daily_reflection_size: int = 5 # Number of focal points to generate

    # Perception & Attention
    vision_r: int = 4 # Number of tiles the persona can see
    att_bandwidth: int = 3 # Attention bandwidth
    retention: int = 5 # Memory retention factor

# Type alias for the Spatial Memory Tree structure
# Structure: World -> Sector -> Arena -> List[GameObjects]
# Example Tree:
# {
#   "the Ville": {
#     "Isabella's Apartment": {
#       "Main Room": ["bed", "desk", "closet"],
#       "Bathroom": ["shower", "sink", "toilet"]
#     },
#     "Hobbs Cafe": {
#       "Cafe": ["counter", "table", "chair"]
#     }
#   }
# }
SpatialMemoryTree = Dict[str, Dict[str, Dict[str, List[str]]]]


# ==============================================================================
# INPUT CONTRACTS - Immutable snapshots passed to cognitive modules
# ==============================================================================

@dataclass(frozen=True)
class AgentIdentity:
    """
    Immutable identity snapshot passed to cognitive modules.
    
    This is a read-only view of the agent's identity traits used
    for decision-making without allowing modules to modify state.
    """
    name: str
    age: int
    innate_traits: str      # Core personality (e.g., "curious, analytical")
    learned_traits: str     # Backstory/occupation
    current_focus: str      # Current goal/context
    lifestyle: str          # Daily routine description
    living_area: str        # Home address string


@dataclass(frozen=True)
class AgentContext:
    """
    Immutable snapshot of agent state passed to all cognitive modules.
    
    Modules CANNOT modify this — they can only read it. This enables
    pure function-like cognitive modules that are easy to test and swap.
    
    Example:
        context = AgentContext(
            identity=AgentIdentity(...),
            vision_radius=4,
            attention_bandwidth=3,
            retention=5,
            current_time=datetime(2023, 2, 13, 10, 0),
            current_tile=(58, 39),
            daily_requirements=["work on painting", "have lunch"],
            daily_schedule=[("sleeping", 360), ("morning routine", 60)],
            current_action=CurrentAction(...)
        )
    """
    identity: AgentIdentity
    
    # Cognitive parameters
    vision_radius: int
    attention_bandwidth: int
    retention: int
    
    # Retrieval weights
    recency_weight: float
    relevance_weight: float
    importance_weight: float
    recency_decay: float
    
    # Reflection parameters
    importance_trigger_max: int
    importance_trigger_curr: int
    thought_count: int
    
    # Current world state
    current_time: datetime
    current_tile: Tuple[int, int]
    
    # Current plans
    daily_requirements: Tuple[str, ...]  # Immutable tuple
    daily_schedule: Tuple[Tuple[str, int], ...]  # ((action, duration), ...)
    
    # Current action (if any)
    current_action: Optional["CurrentAction"] = None


@dataclass(frozen=True)
class WorldContext:
    """
    Immutable snapshot of what the agent can perceive in the world.
    
    Example:
        world = WorldContext(
            nearby_tiles=[(57, 38), (57, 39), (58, 38)],
            current_arena_path="the Ville:Hobbs Cafe:cafe",
            accessible_arenas=["cafe", "kitchen", "bathroom"]
        )
    """
    nearby_tiles: Tuple[Tuple[int, int], ...]  # Tiles within vision radius
    current_arena_path: str  # "world:sector:arena"
    accessible_arenas: Tuple[str, ...]  # Arenas the agent knows about


# ==============================================================================
# OUTPUT CONTRACTS - Explicit return types from cognitive modules
# ==============================================================================

@dataclass
class PerceptionResult:
    """
    Output from Perceiver module.
    
    Contains the memories created from perceived events and metadata
    about what was filtered out (useful for debugging/analysis).
    """
    new_memories: List["Memory"]        # Events worth remembering
    spatial_updates: Dict[str, Any]     # Updates to spatial memory tree
    ignored_events: List[str] = field(default_factory=list)  # Filtered out events


@dataclass  
class RetrievalResult:
    """
    Output from Retriever for a single query/focal point.
    
    Contains the relevant memories found and their scores.
    """
    query_event: Optional["Memory"]          # The event that triggered retrieval
    relevant_events: List["Memory"]          # Past events related to query
    relevant_thoughts: List["Memory"]        # Past reflections related to query
    relevance_scores: Dict[str, float] = field(default_factory=dict)  # Memory ID -> score


@dataclass
class PlanResult:
    """
    Output from Planner module.
    
    Contains the decided action and any schedule updates.
    This is the single source of truth for what the agent will do next.
    """
    # Required: What to do
    action_address: str                 # "world:sector:arena:object" or "<persona>Name"
    action_description: str             # "ordering coffee"
    action_duration: int                # minutes
    action_start_time: datetime         # When this action starts
    action_event: Tuple[str, str, str]  # (subject, predicate, object)
    action_emoji: str                   # Pronunciatio emoji
    
    # Object interaction (optional)
    object_description: Optional[str] = None
    object_emoji: Optional[str] = None
    object_event: Optional[Tuple[str, str, str]] = None
    
    # Schedule updates (optional)
    new_daily_schedule: Optional[List[Tuple[str, int]]] = None
    new_daily_requirements: Optional[List[str]] = None
    
    # Chat state (optional)
    chatting_with: Optional[str] = None
    chat_end_time: Optional[datetime] = None


@dataclass
class ReflectionResult:
    """
    Output from Reflector module.
    
    Contains new thoughts/insights generated and metadata for
    updating the reflection trigger counters.
    """
    new_thoughts: List["Memory"]          # New insights to store
    focal_points: List[str]               # What triggered reflection
    importance_accumulated: int = 0       # For threshold tracking
    should_reset_counter: bool = False    # Whether to reset importance counter


@dataclass
class ExecutionResult:
    """
    Output from Executor module.
    
    The concrete movement/action output for this time step.
    Same structure as PlanExecution but explicitly named as output contract.
    """
    next_tile: Tuple[int, int]
    pronunciatio: str
    description: str
    planned_path: List[Tuple[int, int]] = field(default_factory=list)


@dataclass
class ConversationResult:
    """
    Output from Converser module for a single conversation turn.
    """
    utterance: str
    end_conversation: bool
    conversation_summary: Optional[str] = None
    planning_thought: Optional[str] = None
    memo_thought: Optional[str] = None

