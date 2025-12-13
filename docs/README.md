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

---

## 🧠 Deep Dive: Agent Interactions (First Principles)

How do two independent AI agents actually "talk"? It's not magic; it's a sequence of data processing steps. We can break down an interaction into five fundamental stages.

### 1. Discovery (The Physics of Meeting)
Before agents can talk, they must exist in the same space.
*   **Principle**: **Proximity**.
*   **Mechanism**: The `Maze` calculates the Euclidean distance between Agent A and Agent B.
*   **Code**: In `perceive.py`, the system checks if another agent is within the `vision_radius` (usually 4-8 tiles).
*   **Result**: Agent A's `perceived_events` list now includes `("Agent B", "is", "present")`.

### 2. Contextualization (The Memory Lookup)
Seeing someone isn't enough; you need to know *who* they are to you.
*   **Principle**: **Associative Retrieval**.
*   **Mechanism**: The agent queries its `AssociativeMemory` using the name "Agent B" as the query key.
*   **Ranking**: The memory returns results based on:
    1.  **Recency**: "Did we talk yesterday?"
    2.  **Importance**: "Is this my wife or a stranger?"
    3.  **Relevance**: "Does this relate to my current goal?"
*   **Result**: Agent A retrieves a summary: *"Agent B is my neighbor who likes gardening."*

### 3. Decision (The Cognitive Filter)
Just because you see someone doesn't mean you stop to chat. You might be busy.
*   **Principle**: **Opportunity Cost**.
*   **Mechanism**: The `decide_to_talk()` function runs a logic check (often an LLM call).
*   **Input**:
    *   Current Plan: "I am rushing to the bathroom." (High Urgency)
    *   Relationship: "Agent B is a stranger." (Low Importance)
*   **Output**: `False` (Ignore) or `True` (Initiate Conversation).

### 4. Execution (The Dialogue Loop)
If the decision is `True`, the simulation enters a "Conversation Mode".
*   **Principle**: **Generative State**.
*   **Mechanism**:
    1.  **Prompt Engineering**: The system constructs a massive text prompt containing:
        *   Agent A's Persona (Traits, Mood).
        *   Agent A's Goal ("I want to ask about the party").
        *   The Memory Context ("I know Agent B likes parties").
        *   The Previous Dialogue History.
    2.  **LLM Generation**: The LLM generates the next line of dialogue.
    3.  **Turn-Taking**: The system passes the new line to Agent B, who repeats the process.

### 5. Consequence (Memory Formation)
When the conversation ends, it must not be forgotten.
*   **Principle**: **Compression**.
*   **Mechanism**: Storing the full raw text is inefficient and distracts future retrievals.
*   **Process**:
    1.  **Summarization**: An LLM summarizes the 20-line chat into: *"Agent A invited Agent B to the Valentine's party."*
    2.  **Storage**: This summary is saved as a new `ConceptNode` in the `AssociativeMemory`.
    3.  **Reflection**: Later, this node might trigger a reflection: *"I am hosting a party" -> "I need to buy drinks."*

