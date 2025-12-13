import os
from pathlib import Path

# Base directory of the backend_server package
BASE_DIR = Path(__file__).resolve().parent

# Project root (generative_agents/)
PROJECT_ROOT = BASE_DIR.parent.parent

# Environment paths
ENVIRONMENT_DIR = PROJECT_ROOT / "environment"
FRONTEND_SERVER_DIR = ENVIRONMENT_DIR / "frontend_server"
STATIC_DIRS = FRONTEND_SERVER_DIR / "static_dirs"
ASSETS_DIR = STATIC_DIRS / "assets"

# Exported paths
MAZE_ASSETS_LOC = str(ASSETS_DIR)
ENV_MATRIX = str(ASSETS_DIR / "the_ville" / "matrix")
ENV_VISUALS = str(ASSETS_DIR / "the_ville" / "visuals")

FS_STORAGE = str(FRONTEND_SERVER_DIR / "storage")
FS_TEMP_STORAGE = str(FRONTEND_SERVER_DIR / "temp_storage")

COLLISION_BLOCK_ID = "32125"

# Debug flag
DEBUG = True

# API Keys
# Try to get from environment variable, fallback to the hardcoded one (for now)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
KEY_OWNER = os.getenv("KEY_OWNER", "pvnd")
