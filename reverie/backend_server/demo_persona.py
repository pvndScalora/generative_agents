"""
Demo script showcasing the Persona architecture.

This demonstrates:
1. Loading personas with PersonaFactory
2. Building immutable context snapshots
3. Using the cognitive pipeline
4. Swapping cognitive modules for experimentation
5. Using experimental strategies (memory scoring, reflection triggers)
"""
import os
import sys
import datetime

# Get the directory of the current script
current_dir = os.path.dirname(os.path.abspath(__file__))
# Get the project root (two levels up from backend_server)
project_root = os.path.dirname(os.path.dirname(current_dir))

# Add the project root to sys.path
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from reverie.backend_server.persona.persona import Persona, PersonaFactory
from reverie.backend_server.maze import Maze
from reverie.backend_server.models import AgentContext, AgentIdentity


def demo_basic_loading():
    """
    Basic demo: Load a persona and inspect its state.
    """
    print("\n" + "="*60)
    print("DEMO 1: Basic Persona Loading")
    print("="*60)
    
    storage_base = os.path.join(project_root, "environment", "frontend_server", "storage")
    simulation_folder = "base_the_ville_isabella_maria_klaus"
    persona_name = "Isabella Rodriguez"
    persona_folder = os.path.join(storage_base, simulation_folder, "personas", persona_name)
    
    print(f"Loading persona from: {persona_folder}")
    
    if not os.path.exists(persona_folder):
        print(f"Error: Folder {persona_folder} does not exist.")
        return None, None

    # Method 1: Direct factory method (recommended)
    persona = PersonaFactory.create_legacy(persona_name, persona_folder)
    print(f"✓ Successfully loaded persona: {persona.name}")
    
    # Inspect identity
    print(f"\n--- Identity ---")
    print(f"  Name: {persona.scratch.name}")
    print(f"  Age: {persona.scratch.age}")
    print(f"  Innate traits: {persona.scratch.innate[:80]}...")
    print(f"  Currently: {persona.scratch.currently}")
    
    # Inspect cognitive parameters
    print(f"\n--- Cognitive Parameters ---")
    print(f"  Vision radius: {persona.scratch.vision_r}")
    print(f"  Attention bandwidth: {persona.scratch.att_bandwidth}")
    print(f"  Retention: {persona.scratch.retention}")
    print(f"  Recency weight: {persona.scratch.recency_w}")
    print(f"  Relevance weight: {persona.scratch.relevance_w}")
    print(f"  Importance weight: {persona.scratch.importance_w}")
    
    # Load maze
    maze_name = "the_ville"
    maze = Maze(maze_name)
    print(f"\n✓ Successfully loaded maze: {maze.maze_name}")
    
    return persona, maze


def demo_context_building(persona: Persona, maze: Maze):
    """
    Demo: Building immutable context snapshots.
    
    The new architecture uses immutable context objects passed to cognitive modules.
    This enables pure function-like modules that are easy to test and swap.
    """
    print("\n" + "="*60)
    print("DEMO 2: Building Immutable Context Snapshots")
    print("="*60)
    
    # Ensure persona has a valid location
    if not persona.scratch.curr_tile:
        persona.scratch.curr_tile = (73, 14)  # Isabella's usual spot
    
    # Set a current time if not set
    if not persona.scratch.curr_time:
        persona.scratch.curr_time = datetime.datetime(2023, 2, 13, 8, 0, 0)
    
    # Build an AgentContext - an immutable snapshot of the agent's state
    agent_context = persona.build_agent_context()
    
    print("\n--- AgentContext (Immutable Snapshot) ---")
    print(f"  Identity:")
    print(f"    Name: {agent_context.identity.name}")
    print(f"    Age: {agent_context.identity.age}")
    print(f"    Current focus: {agent_context.identity.current_focus[:60]}..." if agent_context.identity.current_focus else "    Current focus: None")
    
    print(f"\n  Cognitive Params:")
    print(f"    Vision radius: {agent_context.vision_radius}")
    print(f"    Attention bandwidth: {agent_context.attention_bandwidth}")
    
    print(f"\n  Current State:")
    print(f"    Time: {agent_context.current_time}")
    print(f"    Tile: {agent_context.current_tile}")
    print(f"    Daily requirements: {len(agent_context.daily_requirements)} items")
    print(f"    Daily schedule: {len(agent_context.daily_schedule)} actions")
    
    # Build a WorldContext - what the agent can perceive
    world_context = persona.build_world_context(maze)
    
    print("\n--- WorldContext (What Agent Can See) ---")
    print(f"  Nearby tiles: {len(world_context.nearby_tiles)} tiles")
    print(f"  Current arena: {world_context.current_arena_path}")
    print(f"  Known arenas: {len(world_context.accessible_arenas)} arenas")
    
    # These contexts are IMMUTABLE - cognitive modules cannot modify them
    print("\n✓ Contexts are frozen (immutable) - modules receive read-only views")
    
    return agent_context, world_context


