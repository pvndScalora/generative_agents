"""
Author: Joon Sung Park (joonspk@stanford.edu)
Refactored: Hexagonal Architecture cleanup

File: scratch.py
Description: Defines the short-term memory module for generative agents.

Architecture Note:
    This class is now a thin wrapper around PersonaState, providing
    backward-compatible property access. Business logic has been moved
    to state_services.py (pure functions). Serialization has been moved
    to JsonMemoryRepository (adapter).
    
    New code should prefer:
    - Direct PersonaState access for state
    - state_services functions for logic
    - Repository adapters for persistence
"""
import datetime
from typing import Dict, Any, List, Optional, Union, TYPE_CHECKING

from models import (
    PersonaIdentity, CognitiveParams, CurrentAction, Coordinate, Action
)
from .state import (
    PersonaState, IdentityProfile, WorldContext, ExecutiveState, 
    ActionState, SocialContext, MemorySystem, create_empty_persona_state
)
from . import state_services as svc

if TYPE_CHECKING:
    from .associative_memory import AssociativeMemory
    from .spatial_memory import MemoryTree


class Scratch:
    """
    Short-term memory module for generative agents.
    
    This class provides backward-compatible access to persona state while
    delegating business logic to pure functions in state_services.py.
    
    The class can be initialized with:
    - PersonaState object (new way, from repository)
    - dict (legacy way, for backward compatibility)
    - None (creates empty state)
    
    Architecture:
        Scratch is now a FACADE that:
        1. Wraps PersonaState (domain object)
        2. Provides property-based access for legacy code
        3. Delegates logic to state_services (pure functions)
        
        It does NOT:
        - Know about JSON keys (that's in JsonMemoryRepository)
        - Contain business logic (that's in state_services)
    """
    
    def __init__(self, state_or_legacy: Union[PersonaState, dict, None] = None):
        """
        Initialize Scratch with state.
        
        Args:
            state_or_legacy: One of:
                - PersonaState: Direct state injection (preferred)
                - dict: Legacy JSON dict (for backward compatibility)
                - None: Create empty state
        """
        if isinstance(state_or_legacy, PersonaState):
            # New way: direct PersonaState injection
            self.state = state_or_legacy
        elif isinstance(state_or_legacy, dict):
            # Legacy way: parse dict (DEPRECATED - use repository instead)
            self.state = self._legacy_parse_dict(state_or_legacy)
        else:
            # Empty state
            self.state = create_empty_persona_state()

    def _legacy_parse_dict(self, d: dict) -> PersonaState:
        """
        DEPRECATED: Parse legacy dict format.
        
        This exists only for backward compatibility. New code should use
        JsonMemoryRepository which handles all serialization.
        """
        import warnings
        warnings.warn(
            "Passing dict to Scratch.__init__ is deprecated. "
            "Use JsonMemoryRepository.load_scratch() instead.",
            DeprecationWarning,
            stacklevel=3
        )
        
        # Create identity
        identity = PersonaIdentity(
            name=d.get("name", ""),
            age=d.get("age", 0),
            innate=d.get("innate", ""),
            learned=d.get("learned", ""),
            currently=d.get("currently", ""),
            lifestyle=d.get("lifestyle", ""),
            living_area=d.get("living_area", "")
        )
        
        # Create cognitive params
        cognitive_params = CognitiveParams(
            vision_r=d.get("vision_r", 4),
            att_bandwidth=d.get("att_bandwidth", 3),
            retention=d.get("retention", 5),
            concept_forget=d.get("concept_forget", 100),
            daily_reflection_time=d.get("daily_reflection_time", 180),
            daily_reflection_size=d.get("daily_reflection_size", 5),
            overlap_reflect_th=d.get("overlap_reflect_th", 2),
            kw_strg_event_reflect_th=d.get("kw_strg_event_reflect_th", 4),
            kw_strg_thought_reflect_th=d.get("kw_strg_thought_reflect_th", 4),
            recency_weight=d.get("recency_w", 1.0),
            relevance_weight=d.get("relevance_w", 1.0),
            importance_weight=d.get("importance_w", 1.0),
            recency_decay=d.get("recency_decay", 0.99),
            importance_trigger_max=d.get("importance_trigger_max", 150),
            importance_trigger_curr=d.get("importance_trigger_curr", 150),
            importance_ele_n=d.get("importance_ele_n", 0),
            thought_count=d.get("thought_count", 5)
        )
        
        # Parse world context
        curr_time = None
        if d.get("curr_time"):
            curr_time = datetime.datetime.strptime(d["curr_time"], "%B %d, %Y, %H:%M:%S")
        
        curr_tile = None
        if d.get("curr_tile"):
            curr_tile = Coordinate(*d["curr_tile"])
        
        # Parse schedules
        f_daily_schedule = [
            Action(description=x[0], duration=x[1]) 
            for x in d.get("f_daily_schedule", [])
        ]
        f_daily_schedule_hourly_org = [
            Action(description=x[0], duration=x[1]) 
            for x in d.get("f_daily_schedule_hourly_org", [])
        ]
        
        # Parse action
        act_start_time = None
        if d.get("act_start_time"):
            act_start_time = datetime.datetime.strptime(d["act_start_time"], "%B %d, %Y, %H:%M:%S")
        
        current_action = CurrentAction(
            address=d.get("act_address"),
            start_time=act_start_time,
            duration=d.get("act_duration"),
            description=d.get("act_description"),
            pronunciatio=d.get("act_pronunciatio"),
            event=tuple(d.get("act_event", ("", None, None))),
            obj_description=d.get("act_obj_description"),
            obj_pronunciatio=d.get("act_obj_pronunciatio"),
            obj_event=tuple(d.get("act_obj_event", ("", None, None)))
        )
        
        planned_path = [Coordinate(*p) for p in d.get("planned_path", [])]
        
        # Parse social
        chatting_end_time = None
        if d.get("chatting_end_time"):
            chatting_end_time = datetime.datetime.strptime(d["chatting_end_time"], "%B %d, %Y, %H:%M:%S")
        
        return PersonaState(
            identity_profile=IdentityProfile(identity, cognitive_params),
            world_context=WorldContext(curr_time=curr_time, curr_tile=curr_tile),
            executive_state=ExecutiveState(
                daily_plan_req=d.get("daily_plan_req", ""),
                daily_req=d.get("daily_req", []),
                f_daily_schedule=f_daily_schedule,
                f_daily_schedule_hourly_org=f_daily_schedule_hourly_org
            ),
            action_state=ActionState(
                current_action=current_action,
                act_path_set=d.get("act_path_set", False),
                planned_path=planned_path
            ),
            social_context=SocialContext(
                chatting_with=d.get("chatting_with"),
                chat=d.get("chat"),
                chatting_with_buffer=d.get("chatting_with_buffer", {}),
                chatting_end_time=chatting_end_time
            )
        )

    # =========================================================================
    # HELPER PROPERTIES
    # =========================================================================

    @property
    def scratch(self):
        """Allow this object to be passed where 'persona.scratch' is expected."""
        return self

    @property
    def identity(self) -> PersonaIdentity:
        return self.state.identity_profile.identity
    
    @property
    def cognitive_params(self) -> CognitiveParams:
        return self.state.identity_profile.cognitive_params

    # =========================================================================
    # WORLD CONTEXT PROPERTIES
    # =========================================================================

    @property
    def curr_time(self) -> Optional[datetime.datetime]:
        return self.state.world_context.curr_time
    
    @curr_time.setter
    def curr_time(self, value: datetime.datetime):
        self.state.world_context.curr_time = value

    @property
    def curr_tile(self) -> Optional[Coordinate]:
        return self.state.world_context.curr_tile
    
    @curr_tile.setter
    def curr_tile(self, value):
        if isinstance(value, (list, tuple)):
            value = Coordinate(*value)
        self.state.world_context.curr_tile = value

    # =========================================================================
    # EXECUTIVE STATE PROPERTIES
    # =========================================================================

    @property
    def daily_plan_req(self) -> str:
        return self.state.executive_state.daily_plan_req
    
    @daily_plan_req.setter
    def daily_plan_req(self, value: str):
        self.state.executive_state.daily_plan_req = value

    @property
    def daily_req(self) -> List[str]:
        return self.state.executive_state.daily_req
    
    @daily_req.setter
    def daily_req(self, value: List[str]):
        self.state.executive_state.daily_req = value

    @property
    def f_daily_schedule(self) -> List[Action]:
        return self.state.executive_state.f_daily_schedule
    
    @f_daily_schedule.setter
    def f_daily_schedule(self, value: List[Action]):
        self.state.executive_state.f_daily_schedule = value

    @property
    def f_daily_schedule_hourly_org(self) -> List[Action]:
        return self.state.executive_state.f_daily_schedule_hourly_org
    
    @f_daily_schedule_hourly_org.setter
    def f_daily_schedule_hourly_org(self, value: List[Action]):
        self.state.executive_state.f_daily_schedule_hourly_org = value

    # =========================================================================
    # ACTION STATE PROPERTIES
    # =========================================================================

    @property
    def act(self) -> CurrentAction:
        return self.state.action_state.current_action
    
    @act.setter
    def act(self, value: CurrentAction):
        self.state.action_state.current_action = value

    @property
    def act_path_set(self) -> bool:
        return self.state.action_state.act_path_set
    
    @act_path_set.setter
    def act_path_set(self, value: bool):
        self.state.action_state.act_path_set = value

    @property
    def planned_path(self) -> List[Coordinate]:
        return self.state.action_state.planned_path
    
    @planned_path.setter
    def planned_path(self, value):
        if value and not isinstance(value[0], Coordinate):
            value = [Coordinate(*p) if isinstance(p, (list, tuple)) else p for p in value]
        self.state.action_state.planned_path = value

    # =========================================================================
    # SOCIAL CONTEXT PROPERTIES
    # =========================================================================

    @property
    def chatting_with(self) -> Optional[str]:
        return self.state.social_context.chatting_with
    
    @chatting_with.setter
    def chatting_with(self, value: Optional[str]):
        self.state.social_context.chatting_with = value

    @property
    def chat(self) -> Optional[List[List[str]]]:
        return self.state.social_context.chat
    
    @chat.setter
    def chat(self, value: Optional[List[List[str]]]):
        self.state.social_context.chat = value

    @property
    def chatting_with_buffer(self) -> Dict[str, int]:
        return self.state.social_context.chatting_with_buffer
    
    @chatting_with_buffer.setter
    def chatting_with_buffer(self, value: Dict[str, int]):
        self.state.social_context.chatting_with_buffer = value

    @property
    def chatting_end_time(self) -> Optional[datetime.datetime]:
        return self.state.social_context.chatting_end_time
    
    @chatting_end_time.setter
    def chatting_end_time(self, value: Optional[datetime.datetime]):
        self.state.social_context.chatting_end_time = value

    # =========================================================================
    # MEMORY SYSTEM PROPERTIES
    # =========================================================================

    @property
    def a_mem(self) -> Optional["AssociativeMemory"]:
        return self.state.memory_system.associative_memory

    @property
    def s_mem(self) -> Optional["MemoryTree"]:
        return self.state.memory_system.spatial_memory

    # =========================================================================
    # IDENTITY SHORTCUT PROPERTIES
    # =========================================================================

    @property
    def name(self) -> str:
        return self.identity.name
    
    @name.setter
    def name(self, value: str):
        self.identity.name = value

    @property
    def first_name(self) -> str:
        return self.identity.name.split(" ")[0] if self.identity.name else ""

    @property
    def last_name(self) -> str:
        return self.identity.name.split(" ")[-1] if self.identity.name else ""

    @property
    def age(self) -> int:
        return self.identity.age
    
    @age.setter
    def age(self, value: int):
        self.identity.age = value

    @property
    def innate(self) -> str:
        return self.identity.innate
    
    @innate.setter
    def innate(self, value: str):
        self.identity.innate = value

    @property
    def learned(self) -> str:
        return self.identity.learned
    
    @learned.setter
    def learned(self, value: str):
        self.identity.learned = value

    @property
    def currently(self) -> str:
        return self.identity.currently
    
    @currently.setter
    def currently(self, value: str):
        self.identity.currently = value

    @property
    def lifestyle(self) -> str:
        return self.identity.lifestyle
    
    @lifestyle.setter
    def lifestyle(self, value: str):
        self.identity.lifestyle = value

    @property
    def living_area(self) -> str:
        return self.identity.living_area
    
    @living_area.setter
    def living_area(self, value: str):
        self.identity.living_area = value

    # =========================================================================
    # COGNITIVE PARAMS SHORTCUT PROPERTIES
    # =========================================================================

    @property
    def vision_r(self) -> int:
        return self.cognitive_params.vision_r
    
    @vision_r.setter
    def vision_r(self, value: int):
        self.cognitive_params.vision_r = value

    @property
    def att_bandwidth(self) -> int:
        return self.cognitive_params.att_bandwidth
    
    @att_bandwidth.setter
    def att_bandwidth(self, value: int):
        self.cognitive_params.att_bandwidth = value

    @property
    def retention(self) -> int:
        return self.cognitive_params.retention
    
    @retention.setter
    def retention(self, value: int):
        self.cognitive_params.retention = value

    @property
    def concept_forget(self) -> int:
        return self.cognitive_params.concept_forget
    
    @concept_forget.setter
    def concept_forget(self, value: int):
        self.cognitive_params.concept_forget = value

    @property
    def daily_reflection_time(self) -> int:
        return self.cognitive_params.daily_reflection_time
    
    @daily_reflection_time.setter
    def daily_reflection_time(self, value: int):
        self.cognitive_params.daily_reflection_time = value

    @property
    def daily_reflection_size(self) -> int:
        return self.cognitive_params.daily_reflection_size
    
    @daily_reflection_size.setter
    def daily_reflection_size(self, value: int):
        self.cognitive_params.daily_reflection_size = value

    @property
    def overlap_reflect_th(self) -> int:
        return self.cognitive_params.overlap_reflect_th
    
    @overlap_reflect_th.setter
    def overlap_reflect_th(self, value: int):
        self.cognitive_params.overlap_reflect_th = value

    @property
    def kw_strg_event_reflect_th(self) -> int:
        return self.cognitive_params.kw_strg_event_reflect_th
    
    @kw_strg_event_reflect_th.setter
    def kw_strg_event_reflect_th(self, value: int):
        self.cognitive_params.kw_strg_event_reflect_th = value

    @property
    def kw_strg_thought_reflect_th(self) -> int:
        return self.cognitive_params.kw_strg_thought_reflect_th
    
    @kw_strg_thought_reflect_th.setter
    def kw_strg_thought_reflect_th(self, value: int):
        self.cognitive_params.kw_strg_thought_reflect_th = value

    @property
    def recency_w(self) -> float:
        return self.cognitive_params.recency_weight
    
    @recency_w.setter
    def recency_w(self, value: float):
        self.cognitive_params.recency_weight = value

    @property
    def relevance_w(self) -> float:
        return self.cognitive_params.relevance_weight
    
    @relevance_w.setter
    def relevance_w(self, value: float):
        self.cognitive_params.relevance_weight = value

    @property
    def importance_w(self) -> float:
        return self.cognitive_params.importance_weight
    
    @importance_w.setter
    def importance_w(self, value: float):
        self.cognitive_params.importance_weight = value

    @property
    def recency_decay(self) -> float:
        return self.cognitive_params.recency_decay
    
    @recency_decay.setter
    def recency_decay(self, value: float):
        self.cognitive_params.recency_decay = value

    @property
    def importance_trigger_max(self) -> int:
        return self.cognitive_params.importance_trigger_max
    
    @importance_trigger_max.setter
    def importance_trigger_max(self, value: int):
        self.cognitive_params.importance_trigger_max = value

    @property
    def importance_trigger_curr(self) -> int:
        return self.cognitive_params.importance_trigger_curr
    
    @importance_trigger_curr.setter
    def importance_trigger_curr(self, value: int):
        self.cognitive_params.importance_trigger_curr = value

    @property
    def importance_ele_n(self) -> int:
        return self.cognitive_params.importance_ele_n
    
    @importance_ele_n.setter
    def importance_ele_n(self, value: int):
        self.cognitive_params.importance_ele_n = value

    @property
    def thought_count(self) -> int:
        return self.cognitive_params.thought_count
    
    @thought_count.setter
    def thought_count(self, value: int):
        self.cognitive_params.thought_count = value

    # =========================================================================
    # ACTION SHORTCUT PROPERTIES
    # =========================================================================

    @property
    def act_address(self) -> Optional[str]:
        return self.act.address
    
    @act_address.setter
    def act_address(self, value: Optional[str]):
        self.act.address = value

    @property
    def act_start_time(self) -> Optional[datetime.datetime]:
        return self.act.start_time
    
    @act_start_time.setter
    def act_start_time(self, value: Optional[datetime.datetime]):
        self.act.start_time = value

    @property
    def act_duration(self) -> Optional[int]:
        return self.act.duration
    
    @act_duration.setter
    def act_duration(self, value: Optional[int]):
        self.act.duration = value

    @property
    def act_description(self) -> Optional[str]:
        return self.act.description
    
    @act_description.setter
    def act_description(self, value: Optional[str]):
        self.act.description = value

    @property
    def act_pronunciatio(self) -> Optional[str]:
        return self.act.pronunciatio
    
    @act_pronunciatio.setter
    def act_pronunciatio(self, value: Optional[str]):
        self.act.pronunciatio = value

    @property
    def act_event(self):
        return self.act.event
    
    @act_event.setter
    def act_event(self, value):
        self.act.event = tuple(value) if value else ("", None, None)

    @property
    def act_obj_description(self) -> Optional[str]:
        return self.act.obj_description
    
    @act_obj_description.setter
    def act_obj_description(self, value: Optional[str]):
        self.act.obj_description = value

    @property
    def act_obj_pronunciatio(self) -> Optional[str]:
        return self.act.obj_pronunciatio
    
    @act_obj_pronunciatio.setter
    def act_obj_pronunciatio(self, value: Optional[str]):
        self.act.obj_pronunciatio = value

    @property
    def act_obj_event(self):
        return self.act.obj_event
    
    @act_obj_event.setter
    def act_obj_event(self, value):
        self.act.obj_event = tuple(value) if value else ("", None, None)

    # =========================================================================
    # BUSINESS LOGIC - Delegated to state_services (pure functions)
    # =========================================================================

    def get_f_daily_schedule_index(self, advance: int = 0) -> int:
        """Get current index in f_daily_schedule. Delegates to pure function."""
        return svc.get_schedule_index(self.state, advance)

    def get_f_daily_schedule_hourly_org_index(self, advance: int = 0) -> int:
        """Get current index in f_daily_schedule_hourly_org. Delegates to pure function."""
        return svc.get_hourly_schedule_index(self.state, advance)

    def get_str_iss(self) -> str:
        """Get identity stable set string. Delegates to pure function."""
        return svc.format_identity_summary(self.state)

    def get_str_name(self) -> str:
        return self.name

    def get_str_firstname(self) -> str:
        return self.first_name

    def get_str_lastname(self) -> str:
        return self.last_name

    def get_str_age(self) -> str:
        return str(self.age)

    def get_str_innate(self) -> str:
        return self.innate

    def get_str_learned(self) -> str:
        return self.learned

    def get_str_currently(self) -> str:
        return self.currently

    def get_str_lifestyle(self) -> str:
        return self.lifestyle

    def get_str_daily_plan_req(self) -> str:
        return self.daily_plan_req

    def get_str_curr_date_str(self) -> str:
        return self.curr_time.strftime("%A %B %d") if self.curr_time else ""

    def get_curr_event(self):
        """Get current event tuple. Delegates to pure function."""
        return svc.get_current_event(self.state)

    def get_curr_event_and_desc(self):
        """Get current event with description. Delegates to pure function."""
        return svc.get_current_event_and_desc(self.state)

    def get_curr_obj_event_and_desc(self):
        """Get current object event with description. Delegates to pure function."""
        return svc.get_current_obj_event_and_desc(self.state)

    def add_new_action(self,
                       action_address: str,
                       action_duration: int,
                       action_description: str,
                       action_pronunciatio: str,
                       action_event: tuple,
                       chatting_with: Optional[str],
                       chat: Optional[List[List[str]]],
                       chatting_with_buffer: Optional[Dict[str, int]],
                       chatting_end_time: Optional[datetime.datetime],
                       act_obj_description: Optional[str],
                       act_obj_pronunciatio: Optional[str],
                       act_obj_event: tuple,
                       act_start_time: Optional[datetime.datetime] = None):
        """Set a new action."""
        self.act_address = action_address
        self.act_duration = action_duration
        self.act_description = action_description
        self.act_pronunciatio = action_pronunciatio
        self.act_event = action_event

        self.chatting_with = chatting_with
        self.chat = chat
        if chatting_with_buffer:
            self.chatting_with_buffer.update(chatting_with_buffer)
        self.chatting_end_time = chatting_end_time

        self.act_obj_description = act_obj_description
        self.act_obj_pronunciatio = act_obj_pronunciatio
        self.act_obj_event = act_obj_event

        self.act_start_time = act_start_time or self.curr_time
        self.act_path_set = False

    def act_time_str(self) -> str:
        """Get action time as string. Delegates to pure function."""
        return svc.format_action_time(self.state)

    def get_current_action(self) -> Optional[CurrentAction]:
        """Get current action if one is set."""
        if not self.act_address:
            return None
        return self.act

    def act_check_finished(self) -> bool:
        """Check if current action is finished. Delegates to pure function."""
        return svc.is_action_finished(self.state)

    def act_summarize(self) -> dict:
        """Get action summary as dict. Delegates to pure function."""
        return svc.format_action_summary(self.state)

    def act_summary_str(self) -> str:
        """Get action summary as string. Delegates to pure function."""
        return svc.format_action_summary_str(self.state)

    def get_str_daily_schedule_summary(self) -> str:
        """Get daily schedule as string. Delegates to pure function."""
        return svc.format_daily_schedule_summary(self.state)

    def get_str_daily_schedule_hourly_org_summary(self) -> str:
        """Get hourly schedule as string. Delegates to pure function."""
        return svc.format_hourly_schedule_summary(self.state)

    # =========================================================================
    # SERIALIZATION - DEPRECATED (use repository instead)
    # =========================================================================

    def to_dict(self) -> Dict[str, Any]:
        """
        DEPRECATED: Convert state to dict for JSON serialization.
        
        Use JsonMemoryRepository.save_scratch() instead.
        This method remains for backward compatibility.
        """
        import warnings
        warnings.warn(
            "Scratch.to_dict() is deprecated. "
            "Use JsonMemoryRepository.save_scratch() instead.",
            DeprecationWarning,
            stacklevel=2
        )
        
        # Import here to avoid circular dependency
        from .repository.json_repository import JsonMemoryRepository
        
        # Create a temporary repository instance just to use its conversion method
        # This is a bit hacky but ensures consistency
        repo = JsonMemoryRepository.__new__(JsonMemoryRepository)
        return repo._persona_state_to_dict(self.state)
