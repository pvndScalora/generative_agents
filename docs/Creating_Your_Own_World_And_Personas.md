# Creating Your Own World and Personas

This guide will walk you through creating custom worlds and personas for the Generative Agents simulation. You can customize everything from the map layout to persona personalities and behaviors.

## Table of Contents
1. [Quick Start: Simple Customization](#quick-start-simple-customization)
2. [Understanding the Structure](#understanding-the-structure)
3. [Creating a New World](#creating-a-new-world)
4. [Creating Custom Personas](#creating-custom-personas)
5. [Advanced: Editing Maps with Tiled](#advanced-editing-maps-with-tiled)
6. [Running Your Custom Simulation](#running-your-custom-simulation)

---

## Quick Start: Simple Customization

The easiest way to create your own setup is to copy an existing base simulation and modify it.

### Step 1: Copy a Base Simulation

Navigate to `environment/frontend_server/storage/` and copy one of the base simulations:
- `base_the_ville_n25` - 25 agents (more complex)
- `base_the_ville_isabella_maria_klaus` - 3 agents (recommended for beginners)

```bash
# Example: Create a copy for your custom simulation
cp -r base_the_ville_isabella_maria_klaus base_my_custom_world
```

### Step 2: Modify the Simulation Metadata

Edit `base_my_custom_world/reverie/meta.json`:

```json
{
  "fork_sim_code": "base_my_custom_world",
  "start_date": "February 13, 2023",
  "curr_time": "February 13, 2023, 00:00:00",
  "sec_per_step": 10,
  "maze_name": "the_ville",
  "persona_names": [
    "Your First Persona",
    "Your Second Persona",
    "Your Third Persona"
  ],
  "step": 0
}
```

**Key fields:**
- `fork_sim_code`: Name of your simulation (should match folder name)
- `start_date` / `curr_time`: When your simulation begins
- `maze_name`: Name of the world map (default: "the_ville")
- `persona_names`: List of agent names in your simulation
- `sec_per_step`: Real-world seconds per simulation step (10 = each step is 10 seconds in-game)

### Step 3: Customize Your Personas

For each persona in the `personas/` folder, edit their configuration files.

---

## Understanding the Structure

A complete simulation consists of three main components:

### 1. World Definition (The Map)
Location: `environment/frontend_server/static_dirs/assets/the_ville/`

```
the_ville/
├── matrix/                          # World structure (CSV files)
│   ├── maze_meta_info.json         # Map dimensions and settings
│   ├── maze/                       # Core map data
│   │   ├── collision_maze.csv      # Walkable/blocked tiles
│   │   ├── sector_maze.csv         # Building/area definitions
│   │   ├── arena_maze.csv          # Room/space definitions
│   │   ├── game_object_maze.csv    # Interactive objects
│   │   └── spawning_location_maze.csv  # Agent spawn points
│   └── special_blocks/             # ID mappings
│       ├── world_blocks.csv        # World name mapping
│       ├── sector_blocks.csv       # Building name mappings
│       ├── arena_blocks.csv        # Room name mappings
│       └── game_object_blocks.csv  # Object name mappings
└── visuals/                        # Visual assets
    ├── the_ville.tmx               # Tiled map file (for editing)
    └── map_assets/                 # Tile graphics
```

### 2. Persona Definitions
Location: `environment/frontend_server/storage/<simulation_name>/personas/`

Each persona has a folder containing:

```
<Persona Name>/
└── bootstrap_memory/
    ├── scratch.json              # Core persona attributes
    ├── spatial_memory.json       # What locations they know about
    └── associative_memory/       # Initial memories
        ├── embeddings.json
        ├── kw_strength.json
        └── nodes.json
```

### 3. Simulation Metadata
Location: `environment/frontend_server/storage/<simulation_name>/reverie/`

```
reverie/
└── meta.json                     # Simulation configuration
```

---

## Creating a New World

### What is the "Maze" and Why Do We Need It?

The **maze** is the core data structure that defines your simulation world. It's called a "maze" because it's essentially a 2D grid where each tile can have different properties - some tiles are walkable, some are blocked, some belong to a cafe, others to a park, etc.

#### The Maze's Purpose

The maze serves several critical functions:

1. **Physical Layout**: Defines which tiles agents can walk on vs. walls/obstacles
2. **Spatial Organization**: Divides the world into meaningful areas (buildings, rooms)
3. **Object Placement**: Specifies where interactive objects exist
4. **Pathfinding**: Enables agents to navigate from point A to point B
5. **Perception**: Determines what agents can see and discover
6. **Context for AI**: Provides location information to the LLM for decision-making

#### How the Maze Works: A 2D Grid System

Imagine your world as a spreadsheet where each cell is a tile:

```
    0    1    2    3    4    5    (X coordinates)
0  [   ][   ][Wall][   ][   ][   ]
1  [   ][Cafe][Cafe][Cafe][   ][   ]
2  [Wall][Cafe][Cafe][Cafe][   ][   ]
3  [   ][   ][Wall][   ][Park][Park]
4  [   ][   ][   ][   ][Park][Park]
```
(Y coordinates)

Each tile at position [X, Y] stores information about:
- **What's there**: Is it a wall? Part of a cafe? A park?
- **What can you do**: Can you walk on it? What objects are there?
- **Where it belongs**: What sector, arena, and game object it represents

#### The 4-Level Hierarchy

The maze uses a hierarchical structure to organize space:

```
LEVEL 1: WORLD
└─ "the Ville" (the entire map)
   
   LEVEL 2: SECTOR (Buildings/Major Areas)
   ├─ "Hobbs Cafe"
   ├─ "Johnson Park"
   └─ "Isabella Rodriguez's apartment"
      
      LEVEL 3: ARENA (Rooms/Sub-areas)
      ├─ "cafe" (inside Hobbs Cafe)
      ├─ "kitchen" (inside Hobbs Cafe)
      └─ "main room" (inside Isabella's apartment)
         
         LEVEL 4: GAME OBJECTS (Interactive Items)
         ├─ "counter" (in the cafe)
         ├─ "refrigerator" (in the cafe)
         └─ "piano" (in the cafe)
```

**Why this hierarchy?**
- Agents make decisions top-down: "I want to eat → I should go to a restaurant (sector) → specifically the cafe area (arena) → and use the refrigerator (object)"
- It mirrors human spatial reasoning: "I'm going to Starbucks → to the seating area → to grab a chair"
- It enables efficient pathfinding and spatial queries

#### Visual Example: How Maze Data Maps to the World

Here's what a small section of maze CSV data looks like and what it represents:

**collision_maze.csv** (simplified):
```
32125,32125,32124,32124,32125
32125,32125,32125,32125,32125
32125,32125,32125,32125,32125
```
- `32125` = walkable tile (empty ground)
- `32124` = blocked tile (wall, obstacle)

**sector_maze.csv**:
```
0,0,0,32136,32136
0,0,32136,32136,32136
0,0,32136,32136,32136
```
- `0` = no sector (outdoor, generic space)
- `32136` = Hobbs Cafe sector (from special_blocks/sector_blocks.csv)

**arena_maze.csv**:
```
0,0,0,32236,32236
0,0,32236,32236,32236
0,0,32237,32237,32237
```
- `32236` = "cafe" arena within Hobbs Cafe
- `32237` = "kitchen" arena within Hobbs Cafe

**game_object_maze.csv**:
```
0,0,0,32336,0
0,0,32337,32338,0
0,0,0,0,0
```
- `32336` = "counter" object
- `32337` = "refrigerator" object
- `32338` = "piano" object
- `0` = no object (empty floor)

**Combined, this creates**:
```
[Empty][Empty][WALL ][Cafe ][Cafe ]
[Empty][Empty][Cafe ][Cafe ][Cafe ]
                Counter
[Empty][Empty][Cafe ][Cafe ][Cafe ]
              Kitchen Kitchen Kitchen
              Fridge  Piano
```

When an agent stands at position (3, 0), they see:
```
Tile data = {
  'world': 'the Ville',
  'sector': 'Hobbs Cafe',
  'arena': 'cafe',
  'game_object': 'counter',
  'collision': False (walkable),
  'events': set()  # who's doing what here
}
```

### Option 1: Use Existing Map with New Personas

If you're happy with "the Ville" map, you can skip world creation and just create new personas (see next section).

### Option 2: Create a Custom Map

#### Step 1: Install Tiled Map Editor

Download and install [Tiled](https://www.mapeditor.org/) - a free, open-source map editor.

#### Step 2: Create Map Structure

1. Open `environment/frontend_server/static_dirs/assets/the_ville/visuals/the_ville.tmx` in Tiled to see the example
2. Create a new map or modify the existing one
3. Export your map layers as CSV files

#### Step 3: Define Your World Hierarchy

The world uses a 4-level hierarchy:

```
World → Sector → Arena → Game Objects
  ↓        ↓        ↓          ↓
the Ville → Hobbs Cafe → cafe → refrigerator, counter, piano, etc.
```

**Example:**
- **World**: "the Ville" (the entire map)
- **Sector**: "Hobbs Cafe" (a building or outdoor area)
- **Arena**: "cafe" (a room within the building)
- **Game Objects**: "counter", "chairs", "coffee machine" (interactable items)

#### Step 4: Create Special Block Mappings

Edit files in `matrix/special_blocks/`:

**world_blocks.csv:**
```csv
32134, the Ville
```

**sector_blocks.csv:**
```csv
32136, the Ville, Hobbs Cafe
32165, the Ville, Isabella Rodriguez's apartment
32196, the Ville, The Rose and Crown Pub
```

**arena_blocks.csv:**
```csv
32236, the Ville, Hobbs Cafe, cafe
32265, the Ville, Isabella Rodriguez's apartment, main room
32296, the Ville, The Rose and Crown Pub, pub
```

**game_object_blocks.csv:**
```csv
32336, the Ville, Hobbs Cafe, cafe, counter
32337, the Ville, Hobbs Cafe, cafe, refrigerator
32338, the Ville, Hobbs Cafe, cafe, piano
```

**Important Notes:**
- The first number is a unique ID for that block type in the Tiled map
- Each level must reference its parent in the hierarchy
- Use consistent naming throughout

#### Step 5: Create Maze CSV Files

In `matrix/maze/`, create these CSV files. Each file must be the exact same dimensions (matching your `maze_width` × `maze_height` from meta info).

##### 1. collision_maze.csv - Physical Layout

This defines which tiles agents can walk on.

**Format**: Each cell contains a tile ID
- `32125` = **Walkable** (empty ground, floors, paths)
- `32124` = **Blocked** (walls, water, obstacles, void)

**Example** (10×5 grid):
```csv
32124,32124,32124,32124,32124,32124,32124,32124,32124,32124
32124,32125,32125,32125,32124,32125,32125,32125,32125,32124
32124,32125,32125,32125,32124,32125,32125,32125,32125,32124
32124,32125,32125,32125,32124,32125,32125,32125,32125,32124
32124,32124,32124,32124,32124,32124,32124,32124,32124,32124
```

This creates:
```
##########  (# = wall/blocked)
#   # ... #  (space = walkable)
#   # ... #
#   # ... #
##########
```

**Rules**:
- Agents cannot pathfind through `32124` tiles
- Always surround your map with blocked tiles to prevent agents from walking off the edge
- Interior walls should use `32124` to separate rooms

##### 2. sector_maze.csv - Buildings and Major Areas

This divides the world into major locations (buildings, outdoor areas).

**Format**: Each cell contains a sector block ID from `special_blocks/sector_blocks.csv`
- `0` = No sector (generic outdoor space, void)
- `32136` = Hobbs Cafe (example)
- `32165` = Isabella Rodriguez's apartment (example)
- `32196` = The Rose and Crown Pub (example)

**Example** (matching the collision map above):
```csv
0,0,0,0,0,0,0,0,0,0
0,32136,32136,32136,0,32165,32165,32165,32165,0
0,32136,32136,32136,0,32165,32165,32165,32165,0
0,32136,32136,32136,0,32165,32165,32165,32165,0
0,0,0,0,0,0,0,0,0,0
```

This creates:
```
          (empty outdoor space)
 [Cafe ] | [  Apartment    ]
 [Cafe ] | [  Apartment    ]
 [Cafe ] | [  Apartment    ]
```

**Rules**:
- Each unique sector needs an entry in `special_blocks/sector_blocks.csv`
- Sectors should typically align with walkable areas
- Use `0` for outdoor areas that don't belong to any building
- Sector boundaries should be contiguous (same sector tiles touching)

**special_blocks/sector_blocks.csv** must define:
```csv
32136, the Ville, Hobbs Cafe
32165, the Ville, Isabella Rodriguez's apartment
```

##### 3. arena_maze.csv - Rooms and Sub-areas

This divides sectors into smaller functional areas (rooms, zones within buildings).

**Format**: Each cell contains an arena block ID from `special_blocks/arena_blocks.csv`
- `0` = No specific arena
- `32236` = "cafe" arena within Hobbs Cafe
- `32265` = "main room" arena within apartment

**Example**:
```csv
0,0,0,0,0,0,0,0,0,0
0,32236,32236,32236,0,32265,32265,32265,32265,0
0,32237,32237,32237,0,32265,32265,32265,32265,0
0,32237,32237,32237,0,32265,32265,32265,32265,0
0,0,0,0,0,0,0,0,0,0
```

This creates:
```
 [cafe      ] | [ main room      ]
 [kitchen   ] | [ main room      ]
 [kitchen   ] | [ main room      ]
```

**Rules**:
- Arenas must be within sectors (don't put an arena where sector = 0)
- Each unique arena needs an entry in `special_blocks/arena_blocks.csv`
- Multiple arenas can exist within one sector
- Arenas enable fine-grained location awareness ("I'm in the kitchen, not just in Hobbs Cafe")

**special_blocks/arena_blocks.csv** must define:
```csv
32236, the Ville, Hobbs Cafe, cafe
32237, the Ville, Hobbs Cafe, kitchen
32265, the Ville, Isabella Rodriguez's apartment, main room
```

##### 4. game_object_maze.csv - Interactive Objects

This places specific objects that agents can interact with.

**Format**: Each cell contains a game object block ID from `special_blocks/game_object_blocks.csv`
- `0` = No object (empty floor)
- `32336` = "counter"
- `32337` = "refrigerator"
- `32338` = "piano"

**Example**:
```csv
0,0,0,0,0,0,0,0,0,0
0,32336,0,32338,0,32339,0,0,0,0
0,32337,0,0,0,0,0,0,0,0
0,0,0,0,0,0,0,32340,0,0
0,0,0,0,0,0,0,0,0,0
```

This places:
```
Row 1: counter at (1,1), piano at (3,1), desk at (5,1)
Row 2: refrigerator at (1,2)
Row 3: bed at (7,3)
```

**Rules**:
- Objects must be in arenas (don't place where arena = 0)
- Each unique object needs an entry in `special_blocks/game_object_blocks.csv`
- Objects should be on walkable tiles (usually)
- Multiple objects can exist in one arena
- Agents will navigate to these specific tiles to "use" objects

**special_blocks/game_object_blocks.csv** must define:
```csv
32336, the Ville, Hobbs Cafe, cafe, counter
32337, the Ville, Hobbs Cafe, cafe, refrigerator
32338, the Ville, Hobbs Cafe, cafe, piano
32339, the Ville, Isabella Rodriguez's apartment, main room, desk
32340, the Ville, Isabella Rodriguez's apartment, main room, bed
```

##### 5. spawning_location_maze.csv - Agent Starting Positions

This marks where agents can initially spawn.

**Format**: Each cell contains a spawning location ID
- `0` = Not a valid spawn point
- `32340` = Valid spawn location (ID from `special_blocks/spawning_location_blocks.csv`)

**Example**:
```csv
0,0,0,0,0,0,0,0,0,0
0,0,32340,0,0,0,32340,0,0,0
0,0,0,0,0,0,0,0,0,0
0,32340,0,0,0,0,0,0,32340,0
0,0,0,0,0,0,0,0,0,0
```

**Rules**:
- Mark several spawn points throughout the map
- Spawn points should be on walkable tiles
- Distribute them across different sectors
- Agents will start at random spawn points unless specifically placed

**Important**: Each CSV file must have the same dimensions and should align logically:
- Objects should only be placed in arenas
- Arenas should only be placed in sectors
- Everything should respect collision boundaries

#### Step 6: Update Maze Metadata

Edit `matrix/maze_meta_info.json`:

```json
{
  "world_name": "my custom world",
  "maze_width": 140,
  "maze_height": 100,
  "sq_tile_size": 32,
  "special_constraint": ""
}
```

**Fields explained**:
- `world_name`: Display name for your world (used in tile data as the "world" level)
- `maze_width`: Number of tiles wide (must match CSV columns)
- `maze_height`: Number of tiles tall (must match CSV rows)
- `sq_tile_size`: Pixel size of each tile (32 = each tile is 32×32 pixels)
- `special_constraint`: Leave empty (used for custom constraints if needed)

**Critical**: The `maze_width` × `maze_height` must exactly match the dimensions of all your CSV files. If your CSV is 140 columns × 100 rows, these values must be 140 and 100.

#### Understanding the Complete Data Flow

Here's how all the maze data works together when an agent acts:

**Scenario**: Isabella wants to make coffee.

1. **AI Decision**: "I need to make coffee → I should go to Hobbs Cafe → specifically the cafe area → and use the coffee machine"

2. **Spatial Memory Check**: Does Isabella know about Hobbs Cafe? Check her `spatial_memory.json`:
   ```json
   {
     "the Ville": {
       "Hobbs Cafe": {
         "cafe": ["counter", "coffee machine", "refrigerator"]
       }
     }
   }
   ```
   ✅ Yes, she knows about it!

3. **Find the Location**: The system searches the maze for tiles where:
   - `sector` = "Hobbs Cafe" (ID 32136)
   - `arena` = "cafe" (ID 32236)
   - `game_object` = "coffee machine" (ID 32337)

4. **Pathfinding**: Calculate a walkable path from Isabella's current position to the coffee machine tile:
   - Use `collision_maze.csv` to avoid walls (32124)
   - Only step on walkable tiles (32125)

5. **Execute Action**: Isabella walks the path and "uses" the coffee machine, which updates the tile's `events` to show she's there

**Another Example**: What if Isabella wants to go somewhere she doesn't know?

1. **AI Decision**: "I want to visit the park"

2. **Spatial Memory Check**: Is "Johnson Park" in her spatial memory?
   ```json
   {
     "the Ville": {
       "Hobbs Cafe": { ... }
     }
   }
   ```
   ❌ No!

3. **Result**: Isabella **cannot** go to the park because she doesn't know it exists yet.

4. **Discovery**: She can only learn about it by:
   - Walking nearby (within `vision_r` tiles) and seeing it
   - Being told about it by another agent
   - Having it in her initial memories

This is why `spatial_memory.json` is crucial - it limits what agents "know" about the world.

---

## Creating Custom Personas

### Practical Example: Creating a Small 10×10 World

Let's create a tiny complete world to understand how everything fits together.

**Our world will have**:
- A 10×10 tile map
- One cafe (4×4 tiles)
- One apartment (4×4 tiles)
- A hallway connecting them

#### Step 1: Create maze_meta_info.json

```json
{
  "world_name": "tiny town",
  "maze_width": 10,
  "maze_height": 10,
  "sq_tile_size": 32,
  "special_constraint": ""
}
```

#### Step 2: Define Special Blocks

**special_blocks/world_blocks.csv**:
```csv
32134, tiny town
```

**special_blocks/sector_blocks.csv**:
```csv
32136, tiny town, Cozy Cafe
32165, tiny town, Home Apartment
```

**special_blocks/arena_blocks.csv**:
```csv
32236, tiny town, Cozy Cafe, main area
32265, tiny town, Home Apartment, living room
```

**special_blocks/game_object_blocks.csv**:
```csv
32336, tiny town, Cozy Cafe, main area, counter
32337, tiny town, Cozy Cafe, main area, table
32338, tiny town, Home Apartment, living room, bed
32339, tiny town, Home Apartment, living room, desk
```

#### Step 3: Create Maze CSV Files

**maze/collision_maze.csv** (X = wall, . = walkable):
```csv
32124,32124,32124,32124,32124,32124,32124,32124,32124,32124
32124,32125,32125,32125,32124,32125,32125,32125,32125,32124
32124,32125,32125,32125,32124,32125,32125,32125,32125,32124
32124,32125,32125,32125,32125,32125,32125,32125,32125,32124
32124,32125,32125,32125,32124,32125,32125,32125,32125,32124
32124,32124,32124,32124,32124,32124,32124,32124,32124,32124
32124,32125,32125,32125,32124,32125,32125,32125,32125,32124
32124,32125,32125,32125,32124,32125,32125,32125,32125,32124
32124,32125,32125,32125,32125,32125,32125,32125,32125,32124
32124,32124,32124,32124,32124,32124,32124,32124,32124,32124
```

Visual representation:
```
##########
#...#....#
#...#....#
#........#  <- hallway connects them
#...#....#
##########
#...#....#
#...#....#
#........ #  <- hallway
##########
```

**maze/sector_maze.csv**:
```csv
0,0,0,0,0,0,0,0,0,0
0,32136,32136,32136,0,0,0,0,0,0
0,32136,32136,32136,0,0,0,0,0,0
0,32136,32136,32136,0,0,0,0,0,0
0,32136,32136,32136,0,0,0,0,0,0
0,0,0,0,0,0,0,0,0,0
0,0,0,0,0,32165,32165,32165,32165,0
0,0,0,0,0,32165,32165,32165,32165,0
0,0,0,0,0,32165,32165,32165,32165,0
0,0,0,0,0,0,0,0,0,0
```

Visual:
```
          (walls/outside)
 [Cafe  ]     (empty hallway)
 [Cafe  ]     
 [Cafe  ]..... (hallway)
 [Cafe  ]     
          
         [Apartment]
         [Apartment]
         [Apartment]
```

**maze/arena_maze.csv**:
```csv
0,0,0,0,0,0,0,0,0,0
0,32236,32236,32236,0,0,0,0,0,0
0,32236,32236,32236,0,0,0,0,0,0
0,32236,32236,32236,0,0,0,0,0,0
0,32236,32236,32236,0,0,0,0,0,0
0,0,0,0,0,0,0,0,0,0
0,0,0,0,0,32265,32265,32265,32265,0
0,0,0,0,0,32265,32265,32265,32265,0
0,0,0,0,0,32265,32265,32265,32265,0
0,0,0,0,0,0,0,0,0,0
```

**maze/game_object_maze.csv**:
```csv
0,0,0,0,0,0,0,0,0,0
0,32336,0,0,0,0,0,0,0,0
0,0,32337,0,0,0,0,0,0,0
0,0,0,0,0,0,0,0,0,0
0,0,0,0,0,0,0,0,0,0
0,0,0,0,0,0,0,0,0,0
0,0,0,0,0,32338,0,0,0,0
0,0,0,0,0,0,0,32339,0,0
0,0,0,0,0,0,0,0,0,0
0,0,0,0,0,0,0,0,0,0
```

Visual:
```
 [C    ]  (C = counter at (1,1))
 [ T   ]  (T = table at (2,2))
 
 
 
         [B    ]  (B = bed at (5,6))
         [   D ]  (D = desk at (7,7))
```

**maze/spawning_location_maze.csv**:
```csv
0,0,0,0,0,0,0,0,0,0
0,0,32340,0,0,0,0,0,0,0
0,0,0,0,0,0,0,0,0,0
0,0,0,0,0,0,0,0,0,0
0,0,0,0,0,0,0,0,0,0
0,0,0,0,0,0,0,0,0,0
0,0,0,0,0,0,0,32340,0,0
0,0,0,0,0,0,0,0,0,0
0,0,0,0,0,0,0,0,0,0
0,0,0,0,0,0,0,0,0,0
```

Two spawn points: one in the cafe (2,1) and one in the apartment (7,6).

#### What the Final World Looks Like

When an agent stands at position (1, 1) in the cafe:
```javascript
tile_data = {
  'world': 'tiny town',
  'sector': 'Cozy Cafe',
  'arena': 'main area',
  'game_object': 'counter',
  'collision': False,  // walkable
  'events': set()
}
```

When they stand at position (7, 7) in the apartment:
```javascript
tile_data = {
  'world': 'tiny town',
  'sector': 'Home Apartment',
  'arena': 'living room',
  'game_object': 'desk',
  'collision': False,
  'events': set()
}
```

When they stand in the hallway at position (4, 3):
```javascript
tile_data = {
  'world': 'tiny town',
  'sector': '',         // no sector (hallway)
  'arena': '',          // no arena
  'game_object': '',    // no object
  'collision': False,   // still walkable
  'events': set()
}
```

**Key Insights**:
- Each CSV layer adds information to the same tile
- `0` means "nothing here" for that layer
- Blocked tiles (32124) prevent movement even if other layers have data
- The hierarchy must be consistent: objects only in arenas, arenas only in sectors

---

## Creating Custom Personas

### Understanding Persona Configuration

Each persona is defined by three key files in their `bootstrap_memory/` folder:

### 1. scratch.json - Core Attributes

This file defines the persona's fundamental characteristics:

```json
{
  "vision_r": 8,              // How far they can see (in tiles)
  "att_bandwidth": 8,         // How many things they can pay attention to
  "retention": 8,             // How well they remember things
  
  "curr_time": null,          // Simulation time (auto-managed)
  "curr_tile": null,          // Current position (auto-managed)
  
  "daily_plan_req": "Isabella Rodriguez opens Hobbs Cafe at 8am everyday, and works at the counter until 8pm, at which point she closes the cafe.",
  
  "name": "Isabella Rodriguez",
  "first_name": "Isabella",
  "last_name": "Rodriguez",
  "age": 34,
  
  "innate": "friendly, outgoing, hospitable",
  "learned": "Isabella Rodriguez is a cafe owner of Hobbs Cafe who loves to make people feel welcome. She is always looking for ways to make the cafe a place where people can come to relax and enjoy themselves.",
  "currently": "Isabella Rodriguez is planning on having a Valentine's Day party at Hobbs Cafe with her customers on February 14th, 2023 at 5pm.",
  "lifestyle": "Isabella Rodriguez goes to bed around 11pm, awakes up around 6am.",
  "living_area": "the Ville:Isabella Rodriguez's apartment:main room",
  
  "concept_forget": 100,
  "daily_reflection_time": 180,
  "daily_reflection_size": 5,
  "overlap_reflect_th": 4,
  "kw_strg_event_reflect_th": 10,
  "kw_strg_thought_reflect_th": 9,
  
  "recency_w": 1,
  "relevance_w": 1,
  "importance_w": 1,
  "recency_decay": 0.995,
  "importance_trigger_max": 150,
  "importance_trigger_curr": 150,
  "importance_ele_n": 0,
  "thought_count": 5,
  
  "daily_req": [],
  "f_daily_schedule": [],
  "f_daily_schedule_hourly_org": [],
  
  "act_address": null,
  "act_start_time": null,
  "act_duration": null,
  "act_description": null,
  "act_pronunciatio": null,
  "act_event": ["Isabella Rodriguez", null, null],
  "act_obj_description": null,
  "act_obj_pronunciatio": null,
  "act_obj_event": [null, null, null],
  "chatting_with": null,
  "chat": null,
  "chatting_with_buffer": {},
  "chatting_end_time": null,
  "act_path_set": false,
  "planned_path": []
}
```

#### Key Fields Explained:

**Identity & Personality:**
- `name`, `first_name`, `last_name`, `age`: Basic identity
- `innate`: Fundamental personality traits (adjectives)
- `learned`: Detailed background and learned behaviors (paragraph form)
- `currently`: Current situation, goals, or plans (what they're focused on now)
- `lifestyle`: Daily routines, sleep schedule
- `living_area`: Where they live (format: "World:Sector:Arena")

**Daily Routine:**
- `daily_plan_req`: High-level description of their daily routine (used by AI to generate schedule)

**Cognitive Parameters:**
- `vision_r`: Vision radius in tiles (8 = can see 8 tiles in each direction)
- `att_bandwidth`: Number of nearby events/objects they notice
- `retention`: Memory persistence (higher = better memory)
- `recency_w`, `relevance_w`, `importance_w`: Weights for memory retrieval (keep at 1)
- `recency_decay`: How quickly memories fade (0.995 is default)
- `importance_trigger_max/curr`: When to trigger reflection (higher = less frequent reflection)

**Advanced Parameters (usually leave as defaults):**
- `concept_forget`: Memory forgetting threshold
- `daily_reflection_time`: Time spent on daily reflection (seconds)
- `daily_reflection_size`: Number of reflections per day
- `overlap_reflect_th`: Threshold for overlapping reflections
- `kw_strg_*_reflect_th`: Keyword strength thresholds

**Auto-managed Fields (leave as null/empty):**
- `curr_time`, `curr_tile`: Auto-set by simulation
- `daily_req`, `f_daily_schedule`, etc.: Auto-generated during simulation
- All `act_*` fields: Current action state (auto-managed)

### 2. spatial_memory.json - Known Locations

This defines what locations and objects the persona knows about initially:

```json
{
  "the Ville": {
    "Hobbs Cafe": {
      "cafe": [
        "refrigerator",
        "cafe customer seating",
        "cooking area",
        "kitchen sink",
        "behind the cafe counter",
        "piano"
      ],
      "kitchen": [
        "stove",
        "oven",
        "sink"
      ]
    },
    "Isabella Rodriguez's apartment": {
      "main room": [
        "bed",
        "desk",
        "refrigerator",
        "closet",
        "shelf"
      ]
    }
  }
}
```

**Important:**
- Only include locations the persona has been to or knows about
- The structure must match your world hierarchy: `World > Sector > Arena > [Objects]`
- Personas will discover new locations as they explore
- They can only go to places in their spatial memory (unless they discover them)

### 3. associative_memory/ - Initial Memories

This folder contains the persona's initial memory stream:

**nodes.json** - List of memories:
```json
[
  {
    "node_id": 1,
    "node_count": 1,
    "type_count": 1,
    "type": "event",
    "depth": 0,
    "created": "February 13, 2023, 00:00:00",
    "expiration": null,
    "subject": "Isabella Rodriguez",
    "predicate": "is",
    "object": "idle",
    "description": "Isabella Rodriguez is idle",
    "embedding_key": "Isabella Rodriguez is idle",
    "poignancy": 1,
    "keywords": ["Isabella Rodriguez", "idle"],
    "filling": []
  }
]
```

**kw_strength.json** - Keyword associations (auto-generated, can leave empty initially):
```json
{}
```

**embeddings.json** - Vector embeddings (auto-generated, can leave empty initially):
```json
{}
```

### Creating a Persona from Scratch

1. **Copy an existing persona folder** as a template
2. **Edit scratch.json** with your persona's attributes
3. **Edit spatial_memory.json** with locations they should know
4. **Edit associative_memory/nodes.json** for initial memories (or leave minimal)

**Example: Creating "Alice Smith", a librarian**

**scratch.json** (key fields):
```json
{
  "name": "Alice Smith",
  "first_name": "Alice",
  "last_name": "Smith",
  "age": 42,
  "innate": "organized, quiet, intellectual, helpful",
  "learned": "Alice Smith is the head librarian at Oak Hill College Library. She has worked there for 15 years and knows the collection intimately. She loves helping students find the perfect book and maintains a meticulous card catalog.",
  "currently": "Alice Smith is preparing for the upcoming book fair and is curating a special collection on local history.",
  "lifestyle": "Alice Smith wakes up at 6am, arrives at the library by 7:30am, works until 5pm, and goes to bed around 10pm.",
  "living_area": "the Ville:Alice Smith's apartment:main room",
  "daily_plan_req": "Alice Smith opens the library at 7:30am, helps students throughout the day, organizes books, and closes the library at 5pm.",
  "vision_r": 8,
  "att_bandwidth": 8,
  "retention": 10
}
```

**spatial_memory.json**:
```json
{
  "the Ville": {
    "Oak Hill College": {
      "library": [
        "front desk",
        "bookshelves",
        "reading area",
        "card catalog"
      ]
    },
    "Alice Smith's apartment": {
      "main room": [
        "bed",
        "bookshelf",
        "desk",
        "kitchen area"
      ]
    }
  }
}
```

### Using Agent History Files for Initial Memories

Instead of manually editing associative_memory files, you can load initial memories using a history file.

#### Step 1: Create a History CSV File

Create a file in `environment/frontend_server/static_dirs/assets/the_ville/`:

**my_agents_history.csv**:
```csv
Name,Whisper
Alice Smith,You have been the head librarian for 15 years; You are organizing a book fair next week; You love helping students with research; Your favorite book is Pride and Prejudice
Bob Johnson,You are a freshman at Oak Hill College; You are studying computer science; You frequent the library to study; You have a part-time job at the local cafe
```

**Format:**
- Column 1: `Name` - Must match persona name exactly
- Column 2: `Whisper` - Semicolon-separated list of facts/memories
- Use semicolons (`;`) to separate individual memories
- Each memory should be a complete sentence or fact

#### Step 2: Load the History File

When starting your simulation:

```bash
python reverie.py
```

When prompted:
1. Enter fork simulation name: `base_my_custom_world`
2. Enter new simulation name: `test_run_1`
3. At "Enter option:" prompt, type:
   ```
   call -- load history the_ville/my_agents_history.csv
   ```

This will inject the memories into each persona's memory stream.

---

## Advanced: Editing Maps with Tiled

### Installing Tiled

1. Download from [mapeditor.org](https://www.mapeditor.org/)
2. Install the application

### Opening the Ville Map

1. Open Tiled
2. File → Open: `environment/frontend_server/static_dirs/assets/the_ville/visuals/the_ville.tmx`

### Understanding Layers

The map uses multiple layers:
- **Background**: Visual background tiles
- **Collision**: Defines walkable/blocked areas
- **Sector**: Marks building boundaries
- **Arena**: Marks room boundaries within buildings
- **Game Objects**: Places interactive objects
- **Spawning**: Agent starting positions

### Creating a New Map

1. **File → New Map**
   - Orientation: Orthogonal
   - Tile size: 32x32 pixels
   - Map size: 140x100 tiles (or your custom size)

2. **Add Tilesets**
   - Map → Add External Tileset
   - Browse to map_assets and add your tile graphics

3. **Create Layers** for each type (collision, sector, arena, game_object, spawning)

4. **Assign Tile IDs** matching your special_blocks CSV files

5. **Export Layers**:
   - Right-click each layer → Export As
   - Save as CSV in `matrix/maze/` folder
   - Name: `collision_maze.csv`, `sector_maze.csv`, etc.

### Editing Existing Maps

1. Open `the_ville.tmx`
2. Use the Tile Stamp tool to paint new areas
3. Add new sectors/arenas by using the correct tile IDs from special_blocks
4. Export modified layers as CSV
5. Update special_blocks CSV files with any new IDs

**Important Constraints:**

- **Living Area**: Each persona can only enter their own apartment/room
  - The room name must contain the persona's name (e.g., "Isabella Rodriguez's apartment")
- **Collision**: Blocked tiles (ID 32125) cannot be walked through
- **Object Accessibility**: Personas can only interact with objects in their spatial memory

---

## Running Your Custom Simulation

### Step 1: Verify Your Setup

Ensure you have:
- ✅ A simulation folder in `environment/frontend_server/storage/`
- ✅ `reverie/meta.json` with correct persona names
- ✅ A `personas/` folder with one subfolder per persona
- ✅ Each persona folder has `bootstrap_memory/` with required JSON files
- ✅ (Optional) Agent history CSV file if using custom memories

### Step 2: Start the Environment Server

```bash
cd environment/frontend_server
python manage.py runserver
```

Visit [http://localhost:8000/](http://localhost:8000/) to verify it's running.

### Step 3: Start the Simulation Server

```bash
cd reverie/backend_server
python reverie.py
```

When prompted:

**Enter the name of the forked simulation:**
```
base_my_custom_world
```

**Enter the name of the new simulation:**
```
my_first_test
```

*Optional - Load history file:*
```
call -- load history the_ville/my_agents_history.csv
```

### Step 4: Run the Simulation

At the "Enter option:" prompt:

```
run 100
```

This will run 100 simulation steps (each step = 10 seconds by default, so 100 steps = ~16.7 minutes in-game).

View the simulation at: [http://localhost:8000/simulator_home](http://localhost:8000/simulator_home)

### Step 5: Save Your Simulation

When ready to save:

```
fin
```

This saves and exits. Next time, you can resume by using `my_first_test` as the fork simulation.

---

## Common Issues and Solutions

### Issue: "Persona cannot find location"

**Cause**: The location is not in their `spatial_memory.json`

**Solution**: 
- Add the location to their spatial memory, OR
- Let them discover it naturally by being near it (vision_r range)

### Issue: "Persona stuck or not moving"

**Cause**: 
- Blocked path (collision tiles)
- Invalid living_area in scratch.json
- Target location doesn't exist in the maze

**Solution**:
- Check collision_maze.csv for blocked paths
- Verify living_area format: "World:Sector:Arena"
- Ensure the location exists in the maze CSV files

### Issue: "Persona ignoring their daily_plan_req"

**Cause**: The AI may interpret the plan differently, or the required locations aren't accessible

**Solution**:
- Be more specific in daily_plan_req
- Ensure all mentioned locations exist in their spatial_memory
- Check that locations exist in the maze

### Issue: "CSV export from Tiled doesn't match expected format"

**Cause**: Tiled exports include row/column headers or use different delimiters

**Solution**:
- Export as CSV (Comma-separated)
- Remove any header rows
- Ensure each cell contains just the tile ID number

### Issue: "Simulation runs slowly or makes too many API calls"

**Cause**: More personas = more LLM calls

**Solution**:
- Start with 3-5 personas for testing
- Increase `importance_trigger_max` to reduce reflection frequency
- Use smaller `vision_r` to limit perception scope

---

## Best Practices

### Maze Design Best Practices

#### Collision and Pathfinding

**DO**:
- ✅ Surround your entire map with blocked tiles (32124) to create a border
- ✅ Leave at least 1-2 tile width for hallways/paths between rooms
- ✅ Ensure every location has at least one walkable path to other locations
- ✅ Test pathfinding by manually tracing routes on paper

**DON'T**:
- ❌ Create isolated areas with no path in/out
- ❌ Make hallways too narrow (1 tile wide can cause agent traffic jams)
- ❌ Forget to block off areas you don't want accessible (map edges, water, etc.)

#### Sector and Arena Design

**DO**:
- ✅ Keep sectors contiguous (all tiles of "Cafe" should touch each other)
- ✅ Make sectors large enough to be meaningful (at least 4×4 tiles minimum)
- ✅ Create distinct arenas within sectors (kitchen vs. dining area)
- ✅ Name sectors and arenas clearly ("John's Bedroom" not "room_01")

**DON'T**:
- ❌ Split one sector across non-connected areas
- ❌ Make sectors too small (1-2 tiles is too tiny)
- ❌ Overlap sectors (each tile should belong to only one sector)
- ❌ Use identical names for different places

#### Object Placement

**DO**:
- ✅ Place objects on walkable tiles (so agents can reach them)
- ✅ Spread objects out (not all on adjacent tiles)
- ✅ Put objects in appropriate arenas (bed in bedroom, not in kitchen)
- ✅ Include essential objects for daily activities (bed, desk, kitchen items)

**DON'T**:
- ❌ Cluster too many objects on one tile
- ❌ Place objects on walls or blocked tiles
- ❌ Put objects in hallways (use 0 for empty walkways)
- ❌ Forget objects that personas mention in their routines

#### Spatial Memory Alignment

**Critical**: Personas can only go to places in their spatial_memory.json, which must match the maze.

**DO**:
- ✅ Ensure every location in spatial_memory exists in the maze
- ✅ Use exact same names (case-sensitive) in both places
- ✅ Include the persona's living_area in their spatial memory
- ✅ Give personas knowledge of communal areas (cafes, parks, etc.)

**DON'T**:
- ❌ Misspell location names between maze and spatial memory
- ❌ Reference sectors/arenas that don't exist in the maze
- ❌ Forget to include a persona's own home in their spatial memory

#### Common Maze Patterns

**Pattern 1: Simple Building**
```
Sector: Office Building
├─ Arena: Lobby (3×5 tiles)
├─ Arena: Office 1 (3×3 tiles)
├─ Arena: Office 2 (3×3 tiles)
└─ Arena: Conference Room (4×5 tiles)
```

**Pattern 2: Apartment Complex**
```
Sector: Apartment Complex
├─ Arena: Hallway (2 tile wide path)
├─ Arena: Alice's Apartment (4×4 tiles)
│   └─ Objects: bed, desk, kitchen counter
├─ Arena: Bob's Apartment (4×4 tiles)
│   └─ Objects: bed, desk, kitchen counter
└─ Arena: Shared Laundry Room (3×3 tiles)
    └─ Objects: washing machine, dryer
```

**Pattern 3: Mixed Indoor/Outdoor**
```
Sector: Main Street (no specific arena, outdoor)
Sector: Cafe (with "seating" and "kitchen" arenas)
Sector: Park (with "playground" and "pond" arenas)
Sector: Library (with "reading room" and "stacks" arenas)
```

#### Size Recommendations

| Element | Minimum Size | Recommended Size | Notes |
|---------|-------------|------------------|-------|
| Entire Map | 20×20 tiles | 100×100 tiles | Larger = more exploration |
| Sector | 3×3 tiles | 8×8 to 20×20 tiles | Must fit arenas inside |
| Arena | 2×2 tiles | 4×4 to 8×8 tiles | Must fit objects inside |
| Hallway Width | 1 tile | 2-3 tiles | Prevents congestion |
| Border (walls) | 1 tile thick | 1-2 tiles | Prevents edge-walking |

#### CSV File Dimensions

**All CSV files must have identical dimensions**. If your maze is 100×140:
- Every CSV must have 100 rows
- Every CSV must have 140 columns
- No more, no less

**Validation Checklist**:
1. Count rows in collision_maze.csv = maze_height ✓
2. Count columns in collision_maze.csv = maze_width ✓
3. All other CSVs match these dimensions ✓
4. maze_meta_info.json width/height match CSV dimensions ✓

### Start Small
- Begin with 3-5 personas
- Use the existing "the Ville" map
- Test thoroughly before adding more complexity

### Persona Design
- Make personas distinct and interesting
- Give them clear goals and motivations in the `currently` field
- Ensure their `living_area` exists in the map
- Use specific, detailed `learned` descriptions

### World Design
- Keep the hierarchy simple: World → Sector → Arena → Objects
- Name locations clearly and consistently
- Ensure every persona has a home (living_area)
- Create enough communal spaces for interaction (cafes, parks, etc.)

### Memory and Behavior
- Start with minimal initial memories (just basic facts)
- Let personas develop naturally through simulation
- Use agent history files for complex backstories
- Monitor the first few simulation steps to catch issues early

### Testing
- Run short simulations first (10-50 steps)
- Watch persona movement in the browser
- Check logs for errors
- Save frequently with `fin` command

---

## Example: Complete Custom Setup

Let's create a complete example: "University Campus" with 3 students.

### 1. Create Simulation Folder

```bash
cd environment/frontend_server/storage
cp -r base_the_ville_isabella_maria_klaus base_university_campus
cd base_university_campus
```

### 2. Edit reverie/meta.json

```json
{
  "fork_sim_code": "base_university_campus",
  "start_date": "September 1, 2023",
  "curr_time": "September 1, 2023, 08:00:00",
  "sec_per_step": 10,
  "maze_name": "the_ville",
  "persona_names": [
    "Emma Chen",
    "Lucas Martinez",
    "Sophia Patel"
  ],
  "step": 0
}
```

### 3. Rename and Configure Personas

Rename persona folders:
```bash
cd personas
mv "Isabella Rodriguez" "Emma Chen"
mv "Maria Lopez" "Lucas Martinez"
mv "Klaus Mueller" "Sophia Patel"
```

**Emma Chen/bootstrap_memory/scratch.json** (excerpt):
```json
{
  "name": "Emma Chen",
  "first_name": "Emma",
  "last_name": "Chen",
  "age": 20,
  "innate": "studious, friendly, organized, ambitious",
  "learned": "Emma Chen is a junior computer science major at Oak Hill College. She loves coding and spends most of her time in the computer lab or library. She's working on her senior project early.",
  "currently": "Emma Chen is preparing for her algorithms midterm next week and is looking for a study group.",
  "lifestyle": "Emma Chen wakes up at 7am, attends classes from 9am-3pm, studies at the library until 9pm, and goes to bed at 11pm.",
  "living_area": "the Ville:Dorm for Oak Hill College:Emma Chen's room",
  "daily_plan_req": "Emma Chen attends her computer science classes in the morning, has lunch at the cafe at noon, studies at the library in the afternoon and evening."
}
```

**Emma Chen/bootstrap_memory/spatial_memory.json**:
```json
{
  "the Ville": {
    "Oak Hill College": {
      "classroom": ["desks", "whiteboard", "projector"],
      "computer lab": ["computers", "printer"]
    },
    "Dorm for Oak Hill College": {
      "Emma Chen's room": ["bed", "desk", "computer", "bookshelf"]
    },
    "Hobbs Cafe": {
      "cafe": ["cafe customer seating", "counter"]
    }
  }
}
```

### 4. Create Agent History File

**environment/frontend_server/static_dirs/assets/the_ville/university_students.csv**:
```csv
Name,Whisper
Emma Chen,You are a computer science major; You love programming and algorithms; You are preparing for your midterm exam; You want to form a study group; Lucas Martinez is in your algorithms class
Lucas Martinez,You are a physics major; You are also taking algorithms as an elective; You play guitar in your free time; You know Emma Chen from class; You often study at Hobbs Cafe
Sophia Patel,You are a biology pre-med student; You volunteer at the campus health center; You are friends with Emma Chen; You enjoy running in Johnson Park every morning; You study at the library most evenings
```

### 5. Run the Simulation

```bash
# Terminal 1
cd environment/frontend_server
python manage.py runserver

# Terminal 2
cd reverie/backend_server
python reverie.py
```

**Commands:**
```
Enter the name of the forked simulation: base_university_campus
Enter the name of the new simulation: campus_week1
Enter option: call -- load history the_ville/university_students.csv
Enter option: run 500
```

Watch at: [http://localhost:8000/simulator_home](http://localhost:8000/simulator_home)

---

## Additional Resources

- **Main README**: [README.md](../README.md) - Basic setup and running simulations
- **Persona Behavior**: [docs/Persona_behavior.md](Persona_behavior.md) - Deep dive into how personas make decisions
- **Research Paper**: [Generative Agents: Interactive Simulacra of Human Behavior](https://arxiv.org/abs/2304.03442)
- **Tiled Documentation**: [mapeditor.org/docs](https://doc.mapeditor.org/)

---

## Summary Checklist

### Quick Reference: What Information Does the World Need?

Here's a complete overview of what data you need to define for your world:

#### 1. Physical Structure (The Maze)

| File | Purpose | What It Defines | Valid Values |
|------|---------|----------------|--------------|
| `maze_meta_info.json` | Map settings | Width, height, world name | JSON with dimensions |
| `collision_maze.csv` | Walkability | Which tiles can be walked on | `32125` (walk) or `32124` (blocked) |
| `sector_maze.csv` | Buildings/areas | Which sector each tile belongs to | Sector IDs from special_blocks or `0` |
| `arena_maze.csv` | Rooms/zones | Which room/area within sector | Arena IDs from special_blocks or `0` |
| `game_object_maze.csv` | Interactive items | What objects exist where | Object IDs from special_blocks or `0` |
| `spawning_location_maze.csv` | Start positions | Where agents can initially spawn | Spawn IDs or `0` |

**Key Rule**: All CSV files must be the exact same dimensions (width × height from meta info).

#### 2. Naming Mappings (Special Blocks)

| File | Purpose | Format |
|------|---------|--------|
| `world_blocks.csv` | Maps ID to world name | `32134, the Ville` |
| `sector_blocks.csv` | Maps ID to sector name | `32136, the Ville, Hobbs Cafe` |
| `arena_blocks.csv` | Maps ID to arena name | `32236, the Ville, Hobbs Cafe, cafe` |
| `game_object_blocks.csv` | Maps ID to object name | `32336, the Ville, Hobbs Cafe, cafe, counter` |
| `spawning_location_blocks.csv` | Maps ID to spawn point | `32340, the Ville, spawn_1` |

**Key Rule**: IDs must be unique. Names must follow the hierarchy (World > Sector > Arena > Object).

#### 3. Visual Assets (Optional but Recommended)

| File/Folder | Purpose |
|-------------|---------|
| `the_ville.tmx` | Tiled map file for visual editing |
| `map_assets/` | PNG tiles and sprites for rendering |
| `*.png` | Collision maps and visual layers |

**Key Rule**: If using Tiled, export each layer as CSV to the maze/ folder.

#### 4. How the Data Works Together

```
When an agent decides: "I want to make coffee"
                        ↓
1. Check spatial_memory.json
   → Do I know about any cafes with a coffee machine?
   → Yes: "Hobbs Cafe" → "cafe" → "coffee machine"
                        ↓
2. Query the maze
   → Find all tiles where:
     - sector_maze = 32136 (Hobbs Cafe)
     - arena_maze = 32236 (cafe)
     - game_object_maze = 32337 (coffee machine)
   → Result: Tile at position (25, 45)
                        ↓
3. Pathfinding
   → Use collision_maze to find walkable path
   → Avoid all tiles with 32124 (blocked)
   → Only step on tiles with 32125 (walkable)
                        ↓
4. Execute movement
   → Walk to (25, 45)
   → Perform "making coffee" action
   → Update tile's events to show agent is there
```

### What Makes a "Good" World?

A well-designed world should have:

✅ **Clear Structure**: Distinct sectors (buildings) with logical arenas (rooms)  
✅ **Connectivity**: All locations reachable via walkable paths  
✅ **Appropriate Scale**: Large enough for exploration, small enough to navigate (100×100 recommended)  
✅ **Rich Detail**: Enough objects for diverse activities (beds, desks, kitchen items, etc.)  
✅ **Persona Homes**: Each persona has a private living_area they can access  
✅ **Communal Spaces**: Shared areas like cafes, parks where personas can meet  
✅ **Spatial Variety**: Mix of indoor and outdoor, public and private spaces  
✅ **Logical Naming**: Clear, descriptive names that make sense to the LLM  

### Minimal World Requirements

At minimum, your world must have:

1. **One sector** (e.g., "Main Building")
2. **One arena per persona** (their living space)
3. **One communal arena** (where personas can interact)
4. **Basic objects in each arena** (bed, desk at minimum)
5. **Walkable paths** connecting all areas
6. **Collision boundaries** preventing agents from walking off-map

**Example minimal world**:
```
World: "Simple Town"
├─ Sector: "Residential Building"
│  ├─ Arena: "Alice's Room" (objects: bed, desk)
│  └─ Arena: "Bob's Room" (objects: bed, desk)
└─ Sector: "Community Center"
   └─ Arena: "Main Hall" (objects: table, chairs)
```

This creates two private spaces and one shared space - enough for basic simulation.

---

## Summary Checklist

When creating a custom setup, make sure you have:

- [ ] Copied and renamed a base simulation folder
- [ ] Updated `reverie/meta.json` with your simulation details
- [ ] Created/renamed persona folders matching `persona_names` in meta.json
- [ ] Configured each persona's `scratch.json` (especially: name, age, innate, learned, currently, lifestyle, living_area, daily_plan_req)
- [ ] Set up each persona's `spatial_memory.json` with known locations
- [ ] (Optional) Created an agent history CSV file
- [ ] Verified that all `living_area` locations exist in the map
- [ ] Started the environment server
- [ ] Started the simulation server with your simulation name
- [ ] (Optional) Loaded agent history file
- [ ] Run a test simulation with a small step count

Happy simulating! 🎭
