"""
Author: Joon Sung Park (joonspk@stanford.edu)

File: persona.py
Description: Defines the Persona class that powers the agents in Reverie. 

Note (May 1, 2023) -- this is effectively GenerativeAgent class. Persona was
the term we used internally back in 2022, taking from our Social Simulacra 
paper.

Architecture: This class follows the Strategy pattern with Clean Architecture principles.
- Cognitive modules (perceiver, retriever, planner, etc.) are swappable strategies
- State mutations are centralized in Persona, not spread across modules
- Modules receive immutable context snapshots and return explicit result objects
"""
import sys
import datetime
from typing import List, Dict, Any, Optional, Tuple, Union, TYPE_CHECKING

sys.path.append('../')

from persona.memory_structures.spatial_memory import MemoryTree
from persona.memory_structures.associative_memory import AssociativeMemory
from persona.memory_structures.scratch import Scratch
from persona.memory_structures.repository import JsonMemoryRepository, MemoryRepository, InMemoryRepository
from reverie.backend_server.models import (
    AgentIdentity, AgentContext, WorldContext,
    PerceptionResult, RetrievalResult, PlanResult, ReflectionResult, ExecutionResult,
    Memory, PlanExecution
)

if TYPE_CHECKING:
    from reverie.backend_server.maze import Maze
    from persona.cognitive_modules.perceiver.base import AbstractPerceiver
    from persona.cognitive_modules.retriever.base import AbstractRetriever
    from persona.cognitive_modules.planner.base import AbstractPlanner
    from persona.cognitive_modules.reflector.base import AbstractReflector
    from persona.cognitive_modules.executor.base import AbstractExecutor
    from persona.cognitive_modules.converser.base import AbstractConverser

from persona.cognitive_modules.perceiver import LegacyPerceiver
from persona.cognitive_modules.retriever import LegacyRetriever
from persona.cognitive_modules.planner import LegacyPlanner
from persona.cognitive_modules.reflector import LegacyReflector
from persona.cognitive_modules.executor import LegacyExecutor
from persona.cognitive_modules.converser import LegacyConverser


