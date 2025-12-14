import unittest
from unittest.mock import MagicMock, patch
import sys
import os
import datetime

# Add project root to sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
backend_server_path = os.path.join(project_root, 'reverie', 'backend_server')
sys.path.append(project_root)
sys.path.append(backend_server_path)

from reverie.backend_server.persona.persona import Persona

class TestPersona(unittest.TestCase):
    def setUp(self):
        # Patch the dependencies
        # We patch the classes where they are imported in persona.py
        self.repo_patcher = patch('reverie.backend_server.persona.persona.JsonMemoryRepository')
        self.mock_repo_cls = self.repo_patcher.start()
        self.mock_repo = self.mock_repo_cls.return_value

        # Mock the legacy modules classes
        self.perceiver_patcher = patch('reverie.backend_server.persona.persona.LegacyPerceiver')
        self.mock_perceiver_cls = self.perceiver_patcher.start()
        
        self.retriever_patcher = patch('reverie.backend_server.persona.persona.LegacyRetriever')
        self.mock_retriever_cls = self.retriever_patcher.start()

        self.planner_patcher = patch('reverie.backend_server.persona.persona.LegacyPlanner')
        self.mock_planner_cls = self.planner_patcher.start()

        self.executor_patcher = patch('reverie.backend_server.persona.persona.LegacyExecutor')
        self.mock_executor_cls = self.executor_patcher.start()

        self.reflector_patcher = patch('reverie.backend_server.persona.persona.LegacyReflector')
        self.mock_reflector_cls = self.reflector_patcher.start()

        self.converser_patcher = patch('reverie.backend_server.persona.persona.LegacyConverser')
        self.mock_converser_cls = self.converser_patcher.start()

    def tearDown(self):
        self.repo_patcher.stop()
        self.perceiver_patcher.stop()
        self.retriever_patcher.stop()
        self.planner_patcher.stop()
        self.executor_patcher.stop()
        self.reflector_patcher.stop()
        self.converser_patcher.stop()

    def test_initialization(self):
        """
        Test that the Persona initializes correctly via create_from_folder:
        1. Instantiates the JsonMemoryRepository.
        2. Loads spatial, associative, and scratch memory from the repository.
        3. Initializes all cognitive modules (Perceiver, Retriever, etc.) with scratch.
        """
        persona = Persona.create_from_folder("Klaus")
        
        # Verify repository usage
        self.mock_repo_cls.assert_called_once()
        self.mock_repo.load_spatial_memory.assert_called_once()
        self.mock_repo.load_associative_memory.assert_called_once()
        self.mock_repo.load_scratch.assert_called_once()
        
        scratch = self.mock_repo.load_scratch.return_value

        # Verify modules are initialized with the scratch instance
        self.mock_perceiver_cls.assert_called_with(scratch)
        self.mock_retriever_cls.assert_called_with(scratch)
        self.mock_planner_cls.assert_called_with(scratch)
        self.mock_executor_cls.assert_called_with(scratch)
        self.mock_reflector_cls.assert_called_with(scratch)
        self.mock_converser_cls.assert_called_with(scratch)

    def test_save(self):
        """
        Test that the save method delegates persistence to the repository.
        It should call save_spatial_memory, save_associative_memory, and save_scratch
        with the correct memory objects and folder path.
        """
        persona = Persona.create_from_folder("Klaus")
        save_folder = "test_folder"
        persona.save(save_folder)
        
        self.mock_repo.save_spatial_memory.assert_called_with(persona.s_mem, save_folder)
        self.mock_repo.save_associative_memory.assert_called_with(persona.a_mem, save_folder)
        self.mock_repo.save_scratch.assert_called_with(persona.scratch, save_folder)

    def test_move_new_day_logic(self):
        """
        Test the logic for detecting a new day within the move() method.
        - "First day": If scratch.curr_time is None.
        - "New day": If the date of the new curr_time differs from scratch.curr_time.
        - False: If the date is the same.
        """
        # Construct Persona manually with mocks
        scratch = MagicMock()
        repo = MagicMock()
        s_mem = MagicMock()
        a_mem = MagicMock()
        perceiver = MagicMock()
        retriever = MagicMock()
        planner = MagicMock()
        executor = MagicMock()
        reflector = MagicMock()
        converser = MagicMock()
        
        persona = Persona("Klaus", repo, scratch, s_mem, a_mem, 
                          perceiver, retriever, planner, executor, reflector, converser)
        
        # Setup common args
        curr_tile = (10, 10)
        maze = MagicMock()
        personas = {}
        
        # Case 1: First day (curr_time is None)
        scratch.curr_time = None
        curr_time = datetime.datetime(2023, 1, 1, 10, 0)
        
        persona.move(maze, personas, curr_tile, curr_time)
        
        # Check that plan was called with new_day="First day"
        # plan signature: plan(maze, personas, new_day, retrieved)
        persona.planner.plan.assert_called()
        args, _ = persona.planner.plan.call_args
        self.assertEqual(args[2], "First day")
        
        # Case 2: Same day
        scratch.curr_time = datetime.datetime(2023, 1, 1, 9, 0)
        curr_time = datetime.datetime(2023, 1, 1, 10, 0)
        
        persona.move(maze, personas, curr_tile, curr_time)
        args, _ = persona.planner.plan.call_args
        self.assertEqual(args[2], False)

        # Case 3: New day
        scratch.curr_time = datetime.datetime(2023, 1, 1, 23, 0)
        curr_time = datetime.datetime(2023, 1, 2, 8, 0)
        
        persona.move(maze, personas, curr_tile, curr_time)
        args, _ = persona.planner.plan.call_args
        self.assertEqual(args[2], "New day")

    def test_move_execution_flow(self):
        """
        Test the sequence of cognitive steps in the move() method:
        1. Updates scratch with current tile and time.
        2. Calls perceive() -> retrieve() -> plan() -> reflect() -> execute().
        3. Verifies data is passed correctly between these steps.
        """
        # Construct Persona manually with mocks
        scratch = MagicMock()
        repo = MagicMock()
        s_mem = MagicMock()
        a_mem = MagicMock()
        perceiver = MagicMock()
        retriever = MagicMock()
        planner = MagicMock()
        executor = MagicMock()
        reflector = MagicMock()
        converser = MagicMock()
        
        persona = Persona("Klaus", repo, scratch, s_mem, a_mem, 
                          perceiver, retriever, planner, executor, reflector, converser)
        
        # Setup mocks
        maze = MagicMock()
        personas = {}
        curr_tile = (10, 10)
        curr_time = datetime.datetime(2023, 1, 1, 10, 0)
        
        # Mock return values to verify data flow
        persona.perceiver.perceive.return_value = ["perceived_event"]
        persona.retriever.retrieve.return_value = {"retrieved": "context"}
        persona.planner.plan.return_value = "action_address"
        persona.executor.execute.return_value = "execution_details"
        
        result = persona.move(maze, personas, curr_tile, curr_time)
        
        # Verify sequence
        persona.perceiver.perceive.assert_called_with(maze)
        persona.retriever.retrieve.assert_called_with(["perceived_event"])
        
        # plan args: maze, personas, new_day, retrieved
        persona.planner.plan.assert_called()
        self.assertEqual(persona.planner.plan.call_args[0][3], {"retrieved": "context"})
        
        persona.reflector.reflect.assert_called_once()
        
        persona.executor.execute.assert_called_with(maze, personas, "action_address")
        
        self.assertEqual(result, "execution_details")
        
        # Verify state updates
        self.assertEqual(persona.scratch.curr_tile, curr_tile)
        self.assertEqual(persona.scratch.curr_time, curr_time)

if __name__ == '__main__':
    unittest.main()
