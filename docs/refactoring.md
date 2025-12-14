# Refactoring & Architecture Improvements

This document outlines a comprehensive plan to improve the `generative_agents` codebase, focusing on maintainability, scalability, and robustness. The recommendations are based on First Principles of Software Engineering and standard Design Patterns.

## 1. First Principles Analysis

### A. Modularity (Architecture & Imports)
**Current State:** The codebase relies on implicit dependencies (`sys.path.append`, `from global_methods import *`), making it brittle and hard to navigate.
**Recommendation:**
*   **Package Structure:** Convert folders into proper Python packages by adding `__init__.py` files.
*   **Explicit Imports:** Use absolute imports (e.g., `from reverie.backend_server.utils import logs`) instead of wildcards.
*   **Utils Module:** Refactor `global_methods.py` into a structured `utils` package.

### B. Abstraction (Data Modeling)
**Current State:** Core entities like Actions and Plans are represented by raw lists (e.g., `['sleeping', 360]`) and string parsing, leading to "Magic String" vulnerabilities.
**Recommendation:**
*   **Strong Typing:** Use `Dataclasses` or `Pydantic` models to define clear schemas for `Action`, `Plan`, and `Memory`.
*   **Type Hinting:** Add Python type hints to function signatures to improve developer experience and catch errors early.

### C. Robustness (Configuration vs. Logic)
**Current State:** "Magic Numbers" (e.g., `1440` minutes) and hardcoded paths/dates are scattered throughout the logic.
**Recommendation:**
*   **Centralized Config:** Move all constants, file paths, and simulation settings to a dedicated `config.py` file.
*   **Environment Variables:** Load sensitive keys and environment-specific settings from `.env` files.

### D. Observability & Error Handling
**Current State:** Debugging relies on `print` statements, and error handling is often too broad (`try...except` catching everything).
**Recommendation:**
*   **Logging:** Implement the standard `logging` library to allow configurable log levels (DEBUG, INFO, ERROR).
*   **Specific Exceptions:** Catch specific errors and implement retry logic (e.g., using `tenacity`) for external API calls (LLMs).

---

## 2. Strategic Refactoring Plan

To achieve robustness and modularity, we will move from a "God Object" pattern to a **Component-Based Architecture**.

### 1. Deconstruct the "God Object" (`Persona`)
**Current State:** The `Persona` class and its `scratch` attribute hold *everything*. Functions like `retrieve(persona, ...)` take the entire agent state as input, making unit testing impossible and coupling every module to every other module.

**Refactoring Strategy:**
*   **Dependency Injection:** Instead of passing `persona`, pass only the data a module needs.
    *   *Before:* `retrieve(persona, focal_points)`
    *   *After:* `retriever.retrieve(memory_stream=persona.memory, query=focal_points)`
*   **Component Registry:** The `Persona` class should become a lightweight controller that holds instances of interchangeable components (Memory, Planner, Perceiver).

### 2. Abstracting Cognitive Modules (The Strategy Pattern)
**Current State:** Logic for retrieval, planning, and reflection is hardcoded in standalone functions (`retrieve.py`, `plan.py`). To change the retrieval formula, you have to edit the core source code.

**Refactoring Strategy:** Define interfaces (Abstract Base Classes) for each cognitive step. This allows you to swap "brains" via configuration.

*   **Retrieval Strategy:**
    *   Create an `AbstractRetriever` class.
    *   Implement `WeightedScoreRetriever` (the current Recency/Importance/Relevance logic).
    *   *Experiment:* Easily add a `VectorDBRetriever` or `HybridRetriever` without touching the rest of the code.
*   **Reflection Strategy:**
    *   Create an `AbstractReflector`.
    *   *Experiment:* Change the `reflection_trigger` from "sum of importance > 150" to "every 10 turns" or "LLM-decided trigger."

### 3. Memory Backend Abstraction
**Current State:** `AssociativeMemory` is tightly coupled to the file system (`nodes.json`) and specific Python dictionaries. It loads *everything* into RAM.

**Refactoring Strategy:**
*   **Repository Pattern:** Create a `MemoryRepository` interface.
*   **Implementations:**
    *   `JsonMemoryRepository`: The current implementation (good for debugging).
    *   `VectorDbRepository`: Use ChromaDB or Pinecone for the embeddings (better performance/scaling).
    *   `SqliteRepository`: For structured metadata.
*   **Benefit:** You can run simulations with 10,000 memories without crashing the server.

### 4. Centralized LLM Gateway
**Current State:** Calls to `ChatGPT_safe_generate_response` are scattered inside prompt templates.

**Refactoring Strategy:**
*   **LLM Service Layer:** Create a central `LLMClient` that handles:
    *   Rate limiting & Retries (Robustness).
    *   Cost tracking.
    *   Model swapping (e.g., switch from GPT-3.5 to GPT-4 or a local Llama model for specific tasks).
*   **Prompt Registry:** Move prompts out of python files into YAML/JSON templates so non-coders can tweak the "personality" of the prompts.

### 5. Configuration-Driven Experiments
**Current State:** Hyperparameters (decay rates, importance thresholds) are buried in code constants.

**Refactoring Strategy:**
*   Use a config system (like `Hydra` or `Pydantic`).
*   Define an experiment via a config file:
    ```yaml
    agent_config:
      name: "Sherlock_Holmes"
      retrieval:
        strategy: "WeightedScore"
        params:
          recency_weight: 0.5
          relevance_weight: 2.0 # High focus on relevance
      memory:
        backend: "ChromaDB"
    ```

---

## 3. Action Plan

1.  **Phase 1: Cleanup** - Fix imports, add `__init__.py`, and set up `logging`.
2.  **Phase 2: Configuration** - Extract magic numbers and paths to `config.py`.
3.  **Phase 3: Typing** - Introduce `models.py` with Dataclasses for core entities.
4.  **Phase 4: Core Refactoring**
    *   **Data Model Integration:** Refactor `scratch.py`, `associative_memory.py`, and `spatial_memory.py` to use the new `models.py` dataclasses (`PersonaIdentity`, `Action`, `Memory`, `Coordinate`).
    *   **Module Abstraction:** Refactor `plan.py` and `retrieve.py` to use the Strategy Pattern, allowing for swappable implementations.
    *   **Persona Deconstruction:** Update the main `Persona` class to act as a controller, injecting dependencies into the cognitive modules.
    *   **Memory Backend Abstraction:** refactor to use the repository pattern.
    *   **LLM Gateway:** Implement a centralized service for LLM calls with retry logic and cost tracking.