class Persona: 
  """
  The Persona class represents a generative agent in the simulation.
  
  It orchestrates cognitive modules and manages state. The key architectural principle
  is that cognitive modules are PURE — they receive immutable inputs and return 
  explicit outputs. Only Persona mutates state based on those outputs.
  
  This enables:
  - Easy swapping of cognitive strategies (different planners, retrievers, etc.)
  - Simple unit testing (mock inputs, check outputs)
  - Clear contracts between modules
  - Centralized state management
  """
  
  def __init__(self, 
               name: str, 
               repository: MemoryRepository,
               scratch: Scratch,
               spatial_memory: MemoryTree,
               associative_memory: AssociativeMemory,
               perceiver: "AbstractPerceiver",
               retriever: "AbstractRetriever",
               planner: "AbstractPlanner",
               executor: "AbstractExecutor",
               reflector: "AbstractReflector",
               converser: "AbstractConverser"):
    # PERSONA BASE STATE 
    # <name> is the full name of the persona. This is a unique identifier for
    # the persona within Reverie. 
    self.name: str = name

    # PERSONA MEMORY 
    self.repository: MemoryRepository = repository
    self.s_mem: MemoryTree = spatial_memory
    self.a_mem: AssociativeMemory = associative_memory
    self.scratch: Scratch = scratch

    # COGNITIVE MODULES (Swappable Strategies)
    self.perceiver: "AbstractPerceiver" = perceiver
    self.retriever: "AbstractRetriever" = retriever
    self.planner: "AbstractPlanner" = planner
    self.executor: "AbstractExecutor" = executor
    self.reflector: "AbstractReflector" = reflector
    self.converser: "AbstractConverser" = converser

  # ===========================================================================
  # FACTORY METHODS
  # ===========================================================================

  @classmethod
  def create_from_folder(cls, name: str, folder_mem_saved: str = "False") -> "Persona":
    """
    Create a Persona with default (legacy) cognitive modules from a saved folder.
    
    This is the standard factory method that loads a persona from disk
    with the original paper's implementation of all cognitive modules.
    """
    # Initialize the repository
    repository = JsonMemoryRepository(folder_mem_saved)

    # Load memories using the repository
    s_mem = repository.load_spatial_memory()
    a_mem = repository.load_associative_memory()
    scratch = repository.load_scratch()
    
    # Link memories to scratch state
    scratch.state.memory_system.spatial_memory = s_mem
    scratch.state.memory_system.associative_memory = a_mem

    # COGNITIVE MODULES - Legacy implementations
    perceiver = LegacyPerceiver(scratch)
    retriever = LegacyRetriever(scratch)
    converser = LegacyConverser(scratch, retriever)
    planner = LegacyPlanner(scratch, retriever, converser)
    executor = LegacyExecutor(scratch)
    reflector = LegacyReflector(scratch, retriever)

    persona = cls(name, repository, scratch, s_mem, a_mem,
               perceiver, retriever, planner, executor, reflector, converser)
    
    return persona

  # ===========================================================================
  # CONTEXT BUILDERS - Create immutable snapshots for cognitive modules
  # ===========================================================================

  def build_agent_context(self, 
                          curr_tile: Optional[Tuple[int, int]] = None,
                          curr_time: Optional[datetime.datetime] = None) -> AgentContext:
    """
    Build an immutable snapshot of this agent's current state.
    
    This context is passed to cognitive modules, which cannot modify it.
    All decisions are based on this snapshot.
    """
    tile = curr_tile if curr_tile else self.scratch.curr_tile
    time = curr_time if curr_time else self.scratch.curr_time
    
    return AgentContext(
        identity=AgentIdentity(
            name=self.scratch.name,
            age=self.scratch.age,
            innate_traits=self.scratch.innate,
            learned_traits=self.scratch.learned,
            current_focus=self.scratch.currently,
            lifestyle=self.scratch.lifestyle,
            living_area=self.scratch.living_area
        ),
        vision_radius=self.scratch.vision_r,
        attention_bandwidth=self.scratch.att_bandwidth,
        retention=self.scratch.retention,
        recency_weight=self.scratch.recency_w,
        relevance_weight=self.scratch.relevance_w,
        importance_weight=self.scratch.importance_w,
        recency_decay=self.scratch.recency_decay,
        importance_trigger_max=self.scratch.importance_trigger_max,
        importance_trigger_curr=self.scratch.importance_trigger_curr,
        thought_count=self.scratch.thought_count,
        current_time=time,
        current_tile=tuple(tile) if tile else (0, 0),
        daily_requirements=tuple(self.scratch.daily_req) if self.scratch.daily_req else (),
        daily_schedule=tuple(
            (action.description, action.duration) 
            for action in self.scratch.f_daily_schedule
        ) if self.scratch.f_daily_schedule else (),
        current_action=self.scratch.get_current_action()
    )

  def build_world_context(self, maze: "Maze") -> WorldContext:
    """
    Build an immutable snapshot of what the agent can perceive in the world.
    """
    nearby_tiles = maze.get_nearby_tiles(self.scratch.curr_tile, self.scratch.vision_r)
    current_arena_path = maze.get_tile_path(self.scratch.curr_tile, "arena")
    
    # Get accessible arenas from spatial memory
    accessible_arenas = []
    if self.s_mem.tree:
        for world in self.s_mem.tree.values():
            for sector in world.values():
                accessible_arenas.extend(sector.keys())
    
    return WorldContext(
        nearby_tiles=tuple(tuple(t) for t in nearby_tiles),
        current_arena_path=current_arena_path if current_arena_path else "",
        accessible_arenas=tuple(accessible_arenas)
    )

  def _build_other_agent_contexts(self, 
                                   personas: Dict[str, "Persona"],
                                   curr_time: datetime.datetime) -> Dict[str, AgentContext]:
    """
    Build context snapshots for other agents (for social reasoning).
    
    We pass AgentContext objects instead of full Persona references to prevent
    tight coupling between agents and maintain the pure function approach.
    """
    return {
        name: persona.build_agent_context(curr_time=curr_time)
        for name, persona in personas.items()
        if name != self.name
    }

  # ===========================================================================
  # STATE MUTATION METHODS - Centralized state changes
  # ===========================================================================

  def _apply_perception(self, result: PerceptionResult) -> None:
    """Apply perception results to memory state."""
    # Store new memories
    for memory in result.new_memories:
        # The memory is already added in the perceiver for now (legacy behavior)
        # In a full refactor, we'd add it here
        pass
    
    # Apply spatial memory updates
    for world, sectors in result.spatial_updates.items():
        if world not in self.s_mem.tree:
            self.s_mem.tree[world] = {}
        for sector, arenas in sectors.items():
            if sector not in self.s_mem.tree[world]:
                self.s_mem.tree[world][sector] = {}
            for arena, objects in arenas.items():
                if arena not in self.s_mem.tree[world][sector]:
                    self.s_mem.tree[world][sector][arena] = []
                for obj in objects:
                    if obj not in self.s_mem.tree[world][sector][arena]:
                        self.s_mem.tree[world][sector][arena].append(obj)

  def _apply_plan(self, result: PlanResult) -> None:
    """Apply planning results to action state."""
    self.scratch.act_address = result.action_address
    self.scratch.act_description = result.action_description
    self.scratch.act_duration = result.action_duration
    self.scratch.act_start_time = result.action_start_time
    self.scratch.act_event = result.action_event
    self.scratch.act_pronunciatio = result.action_emoji
    
    # Object interaction
    if result.object_description:
        self.scratch.act_obj_description = result.object_description
    if result.object_emoji:
        self.scratch.act_obj_pronunciatio = result.object_emoji
    if result.object_event:
        self.scratch.act_obj_event = result.object_event
    
    # Schedule updates
    if result.new_daily_schedule:
        from reverie.backend_server.models import Action
        self.scratch.f_daily_schedule = [
            Action(description=desc, duration=dur) 
            for desc, dur in result.new_daily_schedule
        ]
    if result.new_daily_requirements:
        self.scratch.daily_req = result.new_daily_requirements
    
    # Chat state
    if result.chatting_with:
        self.scratch.chatting_with = result.chatting_with
    if result.chat_end_time:
        self.scratch.chatting_end_time = result.chat_end_time

  def _apply_reflection(self, result: ReflectionResult) -> None:
    """Apply reflection results to memory state."""
    # New thoughts are added by the reflector for now (legacy behavior)
    # In a full refactor, we'd add them here
    
    # Update importance counter
    if result.should_reset_counter:
        self.scratch.importance_trigger_curr = self.scratch.importance_trigger_max
        self.scratch.importance_ele_n = 0
    else:
        # Accumulate importance (done elsewhere in legacy)
        pass

  def _apply_execution(self, result: ExecutionResult) -> None:
    """Apply execution results to path state."""
    if result.planned_path:
        self.scratch.planned_path = [tuple(t) for t in result.planned_path]
        self.scratch.act_path_set = True

  # ===========================================================================
  # PUBLIC COGNITIVE INTERFACE - Delegate to modules
  # ===========================================================================

  def perceive(self, maze: "Maze") -> List[Memory]:
    """
    Perceive events around the persona.
    
    NOTE: This is the legacy interface. Internally delegates to the perceiver module.
    The perceiver still uses scratch directly for backward compatibility.
    """
    return self.perceiver.perceive(maze)

  def retrieve(self, perceived: List[Memory]) -> Dict[str, Any]:
    """
    Retrieve relevant memories for perceived events.
    
    NOTE: This is the legacy interface for backward compatibility.
    """
    return self.retriever.retrieve(perceived)

  def plan(self, maze: "Maze", personas: Dict[str, "Persona"], new_day: Any, retrieved: Dict[str, Any]) -> str:
    """
    Plan the next action.
    
    NOTE: This is the legacy interface for backward compatibility.
    """
    return self.planner.plan(maze, personas, new_day, retrieved)

  def execute(self, maze: "Maze", personas: Dict[str, "Persona"], plan: str) -> PlanExecution:
    """
    Execute the planned action.
    
    NOTE: This is the legacy interface for backward compatibility.
    """
    return self.executor.execute(maze, personas, plan)

  def reflect(self) -> None:
    """
    Generate reflections from accumulated experiences.
    
    NOTE: This is the legacy interface for backward compatibility.
    """
    self.reflector.reflect()

  # ===========================================================================
  # MAIN COGNITIVE LOOP
  # ===========================================================================

  def move(self, 
           maze: "Maze", 
           personas: Dict[str, "Persona"], 
           curr_tile: Tuple[int, int], 
           curr_time: datetime.datetime) -> PlanExecution:
    """
    Main cognitive function where the perceive-retrieve-plan-reflect-execute loop runs.
    
    This method orchestrates the cognitive modules and centralizes state mutations.
    Each module receives immutable context and returns explicit results.
    
    Args:
        maze: The Maze class of the current world.
        personas: Dictionary of all persona names to Persona instances.
        curr_tile: Current tile location as (row, col) tuple.
        curr_time: Current simulation time.
        
    Returns:
        PlanExecution containing next_tile, pronunciatio, and description.
    """
    # Update basic state
    self.scratch.curr_tile = curr_tile
    
    # Determine if new day
    new_day: Union[bool, str] = False
    if not self.scratch.curr_time: 
        new_day = "First day"
    elif (self.scratch.curr_time.strftime('%A %B %d') != curr_time.strftime('%A %B %d')):
        new_day = "New day"
    self.scratch.curr_time = curr_time

    # =========================================================================
    # COGNITIVE PIPELINE
    # Currently uses legacy interface for backward compatibility.
    # As modules are updated to use new contracts, this can be refactored to:
    #
    # agent_ctx = self.build_agent_context(curr_tile, curr_time)
    # world_ctx = self.build_world_context(maze)
    # other_agents = self._build_other_agent_contexts(personas, curr_time)
    #
    # perception = self.perceiver.perceive(agent_ctx, world_ctx, maze, ...)
    # self._apply_perception(perception)
    #
    # retrieval = self.retriever.retrieve(perception.new_memories, agent_ctx, ...)
    #
    # plan = self.planner.plan(agent_ctx, world_ctx, maze, retrieval, ...)
    # self._apply_plan(plan)
    #
    # reflection = self.reflector.reflect(agent_ctx, self.a_mem, self.retriever)
    # self._apply_reflection(reflection)
    #
    # execution = self.executor.execute(agent_ctx, plan, maze, other_agents)
    # self._apply_execution(execution)
    # =========================================================================
    
    # Main cognitive sequence (legacy interface)
    perceived = self.perceive(maze)
    retrieved = self.retrieve(perceived)
    plan = self.plan(maze, personas, new_day, retrieved)
    self.reflect()

    return self.execute(maze, personas, plan)

  # ===========================================================================
  # CONVERSATION INTERFACE
  # ===========================================================================

  def open_convo_session(self, convo_mode: str) -> None:
    """Open an interactive conversation session."""
    self.converser.open_session(convo_mode)

  # ===========================================================================
  # PERSISTENCE
  # ===========================================================================

  def save(self, save_folder: str) -> None:
    """
    Save persona's current state (i.e., memory). 

    Args:
        save_folder: The folder where we will be saving our persona's state.
    """
    self.repository.save_spatial_memory(self.s_mem, save_folder)
    self.repository.save_associative_memory(self.a_mem, save_folder)
    self.repository.save_scratch(self.scratch, save_folder)


