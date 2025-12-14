import json
import os
from reverie.backend_server.persona.memory_structures.spatial_memory import MemoryTree
from reverie.backend_server.persona.memory_structures.associative_memory import AssociativeMemory
from reverie.backend_server.persona.memory_structures.scratch import Scratch
from reverie.backend_server.global_methods import check_if_file_exists
from .base import MemoryRepository

class JsonMemoryRepository(MemoryRepository):
    def __init__(self, folder_mem_saved: str):
        self.folder_mem_saved = folder_mem_saved
        self.spatial_json_path = f"{folder_mem_saved}/bootstrap_memory/spatial_memory.json"
        self.associative_folder_path = f"{folder_mem_saved}/bootstrap_memory/associative_memory"
        self.scratch_json_path = f"{folder_mem_saved}/bootstrap_memory/scratch.json"
    
    def load_spatial_memory(self) -> MemoryTree:
        tree = {}
        if check_if_file_exists(self.spatial_json_path):
            with open(self.spatial_json_path) as f:
                tree = json.load(f)
        return MemoryTree(tree)

    def save_spatial_memory(self, memory: MemoryTree, save_folder: str):
        out_json = f"{save_folder}/spatial_memory.json"
        with open(out_json, "w") as outfile:
            json.dump(memory.tree, outfile)

    def load_associative_memory(self) -> AssociativeMemory:
        nodes = {}
        embeddings = {}
        kw_strength = {"kw_strength_event": {}, "kw_strength_thought": {}}
        
        nodes_path = f"{self.associative_folder_path}/nodes.json"
        embeddings_path = f"{self.associative_folder_path}/embeddings.json"
        kw_strength_path = f"{self.associative_folder_path}/kw_strength.json"

        if check_if_file_exists(nodes_path):
            with open(nodes_path) as f:
                nodes = json.load(f)
        
        if check_if_file_exists(embeddings_path):
            with open(embeddings_path) as f:
                embeddings = json.load(f)

        if check_if_file_exists(kw_strength_path):
            with open(kw_strength_path) as f:
                kw_strength = json.load(f)
                
        return AssociativeMemory(nodes, embeddings, kw_strength)

    def save_associative_memory(self, memory: AssociativeMemory, save_folder: str):
        out_folder = f"{save_folder}/associative_memory"
        os.makedirs(out_folder, exist_ok=True)
        
        state = memory.get_state()
        
        with open(f"{out_folder}/nodes.json", "w") as outfile:
            json.dump(state["nodes"], outfile)
            
        with open(f"{out_folder}/kw_strength.json", "w") as outfile:
            json.dump(state["kw_strength"], outfile)
            
        with open(f"{out_folder}/embeddings.json", "w") as outfile:
            json.dump(state["embeddings"], outfile)

    def load_scratch(self) -> Scratch:
        scratch_dict = {}
        if check_if_file_exists(self.scratch_json_path):
            with open(self.scratch_json_path) as f:
                scratch_dict = json.load(f)
        return Scratch(scratch_dict)

    def save_scratch(self, scratch: Scratch, save_folder: str):
        out_json = f"{save_folder}/scratch.json"
        scratch_dict = scratch.to_dict()
        with open(out_json, "w") as outfile:
            json.dump(scratch_dict, outfile, indent=2)
