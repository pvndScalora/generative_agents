"""
JSON-based persistence adapter for persona memory.

This adapter implements MemoryRepository using JSON files for storage.
ALL JSON key mapping logic is contained HERE - the domain objects (Scratch,
PersonaState, etc.) are kept pure and unaware of serialization format.

This follows the Hexagonal Architecture principle: adapters know about
external formats, domain objects don't.
"""
import json
import os
import datetime
from typing import Dict, Any, Optional

from persona.memory_structures.spatial_memory import MemoryTree
from persona.memory_structures.associative_memory import AssociativeMemory
from persona.memory_structures.scratch import Scratch
from persona.memory_structures.state import (
    PersonaState, IdentityProfile, WorldContext, ExecutiveState,
    ActionState, SocialContext, MemorySystem
)
from models import (
    PersonaIdentity, CognitiveParams, CurrentAction, Coordinate, Action
)
from global_methods import check_if_file_exists
from .base import MemoryRepository


class JsonMemoryRepository(MemoryRepository):
    """
    JSON file-based implementation of MemoryRepository.
    
    This adapter handles all JSON <-> domain object conversion.
    The domain objects remain pure - they don't know about JSON keys.
    """
    
    def __init__(self, folder_mem_saved: str):
        self.folder_mem_saved = folder_mem_saved
        self.spatial_json_path = f"{folder_mem_saved}/bootstrap_memory/spatial_memory.json"
        self.associative_folder_path = f"{folder_mem_saved}/bootstrap_memory/associative_memory"
        self.scratch_json_path = f"{folder_mem_saved}/bootstrap_memory/scratch.json"
    
    # =========================================================================
    # SPATIAL MEMORY
    # =========================================================================
    
    def load_spatial_memory(self) -> MemoryTree:
        tree = {}
        if check_if_file_exists(self.spatial_json_path):
            with open(self.spatial_json_path) as f:
                tree = json.load(f)
        return MemoryTree(tree)

    def save_spatial_memory(self, memory: MemoryTree, save_folder: str):
        out_json = f"{save_folder}/spatial_memory.json"
        with open(out_json, "w") as outfile:
            json.dump(memory.tree, outfile)

    # =========================================================================
    # ASSOCIATIVE MEMORY
    # =========================================================================

    def load_associative_memory(self) -> AssociativeMemory:
        nodes = {}
        embeddings = {}
        kw_strength = {"kw_strength_event": {}, "kw_strength_thought": {}}
        
        nodes_path = f"{self.associative_folder_path}/nodes.json"
        embeddings_path = f"{self.associative_folder_path}/embeddings.json"
        kw_strength_path = f"{self.associative_folder_path}/kw_strength.json"

        if check_if_file_exists(nodes_path):
            with open(nodes_path) as f:
                nodes = json.load(f)
        
        if check_if_file_exists(embeddings_path):
            with open(embeddings_path) as f:
                embeddings = json.load(f)

        if check_if_file_exists(kw_strength_path):
            with open(kw_strength_path) as f:
                kw_strength = json.load(f)
                
        return AssociativeMemory(nodes, embeddings, kw_strength)

    def save_associative_memory(self, memory: AssociativeMemory, save_folder: str):
        out_folder = f"{save_folder}/associative_memory"
        os.makedirs(out_folder, exist_ok=True)
        
        state = memory.get_state()
        
        with open(f"{out_folder}/nodes.json", "w") as outfile:
            json.dump(state["nodes"], outfile)
            
        with open(f"{out_folder}/kw_strength.json", "w") as outfile:
            json.dump(state["kw_strength"], outfile)
            
        with open(f"{out_folder}/embeddings.json", "w") as outfile:
            json.dump(state["embeddings"], outfile)

    # =========================================================================
    # SCRATCH (PersonaState)
    # =========================================================================

    def load_scratch(self) -> Scratch:
        """
        Load scratch from JSON file.
        
        ALL JSON key mapping is done here in the adapter.
        """
        if not check_if_file_exists(self.scratch_json_path):
            return Scratch(None)
        
        with open(self.scratch_json_path) as f:
            data = json.load(f)
        
        # Convert JSON dict to PersonaState (domain object)
        state = self._dict_to_persona_state(data)
        return Scratch(state)

    def save_scratch(self, scratch: Scratch, save_folder: str):
        """
        Save scratch to JSON file.
        
        ALL JSON key mapping is done here in the adapter.
        """
        out_json = f"{save_folder}/scratch.json"
        
        # Convert PersonaState (domain object) to JSON dict
        scratch_dict = self._persona_state_to_dict(scratch.state)
        
        with open(out_json, "w") as outfile:
            json.dump(scratch_dict, outfile, indent=2)

    # =========================================================================
    # JSON <-> DOMAIN OBJECT MAPPING (All serialization logic contained here)
    # =========================================================================

    def _dict_to_persona_state(self, d: Dict[str, Any]) -> PersonaState:
        """
        Convert JSON dictionary to PersonaState domain object.
        
        This is the ONLY place that knows the JSON key names.
        """
        # Parse identity
        identity = PersonaIdentity(
            name=d.get("name", ""),
            age=d.get("age", 0),
            innate=d.get("innate", ""),
            learned=d.get("learned", ""),
            currently=d.get("currently", ""),
            lifestyle=d.get("lifestyle", ""),
            living_area=d.get("living_area", "")
        )
        
        # Parse cognitive parameters
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
        
        world_context = WorldContext(
            curr_time=curr_time,
            curr_tile=curr_tile
        )
        
        # Parse executive state
        f_daily_schedule = [
            Action(description=x[0], duration=x[1]) 
            for x in d.get("f_daily_schedule", [])
        ]
        f_daily_schedule_hourly_org = [
            Action(description=x[0], duration=x[1]) 
            for x in d.get("f_daily_schedule_hourly_org", [])
        ]
        
        executive_state = ExecutiveState(
            daily_plan_req=d.get("daily_plan_req", ""),
            daily_req=d.get("daily_req", []),
            f_daily_schedule=f_daily_schedule,
            f_daily_schedule_hourly_org=f_daily_schedule_hourly_org
        )
        
        # Parse action state
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
        
        action_state = ActionState(
            current_action=current_action,
            act_path_set=d.get("act_path_set", False),
            planned_path=planned_path
        )
        
        # Parse social context
        chatting_end_time = None
        if d.get("chatting_end_time"):
            chatting_end_time = datetime.datetime.strptime(d["chatting_end_time"], "%B %d, %Y, %H:%M:%S")
        
        social_context = SocialContext(
            chatting_with=d.get("chatting_with"),
            chat=d.get("chat"),
            chatting_with_buffer=d.get("chatting_with_buffer", {}),
            chatting_end_time=chatting_end_time
        )
        
        # Compose the full state
        return PersonaState(
            identity_profile=IdentityProfile(identity, cognitive_params),
            world_context=world_context,
            executive_state=executive_state,
            action_state=action_state,
            social_context=social_context
        )

    def _persona_state_to_dict(self, state: PersonaState) -> Dict[str, Any]:
        """
        Convert PersonaState domain object to JSON dictionary.
        
        This is the ONLY place that knows the JSON key names.
        """
        identity = state.identity_profile.identity
        params = state.identity_profile.cognitive_params
        world = state.world_context
        executive = state.executive_state
        action = state.action_state.current_action
        social = state.social_context
        
        # Format datetimes
        curr_time_str = world.curr_time.strftime("%B %d, %Y, %H:%M:%S") if world.curr_time else None
        act_start_time_str = action.start_time.strftime("%B %d, %Y, %H:%M:%S") if action.start_time else None
        chatting_end_time_str = social.chatting_end_time.strftime("%B %d, %Y, %H:%M:%S") if social.chatting_end_time else None
        
        return {
            # Identity
            "name": identity.name,
            "first_name": identity.name.split(" ")[0] if identity.name else "",
            "last_name": identity.name.split(" ")[-1] if identity.name else "",
            "age": identity.age,
            "innate": identity.innate,
            "learned": identity.learned,
            "currently": identity.currently,
            "lifestyle": identity.lifestyle,
            "living_area": identity.living_area,
            
            # Cognitive parameters
            "vision_r": params.vision_r,
            "att_bandwidth": params.att_bandwidth,
            "retention": params.retention,
            "concept_forget": params.concept_forget,
            "daily_reflection_time": params.daily_reflection_time,
            "daily_reflection_size": params.daily_reflection_size,
            "overlap_reflect_th": params.overlap_reflect_th,
            "kw_strg_event_reflect_th": params.kw_strg_event_reflect_th,
            "kw_strg_thought_reflect_th": params.kw_strg_thought_reflect_th,
            "recency_w": params.recency_weight,
            "relevance_w": params.relevance_weight,
            "importance_w": params.importance_weight,
            "recency_decay": params.recency_decay,
            "importance_trigger_max": params.importance_trigger_max,
            "importance_trigger_curr": params.importance_trigger_curr,
            "importance_ele_n": params.importance_ele_n,
            "thought_count": params.thought_count,
            
            # World context
            "curr_time": curr_time_str,
            "curr_tile": world.curr_tile.as_tuple() if world.curr_tile else None,
            "daily_plan_req": executive.daily_plan_req,
            
            # Executive state
            "daily_req": executive.daily_req,
            "f_daily_schedule": [[a.description, a.duration] for a in executive.f_daily_schedule],
            "f_daily_schedule_hourly_org": [[a.description, a.duration] for a in executive.f_daily_schedule_hourly_org],
            
            # Action state
            "act_address": action.address,
            "act_start_time": act_start_time_str,
            "act_duration": action.duration,
            "act_description": action.description,
            "act_pronunciatio": action.pronunciatio,
            "act_event": list(action.event) if action.event else ["", None, None],
            "act_obj_description": action.obj_description,
            "act_obj_pronunciatio": action.obj_pronunciatio,
            "act_obj_event": list(action.obj_event) if action.obj_event else ["", None, None],
            "act_path_set": state.action_state.act_path_set,
            "planned_path": [p.as_tuple() for p in state.action_state.planned_path],
            
            # Social context
            "chatting_with": social.chatting_with,
            "chat": social.chat,
            "chatting_with_buffer": social.chatting_with_buffer,
            "chatting_end_time": chatting_end_time_str,
        }
