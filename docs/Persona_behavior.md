# How Personas Know What They Can Do and Where

The system uses a **three-layer architecture** for spatial awareness:

## 1. Spatial Memory (`MemoryTree`) — What the persona *knows*

Each persona has a **spatial memory** stored in `spatial_memory.json`. It's a hierarchical tree:

```
World → Sector → Arena → [Game Objects]
```

For example, Isabella Rodriguez knows:
```json
{
  "the Ville": {
    "Hobbs Cafe": {
      "cafe": ["refrigerator", "cafe customer seating", "cooking area", "piano", ...]
    },
    "Isabella Rodriguez's apartment": {
      "main room": ["bed", "desk", "refrigerator", "closet", "shelf"]
    }
  }
}
```

This memory **expands dynamically** as the persona explores — when they walk around, the `LegacyPerceiver` adds new locations they see:

```python
# From perceiver - adds newly seen areas to spatial memory
for tile in nearby_tiles:
    if tile["world"] not in self.scratch.s_mem.tree:
        self.scratch.s_mem.tree[tile["world"]] = {}
    if tile["sector"] not in self.scratch.s_mem.tree[tile["world"]]:
        self.scratch.s_mem.tree[tile["world"]][tile["sector"]] = {}
    # ... adds arenas and game objects
```

**Related files:**
- `reverie/backend_server/persona/memory_structures/spatial_memory.py` — MemoryTree class
- `environment/frontend_server/storage/<sim>/personas/<name>/bootstrap_memory/spatial_memory.json` — Per-persona data

---

## 2. The Maze — What actually exists in the world

The `Maze` class defines the complete world through CSV files exported from Tiled map editor:
- `sector_maze.csv` — Defines sectors (e.g., "Hobbs Cafe", "Johnson Park")
- `arena_maze.csv` — Defines arenas within sectors (e.g., "cafe", "park")
- `game_object_maze.csv` — Defines interactable objects (e.g., "bed", "piano")

Each tile stores metadata:
```python
self.tiles[y][x] = {
    'world': 'the Ville',
    'sector': 'Hobbs Cafe', 
    'arena': 'cafe',
    'game_object': 'piano',
    'collision': False,
    'events': set()  # Who's doing what here
}
```

**Related files:**
- `reverie/backend_server/maze.py` — Maze class
- `environment/frontend_server/static_dirs/assets/the_ville/matrix/` — CSV maze data

---

## 3. LLM-Driven Decision Making — Where to go for an action

When a persona decides to do something (e.g., "eat breakfast"), the planner asks GPT where to go using a **three-step prompt chain**:

### Step 1: Choose Sector (`ActionSectorPrompt`)
```
Isabella Rodriguez lives in {Isabella Rodriguez's apartment} that has main room.
Isabella Rodriguez is currently in {Hobbs Cafe} that has cafe.
Area options: {Isabella Rodriguez's apartment, Hobbs Cafe, Johnson Park, ...}

For eating breakfast, Isabella Rodriguez should go to: {___}
```
→ The LLM picks from **accessible sectors** in spatial memory

### Step 2: Choose Arena (`ActionArenaPrompt`)
```
Isabella Rodriguez is going to Hobbs Cafe.
Hobbs Cafe has: cafe, kitchen, back room
For eating breakfast, which area? {___}
```
→ Picks an arena within the chosen sector

### Step 3: Choose Object (`ActionGameObjectPrompt`)
```
For eating breakfast, which of the following objects?
Options: refrigerator, cafe customer seating, cooking area, kitchen sink
```
→ Picks a specific object to interact with

**Related files:**
- `reverie/backend_server/persona/prompt_template/prompts.py` — Prompt classes
- `reverie/backend_server/persona/cognitive_modules/planner/legacy.py` — Planning logic
- `reverie/backend_server/persona/prompt_template/v1/action_location_sector_v1.txt` — Prompt template

---

## The Full Flow

```
1. Daily Plan: "eat breakfast at 7am"
                    ↓
2. Query Spatial Memory: "What sectors do I know about?"
                    ↓
3. LLM decides: Sector → Arena → Game Object
                    ↓
4. Result: "the Ville:Hobbs Cafe:cafe:cafe customer seating"
                    ↓
5. Pathfinding: Calculate route to that tile
                    ↓
6. Execute: Walk there and perform action
```

---

## Key Constraints

| Constraint | Description |
|------------|-------------|
| **Living Area** | Personas can only enter private rooms matching their name (e.g., "Isabella's room" for Isabella) |
| **Vision Radius** | Personas only discover new areas within their `vision_r` tiles |
| **Collision** | Cannot walk through blocked tiles |
| **Events** | Track who's doing what at each location to enable interactions |

---

## Perception Loop

The cognitive pipeline runs every simulation step:

```
Perceive → Retrieve → Plan → Reflect → Execute
```

1. **Perceive**: Scan nearby tiles, add new locations to spatial memory, observe events
2. **Retrieve**: Query associative memory for relevant past experiences
3. **Plan**: Use LLM to decide next action and location
4. **Reflect**: Generate insights from accumulated experiences
5. **Execute**: Pathfind and move to destination

**Main entry point:** `Persona.move()` in `reverie/backend_server/persona/persona.py`