def demo_cognitive_pipeline(persona: Persona, maze: Maze):
    """
    Demo: Running the cognitive pipeline.
    
    The pipeline is: Perceive → Retrieve → Plan → Reflect → Execute
    """
    print("\n" + "="*60)
    print("DEMO 3: Cognitive Pipeline")
    print("="*60)
    
    # Ensure persona has valid state
    if not persona.scratch.curr_tile:
        persona.scratch.curr_tile = (73, 14)
    if not persona.scratch.curr_time:
        persona.scratch.curr_time = datetime.datetime(2023, 2, 13, 8, 0, 0)
    
    print("\nPipeline: Perceive → Retrieve → Plan → Reflect → Execute\n")
    
    # Note: Full pipeline requires LLM API calls
    # We'll demonstrate the architecture without making actual calls
    
    print("1. PERCEIVE - What events are happening nearby?")
    print("   perceiver.perceive(agent_context, world_context, maze, ...)")
    print("   → Returns: PerceptionResult(new_memories, spatial_updates, ignored)")
    print(f"   Current implementation: {type(persona.perceiver).__name__}")
    
    print("\n2. RETRIEVE - What memories are relevant to these events?")
    print("   retriever.retrieve(queries, agent_context, memory_store)")
    print("   → Returns: Dict[str, RetrievalResult]")
    print(f"   Current implementation: {type(persona.retriever).__name__}")
    print(f"   Memories available: {len(persona.a_mem.seq_event)} events, {len(persona.a_mem.seq_thought)} thoughts")
    
    print("\n3. PLAN - What should the agent do next?")
    print("   planner.plan(agent, world, maze, retrieved, other_agents, is_new_day)")
    print("   → Returns: PlanResult(action_address, action_description, ...)")
    print(f"   Current implementation: {type(persona.planner).__name__}")
    print(f"   Current action: {persona.scratch.act_description or 'None'}")
    
    print("\n4. REFLECT - Should the agent generate new insights?")
    print("   reflector.reflect(agent, memory_store, retriever)")
    print("   → Returns: ReflectionResult(new_thoughts, focal_points, ...)")
    print(f"   Current implementation: {type(persona.reflector).__name__}")
    print(f"   Importance counter: {persona.scratch.importance_trigger_curr}/{persona.scratch.importance_trigger_max}")
    
    print("\n5. EXECUTE - Convert plan to concrete movement")
    print("   executor.execute(agent, plan, maze, other_agents)")
    print("   → Returns: ExecutionResult(next_tile, pronunciatio, description)")
    print(f"   Current implementation: {type(persona.executor).__name__}")
    print(f"   Current tile: {persona.scratch.curr_tile}")
    
    print("\n" + "-"*60)
    print("The full move() method orchestrates this entire pipeline:")
    print("  execution = persona.move(maze, personas, curr_tile, curr_time)")
    print("-"*60)


