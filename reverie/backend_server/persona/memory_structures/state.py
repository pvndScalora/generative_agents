from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple, TYPE_CHECKING
import datetime
from reverie.backend_server.models import (
    PersonaIdentity, CognitiveParams, CurrentAction, Coordinate, Action
)

if TYPE_CHECKING:
    from .associative_memory import AssociativeMemory
    from .spatial_memory import MemoryTree

@dataclass
class IdentityProfile:
    """
    Static or semi-static attributes defining 'who' the agent is.
    """
    identity: PersonaIdentity
    cognitive_params: CognitiveParams

@dataclass
class WorldContext:
    """
    The agent's current perceived position in space and time.
    """
    # Perceived world time.
    curr_time: Optional[datetime.datetime] = None
    # Current x,y tile coordinate of the persona.
    curr_tile: Optional[Coordinate] = None

@dataclass
class MemorySystem:
    """
    The database of the agent's experiences.
    """
    spatial_memory: Optional["MemoryTree"] = None
    associative_memory: Optional["AssociativeMemory"] = None

@dataclass
class ExecutiveState:
    """
    High-level goals, plans, and schedules.
    """
    # Perceived world daily requirement.
    daily_plan_req: str = ""
    
    # <daily_req> is a list of various goals the persona is aiming to achieve
    # today. 
    # e.g., ['Work on her paintings for her upcoming show', 
    #        'Take a break to watch some TV', 
    #        'Make lunch for herself', 
    #        'Work on her paintings some more', 
    #        'Go to bed early']
    # They have to be renewed at the end of the day, which is why we are
    # keeping track of when they were first generated. 
    daily_req: List[str] = field(default_factory=list)
    
    # <f_daily_schedule> denotes a form of long term planning. This lays out 
    # the persona's daily plan. 
    # Note that we take the long term planning and short term decomposition 
    # appoach, which is to say that we first layout hourly schedules and 
    # gradually decompose as we go. 
    # Three things to note in the example below: 
    # 1) See how "sleeping" was not decomposed -- some of the common events 
    #    really, just mainly sleeping, are hard coded to be not decomposable.
    # 2) Some of the elements are starting to be decomposed... More of the 
    #    things will be decomposed as the day goes on (when they are 
    #    decomposed, they leave behind the original hourly action description
    #    in tact).
    # 3) The latter elements are not decomposed. When an event occurs, the
    #    non-decomposed elements go out the window.  
    # e.g., [['sleeping', 360], 
    #         ['wakes up and ... (wakes up and stretches ...)', 5], 
    #         ['wakes up and starts her morning routine (out of bed )', 10],
    #         ...
    #         ['having lunch', 60], 
    #         ['working on her painting', 180], ...]
    f_daily_schedule: List[Action] = field(default_factory=list)
    
    # <f_daily_schedule_hourly_org> is a replica of f_daily_schedule
    # initially, but retains the original non-decomposed version of the hourly
    # schedule. 
    # e.g., [['sleeping', 360], 
    #        ['wakes up and starts her morning routine', 120],
    #        ['working on her painting', 240], ... ['going to bed', 60]]
    f_daily_schedule_hourly_org: List[Action] = field(default_factory=list)

@dataclass
class ActionState:
    """
    Immediate execution details for the current moment.
    """
    # CURR ACTION 
    current_action: CurrentAction = field(default_factory=CurrentAction)
    
    # <path_set> is True if we've already calculated the path the persona will
    # take to execute this action. That path is stored in the persona's 
    # scratch.planned_path.
    act_path_set: bool = False
    
    # <planned_path> is a list of x y coordinate tuples (tiles) that describe
    # the path the persona is to take to execute the <curr_action>. 
    # The list does not include the persona's current tile, and includes the 
    # destination tile. 
    # e.g., [(50, 10), (49, 10), (48, 10), ...]
    planned_path: List[Coordinate] = field(default_factory=list)

@dataclass
class SocialContext:
    """
    Ephemeral state related to active conversations.
    """
    # <chatting_with> is the string name of the persona that the current 
    # persona is chatting with. None if it does not exist. 
    chatting_with: Optional[str] = None
    
    # <chat> is a list of list that saves a conversation between two personas.
    # It comes in the form of: [["Dolores Murphy", "Hi"], 
    #                           ["Maeve Jenson", "Hi"] ...]
    chat: Optional[List[List[str]]] = None
    
    # <chatting_with_buffer>  
    # e.g., ["Dolores Murphy"] = self.vision_r
    chatting_with_buffer: Dict[str, int] = field(default_factory=dict)
    
    chatting_end_time: Optional[datetime.datetime] = None

@dataclass
class PersonaState:
    """
    The composed state object for a Persona.
    """
    identity_profile: IdentityProfile
    world_context: WorldContext
    executive_state: ExecutiveState
    action_state: ActionState
    social_context: SocialContext
    memory_system: MemorySystem = field(default_factory=MemorySystem)

