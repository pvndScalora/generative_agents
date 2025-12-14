"""
Author: Joon Sung Park (joonspk@stanford.edu)

File: persona.py
Description: Defines the Persona class that powers the agents in Reverie. 

Note (May 1, 2023) -- this is effectively GenerativeAgent class. Persona was
the term we used internally back in 2022, taking from our Social Simulacra 
paper.
"""
import math
import sys
import datetime
import random
from typing import List, Dict, Any, Optional, Set, Tuple, TYPE_CHECKING

sys.path.append('../')

from persona.memory_structures.spatial_memory import MemoryTree
from persona.memory_structures.associative_memory import AssociativeMemory
from persona.memory_structures.scratch import Scratch
from persona.memory_structures.repository import JsonMemoryRepository, MemoryRepository

if TYPE_CHECKING:
    from reverie.backend_server.maze import Maze
    from reverie.backend_server.models import Memory, PlanExecution
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

    # COGNITIVE MODULES
    self.perceiver: "AbstractPerceiver" = perceiver
    self.retriever: "AbstractRetriever" = retriever
    self.planner: "AbstractPlanner" = planner
    self.executor: "AbstractExecutor" = executor
    self.reflector: "AbstractReflector" = reflector
    self.converser: "AbstractConverser" = converser

  @classmethod
  def create_from_folder(cls, name: str, folder_mem_saved: str = "False") -> "Persona":
    # Initialize the repository
    repository = JsonMemoryRepository(folder_mem_saved)

    # Load memories using the repository
    s_mem = repository.load_spatial_memory()
    a_mem = repository.load_associative_memory()
    scratch = repository.load_scratch()
    
    # Link memories to scratch state
    scratch.state.memory_system.spatial_memory = s_mem
    scratch.state.memory_system.associative_memory = a_mem

    # COGNITIVE MODULES
    perceiver = LegacyPerceiver(scratch)
    retriever = LegacyRetriever(scratch)
    converser = LegacyConverser(scratch, retriever)
    planner = LegacyPlanner(scratch, retriever, converser)
    executor = LegacyExecutor(scratch)
    reflector = LegacyReflector(scratch, retriever)

    persona = cls(name, repository, scratch, s_mem, a_mem,
               perceiver, retriever, planner, executor, reflector, converser)
    
    return persona


  def save(self, save_folder: str): 
    """
    Save persona's current state (i.e., memory). 

    INPUT: 
      save_folder: The folder where we wil be saving our persona's state. 
    OUTPUT: 
      None
    """
    # Use the repository to save memories
    self.repository.save_spatial_memory(self.s_mem, save_folder)
    self.repository.save_associative_memory(self.a_mem, save_folder)
    self.repository.save_scratch(self.scratch, save_folder)


  def perceive(self, maze: "Maze") -> List["Memory"]:
    """
    This function takes the current maze, and returns events that are 
    happening around the persona. Importantly, perceive is guided by 
    two key hyper-parameter for the  persona: 1) att_bandwidth, and 
    2) retention. 

    First, <att_bandwidth> determines the number of nearby events that the 
    persona can perceive. Say there are 10 events that are within the vision
    radius for the persona -- perceiving all 10 might be too much. So, the 
    persona perceives the closest att_bandwidth number of events in case there
    are too many events. 

    Second, the persona does not want to perceive and think about the same 
    event at each time step. That's where <retention> comes in -- there is 
    temporal order to what the persona remembers. So if the persona's memory
    contains the current surrounding events that happened within the most 
    recent retention, there is no need to perceive that again. xx

    INPUT: 
      maze: Current <Maze> instance of the world. 
    OUTPUT: 
      a list of <ConceptNode> that are perceived and new. 
        See associative_memory.py -- but to get you a sense of what it 
        receives as its input: "s, p, o, desc, persona.scratch.curr_time"
    """
    return self.perceiver.perceive(maze)


  def retrieve(self, perceived: List["Memory"]):
    """
    This function takes the events that are perceived by the persona as input
    and returns a set of related events and thoughts that the persona would 
    need to consider as context when planning. 

    INPUT: 
      perceive: a list of <ConceptNode> that are perceived and new.  
    OUTPUT: 
      retrieved: dictionary of dictionary. The first layer specifies an event,
                 while the latter layer specifies the "curr_event", "events", 
                 and "thoughts" that are relevant.
    """
    return self.retriever.retrieve(perceived)


  def plan(self, maze: "Maze", personas: Dict[str, "Persona"], new_day: Any, retrieved: Dict[str, Any]):
    """
    Main cognitive function of the chain. It takes the retrieved memory and 
    perception, as well as the maze and the first day state to conduct both 
    the long term and short term planning for the persona. 

    INPUT: 
      maze: Current <Maze> instance of the world. 
      personas: A dictionary that contains all persona names as keys, and the 
                Persona instance as values. 
      new_day: This can take one of the three values. 
        1) <Boolean> False -- It is not a "new day" cycle (if it is, we would
           need to call the long term planning sequence for the persona). 
        2) <String> "First day" -- It is literally the start of a simulation,
           so not only is it a new day, but also it is the first day. 
        2) <String> "New day" -- It is a new day. 
      retrieved: dictionary of dictionary. The first layer specifies an event,
                 while the latter layer specifies the "curr_event", "events", 
                 and "thoughts" that are relevant.
    OUTPUT 
      The target action address of the persona (persona.scratch.act_address).
    """
    return self.planner.plan(maze, personas, new_day, retrieved)


  def execute(self, maze: "Maze", personas: Dict[str, "Persona"], plan: str) -> "PlanExecution":
    """
    This function takes the agent's current plan and outputs a concrete 
    execution (what object to use, and what tile to travel to). 

    INPUT: 
      maze: Current <Maze> instance of the world. 
      personas: A dictionary that contains all persona names as keys, and the 
                Persona instance as values. 
      plan: The target action address of the persona  
            (persona.scratch.act_address).
    OUTPUT: 
      execution: A triple set that contains the following components: 
        <next_tile> is a x,y coordinate. e.g., (58, 9)
        <pronunciatio> is an emoji.
        <description> is a string description of the movement. e.g., 
        writing her next novel (editing her novel) 
        @ double studio:double studio:common room:sofa
    """
    return self.executor.execute(maze, personas, plan)


  def reflect(self):
    """
    Reviews the persona's memory and create new thoughts based on it. 

    INPUT: 
      None
    OUTPUT: 
      None
    """
    self.reflector.reflect()


  def move(self, maze: "Maze", personas: Dict[str, "Persona"], curr_tile: Tuple[int, int], curr_time: datetime.datetime) -> "PlanExecution":
    """
    This is the main cognitive function where our main sequence is called. 

    INPUT: 
      maze: The Maze class of the current world. 
      personas: A dictionary that contains all persona names as keys, and the 
                Persona instance as values. 
      curr_tile: A tuple that designates the persona's current tile location 
                 in (row, col) form. e.g., (58, 39)
      curr_time: datetime instance that indicates the game's current time. 
    OUTPUT: 
      execution: A triple set that contains the following components: 
        <next_tile> is a x,y coordinate. e.g., (58, 9)
        <pronunciatio> is an emoji.
        <description> is a string description of the movement. e.g., 
        writing her next novel (editing her novel) 
        @ double studio:double studio:common room:sofa
    """
    # Updating persona's scratch memory with <curr_tile>. 
    self.scratch.curr_tile = curr_tile

    # We figure out whether the persona started a new day, and if it is a new
    # day, whether it is the very first day of the simulation. This is 
    # important because we set up the persona's long term plan at the start of
    # a new day. 
    new_day = False
    if not self.scratch.curr_time: 
      new_day = "First day"
    elif (self.scratch.curr_time.strftime('%A %B %d')
          != curr_time.strftime('%A %B %d')):
      new_day = "New day"
    self.scratch.curr_time = curr_time

    # Main cognitive sequence begins here. 
    perceived = self.perceive(maze)
    retrieved = self.retrieve(perceived)
    plan = self.plan(maze, personas, new_day, retrieved)
    self.reflect()

    # <execution> is a triple set that contains the following components: 
    # <next_tile> is a x,y coordinate. e.g., (58, 9)
    # <pronunciatio> is an emoji. e.g., "\ud83d\udca4"
    # <description> is a string description of the movement. e.g., 
    #   writing her next novel (editing her novel) 
    #   @ double studio:double studio:common room:sofa
    return self.execute(maze, personas, plan)


  def open_convo_session(self, convo_mode: str): 
    self.converser.open_session(convo_mode)
    




































