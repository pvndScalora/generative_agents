# Generative Agents: Project Documentation

## 👋 Informal Overview

### What is this project?
Imagine a video game like *The Sims*, but instead of the characters speaking gibberish and following simple scripts, they have real memories, make plans, and talk to each other in English. 

This project, **Generative Agents**, is a simulation of a small town populated by these AI-driven characters. They are designed to be believable simulacra of human behavior.

### How do the Agents work?
Unlike traditional game NPCs (Non-Player Characters), these agents possess a complex cognitive architecture:

1.  **They Remember**: If an agent sees another agent, they remember it. If they have a conversation, they remember what was said. They don't just react to the present; they are influenced by their past.
2.  **They Plan**: They wake up and plan their day (e.g., "I need to go to the store, then cook lunch"). If something unexpected happens (like a fire in the kitchen), they can change their plans.
3.  **They Reflect**: They don't just record events; they think about them. If an agent notices a messy desk every day, they might form the abstract thought "I am disorganized."
4.  **They Socialize**: They can engage in full natural language conversations with each other, spread rumors, and coordinate events (like a Valentine's Day party).

### The World
The agents live in a sandbox environment called "Smallville". It includes houses, a park, a store, and a bar. You can watch them move around, interact with objects (like making coffee), and talk to one another.

---

## ⚙️ Technical Documentation

### System Architecture

The system is divided into two main components that communicate via file storage:

1.  **The Environment Server (Frontend)**
    *   **Tech Stack**: Django (Python).
    *   **Role**: Renders the visual simulation in the browser, manages the map assets, and allows the user to "replay" or "demo" simulations.
    *   **Location**: `environment/frontend_server/`

2.  **The Simulation Server (Backend)**
    *   **Tech Stack**: Python.
    *   **Role**: The "Game Master" and the "Brain". It runs the simulation loop, processes agent decisions, and updates the state of the world.
    *   **Location**: `reverie/backend_server/`

### Core Components

#### 1. The Simulation Loop (`ReverieServer`)
*   **File**: [`reverie/backend_server/reverie.py`](reverie/backend_server/reverie.py)
*   **Description**: This is the main entry point. It initializes the world and the agents.
*   **Mechanism**: The simulation runs in discrete time steps.
    *   It reads the current environment state (where everyone is).
    *   It triggers the `move()` function for every agent.
    *   It calculates the new positions and actions.
    *   It saves the result to JSON files for the frontend to render.

#### 2. The Agent (`Persona`)
*   **File**: [`reverie/backend_server/persona/persona.py`](reverie/backend_server/persona/persona.py)
*   **Description**: The class representing a single generative agent. It acts as a container for the agent's memory and cognitive modules.

#### 3. Memory Structures
The agents rely on a stream of memories to function.
*   **Associative Memory** (`associative_memory.py`): The core database of the agent's life. It stores "Concept Nodes" (events, thoughts, chat). Retrieval is ranked by:
    *   *Recency*: How long ago did it happen?
    *   *Importance*: How significant is it?
    *   *Relevance*: How related is it to the current situation?
*   **Spatial Memory** (`spatial_memory.py`): A tree structure representing the agent's knowledge of the world (World -> House -> Room -> Object).
*   **Scratch** (`scratch.py`): Short-term working memory. It holds the current day's plan, the agent's current location, and immediate focus.

#### 4. Cognitive Modules
The "Brain" of the agent operates in a loop, processing information through several stages:
*   **Perceive** (`perceive.py`): Filters the raw environment data into what the agent actually notices (based on attention bandwidth).
*   **Retrieve** (`retrieve.py`): Fetches relevant memories from the Associative Memory based on the current context.
*   **Plan** (`plan.py`): Determines future actions. This involves:
    *   *Daily Planning*: Creating a high-level schedule for the day.
    *   *Recursive Decomposition*: Breaking down high-level tasks (e.g., "Write book") into actionable steps (e.g., "Sit down", "Turn on PC").
*   **Reflect** (`reflect.py`): A periodic process where the agent analyzes recent events to generate higher-level insights (Abstract thoughts).
*   **Converse** (`converse.py`): Handles dialogue generation when agents interact with each other.

#### 5. The Environment (`Maze`)
*   **File**: [`reverie/backend_server/maze.py`](reverie/backend_server/maze.py)
*   **Description**: Represents the map of the simulated world.
*   **Structure**: A 2D matrix of tiles. Each tile contains semantic information (e.g., "Kitchen", "Stove") and state (e.g., "On/Off").

### Data Flow
1.  **Frontend** writes `environment/<step>.json` (Current state of the world).
2.  **Backend** reads this file.
3.  **Backend** calculates agent decisions (Perceive -> Retrieve -> Plan -> Act).
4.  **Backend** writes `movement/<step>.json` (Where agents move next).
5.  **Frontend** reads the movement file and updates the visualization.
