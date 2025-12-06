# Generative Agents: Reverie Simulation

## 👋 Informal Overview

Imagine a video game like *The Sims*, but instead of the characters speaking gibberish and following simple scripts, they have real memories, make plans, and talk to each other in English.

This project, **Reverie**, is a simulation of a small town populated by these "Generative Agents".

*   **They Remember**: If an agent sees another agent, they remember it. If they have a conversation, they remember what was said.
*   **They Plan**: They wake up and plan their day (e.g., "I need to go to the store, then cook lunch").
*   **They Reflect**: They don't just record events; they think about them. If they see a messy desk every day, they might form the thought "I am disorganized."

It is a sandbox for observing emergent social behavior among AI agents. You can watch them throw parties, spread rumors, or just go about their daily lives.

---

## ⚙️ Technical Documentation

### Core Architecture

The system follows a hierarchical structure where the `ReverieServer` manages the world state, and individual `Persona` instances manage agent behavior. The architecture is designed to simulate human-like memory and decision-making.

### 1. The Simulation Server (`ReverieServer`)
*   **File**: [`backend_server/reverie.py`](backend_server/reverie.py)
*   **Role**: The "Game Master". It handles the physics, time progression, and the main loop.
*   **Key Mechanism**: It advances time in steps. At each step, it collects actions from all agents, updates the environment (the "Maze"), and serves the new environment state back to the agents.

### 2. The Agent (`Persona`)
*   **File**: [`backend_server/persona/persona.py`](backend_server/persona/persona.py)
*   **Role**: The cognitive entity. It is not just a state machine; it's a memory-processing unit.
*   **Components**:
    *   **Memory Stream**: The database of the agent's life.
    *   **Cognitive Modules**: The functions that process memory into action.

### 3. Memory Structures
Located in [`backend_server/persona/memory_structures/`](backend_server/persona/memory_structures/).

*   **Associative Memory** (`associative_memory.py`): The core database. It stores "Concept Nodes" (events, thoughts, chat). Retrieval is ranked by three factors:
    1.  **Recency**: How long ago did it happen?
    2.  **Importance**: How significant is it?
    3.  **Relevance**: How related is it to the current situation?
*   **Spatial Memory** (`spatial_memory.py`): A tree structure representing the world (World -> House -> Room -> Object).
*   **Scratch** (`scratch.py`): Short-term working memory for the current day's plan and immediate focus.

### 4. Cognitive Modules
Located in [`backend_server/persona/cognitive_modules/`](backend_server/persona/cognitive_modules/).

The "Brain" of the agent operates in a loop:
1.  **Perceive** (`perceive.py`): Filters the raw environment data into what the agent actually notices (based on attention bandwidth).
2.  **Retrieve** (`retrieve.py`): Fetches relevant memories for the current context.
3.  **Plan** (`plan.py`): Determines future actions. This includes:
    *   *Daily Planning*: High-level schedule.
    *   *Recursive Decomposition*: Breaking "Write book" into "Sit down", "Turn on PC", etc.
4.  **Reflect** (`reflect.py`): A periodic process where the agent looks at recent events to generate higher-level insights (Abstract thoughts).
5.  **Converse** (`converse.py`): Handles dialogue generation when agents interact.

### Directory Map
```text
reverie/
├── backend_server/
│   ├── reverie.py              # Main Simulation Loop
│   ├── maze.py                 # Environment/Map handling
│   ├── persona/
│   │   ├── persona.py          # Agent Class
│   │   ├── memory_structures/  # Long-term & Short-term memory
│   │   └── cognitive_modules/  # Perception, Planning, Reflection
│   └── prompt_template/        # LLM Prompts (GPT inputs)
```