# =============================================================================
# PERSONA FACTORY - Easy assembly of personas with different configurations
# =============================================================================

class PersonaFactory:
    """
    Factory for creating Persona instances with different cognitive module configurations.
    
    This enables easy experimentation with different strategies for planning,
    retrieval, reflection, etc. without modifying the core Persona class.
    
    Example:
        # Create with default legacy modules
        persona = PersonaFactory.create_legacy("Isabella", "storage/isabella")
        
        # Create with custom planner
        persona = PersonaFactory.create_with_modules(
            name="Isabella",
            folder="storage/isabella",
            planner=MyCustomPlanner(llm_provider)
        )
    """
    
    @staticmethod
    def create_legacy(name: str, folder: str) -> Persona:
        """
        Create a Persona with all legacy (original paper) cognitive modules.
        
        This is equivalent to Persona.create_from_folder() but provided here
        for consistency with the factory pattern.
        
        Args:
            name: The persona's name.
            folder: Path to the saved persona state folder.
            
        Returns:
            A fully configured Persona instance.
        """
        return Persona.create_from_folder(name, folder)
    
    @staticmethod
    def create_with_modules(
        name: str,
        folder: str,
        perceiver: Optional["AbstractPerceiver"] = None,
        retriever: Optional["AbstractRetriever"] = None,
        planner: Optional["AbstractPlanner"] = None,
        executor: Optional["AbstractExecutor"] = None,
        reflector: Optional["AbstractReflector"] = None,
        converser: Optional["AbstractConverser"] = None
    ) -> Persona:
        """
        Create a Persona with custom cognitive modules.
        
        Any module not provided will use the legacy implementation.
        This allows mixing and matching different strategies.
        
        Args:
            name: The persona's name.
            folder: Path to the saved persona state folder.
            perceiver: Custom perceiver (or None for legacy).
            retriever: Custom retriever (or None for legacy).
            planner: Custom planner (or None for legacy).
            executor: Custom executor (or None for legacy).
            reflector: Custom reflector (or None for legacy).
            converser: Custom converser (or None for legacy).
            
        Returns:
            A configured Persona instance with the specified modules.
            
        Example:
            # Use custom planner but legacy everything else
            persona = PersonaFactory.create_with_modules(
                name="Isabella",
                folder="storage/isabella",
                planner=ReActPlanner(llm_provider)
            )
        """
        # Initialize repository and load state
        repository = JsonMemoryRepository(folder)
        s_mem = repository.load_spatial_memory()
        a_mem = repository.load_associative_memory()
        scratch = repository.load_scratch()
        
        # Link memories to scratch state
        scratch.state.memory_system.spatial_memory = s_mem
        scratch.state.memory_system.associative_memory = a_mem
        
        # Create default modules for any not provided
        _perceiver = perceiver if perceiver else LegacyPerceiver(scratch)
        _retriever = retriever if retriever else LegacyRetriever(scratch)
        _converser = converser if converser else LegacyConverser(scratch, _retriever)
        _planner = planner if planner else LegacyPlanner(scratch, _retriever, _converser)
        _executor = executor if executor else LegacyExecutor(scratch)
        _reflector = reflector if reflector else LegacyReflector(scratch, _retriever)
        
        return Persona(
            name=name,
            repository=repository,
            scratch=scratch,
            spatial_memory=s_mem,
            associative_memory=a_mem,
            perceiver=_perceiver,
            retriever=_retriever,
            planner=_planner,
            executor=_executor,
            reflector=_reflector,
            converser=_converser
        )
    
    @staticmethod
    def create_for_testing(
        name: str,
        scratch: Optional[Scratch] = None,
        s_mem: Optional[MemoryTree] = None,
        a_mem: Optional[AssociativeMemory] = None
    ) -> Persona:
        """
        Create a minimal Persona for unit testing.
        
        Creates a persona with mock or minimal dependencies, useful for
        testing cognitive modules in isolation.
        
        Args:
            name: The persona's name.
            scratch: Optional pre-configured scratch (creates minimal if None).
            s_mem: Optional spatial memory (creates empty if None).
            a_mem: Optional associative memory (creates empty if None).
            
        Returns:
            A Persona suitable for testing.
        """
        # Create minimal dependencies if not provided
        _scratch = scratch if scratch else Scratch(None)
        _s_mem = s_mem if s_mem else MemoryTree({})
        _a_mem = a_mem if a_mem else AssociativeMemory(None)
        
        # Link memories
        _scratch.state.memory_system.spatial_memory = _s_mem
        _scratch.state.memory_system.associative_memory = _a_mem
        
        # Create legacy modules (can be mocked in tests)
        perceiver = LegacyPerceiver(_scratch)
        retriever = LegacyRetriever(_scratch)
        converser = LegacyConverser(_scratch, retriever)
        planner = LegacyPlanner(_scratch, retriever, converser)
        executor = LegacyExecutor(_scratch)
        reflector = LegacyReflector(_scratch, retriever)
        
        # Use in-memory repository for testing
        repository = InMemoryRepository()
        
        return Persona(
            name=name,
            repository=repository,
            scratch=_scratch,
            spatial_memory=_s_mem,
            associative_memory=_a_mem,
            perceiver=perceiver,
            retriever=retriever,
            planner=planner,
            executor=executor,
            reflector=reflector,
            converser=converser
        )

    




