def demo_module_swapping():
    """
    Demo: How to swap cognitive modules for experimentation.
    
    This is the key benefit of the new architecture - you can easily
    swap out any cognitive module to test different strategies.
    """
    print("\n" + "="*60)
    print("DEMO 4: Swapping Cognitive Modules")
    print("="*60)
    
    print("""
The new architecture allows easy experimentation by swapping modules:

    # Example: Create a persona with a custom planner
    from my_experiments import ReActPlanner, SemanticRetriever
    
    persona = PersonaFactory.create_with_modules(
        name="Isabella Rodriguez",
        folder="storage/isabella",
        planner=ReActPlanner(llm_provider),      # Custom!
        retriever=SemanticRetriever(llm_provider) # Custom!
        # Other modules use legacy implementations
    )

Available module slots:
    - perceiver:  How does the agent notice events?
    - retriever:  How does the agent search memory?
    - planner:    How does the agent decide what to do?
    - executor:   How does the agent pathfind/move?
    - reflector:  How does the agent generate insights?
    - converser:  How does the agent have conversations?

Each module has an abstract base class defining the contract:
    - AbstractPerceiver.perceive(agent, world, maze, ...) → PerceptionResult
    - AbstractRetriever.retrieve(queries, agent, memory) → Dict[str, RetrievalResult]
    - AbstractPlanner.plan(agent, world, maze, ...) → PlanResult
    - AbstractReflector.reflect(agent, memory, retriever) → ReflectionResult
    - AbstractExecutor.execute(agent, plan, maze, ...) → ExecutionResult
    - AbstractConverser.generate_utterance(...) → ConversationResult
""")


def demo_testing_persona():
    """
    Demo: Creating a minimal persona for testing.
    """
    print("\n" + "="*60)
    print("DEMO 5: Creating Test Personas")
    print("="*60)
    
    print("""
For unit testing, you can create minimal personas without disk I/O:

    # Create a test persona with in-memory storage
    persona = PersonaFactory.create_for_testing("TestAgent")
    
    # The persona has all modules but uses InMemoryRepository
    # Perfect for unit tests where you mock the cognitive modules
""")
    
    # Actually create one to show it works
    try:
        test_persona = PersonaFactory.create_for_testing("TestAgent")
        print(f"✓ Created test persona: {test_persona.name}")
        print(f"  Repository type: {type(test_persona.repository).__name__}")
        print(f"  Perceiver type: {type(test_persona.perceiver).__name__}")
        print(f"  Planner type: {type(test_persona.planner).__name__}")
    except Exception as e:
        print(f"  (Test persona creation requires all imports to be available)")
        print(f"  Error: {e}")


