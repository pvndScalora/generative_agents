import unittest
import shutil
import tempfile
import os
import json
import sys

# Add the project root to sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
backend_server_path = os.path.join(project_root, 'reverie', 'backend_server')
sys.path.append(project_root)
sys.path.append(backend_server_path)

from reverie.backend_server.persona.memory_structures.repository.json_repository import JsonMemoryRepository
from reverie.backend_server.persona.memory_structures.spatial_memory import MemoryTree
from reverie.backend_server.persona.memory_structures.associative_memory import AssociativeMemory
from reverie.backend_server.persona.memory_structures.scratch import Scratch

class TestJsonMemoryRepository(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory
        self.test_dir = tempfile.mkdtemp()
        self.bootstrap_dir = os.path.join(self.test_dir, "bootstrap_memory")
        os.makedirs(self.bootstrap_dir)
        
        # Setup paths
        self.spatial_path = os.path.join(self.bootstrap_dir, "spatial_memory.json")
        self.associative_dir = os.path.join(self.bootstrap_dir, "associative_memory")
        self.scratch_path = os.path.join(self.bootstrap_dir, "scratch.json")
        
        # Create dummy data for loading tests
        self.spatial_data = {"world": {"sector": {"arena": ["obj"]}}}
        with open(self.spatial_path, "w") as f:
            json.dump(self.spatial_data, f)
            
        os.makedirs(self.associative_dir)
        self.nodes_data = {
            "node_1": {
                "node_count": 1, 
                "type_count": 1, 
                "type": "event", 
                "depth": 0, 
                "created": "2023-01-01 00:00:00", 
                "expiration": None, 
                "subject": "s", 
                "predicate": "p", 
                "object": "o", 
                "description": "desc", 
                "embedding_key": "key", 
                "poignancy": 1, 
                "keywords": ["k"], 
                "filling": []
            }
        }
        self.embeddings_data = {"key": [0.1, 0.2]}
        self.kw_strength_data = {"kw_strength_event": {}, "kw_strength_thought": {}}
        
        with open(os.path.join(self.associative_dir, "nodes.json"), "w") as f:
            json.dump(self.nodes_data, f)
        with open(os.path.join(self.associative_dir, "embeddings.json"), "w") as f:
            json.dump(self.embeddings_data, f)
        with open(os.path.join(self.associative_dir, "kw_strength.json"), "w") as f:
            json.dump(self.kw_strength_data, f)
            
        self.scratch_data = {
            "vision_r": 4, 
            "att_bandwidth": 3, 
            "retention": 5, 
            "curr_time": "January 01, 2023, 00:00:00", 
            "curr_tile": [1, 2], 
            "daily_plan_req": "", 
            "name": "Test", 
            "age": 20, 
            "innate": "", 
            "learned": "", 
            "currently": "", 
            "lifestyle": "", 
            "living_area": "", 
            "concept_forget": 1, 
            "daily_reflection_time": 1, 
            "daily_reflection_size": 1, 
            "overlap_reflect_th": 1, 
            "kw_strg_event_reflect_th": 1, 
            "kw_strg_thought_reflect_th": 1, 
            "recency_w": 1, 
            "relevance_w": 1, 
            "importance_w": 1, 
            "recency_decay": 1, 
            "importance_trigger_max": 1, 
            "importance_trigger_curr": 1, 
            "importance_ele_n": 1, 
            "daily_req": [], 
            "f_daily_schedule": [], 
            "f_daily_schedule_hourly_org": [], 
            "act_address": "", 
            "act_start_time": None, 
            "act_duration": 1, 
            "act_description": "", 
            "act_pronunciatio": "", 
            "act_event": [1, 2, 3], 
            "act_obj_description": "", 
            "act_obj_pronunciatio": "", 
            "act_obj_event": [1, 2, 3], 
            "chatting_with": None, 
            "chat": None, 
            "chatting_with_buffer": {}, 
            "chatting_end_time": None, 
            "act_path_set": False, 
            "planned_path": []
        }
        with open(self.scratch_path, "w") as f:
            json.dump(self.scratch_data, f)

        self.repo = JsonMemoryRepository(self.test_dir)

    def tearDown(self):
        # Remove the directory after the test
        shutil.rmtree(self.test_dir)

    def test_load_spatial_memory(self):
        memory = self.repo.load_spatial_memory()
        self.assertIsInstance(memory, MemoryTree)
        self.assertEqual(memory.tree, self.spatial_data)

    def test_save_spatial_memory(self):
        save_dir = os.path.join(self.test_dir, "save_test")
        os.makedirs(save_dir)
        
        memory = MemoryTree({"new": "tree"})
        self.repo.save_spatial_memory(memory, save_dir)
        
        expected_path = os.path.join(save_dir, "spatial_memory.json")
        self.assertTrue(os.path.exists(expected_path))
        with open(expected_path) as f:
            data = json.load(f)
        self.assertEqual(data, {"new": "tree"})

    def test_load_associative_memory(self):
        memory = self.repo.load_associative_memory()
        self.assertIsInstance(memory, AssociativeMemory)
        # Check if data was loaded correctly (AssociativeMemory structure might be complex, 
        # checking internal dicts if accessible or just that it didn't crash)
        self.assertEqual(memory.embeddings, self.embeddings_data)
        # AssociativeMemory recalculates strength from nodes if loaded strength is empty
        # Our mock node has keyword "k", so we expect it to be present
        self.assertEqual(memory.kw_strength_event, {'k': 1})

    def test_save_associative_memory(self):
        save_dir = os.path.join(self.test_dir, "save_test_assoc")
        # os.makedirs(save_dir) # save_associative_memory creates the folder structure
        
        # Create a mock AssociativeMemory or use the one loaded
        memory = self.repo.load_associative_memory()
        self.repo.save_associative_memory(memory, save_dir)
        
        out_folder = os.path.join(save_dir, "associative_memory")
        self.assertTrue(os.path.exists(os.path.join(out_folder, "nodes.json")))
        self.assertTrue(os.path.exists(os.path.join(out_folder, "embeddings.json")))
        self.assertTrue(os.path.exists(os.path.join(out_folder, "kw_strength.json")))

    def test_load_scratch(self):
        scratch = self.repo.load_scratch()
        self.assertIsInstance(scratch, Scratch)
        self.assertEqual(scratch.vision_r, 4)

    def test_save_scratch(self):
        save_dir = os.path.join(self.test_dir, "save_test_scratch")
        os.makedirs(save_dir)
        
        scratch = self.repo.load_scratch()
        # Modify something
        scratch.vision_r = 10
        
        self.repo.save_scratch(scratch, save_dir)
        
        expected_path = os.path.join(save_dir, "scratch.json")
        self.assertTrue(os.path.exists(expected_path))
        with open(expected_path) as f:
            data = json.load(f)
        self.assertEqual(data["vision_r"], 10)

if __name__ == '__main__':
    unittest.main()