def demo_experimental_strategies():
    """
    Demo: Using pluggable strategies for experimental flexibility.
    
    The architecture now supports fine-grained experimentation with:
    - Memory Scoring Strategies: How memories are ranked for retrieval
    - Reflection Triggers: When agents generate reflections
    """
    print("\n" + "="*60)
    print("DEMO 6: Experimental Strategies")
    print("="*60)
    
    print("""
The architecture supports pluggable strategies for fine-grained experimentation:

╔══════════════════════════════════════════════════════════════════════════╗
║  MEMORY SCORING STRATEGIES                                               ║
║  Control how memories are ranked during retrieval                        ║
╠══════════════════════════════════════════════════════════════════════════╣
║  LinearWeightedScoring (default)                                         ║
║    Original paper: score = recency_w * R + relevance_w * V + importance_w * I ║
║                                                                          ║
║  AttentionBasedScoring                                                   ║
║    Uses softmax to dynamically weight factors based on distribution      ║
║                                                                          ║
║  RecencyOnlyScoring                                                      ║
║    Pure recency ranking - for ablation studies                           ║
║                                                                          ║
║  RelevanceOnlyScoring                                                    ║
║    Pure semantic similarity - for ablation studies                       ║
║                                                                          ║
║  HybridRelevanceRecencyScoring                                           ║
║    Multiplicative: score = recency * relevance                           ║
╚══════════════════════════════════════════════════════════════════════════╝

╔══════════════════════════════════════════════════════════════════════════╗
║  REFLECTION TRIGGERS                                                      ║
║  Control when agents generate reflections                                 ║
╠══════════════════════════════════════════════════════════════════════════╣
║  ImportanceThresholdTrigger (default)                                    ║
║    Original paper: trigger when accumulated importance exceeds threshold ║
║                                                                          ║
║  EventCountTrigger                                                       ║
║    Trigger after N events or thoughts                                    ║
║                                                                          ║
║  TimedTrigger                                                            ║
║    Trigger every N simulated minutes                                     ║
║                                                                          ║
║  CompositeTrigger                                                        ║
║    Combine multiple triggers with AND/OR logic                           ║
║                                                                          ║
║  NeverTrigger / AlwaysTrigger                                            ║
║    For ablation studies and debugging                                    ║
╚══════════════════════════════════════════════════════════════════════════╝
""")
    
    print("EXAMPLE: Experimenting with different scoring strategies")
    print("-"*60)
    print("""
    from persona.strategies import (
        AttentionBasedScoring,
        TimedTrigger,
        CompositeTrigger,
        ImportanceThresholdTrigger
    )
    from persona.cognitive_modules.retriever.legacy import LegacyRetriever
    from persona.cognitive_modules.reflector.legacy import LegacyReflector
    
    # Create retriever with attention-based scoring
    retriever = LegacyRetriever(
        scratch=scratch,
        scoring_strategy=AttentionBasedScoring(temperature=0.5)
    )
    
    # Create reflector with composite trigger (importance OR time-based)
    reflector = LegacyReflector(
        scratch=scratch,
        retriever=retriever,
        trigger_strategy=CompositeTrigger(
            triggers=[
                ImportanceThresholdTrigger(),
                TimedTrigger(interval_minutes=60)
            ],
            require_all=False  # OR logic
        )
    )
    
    # Use in PersonaFactory
    persona = PersonaFactory.create_with_modules(
        name="Isabella Rodriguez",
        folder="storage/isabella",
        retriever=retriever,
        reflector=reflector
    )
""")
    
    # Show the actual strategy interfaces
    try:
        from reverie.backend_server.persona.cognitive_modules.retriever.scoring import (
            LinearWeightedScoring,
            AttentionBasedScoring,
            ScoringContext,
        )
        from reverie.backend_server.persona.cognitive_modules.reflector.triggers import (
            ImportanceThresholdTrigger,
            TimedTrigger,
            ReflectionContext,
        )
        
        print("\n✓ Strategies loaded from cognitive_modules")
        
        # Demonstrate ScoringContext
        scoring_ctx = ScoringContext(
            recency_weight=1.0,
            relevance_weight=1.0,
            importance_weight=1.0,
            recency_decay=0.99,
            current_time_index=100,
        )
        print(f"\n  ScoringContext example: {scoring_ctx}")
        
        # Demonstrate ReflectionContext
        reflection_ctx = ReflectionContext(
            importance_trigger_max=150,
            importance_trigger_curr=50,
            importance_accumulated=100,
            current_time=datetime.datetime.now(),
            has_memories=True,
        )
        
        # Test a trigger
        trigger = ImportanceThresholdTrigger()
        result = trigger.check(reflection_ctx)
        print(f"\n  ImportanceThresholdTrigger check: {result.should_reflect}")
        print(f"    Reason: {result.reason}")
        
    except Exception as e:
        print(f"\n  (Strategy imports require all dependencies)")
        print(f"  Error: {e}")


def main():
    """Run all demos."""
    print("\n" + "#"*60)
    print("#" + " "*20 + "PERSONA ARCHITECTURE DEMO" + " "*13 + "#")
    print("#"*60)
    
    # Demo 1: Basic loading
    result = demo_basic_loading()
    if result[0] is None:
        return
    persona, maze = result
    
    # Demo 2: Context building
    demo_context_building(persona, maze)
    
    # Demo 3: Cognitive pipeline
    demo_cognitive_pipeline(persona, maze)
    
    # Demo 4: Module swapping (documentation)
    demo_module_swapping()
    
    # Demo 5: Test personas
    demo_testing_persona()
    
    # Demo 6: Experimental strategies (NEW!)
    demo_experimental_strategies()
    
    print("\n" + "="*60)
    print("DEMO COMPLETE")
    print("="*60)
    print("""
Key Takeaways:

1. Use PersonaFactory to create personas with different configurations
2. AgentContext provides immutable snapshots for cognitive modules
3. Cognitive modules are swappable strategies (Strategy Pattern)
4. State mutations are centralized in Persona, not spread across modules
5. InMemoryRepository enables easy unit testing
6. NEW: Pluggable strategies for memory scoring and reflection triggers
   allow fine-grained experimentation without modifying core modules

For experimentation:
  - Implement AbstractPlanner, AbstractRetriever, etc. for new cognitive approaches
  - Use MemoryScoringStrategy for retrieval algorithm experiments
  - Use ReflectionTrigger for reflection timing experiments""")


if __name__ == "__main__":
    main()